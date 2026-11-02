"""Verify total deadline despite a server trickling bytes without newlines."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest
import urllib.request
from street_test import timed_lines

class SlowPeer(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def do_GET(self):
        self.send_response(200);self.end_headers()
        try:
            for _ in range(100):
                self.wfile.write(b'x');self.wfile.flush();time.sleep(.05)
        except OSError:pass

class DeadlineTest(unittest.TestCase):
    def test_unfinished_trickled_line_cannot_reset_budget(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),SlowPeer)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        start=time.monotonic()
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}',timeout=2) as response:
                with self.assertRaises(TimeoutError):list(timed_lines(response,start+.3))
            self.assertLess(time.monotonic()-start,1)
        finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main(verbosity=2)
