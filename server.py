"""
미디어 진로 도우미 — 로컬 실행 서버

하는 일 세 가지
  1) career-agent.html 을 http://localhost:8000 으로 띄운다  (file:// 문제 해결)
  2) 브라우저 대신 OpenAI를 호출한다                          (CORS 문제 해결)
  3) 브라우저 대신 커리어넷을 호출한다                        (CORS 문제 해결)

키는 .env 에서만 읽는다. HTML 안에는 키가 들어가지 않는다.

실행:  python3 server.py
종료:  Ctrl+C
파이썬 표준 라이브러리만 쓴다. 설치할 것 없음.
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


def load_env():
    """.env 를 읽어 dict 로 돌려준다. 따옴표는 벗겨 준다."""
    env = {}
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
OPENAI_KEY = ENV.get("OPENAI_API_KEY", "")
OPENAI_MODEL = ENV.get("OPENAI_MODEL", "gpt-5.1")
CAREERNET_KEY = ENV.get("CAREERNET_API_KEY", "")


def post_json(url, payload, headers, timeout=120):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        if "/api/" in self.path:
            print("  →", self.path.split("?")[0])

    def send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------- GET ----------
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
            return SimpleHTTPRequestHandler.do_GET(self)

        if self.path.startswith("/api/health"):
            return self.send_json(200, {
                "ok": True,
                "hasOpenAIKey": bool(OPENAI_KEY),
                "hasCareerNetKey": bool(CAREERNET_KEY),
                "model": OPENAI_MODEL,
            })

        if self.path.startswith("/api/careernet"):
            return self.careernet()

        return SimpleHTTPRequestHandler.do_GET(self)

    def careernet(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        keyword = (q.get("keyword") or [""])[0]
        kind = (q.get("kind") or ["학과"])[0]

        if not CAREERNET_KEY:
            return self.send_json(200, {"error": ".env 에 CAREERNET_API_KEY 가 없습니다."})

        params = {
            "apiKey": CAREERNET_KEY,
            "svcType": "api",
            "contentType": "json",
        }
        if kind == "직업":
            params.update({"svcCode": "JOB", "gubun": "job_dic_list", "searchJobNm": keyword})
        else:
            params.update({"svcCode": "MAJOR", "gubun": "univ_list", "searchTitle": keyword})

        url = "https://www.career.go.kr/cnet/openapi/getOpenApi?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            return self.send_json(200, data)
        except Exception as e:
            return self.send_json(200, {"error": "커리어넷 호출 실패: %s" % e})

    # ---------- POST ----------
    def do_POST(self):
        if not self.path.startswith("/api/openai"):
            return self.send_error(404)

        if not OPENAI_KEY:
            return self.send_json(200, {"error": {"message":
                ".env 에 OPENAI_API_KEY 가 없습니다. 파일을 확인하고 서버를 다시 켜세요."}})

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self.send_json(400, {"error": {"message": "잘못된 요청 본문"}})

        payload.setdefault("model", OPENAI_MODEL)

        try:
            status, body = post_json(
                "https://api.openai.com/v1/chat/completions",
                payload,
                {"Content-Type": "application/json", "Authorization": "Bearer " + OPENAI_KEY},
            )
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            self.send_json(200, {"error": {"message": "OpenAI %s · %s" % (e.code, detail)}})
        except Exception as e:
            self.send_json(200, {"error": {"message":
                "OpenAI 서버에 연결하지 못했습니다: %s (방화벽·VPN·프록시 확인)" % e}})


if __name__ == "__main__":
    print("=" * 52)
    print("  미디어 진로 도우미")
    print("  주소   http://localhost:%d" % PORT)
    print("  모델   %s" % OPENAI_MODEL)
    print("  키     OpenAI %s / 커리어넷 %s"
          % ("있음" if OPENAI_KEY else "없음", "있음" if CAREERNET_KEY else "없음"))
    print("  종료   Ctrl+C")
    print("=" * 52)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
