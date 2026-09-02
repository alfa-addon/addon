# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from lib import jsunhunt
from platformcode import logger
# import requests
import json

####  Genteclic    https://www.bitchute.com/embed/OGHzXgEzQEw1 

server= "https://www.bitchute.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404:
        return False, "[bitchute] El fichero no existe o ha sido borrado"
    
    post_url= "https://api.bitchute.com/api/beta/video/media"
    id = page_url.split("embed/")[-1]
    post = {"video_id": id}
    data = httptools.downloadpage(post_url, post=json.dumps(post), headers=headers).json
    logger.debug(data)
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = data['media_url']
    url += "|Referer=%s/" %server
    video_urls.append(["[bitchute]", url])
    return video_urls

