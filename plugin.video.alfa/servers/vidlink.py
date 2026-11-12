# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidlink (canal vitamina_mio, funcion vidlink())
#
# Los enlaces que monta el canal son ficheros .mp4 directos de un CDN
# (bcdn.hakunaymatata.com) que exige el Referer de vidlink.pro; el canal ya lo mete en
# el sufijo |Referer= del enlace.
# NO se fuerza inputstream.adaptive: son ficheros, no HLS.
# OJO (2026-10-12): ese CDN responde 429 Too Many Requests (probado con 6 combinaciones de
# cabeceras: sin Referer da 428, con Referer 429), tambien desde la IP del usuario, asi que
# estos enlaces aparecen en la lista pero no reproducen. No es un fallo del canal.
# --------------------------------------------------------

from core import httptools
from core import urlparse
from platformcode import logger

kwargs = {"set_tls": True, "set_tls_min": True, "retries_cloudflare": 0,
          "ignore_response_code": True, "cf_assistant": False, "timeout": 10}


def _partir(page_url):
    """Separa url y cabeceras del sufijo |Referer=..&Origin=.. (el CDN EXIGE ese Referer:
    sin el responde 428 Forbidden)."""
    if '|' not in page_url:
        return page_url, {}

    url, resto = page_url.split('|', 1)

    return url, dict(urlparse.parse_qsl(resto))


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    url, cabeceras = _partir(page_url)
    cabeceras['Range'] = 'bytes=0-100'

    response = httptools.downloadpage(url, headers=cabeceras, **kwargs)

    if response.code == 429:
        return False, ("El CDN de vidlink esta limitando las peticiones (429). "
                       "Espera un momento o usa otra fuente.")

    if response.code == 428:
        return False, ("El CDN de vidlink pide el Referer y no lo ha recibido (428). "
                       "Vuelve a intentarlo desde el canal.")

    if response.code >= 400 or not response.data:
        return False, ("El enlace de vidlink no responde (%s)." % response.code)

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    # el enlace va tal cual (ya lleva su Referer y su firma)
    return [["[vidlink] .mp4", page_url]]
