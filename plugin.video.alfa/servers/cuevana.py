# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from core import servertools
from platformcode import logger
from platformcode import platformtools
from bs4 import BeautifulSoup

forced_proxy_opt = 'ProxySSL'

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}


                                                                   # *
         # https://player.cuevana.is/player.php?h=rxPRsRSX4IlkyS1F21W5j07n8JksJAS6EwUrNvURFjy2VXBh1cfx6raW1PI9U7HE   CF
        # https://player.cuevana8.eu/player.php?h=rxPRsRSX4IlkyS1F21W5j07n8JksJAS6EwUrNvURFjy2VXBh1cfx6raW1PI9U7HE
# https://player.cuevana2espanol.net/player.php?h=rxPRsRSX4IlkyS1F21W5j9UVv4kB.pTPZQaJ977vfFTmvP.4LyUcpPCaLrgPQp6Z


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    if response.code == 404 or "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[Cuevana] El fichero no existe o ha sido borrado"

    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    devuelve = servertools.findvideos(page_url, True)
    if devuelve:
        url = devuelve[0][1]
        server = devuelve[0][2]
    video_url = servertools.resolve_video_urls_for_playing(server, url)
    if not video_url:
        platformtools.dialog_ok("Cuevana: Error", "Error en el servidor: %s" %server)
    return video_url[0]


