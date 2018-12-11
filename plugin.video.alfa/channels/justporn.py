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
from core import jsontools

host = 'http://xxx.justporno.tv'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/latest-updates/1/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas", action="peliculas", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar" , action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto
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
    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<div class="videos">(\d+) video.*?</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,numero in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + numero + ")"
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="http://xxx.justporno.tv/videos/(\d+)/.*?" title="([^"]+)" >.*?data-original="([^"]+)".*?<div class="duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
        scrapedurl = "http://xxx.justporno.tv/embed/" + scrapedurl
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = 'video_url: \'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        scrapedplot = ""
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
    return itemlist

