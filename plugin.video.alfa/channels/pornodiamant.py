# -*- coding: utf-8 -*-
#------------------------------------------------------------

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse

####   SOURTYPE  [A-z0-9-ß]+

host = ''
canonical = {
             'channel': 'pornodiamant', 
             'host': config.get_setting("current_host", 'pornodiamant', default=''), 
             'host_alt': ["https://www.pornobereich.com/"], 
             'host_black_list': ["https://www.pornodiamant.com/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "filme/"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "channels/"))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="catalogo", url=host + "pornostars/"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssuchen/?q=%s" % (host,texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a itemprop="url" href="([^"]+)".*?'
    patron += 'src="([^"]+)"\s+data-src="([^"]+)"\s+alt="([^"]+)".*?'
    patron += '</svg>([^<]+)</'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,thumbnail,thumb2,scrapedtitle, cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad.strip())
        if "gif" in thumbnail:
            thumbnail = thumb2
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" data-category-gtmname="([^"]+)".*?'
    patron += 'src="([^"]+)"\s+data-src="([^"]+)".*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,thumbnail,thumb2,cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad.strip())
        if "gif" in thumbnail:
            thumbnail = thumb2
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" data-video-id.*?'
    patron += 'src="([^"]+)"\s+data-src="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,thumbnail,thumb2,scrapedtitle,time in matches:
        time = time.strip()
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        if "gif" in thumbnail:
            thumbnail = thumb2
        url = urlparse.urljoin(item.url,scrapedurl)
        url = urlparse.unquote(url)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    if "video-footer__pornstars" in data:
        data = scrapertools.find_single_match(data, '"video-footer__pornstars">(.*?)</ul')
        pornstars = scrapertools.find_multiple_matches(data, ">([^<]+)</a")
        pornstar = ' & '.join(pornstars)
        pornstar = "[COLOR orange]%s[/COLOR]" % (pornstar)
        lista = item.title.split()
        if "HD" in item.title:
            lista.insert (4, pornstar)
        else:
            lista.insert (2, pornstar)
        item.contentTitle = ' '.join(lista)
    
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist

