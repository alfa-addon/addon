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



host = 'http://woodrocket.com'

def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/porn"))
    itemlist.append( Item(channel=item.channel, title="Parodias" , action="peliculas", url=host + "/parodies"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Shows" , action="categorias", url=host + "/series"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
#    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="sbi-header">Películas por género</div>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <li>
#
# 			<div class="media-panel">
# 	<div class="media-panel-image">
# 		<a href="http://woodrocket.com/categories/amateur" class="video-image">
# 					<img src="/img/categories//Cx_-Cg7y9-9.jpg" />
# 				</a>
# 	</div>
#
# 	<div class="media-panel-title category-title">
# 		<a href="http://woodrocket.com/categories/amateur">Amateur</a>
# 	</div>
# </div> <!-- /category-panel -->
#
# 		</li>


    patron  = '<div class="media-panel-image">.*?<img src="(.*?)".*?<a href="(.*?)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail =  host + scrapedthumbnail
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <li>
# 			<div class="media-panel">
# 	<div class="media-panel-image">
# 		<a href="http://woodrocket.com/videos/body-painting-leads-to-body-fuckin" class="video-image" id="3BNO8E9fN" title="Body painting leads to body fuckin&#039;">
# 			<img src="http://videos.woodrocket.com/thumbs/3BNO8E9fN-1.jpg" />
# 		</a>
# 		<div class='media-icon'><i class="fa fa-film"></i></div>
# 	</div>
#
# 	<div class="media-panel-title">
# 		<a href="http://woodrocket.com/videos/body-painting-leads-to-body-fuckin" class="video-title" title="Body painting leads to body fuckin&#039;">Body painting leads to body fuckin&#039;</a>
# 	</div>
#
# 	<div class="media-panel-info">
# 		<div class="media-panel-votes">
# 							100%
# 						<span class="fa fa-thumbs-o-up"></span>
# 		</div>
# 		<div class='media-panel-views'>
# 				0 <span class="fa fa-eye"></span>
# 		</div>
# 		<div>
# 			Added May 23, 17
# 		</div>
# 	</div>
# </div>
# 		</li>



    patron  = '<div class="media-panel-image">.*?<a href="([^"]+)".*?title="([^"]+)".*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        plot = ""
        contentTitle = scrapedtitle
        thumbnail = host + scrapedthumbnail
        title = scrapedtitle

    #    vid = httptools.downloadpage(scrapedurl).data
    #    scrapedurl = scrapertools.find_single_match(vid, '<iframe src="(.*?)"')

        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#       <li><a href="http://woodrocket.com/porn?page=2" rel="next">&raquo;</a></li>
# "Next page >>"
    try:
        patron  = '<li><a href="([^"]+)" rel="next">&raquo;</a></li>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


    patron  = '<iframe src="(.*?)"'
    matches = scrapertools.find_multiple_matches(data, patron)




    for scrapedurl  in matches:
        scrapedurl = scrapedurl

# "quality_480p":"https:\/\/de.phncdn.com\/videos\/201803\/22\/159135422\/480P_600K_159135422.mp4?ttl=1521988248&ri=1228800&rs=752&hash=59bee12b3466d9f3dff3509727326d10","mediaDefinitions":[{"defaultQuality":false,"format":"",
# "quality":"480","videoUrl":"https:\/\/de.phncdn.com\/videos\/201803\/22\/159135422\/480P_600K_159135422.mp4?ttl=1521988248&ri=1228800&rs=752&hash=59bee12b3466d9f3dff3509727326d10"}],"video_unavailable_country":"false","toprated_url":"https:\/\/es.pornhub.com\/video?o=tr&t=m","mostviewed_url":"https:\/\/es.pornhub.com\/video?o=mv&t=m","browser_url":null,"morefromthisuser_url":"\/users\/woodrocket\/videos","options":"iframe","cdn":"highwinds","startLagThreshold":1000,"outBufferLagThreshold":2000,"appId":"1111","service":"","mp4_seek":"start","cdnProvider":"hw","thumbs":{"samplingFrequency":4,"type":"normal","cdnType":"regular","urlPattern":"https:\/\/bi.phncdn.com\/videos\/201803\/22\/159135422\/timeline\/120x90\/(m=eyzaiCObaaaa)(mh=IvOGu-PmEWJEMKUw)S{4}.jpg","thumbHeight":"90","thumbWidth":"120"},"nextVideo":[],"language":"es"},
# 			    utmSource = document.referrer.split('/')[2];

    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'"quality":"\d*","videoUrl":"(.*?)"')
    scrapedurl = scrapedurl.replace("\/", "/")
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))

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
'''
