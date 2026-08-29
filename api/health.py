from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        res = {
            "status": "ok",
            "project": "Hệ thống Quản lý Garage Tích hợp AI (Garage VTV Automotive)",
            "environment": "Vercel Production Edge"
        }
        self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
