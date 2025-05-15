# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from bs4 import BeautifulSoup

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global data
    
    data = httptools.downloadpage(page_url, **kwargs).json
    
    if data.get('message', ''):
        return False, "[camsoda] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    # data = httptools.downloadpage(page_url, **kwargs).json
    
    server = data['edge_servers']
    token = data['token']
    dir = data['stream_name']
    if dir == "":
        return False, "El video ha sido borrado o no existe"
    if "vide" in server[0]:
        url = "https://%s/cam/mp4:%s_h264_aac_480p/chunklist_w206153776.m3u8?token=%s"  %(server[0],dir,token)
    else:
        # url = "https://%s/%s_v1/tracks-v4a2/mono.m3u8?token=%s" %(server[0],dir,token)
        url = "https://%s/%s_v1/index.m3u8?token=%s" %(server[0],dir,token)
    # url += "|verifypeer=false"
    # url += "|Referer=%s" % page_url
    video_urls.append(["[camsoda]", url])
    return video_urls
