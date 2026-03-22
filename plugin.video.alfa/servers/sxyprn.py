# -*- coding: utf-8 -*-
import re
import base64
from core import httptools
from core import scrapertools
from platformcode import logger

def test_video_exists(page_url):
    logger.info()
    
    global data
    
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data:
        return False, "[sxyprn] El video ha sido borrado o no existe"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global data
    
    vnfo_raw = scrapertools.find_single_match(data, 'data-vnfo=\'{"\w+":"([^"]+)"')
    vnfo_raw= vnfo_raw.replace("\/", "/")
    url = generar_url_final(vnfo_raw)
    video_urls.append(["[sxyprn]", url])
    return video_urls



def generar_url_final(path_string, host="www.sxyprn.com"):
    tmp = path_string.split("/") 
    
    def ssut51(arg):
        digits = re.sub(r'[^0-9]', '', str(arg))
        return sum(int(d) for d in digits)
    
    def boo(ss, es):
        data = f"{ss}-{host}-{es}"
        b = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        return b.replace('+', '-').replace('/', '_').replace('=', '.')
    
    def preda(arg):
        deduction = ssut51(arg[6]) + ssut51(arg[7])
        arg[5] = str(int(arg[5]) - deduction)
        return arg
    
    token = boo(ssut51(tmp[6]), ssut51(tmp[7]))
    
    tmp[1] += "8/" + token
    
    tmp = preda(tmp)
    
    return f"https://{host}/" + "/".join(tmp[1:])