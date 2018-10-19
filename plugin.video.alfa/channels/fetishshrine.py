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

host = 'https://www.fetishshrine.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Mejor Valorado" , action="peliculas", url=host + "/top-rated/"))

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
#    data = scrapertools.get_match(data,'<ul class="dropdown-menu">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


			# 		<a href="https://www.fetishshrine.com/categories/hardcore/" title="Hardcore porn tube" class="thumb">
			# 	<span class="img">
			# 								<img src="https://www.fetishshrine.com/contents/categories/18.jpg" alt="Hardcore"/>
			# 						</span>
			# 	<strong class="title"><span class="total">56289 movies</span>Hardcore</strong>
			# </a><!--thumb-->

    patron  = '<a href="([^"]+)" title="([^"]+) porn tube" class="thumb">.*?<img src="([^"]+)".*?<span class="total">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="video-embed">(.*?)</div>')

	# <div class="thumb" itemscope itemtype="https://schema.org/ImageObject">
	# 			<span class="block-fav">
	# 				<button title="Add To Favorites" data-id="2294032">Favorites</button>
	# 				<span class="success">Video Added</span>
	# 				<span class="fail">You have to <a href="https://www.fetishshrine.com/login.php">Log In</a></span>
	# 			</span>
	# 			<a itemprop="url" href="https://www.fetishshrine.com/videos/2294032/horny-teen-fucks-old-guys-if-you-dont-fuck-him-mommy-will/">
	# 									<span class="img" data-id="2294032" data-poster="https://cdni.fetishshrine.com/contents/videos_screenshots/2294000/2294032/230x138/1.jpg" data-src="https://www.fetishshrine.com/get_file/3/990d824b512fdd0c4f3a4dcf0e96cddd/2294000/2294032/2294032_preview.mp4/">
	# 					<img src="https://cdni.fetishshrine.com/contents/videos_screenshots/2294000/2294032/230x138/1.jpg" width="185" height="103" alt="Horny teen fucks old guys If You Dont Fuck Him Mommy Will">
	# 					<span class="duration">8:00</span>
	# 																														<span class="hd"></span>
	# 																																				</span>
	# 				<strong class="title" itemprop="name">Horny teen fucks old guys If You Dont Fuck Him Mommy Will</strong>
	# 				<meta itemprop="datePublished" content="2018-05-05">
    #
	# 														    										<span class="info"><span>0</span><span class="rate">Porn Rating <em>50%</em></span></span>
	# 			</a>
	# 		</div><!--thumb-->


    patron  = '<a itemprop="url" href="([^"]+)">.*?<img src="([^"]+)".*?alt="([^"]+)">.*?<span class="duration">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        url = scrapedurl
#        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#            <li class="next">
#			"Next page >>"		<li class="next"><a data='2' href="/latest-updates/2/" title="Next">&#62;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a.*?href="([^"]+)" title="Next">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>", text_color="blue", url=next_page_url , folder=True) )


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



#         video_url: 'https://www.fetishshrine.com/get_file/3/1f45fddcf85903ecaa91f82f84a9e7c2/2296000/2296300/2296300.mp4/'

    patron  = 'video_url: \'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:

        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

#        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
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
