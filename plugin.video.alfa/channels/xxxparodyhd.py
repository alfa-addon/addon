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



host = 'https://xxxparodyhd.net'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="New" , action="peliculas", url=host + "/genre/new-release/"))
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/genre/clips-scenes/"))
    itemlist.append( Item(channel=item.channel, title="Parodias" , action="peliculas", url=host + "/genre/parodies/"))

    itemlist.append( Item(channel=item.channel, title="Studio" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))


#    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
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


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Studio" :
        data = scrapertools.get_match(data,'>Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.get_match(data,'<div class=\'sub-container\' style=\'display: none;\'><ul class=\'sub-menu\'>(.*?)</ul>')

#    <li id="menu-item-212731" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-212731"><a href="https://xxxparodyhd.net/genre/all-girl/">All Girl</a></li>

    patron  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = str(scrapedtitle)
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist



def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<h1>Newest(.*?)</ul>')

# <div class="movies-list movies-list-full">
# <div data-movie-id="108500" class="ml-item">
# <a href="https://xxxparodyhd.net/big-booty-twerkout-2/" data-url="" class="ml-mask jt" data-hasqtip="112" oldtitle="Big Booty Twerkout 2" title="">
#
# <img data-original="https://xxxparodyhd.net/wp-content/uploads/2018/03/1522228671_1958166h-212x300.jpg " class="lazy thumb mli-thumb" alt="Big Booty Twerkout 2">
# <span class="mli-info"><h2>Big Booty Twerkout 2</h2></span>
# </a>
#
# <div id="hidden_tip">
# <div id="" class="qtip-title">Big Booty Twerkout 2</div>
#
#
# <div class="jtip-top">
# <div class="jt-info jt-imdb"> IMDb: N/A</div>
#
#
# <div class="jt-info"><a href="https://xxxparodyhd.net/release-year/2018/" rel="tag">2018</a></div>
#
#
# <div class="jt-info">N/A</div>
# <div class="clearfix"></div>
# </div>
#
#  <p class="f-desc"><p>3 Hours of Hardcore Footage! We gave Louise Thirteen&#8217;s all natural 32DDs, sweet pussy and delicious booty the ROYAL TREATMENT! Alix Lovell made her booty clap for us, so I&#8230;</p>
# </p>
#
#
#     <div class="block">Genre: <a href="https://xxxparodyhd.net/genre/big-butts/" rel="category tag">Big Butts</a>, <a href="https://xxxparodyhd.net/genre/gonzo/" rel="category tag">Gonzo</a>, <a href="https://xxxparodyhd.net/genre/new-release/" rel="category tag">New Release</a>, <a href="https://xxxparodyhd.net/genre/teen/" rel="category tag">Teen</a> </div>
#
# <div class="jtip-bottom">
# <a href="https://xxxparodyhd.net/big-booty-twerkout-2/" class="btn btn-block btn-successful"><i class="fa fa-play-circle mr10"></i>
# Watch Movie</a>
#
# </div>

    patron  = '<div data-movie-id="\d+" class="ml-item">.*?<a href="([^"]+)".*?oldtitle="([^"]+)".*?<img data-original="([^"]+)".*?rel="tag">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,year in matches:
        scrapedplot = ""
#        scrapedtitle = scrapedtitle.replace("Ver Pel\xedcula ","")

        scrapedtitle = str(scrapedtitle) + " " + year
#        scrapedthumbnail = "http://www.xxxparodyhd.com" + scrapedthumbnail

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#<li class='active'><a class=''>2</a></li><li><a rel='nofollow' class='page larger' href='https://xxxparodyhd.net/genre/parodies/page/3/'>3</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li class=\'active\'>.*?href=\'([^\']+)\'>')
#    next_page_url = str(item.url) + next_page_url
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
# <div id="clicktracker">
#                 <div id="video" class="text-center" style="overflow:hidden;">
#                     <a href="http://datoporn.co/embed-enq5ttb8d8ol.html" onclick="uClick(5368);" class="preview" target="_blank">
#                         <div class="video-preview" style="display:none;">
#                             <img src="http://www.xxxparodyhd.com//files/covers/11566e4cb2c73cfbad881acd75f89f26.jpg" class="img-responsive" style="width:100%;" />
#                             <div class="video-play"><i class="fa fa-play-circle-o" aria-hidden="true"></i></div>
#                         </div>
#                     </a>
#                 </div>


    patron  = '<div id="video" class="text-center" style="overflow:hidden;">.*?<a href="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl in matches:
        url = scrapedurl
        itemlist.append(item.clone(action="play", title=url, url=url))
    return itemlist



def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''
