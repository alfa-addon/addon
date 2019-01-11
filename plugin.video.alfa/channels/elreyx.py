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

host = 'http://www.elreyx.com'


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/peliculasporno.html"))
    itemlist.append( Item(channel=item.channel, title="Escenas" , action="escenas", url=host + "/index.html"))
    itemlist.append( Item(channel=item.channel, title="Productora" , action="productora", url=host + "/index.html"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/peliculasporno.html"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search-%s" % texto + ".html"
    try:
        return escenas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def productora(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^<]+)" title="View Category ([^<]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        thumbnail="https:" + scrapedthumbnail
        url="https:" + scrapedurl
        itemlist.append( Item(channel=item.channel, action="escenas", title=scrapedtitle, url=url, thumbnail=thumbnail,
                              plot=scrapedplot) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<td><a href="([^<]+)" title="Movies ([^<]+)">.*?</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        url="https:" + scrapedurl
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=url,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def escenas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="notice_image">.*?<a title="([^"]+)" href="([^"]+)">.*?<img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        scrapedplot = ""
        url="https:" + scrapedurl
        thumbnail="https:" + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=url, thumbnail=thumbnail,
                               plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li class="float-xs-right"><a href=\'([^\']+)\' title=\'Pagina \d+\'>')
    if next_page == "":
        next_page = scrapertools.find_single_match(data,'<li><a href=\'([^\']+)\' title=\'Pagina \d+\'>&raquo;</a>')
    if next_page!= "":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="escenas", title="Página Siguiente >>", text_color="blue",
                              url=next_page) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="captura"><a title="([^"]+)" href="([^"]+)".*?><img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        scrapedplot = ""
        url="https:" + scrapedurl
        thumbnail="https:" + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=url, thumbnail=thumbnail,
                              plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a href=\'([^\']+)\' title=\'Pagina \d+\'>&raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel , action="peliculas", title="Página Siguiente >>", text_color="blue",
                              url=next_page) )
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')
    if url == "":
        url = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    data = httptools.downloadpage(url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

