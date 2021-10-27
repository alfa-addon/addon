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

host = 'https://plusone8.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=date"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?filter=popular"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/?orderby=likes"))
    # itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars"))

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/porn-categories"))
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
    soup = create_soup(item.url).find('main', id='main')
    matches = soup.find_all('div', id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        if "svg" in thumbnail:
            thumbnail = elem.img['data-lazy-src']
        # url = url.replace("?actors=","/star/")
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_siblings("li")[0].a['href']
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
    soup = create_soup(item.url).find('main', id='main')
    matches = soup.find_all('div', id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        if "test" in url:
            continue
        title = elem.a['title']
        thumbnail = elem.img['src']
        if "svg" in thumbnail:
            thumbnail = elem.img['data-lazy-src']
        thumbnail += "|verifypeer=false"
        time = elem.find('span', class_='length')
        actors = elem['class']
        actriz = ""
        for x in actors:
            if not "actors-" in x:
                continue
            actor = x.replace("actors-", "").replace("-", " ")
            actriz += "%s & " %actor
        if actriz:
            title = "[COLOR cyan]%s[/COLOR] %s" %(actriz[:-2], title)
        if time:
            time = time.text.strip()
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_siblings("li")[0].a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = create_soup(item.url).find('div', id='video-download').a['href']
    url = url.replace(" ", "%20")
    itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = create_soup(item.url).find('div', id='video-download').a['href']
    url = url.replace(" ", "%20")
    itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    return itemlist
