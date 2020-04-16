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

host = 'https://www.gotporn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/?page=1"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "/top-rated?page=1"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-viewed?page=1"))
    itemlist.append( Item(channel=item.channel, title="Longitud" , action="lista", url=host + "/longest?page=1"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels?page=1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/results?search_query=%s" % (host, texto)
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
    patron = '<a href="([^"]+)">'
    patron += '<span class="text">([^<]+)</span>'
    patron += '<span class="num">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = "%s %s" % (scrapedtitle,cantidad)
        scrapedurl = scrapedurl + "?page=1"
        thumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<header class="clearfix" itemscope>.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = scrapedurl + "?page=1"
        if not scrapedthumbnail.startswith("https"):
            thumbnail = "https:%s" % scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=thumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary"><span class="text">Next')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="catalogo", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li class="video-item.*?'
    patron += 'href="([^"]+)" data-title="([^"]+)".*?'
    patron += '<span class="duration">(.*?)</span>.*?'
    patron += 'src=\'([^\']+)\'.*?'
    patron += '<h3 class="video-thumb-title(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedtime,scrapedthumbnail,quality in matches:
        scrapedtime = scrapedtime.strip()
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (scrapedtime,scrapedtitle)
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "https:%s" % scrapedthumbnail
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot,))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary')
    if "categories" in item.url:
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn btn-secondary paginate-show-more')
    if "search_query" in item.url:
        next_page = scrapertools.find_single_match(data, '<link rel=\'next\' href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def play(item):
    logger.info(item)
    itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
    return itemlist

