# -*- coding: utf-8 -*-
#------------------------------------------------------------
from core import urlparse as alfa_urlparse
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import urlparse


canonical = {
             'channel': 'jizzbunker', 
             'host': config.get_setting("current_host", 'jizzbunker', default=''), 
             'host_alt': ["https://jizzbunker.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=alfa_urlparse.build_url(host, 'en/newest')))
    itemlist.append(Item(channel=item.channel, title="Popular" , action="lista", url=alfa_urlparse.build_url(host, 'en/straight/popular1')))
    itemlist.append(Item(channel=item.channel, title="Tendencia" , action="lista", url=alfa_urlparse.build_url(host, 'en/straight/trending')))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=alfa_urlparse.build_url(host, 'en/channels/alphabetically')))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    _url_query_texto = texto
    texto = texto.replace(" ", "+")
    item.url = alfa_urlparse.build_url(host, 'en/search', query=[('query', u'{}/'.format(u'{}'.format(_url_query_texto)))])
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
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)" class="category-card".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'count">([^<]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for url,thumbnail,title,cantidad in matches:
        plot = ""
        url = url.replace("channel", "channel30")
        title = "%s (%s)" %(title,cantidad.replace(' videos', ''))
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail , thumbnail=thumbnail, plot=plot))
    itemlist.sort(key=lambda x: x.title)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)" class="video-card".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'duration">([^<]+)</'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,thumbnail,title,duracion in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" %(duracion,title)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail , thumbnail=thumbnail, plot=plot))
    next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" [^<]+>Next')
    if next_page !="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = 'type:\'video/mp4\',src:\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https", "http")
        itemlist.append(Item(channel=item.channel, action="play", title="Directo", url=scrapedurl))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = 'type:\'video/mp4\',src:\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https", "http")
        itemlist.append(Item(channel=item.channel, action="play", contentTitle=item.title, url=scrapedurl))
    return itemlist