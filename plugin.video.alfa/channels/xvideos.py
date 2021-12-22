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

host = 'https://www.xvideos.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Lo mejor" , action="lista", url=host + "/best/"))
    itemlist.append(item.clone(title="Pornstar" , action="catalogo", url=host + "/pornstars-index/from/worldwide"))
    itemlist.append(item.clone(title="WebCAM" , action="catalogo", url=host + "/webcam-models-index"))
    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + "/channels-index/from/worldwide/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/tags"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?k=%s&sort=uploaddate" % (host, texto)
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
    soup = create_soup(item.url).find('ul', id='tags')
    matches = soup.find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.b.text.strip()
        cantidad = elem.span.text.strip()
        url = url.replace("/tags/", "/tags/s:uploaddate/")
        url = urlparse.urljoin(item.url,url)
        title = "%s (%s)" % (title, cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail="" ) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', id=re.compile(r"^profile_\w+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.find(class_='profile-name')
        if "Canal" in item.title:
            title= title.text.strip()
        else:
            title= title.a.text.strip()
        thumbnail = elem.script.text.strip()
        thumbnail = scrapertools.find_single_match(thumbnail, 'src="([^"]+)"')
        cantidad = elem.find('span', class_='with-sub')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        url += "/videos/new/0"
        itemlist.append(item.clone(action="lista", title=title, url=url,
                                   fanart=thumbnail, thumbnail=thumbnail))
    next_page = soup.find('a', class_='next-page')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', id=re.compile(r"^video_\d+"))
    for elem in matches:
        url = elem.a['href']
        if "/prof-video-click/" in url:
            url = scrapertools.find_single_match(str(url), '/(\d+/[A-z0-9_]+)')
            url = "/video%s" %url
        title = elem.find('p', class_='title').a['title']
        thumbnail = elem.img['data-src']
        thumbnail = thumbnail.replace("THUMBNUM.", "9.")
        time = elem.find('span', class_='duration').text.strip()
        quality = elem.find('span', class_='video-hd-mark')
        url = urlparse.urljoin(host,url)
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality.text.strip(),title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next-page')
    if next_page:
        next_page = next_page['href']
        if "#" in next_page:
            next_page = scrapertools.find_single_match(str(next_page), '(\d+)')
            next_page = re.sub(r"/\d+", "/{0}".format(next_page), item.url)
        else:
            next_page = urlparse.urljoin(item.url,next_page)
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