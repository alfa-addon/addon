# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidmoly By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools
from core import scrapertools
from platformcode import logger
import sys
import xbmcgui
window = xbmcgui.Window(10000) or None
cf_assistant = True if window and window.getProperty("is_assistant_installed") else False

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

kwargs = {"set_tls": False, "set_tls_min": False, "retries_cloudflare": 5, "ignore_response_code": True, 
          "CF_proxy_alt": False, "cf_assistant": False, "canonical": {}}
if cf_assistant:
    kwargs.update({"cf_assistant": cf_assistant, "cf_assistant_get_source": True, "retries_cloudflare": -1, 
                   "canonical_check": False,  "cf_no_blacklist": True, 
                   "host_alt": [r"(?i)(vidmoly\.\w+)"]})

patrones_url = [r'\{file:"([^"]+)"\}.*?label:\s"([^"]+)"', r'\{\s*file:\s*\'([^\']+)\'\s*\}[^$]+label:\s*"([^"]+)"']

# Error 403  captcha
# NO PIDE el captcha  https://vidmoly.me/\\1.html
# https://vidmoly.me/embed-15e4ac1yvzfm.html  >>>  https://vidmoly.me/w/15e4ac1yvzfm
#

def test_video_exists(page_url):
    global data, response

    logger.info("(page_url='%s')" % page_url)
    response = httptools.downloadpage(page_url, timeout=10, **kwargs)
    data = response.data

    if response.code == 403:
        return False, "[vidmoly] Error"
    if response.code in [404, 400, 429] or "/notice.php" in data:
        return False, "[vidmoly] El archivo no existe o ha sido borrado"
    if not response.sucess:
        return False, "[vidmoly] Error"

    for patron in patrones_url:
        if "&asn=0'" in str(scrapertools.find_single_match(data, patron)):
            response.proxy__ = ''
            break

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data

    domains_alt = ["\/\/transit-", "\/\/box-[^\/]+\/hls\d+\/"]
    url_alt = "biz/embed-"
    cf_challenges_list = ["https://challenges.cloudflare.com", "https://www.google.com/recaptcha/api2/anchor?"]
    for challenge in cf_challenges_list:
        if challenge in data:
            data = resolve_captcha(page_url.replace("me/", url_alt), data)
            break

    for patron in patrones_url:
        if scrapertools.find_single_match(data, patron):
            url, quality = scrapertools.find_single_match(data, patron)
            break
    else:
        url = quality = ''
        logger.error('Datos NO válidos: %s' % data)
        return [["[vidmoly] Error Captcha", ""]]

    for dom in domains_alt:
        if scrapertools.find_single_match(url, dom):
            break
    else:
        response_ = httptools.downloadpage(url, timeout=10, alfa_s=True, **kwargs)
        if not response_.sucess:
            domains_alt += [httptools.obtain_domain(url)]
    for dom in domains_alt:
        if scrapertools.find_single_match(url, dom):
            page_url = page_url.replace("me/", url_alt)
            response_ = httptools.downloadpage(page_url, timeout=10, hide_infobox=True, **kwargs)
            data = response_.data
            if response_.code == 403:
                return [["[vidmoly] Error Captcha", ""]]
            if response_.code == 404 or "/notice.php" in data:
                return [["[vidmoly] El archivo no existe o ha sido borrado", ""]]
            break

    logger.info("url=" + page_url)
    video_urls = []
    for patron in patrones_url:
        if scrapertools.find_single_match(data, patron):
            url, quality = scrapertools.find_single_match(data, patron)
            break
    else:
        url = quality = ''
        logger.error('Datos NO válidos: %s' % data)
        return [["[vidmoly] Error Captcha", ""]]

    url += "|Referer=%s" % page_url
    video_urls.append(['[vidmoly] m3u8 %s' % quality, url])

    # mp4_sources = re.compile('\{file:"([^"]+)",label:"([^"]+)"', re.DOTALL).findall(data)

    # for url, qlty in mp4_sources:
        # video_urls.append(['%s [vidmoly]' % qlty, url])

    return video_urls


def resolve_captcha(url, data):
    if not cf_assistant:
        return data

    if cf_assistant is True:
        req = httptools.downloadpage(url, timeout=10, hide_infobox=True, **kwargs)
        if req.sucess:
            data = req.data
    else:
        if PY3 and isinstance(req._content, bytes):
            data = "".join(chr(x) for x in bytes(req._content))
        else:
            data = req._content

    return data
