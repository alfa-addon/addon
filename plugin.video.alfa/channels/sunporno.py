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

host = 'https://www.sunporno.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host +"/most-recent/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-viewed/date-last-week/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/date-last-week/"))
    itemlist.append( Item(channel=item.channel, title="Mas largas" , action="peliculas", url=host + "/long-movies/date-last-month/"))
#    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/high-definition/date-last-week/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto

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
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

 # <a href="https://www.sunporno.com/channels/345/3d/">
 #                    3d                    <span class="icon">
 #                        <img src="https://sunstatic.fuckandcdn.com/sun/sunstatic/v31/common/sunporno/img/icons/question.png" alt="?" title="" height="19" />
 #                        <span>Pornographic videos all designed in 3D tech for animation loving viewers.</span><b></b>
 #                    </span>
 #                </a>

    patron  = '<a href="([^"]+)">\s*(.*?)\s*<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = scrapedurl + "/most-recent/"
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.get_match(data,'<div id="mainThumbsContainer" class="thumbs-container">(.*?)<div class="clearfix">')


# <div class="thumb-container notranslate with-title moviec movie-1339534 "
# 		data-id="1339534"
# 		data-type="movie"
# 		data-status-id="3"
# 		data-status-name="approved"
# 	>
#         <div>
#             <p class="btime">21:53</p>
#             <a
#                 href="https://www.sunporno.com/videos/1339534/big-tits-mom-wakes-up-to-the-boy-s-throbbing-boner"
#                 class="com-link changeThumb"
#                 data-preview="18/2_2385991.mp4"
#             ></a>
#
# 			<img width="320px" height="240px" src="https://sunstatic2.fuckandcdn.com/sun/thumbs/320x240/745/2385991/27.jpg" class="thumb" alt="no image"
# 			/>
#
# 	<p class="movie-title">
#         <a href="https://www.sunporno.com/videos/1339534/big-tits-mom-wakes-up-to-the-boy-s-throbbing-boner" title="Big tits mom wakes up to the boy&#039;s throbbing boner"></a>
#         <span>Big tits mom wakes up to the boy's throbbing boner</span>
#     </p>
#         <div class="thumb-activity">
#             <p class="bviews">610184</p>
#             <p class="brating r-green ">77%</p>
#         </div>
# 		</div>
# 	</div>

    patron  = '<p class="btime">([^"]+)</p>.*?href="([^"]+)".*?src="([^"]+)".*?title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for duracion,scrapedurl,scrapedthumbnail,scrapedtitle in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        url = scrapedurl
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a class="pag-next" href="https://www.sunporno.com/most-recent/date-last-month/page2.html">Next &gt;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a class="pag-next" href="(.*?)">Next &gt;</a>')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
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

#<video src="https://vstreamcdn.com/key=TEtekIk2dpBTHcGLuXItLA,end=1527184469/speed=168868/530854.mp4" controls poster="https://sunstatic2.fuckandcdn.com/sun/thumbs/original/221/530854/3.jpg" class="play-container"></video>



    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https:", "http:")
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist


    #     itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    # return itemlist



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
