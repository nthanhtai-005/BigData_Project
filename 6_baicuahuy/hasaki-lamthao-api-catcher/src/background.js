/*
 * background.js — Service worker (MV3).
 * Nhiệm vụ:
 *   - Lưu trạng thái ghi (recording) và danh sách request đã bắt (records).
 *   - Nhận message từ content.js: CAPTURE / TOGGLE_RECORD / GET_STATE / EXPORT / CLEAR.
 *   - Xuất dữ liệu JSON, cập nhật badge, đồng bộ trạng thái cho các tab.
 */
'use strict';

var K_REC = 'recording';
var K_RECS = 'records';

var recording = false;
var records = [];
var flushTimer = null;

// Nạp dữ liệu đã lưu khi service worker khởi động
var ready = (async function init() {
  try {
    var data = await chrome.storage.local.get([K_REC, K_RECS]);
    recording = !!data[K_REC];
    records = Array.isArray(data[K_RECS]) ? data[K_RECS] : [];
  } catch (e) {
    recording = false;
    records = [];
  }
  updateBadge();
})();

// ---- Ghi xuống storage (gộp nhiều lần ghi để giảm I/O) ----
function scheduleFlush() {
  if (flushTimer) return;
  flushTimer = setTimeout(function () {
    flushTimer = null;
    chrome.storage.local.set({ [K_RECS]: records }).catch(function () {});
  }, 800);
}
async function flushNow() {
  if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
  try { await chrome.storage.local.set({ [K_RECS]: records }); } catch (e) {}
}

// ---- Badge trên icon extension ----
function updateBadge() {
  try {
    var n = records.length;
    if (recording) {
      chrome.action.setBadgeBackgroundColor({ color: '#d32f2f' });
      chrome.action.setBadgeText({ text: n > 9999 ? '9999+' : (n ? String(n) : 'REC') });
    } else {
      chrome.action.setBadgeBackgroundColor({ color: '#555555' });
      chrome.action.setBadgeText({ text: n ? (n > 9999 ? '9999+' : String(n)) : '' });
    }
  } catch (e) { /* ignore */ }
}

// Giới hạn kích thước mỗi response để tránh phình bộ nhớ
function trimRecord(r) {
  try {
    if (r && typeof r.responseBody === 'string' && r.responseBody.length > 2000000) {
      r.responseBody = r.responseBody.slice(0, 2000000) + '...[truncated]';
    }
  } catch (e) {}
  return r;
}

// Đồng bộ trạng thái cho mọi tab thuộc 2 site
async function broadcastState(toastText) {
  var tabs = [];
  try {
    tabs = await chrome.tabs.query({ url: ['*://*.hasaki.vn/*', '*://*.lamthaocosmetics.vn/*'] });
  } catch (e) { tabs = []; }
  for (var i = 0; i < tabs.length; i++) {
    var id = tabs[i] && tabs[i].id;
    if (id == null) continue;
    chrome.tabs.sendMessage(id, { type: 'STATE', recording: recording, toast: toastText })
      .catch(function () { /* tab chưa có content script -> bỏ qua */ });
  }
}

function buildExport() {
  var payload = {
    exportedAt: new Date().toISOString(),
    source: 'Hasaki & Lamthao API Catcher',
    total: records.length,
    records: records
  };
  var json = JSON.stringify(payload, null, 2);
  var ts = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').replace('Z', '');
  return { json: json, filename: 'api-capture-' + ts + '.json', count: records.length };
}

chrome.runtime.onMessage.addListener(function (msg, sender, sendResponse) {
  (async function () {
    await ready;
    if (!msg || !msg.type) { sendResponse({ ok: false }); return; }

    switch (msg.type) {
      case 'CAPTURE':
        if (recording && msg.record) {
          records.push(trimRecord(msg.record));
          scheduleFlush();
          updateBadge();
        }
        sendResponse({ ok: true, recording: recording });
        break;

      case 'TOGGLE_RECORD':
        recording = !recording;
        try { await chrome.storage.local.set({ [K_REC]: recording }); } catch (e) {}
        updateBadge();
        broadcastState();
        sendResponse({ ok: true, recording: recording, count: records.length });
        break;

      case 'GET_STATE':
        sendResponse({ ok: true, recording: recording, count: records.length });
        break;

      case 'EXPORT': {
        await flushNow();
        var ex = buildExport();
        sendResponse({ ok: true, json: ex.json, filename: ex.filename, count: ex.count });
        break;
      }

      case 'CLEAR':
        records = [];
        await flushNow();
        updateBadge();
        broadcastState();
        sendResponse({ ok: true, count: 0 });
        break;

      default:
        sendResponse({ ok: false, error: 'unknown' });
    }
  })();
  return true; // giữ kênh mở cho sendResponse bất đồng bộ
});
