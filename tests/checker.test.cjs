// Run with: node --test tests/*.test.cjs. No network or installed packages.
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const html = readFileSync(join(__dirname, '..', 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const japanese = html.match(/<script type="application\/json" id="translations-ja">([\s\S]*?)<\/script>/)[1];
const marker = 'Your client successfully connected to the site.';

function checker(fetch, options = {}) {
  function element() {
    return {
      children: [], textContent: '', className: '', disabled: false,
      append(...items) { this.children.push(...items); },
      appendChild(item) { this.children.push(item); },
      addEventListener() {},
    };
  }
  const tbody = element(), summary = element(), rerun = element();
  const verdict = element(), verdictTitle = element(), verdictDetail = element();
  const globalNotice = element(), globalTitle = element(), globalDetail = element(), globalAction = element(), announcement = element();
  const document = {
    documentElement: {},
    createElement: element,
    querySelector: () => tbody,
    querySelectorAll: () => [],
    getElementById: id => ({ summary, rerun, results: element(),
      'browser-verdict': verdict, 'verdict-title': verdictTitle,
      'verdict-detail': verdictDetail, 'verdict-symbol': element(),
      'global-notice': globalNotice, 'global-title': globalTitle,
      'global-detail': globalDetail, 'global-action': globalAction,
      'global-symbol': element(), 'urgent-announcement': announcement,
      'translations-ja': { textContent: japanese } })[id] || null,
  };
  const context = vm.createContext({
    document, navigator: { languages: [options.language || 'en'] },
    location: new URL('https://example.com/'), URL, URLSearchParams,
    window: { addEventListener() {} }, HTMLDetailsElement: class {},
    AbortController: options.unavailable ? undefined : AbortController,
    setTimeout: fn => setTimeout(fn, 1), clearTimeout, fetch,
  });
  if (options.noHasOwn) vm.runInContext('Object.hasOwn = undefined', context);
  vm.runInContext(script, context);
  return { context, tbody, summary, rerun, verdict, verdictTitle, verdictDetail,
    globalNotice, globalTitle, globalDetail, globalAction, announcement,
    probe: () => vm.runInContext("probe('test.example')", context),
    start: () => vm.runInContext('start()', context) };
}

test('only the expected test response produces a connected result', async () => {
  const page = checker(async () => ({ status: 200, text: async () => marker }));
  const result = await page.probe();
  assert.equal(result.status, 'connected');
  assert.match(result.text, /check updates/);
});

test('a proxy block page is inconclusive, regardless of HTTP success', async () => {
  for (const status of [200, 403, 500]) {
    const page = checker(async () => ({ status, text: async () => 'proxy block page' }));
    const result = await page.probe();
    assert.equal(result.status, 'unknown');
    assert.match(result.text, new RegExp(String(status)));
  }
});

test('TLS and network failures retain the original did-not-connect result', async () => {
  const page = checker(async () => { throw new TypeError('Failed to fetch'); });
  const result = await page.probe();
  assert.equal(result.status, 'blocked');
  assert.equal(result.text, '✅ Test response not received');
  await page.start();
  assert.equal(page.tbody.children.length, 14);
  assert.ok(page.tbody.children.every(row => row.children[2].className === 'good'));
  assert.match(page.summary.textContent, /Failed connections do not prove safety/);
  assert.equal(page.summary.children.length, 0);
  assert.equal(page.verdict.className, 'verdict no-response');
  assert.match(page.verdictDetail.textContent, /Network failures/);
});

test('a timed-out request is inconclusive and aborted', async () => {
  let signal;
  const page = checker((url, options) => new Promise((resolve, reject) => {
    signal = options.signal;
    signal.addEventListener('abort', () => reject(Object.assign(new Error('timeout'), { name: 'AbortError' })));
  }));
  const result = await page.probe();
  assert.equal(signal.aborted, true);
  assert.equal(result.status, 'unknown');
  assert.match(result.text, /timed out/);
});

test('response-body read failures retain the original failure classification', async () => {
  const page = checker(async () => ({ status: 200, text: async () => { throw new Error('disconnected'); } }));
  assert.equal((await page.probe()).status, 'blocked');
});

test('missing checker APIs show a failure notice and leave retry enabled', async () => {
  const page = checker(async () => { throw new Error('should not fetch'); }, { unavailable: true });
  await page.start();
  assert.equal(page.rerun.disabled, false);
  assert.match(page.summary.textContent, /No safety conclusion/);
  assert.equal(page.verdict.className, 'verdict neutral');
  assert.ok(page.tbody.children.every(row => row.children[2].className === 'pending'));
});

test('Japanese checker works without Object.hasOwn and IntersectionObserver', async () => {
  const page = checker(async () => { throw new TypeError('Failed to fetch'); }, { language: 'ja', noHasOwn: true });
  await page.start();
  assert.equal(vm.runInContext('document.documentElement.lang', page.context), 'ja');
  assert.equal(page.tbody.children.length, 14);
  assert.match(page.summary.textContent, /安全とは断定できません/);
  assert.ok(page.tbody.children.every(row => row.children[2].textContent === '✅ テスト応答を取得できませんでした' && row.children[2].className === 'good'));
  assert.equal(page.rerun.disabled, false);
});

test('a second start cannot issue duplicate probes while a run is active', async () => {
  let calls = 0, resolve;
  const response = new Promise(done => { resolve = done; });
  const page = checker(() => { calls++; return response; });
  const first = page.start();
  assert.equal(page.rerun.disabled, true);
  await page.start();
  assert.equal(calls, 14);
  resolve({ status: 200, text: async () => marker });
  await first;
  assert.equal(page.rerun.disabled, false);
  assert.match(page.summary.textContent, /14 of 14/);
  assert.equal(page.verdict.className, 'verdict needs-action');
});

test('an incomplete set of checks never produces a green overview', async () => {
  let calls = 0;
  const page = checker(async () => {
    if (++calls === 1) return { status: 403, text: async () => 'proxy block page' };
    throw new TypeError('Failed to fetch');
  });
  await page.start();
  assert.equal(page.verdict.className, 'verdict neutral');
  assert.equal(page.verdictTitle.textContent, 'The check is incomplete.');
});

test('a received test response takes action priority over incomplete checks', async () => {
  let calls = 0;
  const page = checker(async () => ({ status: 200, text: async () => ++calls === 1 ? marker : 'proxy' }));
  await page.start();
  assert.equal(page.verdict.className, 'verdict needs-action');
  assert.match(page.verdictDetail.textContent, /does not show that an attack happened/);
});

test('the first received response raises the global alert before other probes finish', async () => {
  let calls = 0, finish;
  const waiting = new Promise(resolve => { finish = resolve; });
  const page = checker(() => ++calls === 1 ? Promise.resolve({ status: 200, text: async () => marker }) : waiting);
  const running = page.start();
  await new Promise(setImmediate);
  assert.equal(page.rerun.disabled, true);
  assert.equal(page.globalNotice.className, 'global-notice needs-action');
  assert.match(page.globalTitle.textContent, /test response was received/);
  assert.equal(page.globalAction.href, '#browser-action');
  assert.match(page.announcement.textContent, /not proof of an attack/);
  finish({ status: 403, text: async () => 'proxy' });
  await running;
});

test('retry and an incomplete result retain a clearly labeled previous alert', async () => {
  let mode = 'connected', finish;
  const waiting = new Promise(resolve => { finish = resolve; });
  const page = checker(() => {
    if (mode === 'waiting') return waiting;
    if (mode === 'blocked') return Promise.reject(new TypeError('network failure'));
    return Promise.resolve({ status: 200, text: async () => marker });
  });
  await page.start();
  mode = 'waiting';
  const running = page.start();
  assert.equal(page.globalNotice.className, 'global-notice needs-action');
  assert.match(page.globalTitle.textContent, /previous.*Checking again/);
  finish({ status: 403, text: async () => 'proxy' });
  await running;
  assert.equal(page.globalNotice.className, 'global-notice needs-action');
  assert.match(page.globalTitle.textContent, /previous.*incomplete/);
  mode = 'blocked';
  await page.start();
  assert.equal(page.globalNotice.className, 'global-notice no-response');
  assert.match(page.globalDetail.textContent, /Network failures/);
  assert.equal(page.announcement.textContent, '');
});
