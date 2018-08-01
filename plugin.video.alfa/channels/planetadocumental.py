# -*- coding: utf-8 -*-
# -*- Channel Planeta Documental -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channelselector import get_thumb
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


IDIOMAS = {"Latino": "LAT"}
list_language = IDIOMAS.values()

list_quality = []

list_servers = ['gvideo']

host = "https://www.planetadocumental.com"

def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(item.clone(title="Últimos documentales", action="lista",
                               url= host,
                               thumbnail=get_thumb('lastest', auto=True)))
    itemlist.append(item.clone(title="Por genero", action="generos",
                               url= host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(title="Buscar...", action="search", thumbnail=get_thumb('search', auto=True)))

    return itemlist



def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'sub-menu elementor-nav-menu--dropdown(.*?)</ul')
    patron  = 'href="([^"]+).*?'
    patron += '>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(
                             action = "sub_list",
                             title = scrapedtitle,
                             url = scrapedurl,
                             ))
    return itemlist
    

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'Ver Online.*?iframe src="([^"]+)')
    if "/gd/" in url:
        data = httptools.downloadpage(url).data
        data = data.replace("file:",'"file":')
        url = scrapertools.find_single_match(data, 'source.*?file":\s*"([^"]+)')
        itemlist.append(item.clone(
                             action = "play",
                             server = "directo",
                             title = "Ver video " + item.title,
                             url = url
                             ))
    else:
        if url:
            itemlist.append(item.clone(
                                 action = "play",
                                 title = "Ver video " + item.title,
                                 url = url
                                 ))
            itemlist = servertools.get_servers_itemlist(itemlist)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'post__thumbnail__link.*?src="([^"]+).*?'
    patron += 'href="([^"]+).*?'
    patron += '>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action = "findvideos",
                                   contentTitle = scrapedtitle.strip(),
                                   title = scrapedtitle.strip(),
                                   url = scrapedurl,
                                   thumbnail = scrapedthumbnail
                                   ))
    return itemlist


def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = host + "/?s=" + texto
    item.extra = "busqueda"
    try:
        return sub_list(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_list(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'post-thumb-img-content post-thumb.*?src="([^"]+).*?'
    patron += 'href="([^"]+).*?'
    patron += '>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action = "findvideos",
                                   contentTitle = scrapedtitle,
                                   title = scrapedtitle.strip(),
                                   url = scrapedurl,
                                   thumbnail = scrapedthumbnail
                                   ))
    return itemlist
