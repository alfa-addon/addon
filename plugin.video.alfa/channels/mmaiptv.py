# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per mmaiptv
# ----------------------------------------------------------
import re  
import urlparse

from core import httptools
from platformcode import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb




host = "http://mmaiptv.it"

headers = [['Referer', host]]

def mainlist(item):
    logger.info("[mmaiptv.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="list_titles",
                     title="[COLOR azure]Tutti[/COLOR]",
                     url="%s/b.php" % host,
                     extra="anime",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca[/COLOR]",
                     url="%s/b.php" % host,
                     extra="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist

def list_titles(item):
    logger.info("[mmaiptv.py] list_titles")
    itemlist = []

    if item.url == "":
        item.url = host
    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
	
    patronvideos = '<div class="tab-pane active".*?<font color="#000000">([^<]+)<\/font>.*?<a href="([^"]+)"><img src="([^"]+)".*?<\/div>'

    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="episodes",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl if not 'search' in item.extra else (host + "/"+scrapedurl),
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot",
                 Folder=True))
    return itemlist

def episodes(item):
    logger.info("[mmaiptv.py] serietv")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    patronvideos = '<div class="tab-pane active".*?<font color="#000000">([^<]+)<\/font>.*?<a href="([^"]+)"><img src="([^"]+)".*?<\/div>'

    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot"))
    return list(reversed(itemlist))

def search(item, texto):
    logger.info("[mmaiptv.py] search")
    item.url = host + "/d.php?search=" + texto
    return list_titles(item)

def findvideos(item):
    logger.info("[mmaiptv.py] findvideos")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    patron = "file: \"([^\"]+)\""
    matches = re.compile(patron, re.DOTALL).findall(data)
    headers.append(['Referer', item.url])
    for video in matches:
        itemlist.append(Item(channel=item.channel, action="play", title="[.mp4] [COLOR azure]%s[/COLOR]" % item.title,url=video, folder=False))

    return itemlist

