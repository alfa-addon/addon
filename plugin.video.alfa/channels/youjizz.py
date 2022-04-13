# -*- coding: utf-8 -*-
# ------------------------------------------------------------
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


host = "https://www.youjizz.com"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas", action="lista", url=host + "/newest-clips/1.html"))
    itemlist.append(item.clone(title="Popular", action="lista", url=host + "/most-popular/1.html"))
    itemlist.append(item.clone(title="Mejor valorada", action="lista", url=host + "/top-rated-week/1.html"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/recent_%s-1.html" % (host, texto)
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
    matches = soup.find('ul', class_='footer-menu-links').find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        plot = ""
        thumbnail = ""
        url = urlparse.urljoin(item.url, url)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                             thumbnail=thumbnail, plot=plot))
    itemlist.sort(key=lambda x: x.title)
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
    matches = soup.find_all('div', class_='video-thumb')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('div', class_='video-title').text.strip()
        thumbnail = elem.img['data-original']
        time = elem.find('span', class_='time').text.strip()
        quality = elem.find('span', class_='i-hd')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        url = urlparse.urljoin(item.url,url)
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                             plot=plot, contentTitle=title))
    next_page = soup.find('a', class_='pagination-next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'var dataEncodings(.*?)var')
    patron = '"quality":"(\d+)","filename":"([^"]+)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        if ".mp4?" in url: serv= "mp4"
        else: serv="m3u8"
        if not url.startswith("https"):
            url = "https:%s" % url.replace("\\", "")
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'var dataEncodings(.*?)var')
    patron = '"quality":"(\d+)","filename":"([^"]+)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        if ".mp4?" in url: serv= "mp4"
        else: serv="m3u8"
        if not url.startswith("https"):
            url = "https:%s" % url.replace("\\", "")
        itemlist.append(['%sp [%s]' %(quality,serv), url])
    return itemlist
