# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger
from core import urlparse


forced_proxy_opt = 'ProxySSL'

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'ignore_response_code': True, 'cf_assistant': False}


host = "https://cdn.loadvid.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    videoHash = scrapertools.find_single_match(response.data, "videoHash\s*=\s*'([^']+)'")
    token = scrapertools.find_single_match(response.data, 'name="csrf-token" content="([^"]+)"')
    if not videoHash or not token:
        return False, "[loadvid] El fichero no existe o ha sido borrado"
    
    url = "%s/videos/get-signed-url/%s" %(host,videoHash)
    
    kwargs['headers'] = {
                         'Referer': page_url,
                         'Origin': host,
                         'Set-Cookie': response.headers["set-cookie"],
                         'Accept' : 'application/json',
                         'X-CSRF-TOKEN': token
                        }
    response = httptools.downloadpage(url, post={}, **kwargs)
    if response.code == 404 or "<h2>WE ARE SORRY</h2>" in response.data or '<title>404 Not Found</title>' in response.data:
        return False, "[loadvid] El fichero no existe o ha sido borrado"
    
    data = response.json

    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    global data
    url = data['signed_url']
    url += "|%s" % urlparse.urlencode(kwargs['headers'])
    video_urls.append(['[loadvid]', url])
    return video_urls
