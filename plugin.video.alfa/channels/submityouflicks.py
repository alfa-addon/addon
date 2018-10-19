# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://www.submityourflicks.com'
def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Útimos videos", url=host,
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Populares", url=host + "/most-viewed/month/",
             viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, action="videos", title="Mejor valorados", url=host + "/top-rated/month/",
             viewmode="movie"))

    itemlist.append(
        Item(channel=item.channel, action="videos", title="Big Tits", url=host + "/search/big-tits/",
             viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar",
                         url="http://www.submityourflicks.com/index.php?mode=search&q=%s&submit=Search"))
    return itemlist


def search(item, texto):
    logger.info()
    tecleado = texto.replace(" ", "+")
    item.url = item.url % tecleado
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def videos(item):
    logger.info()
    itemlist = []
    data = scrapertools.downloadpageGzip(item.url)
    patron = '<div class="item-block[^<]+'
    patron += '<div class="inner-block[^<]+'
    patron += '<a href="([^"]+)" title="([^"]+)"[^<]+'
    patron += '<span class="image".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="icon i-time"></span>([^"]+)\| <span class="icon i-calendar">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail,scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumbnail.replace(" ", "%20")
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                             folder=False))
    next_page_url = scrapertools.find_single_match(data, "<a href='([^']+)' class=\"next\">NEXT</a>")
    if next_page_url != "":
        url = urlparse.urljoin(item.url, next_page_url)
        itemlist.append(Item(channel=item.channel, action="videos", title=">> Página siguiente", url=url, folder=True,
                             viewmode="movie"))
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    media_url = "https:" + scrapertools.find_single_match(data, 'source src="([^"]+)"')
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, show=item.title, server="directo", folder=False))
    return itemlist
