# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector pornhd8k (CDN de pornhd8k: cdn.pornhouse.me / cdn-aws-t11.cdnamz.me)
#
# El canal pornhd8k (channels/pornhd8k.py) monta el enlace del .m3u8 pidiendo el
# ajax de fuentes con token + cookie, y entrega la url con el sufijo
#   |User-Agent=<chrome>&Referer=<pagina real>
#
# Sin esas cabeceras el CDN NO da video: devuelve una secuencia de PNG (comprobado
# el 2026-10-12; Kodi abria el primer PNG y cerraba). Con ellas da video/mp2t.
#
# Por que existe este conector: cuando la url llega a platformtools sin servidor
# asignado, Alfa intenta resolverla con el server "directo" y, al no reconocer el
# CDN, sale "No se encontraron servidores soportados". Con este conector la url se
# reconoce, se conserva tal cual (con sus cabeceras) y el .json fuerza
# inputstream.adaptive.
# --------------------------------------------------------

from core import httptools, scrapertools
from core import urlparse
from platformcode import config, logger

kwargs = {"set_tls": True, "set_tls_min": True, "retries_cloudflare": 0,
          "ignore_response_code": True, "cf_assistant": False, "timeout": 10}

DOMINIOS = ('cdn.pornhouse.me', 'cdnamz.me')


def _partir(page_url):
    """Separa url y cabeceras del sufijo |User-Agent=..&Referer=.."""
    if '|' not in page_url:
        return page_url, {}

    url, resto = page_url.split('|', 1)

    return url, dict(urlparse.parse_qsl(resto))


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    url, cabeceras = _partir(page_url)

    if not any(dominio in url for dominio in DOMINIOS):
        return False, "El enlace no es de este servidor."

    # Range corto: la lista se pide entera pero solo hace falta saber que responde.
    cabeceras['Range'] = 'bytes=0-100'

    response = httptools.downloadpage(url, headers=cabeceras, **kwargs)

    if response.code == 429 or response.code == 403:
        return False, ("El CDN esta limitando las peticiones (%s). " % response.code) + \
                      "Espera un momento y vuelve a intentarlo."

    if response.code >= 400 or not response.data:
        return False, ("El enlace del CDN no responde (%s). " % response.code) + \
                      "Vuelve a intentarlo desde el canal."

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = []

    # El enlace se devuelve TAL CUAL (con su sufijo de cabeceras): el .json fuerza
    # inputstream.adaptive y platformtools las convierte en cabeceras del reproductor.
    etiqueta = "[pornhd8k] .m3u8" if '.m3u8' in page_url else "[pornhd8k] .mp4"

    video_urls.append([etiqueta, page_url])

    return video_urls
