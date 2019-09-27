# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'http://xxxstreams.org' #es http://freepornstreams.org

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url= host + "/category/full-porn-movie-stream/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/category/new-porn-streaming/"))
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
    if item.title == "Categorias" :
        data1 = scrapertools.find_single_match(data,'>Top Tags</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Ethnic</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'>Kinky</a>(.*?)</ul>')
    if item.title == "Canal" :
        data1 = scrapertools.find_single_match(data,'>Top sites</a>(.*?)</ul>')
        data1 += scrapertools.find_single_match(data,'Downloads</h2>(.*?)</ul>')
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data1)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="entry-content">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<a href="([^<]+)".*?'
    patron += '<span class="screen-reader-text">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        if '/HD' in scrapedtitle : title= "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        elif 'SD' in scrapedtitle : title= "[COLOR red]" + "SD" + "[/COLOR] " + scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]" + "FullHD" + "[/COLOR] " + scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]" + "1080p" + "[/COLOR] " + scrapedtitle
        else: title = scrapedtitle
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                               fanart=scrapedthumbnail, thumbnail=scrapedthumbnail,plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &rarr;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista" , title="Next page >>", text_color="blue", url=next_page) )
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)"[^<]+>(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        if not "ubiqfile" in url:
            itemlist.append(item.clone(action='play',title="%s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" rel="nofollow"[^<]+>(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        if not "ubiqfile" in url:
            itemlist.append(item.clone(action='play',title="%s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    a = len (itemlist)
    for i in itemlist:
        
        if a < 1:
            return []
        res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue
            
            
