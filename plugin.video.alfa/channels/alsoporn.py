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

host = 'http://www.alsoporn.com/en'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host +"/g/All/new/1"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/g/All/top/1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/=%s/" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li><a href="([^"]+)" title="">.*?<span class="videos-count">([^"]+)</span><span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)" />'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = scrapedurl.replace("top", "new")
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="alsoporn_prev">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += '<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)" target="_self"><span class="alsoporn_page">NEXT</span></a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'([^\']+)\'')
    data = scrapertools.cachePage(scrapedurl)
    scrapedurl1 = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    scrapedurl1 = scrapedurl1.replace("//www.playercdn.com/ec/i2.php?", "https://www.synergytube.xyz/ec/i2.php?")
    data = scrapertools.cachePage(scrapedurl1)
    scrapedurl2 = scrapertools.find_single_match(data,'<source src="(.*?)" type=\'video/mp4\'>')
    itemlist.append(item.clone(action="play", title=item.title, fulltitle = item.title, url=scrapedurl2))
    return itemlist
