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

host = 'https://www.youporn.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/browse/time/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/browse/views/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top_rated/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/alphabetical/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?query=%s" % texto
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
    data = scrapertools.get_match(data,'<a href="/pornstars/most_popular/" class="selected">All</a>(.*?)<i class=\'icon-menu-right\'></i></a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)".*?data-original="([^"]+)".*?<span class="porn-star-name">([^"]+)</span>.*?<span class="video-count">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" data-page-number=.*?>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class=\'row alphabetical\'.*?>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)".*?data-original="([^"]+)".*?<p>([^"]+)<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)" class=\'video-box-image\'.*?data-original="([^"]+)".*?<div class="video-box-title">([^"]+)</div>.*?<div class="video-duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<div class="prev-next"><a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = 'page_params.video.mediaDefinition =.*?"videoUrl":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl =  scrapedurl.replace("\/", "/")
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist


