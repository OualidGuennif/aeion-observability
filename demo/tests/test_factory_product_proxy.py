"""Actual HTTP canaries: the untrusted product cannot read or set host control cookies."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.product_proxy import handler, product_cookie


class ProxyTests(unittest.TestCase):
    def test_cookie_filter_refuses_domain_and_unrelated_response_cookies(self):
        self.assertIsNone(product_cookie('aeion_factory=control',response=True))
        self.assertIsNone(product_cookie('agora_session=product; Domain=127.0.0.1',response=True))
        self.assertIsNone(product_cookie('agora_session=product; aeion_factory=control',response=True))
        self.assertEqual(product_cookie('aeion_factory=control; next-auth.session-token=private; agora_session=product'),
                         'agora_session=product')
        self.assertIn('HttpOnly',product_cookie('agora_session=product',response=True))

    def test_real_proxy_strips_private_cookies_and_refuses_foreign_origin_and_framing(self):
        seen=[]
        class Candidate(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def do_GET(self):
                seen.append(dict(self.headers))
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Set-Cookie','aeion_factory=forged; Path=/')
                self.send_header('Set-Cookie','agora_session=forged-domain; Domain=127.0.0.1')
                self.send_header('Set-Cookie','agora_session=product; Path=/')
                self.send_header('Clear-Site-Data','"cookies"')
                self.send_header('ETag','fake\r\n\tSet-Cookie: aeion_factory=forged')
                self.end_headers();self.wfile.write(b'{"status":"ok"}')
        backend=ThreadingHTTPServer(('127.0.0.1',0),Candidate)
        proxy=ThreadingHTTPServer(('127.0.0.1',0),handler(backend.server_port))
        for server in (backend,proxy):
            threading.Thread(target=server.serve_forever,daemon=True).start()
            self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        def get(extra):
            connection=http.client.HTTPConnection('127.0.0.1',proxy.server_port,timeout=3)
            connection.request('GET','/healthz',headers={'Host':'127.0.0.1:8081',**extra})
            result=connection.getresponse();body=result.read();headers=result.getheaders()
            connection.close();return result.status,dict(headers),headers,body
        status,headers,pairs,body=get({'Cookie':'aeion_factory=private-canary; next-auth.session-token=private-canary; agora_session=product'})
        self.assertEqual(status,200);self.assertEqual(body,b'{"status":"ok"}')
        self.assertEqual(seen[0].get('Cookie'),'agora_session=product')
        self.assertNotIn('private-canary',str(seen))
        self.assertNotIn('Clear-Site-Data',headers)
        self.assertNotIn('aeion_factory',str(pairs))
        cookies=[v for k,v in pairs if k=='Set-Cookie']
        self.assertEqual(len(cookies),1);self.assertTrue(cookies[0].startswith('agora_session=product;'))
        self.assertEqual(get({'Origin':'http://127.0.0.1:8088'})[0],403)
        self.assertEqual(get({'Transfer-Encoding':'chunked'})[0],400)
        self.assertEqual(len(seen),1)


if __name__=='__main__': unittest.main()
