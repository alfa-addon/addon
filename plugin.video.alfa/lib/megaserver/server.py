# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import traceback
from threading import Thread

from platformcode import logger

PY3 = sys.version_info[0] >= 3

if PY3:
    from http import server as BaseHTTPServer
    from socketserver import ThreadingMixIn
else:
    import BaseHTTPServer
    from SocketServer import ThreadingMixIn


class Server(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    daemon_threads = True
    timeout = 1
    def __init__(self, address, handler, client):
        BaseHTTPServer.HTTPServer.__init__(self,address,handler)
        self._client = client
        self.running = True
        self.request = None

    def stop(self):
        self.running = False

    def serve(self):
        while self.running:
            try:
                self.handle_request()
            except Exception:
                logger.error(traceback.format_exc())

    def run(self):
        t = Thread(target=self.serve, name='HTTP Server')
        t.daemon=self.daemon_threads
        t.start()

    def handle_error(self, request, client_address):
        if "socket.py" not in traceback.format_exc():
            logger.error(traceback.format_exc())