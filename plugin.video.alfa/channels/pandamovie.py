# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host= 'https://pandamovies.pw'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/list-movies"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/list-movies"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/list-movies"))
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
        itemlist = []
        data = scrapertools.cache_page(item.url)
        if item.title == "Categorias" :
            data = scrapertools.get_match(data,'<a href="#">Genres</a>(.*?)</ul>')
        else:
            data = scrapertools.get_match(data,'<a href="#">Studios</a>(.*?)</ul>')
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
        patron  = '<li><a title=".*?" href="([^"]+)">([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            scrapedurl = scrapedurl.replace("https:", "")
            scrapedurl = "https:" + scrapedurl
            itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                                  thumbnail=scrapedthumbnail , plot=scrapedplot) )
        return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron = '<a class="clip-link" title="([^"]+)"  href="([^"]+)".*?'
    patron += 'src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail,
                              plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page =="":
        next_page = scrapertools.find_single_match(data,'<a.*?href="([^"]+)" >Next &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist

