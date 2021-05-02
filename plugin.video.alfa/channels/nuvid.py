# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core.item import Item
from core import httptools
from core import servertools
from core import scrapertools
from platformcode import logger
import base64
import hashlib


host = "https://www.nuvid.com"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(action="lista", title="Nuevos Vídeos", url="https://www.nuvid.com/search/videos/_empty_/"))
    itemlist.append(item.clone(action="lista", title="Mejor Valorados", url="https://www.nuvid.com/search/videos/_empty_/", extra="rt"))
    itemlist.append(item.clone(action="lista", title="Solo HD", url="https://www.nuvid.com/search/videos/hd", calidad="1"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "https://www.nuvid.com/search/videos/%s" %texto 
    item.extra = "buscar"
    return lista(item)


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage("https://www.nuvid.com/categories").data
    bloques = scrapertools.find_multiple_matches(data, '<h2 class="c-mt-output title2">.*?>([^<]+)</h2>(.*?)</div>')
    for cat, b in bloques:
        cat = cat.replace("Straight", "Hetero")
        itemlist.append(item.clone(action="", title=cat, text_color="gold"))
        matches = scrapertools.find_multiple_matches(b, '<li>.*?href="([^"]+)" >(.*?)</span>')
        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = "   %s" % scrapedtitle.replace("<span>", "")
            scrapedurl = urlparse.urljoin(host, scrapedurl)
            itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    if not item.calidad:
        item.calidad = "0"
    filter = 'ch=178.1.2.3.4.191.7.8.5.9.10.169.11.12.13.14.15.16.17.18.28.190.20.21.22.27.23.24.25.26.189.30.31.32.181' \
             '.35.36.37.180.176.38.33.34.39.40.41.42.177.44.43.45.47.48.46.49.50.51.52.53.54.55.56.57.58.179.59.60.61.' \
             '62.63.64.65.66.69.68.71.67.70.72.73.74.75.182.183.77.76.78.79.80.81.82.84.85.88.86.188.87.91.90.92.93.94' \
             '&hq=%s&rate=&dur=&added=&sort=%s' % (item.calidad, item.extra)
    header = {'X-Requested-With': 'XMLHttpRequest'}
    if item.extra != "buscar":
        header['Cookie'] = 'area=EU; lang=en; search_filter_new=%s' % filter
    data = httptools.downloadpage(item.url, headers=header, cookies=False).data
    patron = '<div class="box-tumb related_vid.*?'
    patron += 'href="([^"]+)" title="([^"]+)".*?'
    patron += 'src="([^"]+)"(.*?)<i class="time">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, quality, duration in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        if duration:
            title = "[COLOR yellow]%s[/COLOR] %s" % (duration, scrapedtitle)
        if item.calidad == "0" and 'class="hd"' in quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red][HD][/COLOR] %s" % (duration, scrapedtitle)
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "https:%s" % scrapedthumbnail
        itemlist.append(item.clone(action="play", title=title, contentTitle = title, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<li class="next1">.*?href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(host, next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist
