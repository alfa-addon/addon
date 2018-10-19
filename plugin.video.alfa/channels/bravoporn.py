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

host = 'http://www.bravoporn.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host +"/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/date-last-week/"))
#    itemlist.append( Item(channel=item.channel, title="Dururacion" , action="peliculas", url=host + "/long-movies/"))
#    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/high-definition/date-last-week/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/c/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/s/?q=%s" % texto

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

# <a href="/c/teens/" class="th">
#                   <img src="//p8i9c5u6.ssl.hwcdn.net/categories/2.jpg" width="240" height="180" alt="Teens"/>
#                 <div class="in-mod">
#           <strong class="category-name">
#             <span>Teens</span>
#             22952 movies
#             <br>
#           </strong>
#         </div>
#       </a>

    patron  = '<a href="([^"]+)" class="th">.*?<img src="([^"]+)".*?<span>([^"]+)</span>\s*(\d+) movies.*?</strong>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/latest/"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

	                #     <div class="video_block_205 video_block">
                    #     <a href="http://www.bravotube.net/videos/dick-craving-blonde-anna-rey-drops-on-her-knees-for-a-dick/" data-rt="pqr=1:6a6f84d94c8eadd3823587c64e8e1bc5:0:511326:1:">
                    #         <div class="click_spacer">&nbsp;</div><img src="http://bt3.cdnbm.com/511000/511326/240x180/13.jpg" width="240" height="180" alt="Dick craving blonde Anna Rey drops on her knees for a dick" onmouseover="KT_rotationStart(this, 'http://bt2.cdnbm.com/511000/511326/240x180/', 14)" onmouseout="KT_rotationStop(this)" />
                    #         <div class="hd"></div>
                    #         <div class="on"><span>Added: 10 minutes ago</span><span class="time">6:59</span>
                    #         </div><strong>Dick craving blonde Anna...</strong>
                    #     </a><em>80%</em>
                    # </div>
                    # <a href="/videos/242661/" title="Sexy brunette Anissa Kate gets sandwiched by J.P.X. and Tony Carrera">
                    # <img src="//n3y8w5r5.ssl.hwcdn.net/242000/242661/240x180/1.jpg" width="240" height="180" alt="Sexy brunette Anissa Kate gets sandwiched by J.P.X. and Tony Carrera" onmouseover="KT_rotationStart(this, '//r3w6x5i3.ssl.hwcdn.net/242000/242661/240x180/', 9)" onmouseout="KT_rotationStop(this)"></a><div class="on">
                    # <span class="time">6:56</span></div>

    patron  = '<div class=".*?video_block"><a href="([^"]+)".*?<img src="([^"]+)".*?alt="([^"]+)".*?<span class="time">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = "https:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))


#			"Next page >>"		<a href="/latest-updates/2/" class="next" title="Next">Next</a>


    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next" title="Next">Next</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
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

          # <div class="player" id="player" style='width: 100%; height: auto; position: relative;'>
          #   <video id="bravoplayer" >
          #                   <source src="https://www.bravoporn.com/get_file/1/8101e45a9c41beddbefebc4b030c429b/113000/113675/113675_360p.mp4/?br=491" type='video/mp4' title="LQ" />
          #                   <source src="https://www.bravoporn.com/get_file/1/07987c82fd4887caf6c2c45879e8449b/113000/113675/113675_hq.mp4/?br=668" type='video/mp4' title="HQ" />
          #   </video>      <source src="https://www.bravoporn.com/get_file/1/2b23f27a30048fd04349a3f1b8f739ab/575000/575296/575296_hq.mp4/?br=1681" type='video/mp4' title="HQ" />
          # </div>  server="directo",

    patron  = '<source src="([^"]+)" type=\'video/mp4\' title="HQ" />'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, url=scrapedurl, folder=True))

    return itemlist
    #     itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    # return itemlist
