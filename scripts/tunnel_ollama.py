"""
NEXORA - Remote / Tunnel Ollama Helper Script.
Runs a local reverse proxy that rewrites the Host header for Ollama (port 11434),
allowing it to accept connections from ngrok tunnels or external IP addresses without 403 Forbidden.
"""

import http.server
import urllib.request
import socketserver
import sys

PROXY_PORT = 11435
TARGET_URL = "http://127.0.0.1:11434"

class OllamaTunnelProxy(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request("GET")

    def do_POST(self):
        self.proxy_request("POST")

    def proxy_request(self, method: str):
        url = TARGET_URL + self.path
        length = int(self.headers.get("content-length", 0))
        data = self.rfile.read(length) if length > 0 else None

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Host", "127.0.0.1:11434")
        if "content-type" in self.headers:
            req.add_header("Content-Type", self.headers["content-type"])

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            err_body = str(e).encode()
            self.send_response(502)
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)

if __name__ == "__main__":
    print(f"[*] Starting NEXORA Ollama Tunnel Proxy on port {PROXY_PORT} -> {TARGET_URL}...")
    print(f"[*] Run: ngrok http {PROXY_PORT}")
    try:
        with socketserver.ThreadingTCPServer(("", PROXY_PORT), OllamaTunnelProxy) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Proxy stopped.")
        sys.exit(0)
