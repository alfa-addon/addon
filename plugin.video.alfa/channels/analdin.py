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

host = 'https://www.analdin.com/es'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/más-reciente/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/más-visto/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/mejor-valorado/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))


#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url="https://www.analdin.com/categories/"))
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
    data = scrapertools.get_match(data,'<strong class="popup-title">Canales</strong>(.*?)<strong>Models</strong>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

  #<li><a class="item" href="https://www.analdin.com/es/сanales/18-years-old/" title="18 Years Old">18 Years Old</a></li>

    patron  = '<li><a class="item" href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="footer-category">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# 									<a class="item" href="https://www.analdin.com/es/categorías/solo/" title="Solo">
# 							<div class="img">
# 																	<img class="thumb" src="https://i.analdin.com/contents/categories/507.jpg" alt="Solo"/>
# 															</div>
# 							<strong class="title hp-video-title">Solo</strong>
# <!--							<div class="videos hp-videos-counter">1899 videos</div>
#  							<div class="wrap">
# 								<div class="videos">1899 videos</div>
#
# 																								<div class="rating positive">
# 									82%
# 								</div>
# 							</div> -->
# 						</a>


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?src="([^"]+)".*?<div class="videos">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')



    patron  = '<a class="popup-video-link" href="([^"]+)".*?thumb="([^"]+)".*?<div class="duration">(.*?)</div>.*?<strong class="title">\s*([^"]+)</strong>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,duracion,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))


#			"Next page >>"		<li class="next"><a href="/es/m%C3%A1s-reciente/2/" data-action="ajax" data-container-id="list_videos_latest_videos_list_pagination" data-block-id="list_videos_latest_videos_list" data-parameters="sort_by:post_date;from:2">Siguiente</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


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


#video_url: 'https://www.analdin.com/es/get_file/6/50766494fc07aa94cce793849d85afbc/152000/152711/152711.mp4/'

    patron  = 'video_url: \'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
#        scrapedurl = "http:" + scrapedurl.replace("\\", "")
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist




'''
def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
