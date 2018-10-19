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

host = 'http://www.tryboobs.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/week/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valorado" , action="peliculas", url=host + "/top-rated/week/"))
    itemlist.append( Item(channel=item.channel, title="Modelos" , action="modelos", url=host + "/models/model-viewed/1/"))


    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def modelos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <a href="http://www.tryboobs.com/models/2265/claudia-marie/" class="th-model">
#         <ins>
#             <img width="180" height="240" src="http://tb.fuckandcdn.com/tb/sunthumbs/pornstars/180x240/8299/1.jpg" alt="" />
#             <span class="roliks"><span>224</span></span>
#         </ins>
#         <span class="title">Claudia Marie</span>
#     </a>

    patron  = '<a href="([^"]+)" class="th-model">.*?src="([^"]+)".*?<span class="roliks"><span>(\d+)</span>.*?<span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + "   (" + cantidad + ")"
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#                                                        <li><a class="pag-next" href="http://www.tryboobs.com/models/model-viewed/2/"><ins>Next</ins></a></li>

    next_page_url = scrapertools.find_single_match(data,'<li><a class="pag-next" href="([^"]+)"><ins>Next</ins></a>')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="modelos" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="dropdown-menu">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

       # <a href="http://www.tryboobs.com/categories/499/69/" class="th-cat">
       #      <ins>
       #          <img src="http://tb.fuckandcdn.com/tb/tbstatic/v20/thumbs/categories/new/straight/69.jpg" alt="no pic" />
       #          <span class="roliks"><span>538</span></span>
       #      </ins>
       #      <span class="title">69</span>
       #  </a>

    patron  = '<a href="([^"]+)" class="th-cat">.*?<img src="([^"]+)".*?<span>(\d+)</span>.*?<span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="video-embed">(.*?)</div>')

    patron  = 'href="([^"]+)"\s*class="th-video.*?<img src="([^"]+)".*?<span class="time">([^"]+)</span>.*?<span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,duracion,scrapedtitle  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        url = scrapedurl
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a class="pag-next" href="http://www.tryboobs.com/latest-updates/2/"><ins>Next</ins></a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a class="pag-next" href="([^"]+)"><ins>Next</ins></a>')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#  <video src="http://tb.vstreamcdn.com/key=c7mwN8lFwuYbGbHm2iEy8A,end=1510224632/speed=224330/2371323.mp4" controls poster="http://tb.fuckandcdn.com/tb/thumbs/320x240/740/2371323/13.jpg" class="play-container"></video>


    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist

    #     itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    # return itemlist
