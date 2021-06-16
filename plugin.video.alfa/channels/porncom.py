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

host = 'https://www.porn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/channels"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/videos/search?q=%s" % (host,texto)
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
    matches = soup.find_all('div', class_='list-global__item')
    for elem in matches:
        elem = elem.find('a', class_=False)
        url = elem['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-src']
        cantidad = elem.find('div', class_='list-global__details')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    if "Categorias" in item.title:
        itemlist.sort(key=lambda x: x.title)
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
    # next_page = scrapertools.find_single_match(data, '<a class="next pagination__number" href="([^"]+)" rel="nofollow">Next')
    # if next_page:
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
    matches = soup.find_all('div', class_='list-global__item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='list-global__duration').text.strip()
        server = elem.find('div', class_='list-global__details').a.text.strip()
        title = "[COLOR yellow]%s[/COLOR] [%s] %s" % (time, server, title)
        url = scrapertools.find_single_match(url,'.*?5odHRwczov([^/]+)/\d+/\d+')
        url = url.replace("%3D", "=").replace("%2F", "/")
        plot = ""
        itemlist.append(item.clone(action="play", title=title, contentTitle = title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist

# https://www.pornlib.com/video/horny-amateur-couple-make-their-first-homemade-video-222012

# https://www.milffox.com/porn-movies/Latina-Stepmom-Kailani-Kai-With-Big-Tits-Has-Sex-With-Her-Stepson/
# https://porntop.com/video/238835/deepika-bernie-svintis-our-boobs-are-the-same/
# https://ebonyo.com/black-chick-with-big-boobs-tori-taylor-riding-white-man/
# https://www.jacquieetmicheltv.net/en/videos/show/1672/ania-and-caroline-two-beautiful-lesbian-milfs-with-big-tits.html
# https://www.stileproject.com/video/amy-rogue-takes-her-step-brothers-cock-in-her-pussy-9913541.html
# https://www.pornrabbit.com/video/yuzuna-oshima-hot-japanese-girl-being-fucked-39797102.html var desktopFile='https://cdn.pornrabbit.com/media/videos/8/2/8/8/7/82887c73cecbf95d298b8458a1fa67ba.mp4'

def play(item):
    logger.info()
    itemlist = []
    import base64
    url = base64.b64decode(item.url)
    url = url.decode("utf8")
    url = "https:/%s" % url
    if "vid.com/v/" in url:
        url = httptools.downloadpage(url).url
    logger.debug(url)
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

