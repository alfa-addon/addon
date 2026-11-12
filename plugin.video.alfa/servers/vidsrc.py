# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidsrc (canal vitamina_mio, funcion vidsrc())
#
# Los enlaces los monta el canal: son playlists HLS (.m3u8) de un host que cambia
# en cada ventana de 5 minutos y que exigen el token de <origen>/generate.php.
# El server 'directo' no vale: Kodi intenta reproducir el .m3u8 con su reproductor
# interno y muere con "eof reading from demuxer" (visto en kodi.log el 2026-10-12).
# Este conector acepta el enlace y fuerza inputstream.adaptive (ver el .json).
# --------------------------------------------------------

from core import httptools
from core import urlparse
from platformcode import logger

kwargs = {"set_tls": True, "set_tls_min": True, "retries_cloudflare": 0,
          "ignore_response_code": True, "cf_assistant": False, "timeout": 10}


def _partir(page_url):
    """Separa url y cabeceras del sufijo |Referer=..&Origin=.."""
    if '|' not in page_url:
        return page_url, {}

    url, resto = page_url.split('|', 1)

    return url, dict(urlparse.parse_qsl(resto))


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    if page_url.startswith('vidsrc://'):
        # el canal no pudo descifrar los enlaces (sin pywasm y sin asistente): el aviso se da
        # aqui, al pulsar, no en la lista
        return False, ("vidsrc necesita el Asistente de Alfa (o un Kodi con Python 3.10+): "
                       "sin el no se pueden descifrar los enlaces del reproductor.")

    url, cabeceras = _partir(page_url)

    # Range corto: asi la comprobacion no se baja el manifiesto entero ni los segmentos
    cabeceras['Range'] = 'bytes=0-100'

    response = httptools.downloadpage(url, headers=cabeceras, **kwargs)

    if response.code in (401, 403):
        return False, ("El host de vidsrc rechaza el enlace (%s): el token ha caducado o no "
                       "se pudo obtener. Vuelve a intentarlo desde el canal." % response.code)

    if response.code == 429:
        return False, ("El host de vidsrc esta limitando las peticiones (429). "
                       "Espera un momento y vuelve a intentarlo.")

    if response.code >= 400 or not response.data:
        return False, ("El enlace de vidsrc no responde (%s)." % response.code)

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    # el enlace va tal cual: es una playlist HLS con su token
    return [["[vidsrc] .m3u8", page_url]]
