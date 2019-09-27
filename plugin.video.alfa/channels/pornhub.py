﻿# -*- coding: utf-8 -*-

import re
import urlparse
from core import httptools
from core import servertools
from core import scrapertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", fanart=item.fanart,
                         url="http://es.pornhub.com/video?o=cm"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorias", fanart=item.fanart,
                         url="http://es.pornhub.com/categories"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", fanart=item.fanart,
                         url="http://es.pornhub.com/video/search?search=%s&o=mr"))
    return itemlist


def search(item, texto):
    logger.info()

    item.url = item.url % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="cat_pic" data-category=".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'data-thumb_url="(.*?)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '<var>(.*?)</var>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, cantidad in matches:
        if "?" in scrapedurl:
            url = urlparse.urljoin(item.url, scrapedurl + "&o=cm")
        else:
            url = urlparse.urljoin(item.url, scrapedurl + "?o=cm")
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                             fanart=scrapedthumbnail, thumbnail=scrapedthumbnail))
    itemlist.sort(key=lambda x: x.title)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    videodata = scrapertools.find_single_match(data, 'videos search-video-thumbs">(.*?)<div class="reset"></div>')
    patron = '<div class="phimage">.*?'
    patron += '<a href="([^"]+)" title="([^"]+).*?'
    patron += 'data-mediumthumb="([^"]+)".*?'
    patron += '<var class="duration">([^<]+)</var>(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(videodata)
    for url, scrapedtitle, thumbnail, duration, scrapedhd in matches:
        scrapedhd = scrapertools.find_single_match(scrapedhd, '<span class="hd-thumbnail">(.*?)</span>')
        if scrapedhd  == 'HD':
            title = "[COLOR yellow]" +duration+ "[/COLOR] " + "[COLOR red]" +scrapedhd+ "[/COLOR]  "+scrapedtitle
        else:
            title = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
        url = urlparse.urljoin(item.url, url)
        itemlist.append(
            Item(channel=item.channel, action="play", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail))
    if itemlist:
        # Paginador
        patron = '<li class="page_next"><a href="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if matches:
            url = urlparse.urljoin(item.url, matches[0].replace('&amp;', '&'))
            itemlist.append(
                Item(channel=item.channel, action="lista", title=">> Página siguiente", fanart=item.fanart,
                     url=url))
    return itemlist

def play(item):
    logger.info(item)
    itemlist = servertools.find_video_items(item.clone(url = item.url))
    return itemlist
    
