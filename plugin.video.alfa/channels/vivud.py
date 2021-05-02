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

from core import jsontools as json
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://vivud.com'    #titbox vivud zmovs

url_api = host + "/?ajax=1&type="

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=url_api + "most-recent&page=1"))
    itemlist.append(item.clone(title="Mejor valorados" , action="lista", url=url_api + "top-rated&page=1"))
    itemlist.append(item.clone(title="Longitud" , action="lista", url=url_api + "long&page=1"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<ul class="sidebar-nav">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a class="category-item" href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        url = "%s%s?ajax=1&type=top-rated&page=1" %(host, scrapedurl)  #most-recent
        scrapedplot = ""
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=url,
                              thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for Video in JSONData["data"]:
        duration = Video["duration"]
        title = Video["videoTitle"]
        title = "[COLOR yellow]%s[/COLOR] %s" % (duration,title)
        src= Video["src"]
        domain=""
        thumbnail = src.get('domain', domain) + src.get('pathMedium', domain)+"1.jpg"
        url= Video["urls_CDN"]
        url= url.get('480', domain)
        url = url.replace("/\n/", "/")
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, contentTitle = title, plot=plot,))
    Actual = int(scrapertools.find_single_match(item.url, '&page=([0-9]+)'))
    if JSONData["pagesLeft"] - 1 > Actual:
        scrapedurl = item.url.replace("&page=" + str(Actual), "&page=" + str(Actual + 1))
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=scrapedurl))
    return itemlist


def findvideos(item):
    return

