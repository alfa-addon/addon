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

host = 'http://porneq.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/videos/browse/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistos" , action="peliculas", url=host + "/videos/most-viewed/"))
    itemlist.append( Item(channel=item.channel, title="Mas Votado" , action="peliculas", url=host + "/videos/most-liked/"))
    itemlist.append( Item(channel=item.channel, title="Big Tits" , action="peliculas", url=host + "/show/big+tits&sort=w"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/show/%s" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="clip-link" data-id="\d+" title="([^"]+)" href="([^"]+)">.*?<img src="([^"]+)".*?<span class="timer">(.*?)</span></div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedtitle,scrapedurl,scrapedthumbnail,scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<nav id="page_nav"><a href="(.*?)"')
    if next_page_url!="":
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '"video-setup".*?file: "(.*?)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl in matches:
        scrapedurl = str(scrapedurl)
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                        thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

