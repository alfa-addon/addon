# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Logger (kodi)
# --------------------------------------------------------------------------------

import inspect

import xbmc
from platformcode import config

loggeractive = (config.get_setting("debug") == True)


def log_enable(active):
    global loggeractive
    loggeractive = active


def encode_log(message=""):
    # Unicode to utf8
    if type(message) == unicode:
        message = message.encode("utf8")

    # All encodings to utf8
    elif type(message) == str:
        message = unicode(message, "utf8", errors="replace").encode("utf8")

    # Objects to string
    else:
        message = str(message)

    return message


def get_caller(message=None):
    module = inspect.getmodule(inspect.currentframe().f_back.f_back)

    module = module.__name__

    function = inspect.currentframe().f_back.f_back.f_code.co_name

    if module == "__main__":
        module = "alfa"
    else:
        module = "alfa." + module
    if message:
        if module not in message:
            if function == "<module>":
                return module + " " + message
            else:
                return module + " [" + function + "] " + message
        else:
            return message
    else:
        if function == "<module>":
            return module
        else:
            return module + "." + function


def info(texto=""):
    if loggeractive:
        xbmc.log(get_caller(encode_log(texto)), xbmc.LOGNOTICE)


def debug(texto=""):
    if loggeractive:
        texto = "    [" + get_caller() + "] " + encode_log(texto)

        xbmc.log("######## DEBUG #########", xbmc.LOGNOTICE)
        xbmc.log(texto, xbmc.LOGNOTICE)


def error(texto=""):
    texto = "    [" + get_caller() + "] " + encode_log(texto)

    xbmc.log("######## ERROR #########", xbmc.LOGERROR)
    xbmc.log(texto, xbmc.LOGERROR)


class WebErrorException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
