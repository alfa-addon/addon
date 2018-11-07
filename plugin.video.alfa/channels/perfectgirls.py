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

host = 'http://www.perfectgirls.net'


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
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li class="additional_list__item"><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        url = urlparse.urljoin(item.url,scrapedurl) + "/1"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=url , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="list__item_link"><a href="([^"]+)" title="([^"]+)">.*?data-original="([^"]+)".*?<time>([^"]+)</time>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,time in matches:
        plot = ""
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + "[/COLOR]  " + scrapedtitle
        scrapedthumbnail = "http:" + scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page = scrapertools.find_single_match(data, '<a class="btn_wrapper__btn" href="([^"]+)">Next</a></li>')
    if next_page:
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>" , text_color="blue", url=next_page ))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)" res="\d+" label="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle  in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
    return itemlist

