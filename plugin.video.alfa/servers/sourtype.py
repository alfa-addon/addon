# -*- coding: utf-8 -*-
import sys
import re

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from bs4 import BeautifulSoup

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global host, server, data
    domain = scrapertools.get_domain_from_url(page_url)
    host = "https://%s" % domain
    server = domain.split(".")[-2]
    # server = scrapertools.get_domain_from_url(page_url).split(".")[-2]
    if "send" in server:
        data = httptools.downloadpage(page_url, **kwargs).data
    response = httptools.downloadpage(page_url, **kwargs)
    data = response.data
    data = data.replace('\\u003C', '<').replace('\\u0022', '"').replace('\\u003E', '>').replace('\/', '/') # fapmeifyoucan entrega json
    if response.code == 404 or "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    try:
        if soup.video.source:
            tipo = soup.video.source['type']    # application/x-mpegURL & video/mp4
        matches  = soup.video.find_all('source', type=tipo)
    except Exception:
        matches = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" type="video/mp4"')
        for url in matches:
            if server not in url:
                url = urlparse.urljoin(page_url,url) #justporn
            # if "justporn" in page_url:
                # url = urlparse.urljoin(page_url,url)
            if not url.startswith("http"):
                url = "http:%s" % url
            
            url = urlparse.unquote(url)
            url += "|Referer=%s" % page_url
            video_urls.append(["[%s] mp4" %(server), url])
        return video_urls
    
    for elem in matches:
        url = elem['src']
        if "preview" in url: continue ## Monzr (multicanal Ezporn)
        if server not in url:
            url = urlparse.urljoin(page_url,url) #justporn
        if not url.startswith("http"):
            url = "http:%s" % url
        url = urlparse.unquote(url)
        
        if "multi=" in url:
            m3u8_source = url
            response = httptools.downloadpage(m3u8_source, **kwargs)
            logger.debug(response.code)
            # if response.code == 403:
                # post_url = "https://u3.bigfuck.tv/ah/sign"
                # post = {"urls":{"hls": m3u8_source}}
                # kwargs['headers'] = {
                                     # 'Referer': '%s/' %host,
                                     # 'Origin': host,
                                     # 'Content-Type': 'application/json;charset=UTF-8',
                                     # 'Accept-Encoding': 'gzip, deflate, br, zstd',
                                     # 'Sec-Fetch-Dest': 'empty',
                                     # 'Sec-Fetch-Mode': 'cors',
                                     # 'Sec-Fetch-Site': 'same-site',
                                     # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
                                    # }
                # logger.debug(kwargs['headers'])
                # datos = httptools.downloadpage(post_url, post=post, **kwargs).json
                # logger.debug(datos)
            datos = httptools.downloadpage(m3u8_source, **kwargs).data
            if sys.version_info[0] >= 3 and isinstance(datos, bytes):
                datos = "".join(chr(x) for x in bytes(datos))
            if datos:
                matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                ##matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                for quality, url in matches_m3u8:
                    url =urlparse.urljoin(m3u8_source,url)
                    # url += "|Referer=%s" % host
                    url += "|Referer=%s/&Origin=%s" % (host, host)
                    video_urls.append(['[%s] %s' % (server,quality), url])
        else:
            # url += "|Referer=%s" % host
            headers = httptools.default_headers.copy() 
            url += "|%s&Referer=%s/&Origin=%s" % (urlparse.urlencode(headers), host,host)
            # url += "|Referer=%s/&Origin=%s" % (host, host)
            video_urls.append(["[%s] mp4" %(server), url])
    return video_urls

