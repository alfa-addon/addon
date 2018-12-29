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

host = 'http://czechvideo.org'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/tags/%s/" % texto
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
    data = scrapertools.get_match(data,'<ul class="cat_menu" id="cat_menu_c0">(.*?)</ul>')
    patron  = '<li><a href="(.*?)".*?>(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="short-story">.*?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)".*?div class="short-time">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        scrapedthumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<del><a href="([^"]+)">Next</a></del>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    data = scrapertools.cachePage(item.url)
    url = scrapertools.find_single_match(data,'<iframe src=.*?<iframe src="([^"]+)"')
    url = "http:" + url
    itemlist = servertools.find_video_items(data=url)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

