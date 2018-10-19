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

host = 'http://tubepornclassic.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto

    try:
        return sub_search(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# http://www.tubepornclassic.com/search/BOOBS/3/

def sub_search(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


    patron  = '<div class="item  ">.+?<a href="([^"]+)" title="([^"]+)".*?original="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="next">.*?<a href="([^"]+)"')

#    next_page_url = "http://www.elreyx.com/"+str(next_page_url)

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist



def categorias(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


            # <li class="list-item">
            #                                                                          <span class="list-item__action list-item__action--add">
            #                 <label for="checkbox_categories-anal" title="Combine Category">
            #                     <a data-action="ajax" data-container="list_videos2_videos_list" data-parameters="sort_by:title" data-type="a-in-label" href="http://de.tubepornclassic.com/categories/public/?category_dirs=categories-anal">+</a>
            #                 </label>
            #             </span>
            #             <input type="checkbox" name="category_dirs[]" id="checkbox_categories-anal" value="categories-anal">
            #             <span class="list-item__info">4514</span>
            #             <span class="list-item__info list-item__info--sub">11</span>
            #
            #             <a class="list-item__link" href="http://de.tubepornclassic.com/categories/categories-anal/" title="Anal">Anal</a>
            #                                     </li>												</div>

    patron  = '<li class="list-item">.*?href="([^"]+)".*?<span class="list-item__info">([^"]+)</span>.*?title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        scrapedtitle = scrapedtitle + " (" + scrapedthumbnail + ")"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

            			# 										<div class="item  ">
						# <a href="https://es.tubepornclassic.com/videos/150009/count-dracula-s-snappish-juicecunts/" >
						# 	<div class="img">
						# 											<img data-sgid="1" data-video-id="150009" class="thumb EoCk7" src="https://static1.tubepornclassic.com/contents/videos_screenshots/150000/150009/240x180/11.jpg" src="//tubepornclassic.com/images/load-foto.png"  alt="Count Dracula'S Snappish Juicecunts"  width="240" height="180"/>
						# 																																					<span class="ico-fav-0 " title="Agregar a favoritos" data-href="/login-required/" data-fancybox="ajax" "></span>
						# 													<span class="ico-fav-1 " title="Ver más tarde" data-href="/login-required/" data-fancybox="ajax" "></span>
						# 																		</div>
						# 	<strong class="title">
						# 											Count Dracula'S Snappish Juicecunts
						# 									</strong>
						# 	<div class="wrap">
						# 		<div class="duration">84m:43s</div>
                        #
                        #                                                                         <div class="rating positive">
                        #             83%
                        #         </div>
						# 	</div>
						# 	<div class="wrap">
						# 																		<div class="added"><em>4 weeks ago</em></div>
                        #         <div class="views ico ico-eye">20 540</div>
						# 	</div>
						# </a>
						# 					</div>


    patron  = '<div class="item  ">.*?<a href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)".*?<div class="duration">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        itemlist.append( Item(channel=item.channel, action="play", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , contentTitle = contentTitle , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="next">.*?<a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


#var video_url="https://tubepornclassic.com/get_file/1/0fce78fafe049049ef1e946aa7ba4a50/150000/150025/150025.mp4/?time=20180309122530&s=1766f80cd4ab26c7971940733c70302b&br=415&d=4401";

    patron  = 'var video_url="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for url in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist

    #    itemlist.append(item.clone(action="play", title=item.title, url=url))
    # return itemlist
