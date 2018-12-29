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

host = 'http://pornboss.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="     categorias" , action="categorias", url=host + "/category/movies/"))
    
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/category/clips/"))
    itemlist.append( Item(channel=item.channel, title="     categorias" , action="peliculas", url=host + "/category/clips/"))
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.url == host + "/category/movies/":
        data = scrapertools.get_match(data,'>Movies</a>(.*?)</ul>')
    else:
        data = scrapertools.get_match(data,'>Clips</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^"]+)</a>'
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
    patron  = '<article id="post-\d+".*?<img class="center cover" src="([^"]+)" alt="([^"]+)".*?<blockquote>.*?<a href=\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedthumbnail,scrapedtitle,scrapedurl in matches:
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page_url!="":
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist

def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

