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

host = 'https://pornburst.xxx'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/page3.html"))
    itemlist.append(item.clone(title="Pornstars" , action="categorias", url=host + "/pornstars/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/sites/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?q=%s" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if not "/categories/" in item.url:
        patron = 'class="muestra-escena.*?'
        patron += 'href="([^"]+)".*?'
        patron += 'data-src="([^"]+)".*?'
        patron += 'alt="([^"]+)".*?'
        patron += '</span>([^<]+)</span>'
    else:
        patron  = 'class="muestra-escena.*?'
        patron += 'href="([^"]+)".*?'
        patron += 'data-src="([^"]+)".*?'
        patron += 'alt="([^"]+)".*?'
        patron += '<span class="ico.*?></span>([^<]+)</h2>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        if "videos" in cantidad:
            scrapedtitle ="%s (%s)" % (scrapedtitle, cantidad)
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="muestra-escena"\s*href="([^"]+)".*?'
    patron += 'data-stats-video-name="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<span class="ico-minutos sprite" title="Length"></span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]%s[/COLOR] %s" % (duracion,scrapedtitle)
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')
    if not next_page:
        next_page = scrapertools.find_single_match(data,'next "><a href="([^"]+)"')
        next_page = urlparse.urljoin(host,next_page)
    if next_page!="":
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<source src="([^"]+)" type="video/mp4"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        title = scrapedurl
    itemlist.append(item.clone(action="play", title=title, url=scrapedurl))
    return itemlist

