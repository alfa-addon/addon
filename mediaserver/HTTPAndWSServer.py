# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import random
import re
import threading
import time
import inspect
import traceback
from platformcode import platformtools
if PY3:
    from HTTPWebSocketsHandler_py3 import HTTPWebSocketsHandler
    from http.server import HTTPServer
else:
    from HTTPWebSocketsHandler import HTTPWebSocketsHandler
    from BaseHTTPServer import HTTPServer

from platformcode import config, logger
from core import jsontools as json

class MyHTTPServer(HTTPServer):
    daemon_threads = True

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        ID = "%032x" % (random.getrandbits(128))
        t = threading.Thread(target=self.process_request_thread,
                             args=(request, client_address), name=ID)
        t.daemon = self.daemon_threads
        t.start()

    def handle_error(self, request, client_address):
        import traceback
        if not "socket.py" in traceback.format_exc():
            logger.error(traceback.format_exc())

class Handler(HTTPWebSocketsHandler):
    def log_message(self, format, *args):
        # if sys.version_info[0:2] >= (3, 5, 0):
        #     caller_function = inspect.stack()[1].function
        # else:
        #     caller_function = inspect.stack()[1][3]
        caller_function = inspect.currentframe().f_back.f_code.co_name
        try:
            logger.info("[{}]".format(caller_function, ("%s - - %s\n" % (self.client_address[0], format%args)).strip()))
        except TypeError:
            logger.info("%s - - %s\n" % (self.client_address[0], args))

    # def log_error(self, format, *args):
        # logger.error(("%s - - %s\n" %(self.client_address[0], format%args)).strip())
        # self.log_message(self, format, )

    def sendMessage(self, message):
        self.send_message(message)

    def do_GET_HTTP(self):
        from platformcode import platformtools
        from platformcode import controllers
        # Control de accesos
        # Usuario = "user"
        # Password = "password"
        # ControlAcceso = False
        # import base64
        # Comprueba la clave
        # if ControlAcceso and self.headers.getheader('Authorization') != "Basic " + base64.b64encode(
        #                         Usuario + ":" + Password):
        #     self.send_response(401)
        #     self.send_header('WWW-Authenticate',
        #                      'Basic realm=\"' + config.get_localized_string(70264) + '\"')
        #     self.send_header('Content-type', 'text/html; charset=utf-8')
        #     self.end_headers()
        #     self.wfile.write('¡Los datos introducidos no son correctos!')
        #     return

        data = re.compile('/data/([^/]+)/([^/]+)/([^/]+)', re.DOTALL).findall(self.path)
        if data:
            data = data[0]
            if data[0] in platformtools.requests:
                c = platformtools.requests[data[0]]
                response = {"id": data[1], "result": data[2]}
                print(response)
                c.handler = self
                c.set_data(response)
                while data[0] in platformtools.requests and not self.wfile.closed:
                    time.sleep(1)
        else:
            if self.path == "": self.path = "/"

            # Busca el controller para la url
            controller = controllers.find_controller(self.path)
            if controller:
                try:
                    c = controller(self)
                    c.run(self.path)
                except:
                    if not "socket.py" in traceback.format_exc():
                        logger.error(traceback.format_exc())
                finally:
                    c.__del__()
                    del c
        return

    def on_ws_message(self, message):
        try:
            if message:
                json_message = json.load(message)

            if "request" in json_message:
                t = threading.Thread(target=run, args=[self.controller, json_message["request"].encode("utf8")], name=self.ID)
                t.setDaemon(True)
                t.start()

            elif "data" in json_message:
                if type(json_message["data"]["result"]) == unicode:
                    json_message["data"]["result"] = json_message["data"]["result"].encode("utf8")

                self.controller.data = json_message["data"]

        except:
            logger.error(traceback.format_exc())
            show_error_message(traceback.format_exc())

    def on_ws_connected(self):
        try:
            self.ID = "%032x" % (random.getrandbits(128))
            from platformcode.controllers.html import html
            self.controller = html(self, self.ID)
            self.server.fnc_info()
        except:
            logger.error(traceback.format_exc())

    def on_ws_closed(self):
        # self.controller.__del__()
        # del self.controller
        self.server.fnc_info()

    def address_string(self):
        # Disable reverse name lookups
        return self.client_address[:2][0]

PORT = config.get_setting("server.port")
server = None
waking_server = True
exc = None
attempts = 0
while waking_server:
    try:
        server = MyHTTPServer(('', int(PORT)), Handler)
        config.set_setting("server.port", PORT)
        waking_server = False
    except Exception as e:
        if attempts < 3 and True == False:
            PORT = input("El puerto {} está ocupado.\nIngresa otro número de puerto (ej. 8888): ".format(PORT))
            attempts += 1
        else:
            waking_server = False
            exc = e
if server == None:
    if isinstance(exc, Exception):
        raise exc
    else:
        raise Exception("No fue posible iniciar el servidor\n(¿Tienes permisos suficientes o hay algún cortafuegos bloqueando a Python?)")

def run(controller, path):
    try:
        controller.run(path)
    except:
        logger.error(traceback.format_exc())
        show_error_message(traceback.format_exc())

def show_error_message(err_info):
    from core import scrapertools
    patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\", "\\\\") + '([^.]+)\.py"'
    canal = scrapertools.find_single_match(err_info, patron)
    if canal:
        platformtools.dialog_ok(
            "Se ha producido un error en el canal " + canal,
            "Esto puede ser devido a varias razones: \n \
            - El servidor no está disponible, o no esta respondiendo.\n \
            - Cambios en el diseño de la web.\n \
            - Etc...\n \
            Comprueba el log para ver mas detalles del error.")
    else:
        platformtools.dialog_ok(
            "Se ha producido un error en Alfa",
            "Comprueba el log para ver mas detalles del error.")

def start(fnc_info):
    server.fnc_info = fnc_info
    threading.Thread(target=server.serve_forever).start()

def stop():
    server.socket.close()
    server.shutdown()
