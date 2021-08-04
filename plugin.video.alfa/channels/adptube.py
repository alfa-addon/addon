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
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []

host = 'https://www.adptube.com'


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/videos?order_by=date_publish"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/videos/?order_by=views_count"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/series"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    # itemlist.append(item.clone(title="Buscar", action="search"))

    # autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host,texto)
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
    matches = soup.find_all('div', class_='col-md-2')
    if "series" in item.url:
        matches = soup.find_all('div', class_='col-md-3')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.find('div', class_='size-maintained')['style']
        cantidad = elem.find('div', class_='scenes-count')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        thumbnail = thumbnail.replace("background-image: url(", "").replace(");", "")
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
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
    matches = soup.find_all('div', class_='col-md-3')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        time = elem.find('div', class_='corner-right-bottom').text.strip()
        actriz = []
        plot = ""
        reparto = elem.find('div', class_='performers').find_all('a')
        for elem in reparto:
            if not "Actriz Porno" in elem['title']:
                actriz.append(elem['title'])
        actriz = ", ".join(actriz)
        if actriz:
            plot = actriz
            actriz = "%s" %actriz
        if time:
            title = "[COLOR yellow]%s[/COLOR] [COLOR cyan]%s[/COLOR] %s" % (time, actriz, title)
        url = urlparse.urljoin(host, url)
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find('source', type='video/mp4')['src']
    # itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    itemlist.append(item.clone(title='%s', url=url, action='play', language='VO',contentTitle = item.title))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
