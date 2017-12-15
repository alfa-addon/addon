# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = "https://watchfreexxx.net/"


def mainlist(item):
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Todas", action="lista",
                         thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                         fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                         url =host))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+'?s=',
                         thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
                         fanart='https://s30.postimg.org/pei7txpa9/buscar.png'))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    if item.url == '': item.url = host
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if item.extra != 'Buscar':
        patron = '<div class=item>.*?href=(.*?)><div.*?<img src=(.*?) alt=(.*?) width'
    else:
        patron = '<div class=movie>.*?<img src=(.*?) alt=(.*?) \/>.*?href=(.*?)\/>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_1, data_2, data_3 in matches:
        if item.extra != 'Buscar':
            url = data_1
            thumbnail = data_2
            title = data_3
        else:
            url = data_3
            thumbnail = data_1
            title = data_2

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
            item.extra = 'Buscar'
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
