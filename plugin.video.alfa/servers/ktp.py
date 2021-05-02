# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vipporns By Alfa development Group
# --------------------------------------------------------
import re

from core import httptools
from core import scrapertools
from platformcode import logger

from lib.kt_player import decode

def test_video_exists(page_url):

    response = httptools.downloadpage(page_url)

    if response.code == 404 or \
    "Page not Found" in response.data \
    or "File was deleted" in response.data \
    or "video is a private" in response.data \
    or "is no longer available" in response.data:
        return False, "[ktplayer] El fichero no existe o ha sido borrado"

    global data, license_code
    data = response.data
    license_code = scrapertools.find_single_match(response.data, 'license_code:\s*(?:\'|")([^\,]+)(?:\'|")')
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []
    if "video_url_text" in data:
        patron = '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += '(?:video_url_text|video_alt_url_text|video_alt_url[0-9]*_text):\s*(?:\'|")([^\,]+)(?:\'|")'
    else:
        patron = 'video_url:\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += 'postfix:\s*(?:\'|")([^\,]+)(?:\'|")'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,quality in matches:
        if not "?login" in url and not "signup" in url:
            if "function/" in url:
                url = decode(url, license_code)
            # url += "?download=true"
            # url += "|verifypeer=false"
            logger.debug(quality + "  --  " + url)
            itemlist.append(['%s [ktplayer]' %quality, url])
        invert = ""
        if "LQ" in quality:
            invert= "true"
    if invert:
        itemlist.reverse()
    return itemlist

