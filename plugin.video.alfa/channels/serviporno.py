# -*- coding: utf-8 -*-
import re

from core import httptools
from core import scrapertools
from core import urlparse
from core.item import Item
from core import servertools
from platformcode import config, logger

canonical = {
             'channel': 'serviporno', 
             'host': config.get_setting("current_host", 'serviporno', default=''), 
             'host_alt': ["https://www.serviporno.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="videos", title="Útimos videos", url=host))
    itemlist.append(Item(channel=item.channel, action="videos", title="Más vistos", url=host + "mas-vistos/"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Más votados", url=host + "mas-votados/"))
    itemlist.append(Item(channel=item.channel, action="chicas", title="Chicas", url=host + "pornstars/"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Canal", url=host + "sitios/"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorias", url= host + "categorias/"))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", last=""))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = '%ssearch/?q=%s' % (host, texto)
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron = '<div class="wrap-box-escena.*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<h4.*?<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for thumbnail, url, title in matches:
        url = urlparse.urljoin(item.url, url)
        itemlist.append(Item(channel=item.channel, action='videos', title=title, url=url,
                             thumbnail=thumbnail, fanart=thumbnail))
    if "categorias/" in item.url:
        itemlist.sort(key=lambda x: x.title)
    # Paginador   "Página Siguiente >>"
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def chicas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron = '<div class="box-chica">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src=\'([^\']+.jpg)\'.*?'
    patron += '<h4><a href="[^"]+">([^<]+)</a></h4>.*?'
    patron += '<a class="total-videos".*?>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, videos in matches:
        url = urlparse.urljoin(item.url, url)
        title = "%s (%s)" % (title, videos)
        itemlist.append(Item(channel=item.channel, action='videos', title=title, url=url,
                             thumbnail=thumbnail, fanart=thumbnail))
    # Paginador 
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="chicas", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = '<div class="wrap-box-escena.*?'
    # patron += '<div class="box-escena">.*?'
    patron += '<a\s+href="([^"]+)".*?'
    patron += '"([^"]+.jpg)".*?'
    patron += 'alt="([^"]+)".*?'
    # patron += '<h4><a href="[^"]+">([^<]+)<.*?'
    patron += '<div class="duracion">([^"]+) min<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, thumbnail, title,duration in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (duration, title)
        url = urlparse.urljoin(item.url, url)
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle = title, url=url, 
                             thumbnail=thumbnail, fanart=thumbnail))
    # Paginador
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="videos", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if ">Pornostars:<" in data:
        data = scrapertools.find_single_match(data, '>Pornostars:</strong>(.*?)</p')
        pornstars = scrapertools.find_multiple_matches(data, "'link12'\s+>([^<]+)")
        pornstar = ' & '.join(pornstars)
        pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
        lista = item.title.split()
        if "HD" in item.title:
            lista.insert (4, pornstar)
        else:
            lista.insert (2, pornstar)
        item.contentTitle = ' '.join(lista)
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist