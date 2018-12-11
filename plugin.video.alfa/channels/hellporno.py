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

host = 'http://hellporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto
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
    patron  = '<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+) - Porn videos">.*?<span>(\d+) videos</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="video-thumb"><a href="([^"]+)" class="title".*?>([^"]+)</a>.*?<span class="time">([^<]+)</span>.*?<video poster="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,duracion,scrapedthumbnail  in matches:
        url = scrapedurl
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    
    #<source src="https://hellporno.com/get_file/6/b44b40165f7e95e4aeff4d9c33100447/202000/202198/202198_360p.mp4/?br=390" title="360p" type="video/mp4" />
    #<source data-fluid-hd src="https://hellporno.com/get_file/6/4ec6bbf8288123603094c76d9cd8ede4/202000/202198/202198.mp4/?br=1440" title="720p" type="video/mp4" />

    scrapedurl = scrapertools.find_single_match(data,'<source data-fluid-hd src="([^"]+)/?br=\d+"')
    if scrapedurl=="":
        scrapedurl = scrapertools.find_single_match(data,'<source src="([^"]+)/?br=\d+"')
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

