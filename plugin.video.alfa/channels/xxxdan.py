# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup

canonical = {
             'channel': 'xxxdan', 
             'host': config.get_setting("current_host", 'xxxdan', default=''), 
             'host_alt': ["https://xxxdan.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "newest"))
    itemlist.append(Item(channel=item.channel, title="Popular" , action="lista", url=host + "straight/popular7"))
    itemlist.append(Item(channel=item.channel, title="HD" , action="lista", url=host + "channel30/hd"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="canal", url=host + "partners"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "channels"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch?query=%s" % (host, texto)
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
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='category-list__item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail = ""
        cantidad = elem.find('span', class_='category-list__count')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              thumbnail=thumbnail , fanart=thumbnail, plot=plot) )
    return itemlist


def canal(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('a', class_='channel-card')
    for elem in matches:
        url = elem['href']
        # title = elem.img['alt']
        title = elem.find('div', class_='channel-card__name').text.strip()
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='channel-card__count')
        title = "%s (%s)" % (title,cantidad.text.strip())
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot))
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
    matches = soup.find_all('a', class_='video-card')
    for elem in matches:
        url = elem['href']
        # title = elem.img['alt']
        title = elem.find('div', class_='video-card__title').text.strip()
        thumbnail = elem.img['src']
        time = elem.find('span', class_='video-card__duration').text.strip()
        title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = soup.find('link', rel='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    scrapedurl = scrapertools.find_single_match(data, 'src:\'([^\']+)\'')
    scrapedurl = scrapedurl.replace("https","http")
    itemlist.append(Item(channel=item.channel, action="play", title="Directo", url=scrapedurl, contentTitle=item.contentTitle ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    scrapedurl = scrapertools.find_single_match(data, 'src:\'([^\']+)\'')
    scrapedurl = scrapedurl.replace("https","http")
    itemlist.append(Item(channel=item.channel, action="play", url=scrapedurl, contentTitle=item.contentTitle ))
    return itemlist
