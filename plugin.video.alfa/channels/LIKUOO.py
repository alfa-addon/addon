# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb
from core import jsontools

## italiafilm                                             \'([^\']+)\'

host = 'http://www.likuoo.video'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/all-channels/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<img class="thumb" src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        thumbnail = "http:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=thumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="category round">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<div class="item_p">.*?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedthumbnail = "https:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')



    patron = '<div class="item">.*?<a href="([^"]+)" title="(.*?)">.*?src="(.*?)".*?<div class="runtime">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        scrapedtime = scrapedtime.replace("m", ":").replace("s", " ")
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " +scrapedtitle

        contentTitle = title
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = "https:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li class="next"><a href="/latest-updates/2/" data-action="ajax" data-container-id="list_videos_latest_videos_list_pagination" data-block-id="list_videos_latest_videos_list" data-parameters="sort_by:post_date;from:2">Next</a></li>


    next_page_url = scrapertools.find_single_match(data,'...<a href="([^"]+)" class="next">&#187;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#    \'([^\']+)\'    window.open('https://openload.co/f/dUwrUKJePqo/Alesandra_720p.mp4', '_blank');



    scrapedurl = scrapertools.find_single_match(data, 'window.open\(\'([^\']+)\'')

#    for scrapedurl  in matches:
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist
'''
def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
