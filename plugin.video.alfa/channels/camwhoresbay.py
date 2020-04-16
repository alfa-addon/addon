# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.camwhoresbay.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto.replace("+", "-"))
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron  += '<img class="thumb" src="([^"]+)".*?'
    patron  += '<div class="videos">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        scrapedtitle = "%s (%s)" % (scrapedtitle, cantidad)
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "http:%s" % scrapedthumbnail
        scrapedthumbnail += "|Referer=%s" % item.url
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video-item\s+">.*?'
    patron += '<a href="([^"]+)" title="([^"]+)"  class="thumb">.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<i class="fa fa-clock-o"></i>(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime, scrapedtitle)
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "http:%s" % scrapedthumbnail
        scrapedthumbnail += "|Referer=%s" % item.url
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=scrapedthumbnail,
                              fanart=scrapedthumbnail, plot=plot))
    if item.extra:
       next_page = scrapertools.find_single_match(data, '<li class="next">.*?from_videos\+from_albums:(\d+)')
       if next_page:
           if "from_videos=" in item.url:
               next_page = re.sub(r'&from_videos=(\d+)', '&from_videos=%s' % next_page, item.url)
           else:
               next_page = "%s?mode=async&function=get_block&block_id=list_videos_videos_list_search_result" \
                           "&q=%s&category_ids=&sort_by=post_date&from_videos=%s" % (item.url, item.extra, next_page)
           itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    else:
        next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
        if next_page and not next_page.startswith("#"):
            next_page = urlparse.urljoin(item.url,next_page)
            itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
        else:
            next_page = scrapertools.find_single_match(data, '<li class="next">.*?from:(\d+)')
            if next_page:
                if "from" in item.url:
                    next_page = re.sub(r'&from=(\d+)', '&from=%s' % next_page, item.url)
                else:
                    next_page = "%s?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=%s" % (
                         item.url, next_page)
                itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page))
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

