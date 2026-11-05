"""Trusted fixed-upstream product proxy: localhost ports do not isolate cookies.

Run in a separate container sharing only the product's owned network namespace. Only
this proxy port is published. The candidate application never receives Observatory or
Langfuse cookies and cannot replace them through Set-Cookie. No credentials or logs.
"""
from http.cookies import SimpleCookie, CookieError
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re

COOKIE = 'agora_session'
MAX_REQUEST = 16384
MAX_RESPONSE = 16 * 1024 * 1024
REQUEST_HEADERS = {'accept', 'accept-language', 'content-type', 'x-csrf-token', 'origin',
                   'if-none-match', 'if-modified-since', 'range'}
RESPONSE_HEADERS = {'content-type', 'content-encoding', 'cache-control', 'etag', 'last-modified',
                    'content-security-policy', 'referrer-policy', 'x-content-type-options',
                    'x-frame-options', 'location', 'content-range', 'accept-ranges', 'vary'}


def product_cookie(value, *, response=False):
    """Allow one bounded product cookie; never relay another host-wide cookie."""
    try:
        parsed = SimpleCookie(value or '')
    except CookieError:
        return None
    item = parsed.get(COOKIE)
    if item is None or not re.fullmatch(r'[A-Za-z0-9_.~=-]{0,4096}', item.value):
        return None
    if not response:
        return COOKIE + '=' + item.value
    if len(parsed) != 1 or item['domain']:
        return None
    item['path'] = '/'
    item['httponly'] = True
    item['samesite'] = 'Strict'
    return item.OutputString()


def handler(upstream_port=8080, public_host='127.0.0.1:8081'):
    class ProductProxy(BaseHTTPRequestHandler):
        # HTTP/1.0 closes each response: no pooled untrusted framing survives a request.
        server_version = 'Agora'
        sys_version = ''

        def log_message(self, *_):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def do_GET(self): self.forward()
        def do_HEAD(self): self.forward()
        def do_POST(self): self.forward()
        def do_PUT(self): self.forward()
        def do_PATCH(self): self.forward()
        def do_DELETE(self): self.forward()

        def forward(self):
            if (self.headers.get_all('Host') != [public_host]
                    or self.headers.get('Origin') not in (None, 'http://' + public_host)):
                self.send_error(403, 'Origin refused'); return
            if not self.path.startswith('/') or self.path.startswith('//') or any(ord(c)<32 for c in self.path):
                self.send_error(400, 'Path refused'); return
            lengths = self.headers.get_all('Content-Length', [])
            if (self.headers.get('Transfer-Encoding') is not None or len(lengths)>1
                    or lengths and not re.fullmatch(r'[0-9]{1,6}', lengths[0])):
                self.send_error(400, 'Framing refused'); return
            size = int(lengths[0]) if lengths else 0
            if size>MAX_REQUEST:
                self.send_error(413, 'Request too large'); return
            upstream = http.client.HTTPConnection('127.0.0.1', upstream_port, timeout=15)
            responded = False
            try:
                body = self.rfile.read(size)
                if len(body) != size:
                    self.send_error(400, 'Incomplete body'); return
                headers = {k:v for k,v in self.headers.items() if k.lower() in REQUEST_HEADERS}
                headers['Host'] = public_host
                headers['Connection'] = 'close'
                cookie = product_cookie('; '.join(self.headers.get_all('Cookie', [])))
                if cookie is not None: headers['Cookie'] = cookie
                upstream.request(self.command, self.path, body=body, headers=headers)
                result = upstream.getresponse()
                content = result.read(MAX_RESPONSE+1)
                if len(content)>MAX_RESPONSE:
                    self.send_error(502, 'Upstream response too large'); return
                responded = True
                self.send_response(result.status)
                for name,value in result.getheaders():
                    if any(ord(c)<32 or ord(c)==127 for c in value):
                        continue
                    if name.lower() in RESPONSE_HEADERS:
                        self.send_header(name,value)
                    elif name.lower() == 'set-cookie':
                        cookie = product_cookie(value,response=True)
                        if cookie is not None: self.send_header('Set-Cookie',cookie)
                self.send_header('Content-Length',str(len(content)))
                self.end_headers()
                if self.command != 'HEAD': self.wfile.write(content)
            except (OSError, http.client.HTTPException):
                if not responded:
                    try: self.send_error(502, 'Upstream unavailable')
                    except OSError: pass
                self.close_connection = True
            finally:
                upstream.close()
    return ProductProxy


if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0',8081),handler())
    server.daemon_threads = True
    server.serve_forever()
