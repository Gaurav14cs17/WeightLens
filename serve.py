#!/usr/bin/env python3
"""WeightLens Development Server — serves with no-cache headers and CORS."""
import http.server
import os
import sys

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"  {args[0]}", flush=True)

if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
    port = 8080
    print(f'\n  WeightLens running at http://localhost:{port}', flush=True)
    print(f'  Serving from: {os.getcwd()}\n', flush=True)
    sys.stdout.flush()
    server = http.server.HTTPServer(('0.0.0.0', port), NoCacheHandler)
    server.serve_forever()
