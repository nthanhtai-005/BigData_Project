/*
 * interceptor.js — Chạy trong MAIN world (ngữ cảnh của trang web).
 * Nhiệm vụ: override fetch() và XMLHttpRequest để bắt mọi lời gọi API,
 * lọc bỏ domain Google, rồi gửi dữ liệu sang content.js qua window.postMessage.
 *
 * Lưu ý: file này KHÔNG truy cập được chrome.* (vì chạy ở MAIN world).
 */
(function () {
  'use strict';

  if (window.__HSLT_API_CATCHER_INSTALLED__) return;
  window.__HSLT_API_CATCHER_INSTALLED__ = true;

  // ---- Danh sách domain bị BỎ QUA (không bắt). Mặc định: các dịch vụ của Google. ----
  var BLOCKED_HOSTS = [
    'google-analytics.com',
    'analytics.google.com',
    'googletagmanager.com',
    'googleapis.com',
    'gstatic.com',
    'google.com',
    'google.com.vn',
    'doubleclick.net',
    'g.doubleclick.net',
    'googlesyndication.com',
    'googleadservices.com',
    'googletagservices.com',
    'app-measurement.com',
    'recaptcha.net'
  ];

  function hostOf(url) {
    try { return new URL(url, location.href).hostname.toLowerCase(); }
    catch (e) { return ''; }
  }
  function absolutize(url) {
    try { return new URL(url, location.href).href; }
    catch (e) { return String(url || ''); }
  }
  function isBlocked(url) {
    var host = hostOf(url);
    if (!host) return false;
    for (var i = 0; i < BLOCKED_HOSTS.length; i++) {
      var b = BLOCKED_HOSTS[i];
      if (host === b || host.endsWith('.' + b)) return true;
    }
    return false;
  }
  function shouldCapture(url) {
    return !!url && !isBlocked(url);
  }

  // Chỉ đọc body cho các response dạng text/JSON; bỏ qua nhị phân (ảnh, font, video...)
  function isReadableType(ct) {
    if (!ct) return true; // không rõ -> vẫn đọc
    ct = ct.toLowerCase();
    return /(json|text|xml|javascript|csv|html|x-www-form-urlencoded|graphql|plain)/.test(ct);
  }

  function safeBody(body) {
    if (body == null) return null;
    try {
      if (typeof body === 'string') {
        return body.length > 200000 ? body.slice(0, 200000) + '...[truncated]' : body;
      }
      if (body instanceof URLSearchParams) return body.toString();
      if (typeof FormData !== 'undefined' && body instanceof FormData) {
        var o = {};
        body.forEach(function (v, k) { o[k] = (typeof v === 'string') ? v : '[file]'; });
        return JSON.stringify(o);
      }
      if (typeof Blob !== 'undefined' && body instanceof Blob) return '[blob ' + body.size + ' bytes]';
      if (body instanceof ArrayBuffer) return '[arraybuffer ' + body.byteLength + ' bytes]';
      return String(body);
    } catch (e) { return null; }
  }

  function post(record) {
    try {
      record.url = absolutize(record.url);
      record.page = location.href;
      record.ts = Date.now();
      window.postMessage({ __HSLT_API_CATCHER__: true, record: record }, location.origin);
    } catch (e) { /* ignore */ }
  }

  // ---------------- fetch ----------------
  var origFetch = window.fetch;
  if (typeof origFetch === 'function') {
    window.fetch = function () {
      var args = arguments;
      var input = args[0];
      var init = args[1] || {};
      var url = (typeof input === 'string') ? input : (input && input.url) || '';
      var method = (init && init.method) || (input && input.method) || 'GET';
      var reqBody = (init && init.body != null) ? init.body : null;

      var p = origFetch.apply(this, args);

      try {
        if (shouldCapture(url)) {
          p.then(function (response) {
            try {
              var ct = '';
              try { ct = response.headers.get('content-type') || ''; } catch (e) {}
              var base = {
                type: 'fetch',
                method: String(method).toUpperCase(),
                url: url,
                status: response.status,
                contentType: ct,
                requestBody: safeBody(reqBody)
              };
              if (isReadableType(ct)) {
                response.clone().text().then(function (text) {
                  base.responseBody = text;
                  post(base);
                }).catch(function () {
                  base.responseBody = '';
                  post(base);
                });
              } else {
                base.responseBody = '[skipped ' + ct + ']';
                post(base);
              }
            } catch (e) { /* ignore */ }
          }).catch(function () { /* ignore network errors */ });
        }
      } catch (e) { /* ignore */ }

      return p;
    };
  }

  // ---------------- XMLHttpRequest ----------------
  var XHR = window.XMLHttpRequest;
  if (XHR && XHR.prototype) {
    var origOpen = XHR.prototype.open;
    var origSend = XHR.prototype.send;

    XHR.prototype.open = function (method, url) {
      try { this.__hslt = { method: method, url: url }; } catch (e) {}
      return origOpen.apply(this, arguments);
    };

    XHR.prototype.send = function (body) {
      var xhr = this;
      try {
        if (xhr.__hslt) xhr.__hslt.requestBody = body;
        xhr.addEventListener('loadend', function () {
          try {
            var info = xhr.__hslt || {};
            if (!shouldCapture(info.url)) return;

            var ct = '';
            try { ct = xhr.getResponseHeader('content-type') || ''; } catch (e) {}

            var text = '';
            try {
              var rt = xhr.responseType;
              if (rt === '' || rt === 'text') {
                text = isReadableType(ct) ? xhr.responseText : '[skipped ' + ct + ']';
              } else if (rt === 'json') {
                text = JSON.stringify(xhr.response);
              } else {
                text = '[' + rt + ' response]';
              }
            } catch (e) { text = ''; }

            post({
              type: 'xhr',
              method: String(info.method || 'GET').toUpperCase(),
              url: info.url,
              status: xhr.status,
              contentType: ct,
              requestBody: safeBody(info.requestBody),
              responseBody: text
            });
          } catch (e) { /* ignore */ }
        });
      } catch (e) { /* ignore */ }
      return origSend.apply(this, arguments);
    };
  }
})();
