# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://www.xn--hentaienespaol-1nb.net/'
headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todos", action="todas", url=host, thumbnail='', fanart=''))

    itemlist.append(
        Item(channel=item.channel, title="Sin Censura", action="todas", url=host + 'hentai/sin-censura/', thumbnail='',
             fanart=''))

    return itemlist


def todas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="box-peli" id="post-.*?">.<h2 class="title">.<a href="([^"]+)">([^<]+)<\/a>.*?'
    patron += 'height="170px" src="([^"]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle  # .decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = ''
        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, fanart=fanart))

    # Paginacion
    title = ''
    siguiente = scrapertools.find_single_match(data, 'class="nextpostslink" rel="next" href="([^"]+)">')
    title = 'Pagina Siguiente >>> '
    fanart = ''
    itemlist.append(Item(channel=item.channel, action="todas", title=title, url=siguiente, fanart=fanart))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return todas(item)
    else:
        return []
