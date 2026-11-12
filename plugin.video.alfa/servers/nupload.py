# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector nupload By Alfa development Group
# --------------------------------------------------------
from core import urlparse as alfa_urlparse
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from core import httptools
from core import scrapertools
from platformcode import logger
import base64

# https://pelisflix1.click/pelicula/anaconda/   nuuup
# https://nupload.me/watch/vRFYtL86SCjpOEqeymyuQ8ra3jz3dGq7YyWX4OG9qLdKaM

host = "https://nupload.me"

def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url)
    if response.code == 404:
        return False, "[nupload] El archivo no existe o ha sido borrado"
    data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    if sys.version_info >= (3,):
        from lib import alfaresolver_py3 as alfaresolver
    else:
        from lib import alfaresolver as alfaresolver
    logger.info("url=" + page_url)
    video_urls = []
    
    sesz = scrapertools.find_single_match(data, 'sesz="([^"]+)"')
    z_var = scrapertools.find_single_match(data, 'var [A-z]+ = \[([^\]]+)')
    base = scrapertools.find_single_match(data, 'atob.*?- (\d+)\);')
    
    z_var = z_var.split(",")
    vid = alfaresolver.pasma(z_var, base)
    vid += "?s=%s" %sesz
    url = httptools.downloadpage(vid, follow_redirects=False, only_headers=True).headers.get("location", "")
    
    # headers = httptools.default_headers.copy()
    # url += "|%s&Referer=%s/&Origin=%s" % (urlparse.urlencode(headers), host, host)
    url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}/'.format(u'{}'.format(host)), 'Origin': u'{}'.format(host)})
    
    video_urls.append(['[nupload]', url])
    
    return video_urls
