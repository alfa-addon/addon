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

host = 'http://www.webpeliculasporno.com'


def mainlist(item):
    logger.info("pelisalacarta.webpeliculasporno mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimas" , action="peliculas", url= host))
    itemlist.append( Item(channel=item.channel, title="Mas vistas" , action="peliculas", url= host + "/?display=tube&filtre=views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url= host + "/?display=tube&filtre=rate"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url= host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
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
    itemlist = []
    data = scrapertools.cache_page(item.url)
    patron  = '<li class="cat-item [^>]+><a href="([^"]+)" >([^<]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<li class="border-radius-5 box-shadow">.*?'
    patron  += 'src="([^"]+)".*?'
    patron += '<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle ))
    next_page_url = scrapertools.find_single_match(data,'<li><a class="next page-numbers" href="([^"]+)">Next')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel, action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

