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

host = 'http://pornboss.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/category/clips/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
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
    data = scrapertools.find_single_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu">(.*?)</ul>')
    patron  = '<li><a href=(.*?) class>([^<]+)</a>'
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
    patron = '<article id=item-\d+.*?'
    patron += '<img class="center cover" src=([^"]+) alt="([^"]+)".*?'
    patron += 'Duration:</strong>(.*?) / <strong>.*?'
    patron += '<a class=dlbtn href=([^"]+) target=_blank' 
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedtitle,duration,scrapedurl in matches:
        scrapedplot = ""
        title = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a href=([^<]+)><i class=uk-icon-angle-double-right>')
    if next_page!="":
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    url=scrapertools.find_single_match(data,'<span class="bottext">Streamcloud.eu</span>.*?href="([^"]+)"')
    url= "https://tolink.to" + url
    data = httptools.downloadpage(url).data
    patron = '<input type="hidden" name="id" value="([^"]+)">.*?'
    patron += '<input type="hidden" name="fname" value="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for id, url in matches:
        url= "http://streamcloud.eu/" + id + "/" + url
    itemlist = servertools.find_video_items(data=url)
    for item in itemlist:
        item.channel = "url"
        item.action = "play"
    return itemlist


