# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse
import re

from platformcode import config, logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gounlimited']
host = 'http://freepornstreams.org'    #es http://xxxstreams.org http://fullxxxmovies.net


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/free-full-porn-movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/videos/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

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
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title == "Categorias" :
        data = scrapertools.find_single_match(data,'filehosts</h3>(.*?)</aside>')
    else:
        data = scrapertools.find_single_match(data,'Popular Paysites</h3>(.*?)</aside>')
    patron  = '<a href="([^"]+)".*?>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        if not "Featured" in scrapedtitle:
            scrapedplot = ""
            scrapedthumbnail = ""
            scrapedurl = scrapedurl.replace ("http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=" , "")
            itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                                   thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" rel="bookmark">(.*?)</a>.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        if '/HD' in scrapedtitle : title= "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        elif 'SD' in scrapedtitle : title= "[COLOR red]" + "SD" + "[/COLOR] " + scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]" + "FullHD" + "[/COLOR] " + scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]" + "1080p" + "[/COLOR] " + scrapedtitle
        else: title = scrapedtitle
        thumbnail = scrapedthumbnail.replace("jpg#", "jpg")
        plot = ""
        if not "manyvids" in title:
            itemlist.append( Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot) )
    next_page = scrapertools.find_single_match(data, '<div class="nav-previous"><a href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" rel="nofollow[^<]+>(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        if not "ubiqfile" in url:
            itemlist.append(item.clone(action='play',title="%s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
