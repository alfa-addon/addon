# -*- coding: utf-8 -*-
"""Subtítulos temporales de Alfa, separados de las carpetas del usuario."""
import os
import shutil
import tempfile
import threading
import time

import xbmc
from platformcode import config, logger


def _root():
    return os.path.realpath(os.path.join(config.get_data_path(), 'temp_subtitles'))


def cleanup(session):
    path = os.path.realpath(session)
    if os.path.dirname(path) != _root() or not os.path.basename(path).startswith('session-'):
        return
    try:
        shutil.rmtree(path)
    except OSError:
        if os.path.exists(path):
            logger.error('No se pudo limpiar la sesión de subtítulos: %s' % path)


def create_session():
    root = _root()
    if not os.path.isdir(root):
        try:
            os.makedirs(root)
        except OSError:
            if not os.path.isdir(root):
                raise
    # Recuperar restos de cierres abruptos; solo dentro del espacio temporal propio.
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if name.startswith('session-') and os.path.isdir(path) and time.time() - os.path.getmtime(path) > 86400:
            cleanup(path)
    return tempfile.mkdtemp(prefix='session-', dir=root)


def _wait_and_cleanup(session):
    try:
        player = xbmc.Player()
        monitor = xbmc.Monitor()
        deadline = time.time() + 120
        while not player.isPlayingVideo():
            if time.time() >= deadline or monitor.waitForAbort(1):
                return
        playing_file = player.getPlayingFile()
        while player.isPlayingVideo() and player.getPlayingFile() == playing_file:
            if monitor.waitForAbort(1):
                break
    finally:
        cleanup(session)


def cleanup_after_playback(session):
    thread = threading.Thread(target=_wait_and_cleanup, args=(session,))
    thread.daemon = False
    thread.start()
