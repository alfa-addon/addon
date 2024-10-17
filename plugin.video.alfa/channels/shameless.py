# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

canonical = {
             'channel': 'shameless', 
             'host': config.get_setting("current_host", 'shameless', default=''), 
             'host_alt': ["https://www.shameless.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "search/?sort_by=post_date&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Pornstar" , action="categorias", url=host + "models/?&sort_by=model_id&from=1"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories/?sort_by=category_id&from=1"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch/?q=%s&from_videos=1" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item.*?'
    patron += 'href="([^"]+)" title="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<li class="info-item">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        title = "%s (%s)" % (scrapedtitle,cantidad.replace(" videos", ""))
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, 'data-parameters="([^"]+)"')
    if next_page:
        next_page = next_page.split(":")[-1]
        if "from_videos" in item.url:
            next_page = re.sub(r"&from_videos=\d+", "&from_videos={0}".format(next_page), item.url)
        else:
            next_page = re.sub(r"&from=\d+", "&from={0}".format(next_page), item.url)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item.*?'
    patron += 'href="([^"]+)" title="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<div class="card-time">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" %(scrapedtime, scrapedtitle)
        thumbnail = scrapedthumbnail + "|Referer=%s" %host
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, 'data-parameters="([^"]+)"')
    if next_page:
        next_page = next_page.split(":")[-1]
        if "from_videos" in item.url:
            next_page = re.sub(r"&from_videos=\d+", "&from_videos={0}".format(next_page), item.url)
        else:
            next_page = re.sub(r"&from=\d+", "&from={0}".format(next_page), item.url)
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
    
    data = httptools.downloadpage(item.url).data
    if ">Models:<" in data:
        data = scrapertools.find_single_match(data, '>Models:</span>.*?<ul>(.*?)</ul')
        pornstars = scrapertools.find_multiple_matches(data, ">([^<]+)</a")
        pornstar = ' & '.join(pornstars)
        pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
        lista = item.title.split()
        if "HD" in item.title:
            lista.insert (4, pornstar)
        else:
            lista.insert (2, pornstar)
        item.contentTitle = ' '.join(lista)
    
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist