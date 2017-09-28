# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa 
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import httptools
from core import tmdb
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Novedades", action="peliculas", url="http://gnula.mobi/"))
    itemlist.append(item.clone(title="Castellano", action="peliculas",
                                     url="http://www.gnula.mobi/tag/esp)anol/"))
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

    for url,name,img   in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", show=name, thumbnail=img))

    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon '
                                                      'glyphicon-chevron-right" aria-hidden="true"></i>')

    if paginacion:
        itemlist.append(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion)

    return itemlist

def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="col-mt-5 postsh">.*?href="(.*?)" title="(.*?)".*?under-title">(.*?)<.*?src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedyear, scrapedtitle, scrapedthumbnail in matches:

        url = scrapedurl
        title = scrapedtitle
        year = scrapertools.find_single_match(scrapedyear, r'.*?\((\d{4})\)')
        thumbnail = scrapedthumbnail
        new_item =Item (channel = item.channel, action="findvideos", title=title, contentTitle=title, url=url,
                                         thumbnail=thumbnail, infoLabels = {'year':year})
        if year:
            tmdb.set_infoLabels_item(new_item)

        itemlist.append(new_item)

    next_page_url = scrapertools.find_single_match(data,'<link rel="next" href="(.*?)"\/>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="peliculas", title="Siguiente >>", text_color="yellow",
                                        url=next_page_url))

    return itemlist

