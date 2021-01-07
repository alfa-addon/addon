# -*- coding: utf-8 -*-
#------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re
import os

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

host = 'https://hotmovs.com'   # https://hotmovs.com   https://upornia.com

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Mas Vistas" , action="lista", url=host + "/most-popular/?sort_by=video_viewed_week"))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/top-rated/?sort_by=rating_week"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/channels/?sort_by=cs_viewed"))
    itemlist.append(item.clone(title="Pornstars" , action="categorias", url=host + "/models//?sort_by=model_viewed"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/?sort_by=title"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
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
    soup = create_soup(item.url)
    matches = soup.find_all('article')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('h5').text
        thumbnail = elem.img['src']
        cantidad = elem.find('div', class_='thumbnail__label')
        if not cantidad:
            cantidad = elem.find('span', class_='thumbnail__info__right')
        if cantidad:
            title = "%s (%s)" % (title, cantidad.text.strip())
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail ) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('h5').text
        thumbnail = elem.img['src']
        time = elem.find('div', class_='thumbnail__info__right').text.strip()
        quality = elem.find('div', class_='thumbnail__label--left')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                                   fanart=thumbnail, contentTitle = title))
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

