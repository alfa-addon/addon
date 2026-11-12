# -*- coding: utf-8 -*-
# -*- Server vidsonic -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import base64
import json
import sys

from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


##### canal Luxporn    https://vidsonic.net/e/t61ki9h9lz8u
##### vixeo.io es el mismo reproductor (medido el 2026-10-28): cambia el sitio donde
#####   viene el hexadecimal, que va dentro de data-config (JSON en base64) como "source".

host = "https://vidsonic.net/"


def _encoded(data):
    """El hexadecimal del que sale la url, venga de donde venga.

    vidsonic:  <script>_0x1 = '3234|6137|...'</script>   (pares hex separados por |)
    vixeo:     <div ... data-config="<base64 de {\"source\": \"3234|6137|...\"}>">
    """
    encoded = scrapertools.find_single_match(data, "_0x1 = '([^']+)'")
    if encoded:
        return encoded

    config = scrapertools.find_single_match(data, 'data-config="([^"]+)"')
    if not config:
        return ''

    try:
        crudo = base64.b64decode(config + '=' * (-len(config) % 4))
        datos = json.loads(crudo.decode('utf-8', 'replace'))
        return datos.get('source', '') or ''
    except Exception:
        logger.error("no se pudo leer data-config")
        return ''


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, encoded

    response = httptools.downloadpage(page_url)
    data = response.data
    encoded = _encoded(data)

    if response.code == 404  or "File Not Found" in data or "File is no longer available" in data:
        return False, "[vidsonic] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    global data, encoded

    try:
        url = decode(encoded) if encoded else ''
    except Exception as e:
        logger.error("no se pudo decodificar el enlace: %s" % e)
        url = ''

    if url:
        # La web puede devolver dos cosas (medido el 2026-10-21):
        #   - una url ABSOLUTA y firmada (HLS): https://sfy-01-fr.vidsonic.net/secure/.../master.m3u8?md5=...
        #   - una RUTA relativa (los mp4):      /uploads/<id>.mp4
        # Con la relativa, Kodi no puede reproducir nada: se hace absoluta contra el host del conector.
        if not url.startswith('http'):
            url = host.rstrip('/') + '/' + url.lstrip('/')
        video_urls.append(["[vidsonic]", "%s|Referer=%s" % (url, page_url)])

    return video_urls


def decode(s):
    clean = s.replace('|', '')
    out = ''

    for i in range(0, len(clean), 2):
        hex_pair = clean[i:i+2]
        out += chr(int(hex_pair, 16))

    return out[::-1]  # reverse string
