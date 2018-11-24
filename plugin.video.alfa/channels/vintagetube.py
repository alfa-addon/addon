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

host = 'http://www.vintagetube.club'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/tube/last-1/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/tube/popular-1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto
    item.url =     item.url + "/popular-1/"
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
    patron  = '<div class="prev prev-ct">.*?<a href="(.*?)">.*?<img src="(.*?)".*?<span class="prev-tit">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedtitle = str(scrapedtitle)
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="prev">.*?<a href="(.*?)">.*?<img src="(.*?)">.*?<span class="prev-tit">(.*?)</span>.*?<div class="prev-dur"><span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + str(scrapedtitle)
        scrapedurl = scrapedurl.replace("/xxx.php?tube=", "")
        scrapedurl = host + scrapedurl
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    current_page = scrapertools.find_single_match(data,'<li><span class="page">(.*?)</span></li>')
    next_page = int(current_page) + 1
    url = item.url
    url_page = current_page + "/"
    url = url.replace(url_page, "")
    next_page_url = url + str(next_page)+"/"
    itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'(.*?)\'')
    if scrapedurl == "":
        scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
        scrapedurl = scrapedurl.replace ("http:", "")
        data = httptools.downloadpage("http:" + scrapedurl).data
    else:
        data = httptools.downloadpage(scrapedurl).data
        scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
        data = httptools.downloadpage("https:" + scrapedurl).data
    media_url = scrapertools.find_single_match(data,'<source src="(.*?)"')
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=media_url, fulltitle=media_url, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

