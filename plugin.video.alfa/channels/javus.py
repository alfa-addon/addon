# -*- coding: utf-8 -*-

import re

from core import httptools
from core import servertools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'http://javuss.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="([^"]+)" title="([^"]+)" rel="nofollow" class="post-image post-image-left".*?\s*<div class="featured-thumbnail"><img width="203" height="150" src="([^"]+)" class="attachment-featured size-featured wp-post-image" alt="" title="" \/><\/div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = ''
        itemlist.append(
            Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail))
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')
    next_page = next_page.replace('"', '')
    if next_page!="":
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    itemlist = []
    itemlist = servertools.find_video_items(item)
    a = len (itemlist)
    for i in itemlist:
        if a < 1:
            return []
        res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue
