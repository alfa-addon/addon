# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
import base64

host = 'http://www.alsoporn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    # itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/en/g/All/new/1"))
    itemlist.append( Item(channel=item.channel, title="Top" , action="lista", url=host + "/g/All/top/1"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/=%s/" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)" />'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl, 
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="alsoporn_prev">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += '<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        if not "0:00" in scrapedtime:
            itemlist.append( Item(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                                  fanart=thumbnail, plot=plot, contentTitle = scrapedtitle))

    next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)" target="_self"><span class="alsoporn_page">NEXT</span></a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'([^\']+)\'')
    data = httptools.downloadpage(scrapedurl).data
    scrapedurl1 = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    scrapedurl1 = scrapedurl1.replace("//www.playercdn.com/ec/i2.php?url=", "")
    scrapedurl1 = base64.b64decode(scrapedurl1 + "=")
    logger.debug(scrapedurl1)
    data = httptools.downloadpage(scrapedurl1).data
    if "xvideos" in scrapedurl1:
        scrapedurl2 = scrapertools.find_single_match(data, 'html5player.setVideoHLS\(\'([^\']+)\'\)')
    if "xhamster" in scrapedurl1:
        scrapedurl2 = scrapertools.find_single_match(data, '"[0-9]+p":"([^"]+)"').replace("\\", "")

    logger.debug(scrapedurl2)
    itemlist.append(item.clone(action="play", title=item.title, url=scrapedurl2))
    return itemlist

