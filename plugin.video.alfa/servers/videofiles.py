# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Videofiles By Alfa development Group
# --------------------------------------------------------

import re, time
from core import httptools, scrapertools
from platformcode import logger, platformtools

post = ""
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url)

    if not data.sucess or "Not Found" in data.data or "File was deleted" in data.data or "is no longer available" in data.data:
        return False, "[Videofiles] El archivo no existe o  ha sido borrado"
    data = data.data
    patron = 'hidden" name="([^"]+)" value="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for name, value in matches:
        post += "%s=%s&" % (name, value)
    global post
    post = post+"imhuman=Proceed+to+video"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    
    ts = time.time()
    post_ts = scrapertools.find_single_match(post, '-(\d{10})-')
    logger.info(post_ts)
    wait_time = int(post_ts) - ts
    wait_r = int(wait_time)
    platformtools.dialog_notification('Cargando videofiles', 'Espera de %s segundos requerida' % wait_r, sound=False)
    
    try:
        time.sleep(wait_time)
    except:
        time.sleep(10)

    new_data = httptools.downloadpage(page_url, post).data
    new_data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", new_data)
    logger.info("%s post=%s,/n%s" % (new_data, post, time.time()))
    patron = 'src: "([^"]+)", type: "([^"]+)", res: (\d+),'
    matches = re.compile(patron, re.DOTALL).findall(new_data)

    for url, ext, res in matches:
        res = res+'p'
        try:
            ext = ext.split("/")[1]
        except:
            pass
        video_urls.append(["%s (%s) [videofiles]" % (ext, res), url])

    return video_urls
