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

## italiafilm

'''
([^<]+) para extraer el texto entre dos tags “uno o más caracteres que no sean <" ^ cualquier caracter que no sea <
"([^"]+)" para extraer el valor de un atributo
\d+ para saltar números
\s+ para saltar espacios en blanco
(.*?) cuando la cosa se pone complicada

    ([^<]+)
  \'([^\']+)\'



    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist

'''

host = 'http://czechvideo.org'


def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.vintagetube.club/tube/last-1/" http://www.vintagetube.club/tube/popular-1/

    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Big Tits" , action="peliculas", url=host + "/tags/big+tits/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/tags/%s/" % texto

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

#
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<ul class="cat_menu" id="cat_menu_c0">(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <li><a href="/index.php?do=cat&category=amateurallure" rel="index section" title="Amateur Allure - amateur porno video">AmateurAllure</a></li>

    patron  = '<li><a href="(.*?)".*?>(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

#    itemlist.append( Item(channel=item.channel, action="peliculas", title="Big Tits" , url=host + "/tags/big+tits/" , thumbnail="" , plot="" , folder=True) )
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="ntitle1">Newest video:</div></td>(.*?)</table>')


# <div class="short-story">
# <a href="https://czechvideo.org/8103-czech-streets-88.html" title="Czech Streets 88" >
#
# <img src="/templates/Default/images/spacer.png" style="background:url(/uploads/posts/2016-07/1468257523_czechstreets.com-88.jpg) no-repeat; background-size: 100% 100%;-webkit-background-size: 100% 100%; -o-background-size:100% 100%; -moz-background-size: 100% 100%;filter: progid:DXImageTransform.Microsoft.AlphaImageLoader(src='/uploads/posts/2016-07/1468257523_czechstreets.com-88.jpg', sizingMethod='scale');
# -ms-filter: "progid:DXImageTransform.Microsoft.AlphaImageLoader(src='/uploads/posts/2016-07/1468257523_czechstreets.com-88.jpg', sizingMethod='scale')";" />
#
# <h2 class="short-title">Czech Streets 88</h2>
# </a>
# <div class="short-time">24:28</div>
#
# <div class="clear"></div>
#
# </div>

    patron = '<div class="short-story">.*?<a href="([^"]+)" title="([^"]+)" >.*?\(src=\'(.*?)\'.*?div class="short-time">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        scrapedthumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        scrapedplot = ""

        itemlist.append( Item(channel=item.channel, action="play", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# "Next page >>"                         <del><a href="http://czechvideo.org/page/2/">Next</a></del></div></div></td>
    next_page_url = scrapertools.find_single_match(data,'<del><a href="([^"]+)">Next</a></del>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

#<br><iframe src="https://openload.co/embed/ZW1UR2LmCRU/FakeCop_-_Cecilia_Scott_-_Cops_Cock_Gives_Her_Multiple_Orgasms.mp4" width="720"

#    data = scrapertools.get_match(data,'<strong>Download</strong>(.*?)<div class="clear"></div>')
    patron = '<iframe src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
#    scrapedurl = scrapertools.find_single_match(data,'<iframe width=.*?src=\'(.*?)\'')
#    scrapedurl = str(scrapedurl)
    for scrapedurl in matches:
        scrapedplot = ""
#    data = httptools.downloadpage(scrapedurl).data

 # <source src="http://optimaltube.xyz/sda/xvideos/aHR0cDovL3d3dy54dmlkZW9zLmNvbS92aWRlbzkyOTMyMDcvZnVubnlfcG9ybl8tX3d3dy5rb3pvZGlya3kuY3o=.mp4" type='video/mp4'>
 #              </video>

#    scrapedurl = scrapertools.find_single_match(data,'<source src="(.*?)"')


    itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
    return itemlist
'''


def play(item):
    logger.info()
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
