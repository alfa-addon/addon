# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import urlparse

canonical = {
             'channel': 'zmovs', 
             'host': config.get_setting("current_host", 'zmovs', default=''), 
             'host_alt': ["https://zmovs.com/"], 
             'host_black_list': [], 
             'pattern': ['<li class="active"><a href="?([^"|\s*]+)["|\s*]'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
url_api = host + "?ajax=1&type="
# httptools.downloadpage(url, canonical=canonical).data    #categorias

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=url_api + "most-recent&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorados" , action="lista", url=url_api + "top-rated&page=1"))
    itemlist.append(Item(channel=item.channel, title="Longitud" , action="lista", url=url_api + "long&page=1"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = scrapertools.find_single_match(data, '<ul class="sidebar-nav">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a class="category-item" href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        url = urlparse.urljoin(host,scrapedurl)
        url = "%s?ajax=1&type=most-recent&page=1" %url  #most-recent
        scrapedplot = ""
        thumbnail = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for Video in data["data"]:
        duration = Video["duration"]
        title = Video["videoTitle"]
        title = "[COLOR yellow]%s[/COLOR] %s" % (duration,title)
        src= Video["src"]
        domain=""
        thumbnail = src.get('domain', domain) + src.get('pathMedium', domain)+"1.jpg"
        url= Video["urls_CDN"]
        url= url.get('480', domain)
        url = url.replace("/\n/", "/")
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    Actual = int(scrapertools.find_single_match(item.url, '&page=([0-9]+)'))
    if data["pagesLeft"] - 1 > Actual:
        scrapedurl = item.url.replace("&page=" + str(Actual), "&page=" + str(Actual + 1))
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=scrapedurl))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title="Directo", url=item.url) )
    return itemlist

