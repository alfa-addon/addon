# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host ='http://www.coomelonitas.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host+ "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="all"(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        title = scrapertools.find_single_match(match,'title="([^"]+)"')
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
        thumbnail = scrapertools.find_single_match(match,'<img src="([^"]+)"')
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, viewmode="movie") )
    next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" class="siguiente">')
    if next_page!="":
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist

def play(item):
    itemlist = []
    itemlist = servertools.find_video_items(item)
    a = len (itemlist)
    for i in itemlist:
        if a < 1:
            return []
        res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue

