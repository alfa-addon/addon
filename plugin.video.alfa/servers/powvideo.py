# -*- coding: utf-8 -*-

import re
import base64
import urllib

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]


def test_video_exists(page_url):
    referer = page_url.replace('iframe', 'preview')

    httptools.downloadpage(referer)

    data = httptools.downloadpage(page_url, headers={'referer': referer}).data
    if data == "File was deleted" or data == '':
        return False, "[powvideo] El video ha sido borrado"
    if 'function(p,a,c,k,e,' not in data:
        return False, "[powvideo] El video no está disponible"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    referer = page_url.replace('iframe', 'preview')

    data = httptools.downloadpage(page_url, headers={'referer': referer}).data

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)
    
    url = scrapertools.find_single_match(unpacked, "(?:src):\\\\'([^\\\\]+.mp4)\\\\'")
    url = decode_video_url(url, data)
    itemlist.append([".mp4" + " [powvideo]", url])

    itemlist.sort(key=lambda x: x[0], reverse=True)
    return itemlist
 
def decode_video_url(url, data):
    matches = re.compile("(var \w+\s*=\s*\[.*?\];\(function\(.*?)\n").findall(data)
    from lib import alfaresolver
    net = alfaresolver.EstructuraInicial(matches[0])
    net1 = alfaresolver.EstructuraInicial(net.data)
    data1 = ''.join(net1.data)
    match = re.compile("='(.*?);';eval", re.DOTALL).findall(data1)[0]
    matches = re.compile('data\("([a-z0-9]+)",(\d+)\)', re.DOTALL).findall(match)
    pos = []
    for e, val in matches:
        matches2 = re.compile(r'data\("%s"\)&(\d+)\]=r' % e, re.DOTALL).findall(match)
        for i in matches2:
            num1 = eval(val+"&"+i)
            pos.append(num1)
        matches2 = re.compile(r'data\("%s"\)>>(.*?),' % e, re.DOTALL).findall(match)
        for i in matches2:
            num2 = eval(val+">>"+i)
            pos.append(num2)
    tria = re.compile('[0-9a-z]{40,}', re.IGNORECASE).findall(url)[0]
    gira = list(tria[::-1])
    gira.pop(1)
    
    x1 = gira[pos[0]]
    x2 = gira[pos[1]]
    gira[pos[0]] = x2
    gira[pos[1]] = x1
    
    x1 = gira[pos[2]]
    x2 = gira[pos[3]]
    gira[pos[2]] = x2
    gira[pos[3]] = x1
    
    x1 = gira[pos[4]]
    x2 = gira[pos[5]]
    gira[pos[4]] = x2
    gira[pos[5]] = x1

    x = "".join(gira)

    return re.sub(tria, x, url)
