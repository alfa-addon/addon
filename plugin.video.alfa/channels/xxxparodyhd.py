# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'https://xxxparodyhd.net'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/genre/clips-scenes/"))
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/genre/new-release/"))
    itemlist.append( Item(channel=item.channel, title="Parodias" , action="lista", url=host + "/genre/parodies/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
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
    if item.title == "Canal" :
        data = scrapertools.find_single_match(data,'>Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data,'>Categories</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div data-movie-id="\d+".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'oldtitle="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?rel="tag">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedyear in matches:
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot, infoLabels={'year':scrapedyear}) )
    next_page = scrapertools.find_single_match(data,'<li class=\'active\'>.*?href=\'([^\']+)\'>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = ' - on ([^"]+)" href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle,url in matches:
        itemlist.append( Item(channel=item.channel, action="play", title = "%s", contentTitle=item.title, url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    logger.debug(itemlist)
    a = len (itemlist)
    for i in itemlist:
        if a < 1:
            return []
        if 'clipwatching' in i.url:
            res = ""
        elif 'mangovideo' in i.url:
            res = ""
        else:
            res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue