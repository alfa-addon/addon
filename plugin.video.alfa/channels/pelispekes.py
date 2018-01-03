# -*- coding: utf-8 -*-

import re

from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []

    if item.url == "":
        item.url = "http://www.pelispekes.com/"

    data = scrapertools.cachePage(item.url)
    patron = '<div class="poster-media-card"[^<]+'
    patron += '<a href="([^"]+)" title="([^"]+)"[^<]+'
    patron += '<div class="poster"[^<]+'
    patron += '<div class="title"[^<]+'
    patron += '<span[^<]+</span[^<]+'
    patron += '</div[^<]+'
    patron += '<span class="rating"[^<]+'
    patron += '<i[^<]+</i><span[^<]+</span[^<]+'
    patron += '</span[^<]+'
    patron += '<div class="poster-image-container"[^<]+'
    patron += '<img width="\d+" height="\d+" src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")
        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail,
                 plot=plot, contentTitle=title, contentThumbnail=thumbnail))

    # Extrae la pagina siguiente
    next_page_url = scrapertools.find_single_match(data,
                                                   '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right')
    if next_page_url != "":
        itemlist.append(Item(channel=item.channel, action="mainlist", title=">> Página siguiente", url=next_page_url,
                             viewmode="movie"))

    return itemlist


def findvideos(item):
    logger.info("item=" + item.tostring())
    data = scrapertools.cachePage(item.url)
    data = data.replace("www.pelispekes.com/player/tune.php?nt=", "netu.tv/watch_video.php?v=")

    item.plot = scrapertools.find_single_match(data, '<h2>Sinopsis</h2>(.*?)<div')
    item.plot = scrapertools.htmlclean(item.plot).strip()
    item.contentPlot = item.plot
    logger.info("plot=" + item.plot)

    return servertools.find_video_items(item=item, data=data)
