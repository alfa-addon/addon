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

host = 'http://xxxdan.com'

#NO SE REPRODUCE EL VIDEO QUE ENCUENTRA

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular30"))
    itemlist.append( Item(channel=item.channel, title="Dururacion" , action="peliculas", url=host + "/longest"))
    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/channel30/hd"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?query=%s" % texto
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
    for scrapedurl,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)" rel="tag".*?title="([^"]+)".*?data-original="([^"]+)".*?<span class="score">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = scrapedurl.replace("channel", "channel30")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li><figure>\s*<a href="([^"]+)" class="img\s*" title="([^"]+)".*?data-original="([^"]+)".*?<time datetime="\w+">([^"]+)</time>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = scrapedurl
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">&rarr;</a>')
    if next_page_url!="":
        next_page_url = next_page_url.replace("http://xxxdan.com/","")
        next_page_url = "/" + next_page_url
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    media_url = scrapertools.find_single_match(data, 'src:\'([^\']+)\'')
    media_url = media_url.replace("https","http")
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                        thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

