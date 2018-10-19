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
from core import jsontools

## italiafilm

'''
([^<]+) para extraer el texto entre dos tags “uno o más caracteres que no sean <" ^ cualquier caracter que no sea <
"([^"]+)" para extraer el valor de un atributo
\d+ para saltar números
\s+ para saltar espacios en blanco
(.*?) cuando la cosa se pone complicada

    ([^<]+)
  \'([^\']+)\'



    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist

'''


host = 'http://xxx.justporno.tv'


def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.vintagetube.club/tube/last-1/" http://www.vintagetube.club/tube/popular-1/



    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/latest-updates/1/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Votado" , action="catalogo", url=host + "/videos/most-liked/"))

    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas", action="peliculas", url=host + "/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias", action="categorias", url=host + "/categories/"))
#    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://justporn.to/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    # <div class="row">
	# 		<a href="http://gnula.mobi/16160/pelicula/sicario-2015/" title="Sicario (2015)">
	# 			<img src="http://image.tmdb.org/t/p/w300/voDX6lrA37mtk1pVVluVn9KI0us.jpg" title="Sicario (2015)" alt="Sicario (2015)" />
	# 		</a>
	# </div>

    patron = '<div class="row">.*?<a href="([^"]+)" title="([^"]+)">.*?<img src="(.*?)" title'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url,name,img   in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", show=name, thumbnail=img))

# <a href="http://gnula.mobi/page/2/?s=la" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a></div>

    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion))

    return itemlist

def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'>Scenes</a>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#           <li class="cat-item cat-item-114"><a href="http://justporn.to/category/genre/all-sex/" >All Sex</a>

    patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
#        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'>Genre</a>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#           <a class="item" href="http://xxx.justporno.tv/categories/fung/" title="fung">
						# 	<div class="img">
						# 											<span class="no-thumb">no image</span>
						# 									</div>
						# 	<strong class="title">fung</strong>
						# 	<div class="wrap">
						# 		<div class="videos">1 video</div>
                        #
						# 																		<div class="rating positive">
						# 			78%
						# 		</div>
						# 	</div>
						# </a>


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<div class="videos">(\d+) video.*?</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,numero in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + numero + ")"
#        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="ntitle1">Newest video:</div></td>(.*?)</table>')

		# <div class="item  ">
		# 				<a href="http://xxx.justporno.tv/videos/6679/classroom-pov-anal-with-hot-teacher/" title="Classroom POV anal with hot teacher" >
		# 					<div class="img">
		# 															<img class="thumb lazy-load" data-original="http://xxx.justporno.tv/contents/videos_screenshots/6000/6679/224x168/1.jpg" alt="Classroom POV anal with hot teacher" data-cnt="5" width="224" height="168"/>
		# 																																									<span class="ico-fav-0 " title="Add to Favourites" data-fav-video-id="6679" data-fav-type="0"></span>
		# 																	<span class="ico-fav-1 " title="Watch Later" data-fav-video-id="6679" data-fav-type="1"></span>
		# 																						</div>
		# 					<strong class="title">
		# 															Classroom POV anal with hot teacher
		# 													</strong>
		# 					<div class="wrap">
		# 						<div class="duration">7m:05s</div>
        #
		# 																						<div class="rating positive">
		# 							0%
		# 						</div>
		# 					</div>
		# 					<div class="wrap">
		# 																						<div class="added"><em>4 hours ago</em></div>
		# 						<div class="views">43</div>
		# 					</div>
		# 				</a>
		# 									</div>

    patron = '<a href="http://xxx.justporno.tv/videos/(\d+)/.*?" title="([^"]+)" >.*?data-original="([^"]+)".*?<div class="duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle.replace("Ver Pel\ícula", "")
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
#        scrapedtitle = str(scrapedtitle)
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
        scrapedurl = "http://xxx.justporno.tv/embed/" + scrapedurl
#        scrapedthumbnail = host + scrapedthumbnail
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#     <li class="next"><a href="http://xxx.justporno.tv/latest-updates/2/" data-action="ajax" data-container-id="list_videos_most_recent_videos_pagination" data-block-id="list_videos_most_recent_videos" data-parameters="sort_by:post_date;from:2">Next</a></li>


# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

#             video_url: 'http://xxx.justporno.tv/get_file/1/41ad05488e90f148c0e35d730f0dc9b1/6000/6643/6643.mp4/'


    patron = 'video_url: \'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

#    scrapedurl = scrapertools.find_single_match(data,'<iframe width=.*?src=\'(.*?)\'')
#    scrapedurl = str(scrapedurl)
    for scrapedurl in matches:
        scrapedplot = ""

        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
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
