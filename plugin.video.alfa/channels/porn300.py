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

host = 'https://www.porn300.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/es/videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/es/mas-vistos/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/es/mas-votados/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/es/canales/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/es/pornostars/?sort=views"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/es/categorias/?sort=videos"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/es/buscar/?q=%s" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a itemprop="url" href="([^"]+)".*?title="([^"]+)">.*?<img itemprop="image" src=([^"]+) alt=.*?</svg>          ([^"]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a itemprop="url" href="([^"]+)".*?title="([^"]+)">.*?<img itemprop="image" src="([^"]+)".*?</svg>([^"]+)               </small>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a itemprop="url" href="([^"]+)" data-video-id="\d+" title="([^"]+)">.*?<img itemprop="thumbnailUrl" src="([^"]+)".*?</svg>\s+(.*?)         </li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl  in matches:
        url =  scrapedurl
    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist

