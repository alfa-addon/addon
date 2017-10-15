# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa 
# ------------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger

def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(item.clone(title="Novedades", action="peliculas", url="http://gnula.mobi/"))
    itemlist.append(item.clone(title="Castellano", action="peliculas",
                               url="http://www.gnula.mobi/tag/espanol/"))
    itemlist.append(item.clone(title="Latino", action="peliculas", url="http://gnula.mobi/tag/latino/"))
    itemlist.append(item.clone(title="VOSE", action="peliculas", url="http://gnula.mobi/tag/subtitulada/"))

    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://gnula.mobi/?s=%s" % texto

    try:
        return sub_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron = '<div class="row">.*?<a href="([^"]+)" title="([^"]+)">.*?<img src="(.*?)" title'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, name, img in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", thumbnail=img))

    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon '
                                                      'glyphicon-chevron-right" aria-hidden="true"></i>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>", url=paginacion))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="col-mt-5 postsh">.*?href="(.*?)" title="(.*?)".*?under-title">(.*?)<.*?src="(.*?)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedyear, scrapedtitle, scrapedthumbnail in matches:
        year = scrapertools.find_single_match(scrapedyear, r'.*?\((\d{4})\)')
        itemlist.append(Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle = scrapedtitle, url=scrapedurl,
                        thumbnail=scrapedthumbnail, infoLabels={'year': year}))

    tmdb.set_infoLabels(itemlist, True)
    next_page_url = scrapertools.find_single_match(data, '<link rel="next" href="(.*?)"')
    if next_page_url != "":
        next_page_url = item.url + next_page_url
        itemlist.append(item.clone(action="peliculas", title="Siguiente >>", text_color="yellow",
                                   url=next_page_url))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'data-src="([^"]+)".*?'
    patron += 'data-toggle="tab">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, language in matches:
        url = url.replace("&amp;", "&")
        response = httptools.downloadpage(url, follow_redirects=False, add_referer=True)
        if response.data:
            url = scrapertools.find_single_match(response.data, 'src="([^"]+)"')
        else:
            url = response.headers.get("location", "")
        url = url.replace("&quot","")
        titulo = "Ver en %s (" + language + ")"
        itemlist.append(item.clone(
                                   action = "play",
                                   title = titulo,
                                   url = url,
                                   language = language))
    tmdb.set_infoLabels(itemlist, True)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
