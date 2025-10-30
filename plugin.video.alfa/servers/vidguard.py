# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidguard By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from platformcode import logger
from lib import aadecode
import base64
import binascii
from core import jsontools

# Código original de Gujal00, ResolveURL
# https://github.com/Gujal00/ResolveURL/blob/d497c23a1cca21e17fe1e5a4bccf08063978910b/script.module.resolveurl/lib/resolveurl/plugins/vidguard.py#L38
# https://vembed.net/e/MAlwEMZea4OJ39X  #360 720 1080

def test_video_exists(page_url):
    global json_data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    
    r = re.search(r'eval\("window\.ADBLOCKER\s*=\s*false;\\n(.+?);"\);</script', data)
    if not r:
        return False, "[vidguard] No se ha podido encontrar el video"
    
    r = r.group(1).replace('\\u002b', '+')
    r = r.replace('\\u0027', "'")
    r = r.replace('\\u0022', '"')
    r = r.replace('\\/', '/')
    r = r.replace('\\\\', '\\')
    r = r.replace('\\"', '"')
    
    text_decode = aadecode.decode(r, alt=True)
    if "p,a,c,k,e,r" in text_decode:
        return False, "[vidguard] Video is being encode"

    try:
        js_data = text_decode[11:]
        json_data = jsontools.load(js_data)  #quita window.svg=
    except Exception as e:
        logger.error("Error loading JSON data: %s", e)
    
    if not json_data or not json_data.get('stream'):
        return False, "[vidguard] No se ha podido encontrar la URL del video"
    
    return True, ""


def get_video_url(page_url, video_password):
    global json_data
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = json_data['stream']
    if not url.startswith('https://'):
        url = re.sub(':/*', '://', url)
    url = sig_decode(url)
    url += "|Referer=%s" % page_url
    video_urls.append(["[vidguard]", url])
    return video_urls


    # Adapted from PHP code by vb6rocod
    # Copyright (c) 2019 vb6rocod
def sig_decode(url):
    sig = url.split('sig=')[1].split('&')[0]
    t = ''
    for v in binascii.unhexlify(sig):
        t += chr((v if isinstance(v, int) else ord(v)) ^ 2)
    t += "=="
    t = list(base64.b64decode(t)[:-5][::-1])
    for i in range(0, len(t) - 1, 2):
        t[i + 1], t[i] = t[i], t[i + 1]
    s=""
    for v in t:
        s += chr(v) if isinstance(v, int) else v
    url = url.replace(sig, s[:-5])
    return url