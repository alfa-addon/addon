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
from platformcode import logger
from bs4 import BeautifulSoup

host = 'https://www.eporner.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Últimos videos", action="lista", url=host + "/0/"))
    itemlist.append(item.clone(title="Más visto", action="lista", url=host + "/most-viewed/"))
    itemlist.append(item.clone(title="Mejor valorado", action="lista", url=host + "/top-rated/"))
    itemlist.append(item.clone(title="Pornstars", action="pornstars_list", url=host + "/pornstar-list/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host + "/cats/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def pornstars_list(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Mas Populares", action="categorias", url=item.url))
    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        itemlist.append(item.clone(title=letra, action="categorias", url=urlparse.urljoin(item.url, letra)))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "cats" in item.url:
        matches = soup.find_all('div', class_='categoriesbox')
    else:
        matches = soup.find_all('div', class_='mbprofile')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        cantidad = elem.find('div', class_='mbtim')
        if cantidad:
            cantidad = cantidad.text.replace("Videos: ", "")
            title = "%s (%s)" %(title, cantidad)
        url = urlparse.urljoin(host,url)
        itemlist.append(item.clone(title=title, url=url, action="lista", thumbnail=thumbnail, fanart=thumbnail))
    next_page = soup.find('a', class_='nmnext')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
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
    matches = soup.find_all('div', class_='mb')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('p', class_='mbtit').text.strip()
        thumbnail = elem.img['src']
        if "gif" in thumbnail:
            thumbnail = elem.img['data-src']
        time = elem.find('span', class_='mbtim').text
        quality = elem.find('div', title="Quality").text
        url = urlparse.urljoin(host,url)
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                                fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='nmnext')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

