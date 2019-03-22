# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'http://xxxstreams.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url= host + "/category/full-porn-movie-stream/"))
    itemlist.append( Item(channel=item.channel, title="Clips" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data1 = scrapertools.get_match(data,'<h5>Popular Categories<br />(.*?)</aside>')
    if item.title == "Canal" :
        data1 = scrapertools.get_match(data,'>Top sites</a>(.*?)</ul>')
        data1 += scrapertools.get_match(data,'Downloads</h2>(.*?)</ul>')
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data1)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="entry-content">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<a href="([^<]+)".*?'
    patron += '<span class="screen-reader-text">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        if '/HD' in scrapedtitle : title= "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]" + "FullHD" + "[/COLOR] " + scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]" + "1080p" + "[/COLOR] " + scrapedtitle
        else: title = scrapedtitle
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &rarr;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista" , title="Next page >>", text_color="blue", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'--more-->(.*?)/a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)".*?class="external">(.*?)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, fulltitle=item.title,
                              url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

