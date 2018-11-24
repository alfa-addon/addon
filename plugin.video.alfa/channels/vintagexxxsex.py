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

host = 'http://www.vintagexxxsex.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Top" , action="peliculas", url=host + "/all-top/1/"))
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/all-new/1/"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="peliculas", url=host + "/all-longest/1/"))
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
    patron  = '<li><a href="([^"]+)"><i class="fa fa-tag"></i>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="th">.*?<a href="([^"]+)".*?<img src="([^"]+)".*?<span class="th_nm">([^"]+)</span>.*?<i class="fa fa-clock-o"></i>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + " [/COLOR]" + scrapedtitle
        scrapedurl = scrapedurl.replace("/up.php?xxx=", "")
        scrapedurl = host + scrapedurl
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))


    next_page_url = scrapertools.find_single_match(data,'<li><span class="pg_nm">\d+</span></li>.*?href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )


    # else:
        # patron  = '<li><span class="pg_nm">\d+</span></li>.*?href="([^"]+)"'
        # next_page = re.compile(patron,re.DOTALL).findall(data)
        # next_page = item.url + next_page[0]
        # itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page[0] , text_color="blue", url=next_page[0] ) )
    return itemlist



def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<source src="(.*?)"')
    if scrapedurl == "":
        scrapedurl = "http:" + scrapertools.find_single_match(data,'<iframe src="(.*?)"')
        data = httptools.downloadpage(scrapedurl).data
        scrapedurl = scrapertools.find_single_match(data,'file: "(.*?)"')
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                    thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

