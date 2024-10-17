# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import urlparse

host = ''
canonical = {
             'channel': 'motherless', 
             'host': config.get_setting("current_host", 'motherless', default=''), 
             'host_alt': ["https://motherless.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host +"videos/recent"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "videos/viewed"))
    itemlist.append(Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "videos/popular"))
    itemlist.append(Item(channel=item.channel, title="Mas comentado" , action="lista", url=host + "videos/commented"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch/videos?term=%s&size=0&range=0&sort=date" % (host, texto)
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
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    data = scrapertools.find_single_match(data, '<div class="menu-categories-tab"(.*?)<div class="menu-categories-tab"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\\", "", data)
    patron = '<a href="([^"]+)" class="[^"]+">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist



def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="thumb.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<span class="size">([^<]+)<.*?'
    patron += 'src="([^"]+.jpg)".*?'
    patron += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,time,scrapedthumbnail,scrapedtitle in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        thumbnail = scrapedthumbnail
        thumbnail += "|verifypeer=false"
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="pop" rel="next"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    url = scrapertools.find_single_match(data, 'fileurl = \'([^,\']+)\'')
    itemlist.append(Item(channel=item.channel, action="play",title="Directo", url=url, contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    url = scrapertools.find_single_match(data, 'fileurl = \'([^,\']+)\'')
    itemlist.append(Item(channel=item.channel, action="play", url=url, contentTitle=item.contentTitle))
    return itemlist