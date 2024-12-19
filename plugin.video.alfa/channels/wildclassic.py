# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse

host = 'https://www.wildclassic.com'

#### ERROR AÑ REPRODUCIR DIRECTOS

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/vintage/newest-videos/", page=host + "/vintage/newest-videos/" ))
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/vintage/"))
    itemlist.append(item.clone(title="Mas largos" , action="lista", url=host + "/vintage/longest-videos/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?query=%s" % (host, texto)
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" class="cle">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    Accept= "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    data = httptools.downloadpage(item.url, headers={'Referer': item.page, 'Accept': Accept}).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li>.*?'
    patron += '<a class=thumba href="([^"]+)".*?'
    patron += '<img alt="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<strong>([^<]+)</strong>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle ,scrapedthumbnail,scrapedtime in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime, scrapedtitle)
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
                              # "Página Siguiente >>"  headers cookie
    next_page = scrapertools.find_single_match(data, '<li class="next visible"><a href="([^"]+)"')
    if next_page =="":
        next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if next_page:
        item.page = item.url
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    url = scrapertools.find_single_match(data, '<iframe src=\'([^\']+)\'')
    url = urlparse.urljoin(item.url,url)
    data = httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data, 'src="([^"]+)"')
    url = urlparse.urljoin(item.url, url)
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    url = scrapertools.find_single_match(data, '<iframe src=\'([^\']+)\'')
    url = urlparse.urljoin(item.url,url)
    data = httptools.downloadpage(url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data, 'src="([^"]+)"')
    # url = url.replace("%3D", "=").replace("%2B", "+").replace("%2F", "/")
    # url = urlparse.unquote(url)
    # url += "|Referer=%s" % url
    # url = urlparse.urljoin(item.url, url)
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


