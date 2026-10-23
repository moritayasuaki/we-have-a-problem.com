const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');

test('social crawlers can find a real large preview image without JavaScript', () => {
  const root = join(__dirname, '..');
  const head = readFileSync(join(root, 'index.html'), 'utf8').split('</head>')[0];
  const meta = name => head.match(new RegExp('<meta (?:name|property)="' + name + '" content="([^"]+)"'))?.[1];
  const imageUrl = new URL(meta('og:image'));
  assert.equal(meta('twitter:card'), 'summary_large_image');
  assert.equal(meta('twitter:image'), imageUrl.href);
  assert.equal(imageUrl.origin, new URL(meta('og:url')).origin);
  assert.equal(imageUrl.protocol, 'https:');
  assert.ok(meta('og:image:alt'));
  const image = readFileSync(join(root, imageUrl.pathname));
  assert.equal(image.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  assert.equal(image.readUInt32BE(16), Number(meta('og:image:width')));
  assert.equal(image.readUInt32BE(20), Number(meta('og:image:height')));
  assert.ok(image.readUInt32BE(16) >= 600 && image.readUInt32BE(20) >= 315);
  assert.ok(image.byteLength < 5 * 1024 * 1024);
});
