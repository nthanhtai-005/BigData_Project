'use strict';

function send(msg) {
  return new Promise(function (res) {
    chrome.runtime.sendMessage(msg, function (r) {
      res(chrome.runtime.lastError ? null : r);
    });
  });
}

var dot = document.getElementById('dot');
var stateText = document.getElementById('stateText');
var countEl = document.getElementById('count');
var toggleBtn = document.getElementById('toggle');

function render(state) {
  var rec = !!(state && state.recording);
  dot.className = 'dot' + (rec ? ' on' : '');
  stateText.textContent = rec ? 'Đang ghi API…' : 'Đang dừng';
  toggleBtn.textContent = rec ? 'Dừng ghi' : 'Bắt đầu ghi';
  toggleBtn.className = rec ? 'stop' : 'primary';
  countEl.textContent = ((state && state.count) || 0) + ' request đã bắt';
}

async function refresh() {
  var s = await send({ type: 'GET_STATE' });
  if (s && s.ok) render(s);
}

toggleBtn.addEventListener('click', async function () {
  var s = await send({ type: 'TOGGLE_RECORD' });
  if (s && s.ok) render(s);
});

document.getElementById('download').addEventListener('click', async function () {
  var ex = await send({ type: 'EXPORT' });
  if (!ex || !ex.ok) { alert('Lỗi xuất dữ liệu'); return; }
  if (!ex.count) { alert('Chưa có dữ liệu để tải'); return; }
  var blob = new Blob([ex.json], { type: 'application/json' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = ex.filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 8000);
});

document.getElementById('clear').addEventListener('click', async function () {
  if (!confirm('Xóa toàn bộ dữ liệu đã bắt?')) return;
  var s = await send({ type: 'CLEAR' });
  if (s && s.ok) { render({ recording: false, count: 0 }); }
  refresh();
});

refresh();
