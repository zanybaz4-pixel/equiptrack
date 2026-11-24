const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {runInNewContext} = require('node:vm');
const {createHmac} = require('node:crypto');
const source = readFileSync(resolve(__dirname, '../infra/gmail/Code.gs'), 'utf8');

function relay({quota = 100, lockAvailable = true} = {}) {
  const saved = {RELAY_SECRET: 'test-secret-'.repeat(4), APP_ORIGIN: 'https://equiptrack.example.invalid',
    RELAY_EXPIRES_AT: new Date(Date.now() + 86400000).toISOString()};
  const sent = [];
  let locked = false;
  const context = {
    ContentService: {MimeType: {JSON: 'json'}, createTextOutput: (text) => ({text, setMimeType() {return this;}})},
    PropertiesService: {getScriptProperties: () => ({getProperty: key => saved[key] || null,
      getProperties: () => ({...saved}), setProperties: value => Object.assign(saved, value), deleteProperty: key => delete saved[key]})},
    Utilities: {Charset: {UTF_8: 'utf-8'}, computeHmacSha256Signature: (value, key) =>
      [...createHmac('sha256', key).update(value).digest()].map(byte => byte > 127 ? byte - 256 : byte)},
    LockService: {getScriptLock: () => ({tryLock() {locked = lockAvailable; return locked;}, hasLock: () => locked, releaseLock() {locked = false;}})},
    MailApp: {getRemainingDailyQuota: () => quota, sendEmail: email => sent.push(email)},
  };
  runInNewContext(source, context);
  function body(nonce = 'n'.repeat(22)) {
    const data = {issued_at: Math.floor(Date.now() / 1000), request_id: nonce, email: 'borrower@example.invalid', token: 't'.repeat(43)};
    data.signature = createHmac('sha256', saved.RELAY_SECRET).update([data.issued_at, data.request_id, data.email, data.token].join('\n')).digest('hex');
    return data;
  }
  const post = data => JSON.parse(context.doPost({postData: {contents: JSON.stringify(data)}}).text);
  return {body, post, saved, sent};
}

test('valid signed request sends one fixed-purpose email and replay cannot resend', () => {
  const r = relay(); const data = r.body();
  assert.equal(r.post(data).ok, true);
  assert.equal(r.post(data).ok, false);
  assert.equal(r.sent.length, 1);
  assert.equal(r.sent[0].subject, 'Reset your EquipTrack password');
  assert.match(r.sent[0].body, /https:\/\/equiptrack\.example\.invalid\/#\/reset-password\?token=/);
  assert.equal(JSON.stringify(r.saved).includes(data.token), false);
  assert.equal(JSON.stringify(r.saved).includes(data.email), false);
});

test('tampered recipient and missing authentication cannot send', () => {
  const r = relay(); const data = r.body();
  assert.equal(r.post({...data, email: 'other@example.invalid'}).ok, false);
  assert.equal(r.post({...data, signature: undefined}).ok, false);
  assert.equal(r.sent.length, 0);
});

test('stale signed request cannot send', () => {
  const r = relay(); const data = r.body(); data.issued_at -= 301;
  data.signature = createHmac('sha256', r.saved.RELAY_SECRET).update([data.issued_at, data.request_id, data.email, data.token].join('\n')).digest('hex');
  assert.equal(r.post(data).ok, false);
  assert.equal(r.sent.length, 0);
});

test('quota exhaustion and unavailable lock fail safely', () => {
  for (const options of [{quota: 0}, {lockAvailable: false}]) {
    const r = relay(options); assert.equal(r.post(r.body()).ok, false); assert.equal(r.sent.length, 0);
  }
});

test('relay limits total hourly sends and rejects unsafe link configuration', () => {
  const r = relay();
  for (let i = 0; i < 30; i++) assert.equal(r.post(r.body(String(i).padStart(22, 'n'))).ok, true);
  assert.equal(r.post(r.body('z'.repeat(22))).ok, false);
  const unsafe = relay(); unsafe.saved.APP_ORIGIN = 'https://evil.example.invalid/path?x=y';
  assert.equal(unsafe.post(unsafe.body()).ok, false);
});

test('expired or missing relay authorization cannot send', () => {
  const expired = relay(); expired.saved.RELAY_EXPIRES_AT = '2000-01-01T00:00:00Z';
  assert.equal(expired.post(expired.body()).ok, false);
  const missing = relay(); delete missing.saved.RELAY_EXPIRES_AT;
  assert.equal(missing.post(missing.body()).ok, false);
});
