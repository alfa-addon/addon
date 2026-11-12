# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vixsrc (canal vitamina_mio, funcion vixsrc())
#
# El enlace que monta el canal es el playlist HLS de vixsrc, que:
#   - esta detras de Cloudflare: exige User-Agent de navegador (con el de Kodi, 403),
#   - va CIFRADO en AES-128 con la clave en /storage/enc.key, y
#   - su URL (/playlist/<id>?...) no acaba en .m3u8, asi que Alfa no elegia
#     inputstream.adaptive y moria con "error probing input format".
#
# HISTORIA (importa, para no volver a romperlo):
#   - 2026-10-12: inputstream.adaptive NO aplicaba el User-Agent del sufijo a la peticion de la CLAVE
#     (403 en kodi.log) aunque SI lo aplicaba al manifiesto y a los segmentos (issue #522). Se monto
#     la via LOCAL + ffmpegdirect, que reescribe el playlist en disco. Esa via SIGUE ABAJO
#     (get_video_url_local) por si la clave se vuelve a cerrar.
#   - 2026-10-15: medido de nuevo desde otra conexion: /storage/enc.key responde 200 CON Y SIN
#     cabeceras, y un segmento descifrado con esa clave empieza por 0x47 (MPEG-TS). Con la clave
#     publica se vuelve a la via REMOTA (get_video_url): mucho mas simple, basta el sufijo de
#     cabeceras para el manifiesto, las variantes y los segmentos.
# La clave esta detras de Cloudflare y YA cambio una vez: si vuelve el 403, la via local sigue ahi.
# --------------------------------------------------------

import os
import threading

try:
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
except ImportError:
    from http.server import SimpleHTTPRequestHandler, HTTPServer as ThreadingHTTPServer

from core import httptools
from core import urlparse
from platformcode import config, logger

# retries_cloudflare a 0: con 1, el solucionador de Cloudflare de Alfa se queda reintentando
# y la descarga de una pista no terminaba (visto en kodi.log 12:20, el intento se colgo)
kwargs = {"set_tls": True, "set_tls_min": True, "retries_cloudflare": 0,
          "ignore_response_code": True, "cf_assistant": False, "timeout": 10}

# Cloudflare de vixsrc: con el User-Agent de Kodi responde 403 y con uno de navegador 200.
# El canal ya no manda sufijo (Alfa lo re-pega al enlace resuelto y rompia el fichero local),
# asi que las cabeceras se ponen aqui.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
CABECERAS = {'User-Agent': UA, 'Referer': 'https://vixsrc.to/', 'Origin': 'https://vixsrc.to',
             'Accept': '*/*'}

# ajuste estandar de Alfa: el canal define DEBUG, pero un conector no lo hereda
DEBUG = config.get_setting("debug_report", default=False)


def _partir(page_url):
    """Separa url y cabeceras del sufijo |User-Agent=..&Referer=..&Origin=.."""
    if '|' not in page_url:
        return page_url, {}

    url, resto = page_url.split('|', 1)

    return url, dict(urlparse.parse_qsl(resto))


def _texto(url, cabeceras):
    """Descarga y devuelve texto (httptools puede dar bytes)."""
    datos = httptools.downloadpage(url, headers=cabeceras, **kwargs).data

    if isinstance(datos, bytes):
        datos = datos.decode('utf-8', 'replace')

    return datos or ''


def _carpeta():
    return config.get_data_path()


def _carpeta_vixsrc():
    """Carpeta propia: el servidor local solo sirve esto, no todo addon_data."""
    ruta = os.path.join(_carpeta(), 'vixsrc')
    if not os.path.isdir(ruta):
        os.makedirs(ruta)
    return ruta


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kw):
        SimpleHTTPRequestHandler.__init__(self, *args, directory=_carpeta_vixsrc(), **kw)

    def log_message(self, format, *args):
        pass


_server = None
_server_port = 0
_server_lock = threading.Lock()


def _servidor_local():
    """Servidor HTTP en 127.0.0.1 para que ffmpegdirect lea el master local."""
    global _server, _server_port

    with _server_lock:
        if _server is None:
            _server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
            _server.daemon_threads = True
            _server_port = _server.server_address[1]
            hilo = threading.Thread(target=_server.serve_forever, daemon=True)
            hilo.start()

        return _server_port


def _clave_local(clave_url, cabeceras, nombre):
    """Baja la clave y devuelve su URI local."""
    ruta = os.path.join(_carpeta_vixsrc(), 'vixsrc_key_%s.bin' % nombre)

    datos = httptools.downloadpage(clave_url, headers=cabeceras, **kwargs).data

    if not isinstance(datos, bytes):
        datos = datos.encode('latin-1', 'replace')

    fichero = open(ruta, 'wb')
    fichero.write(datos)
    fichero.close()

    # ruta RELATIVA: el manifiesto vive en la misma carpeta, asi que resuelve al fichero local
    # (mas compatible que file:/// , que el reproductor no seguia)
    return os.path.basename(ruta)


def _localiza_media(media, base, cabeceras, nombre):
    """Playlist de una pista: clave a fichero local y segmentos absolutos."""
    salida = []
    clave_hecha = False

    for linea in media.split('\n'):
        limpia = linea.strip()

        if limpia.startswith('#EXT-X-KEY') and 'URI="' in limpia:
            ini = limpia.index('URI="') + 5
            fin = limpia.index('"', ini)
            clave_url = urlparse.urljoin(base, limpia[ini:fin])

            if not clave_hecha:
                limpia = limpia[:ini] + _clave_local(clave_url, cabeceras, nombre) + limpia[fin:]
                clave_hecha = True

            salida.append(limpia)
            continue

        if limpia.startswith('#EXT-X-MAP') and 'URI="' in limpia:
            ini = limpia.index('URI="') + 5
            fin = limpia.index('"', ini)
            limpia = limpia[:ini] + urlparse.urljoin(base, limpia[ini:fin]) + limpia[fin:]

            salida.append(limpia)
            continue

        if limpia and not limpia.startswith('#'):
            salida.append(urlparse.urljoin(base, limpia))
        else:
            salida.append(limpia)

    # los segmentos van por red: si la clave no se pudo bajar, no sirve
    if not clave_hecha and '#EXT-X-KEY' in media:
        return ''

    return '\n'.join(salida)


def _localiza_master(master, base, cabeceras):
    """Master: localiza cada pista (#EXT-X-MEDIA) y cada variante."""
    salida = []
    indice = 0

    for linea in master.split('\n'):
        limpia = linea.strip()

        if (limpia.startswith('#EXT-X-MEDIA') or limpia.startswith('#EXT-X-STREAM-INF')) and 'URI="' in limpia:
            ini = limpia.index('URI="') + 5
            fin = limpia.index('"', ini)
            hija_url = urlparse.urljoin(base, limpia[ini:fin])

            indice += 1

            if DEBUG:
                logger.info("Vixsrc pista %d: %s" % (indice, hija_url[:110]))

            # solo las playlists (.m3u8) se reescriben; subtitulos .vtt/.srt se copian tal cual
            if '.m3u8' in hija_url or 'playlist' in hija_url:
                ruta = os.path.join(_carpeta_vixsrc(), 'vixsrc_pista_%d.m3u8' % indice)
                localizada = _localiza_media(_texto(hija_url, cabeceras), hija_url, cabeceras,
                                             'pista%d' % indice)

                if not localizada:
                    if DEBUG:
                        logger.error("Vixsrc pista %d NO se pudo localizar (queda REMOTA, dara 403): %s"
                                     % (indice, hija_url[:100]))
                    salida.append(limpia)
                    continue

                contenido = localizada

                if DEBUG:
                    logger.info("Vixsrc pista %d LOCALIZADA (%d bytes) -> %s"
                                % (indice, len(localizada), os.path.basename(ruta)))
            else:
                extension = hija_url.split('?')[0].rsplit('.', 1)[-1].lower() or 'txt'
                ruta = os.path.join(_carpeta_vixsrc(), 'vixsrc_pista_%d.%s' % (indice, extension))
                contenido = httptools.downloadpage(hija_url, headers=cabeceras, **kwargs).data

                if not isinstance(contenido, str):
                    contenido = contenido.decode('utf-8', 'replace')

            fichero = open(ruta, 'w')
            fichero.write(contenido)
            fichero.close()

            # El master se sirve por HTTP local: los hijos van RELATIVOS y el
            # servidor los resuelve contra /vixsrc_local.hls.
            salida.append(limpia[:ini] + os.path.basename(ruta) + limpia[fin:])
            continue

        # linea suelta = variante (una playlist .m3u8)
        if limpia and not limpia.startswith('#'):
            indice += 1
            ruta = os.path.join(_carpeta_vixsrc(), 'vixsrc_variante_%d.m3u8' % indice)
            variante_url = urlparse.urljoin(base, limpia)
            localizada = _localiza_media(_texto(variante_url, cabeceras), variante_url, cabeceras,
                                         'variante%d' % indice)

            if localizada:
                fichero = open(ruta, 'w')
                fichero.write(localizada)
                fichero.close()
                salida.append(os.path.basename(ruta))
                continue

        salida.append(limpia)

    return '\n'.join(salida)


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    url, cabeceras = _partir(page_url)

    for clave, valor in CABECERAS.items():
        cabeceras.setdefault(clave, valor)

    cabeceras['Range'] = 'bytes=0-100'

    response = httptools.downloadpage(url, headers=cabeceras, **kwargs)

    if response.code in (401, 403):
        # no hay ningun token: este host esta tras Cloudflare y rechaza la peticion
        return False, ("El servidor de vixsrc rechaza la peticion (%s, Cloudflare). " % response.code) + \
                      "Vuelve a intentarlo en un momento."

    if response.code == 429:
        return False, ("El servidor de vixsrc esta limitando las peticiones (429). "
                       "Espera un momento y vuelve a intentarlo.")

    if response.code >= 400 or not response.data:
        return False, ("El enlace de vixsrc no responde (%s)." % response.code)

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    # VIA LOCAL (2026-10-20). La clave /storage/enc.key vuelve a dar 403 a adaptive:
    # inputstream.adaptive no manda las cabeceras del sufijo a la peticion de la CLAVE
    # (xbmc/inputstream.adaptive#522) y Cloudflare la rechaza con el User-Agent de Kodi.
    # get_video_url_local la descarga con cabeceras de navegador y la deja en disco.
    # Requiere servers/vixsrc.json con "force_inputstream": "ffmpegdirect".
    return get_video_url_local(page_url, premium, user, password, video_password)


def get_video_url_local(page_url, premium=False, user="", password="", video_password=""):
    """Descarga el manifiesto, las pistas y las claves, y devuelve el .m3u8 local."""
    logger.info("(page_url='%s')" % page_url)

    etiqueta = u"[vixsrc] HLS"

    url, cabeceras = _partir(page_url)

    for clave, valor in CABECERAS.items():
        cabeceras.setdefault(clave, valor)

    try:
        master = _texto(url, cabeceras)

        if not master:
            return [[etiqueta, page_url]]

        local = _localiza_master(master, url, cabeceras)

        if not local:
            return [[etiqueta, page_url]]

        # 2026-10-20: extension .hls (no .m3u8) para que Kodi no lo trate como
        # lista de reproduccion. platformtools acepta .hls en la rama ffmpegdirect.
        ruta = os.path.join(_carpeta_vixsrc(), 'vixsrc_local.hls')
        fichero = open(ruta, 'w')
        fichero.write(local)
        fichero.close()
    except Exception as e:
        logger.error("vixsrc: no se pudo preparar la playlist local (%s)" % str(e))
        return [[etiqueta, page_url]]

    # 2026-10-20: se sirve por HTTP local (127.0.0.1) porque ffmpegdirect no
    # resuelve bien los hijos file:/// del master. El servidor solo expone
    # addon_data/vixsrc, no el resto de addon_data.
    puerto = _servidor_local()

    return [[etiqueta, 'http://127.0.0.1:%d/vixsrc_local.hls' % puerto]]
