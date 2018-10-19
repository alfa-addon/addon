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

host = 'http://hellporno.com/'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/?page=1"))
#    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/"))


#    itemlist.append( Item(channel=item.channel, title="Chanel" , action="catalogo", url=host + "/channels/"))
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


def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<img class="thumb" src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        thumbnail = "http:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=thumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="categories-holder-videos">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#<div class="categories-holder-videos"><a href="http://hellporno.com/mom/"><span class="image"><img src="http://hellporno.com/contents/categories/100336/100336_straight_video.jpg" alt="Mom - Porn videos"></span><span class="title">Mom</span><span class="cat-info"><span>4955 videos</span><span>


    patron  = '<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+) - Porn videos">.*?<span>(\d+) videos</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
    #    scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
    #    scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

 # <div class="video-thumb">
 #                           <a href="https://hellporno.com/videos/blondie-sure-loves-the-mature-cock-in-her-fresh-cunt/" class="title">Blondie sure loves the mature cock in her fresh cunt</a>
 #                           <span class="image">
 #                              <span class="time">5:52</span><span class="loader"></span>
 #                              <video poster="https://e4j7g2z7.ssl.hwcdn.net/201000/201003/240x160/8.jpg" type='video/mp4; codecs="avc1.42E01E, mp4a.40.2"' loop id="201003" preload="none" src="https://hellporno.com/get_file/6/1a6913106048b2743049f96a3c7092ed/201000/201003/201003_trailer.mp4"></video>
 #                              <img alt="Blondie sure loves the mature cock in her fresh cunt" src="https://y8h5g7v6.ssl.hwcdn.net/201000/201003/240x160/8.jpg">
 #                           </span>
 #                           <span class="video-rating"><span style="height:92%"></span></span><span class="info"><span>1213 views</span> Added 6 hours ago</span>
 #                        </div>
 #                        <div class="video-thumb">
 #                           <a href="https://hellporno.com/videos/busty-brunette-plays-with-the-pussy-under-the-warm-shower/" class="title" data-rt="pqr=5:07e988fe5cf562d7d408994bf0c211e8:3:201094:1" onClick="_gaq.push(['_trackEvent', 'Rotator', 'Click']);">Busty brunette plays with the pussy under the warm shower</a>
 #                           <span class="image">
 #                              <span class="time">4:57</span><span class="loader"></span>
 #                              <video poster="https://k7q4b8x2.ssl.hwcdn.net/201000/201094/240x160/3.jpg" type='video/mp4; codecs="avc1.42E01E, mp4a.40.2"' loop id="201094" preload="none" src="https://hellporno.com/get_file/6/382195ae41758337ba21eb293e99dcc3/201000/201094/201094_trailer.mp4"></video>
 #                              <img alt="Busty brunette plays with the pussy under the warm shower" src="https://h3x8f3x5.ssl.hwcdn.net/201000/201094/240x160/3.jpg">
 #                           </span>
 #                           <span class="video-rating"><span style="height:92%"></span></span><span class="info"><span>747 views</span> Added 6 hours ago</span>
 #                        </div>


    patron  = '<div class="video-thumb"><a href="([^"]+)" class="title".*?>([^"]+)</a>.*?<span class="time">([^<]+)</span>.*?<video poster="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,duracion,scrapedthumbnail  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        url = scrapedurl
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<a href="/2/" class="next">Next page &raquo;</a>


    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


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

#  \'([^\']+)/\'

			# 	file: "http://hellporno.com/get_file/6/a5f6762552071e83c2f28c6a649b1c0e/200000/200229/200229_360p.mp4/?br=314",
			# 	label: "360p",
			# 	type: "video/mp4"
			# },
			# 				{
			# 	file: "http://hellporno.com/get_file/6/653ae77ce3d6503cf7c0abab7f0188db/200000/200229/200229.mp4/?br=1099",
			# 	label: "720p HD",
			# 	type: "video/mp4"

    patron  = 'file: "([^"]+)",.*?label: "([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,scrapedtitle  in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))

    return itemlist
