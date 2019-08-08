# -*- coding: utf-8 -*-

from monitor import Monitor

import traceback

try:
    import xbmc, xbmcgui
except:
    pass
from platformcode import config
LIBTORRENT_PATH = config.get_setting("libtorrent_path", server="torrent", default='')

try:
    e = ''
    e1 = ''
    e2 = ''
    pathname = ''
    try:
        import libtorrent as lt
        pathname = LIBTORRENT_PATH
    except Exception, e:
        try:
            import imp
            from ctypes import CDLL
            dll_path = os.path.join(LIBTORRENT_PATH, 'liblibtorrent.so')
            liblibtorrent = CDLL(dll_path)
            path_list = [LIBTORRENT_PATH, xbmc.translatePath('special://xbmc')]
            fp, pathname, description = imp.find_module('libtorrent', path_list)
            try:
                lt = imp.load_module('libtorrent', fp, pathname, description)
            finally:
                if fp: fp.close()
        
        except Exception, e1:
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
            from lib.python_libtorrent.python_libtorrent import get_libtorrent
            lt = get_libtorrent()

except Exception, e2:
    try:
        xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
        do = xbmcgui.Dialog()
        e = e1 or e2
        do.ok('ERROR en el cliente BT Libtorrent', 'Módulo no encontrado o imcompatible con el dispositivo.', 
                    'Reporte el fallo adjuntando un "log".', str(e))
    except:
        pass


class Dispatcher(Monitor):
    def __init__(self, client):
        super(Dispatcher, self).__init__(client)

    def do_start(self, th, ses):
        self._th = th
        self._ses = ses
        self.start()

    def run(self):
        if not self._ses:
            raise Exception('Invalid state, session is not initialized')

        while self.running:
            a = self._ses.wait_for_alert(1000)
            if a:
                alerts = self._ses.pop_alerts()
                for alert in alerts:
                    with self.lock:
                        for cb in self.listeners:
                            cb(lt.alert.what(alert), alert)
