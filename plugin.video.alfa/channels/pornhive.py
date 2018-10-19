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

host = 'http://www.pornhive.tv/en'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="MOVIES" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="CLIPS" , action="peliculas", url=host + "/free-stream-porn/"))
    itemlist.append( Item(channel=item.channel, title="CHANNELS" , action="catalogo", url=host))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?keyword=%s" % texto


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
    data = scrapertools.get_match(data,'Channels(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#<li><a href="http://www.pornhive.tv/en/channel/Evil-Angel" title="Evil Angel">Evil Angel (848)</a></li>

    patron  = '<li><a href="([^"]+)" title=.*?>(.*?)</a>'
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
    data = scrapertools.get_match(data,'Categories(.*?)<li class="divider"')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#       <li><a href="http://www.pornhive.tv/en/anal-porn-movies" title="Anal">Anal (11,656)</a></li>

    patron  = '<li><a href="([^"]+)" title="[^"]+">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)Son &raquo;</a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    #             <div class="col-lg-3 col-md-3 col-sm-4 col-xs-6 col-thumb panel-video-171447">
    # <div class="movie-panel">
    # <div class="panel-img">
    #     <a href="http://www.pornhive.tv/en/watch?v=TvaPJITd-t7">
    #         <img data-id="280b19edfa5adef832aa3ed6acf83338" data-src="http://www.pornhive.tv/files/covers/280b19edfa5adef832aa3ed6acf83338.jpg" src="http://www.pornhive.tv/assets/default/images/img-loader-lg.png" alt="Get Smartass -2008" class="img-responsive listImgs onLoad" />
    #     </a>
    # </div>
    # <div class="movie-panel-meta panel-info">
    #             <div class="movie-panel-duration pull-right">
    #                 <a href="javascript:void(0);" onclick="save_watch_list(171447);" class="qtips" title="Add to playlist" id="watch-171447">
    #             <span id="watch-span-171447"><i class="fa fa-clock-o"></i></span>
    #         </a>
    #                 </div>
    #     <div class="pull-left movie-panel-duration channel-171447" id="channel-171447" style="display:none;"></div>
    #     <div class="qtips pull-right movie-panel-watched" id="watched-171447" title="Watched">
    #         <i class="fa fa-eye"></i>
    #     </div>
    #     <div class="clearfix"></div>
    # </div>
    # <div class="movie-panel-title">
    #     <a href="http://www.pornhive.tv/en/watch?v=TvaPJITd-t7">
    #         Get Smartass -2008        </a>
    # </div>
    # </div>
    # </div>s


#    patron  = '<div class="content ">.*?<img class="content_image" src="([^"]+).mp4/\d+.mp4-\d.jpg" alt="([^"]+)".*?this.src="([^"]+)"'
    patron  = '<div class="col-lg-3 col-md-3 col-sm-4 col-xs-6 col-thumb panel-video-\d+">.*?<a href="([^"]+)".*?data-src="([^"]+)".*?alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)

        title = scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
#        scrapedurl = scrapedurl.replace("/thumbs/", "/videos/") + ".mp4"

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=title, infoLabels={'year':year} ))

#               <li><a href="http://www.pornhive.tv/en/big-tits-porn-movies/32" data-ci-pagination-page="32" rel="next">Next &rsaquo;</a></li>
#               <li><a href="http://www.pornhive.tv/en/page/32" data-ci-pagination-page="32" rel="next">Next &rsaquo;</a></li>
# "Next page >>"
    else:
        patron  = '<li><a href="([^"]+)" data-ci-pagination-page="\d+" rel="next">Next &rsaquo;'
        next_page = re.compile(patron,re.DOTALL).findall(data)
#        next_page = scrapertools.find_single_match(data,'class="last" title=.*?<a href="([^"]+)">')
        next_page =  next_page[0]
#        next_page = host + next_page
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page ) )

    return itemlist


'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<p> Streaming and Download Links:(.*?)</p>')

# <p> Streaming and Download Links:
#                                 <br /><a href="https://openload.co/f/4rkpwL1ofpg/cxc5454_1.mp4" target="_blank">Streaming Openload.co</a>
#                                 <br /><a href="https://www.rapidvideo.com/v/FGD0OAN62D" target="_blank">Streaming Rapidvideo.com</a>
#                                 <br /><a href="http://yep.pm/t1m6i72Mk" target="_blank">Download Depfile.com</a>
#                             </p>

    patron  = '<br /><a href="([^"]+)" target="_blank">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
    return itemlist
'''
def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
