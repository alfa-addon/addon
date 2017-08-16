# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = "http://www.playpornx.net/list-movies/"


def mainlist(item):
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Todas", action="lista",
                         thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                         fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                         url ='https://www.playpornx.net/category/porn-movies/?filter=date'))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url='http://www.playpornx.net/?s=',
                         thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
                         fanart='https://s30.postimg.org/pei7txpa9/buscar.png'))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    if item.url == '': item.url = host
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'role=article><a href=(.*?) rel=bookmark title=(.*?)>.*?src=(.*?) class'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapedtitle

        itemlist.append(Item(channel=item.channel, action='findvideos', title=title, url=url, thumbnail=thumbnail))

    # #Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<link rel=next href=(.*?) \/>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="lista", title='Siguiente >>>', url=next_page,
                                 thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png', extra=item.extra))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    try:
        if texto != '':
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
