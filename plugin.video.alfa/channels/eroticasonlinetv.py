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

host = 'http://www.peliculaseroticasonline.tv'

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
    patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)".*?>([^"]+)</a>'
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="movie-poster"><a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        plot = ""
        contentTitle = scrapedtitle
        url = urlparse.urljoin(item.url,scrapedurl)
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=scrapedtitle , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page = scrapertools.find_single_match(data, '<div class="naviright"><a href="([^"]+)">Siguiente &raquo;</a>')
    if next_page:
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>" , text_color="blue", url=next_page ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    url = urlparse.urljoin(item.url, url)
    data = httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    if url == "":
        url = scrapertools.find_single_match(data, 'window.location="([^"]+)"')
    itemlist = servertools.find_video_items(data=url)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

