# -*- coding: utf-8 -*-

import re
import urlparse
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://sexkino.to'

def mainlist(item):
    logger.info("pelisalacarta.sexkino mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="New" , action="peliculas", url= host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Año" , action="anual", url= host))
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
    logger.info("pelisalacarta.sexkino categorias")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<li class="cat-item cat-item-.*?<a href="(.*?)" >(.*?)</a> <i>(.*?)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,cantidad  in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " ("+cantidad+")"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def anual(item):
    logger.info("pelisalacarta.sexkino anual")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<li><a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.sexkino peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    #hay que hacer que coincida con el buscador
    patron  = '<article.*?<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)".*?>(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle,date in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + date + ")"
        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'resppages.*?<a href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def findvideos(item):
    logger.info("pelisalacarta.a0 findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<tr id=(.*?)</tr>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        url = scrapertools.find_single_match(match,'href="([^"]+)" target')
        title = scrapertools.find_single_match(match,'<td><img src=.*?> (.*?)</td>')
        itemlist.append(item.clone(action="play", title=title, url=url))
    patron  = '<iframe class="metaframe rptss" src="([^"]+)".*?<li><a class="options" href="#option-\d+">\s+(.*?)\s+<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle
        itemlist.append(item.clone(action="play", title=title, url=url))
    return itemlist


def play(item):
    logger.info("pelisalacarta.sexkino play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

