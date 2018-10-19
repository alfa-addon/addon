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

host = 'http://sexofilm.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/xtreme-adult-wing/adult-dvds/"))
    itemlist.append( Item(channel=item.channel, title="Parody" , action="peliculas", url=host + "/xtreme-adult-wing/porn-parodies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/xtreme-adult-wing/porn-clips-movie-scene/"))
    itemlist.append( Item(channel=item.channel, title="SexMUSIC" , action="peliculas", url=host + "/topics/sexo-music-videos/"))
    itemlist.append( Item(channel=item.channel, title="Xshows" , action="peliculas", url=host + "/xshows/"))


    itemlist.append( Item(channel=item.channel, title="Big boobs" , action="peliculas", url=host + "/xxx-section/big-boobs/"))


#    itemlist.append( Item(channel=item.channel, title="Portugues" , action="peliculas", url="http://www.tupelicula.tv/filter?language=5"))
#    itemlist.append( Item(channel=item.channel, title="VOS" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-sub-espanol/"))
#    itemlist.append( Item(channel=item.channel, title="Año" , action="anual", url="http://sexofilm.com/"))
#    itemlist.append( Item(channel=item.channel, title="Parody" , action="categorias", url="http://sexofilm.com/topics/parody-films/"))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url =host + "/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))s
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

# <li class="cat-item cat-item-1275"><a href="http://sexkino.to/genre/amateur/" >Amateur</a> <i>36</i>

    patron  = '<li class="cat-item cat-item-.*?<a href="(.*?)" >(.*?)</a> <i>(.*?)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,cantidad  in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " ("+cantidad+")"
#        scrapedtitle = scrapedtitle.replace("Pelculas de ", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
#        scrapedthumbnail ="http://www.porntrex.com" + scrapedthumbnail
#        scrapedurl ="http://www.porntrex.com" + scrapedurl

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def anual(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

#           <li><a href="http://sexkino.to/release/2017/">2017</a></li>
    patron  = '<li><a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist



def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



    patron  = '<div class="post-thumbnail.*?<a href="([^"]+)" title="(.*?)".*?src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)


    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace(" Porn DVD", "")
#        scrapedtitle = scrapedtitle + str(duration)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        scrapedthumbnail = "http://www.xxxparodyhd.com" + scrapedthumbnail

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#                                    <a class="nextpostslink" rel="next" href="http://sexofilm.com/page/2/">&raquo;</a>

#  "Next Page >>"
    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">&raquo;</a>')
#    next_page_url = "http://sexody.com" + next_page_url
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

'''

def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data



# <div class="entry themeform share">
# <div class="entry-inner">
# <p style="text-align: center;">
# <iframe src="https://openload.co/embed/XgMV_AELsx0/Trick_Or_Dick_%282016%29_-_Full_Free_HD_SexoFilm.mp4" width="100%" height="360" frameborder="0" scrolling="no" allowfullscreen="allowfullscreen"></iframe></p>


#https://openload.co/f/7Vm8bB7jo94/Interracial_Pickups_%2313_%282016%29_-_Full_Free_HD_SexoFilm.mp4

#    <strong>Calidad:</strong> HD Rip</p>
#    calidad = scrapertools.find_single_match(data,'<strong>Calidad:</strong>(.*?)</p>')

#      url = str(url)
    if (DEBUG):
        url = scrapertools.find_single_match(data,'<div class="entry themeform share">.*?<p style="text-align: center;"><iframe src="([^"]+)" width="100%"')
        url = url.replace("embed","f").replace("%23","#").replace("%28","(").replace("%29",")")
#        url = str(url)
    #    title = scrapertools.find_single_match(match,'<td><img src=.*?> (.*?)</td>')

     #
    #  patron  = '<li><a href="#ms(.*?)</li>'
    #  matche2 = re.compile(patron,re.DOTALL).findall(data)
    #  for match in matche2:
    #      idioma = scrapertools.find_single_match(match,'">VER(.*?)</a>')

#        url = "http://www.tripledeseo.com/"+url
#        idioma = scrapertools.find_single_match(match,'<div class="calidad-txt">(.*?)</div>')

#       calidad = calidad.replace("Ahora en ", "")

    #    title = str(calidad)


        itemlist.append(item.clone(action="play", title=url, url=url))

# <div class="vid-play vid-loading" vid="2243" id="vid-play">
#         <iframe src="http://www.wankz.com/embed/1381768" scrolling="no" frameborder="0" width="100%" height="100%" data-id="1435" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true" id="iframe-play"></iframe>
# </div>

    # patron  = '<div class="vid-play(.*?)</div>'
    # matches = re.compile(patron,re.DOTALL).findall(data)
    # for match in matches:
    #     url = scrapertools.find_single_match(match,'<iframe src="([^"]+)" scrolling=')
    #     itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist
'''


def play(item):
    logger.info()
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
