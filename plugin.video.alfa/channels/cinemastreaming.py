# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cinemastreaming
# ------------------------------------------------------------
import re

from channels import  filtertools
from core import scrapertools, servertools, httptools
from core.item import Item
from platformcode import config
from core import tmdb

host = 'https://cinemastreaming.info'

headers = [['Referer', host]]

def mainlist(item):
    log()

    # Menu Principale

    itemlist = [Item(channel = item.channel,
                     contentType = 'movie',
                     title = 'Film',
                     url = host + '/film/',
                     action = 'video',
                     thumbnail = '',
                     fanart = ''
                     ),
    ]

    return itemlist

def video(item):
    log()

    itemlist = []  # Creo una lista Vuota

    # Carica la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertools.find_single_match(data, r'<main>(.*?)<\/main>')
    block = re.sub('\t|\n', '', block)

    patron = r'<article.*?class="TPost C">.*?<a href="([^"]+)">.*?src="([^"]+)".*?>.*?<h3 class="Title">([^<]+)<\/h3>(.*?)<\/article>'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl, scrapedthumb, scrapedtitle, scrapedinfo in matches:
        log('Info Block', scrapedinfo)
        patron = r'<span class="Year">(.*?)<\/span>.*?<span class="Vote.*?">(.*?)<\/span>.*?<div class="Description"><p>(.*?)<\/p>.*?<p class="Genre.*?">(.*?)<\/p><p class="Director.*?">.*?<a.*?>(.*?)<\/a>.*?<p class="Actors.*?">(.*?)<\/p>'
        info = re.compile(patron, re.DOTALL).findall(scrapedinfo)
        for year, rating, plot, genre, director, cast in info:
            genre = scrapertools.find_multiple_matches(genre, r'<a.*?>(.*?)<\/a>')
            cast = scrapertools.find_multiple_matches(cast, r'<a.*?>(.*?)<\/a>')
            
            infoLabels = {}
            infoLabels['Year'] = year
            infoLabels['Rating'] = rating
            infoLabels['Plot'] = plot
            infoLabels['Genre'] = genre
            infoLabels['Director'] = director
            infoLabels['Cast'] = cast
            
            itemlist.append(
                Item(channel=item.channel,
                    action="findvideos",
                    contentType=item.contentType,
                    title=scrapedtitle,
                    fulltitle=scrapedtitle,
                    url=scrapedurl,
                    thumbnail=scrapedthumb,
                    infoLabels = infoLabels,
                    show=scrapedtitle))

    return itemlist


def log(stringa1="", stringa2=""):
    import inspect, os
    from platformcode import logger
    logger.info("[" + os.path.basename(__file__) + "] - [" + inspect.stack()[1][3] + "] " + str(stringa1) + str(stringa2))