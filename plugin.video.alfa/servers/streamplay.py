# -*- coding: utf-8 -*-

import re
import base64
import urllib

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    if data == "File was deleted":
        return False, "[Streamplay] El archivo no existe o ha sido borrado"
    elif "Video is processing now" in data:
        return False, "[Streamplay] El archivo se está procesando"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    video_urls = []

    referer = re.sub(r"embed-|player-", "", page_url)[:-5]

    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data

    if data == "File was deleted":
        return "El archivo no existe o ha sido borrado"

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)

    sources = eval(scrapertools.find_single_match(unpacked, "sources=(\[[^\]]+\])"))
    for video_url in sources:
        video_url = decode_video_url(video_url, data)
        filename = scrapertools.get_filename_from_url(video_url)[-4:]
        if not video_url.endswith(".mpd"):
            video_urls.append([filename + " [streamplay]", video_url])

    video_urls.sort(key=lambda x: x[0], reverse=True)

    return video_urls


def decode_video_url(url, data):
    matches = re.compile("(var \w+\s*=\s*\[.*?\];\(function\(.*?)\n").findall(data)
    from lib import alfaresolver
    net = alfaresolver.EstructuraInicial(matches[0])
    net1 = alfaresolver.EstructuraInicial(net.data)
    data1 = ''.join(net1.data)
    match = re.compile("='(.*?);';eval", re.DOTALL).findall(data1)[0]
    matches = re.compile('data\("([e0-9]+)",(\d+)\)', re.DOTALL).findall(match)
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
