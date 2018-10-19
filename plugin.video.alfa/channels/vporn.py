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

host = 'https://www.vporn.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/newest/month/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/views/month/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valoradas" , action="peliculas", url=host + "/rating/month/"))
    itemlist.append( Item(channel=item.channel, title="Favoritas" , action="peliculas", url=host + "/favorites/month/"))
    itemlist.append( Item(channel=item.channel, title="Mas Votada" , action="peliculas", url=host + "/votes/month/"))
    itemlist.append( Item(channel=item.channel, title="Mayor Duracion" , action="peliculas", url=host + "/longest/month/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?q=%s" % texto

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

# <a class="subhover" title="NEWS CLIPS" href="/category/clips/">All Clips</a> <BR>
#  - <a class=""  title="Clips 21Sextury"  href="/category/clips/?s=21Sextury">21Sextury</a> <BR>

    patron  = '<a class=""\s+title="([^"]+)"\s+href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedtitle,scrapedurl in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class="cats-all categories-list">(.*?)</div>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <<li> <a href="/cat/asian/"  title="Asian">
# <li><a href="/cat/1080p/"><img src="https://th-eu1.vporn.com/images/new/point.png" width="12" height="4">1080p</a></li>
# <li><a href="/cat/720p/"><img src="https://th-eu1.vporn.com/images/new/point.png" width="12" height="4">720p</a></li>


    patron  = '<li>.*?<a href="([^"]+)".*?>\s+([^"]+)</a>'
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
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    #         <div  class="video">
    #         <a  href="https://www.vporn.com/milf/pervcity-big-boob-anal-milfs-mercedes-carerra-alura-jenson/2288924/"  class="links">
    #         <div class="thumb videothumb">
    #                     <span class="thumb-time">
    #                         <span class="time">23:36</span>
    #                         <span class="hd-marker is-hd" title="HD Video"></span>
    #                     </span>
    #                     <img src="https://th-eu2.vporn.com/t/24/2288924/d17.jpg" alt="PervCity Big Boob Anal MILFs Mercedes Carerra Alura Jenson" width="270" height="158" class="imgvideo" id="2288924" />
    #
    # <div class="editvideo promoteedit" >
    #                 <img id="2288924"  thumb="17" class="context-menu" src="https://th-eu2.vporn.com/images/add-small.png" data-toggle="tooltip" data-placement="top" data-original-title="Add&nbsp;to" data-container="body" alt="Add to Playlist" height="18" width="26">
    #                 </div>
    #                 <img class="promoteedit editvideo2" src="https://th-eu2.vporn.com/images/new-video.png"  alt="new features" height="15" width="30">
    #
    #             </div>
    #             <div class="thumb-info">
    #                 <span class="cwrap" >Pervcity Big Boob Anal Milfs Mercedes Carerra Alura Jenson
    #                 </span>
    #                 <p>  by <span>PervCity</span> </p>
    #                 <span class="views" title="Views">
    #                     <img  class="views-img"  height="13" width="17" src="https://th-eu1.vporn.com/images/views.png" alt="Views">28,384
    #                 </span>
    #                 <span class="added" title="Added"><img src="https://th-eu1.vporn.com/images/added.png" alt="Added">3mo ago</span>
    #                 <span class="likes" title="Rating">
    #                             <img src="https://th-eu1.vporn.com/images/like.png" alt="Rating">
    #                             96%
    #                  </span>
    #                </div>
    #             </a>
    #         </div>

    patron  = ' <div  class="video">.*?<a\s+href="([^"]+)".*?<span class="time">(\d+:.*?)</span>.*?<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,time,scrapedthumbnail,scrapedtitle in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)

        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))

#        <a class="next linkage" title="Next Page" href="https://www.vporn.com/2/">Next <img src=https://th-eu2.vporn.com/images/next.png alt="Next Page"></a></div></div></div>    </div>

# "Next page >>"

    next_page_url = scrapertools.find_single_match(data,'<a class="next linkage" title="Next Page" href="([^"]+)">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    # else:
    #     patron  = '<a class="next" title="Next Page" href="([^"]+)">'
    #     next_page = re.compile(patron,re.DOTALL).findall(data)
    #     itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#        <source src="https://cdn-fr606.vporn.com/vid2/b638kyQqZrWtYM1fRe8RHQ/1516554512/s292-s281/38/2220538/2220538_720x406_500k.mp4" type="video/mp4" label="480p" default/>
#        <source src="https://cdn-fr639.vporn.com/vid2/VlSak3x_9FJGW3jn_6tWaA/1516554512/s288-s283/38/2220538/2220538_480x320_400k.mp4" type="video/mp4" label="320p" />						</video>


    patron  = '<source src="([^"]+)" type="video/mp4" label="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,scrapedtitle  in matches:

        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
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
'''
