#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
import os

ROOT = os.path.dirname(__file__)


def clean_base(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError("Invalid HA URL")
    return f"{p.scheme}://{p.netloc}"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.split("?", 1)[0].split("#", 1)[0]
        rel = rel.lstrip("/") or "index.html"
        return os.path.join(ROOT, rel)

    def _json(self, code, payload):
        b = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _proxy(self, upstream, method="GET", body=None):
        token = self.headers.get("X-HA-Token", "").strip()
        if not token:
            return self._json(400, {"error": "Missing X-HA-Token"})

        headers = {"Authorization": f"Bearer {token}"}
        if method != "GET":
            headers["Content-Type"] = "application/json"
        req = Request(upstream, data=body, headers=headers, method=method)

        try:
            with urlopen(req, timeout=20) as r:
                resp = r.read()
                self.send_response(r.status)
                self.send_header("Content-Type", r.headers.get_content_type() or "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
        except HTTPError as e:
            body = e.read() or b""
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body or json.dumps({"error": str(e)}).encode())
        except Exception as e:
            self._json(502, {"error": str(e)})

    def do_GET(self):
        if self.path == "/proxy/states":
            try:
                base = clean_base(self.headers.get("X-HA-Url", ""))
                return self._proxy(f"{base}/api/states")
            except Exception as e:
                return self._json(400, {"error": str(e)})

        if self.path.startswith("/proxy/states/"):
            try:
                base = clean_base(self.headers.get("X-HA-Url", ""))
                entity = self.path[len("/proxy/states/"):]
                return self._proxy(f"{base}/api/states/{quote(entity, safe='._')}")
            except Exception as e:
                return self._json(400, {"error": str(e)})

        if self.path.startswith("/proxy/history"):
            try:
                base = clean_base(self.headers.get("X-HA-Url", ""))
                q = parse_qs(urlparse(self.path).query)
                entity = q.get("entity", [""])[0]
                start = q.get("start", [""])[0]
                end = q.get("end", [""])[0]
                if not (entity and start and end):
                    return self._json(400, {"error": "Missing entity/start/end"})
                # IMPORTANT: '+' in query values can be interpreted as space by servers.
                # For query params we must percent-encode '+' as %2B.
                upstream = (
                    f"{base}/api/history/period/{quote(start, safe=':-T.Z')}"
                    f"?end_time={quote(end, safe=':-T.Z')}&filter_entity_id={quote(entity, safe='._')}&minimal_response"
                )
                return self._proxy(upstream)
            except Exception as e:
                return self._json(400, {"error": str(e)})

        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/proxy/services/"):
            try:
                base = clean_base(self.headers.get("X-HA-Url", ""))
                parts = self.path.split("/")
                if len(parts) < 5:
                    return self._json(400, {"error": "Path must be /proxy/services/<domain>/<service>"})
                domain, service = parts[3], parts[4]
                length = int(self.headers.get("Content-Length", "0") or "0")
                body = self.rfile.read(length) if length > 0 else b"{}"
                upstream = f"{base}/api/services/{quote(domain)}/{quote(service)}"
                return self._proxy(upstream, method="POST", body=body)
            except Exception as e:
                return self._json(400, {"error": str(e)})

        return self._json(404, {"error": "Unknown POST endpoint"})


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", 8099), Handler)
    print("Serving on http://0.0.0.0:8099")
    server.serve_forever()
