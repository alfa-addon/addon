# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = "https://www.vipporns.com" 

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Útimos videos", url= host + "/latest-updates/?sort_by=post_date&from=1"))
    itemlist.append(item.clone(action="lista", title="Populares", url=host + "/most-popular/?sort_by=video_viewed_month&from=1"))
    itemlist.append(item.clone(action="lista", title="Mejor valorado", url=host + "/top-rated/?sort_by=rating_month&from=1"))
    itemlist.append(item.clone(action="categorias", title="Canal", url=host + "/categories/"))

    itemlist.append(item.clone(action="search", title="Buscar"))
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/searches/%s/?sort_by=post_date" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="videos">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        title= "%s (%s)" %(scrapedtitle,cantidad)
        thumbnail =scrapedthumbnail
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                             thumbnail=thumbnail, fanart=thumbnail))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data) #quita espacio doble
    patron = '<div class="item">.*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += 'data-original="([^"]+)".*?'
    patron += '<div class="duration">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedurl,scrapedtitle,scrapedthumbnail,time in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, thumbnail=thumbnail, fanart=thumbnail, title=title,
                             url=url, viewmode="movie", folder=True))
    next_page = scrapertools.find_single_match(data, 'data-parameters="([^"]+)">Next')
    if next_page:
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
