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

host = 'https://www.analdin.com/es'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/más-reciente/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/más-visto/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/mejor-valorado/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categorías/"))
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


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<strong class="popup-title">Canales</strong>(.*?)<strong>Models</strong>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li><a class="item" href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                               thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel, action="catalogo", title="Página Siguiente >>", text_color="blue",
                               url=next_page_url) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="videos">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                               thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="popup-video-link" href="([^"]+)".*?'
    patron += 'thumb="([^"]+)".*?'
    patron += '<div class="duration">(.*?)</div>.*?'
    patron += '<strong class="title">\s*([^"]+)</strong>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtime,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail, plot=plot,
                              contentTitle = title, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>", text_color="blue",
                              url=next_page_url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'video_url: \'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl  in matches:
        url = scrapedurl
    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist

