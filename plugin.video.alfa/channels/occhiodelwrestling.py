# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale  per http://www.occhiodelwrestling.netsons.org/
# Ringraziamo Icarus crew
# ------------------------------------------------------------

import re

from core import httptools, scrapertools, servertools
from core.item import Item
from lib import unshortenit
from platformcode import logger

host = "http://www.occhiodelwrestling.netsons.org"


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info()
    itemlist = [
        Item(channel=item.channel,
             action="categorie",
             title="Lista categorie",
             text_color="azure",
             url=host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"
             )
    ]

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    blocco = scrapertools.get_match(data, '<div class="menu-container">(.*?)</div>')

    patron = r'<li[^>]+><a title="[^"]+" href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="loaditems",
                 title=scrapedtitle,
                 text_color="azure",
                 url=scrapedurl,
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def loaditems(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<a class="[^"]+" href="([^"]+)" title="([^"]+)"[^>]*>\s*<img[^s]+src="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedimg in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 text_color="azure",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedimg,
                 folder=True))

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    index = 1
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title="[COLOR orange][B]Link %s:[/B][/COLOR] %s" % (index, scrapedtitle),
                 text_color="azure",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=item.thumbnail))
        index += 1
    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def play(item):
    logger.info()

    url, c = unshortenit.unshorten(item.url)

    itemlist = servertools.find_video_items(data=url)

    for videoitem in itemlist:
        videoitem.title = item.show
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist

# ================================================================================================================
