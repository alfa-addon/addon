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

host = 'http://www.absoluporn.es'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="peliculas", url=host + "/wall-date-1.html"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="peliculas", url=host + "/wall-note-1.html"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="peliculas", url=host + "/wall-main-1.html"))
    itemlist.append( Item(channel=item.channel, title="Mas largos" , action="peliculas", url=host + "/wall-time-1.html"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search-%s-1.html" % texto

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

# &nbsp;<a href="wall-81-1.html" class="link1">Tetas grandes</a><br>

    patron  = '&nbsp;<a href="([^"]+)" class="link1">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = scrapedurl.replace(".html", "_date.html")
        scrapedurl = host +"/" + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

# <div class="thumb-main">
#     <div class="thumb-main-titre"><a href="video7-159775.html" class="link7" title="Czech fantasy orgy">Czech fantasy orgy</a></div>
#     <div class="thumb-video-img"><a href="video7-159775.html"><img id='132984484' src="http://5.196.110.248/absoluporn-12/image/240-180/004/132984484.jpg" class="rot" border="0"></a>
#     <div class="thumb-info">
# 		  <div class="format">16:9</div>
# 			<div class="fullhd">Full HD</div>	</div>
# 	<div class="time">7:25</div>
# 	</div>

    patron  = '<div class="thumb-main-titre"><a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?<div class="time">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year

        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))

    next_page = scrapertools.find_single_match(data, '<span class="text16">\d+</span> <a href="..([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data


    patron  = 'servervideo = \'([^\']+)\'.*?'
    patron += 'path = \'([^\']+)\'.*?'
    patron += 'filee = \'([^\']+)\'.*?'
    matches = scrapertools.find_multiple_matches(data, patron)

    for servervideo,path,filee  in matches:
        scrapedurl = servervideo + path + "56ea912c4df934c216c352fa8d623af3" + filee

        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist
    #     itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    # return itemlist
