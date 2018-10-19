# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb

## italiafilm                                             \'([^\']+)\'

host = 'http://www.upvintageporn.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Top" , action="peliculas", url=host + "/all-top/1/"))
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/all-new/1/"))
    itemlist.append( Item(channel=item.channel, title="Duracion" , action="peliculas", url=host + "/all-longest/1/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

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
    data = scrapertools.get_match(data,'<a href="#">Top Networks</a>(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="menu-menu-1-container">(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#   <li><a href="/group/69-top/1/"><i class="fa fa-tag"></i> 69</a></li>

    patron  = '<li><a href="([^"]+)"><i class="fa fa-tag"></i>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)Son &raquo;</a>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <div class="th">
#             			                <a href="/up.php?xxx=/video/deborah-kara-unger-anal-scenes-bottom-drop/" id="id=Mjh4MTN4MTg1NDA=">
# 	                    <img src="http://sexretrosex.com/content/18/540_Unger_Scenes.jpg" />
# 	                    <span class="th_nm">Deborah  Kara Unger Anal..</span>
# </a>
# 	                    <span class="th_vws"><i class="fa fa-eye"></i> 846 views</span>
#                             <span class="th_dr"><i class="fa fa-clock-o"></i> 15:00</span>
#                 </div>


    patron  = '<div class="th">.*?<a href="([^"]+)".*?<img src="([^"]+)".*?<span class="th_nm">([^"]+)</span>.*?<i class="fa fa-clock-o"></i>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + " [/COLOR]" + scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        scrapedurl = scrapedurl.replace("/up.php?xxx=", "")
        scrapedurl = host + scrapedurl

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))


# <li><span class="pg_nm">2</span></li>
#
#                     <li><a target="_self" href="../3/" target="_self"><span class="pg_nm">3</span></a></li>


# "Next page >>"
    else:
        patron  = '<li><span class="pg_nm">\d+</span></li>.*?href="([^"]+)"'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        next_page = item.url + next_page[0]
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page[0] , text_color="blue", url=next_page[0] ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    #        <iframe src="http://www.playercdn.com/ec/i2.php?aspectratio=16:9&url=aHR0cDovL3d3dy54dmlkZW9zLmNvbS92aWRlbzgwMzU1ODMvMjk1MDA2OA==" frameborder="0" allowfullscreen></iframe>

    scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')

#       <source src="http://shoretube.xyz/sda/xvideos/aHR0cDovL3d3dy54dmlkZW9zLmNvbS92aWRlbzgwMzU1ODMvMjk1MDA2OA==.mp4" type='video/mp4'>

    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<source src="(.*?)"')


    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

'''
def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
#    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
