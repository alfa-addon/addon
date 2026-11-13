# Conector KinoGer By Alfa development Group
# Thanks to ResolveURL for the logic
# --------------------------------------------------------

from core import urlparse as alfa_urlparse
import pyaes
import binascii
import json
import re
from core import httptools
from platformcode import logger

# https://xfuntaxy.upns.xyz/#onaa9w
# https://amg.upns.live/#x6diue
# https://88z.io/#tapgfp  xtapes
# https://flizzmovies.rpmvid.com/#lrkbfy  flizzmovies

KEY = b'\x6b\x69\x65\x6d\x74\x69\x65\x6e\x6d\x75\x61\x39\x31\x31\x63\x61'
IV = b'\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x6f\x69\x75\x79\x74\x72'


def _url_api(page_url):
    """Devuelve la url de la API y el origen del reproductor.

    El conector puede recibir la url de dos formas:
      - la del reproductor: https://host/#id      (la que entrega un canal, p. ej. flizzmovies)
      - la de la API:       https://host/api/v1/video?id=id   (la que arma el patron del .json)

    Con la del reproductor se pedia la PAGINA (HTML) y el descifrado reventaba con
    "Odd-length string" (medido el 2026-10-21 en kodi.log con flizzmovies). La pagina no
    sirve: los datos cifrados los da la API.
    """
    if '/api/v1/video' in page_url:
        return page_url, page_url.split('/api/v1/video')[0]

    match = re.search(r'(https?://[^/#?]+)/?#([A-Za-z0-9]+)', page_url or '')
    if match:
        host = match.group(1)
        return alfa_urlparse.build_url(host, '/api/v1/video', query=[('id', u'{}'.format(match.group(2)))]), host

    return page_url, (page_url or '').split('/#')[0].rstrip('/')


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data

    url_api, _host = _url_api(page_url)
    response = httptools.downloadpage(url_api)
    data = response.data
    if response.code == 404:
        return False,  "[%s] El fichero no existe o ha sido borrado" % page_url
    if not data:
        return False,  "[%s] La API no devolvio datos" % page_url
    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        # si no paso por test_video_exists (o el proceso es nuevo), se pide aqui la API
        if not globals().get('data'):
            test_video_exists(page_url)

        crudo = data.strip()
        # la respuesta acaba en salto de linea; si tras quitarlo queda impar, sobra un caracter
        if len(crudo) % 2:
            crudo = crudo[:-1]
        edata = binascii.unhexlify(crudo)
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(KEY, IV))
        ddata = decrypter.feed(edata)
        ddata += decrypter.feed()
        ddata = ddata.decode('utf-8')
        ddata = json.loads(ddata)
        url = ddata.get('source')
        if url:
            _url, host = _url_api(page_url)
            url = alfa_urlparse.add_url_headers(url, {'User-Agent': u'{}'.format(httptools.get_user_agent()), 'Referer': u'{}/'.format(u'{}'.format(host)), 'Origin': u'{}'.format(host)})
            video_urls.append(['[KinoGer] m3u8', url])
    except Exception as e:
        logger.error(e)

    return video_urls
