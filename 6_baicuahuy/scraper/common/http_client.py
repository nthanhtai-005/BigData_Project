# -*- coding: utf-8 -*-
"""
HTTP client tối giản, KHÔNG cần thư viện ngoài (chỉ urllib stdlib).

Tính năng:
- Header mặc định + header tuỳ biến mỗi request.
- Rate limiting (delay giữa các request, có jitter).
- Retry với exponential backoff cho 429 / 5xx / lỗi mạng.
- Trả JSON đã parse, hoặc text thô.
"""
from __future__ import annotations
import json
import time
import random
import ssl
import gzip
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")


class HttpClient:
    def __init__(self,
                 base_headers: Optional[Dict[str, str]] = None,
                 delay: float = 0.6,
                 jitter: float = 0.4,
                 max_retries: int = 4,
                 timeout: int = 30,
                 verbose: bool = True):
        self.base_headers = {
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }
        if base_headers:
            self.base_headers.update(base_headers)
        self.delay = delay
        self.jitter = jitter
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose
        self._last_request_ts = 0.0
        # SSL context khoan dung (tránh lỗi cert trên một số máy Windows)
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE
        self.stats = {"requests": 0, "retries": 0, "errors": 0}

    def _throttle(self):
        """Đảm bảo cách nhau >= delay giây giữa 2 request."""
        if self.delay <= 0:
            return
        elapsed = time.time() - self._last_request_ts
        wait = self.delay + random.uniform(0, self.jitter) - elapsed
        if wait > 0:
            time.sleep(wait)

    def _read_body(self, resp) -> bytes:
        data = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip":
            try:
                data = gzip.decompress(data)
            except OSError:
                pass
        return data

    def get(self, url: str, headers: Optional[Dict[str, str]] = None,
            as_json: bool = True) -> Optional[Any]:
        """GET có retry. Trả JSON (dict/list) nếu as_json, ngược lại text.
        Trả None nếu thất bại sau khi hết retry."""
        h = dict(self.base_headers)
        if headers:
            h.update(headers)

        attempt = 0
        while attempt <= self.max_retries:
            self._throttle()
            self._last_request_ts = time.time()
            self.stats["requests"] += 1
            try:
                req = urllib.request.Request(url, headers=h, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                    body = self._read_body(resp)
                    if as_json:
                        return json.loads(body.decode("utf-8", errors="replace"))
                    return body.decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                code = e.code
                if code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    if self.verbose:
                        print(f"    [retry] HTTP {code} -> chờ {backoff:.1f}s | {url[:90]}")
                    self.stats["retries"] += 1
                    time.sleep(backoff)
                    attempt += 1
                    continue
                self.stats["errors"] += 1
                if self.verbose:
                    print(f"    [err] HTTP {code} | {url[:90]}")
                return None
            except (urllib.error.URLError, TimeoutError, ConnectionError, ssl.SSLError) as e:
                if attempt < self.max_retries:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    if self.verbose:
                        print(f"    [retry] {type(e).__name__} -> chờ {backoff:.1f}s | {url[:90]}")
                    self.stats["retries"] += 1
                    time.sleep(backoff)
                    attempt += 1
                    continue
                self.stats["errors"] += 1
                if self.verbose:
                    print(f"    [err] {type(e).__name__}: {e} | {url[:90]}")
                return None
            except json.JSONDecodeError:
                self.stats["errors"] += 1
                if self.verbose:
                    print(f"    [err] JSON không hợp lệ | {url[:90]}")
                return None
        return None
