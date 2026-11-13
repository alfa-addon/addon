# -*- coding: utf-8 -*-
# -*- Server vidara -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import urlparse as alfa_urlparse
from core import httptools
from core import scrapertools
from platformcode import logger
from core.jsontools import json
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


##### canal leakslove  https://vidara.to/e/N3iNzTI8dcGqe   https://leakslove.com/therealemily34-redheaded-stepmom-in-virtual-sex/
##### canal Luxporn    https://vidara.to/e/BBk68zQGrvTDm   https://luxporn.cc/movies/boob-lovers-guide-to-big-tits-the-2-disc/
##### canal tubeonline https://vidara.to/e/lpIdrXIPq9VbU   https://www.tubeonline.net/pelicula/el-engano/

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}


host = "https://vidara.to/"


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    
    if response.code == 404  or "File Not Found" in data or "File is no longer available" in data:
        return False, "[vidara] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    id = scrapertools.find_single_match(page_url, '/e/([A-z0-9]+)')
    post_url = alfa_urlparse.build_url(host, 'api/stream')
    post = json.dumps({'filecode': id, 'device': 'web'})
    
    kwargs['headers'] = {
                         'Referer': page_url,
                         'Content-Type':'application/json'
                        }
    
    data_json = httptools.downloadpage(post_url, post=post, **kwargs).json
    url = data_json.get('streaming_url', '')
    if url:
        video_urls.append(["[vidara]", url])
    
    return video_urls

