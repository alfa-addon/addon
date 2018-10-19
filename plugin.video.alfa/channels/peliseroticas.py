# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para Pelisxporno
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



host = 'http://www.peliculaseroticasonline.tv'


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="peliculas"  , title="Novedades" , url=host))
    itemlist.append( Item(channel=item.channel, action="categorias"  , title="Categorías" , url=host))
    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

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
    '''
      <h2>Categorias</h2>
    <ul>
    <li class="cat-item cat-item-1"><a href="http://www.peliculaseroticasonline.tv/genero/hentai/" title="Ver Hentai Online Gratis">Hentai</a></li>
    <li class="cat-item cat-item-11"><a href="http://www.peliculaseroticasonline.tv/genero/erotico/" title="Ver Cine Erotico Online Gratis">Cine Erotico</a></li>
    <li class="cat-item cat-item-12"><a href="http://www.peliculaseroticasonline.tv/genero/eroticas-de-accion/" title="Ver Peliculas Eroticas de Accion Gratis">Peliculas Eroticas de Accion</a></li>
    <li class="cat-item cat-item-13"><a href="http://www.peliculaseroticasonline.tv/genero/eroticas-de-asesinos-en-serie/" title="Ver Peliculas Eroticas de Asesinos en Serie Online Gratis">Peliculas Eroticas de Asesinos en Serie</a></li>
    <li class="cat-item cat-item-14"><a href="http://www.peliculaseroticasonline.tv/genero/eroticas-de-aventura/" title="Ver Peliculas Eroticas de Aventura Online Gratis">Peliculas Eroticas de Aventura</a></li>
    <li class="cat-item cat-item-15"><a href="http://www.peliculaseroticasonline.tv/genero/eroticas-de-belico/" title="Ver Peliculas Eroticas de Belico Online Gratis">Peliculas Eroticas de Belico</a></li>
<li class="cat-item cat-item-1"><a href="http://www.peliculaseroticasonline.tv/genero/hentai/" title="Ver Hentai Online Gratis">Hentai</a>
                            </li>
<li class="cat-item cat-item-53"><a href="http://www.peliculaseroticasonline.tv/genero/eroticas-de-accion/">Peliculas Eroticas de Accion</a></li>

    '''


    logger.info()
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url)
#    data = scrapertools.downloadpageGzip(item.url)

    # Extrae las entradas (carpetas) <div class="sidebar-right"
    bloque_cat = scrapertools.find_single_match(data, '<a href="#">Peliculas</a>(.*?)<div class="clear"></div>')
    logger.info("[peliseroticas.py] "+ bloque_cat)
#<a href="http://www.peliculaseroticasonline.tv/genero/hentai/" title="Ver Hentai Online Gratis">Hentai</a>
    patronvideos ='<a href="([^"]+)".*?>(.*?)</a>'
    matches = re.compile(patronvideos,re.DOTALL).findall(bloque_cat)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("Peliculas Eroticas en", "").replace("Peliculas Eroticas de", "").replace("idiomas", "").replace("categorias", "")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , folder=True) )

    return itemlist

def peliculas(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url)

    '''


<div class="movie-preview movie-88526 existing_item res_item col-6">
                            <div class="movie-preview-content">
                                <div class="movie-poster"><a href="http://www.peliculaseroticasonline.tv/violada-napoles-xxx-2003/"><span class="center-icons"><span class="icon-hd tooltip-w" title="Calidad HD ">HD</span></span><div class="imagen"> <img src="http://www.peliculaseroticasonline.tv/wp-content/uploads/2017/08/Violada-en-N25C325A1poles-2000-Espa25C325B1ol.jpg" alt="Violada en Nápoles xXx (2003)"/></div></a>
                                    <div class="small_rating">
                                        <div class="ratebox">
                                            <div id="ratig-layer-104">
                                                <div id="post-ratings-88526" class="post-ratings" data-nonce="5b02786ec3"><img id="rating_88526_1" src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/stars/rating_on.gif" alt="1 Star" title="1 Star" onmouseover="current_rating(88526, 1, '1 Star');" onmouseout="ratings_off(3.5, 4, 0);" onclick="rate_post();" onkeypress="rate_post();" style="cursor: pointer; border: 0px;" height="15px" width="15px" /><img id="rating_88526_2" src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/stars/rating_on.gif" alt="2 Stars" title="2 Stars" onmouseover="current_rating(88526, 2, '2 Stars');" onmouseout="ratings_off(3.5, 4, 0);" onclick="rate_post();" onkeypress="rate_post();" style="cursor: pointer; border: 0px;" height="15px" width="15px" /><img id="rating_88526_3" src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/stars/rating_on.gif" alt="3 Stars" title="3 Stars" onmouseover="current_rating(88526, 3, '3 Stars');" onmouseout="ratings_off(3.5, 4, 0);" onclick="rate_post();" onkeypress="rate_post();" style="cursor: pointer; border: 0px;" height="15px" width="15px" /><img id="rating_88526_4" src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/stars/rating_half.gif" alt="4 Stars" title="4 Stars" onmouseover="current_rating(88526, 4, '4 Stars');" onmouseout="ratings_off(3.5, 4, 0);" onclick="rate_post();" onkeypress="rate_post();" style="cursor: pointer; border: 0px;" height="15px" width="15px" /><img id="rating_88526_5" src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/stars/rating_off.gif" alt="5 Stars" title="5 Stars" onmouseover="current_rating(88526, 5, '5 Stars');" onmouseout="ratings_off(3.5, 4, 0);" onclick="rate_post();" onkeypress="rate_post();" style="cursor: pointer; border: 0px;" height="15px" width="15px" />
                                                </div>
                                                <div id="post-ratings-88526-loading" class="post-ratings-loading"> <img src="http://www.peliculaseroticasonline.tv/wp-content/plugins/wp-postratings/images/loading.gif" width="16" height="16" class="post-ratings-image" height="15px" width="15px" />Loading...</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="movie-details existing-details"><span class="movie-title"><a href="http://www.peliculaseroticasonline.tv/violada-napoles-xxx-2003/" title="Violada en Nápoles xXx (2003)">Violada en Nápoles xXx (2003)</a></span>
                                    <div class="movie-specials">
                                        <div class="tags info">
                                            <h4>Film</h4>: <a href="http://www.peliculaseroticasonline.tv/tag/eroticas-del-ano-2003/" rel="tag">Peliculas Eroticas del Año 2003</a>
                                        </div>
                                        <div class="movie-excerpt">
                                            <p class="story">Un pescador napolitano necesita una gran cantidad de dinero en la seguridad de su amada esposa hermosa. Pero algo le empuja a los juegos de azar. Como...</p>
                                        </div>
                                        <div class="movie-info"><span class="icon-eye views tooltip">31,877 <span class="flear"></span><small>Vistas</small>
                                            </span><span class="icon-comment comments tooltip">1 <span class="flear"></span><small>Comentarios</small>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>


    <div class="moviefilm cssToolTip"[^"]+<a href="([^"]+)"> <img src="([^"]+)" alt="([^"]+)"
    <div class="thumb">\n.*?<a href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)".*?\/>
    '''


    # Extrae las entradas (carpetas)

    patron ='<div class="movie-poster">.*?<a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle.replace("Ver Pel\ícula", "")
#        scrapedtitle = "[COLOR limegreen]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
#        scrapedtitle = str(scrapedtitle)
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = scrapedurl.replace("/xxx.php?tube=", "")
#        scrapedthumbnail = host + scrapedthumbnail
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    #Extrae la marca de siguiente página

#        <div class="naviright"><a href="http://www.peliculaseroticasonline.tv/page/2/">Siguiente &raquo;</a>

    next_page_url = scrapertools.find_single_match(data,'<div class="naviright"><a href="([^"]+)">Siguiente &raquo;</a>')
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist




def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

# <div id="option1" class="tab_part  "> <iframe src="/player/play.php?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9YZ3V5OE55LXVJSS8=" frameborder="0" allowfullscreen></iframe></div>
# <div id="option2" class="tab_part  "> <iframe src="/player/play.php?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9YZ3V5OE55LXVJSS8=" frameborder="0" allowfullscreen></iframe></div></div>
# https://ph2dra.oloadcdn.net/dl/l/p2_PgPfBdrjMjqEg/Xguy8Ny-uII/Pure+Sexual+Attraction+7.MP4.mp4?mime=true

    patron  = '<div id="option\d" class="tab_part  "> <iframe src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl  in matches:
#        scrapedplot = ""
        scrapedurl = host + scrapedurl
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

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
