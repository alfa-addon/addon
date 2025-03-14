# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import re

from platformcode import config, logger, unify
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from core import urlparse
from modules import autoplay
from bs4 import BeautifulSoup

UNIFY_PRESET = config.get_setting("preset_style", default="Inicial")
color = unify.colors_file[UNIFY_PRESET]

list_quality = ['default']
list_servers = ['mangovideo']

#  https://mangoporn.net   
#  https://pandamovies.pw/ & https://xxxparodyhd.net & https://streamporn.pw/ & https://streamporn.li 
#  https://www.netflixporno.net & https://watchpornfree.info & https://losporn.org/ 
#  https://xxxscenes.net & https://watchfreexxx.net/ & https://speedporn.net &https://pornkino.cc/
canonical = {
             'channel': 'pandamovie', 
             'host': config.get_setting("current_host", 'pandamovie', default=''), 
             'host_alt': ["https://pandamovies.pw/"], 
             'host_black_list': ["https://pandamovies.org/", "https://streamporn.pw/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="lista", url=host + "movies"))
    itemlist.append(Item(channel=item.channel, title="Year", action="categorias", url=host + "movies", id="menu-item-24"))
    itemlist.append(Item(channel=item.channel, title="Canal", action="categorias", url=host + "movies", id="menu-item-23"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=host + "movies", id="menu-item-25"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + "movies"))
    itemlist.append(Item(channel=item.channel, title="-------------------"))
    itemlist.append(Item(channel=item.channel, title="Escenas", action="submenu", url=host + "xxxscenes/"))
    
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Ultimos", action="lista", url=item.url + "movies"))
    itemlist.append(Item(channel=item.channel, title="Canal", action="categorias", url=item.url , id="menu-item-38820"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=item.url,  id="menu-item-38760"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch/%s" % (item.url, texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('ul', class_='top-menu').find('li', id=item.id)
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        plot = ""
        thumbnail = ""
        if not url.startswith("https"):
            url = "https:%s" % url
        if "#" not in url:
            itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                                 thumbnail=thumbnail, plot=plot))
    if "Year" in item.title:
        itemlist.reverse()
    else:
        itemlist.sort(key=lambda x: x.title)
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
    matches = soup.find_all('div', class_='ml-item')
    for elem in matches:
        year = ""
        url = elem.a['href']
        title = elem.a['oldtitle']
        thumbnail = elem.img['src']
        if "svg" in thumbnail:
            thumbnail = elem.img['data-lazy-src']
        if "xxxscenes" not in item.url:
            year = elem.find('div', class_='jtip-top').a
            if year:
                year = year.text.strip()
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, contentTitle=title, infoLabels={"year": year} ))
    next_page = soup.find('li', class_='active')
    if next_page and next_page.find_next_sibling("li"):
        next_page = next_page.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    video_urls = []
    soup = create_soup(item.url)
    pornstars = soup.find('div', class_='mvic-info').find_all('a', href=re.compile("/actors/"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    if "N/A" not in pornstar:
        pornstar = "[COLOR %s]%s[/COLOR]" % (color.get('rating_3',''), pornstar)
    else:
        pornstar = ""
    plot = pornstar
    # lista = item.contentTitle.split()
    # lista.insert (0, pornstar)
    # item.contentTitle = ' '.join(lista)    
    matches = soup.find('div', id='pettabs').find_all('a')
    for elem in matches:
        url = elem['href']
        url = url.split("?link=")[-1]
        if url not in video_urls:
            video_urls += url
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', plot=plot, language='VO',contentTitle = item.contentTitle))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
