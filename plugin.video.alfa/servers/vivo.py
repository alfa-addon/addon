# Conector Vivo By Alfa development Group
# --------------------------------------------------------

import re
import base64
from core import httptools
from core import scrapertools
from platformcode import logger



def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url)

    if data.code == 404:
        return False, "[Vivo] El archivo no existe o  ha sido borrado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    enc_data = scrapertools.find_single_match(data, "Core.InitializeStream \('(.*?)'\)")
    logger.debug(enc_data)
    dec_data = base64.b64decode(enc_data)

    logger.debug(dec_data)

    for url in eval(dec_data):
        video_urls.append(['vivo', url])

    return video_urls
