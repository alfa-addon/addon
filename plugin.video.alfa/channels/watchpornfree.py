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
from core import servertools
from core.item import Item
from core import httptools
from bs4 import BeautifulSoup
from modules import autoplay

list_quality = []
list_servers = ['mangovideo']

#  https://mangoporn.net   
#  https://pandamovies.pw/ & https://xxxparodyhd.net & https://streamporn.pw/ & https://streamporn.li 
#  https://www.netflixporno.net & https://watchpornfree.info & https://losporn.org/ 
#  https://xxxscenes.net & https://watchfreexxx.net/ & https://speedporn.net &https://pornkino.cc/
canonical = {
             'channel': 'watchpornfree', 
             'host': config.get_setting("current_host", 'watchpornfree', default=''), 
             'host_alt': ["https://watchpornfree.info/"], 
             'host_black_list': [], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*hreflang="?en"?'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info("")
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Videos" , action="submenu", url=host + "/scenes/"))
    
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="lista", url=host))
    itemlist.append(Item(channel=item.channel, title=".........Mas vistas" , action="lista", url=host + "?v_sortby=views"))
    itemlist.append(Item(channel=item.channel, title=".........Mas valoradas" , action="lista", url=host + "?r_sortby=highest_rated"))
    itemlist.append(Item(channel=item.channel, title="Parodia" , action="lista", url=host + "/category/parodies"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Year" , action="categorias", url=host))
    # itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=item.url))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=item.url + "?v_sortby=views"))
    itemlist.append(Item(channel=item.channel, title="Mas valorados" , action="lista", url=item.url + "?r_sortby=highest_rated"))
    itemlist.append(Item(channel=item.channel, title="Destacados" , action="lista", url=item.url + "category/featured-scenes/"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=item.url))
    # itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host, vid = "vid"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url))
    return itemlist


def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (item.url, texto)
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
    soup = create_soup(item.url)#.find('ul', class_='top-menu')
    if "Categorias" in item.title:
        matches = soup.find_all(href=re.compile("/category/"))
    elif "Year" in item.title:
        matches = soup.find_all(href=re.compile("/release-year/"))
    else:
        matches = soup.find_all(href=re.compile("/director/"))
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        plot = ""
        thumbnail = ""
        if not url.startswith("https"):
            url = "https:%s" % url
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail, plot=plot))
    if "Year" in item.title:
        itemlist.reverse()
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='TPost')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('div', class_='Title').text.strip()
        thumbnail = elem.img['src']
        if "/svg" in thumbnail:
            thumbnail = elem.img['data-lazy-src']

        time = elem.find('span', class_='duration')
        if time:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text.strip(),title)
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, contentTitle=title, infoLabels={"year": ""} ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    video_urls = []
    soup = create_soup(item.url).find('div', id='pettabs')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        if not url in video_urls:
            video_urls += url
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language='VO',contentTitle = item.contentTitle))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
