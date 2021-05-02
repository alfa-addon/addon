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
from core import jsontools as json

host = 'https://poroyal.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/videos?o=mr"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/videos?o=mv&t=a"))
    itemlist.append(item.clone(title="Mas comentados" , action="lista", url=host + "/videos?t=a&o=md"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/videos?t=a&o=lg"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/videos/%s" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-4 m-b-20">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" title="([^"]+)".*?'
    patron += '<div class="float-right">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        title = "%s (%s)" %(scrapedtitle, cantidad)
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-3">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" title="([^"]+)".*?'
    patron += '<div class="duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
        quality = ""
        if "HD" in time:
            quality = "HD"
            time = time.replace("<span class=\"hd-text-icon\">HD</span>", "")
        time = time.strip()
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time, quality, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="page-item"><a class="page-link" href="([^"]+)" class="prevnext">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<source src="([^"]+)" type=\'video/mp4\' label=\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,quality in matches:
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist[::-1]

