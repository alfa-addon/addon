# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup
from modules import autoplay
from platformcode import unify

# https://letsjerk.tv https://letsjerk.to

UNIFY_PRESET = config.get_setting("preset_style", default="Inicial")
color = unify.colors_file[UNIFY_PRESET]

list_language = []
list_quality = []
list_servers = []

canonical = {
             'channel': 'letsjerk', 
             'host': config.get_setting("current_host", 'letsjerk', default=''), 
             'host_alt': ["https://letsjerk.tv/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# No se ven thumbnail

def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "?order=newest"))
    itemlist.append(Item(channel=item.channel, title="Mas valorados" , action="lista", url=host + "?order=rating_month"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "?order=views_month"))
    itemlist.append(Item(channel=item.channel, title="Mas comentado" , action="lista", url=host + "?order=comments_month"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories"))
    
    autoplay.show_option(item.channel, itemlist)
    
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (host,texto)
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
    matches = soup.find('div', class_='thumbs').find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('div', class_='taxonomy-name').text.strip()
        thumbnail = ""
        cantidad = elem.find('div', class_='number').text.strip()
        title = "%s (%s)" % (title, cantidad)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find('div', class_='thumbs').find_all('li')
    for elem in matches:
        quality = ""
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-original']
        time = elem.find('em', class_='time_thumb').em#.text.strip()
        quality = elem.find('i', class_='quality')
        if quality:
            quality = "[COLOR %s]HD[/COLOR]" %color.get('quality','')
        if time:
            title = "[COLOR %s]%s[/COLOR] %s %s" % (color.get('year',''),time.text.strip(),quality,title)
        elif quality:
            title = "%s %s" % (quality,title)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, contentTitle = title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    
    if soup.find_all('a', href=re.compile("/performer/[A-z0-9-]+/")):
        pornstars = soup.find_all('a', href=re.compile("/performer/[A-z0-9-]+/"))
        for x, value in enumerate(pornstars):
            pornstars[x] = value.get_text(strip=True)
        pornstar = ' & '.join(pornstars)
        pornstar = "[COLOR %s]%s[/COLOR]" % (color.get('rating_3',''), pornstar)
        lista = item.contentTitle.split('[/COLOR]')
        pornstar = pornstar.replace('[/COLOR]', '')
        pornstar = ' %s' %pornstar
        if color.get('quality','') in item.contentTitle:
            lista.insert (2, pornstar)
        else:
            lista.insert (1, pornstar)
        item.contentTitle = '[/COLOR]'.join(lista)
    
    matches = soup.find('ul', class_='post-tape').find_all("a")
    for elem in matches:
        soup = create_soup(elem['href'])
        url = soup.find('div', class_='video-container').iframe['src']
        itemlist.append(Item(channel=item.channel, action="play", title="%s", contentTitle = item.contentTitle, url=url) )
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
