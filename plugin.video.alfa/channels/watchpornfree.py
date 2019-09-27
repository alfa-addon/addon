# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

# https://playpornfree.org/    https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/

host = 'https://watchpornfree.info'

def mainlist(item):
    logger.info("")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/category/clips-scenes"))
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Parodia" , action="lista", url=host + "/category/parodies"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Año" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("")
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
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title == "Canal":
        data = scrapertools.find_single_match(data,'Scenes</a></li>(.*?)</ul>')
    if item.title == "Año":
        data = scrapertools.find_single_match(data,'Year</a>(.*?)</ul>')
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data,'>Categories</div>(.*?)</ul>')
    patron  = '<a href="([^"]+)".*?>([^"]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

def lista(item):
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<article class="TPost B">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="Title">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    itemlist = []
    itemlist = servertools.find_video_items(item)
    itemlist.reverse()
    a = len (itemlist)
    for i in itemlist:
        
        if a < 1:
            return []
        res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue

