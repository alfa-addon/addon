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

host = 'https://frprn.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/ás-visto/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-raped/"))
#    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))


#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
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
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

  #<li id="menu-item-38568" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-38568"><a href="http://pornstreams.eu/tag/assparade/">AssParade</a></li>

    patron  = '<li id="menu-item-.*?<a href="([^"]+)">([^"]+)</a>'
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

	# <li class="thumb thumb-category">
	# 		<a href="https://frprn.com/categories/amateur/">
	# 			<div class="image-holder">
	# 										<img class="lazy" data-original="https://frprn.com/contents/videos_screenshots/5000/5255/240x180/1.jpg">
	# 								</div>
	# 			<div class="title">
	# 				<div class="name">Amateur</div>
	# 				<div class="count">584</div>
	# 			</div>
	# 		</a>
	# 	</li>

    patron  = '<li class="thumb thumb-category">.*?<a href="([^"]+)">.*?<img class="lazy" data-original="([^"]+)">.*?<div class="name">([^"]+)</div>.*?<div class="count">(\d+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + "  (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

				# 	<div class="thumb">
				# 	<a href="https://frprn.es/videos/28043/" class="js-video" data-video-url="https://frprn.es/videos/28043/" data-thumb-id="28043">
				# 		<div class="image-holder">
				# 			<img class="lazy" data-original="https://frprn.com/contents/videos_screenshots/28000/28043/240x180/5.jpg" alt="Glorious babe Katerina Hartlova with admirable boobies softly nailed" onmouseover="KT_rotationStart(this, 'https://frprn.com/contents/videos_screenshots/28000/28043/240x180/', 5)" onmouseout="KT_rotationStop(this)"/>
				# 																								<span class="duration">28:19</span>
				# 		</div>
				# 		<div class="title">
				# 			<div class="text">Glorious babe Katerina Hartlova with admirable boobies softly nailed</div>
				# 		</div>
				# 	</a>
				# </div>

    patron  = '<div class="thumb">.*?<a href="([^"]+)".*?<img class="lazy" data-original="([^"]+)" alt="([^"]+)".*?<span class="duration">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li class="pagination-next"><a href="/2/"><i class="icon-arrow-right"></i></a></li>

    next_page_url = scrapertools.find_single_match(data,'<li class="pagination-next"><a href="([^"]+)">')

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

# <meta property="og:video" content="https://frprn.com/get_file/1/aa8eb1196e7d60f0af91fb701b353e93/28000/28029/28029.mp4/" />
#     							{
# 									file: "https://frprn.com/get_file/1/d127fcc1bb1b0aa0fbfa2d842165b002/28000/28029/28029_low.mp4",
# 									label: "low"
# 								},
# 								{
# 									file: "https://frprn.com/get_file/1/aa8eb1196e7d60f0af91fb701b353e93/28000/28029/28029.mp4",
# 									label: "high"
# 								},

#video_url: 'https://www.analdin.com/es/get_file/6/50766494fc07aa94cce793849d85afbc/152000/152711/152711.mp4/'

    patron  = '<meta property="og:video" content="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
#        scrapedurl = "http:" + scrapedurl.replace("\\", "")
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = scrapedurl, url=scrapedurl))

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
