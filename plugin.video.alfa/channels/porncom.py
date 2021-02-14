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

host = 'https://www.porn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/channels"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/videos/search?q=%s" % (host,texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\\", "", data)
    patron = '<div class="list-global__item".*?'
    patron += 'href="([^"]+)">.*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        thumbnail = scrapedthumbnail
        scrapedtitle = scrapedtitle.replace(" Porn", "")
        title = "%s (%s)" % (scrapedtitle, cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, '<a class="next pagination__number" href="([^"]+)" rel="nofollow">Next')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>|amp;", "", data)
    patron = '<div class="list-global__item(.*?)'
    patron += 'class="go" title="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += 'duration">([^<]+)<.*?'
    patron += '<span><a href="[^"]+">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,time,server in matches:
        title = "[COLOR yellow]%s[/COLOR] [%s] %s" % (time, server, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = ""
        url = scrapertools.find_single_match(scrapedurl,'<a href=".*?5odHRwczov([^/]+)/\d+/\d+"')
        url = url.replace("%3D", "=").replace("%2F", "/")
        import base64
        url = base64.b64decode(url)
        url = "https:/" + url
        plot = ""
        itemlist.append(item.clone(action="play", title=title, contentTitle = title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot))
    next_page = scrapertools.find_single_match(data, '<a class="next pagination__number" href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

