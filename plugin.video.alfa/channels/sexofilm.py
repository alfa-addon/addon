# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'http://sexofilm.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/xtreme-adult-wing/adult-dvds/"))
    itemlist.append( Item(channel=item.channel, title="Parody" , action="lista", url=host + "/xtreme-adult-wing/porn-parodies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/xtreme-adult-wing/porn-clips-movie-scene/"))
    itemlist.append( Item(channel=item.channel, title="SexMUSIC" , action="lista", url=host + "/topics/sexo-music-videos/"))
    itemlist.append( Item(channel=item.channel, title="Xshows" , action="lista", url=host + "/xshows/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    # itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url =host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Canal" :
        data = scrapertools.find_single_match(data,'>Best Porn Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data,'<div class="nav-wrap">(.*?)<ul class="sub-menu">')
        itemlist.append( Item(channel=item.channel, action="lista", title="Big tit", url="https://sexofilm.com/?s=big+tits"))
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl) )
    return itemlist


def anual(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li><a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<h2 class="post-title.*?title="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        plot = ""
        title = scrapedtitle.replace(" Porn DVD", "").replace("Permalink to ", "").replace(" Porn Movie", "")
        itemlist.append(item.clone(action="play", title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail, plot=plot) )
    next_page = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data,'<div class="entry-inner">.*?<source src="([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data,'<div class="entry-inner">.*?<source src=\'([^\']+)\'')
    itemlist = servertools.find_video_items(item.clone(url = item.url))
    if url:
        itemlist.append(item.clone(action="play", title=url, url=url))
    return itemlist


