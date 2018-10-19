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
__channel__ = "sexkino"
__category__ = "F"
__type__ = "generic"
__title__ = "sexkino"
__language__ = "ES"


def mainlist(item):
    logger.info("pelisalacarta.sexkino mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="New" , action="peliculas", url="http://sexkino.to/movies/"))
#    itemlist.append( Item(channel=__channel__, title="Castellano" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-espanol/"))
#    itemlist.append( Item(channel=__channel__, title="Latino" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-latino/"))
#    itemlist.append( Item(channel=__channel__, title="VO" , action="peliculas", url="http://www.tupelicula.tv/filter?language=3"))
#    itemlist.append( Item(channel=__channel__, title="Portugues" , action="peliculas", url="http://www.tupelicula.tv/filter?language=5"))
#    itemlist.append( Item(channel=__channel__, title="VOS" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-sub-espanol/"))
    itemlist.append( Item(channel=__channel__, title="Año" , action="anual", url="http://sexkino.to/"))
    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://sexkino.to/"))

#    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = "http://sexkino.to/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info("pelisalacarta.sexkino categorias")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#  data = httptools.downloadpage(item.url).data

# <li class="cat-item cat-item-1275"><a href="http://sexkino.to/genre/amateur/" >Amateur</a> <i>36</i>


    patron  = '<li class="cat-item cat-item-.*?<a href="(.*?)" >(.*?)</a> <i>(.*?)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,cantidad  in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " ("+cantidad+")"
#        scrapedtitle = scrapedtitle.replace("Pelculas de ", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
#        scrapedthumbnail ="http://www.porntrex.com" + scrapedthumbnail
#        scrapedurl ="http://www.porntrex.com" + scrapedurl

        itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def anual(item):
    logger.info("pelisalacarta.sexkino anual")
    itemlist = []
    data = scrapertools.cachePage(item.url)

#           <li><a href="http://sexkino.to/release/2017/">2017</a></li>
    patron  = '<li><a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist



def peliculas(item):
    logger.info("pelisalacarta.sexkino peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



# <article class="item movies" id="post-2643">
# 	<div class="poster">
# 		<a href="http://sexkino.to/movies/big-anal-asses-4/"><img src="https://i1.wp.com/sexkino.to/wp-content/uploads/2017/02/10143847.jpg?resize=185%2C278" alt="Big Anal Asses # 4"></a>
# 				<div class="rating"><span class="icon-star2"></span> 10</div>
# 						<span class="quality">DVD</span>	</div>
# 	<div class="data">
# 		<h3><a href="http://sexkino.to/movies/big-anal-asses-4/">Big Anal Asses # 4</a></h3>
# 				<span>2016</span>
# 			</div>
# 	</article>

# <div class="figure-link-w"><a href="([^"]+)".*?src="([^"]+)".*?alt="(.*?)"

    patron  = '<div class="poster">.*?<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)">.*?<span>(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)



    for scrapedurl,scrapedthumbnail,scrapedtitle,date in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + date + ")"
        # scrapedurl = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", scrapedurl)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        scrapedthumbnail = "http://www.xxxparodyhd.com" + scrapedthumbnail

        itemlist.append( Item(channel=__channel__, action="findvideos", title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#<div class='resppages'><a href="http://sexkino.to/movies/page/2/" ><span class="icon-chevron-right"></span></a></div>	</div>

#  "Next Page >>"
    next_page_url = scrapertools.find_single_match(data,'resppages.*?<a href="([^"]+)" ><span class="icon-chevron-right">')
#    next_page_url = "http://sexody.com" + next_page_url
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__ , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist



def findvideos(item):
    logger.info("pelisalacarta.a0 findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)


# <tbody>
# <tr id="217669">
# <td><a class="link_a" href="http://sexkino.to/links/217669/" target="_blank">Watch online</a></td>
# <td><img src="https://plus.google.com/_/favicon?domain=xvidstage.com"> xvidstage.com</td>
# <td>DVDRip</td>
# <td>German</td>
# <td>1 day </td>
# </tr>
# <tbody>


    patron  = '<tr id=(.*?)</tr>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match,'href="([^"]+)" target')
#        url = url.replace("'","").replace("load_hoster(","")
#        url = str(url)
        title = scrapertools.find_single_match(match,'<td><img src=.*?> (.*?)</td>')

        itemlist.append(item.clone(action="play", title=title, url=url))


# <div class="playex">
# 									<div id="option-1" class="play-box-iframe fixidtab">
# 				<iframe class="metaframe rptss" src="https://streamcherry.com/embed/pqbkcfdmcscdslbs/" frameborder="0" allowfullscreen></iframe>
# 			</div>
#
# 	</div>
# 		<div class="control">
# 		<nav class="player">
# 			<ul class="options">
# 				<li>
# 					<a><i class="icon-menu"></i> <b>Options</b></a>
# 											<ul class="idTabs">
# 													<li><a class="options" href="#option-1">
# 							Streamcherry
# 							<span class="dt_flag"><img src="http://sexkino.to/wp-content/themes/Dooplay1.1.9.1/assets/img/flags/de.png"></span>							</a></li>
#
# 						</ul>

    # 								<div id="option-1" class="play-box-iframe fixidtab">
	# 			<iframe src="https://openload.co/embed/kaSEVuTUZdU/" frameborder="0" allowfullscreen></iframe>
	# 		</div>
	#
	# </div>
	# 	<div class="control">
	# 	<nav class="player">
	# 		<ul class="options">
	# 			<li>
	# 				<a><i class="icon-menu"></i> <b>Options</b></a>
	# 										<ul class="idTabs">
	# 												<li><a href="#option-1">Openload </a></li>
	#
	# 					</ul>
	# 								</li>
	# 		</ul>
	# 	</nav>
    patron  = '<iframe class="metaframe rptss" src="([^"]+)".*?<li><a class="options" href="#option-\d+">\s+(.*?)\s+<'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle
        itemlist.append(item.clone(action="play", title=title, url=url))
    return itemlist



def play(item):
    logger.info("pelisalacarta.sexkino play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist



# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    peliculas_items = peliculas(mainlist_items[0])
    bien = False
    for pelicula_item in peliculas_items:
        mirrors = servertools.find_video_items( item=pelicula_item )
        if len(mirrors)>0:
            bien = True
            break

    return bien
