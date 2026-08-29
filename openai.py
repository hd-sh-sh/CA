"""POST /api/openai — 브라우저 대신 OpenAI를 호출한다. 키는 Vercel 환경 변수에서만 읽는다."""
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class handler(BaseHTTPRequestHandler):
    def reply(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return self.reply(200, {"error": {"message":
                "Vercel 프로젝트의 Environment Variables 에 OPENAI_API_KEY 가 없습니다."}})

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self.reply(400, {"error": {"message": "잘못된 요청 본문"}})

        payload.setdefault("model", os.environ.get("OPENAI_MODEL", "gpt-5.1"))

        req = urllib.request.Request(
            OPENAI_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=55) as r:
                raw = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(raw)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            self.reply(200, {"error": {"message": "OpenAI %s · %s" % (e.code, detail)}})
        except Exception as e:
            self.reply(200, {"error": {"message": "OpenAI 연결 실패: %s" % e}})
