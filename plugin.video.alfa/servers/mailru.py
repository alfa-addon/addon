# -*- coding: utf-8 -*-

import re
from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger
from core import urlparse


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global vurl
    
    response = httptools.downloadpage(page_url)
    data = response.data
    
    if response.code == 404 or '"error":"video_not_found"' in data or '"error":"Can\'t find VideoInstance"' in data \
        or not '"metadataUrl":' in data:
        return False, "[Mail.ru] El archivo no existe o ha sido borrado"
    
    elif scrapertools.find_single_match(data, '"metadataUrl"\s*:\s*"([^"]+)"'):
        video = scrapertools.find_single_match(data, '"metadataUrl"\s*:\s*"([^"]+)"')
        vurl = urlparse.urljoin(page_url,video)
    elif "/+/" in page_url:
        vurl = page_url
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % (page_url))
    video_urls = []
    
    global vurl
    
    # Carga la página para coger las cookies
    # Carga los datos y los headers
    response = httptools.downloadpage(vurl)
    datos = httptools.downloadpage(vurl).json
    
    # La cookie video_key necesaria para poder visonar el video
    cookie_video_key = scrapertools.find_single_match(response.headers["set-cookie"], '(video_key=[a-f0-9]+)')
    
    # Formar url del video + cookie video_key
    for videos in datos['videos']:
        media_url = videos['url'] + "|Referer=https://my1.imgsmail.ru/r/video2/uvpv3.swf?75&Cookie=" + cookie_video_key
        if not media_url.startswith("http"):
            media_url = "http:" + media_url
        quality = " %s" % videos['key']
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + quality + " [mail.ru]", media_url])
    try:
        video_urls.sort(key=lambda video_urls: int(video_urls[0].rsplit(" ", 2)[1][:-1]))
    except:
        pass

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
