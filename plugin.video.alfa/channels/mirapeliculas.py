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

__channel__ = "mirapeliculas"
__category__ = "F"
__type__ = "generic"
__title__ = "mirapeliculas"
__language__ = "EN"

DEBUG = config.get_setting("debug")


def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.mirapeliculas mainlist")
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=__channel__, title="Peliculas" , action="peliculas", url="http://mirapeliculas.net/"))
#    itemlist.append( Item(channel=__channel__, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=__channel__, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://mirapeliculas.net/"))
    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist

#http://gnula.mobi/?s=sicario

def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = "http://mirapeliculas.net/buscar/?q=%s" % texto

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



def categorias(item):
    logger.info("pelisalacarta.mirapeliculas categorias")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


#      <li class="cat-item cat-item-3"><a href="http://mirapeliculas.net/genero/accion/" title="Acción">Acción</a> <span>2</span> </li>
    patron  = '<li class="cat-item cat-item-3"><a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = "http://qwertty.net"+scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info("pelisalacarta.mirapeliculas peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <div class="col-mt-5 postsh">
#                                             <div class="poster-media-card hd-real-720">
#                                                 <a href="http://mirapeliculas.net/pelicula/he-even-has-your-eyes-/" title="Ver Película He Even Has Your Eyes  Completa">
#                                                     <div class="poster">
#                                                         <div class="title"><span class="under-title-gnro">HD</span> </div>
#                                                         <div class="ano">
#                                                             <p>2016</p>
#                                                         </div>
#                                                         <div class="poster-image-container"> <img src="https://2.bp.blogspot.com/-jEfLt0UDf48/WQo6cxELapI/AAAAAAAAAU4/whvsjDP7ICwu4JPVz2GcbQlJyeQQKJwkwCLcB/s200/Il_a_deja_tes_yeux_poster_francia.jpg" width="300" height="428" border="0"> </div>
#                                                     </div>
#                                                 </a>
#                                                 <div class="info"><a href="http://mirapeliculas.net/pelicula/he-even-has-your-eyes-/" title="He Even Has Your Eyes  " class="info-title one-line"><h2>He Even Has Your Eyes  </h2></a> </div>
#                                             </div>
#                                         </div>

    patron  = '<div class="col-mt-5 postsh">.*?<a href="([^"]+)".*?<span class="under-title-gnro">([^"]+)</span>.*?<p>(\d+)</p>.*?<img src="([^"]+)".*?title="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,calidad,scrapedyear,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
        scrapedtitle = scrapedtitle + " (" + scrapedyear + ") " + "[COLOR red]" + calidad + "[/COLOR]"
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )



#        <span class="current">1</span> <a href="http://mirapeliculas.net/page/2" class="single_page">2</a>


# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<span class="current">\d+</span>.*?<a href="([^"]+)"')
#    next_page_url = item.url + next_page_url

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__ , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info("pelisalacarta.mirapeliculas findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)

#    <b>Titulo original:</b> Hell or High Water (Comanchería) (2016)<br>
#    <b>Género:</b> <a href="http://mirapeliculas.net/categoria/thriller/" title="">Thriller</a><br>
#    <b>Año:</b> 2016 <br>
#    <b>Idioma:</b> Español <br>
#    <b>Calidad:</b> BR-Rip <br>
#    <b>Visualizada:</b> 221 veces <br>
#    <div class="divSinopsis"><b>Sinopsis:</b> La trama gira en torno a dos hermanos, un padre divorciado a cargo de dos hijos y un ex convicto. Ambos se enfrentan a la pérdida de su granja familiar en Texas porque no pueden afrontar el pago. Para intentar salvar la propiedad ponen en marcha un plan: robarán un banco de la zona. Pero no todo es tan fácil como parece ya que en el camino se encontrarán con un par de agentes de los Ranger de Texas que no se darán por vencidos hasta que los atrapen.   <br>
#    <div id="pubs2">

#        idioma = scrapertools.find_multiple_matches(match,'<img src="[^"]+" title="([^"]+)"')

    patron  = '<div id="contenido">(.*?)"<div id="pubs2">'
    datos = re.compile(patron,re.DOTALL).findall(data)


# <div id="tab1" class="contenido_tab">
# 		<div style="text-align:center;">
# 					<iframe src="https://openload.co/embed/AmMOeajpiPQ/" scrolling="no" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true" width="640" height="380" frameborder="0"></iframe>
# 		</div>
# 	</div>

    patron  = '<div style="text-align:center;">.*?<iframe src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl  in matches:
        idioma = scrapertools.find_single_match(datos,'<b>Idioma:</b>(.*?)<br>')
        calidad = scrapertools.find_single_match(datos,'<b>Calidad:</b>(.*?)<br>')
        scrapedplot= scrapertools.find_single_match(datos,'<b>Sinopsis:</b>(.*?)<br>')
        scrapedtitle = str(idioma) + str(calidad)
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"]")
        itemlist.append(item.clone(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , plot=scrapedplot , folder=True) )
    return itemlist

def play(item):
    logger.info("pelisalacarta.mirapeliculas play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

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
