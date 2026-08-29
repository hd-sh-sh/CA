"""GET /api/health — 앱이 서버 모드인지, 키가 들어 있는지 확인한다."""
import json
import os
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "ok": True,
            "hasOpenAIKey": bool(os.environ.get("OPENAI_API_KEY")),
            "hasCareerNetKey": bool(os.environ.get("CAREERNET_API_KEY")),
            "model": os.environ.get("OPENAI_MODEL", "gpt-5.1"),
        }, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
