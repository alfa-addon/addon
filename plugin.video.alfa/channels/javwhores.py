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


host = 'https://www.javbangers.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Mejor valorados" , action="lista", url=host + "/top-rated/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s/" % (host, texto)
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
    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron  += '<img class="thumb" src="([^"]+)".*?'
    patron  += '<div class="videos">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad)
        scrapedplot = ""
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    # PURGA los PRIVATE 
    patron  = 'div class="video-item\s+".*?href="([^"]+)".*?'
    patron += 'data-original="([^"]+)" '
    patron += 'alt="([^"]+)"(.*?)fa fa-clock-o"></i>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, quality, duration in matches:
        url = urlparse.urljoin(host, scrapedurl)
        scrapedtitle = scrapedtitle.strip()
        if not 'HD' in quality :
            title = "[COLOR yellow]%s[/COLOR] %s" % (duration.strip(), scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (duration.strip(), scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                              plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if "#" in next_page:
        next_page = scrapertools.find_single_match(data, 'data-parameters="([^"]+)">Next')
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

