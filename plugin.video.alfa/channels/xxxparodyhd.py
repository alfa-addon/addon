# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb

host = 'https://xxxparodyhd.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/genre/new-release/"))
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Parodias" , action="peliculas", url=host + "/genre/parodies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/genre/clips-scenes/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Canal" :
        data = scrapertools.get_match(data,'>Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.get_match(data,'<div class=\'sub-container\' style=\'display: none;\'><ul class=\'sub-menu\'>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div data-movie-id="\d+" class="ml-item">.*?<a href="([^"]+)".*?oldtitle="([^"]+)".*?<img src="([^"]+)".*?rel="tag">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,year in matches:
        scrapedplot = ""
        scrapedtitle = str(scrapedtitle) + " " + year
        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<li class=\'active\'>.*?href=\'([^\']+)\'>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist

