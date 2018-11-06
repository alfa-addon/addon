# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host ='http://www.coomelonitas.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host+ "/?s=%s" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
        itemlist = []
        data = scrapertools.cache_page(item.url)
        #data = scrapertools.get_match(data,'<div class="sidetitle">Categorías</div>(.*?)</ul>')
		#<li class="cat-item cat-item-203077"><a href="http://www.coomelonitas.com/Categoria/asiaticas">ASIÁTICAS</a>
        patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">([^"]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)
        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
        return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="all"(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        title = scrapertools.find_single_match(match,'title="([^"]+)"')
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
        thumbnail = scrapertools.find_single_match(match,'<img src="([^"]+)"')
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="siguiente">')
    if next_page_url!="":
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist

