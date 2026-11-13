# -*- coding: utf-8 -*-
#------------------------------------------------------------
from core import urlparse as alfa_urlparse
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import jsontools as json
from core import urlparse


canonical = {
             'channel': 'sexu', 
             'host': config.get_setting("current_host", 'sexu', default=''), 
             'host_alt': ["https://sexu.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=alfa_urlparse.build_url(host, 'new')))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=alfa_urlparse.build_url(host, 'engaging')))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=alfa_urlparse.build_url(host, 'all')))
    itemlist.append(Item(channel=item.channel, title="Mas comentados" , action="lista", url=alfa_urlparse.build_url(host, 'trending')))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="categorias", url=alfa_urlparse.build_url(host, 'pornstars')))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=alfa_urlparse.build_url(host, 'categories', query='sort=name')))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    _url_query_texto = texto
    texto = texto.replace(" ", "+")
    item.url = alfa_urlparse.build_url(host, 'search', query=[('q', u'{}'.format(_url_query_texto)), ('st', 'upload')])
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
    patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?'
    patron += '(?:data-src|src)="([^"]+)".*?'
    patron += '<div class="item__counter">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad)
        if not scrapedthumbnail.startswith("https"):
            thumbnail = "http:%s" % scrapedthumbnail
        url = urlparse.urljoin(host,scrapedurl)
        url = alfa_urlparse.build_url(url, query='st=upload')
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, '<a class="pagination__arrow pagination__arrow--next" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist

def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a class="item__main" href="/([^"]+)/" title="([^"]+)".*?'
    patron += '(?:data-src|src)="([^"]+)".*?'
    patron += '<div class="item__counter">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,time in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        if not scrapedthumbnail.startswith("https"):
            thumbnail = "http:%s" % scrapedthumbnail
        url = 'videoId=%s' %scrapedurl
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a class="pagination__arrow pagination__arrow--next" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = alfa_urlparse.build_url(host, 'api/video-info')
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = httptools.downloadpage(url, post=item.url, headers=headers, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for cat in  JSONData["sources"]:
        url = cat["src"]
        quality = cat["quality"]
        if not url.startswith("https"):
            url = "https:%s" % url
        itemlist.append(Item(channel=item.channel, action="play", title=quality, url=url) )
    return itemlist[::-1]


def play(item):
    logger.info()
    itemlist = []
    url = alfa_urlparse.build_url(host, 'api/video-info')
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = httptools.downloadpage(url, post=item.url, headers=headers, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for cat in  JSONData["sources"]:
        url = cat["src"]
        quality = cat["quality"]
        if not url.startswith("https"):
            url = "https:%s" % url
        itemlist.append(['[sexu] %s' %quality, url])
    return itemlist[::-1]