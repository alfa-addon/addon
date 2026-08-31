# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from lib import jsunhunt
from platformcode import logger
# import requests
import json

####  Siska    https://playmate.to/embed/eqaHQ2f6arTI 

server= "https://playmate.to"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url)
    data = response.data
    if response.code == 404:
        return False, "[playmate] El fichero no existe o ha sido borrado"
    
    headers = {
                # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                # 'Referer': page_url,
                # 'Origin': server,
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json, text/plain, */*',
                # 'Accept-Language': 'es-ES,es;q=0.9',
                # 'X-Requested-With': 'XMLHttpRequest'
               }
    
    post_url= "%s/api/s" %server
    id = page_url.split("embed/")[-1]
    post = {"c": id, "d": "web"}
    data = httptools.downloadpage(post_url, post=json.dumps(post), headers=headers).json
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = data['sx']
    video_urls.append(["[playmate]", url])
    return video_urls

