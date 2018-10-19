# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import httptools
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

## italiafilm


host = "http://gnula.mobi"

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.gmobi mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="New" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Castellano" , action="peliculas", url=host +"/tag/espanol/"))
    itemlist.append( Item(channel=item.channel, title="Latino" , action="peliculas", url=host + "/tag/latino/"))
    itemlist.append( Item(channel=item.channel, title="VOSE" , action="peliculas", url=host + "/tag/subtitulada/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


#http://gnula.mobi/?s=sicario

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://gnula.mobi/?s=%s" % texto

    try:
        return sub_search(item)

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

def categorias(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#              <option class="level-0" value="89">Acción</option>
    patron  = '<option class="level-0" value="\d+">(.*?)</option>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for title in matches:
#        title = scrapertools.find_single_match(match,'<option class="level-0" value="\d+">(.*?)</option>')
        url = host + title
        itemlist.append( Item(channel=item.channel, action="peliculas", title=title , fulltitle=title, url=url , viewmode="movie", folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="col-mt-5 postsh">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)


    for match in matches:
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
#        url = "http://www.tripledeseo.com/"+url
#        idioma = scrapertools.find_multiple_matches(match,'<img src="[^"]+" title="([^"]+)"')
        calidad = scrapertools.find_single_match(match,'class="rating-number">(.*?)</span>')
        calidad = calidad.replace("Ahora en ", "")
        title = scrapertools.find_single_match(match,'title="([^"]+)"')
#        title = title + idioma

#        title = title.replace("Ver Película","").replace("ver película","").replace("ver pelicula","").replace("Online Gratis","")
#        title = scrapertools.htmlclean(title).strip()
        plot = ""
#        plot = scrapertools.find_single_match(match,'<div class="divSinopsis"> (.*?)</div>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'src="([^"]+)"')
#        thumbnail = "http://www.tripledeseo.com/"+thumbnail
# pelisalacarta.channels.a1 [peliculas] title=[Backyard (El traspatio) (2009)], url=[http://gnula.mobi/15565/pelicula/backyard-traspatio-2009/], thumbnail=[http://image.tmdb.org/t/p/w185/4HJD3venwfgGfCKm8MdkPgoj9pF.jpg]

        itemlist.append( Item(channel=item.channel, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )



    # Extrae el paginador   <a href="http://www.gnula.mobi/page/2/"><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a>
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"')
#    next_page_url = "http://www.tripledeseo.com/"+next_page_url
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

'''
def findvideos(item):
    logger.info("pelisalacarta.gmobi findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = scrapertools.get_match(data,'<div class="table-responsive dlmt" id="olmt">(.*?)</div>')

<ul class="nav nav-pills reprobut"><li class="active" ><a href="#embed1" data-toggle="tab">Latino</a></li><li><a href="#trailerpro" data-toggle="tab">Trailer</a></li>
</ul>
<div class="tab-content">
<div class="tab-pane reproductor repron active" id="embed1">
<div class="calishow">HD Real 720</div>
<div id="repro54439"><iframe width="100%" height="400" src="https://openload.co/embed/Niv6R3QmWTw/tt0388980.mp4" frameborder="0" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true" oallowfullscreen="true" msallowfullscreen="true"></iframe></div>
<div class="clear"></div></div><div class="tab-pane reproductor repron" id="trailerpro"><div class="container_trailer"><iframe width="100%" height="200" src="//www.youtube.com/embed/q4TZ3yb2DmU" frameborder="0" allowfullscreen></iframe><i>Trailer de Entrenador Carter (2005)</i>	</div></div><div class="clear"></div></div>                        <div class="clear"></div>
<center>
<a href="http://bit.ly/2hr8NZ6" rel="nofollow"><img class="img-responsive" src="https://lh3.googleusercontent.com/-322HiW2VDdI/V4EZsPCrolI/AAAAAAAAAio/_DJ5HTzrxlkSB0gFLYnLCNx8v8Csakw3ACCo/s585/1.PNG" title="descargar Entrenador Carter (2005) gratis" alt="descargar Entrenador Carter (2005) gratis" /></a></center>
<div class="clear"></div>


    patron  = '<td><a href="([^<]+)".*?<td>.*?title="(.*?)".*?<td>(.*?)</td>.*?<td>(.*?)</td>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,idioma,calidad  in matches:
        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
        scrapedtitle = scrapedtitle + "  " + str(idioma) + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"]")
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , folder=True) )
    return itemlist



def play(item):
    logger.info("pelisalacarta.gmobi play")
    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''


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
