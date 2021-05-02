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

host = 'https://www.pornxbit.com'


# gounlimited, woolf, openload

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Peliculas" , action="lista", url=host + "/full-movie/?asgtbndr=1"))
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/porn-videos/?filter=latest&asgtbndr=1"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/porn-videos/?filter=most-viewed&asgtbndr=1"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/porn-videos/?filter=popular&asgtbndr=1"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/porn-videos/?filter=longest&asgtbndr=1"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/actors/"))
    # itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/sites/?sort_by=avg_videos_popularity&from=01"))

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host,texto)
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
    soup = create_soup(item.url).find('div', class_='videos-list')
    matches = soup.find_all('article', id=re.compile(r"^post-\d+"))
    for elem in matches:

        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_sibling("li").a['href']
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
    soup = create_soup(item.url).find('main')
    matches = soup.find_all('article', class_=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title'].replace("&#8211;", "-")
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration')
        quality = elem.find('span', class_='hd-video')
        if time:
            time = time.text.strip()
        else:
            time = ""
        if quality:
            quality = quality.text
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    matches = soup.find_all('iframe')
    for elem in matches:
        url = elem['src']
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # logger.debug(url)
    return itemlist

