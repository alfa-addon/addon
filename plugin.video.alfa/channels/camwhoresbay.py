# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb
from core import jsontools


host = 'https://www.camwhoresbay.com'

# EN CATALOGO Y BUSQUEDA LA PAGINACION FUNCIONA CON UN AJAX 

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="peliculas", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto
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
    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron  += '<img class="thumb" src="([^"]+)".*?'
    patron  += '<div class="videos">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video-item   ">.*?'
    patron += '<a href="([^"]+)" title="([^"]+)"  class="thumb">.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<i class="fa fa-clock-o"></i>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail, plot=plot,
                              contentTitle = title, infoLabels={'year':year} ))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>", text_color="blue",
                              url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data, 'video_alt_url3: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_alt_url2: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_alt_url: \'([^\']+)\'')
    if scrapedurl == "" :
        scrapedurl = scrapertools.find_single_match(data, 'video_url: \'([^\']+)\'')

    itemlist.append(Item(channel=item.channel, action="play", title=scrapedurl, fulltitle=item.title, url=scrapedurl,
                        thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist


