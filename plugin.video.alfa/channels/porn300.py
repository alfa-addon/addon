# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse

canonical = {
             'channel': 'porn300', 
             'host': config.get_setting("current_host", 'porn300', default=''), 
             'host_alt': ["https://www.porn300.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "?page=1"))  # "en_US/ajax/page/list_videos/?page=1"
    itemlist.append(Item(channel=item.channel, title="Mas visto" , action="lista", url=host + "most-viewed/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "top-rated/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "channels/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "pornstars/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host))
    itemlist.append(Item(channel=item.channel, title="---------"))
    itemlist.append(Item(channel=item.channel, title="Gay" , action="submenu", url=host + "gay/"))
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=item.url + "?page=1"))  # "en_US/ajax/page/list_videos/?page=1"
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=item.url + "channels/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=item.url + "pornstars/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=item.url + "categories/?page=1"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch/?q=%s&page=1" % (item.url, texto)
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
    if "categories" in item.url:
        patron  = '<li class="grid__item grid__item--category">.*?'
        patron += '<a href="([^"]+)".*?'
        patron += '(<img[^>]+).*?'
        patron += '>([^<]+)</h3>.*?'
        patron += '</svg>([^<]+)<'
    else:
        patron  = '<a itemprop="url" href="/([^"]+)".*?'
        patron += '(<img[^>]+).*?'
        patron += 'itemprop="name">([^<]+)</h3>.*?'
        if "pornstars" in item.url:
            patron += '</svg>([^<]+)</li'
        else:
            patron += '</svg>([^<]+)</small'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        cantidad = re.compile("\s+", re.DOTALL).sub(" ", cantidad)
        title = "%s (%s)" %(scrapedtitle,cantidad)
        thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'src="([^"]+)"')
        if "base64" in thumbnail:
            thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'data-src="([^"]+)"')
        if "categories" not in item.url:
            scrapedurl = scrapedurl.replace("channel/", "producer/")
            scrapedurl = "/en_US/ajax/page/show_%s?page=1" %scrapedurl
        else:
            scrapedurl = "%s%s?page=1" %( host,scrapedurl)
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=scrapedplot) )
    if "/categories/" in item.url:
        itemlist.sort(key=lambda x: x.title)
    next_page = scrapertools.find_single_match(data,'href="([^"]+)" title="(?:Next|Siguiente)"')
    # next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" data-video-id=.*?'
    patron += '(<img[^>]+).*?'
    patron += '<span class="duration-video">([^<]+)<.*?'
    patron += '<h3 [^>]+>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtime,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedtime = scrapedtime.strip()
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime,scrapedtitle)
        contentTitle = title
        thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'src="([^"]+)"')
        if "base64" in thumbnail:
            thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'data-src="([^"]+)"')
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title , url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle) )
    next_page = scrapertools.find_single_match(data,'href="([^"]+)" title="(?:Next|Siguiente)"')
    # next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
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
    pornstars = scrapertools.find_single_match(data, "gtmData.pornStar = '([^']+)'")
    pornstars = pornstars.split('|')
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    lista = item.contentTitle.split()
    lista.insert (2, pornstar)
    item.contentTitle = ' '.join(lista)    

    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist