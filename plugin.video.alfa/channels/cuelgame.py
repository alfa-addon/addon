# -*- coding: utf-8 -*-

import re
import urlparse

from core import scrapertools, httptools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="[COLOR forestgreen]Videos[/COLOR]", action="scraper",
                         url="http://cuelgame.net/?category=4",
                         thumbnail="http://img5a.flixcart.com/image/poster/q/t/d/vintage-camera-collage-sr148-medium-400x400-imadkbnrnbpggqyz.jpeg",
                         fanart="http://imgur.com/7frGoPL.jpg"))
    itemlist.append(Item(channel=item.channel, title="[COLOR forestgreen]Buscar[/COLOR]", action="search", url="",
                         thumbnail="http://images2.alphacoders.com/846/84682.jpg",
                         fanart="http://imgur.com/1sIHN1r.jpg"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://cuelgame.net/search.php?q=%s" % (texto)

    try:
        return scraper(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def scraper(item):
    logger.info()
    itemlist = []
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|CET", "", data)
    patron  = '<h2> <a href="([^"]+)".*?'
    patron += 'class="l:\d+".*?>([^<]+)</a>'
    patron += '(.*?)class="lazy".*?'
    patron += 'news-content">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, check_thumb, scrapedplot in matches:
        scrapedtitle = re.sub(r'\.', ' ', scrapedtitle)
        scrapedthumbnail = scrapertools.find_single_match(check_thumb, "</div><img src=\'([^\']+)\'")
        title_year = re.sub(r"(\d+)p", "", scrapedtitle)
        if "category=4" in item.url:
            try:
                year = scrapertools.find_single_match(title_year, '.*?(\d\d\d\d)')
            except:
                year = ""
        else:
            year = ""
        # No deja pasar items de la mula
        if scrapedurl.startswith("ed2k:"):
            continue
        scrapedtitle = "[COLOR greenyellow]" + scrapedtitle + "[/COLOR]"
        itemlist.append(
            Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, action="play", server="torrent",
                 thumbnail=scrapedthumbnail, folder=False))
    # Extrae el paginador
    patronvideos = '<a href="([^"]+)" rel="next">siguiente &#187;</a>'
    matches = scrapertools.find_multiple_matches(data, patronvideos)
    if len(matches) > 0:
        # corrige "&" para la paginación
        next_page = matches[0].replace("amp;", "")
        scrapedurl = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="scraper", title="Página siguiente >>", url=scrapedurl,
                             thumbnail="http://imgur.com/ycPgVVO.png", folder=True))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = 'http://cuelgame.net/?category=4'
        itemlist = scraper(item)
        if itemlist[-1].action == "Página siguiente >>":
            itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist
