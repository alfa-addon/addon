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
from bs4 import BeautifulSoup


host = 'https://www.youporn.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas", action="lista", url=host + "/browse/time/"))
    itemlist.append(item.clone(title="Mas Vistas", action="lista", url=host + "/browse/views/"))
    itemlist.append(item.clone(title="Mejor valorada", action="lista", url=host + "/top_rated/"))
    itemlist.append(item.clone(title="Canal", action="catalogo", url=host + "/channels/most_popular/"))
    itemlist.append(item.clone(title="Pornstars", action="catalogo", url=host + "/pornstars/most_popular/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?query=%s" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "/pornstars/" in item.url:
        matches = soup.find_all('div', class_='porn-star-list')
    else:
        matches = soup.find_all('div', class_='channel-box')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-original']
        cantidad = elem.find('span', class_='video-count')
        if not cantidad:
            cantidad = elem.find('div', class_='videoCount')
        title = "%s (%s)" %(title,cantidad.text)
        url = urlparse.urljoin(item.url,url)
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('link', rel='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='row grouped')
    matches = soup.find_all('div', class_='categories-row')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-original']
        cantidad = elem.find('span').text
        title = "%s (%s)" %(title,cantidad)
        url = urlparse.urljoin(item.url,url)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail) )
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
    matches = soup.find_all('div', class_='video-box')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-original']
        time = elem.find('div', class_='video-duration').text
        quality = elem.find('div', class_='video-best-resolution')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality.text,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        url = urlparse.urljoin(host,url).replace("watch", "embed")
        contentTitle = title
        itemlist.append(item.clone(action="play" , title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, contentTitle = contentTitle))
    next_page = soup.find('link', rel='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
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

