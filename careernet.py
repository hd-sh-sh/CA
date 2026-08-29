"""GET /api/careernet?keyword=&kind= — 브라우저 대신 커리어넷을 호출한다."""
import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def reply(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        key = os.environ.get("CAREERNET_API_KEY")
        if not key:
            return self.reply({"error": "환경 변수에 CAREERNET_API_KEY 가 없습니다."})

        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        keyword = (q.get("keyword") or [""])[0]
        kind = (q.get("kind") or ["학과"])[0]

        params = {"apiKey": key, "svcType": "api", "contentType": "json"}
        if kind == "직업":
            params.update({"svcCode": "JOB", "gubun": "job_dic_list", "searchJobNm": keyword})
        else:
            params.update({"svcCode": "MAJOR", "gubun": "univ_list", "searchTitle": keyword})

        url = "https://www.career.go.kr/cnet/openapi/getOpenApi?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                self.reply(json.loads(r.read().decode("utf-8", "replace")))
        except Exception as e:
            self.reply({"error": "커리어넷 호출 실패: %s" % e})
