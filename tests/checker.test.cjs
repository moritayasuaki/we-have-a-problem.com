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
  const document = {
    documentElement: {},
    createElement: element,
    querySelector: () => tbody,
    querySelectorAll: () => [],
    getElementById: id => ({ summary, rerun, results: element(),
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
  return { context, tbody, summary, rerun,
    probe: () => vm.runInContext("probe('test.example')", context),
    start: () => vm.runInContext('start()', context) };
}

test('only the expected test response produces a connected result', async () => {
  const page = checker(async () => ({ status: 200, text: async () => marker }));
  const result = await page.probe();
  assert.equal(result.status, 'connected');
  assert.match(result.text, /potentially affected/);
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
  assert.equal(result.text, '✅ Did not connect');
  await page.start();
  assert.equal(page.tbody.children.length, 14);
  assert.ok(page.tbody.children.every(row => row.children[2].className === 'good'));
  assert.match(page.summary.textContent, /Failed connections do not prove safety/);
  assert.equal(page.summary.children.length, 0);
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
  assert.ok(page.tbody.children.every(row => row.children[2].className === 'pending'));
});

test('Japanese checker works without Object.hasOwn and IntersectionObserver', async () => {
  const page = checker(async () => { throw new TypeError('Failed to fetch'); }, { language: 'ja', noHasOwn: true });
  await page.start();
  assert.equal(vm.runInContext('document.documentElement.lang', page.context), 'ja');
  assert.equal(page.tbody.children.length, 14);
  assert.match(page.summary.textContent, /安全とは断定できません/);
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
});
