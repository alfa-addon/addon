# -*- coding: utf-8 -*-
#------------------------------------------------------------

import re
import urlparse
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger

host = 'https://es.redtube.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/mostviewed"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstar"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?search=%s" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a class="pornstar_link js_mpop js-pop" href="([^"]+)".*?"([^"]+)"\s+title="([^"]+)".*?<div class="ps_info_count">\s+([^"]+)\s+Videos'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle +  " [COLOR yellow]" + cantidad + "[/COLOR] "
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a id="wp_navNext" class="js_pop_page" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="category_item_wrapper">.*?<a href="([^"]+)".*?data-thumb_url="([^"]+)".*?alt="([^"]+)".*?<span class="category_count">\s+([^"]+) Videos'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<img id="img_.*?data-path="([^"]+)".*?<span class="duration">(.*?)</a>.*?<a title="([^"]+)" href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,duration,scrapedtitle,scrapedurl in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        scrapedhd = scrapertools.find_single_match(duration, '<span class="hd-video-text">(.*?)</span>')
        if scrapedhd == 'HD':
            duration = scrapertools.find_single_match(duration, 'HD</span>(.*?)</span>')
            title = "[COLOR yellow]" + duration + "[/COLOR] " + "[COLOR red]" + scrapedhd  + "[/COLOR]  " + scrapedtitle
        else:
            title = "[COLOR yellow]" + duration + "[/COLOR] " + scrapedtitle
        title = title.replace("    </span>", "").replace("    ", "")
        scrapedthumbnail = scrapedthumbnail.replace("{index}.", "1.")
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<a id="wp_navNext" class="js_pop_page" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '"defaultQuality":true,"format":"",.*?"videoUrl"\:"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl  in matches:
        url =  scrapedurl.replace("\/", "/")
    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist

