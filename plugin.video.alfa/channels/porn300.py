# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.porn300.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="lista", url=host + "/es/videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="lista", url=host + "/es/mas-vistos/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/es/mas-votados/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/es/canales/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "/es/pornostars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/es/categorias/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/es/buscar/?q=%s" % texto
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
    patron  = '<a itemprop="url" href="([^"]+)".*?'
    patron += 'title="([^"]+)">.*?'
    if "/pornostars/" in item.url:
        patron += '<img itemprop="image" src=([^"]+) alt=.*?'
        patron += '</svg>([^<]+)<'
    else:
        patron += '<img itemprop="image" src="([^"]+)" alt=.*?'
        patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        cantidad = re.compile("\s+", re.DOTALL).sub(" ", cantidad)
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/?sort=latest"
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a itemprop="url" href="([^"]+)" data-video-id="\d+" title="([^"]+)">.*?'
    patron += '<img itemprop="thumbnailUrl" src="([^"]+)".*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        cantidad = re.compile("\s+", re.DOTALL).sub(" ", cantidad)
        title = "[COLOR yellow]" + cantidad + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                              plot=plot, contentTitle = contentTitle) )
    next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl  in matches:
        url =  scrapedurl
    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist

