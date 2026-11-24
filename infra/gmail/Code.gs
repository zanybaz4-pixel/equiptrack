/** EquipTrack's signed, fixed-purpose Gmail relay. Never logs email addresses or tokens. */
function jsonReply(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return jsonReply({service: 'EquipTrack password reset email relay'});
}

function sameSignature(left, right) {
  if (typeof right !== 'string' || !/^[a-f0-9]{64}$/.test(right)) return false;
  var different = 0;
  for (var i = 0; i < 64; i++) different |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return different === 0;
}

function doPost(event) {
  var lock;
  try {
    var raw = event && event.postData && event.postData.contents;
    if (typeof raw !== 'string' || raw.length > 2000) return jsonReply({ok: false});
    var data = JSON.parse(raw);
    var now = Math.floor(Date.now() / 1000);
    if (!Number.isInteger(data.issued_at) || Math.abs(now - data.issued_at) > 300
        || typeof data.request_id !== 'string' || !/^[A-Za-z0-9_-]{22}$/.test(data.request_id)
        || typeof data.email !== 'string' || data.email.length > 254
        || !/^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+$/.test(data.email)
        || typeof data.token !== 'string' || !/^[A-Za-z0-9_-]{43}$/.test(data.token)) {
      return jsonReply({ok: false});
    }
    var properties = PropertiesService.getScriptProperties();
    var secret = properties.getProperty('RELAY_SECRET') || '';
    var origin = properties.getProperty('APP_ORIGIN') || '';
    var expiry = Date.parse(properties.getProperty('RELAY_EXPIRES_AT') || '') / 1000;
    if (secret.length < 32 || !Number.isFinite(expiry) || expiry <= now
        || !/^https:\/\/[A-Za-z0-9.-]+(?::[0-9]+)?$/.test(origin)) return jsonReply({ok: false});
    var message = [data.issued_at, data.request_id, data.email, data.token].join('\n');
    var expected = Utilities.computeHmacSha256Signature(message, secret, Utilities.Charset.UTF_8)
      .map(function(value) { return ('0' + ((value + 256) % 256).toString(16)).slice(-2); }).join('');
    if (!sameSignature(expected, data.signature)) return jsonReply({ok: false});
    lock = LockService.getScriptLock();
    if (!lock.tryLock(5000)) return jsonReply({ok: false});
    var nonceKey = 'NONCE_' + data.request_id;
    if (properties.getProperty(nonceKey)) return jsonReply({ok: false});
    var saved = properties.getProperties();
    Object.keys(saved).forEach(function(key) {
      if (key.indexOf('NONCE_') === 0 && Number(saved[key]) < now - 600) properties.deleteProperty(key);
    });
    var hour = String(Math.floor(now / 3600));
    var count = properties.getProperty('SEND_HOUR') === hour ? Number(properties.getProperty('SEND_COUNT') || '0') : 0;
    if (count >= 30 || MailApp.getRemainingDailyQuota() < 1) return jsonReply({ok: false});
    // Consume before sending, so simultaneous/replayed requests cannot send twice.
    properties.setProperties({[nonceKey]: String(now), SEND_HOUR: hour, SEND_COUNT: String(count + 1)});
    var link = origin + '/#/reset-password?token=' + encodeURIComponent(data.token);
    MailApp.sendEmail({
      to: data.email,
      subject: 'Reset your EquipTrack password',
      name: 'EquipTrack',
      body: 'We received a request to reset your EquipTrack password.\n\nChoose a new password here:\n'
        + link + '\n\nThis link expires in 15 minutes and can be used once. After resetting, sign in again on your devices.'
        + '\n\nIf you did not request this, ignore this email. Your password has not changed.'
        + '\nUse a separate EquipTrack password, not your Gmail password.'
    });
    return jsonReply({ok: true});
  } catch (ignored) {
    return jsonReply({ok: false});
  } finally {
    if (lock && lock.hasLock()) lock.releaseLock();
  }
}
