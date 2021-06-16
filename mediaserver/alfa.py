#! /usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Launcher
# ------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import threading
import time
from functools import wraps
# Requerido para el ejecutable en windows
if PY3:
    import http.server as SimpleHTTPServer
else:
    import SimpleHTTPServer

sys.dont_write_bytecode = True
from platformcode import config

sys.path.append(os.path.join(config.get_runtime_path(), 'lib'))
from platformcode import platformtools, logger
import HTTPAndWSServer

http_port = config.get_setting("server.port")
myip = config.get_local_ip()
version = config.get_addon_version()


def thread_name_wrap(func):
    @wraps(func)
    def bar(*args, **kw):
        if "name" not in kw:
            kw['name'] = threading.current_thread().name
        return func(*args, **kw)

    return bar


threading.Thread.__init__ = thread_name_wrap(threading.Thread.__init__)

# if sys.version_info < (2, 7, 11):
#     import ssl

#     ssl._create_default_https_context = ssl._create_unverified_context
# os.system('@echo off')

def show_info():
    os.system('cls' if os.name == 'nt' else 'clear')
    # os.system('echo Reloading...')
    print("--------------------------------------------------------------------")
    print("Alfa %s Iniciado" % version)
    print("La URL para acceder es http://%s:%s" % (myip, http_port))
    print("--------------------------------------------------------------------")
    print("Runtime Path      : " + config.get_runtime_path())
    print("Data Path         : " + config.get_data_path())
    print("Download Path     : " + config.get_setting("downloadpath"))
    print("DownloadList Path : " + config.get_setting("downloadlistpath"))
    print("Bookmark Path     : " + config.get_setting("bookmarkpath"))
    print("Videolibrary Path : " + config.get_setting("videolibrarypath"))
    print("--------------------------------------------------------------------")
    controllers = platformtools.controllers
    for a in controllers:
        try:
            print(platformtools.controllers[a].controller.client_ip + " - (" + platformtools.controllers[a].controller.name + ")")
        except Exception as e:
            print(e)


def start():
    logger.info("server init {}...".format(sys.version_info[0:2]))
    config.verify_directories_created()
    if PY3:
        from platformcode import custom_code
        custom_code.marshal_check()
    try:
        HTTPAndWSServer.start(show_info)

        # Da por levantado el servicio
        logger.info("--------------------------------------------------------------------")
        logger.info("Alfa %s Iniciado" % version)
        logger.info("La URL para acceder es http://%s:%s" % (myip, http_port))
        logger.info("--------------------------------------------------------------------")
        logger.info("Runtime Path      : " + config.get_runtime_path())
        logger.info("Data Path         : " + config.get_data_path())
        logger.info("Download Path     : " + config.get_setting("downloadpath"))
        logger.info("DownloadList Path : " + config.get_setting("downloadlistpath"))
        logger.info("Bookmark Path     : " + config.get_setting("bookmarkpath"))
        logger.info("VideoLibrary Path : " + config.get_setting("videolibrarypath"))
        logger.info("--------------------------------------------------------------------")
        show_info()

        # Identifica la dirección Proxy y la lista de alternativas
        if not PY3:
            from core import proxytools
        else:
            from core import proxytools_py3 as proxytools
           
        proxytools.get_proxy_list()

        flag = True
        while flag:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Deteniendo el servidor HTTP...')
        HTTPAndWSServer.stop()
        print('Alfa Detenido')
        flag = False


# Inicia el programa
start()
