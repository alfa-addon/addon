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

host = 'http://www.alsoporn.com/en'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host +"/g/All/new/1"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/g/All/top/1"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/date-last-week/"))
#    itemlist.append( Item(channel=item.channel, title="Dururacion" , action="peliculas", url=host + "/long-movies/"))
#    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/high-definition/date-last-week/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/=%s/" % texto

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
    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



    patron  = '<li><a href="([^"]+)" title="">.*?<span class="videos-count">([^"]+)</span><span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

         # <div class="alsoporn_prev alsoporn_prev-ct">
         #                <a href="/en/g/stepmom/top/1">
         #                    <img src="http://cdn.alsoporn.com/content/854/942_81.jpg" alt="stepmom" />
         #                    <span class="alsoporn_prev-tit">stepmom</span>
         #                </a>
         #            </div>

    patron  = '<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)" />'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = scrapedurl.replace("top", "new")
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

# <div class="alsoporn_prev">
#     <a href="/en/video/schoolgirl-uncomplaining-abused-and-screwed">
#         <img src="http://cdn.alsoporn.com/content/646/911_and_screwed.jpg" alt="Schoolgirl Uncomplaining is abused and screwed">
#         <span class="alsoporn_prev-tit">Schoolgirl Uncomplaining is abused and screwed</span>
#     </a>
#     <div class="alsoporn_prev-dur"><span>1:34:52</span></div>
# </div

    patron  = '<div class="alsoporn_prev">.*?<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)">.*?<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))


#			"Next page >>"		<li><a href="2" target="_self"><span class="alsoporn_page">NEXT</span></a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)" target="_self"><span class="alsoporn_page">NEXT</span></a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'([^\']+)\'')
    data = scrapertools.cachePage(scrapedurl)
    scrapedurl1 = scrapertools.find_single_match(data,'<iframe src="(.*?)"')
    scrapedurl1 = scrapedurl1.replace("http://www.playercdn.com/ec/i2.php?", "http://www.intelligenttube.xyz/ec/i2.php?")
    data = scrapertools.cachePage(scrapedurl1)
    scrapedurl2 = scrapertools.find_single_match(data,'<source src="(.*?)" type=\'video/mp4\'>')


    itemlist.append(item.clone(action="play", title=scrapedurl1, fulltitle = item.title, url=scrapedurl2))
    return itemlist
