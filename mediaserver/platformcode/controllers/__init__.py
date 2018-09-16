# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Módulo para acciones en el cliente HTML
# ------------------------------------------------------------

import os
from inspect import isclass

from controller import Controller
from platformcode import config, logger


def load_controllers():
    controllers = []
    path = os.path.join(config.get_runtime_path(),"platformcode", "controllers")
    for fname in os.listdir(path):
        mod, ext = os.path.splitext(fname)
        fname = os.path.join(path, fname)
        if os.path.isfile(fname) and ext == '.py' and not mod.startswith('_'):
            try:
                exec "import " + mod + " as controller"
            except:
                import traceback
                logger.error(traceback.format_exc())

            for c in dir(controller):
                cls = getattr(controller, c)

                if not c.startswith('_') and isclass(cls) and issubclass(cls, Controller) and Controller != cls:
                    controllers.append(cls)
    return controllers


controllers = load_controllers()


def find_controller(url):
    result = []
    for c in controllers:
        if c().match(url):
            return c
