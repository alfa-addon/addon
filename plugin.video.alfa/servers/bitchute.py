# -*- coding: utf-8 -*-
from core import urlparse as alfa_urlparse
from core import httptools
from platformcode import logger
# import requests
import json

####  Genteclic    https://www.bitchute.com/embed/OGHzXgEzQEw1 

server= "https://www.bitchute.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url)
    data = {}
    if response.code == 404:
        return False, "[bitchute] El fichero no existe o ha sido borrado"
    
    post_url= "https://api.bitchute.com/api/beta/video/media"
    id = page_url.split("embed/")[-1]
    post = {"video_id": id}
    headers = {'Content-Type': 'application/json', 'Referer': page_url, 'Origin': server}
    response = httptools.downloadpage(post_url, post=json.dumps(post), headers=headers)
    if response.code != 200 or not isinstance(response.json, dict) or not response.json.get('media_url'):
        return False, "[bitchute] No se pudo obtener el enlace del vídeo"
    data = response.json
    logger.debug(data)
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = data['media_url']
    url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}/'.format(u'{}'.format(server))})
    video_urls.append(["[bitchute]", url])
    return video_urls

