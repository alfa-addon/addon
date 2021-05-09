# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# logger for mediaserver
# ------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import logging
# import logging.config
import os
from lib import xbmcaddon

__settings__ = xbmcaddon.Addon(id="plugin.video.alfa")

class ExtendedLogger(logging.Logger):
    def findCaller(self, stack_info=True, stacklevel=1):
        if PY3:
            f = logging.currentframe()
            #On some versions of IronPython, currentframe() returns None if
            #IronPython isn't run with -X:Frames.
            if f is not None:
                f = f.f_back
            orig_f = f
            while f and stacklevel > 1:
                f = f.f_back
                stacklevel -= 1
            if not f:
                f = orig_f
            rv = "(unknown file)", 0, "(unknown function)", None
            while hasattr(f, "f_code"):
                co = f.f_code
                filename = os.path.normcase(co.co_filename)
                if "logger" in filename:  # This line is modified.
                    f = f.f_back
                    continue
                sinfo = None
                if stack_info:
                    sio = io.StringIO()
                    sio.write('Stack (most recent call last):\n')
                    traceback.print_stack(f, file=sio)
                    sinfo = sio.getvalue()
                    if sinfo[-1] == '\n':
                        sinfo = sinfo[:-1]
                    sio.close()
                rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
                break
            return rv
        else:
            f = logging.currentframe().f_back.f_back
            rv = "(unknown file)", 0, "(unknown function)"
            while hasattr(f, "f_code"):
                co = f.f_code
                filename = os.path.normcase(co.co_filename)
                if "logger" in filename:  # This line is modified.
                    f = f.f_back
                    continue
                filename = filename + " " + co.co_name
                rv = (filename, f.f_lineno, co.co_name)
                break
            return rv

logging.setLoggerClass(ExtendedLogger)
logging.basicConfig(filename=os.path.join(__settings__.getAddonInfo("Profile"), "alfa.log"),
                    filemode='w',
                    format='%(levelname)-5s %(asctime)s [%(filename)-40s] %(message)s',
                    datefmt="%d/%m/%y-%H:%M:%S",
                    level=logging.DEBUG)

logger_object = logging.getLogger("mediaserver")

loggeractive = (__settings__.getSetting("debug") == True)


def log_enable(active):
    global loggeractive
    loggeractive = active


def info(texto="", force=False):
    if loggeractive or force:
        if not isinstance(texto, str):
            str(texto, "utf-8", "ignore")
        texto = texto.replace("\n", "\n" + " " * 67)
        logger_object.info(texto)


def debug(texto="", force=False):
    if loggeractive or force:
        if not isinstance(texto, str):
            str(texto, "utf-8", "ignore")
        texto = texto.replace("\n", "\n" + " " * 67)
        logger_object.debug(texto)


def error(texto=""):
    if not isinstance(texto, str):
        str(texto, "utf-8", "ignore")
    texto = texto.replace("\n", "\n" + " " * 67)
    logger_object.error(texto)


class WebErrorException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
