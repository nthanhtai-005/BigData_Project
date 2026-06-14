/*
 * content.js — Chạy trong ISOLATED world.
 * Nhiệm vụ:
 *   - Nhận dữ liệu API từ interceptor.js (qua window.postMessage) và chuyển cho background.
 *   - Bắt phím tắt Ctrl+Alt+N (ghi/dừng) và Ctrl+Alt+M (tải về).
 *   - Hiển thị chỉ báo "đang ghi" và toast thông báo.
 */
(function () {
  'use strict';

  var isRecording = false;

  function sendBg(msg) {
    return new Promise(function (resolve) {
      try {
        chrome.runtime.sendMessage(msg, function (resp) {
          if (chrome.runtime.lastError) resolve(null);
          else resolve(resp);
        });
      } catch (e) { resolve(null); }
    });
  }

  // ---- Nhận dữ liệu API từ interceptor (MAIN world) ----
  window.addEventListener('message', function (event) {
    if (event.source !== window) return;
    var data = event.data;
    if (!data || data.__HSLT_API_CATCHER__ !== true || !data.record) return;
    if (!isRecording) return; // không ghi thì bỏ qua để giảm tải
    sendBg({ type: 'CAPTURE', record: data.record });
  }, false);

  // ---- Đồng bộ trạng thái từ background ----
  chrome.runtime.onMessage.addListener(function (msg) {
    if (!msg) return;
    if (msg.type === 'STATE') {
      isRecording = !!msg.recording;
      updateIndicator();
      if (msg.toast) toast(msg.toast);
    }
  });

  // ---- Phím tắt ----
  window.addEventListener('keydown', function (e) {
    if (!e.ctrlKey || !e.altKey || e.shiftKey || e.metaKey) return;
    if (e.repeat) return;
    if (e.code === 'KeyN') {
      e.preventDefault(); e.stopPropagation();
      toggleRecord();
    } else if (e.code === 'KeyM') {
      e.preventDefault(); e.stopPropagation();
      doDownload();
    }
  }, true);

  function toggleRecord() {
    sendBg({ type: 'TOGGLE_RECORD' }).then(function (resp) {
      if (!resp || !resp.ok) { toast('⚠ Không kết nối được extension (thử tải lại trang)'); return; }
      isRecording = !!resp.recording;
      updateIndicator();
      toast(isRecording ? '🔴 Bắt đầu ghi API' : ('⏹ Đã dừng — ' + resp.count + ' request'));
    });
  }

  function doDownload() {
    sendBg({ type: 'EXPORT' }).then(function (resp) {
      if (!resp || !resp.ok) { toast('⚠ Lỗi khi xuất dữ liệu'); return; }
      if (!resp.count) { toast('Chưa có dữ liệu để tải'); return; }
      try {
        var blob = new Blob([resp.json], { type: 'application/json' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = resp.filename;
        (document.body || document.documentElement).appendChild(a);
        a.click();
        a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 8000);
        toast('💾 Đã tải ' + resp.count + ' request');
      } catch (err) {
        toast('⚠ Lỗi tải file: ' + (err && err.message));
      }
    });
  }

  // ---- Chỉ báo "đang ghi" ----
  var indicator = null;
  function updateIndicator() {
    if (isRecording) {
      if (!indicator) {
        indicator = document.createElement('div');
        indicator.textContent = '● REC API';
        indicator.style.cssText = [
          'position:fixed', 'top:10px', 'right:10px', 'z-index:2147483647',
          'background:#d32f2f', 'color:#fff', 'font:bold 12px/1 system-ui,Arial,sans-serif',
          'padding:6px 10px', 'border-radius:6px', 'box-shadow:0 2px 8px rgba(0,0,0,.3)',
          'pointer-events:none', 'letter-spacing:.5px'
        ].join(';');
        (document.body || document.documentElement).appendChild(indicator);
      }
    } else if (indicator) {
      indicator.remove();
      indicator = null;
    }
  }

  // ---- Toast thông báo ----
  var toastEl = null, toastTimer = null;
  function toast(text) {
    try {
      if (!toastEl) {
        toastEl = document.createElement('div');
        toastEl.style.cssText = [
          'position:fixed', 'bottom:20px', 'right:20px', 'z-index:2147483647',
          'background:#222', 'color:#fff', 'font:14px/1.4 system-ui,Arial,sans-serif',
          'padding:10px 14px', 'border-radius:8px', 'box-shadow:0 4px 16px rgba(0,0,0,.35)',
          'max-width:320px', 'pointer-events:none', 'opacity:0', 'transition:opacity .2s'
        ].join(';');
        (document.body || document.documentElement).appendChild(toastEl);
      }
      toastEl.textContent = text;
      toastEl.style.opacity = '1';
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { if (toastEl) toastEl.style.opacity = '0'; }, 2500);
    } catch (e) { /* ignore */ }
  }

  // ---- Lấy trạng thái ban đầu khi trang vừa tải ----
  sendBg({ type: 'GET_STATE' }).then(function (resp) {
    if (resp && resp.ok) {
      isRecording = !!resp.recording;
      updateIndicator();
    }
  });
})();
