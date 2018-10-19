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
__channel__ = "pelistv"
__category__ = "F"
__type__ = "generic"
__title__ = "Pelistv"
__language__ = "ES"

DEBUG = config.get_setting("debug")
IDIOMAS = {"Castellano":"CAST","Latino":"LAT","Subtitulado":"VOSE","Ingles":"VO"}


def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.pelistv mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="New" , action="peliculas", url="http://pelistv.es/"))
#    itemlist.append( Item(channel=__channel__, title="Popular" , action="peliculas", url="http://peliculas-porno-gratis.com/"))

    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://pelistv.es/"))
    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://pelistv.es/?s=%s" % texto

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
        itemlist = []

        # Descarga la pagina
        data = scrapertools.cache_page(item.url)


        '''
     <li class="menu-item ocult"><a title="Ver Peliculas de Accion Online" href="http://www.tvpelis.tv/genero/accion/">Accion </a></li>

        '''
        # Extrae las entradas (carpetas)
        patron  = '<li class="menu-item.*?href="([^"]+)".*?>([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        patron = '<li> <a href="([^"]+)".*?>([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


        return itemlist






def peliculas(item):
    '''

      <article id="mt-102825">
                           <a href="http://www.tvpelis.tv/sevices-militaires-xxx-2017/" title="Ver Sevices Militaires XxX (2017) Online">
                              <figure class="image"><img src="https://3.bp.blogspot.com/-XW9y3G3EXaY/WmdyDsrQDUI/AAAAAAAAct0/0W_1ecUo_w4W9ect-n9XmG9wAUlVijLwACLcBGAs/s220/Sevices-Militaires-2017-214x300.jpg" alt="Sevices Militaires XxX (2017)" height="235px" width="180px" /> <span class="player"></span><em class="HD calidad2">HD</em></figure>
                           </a>
                           <span class="selectidioma"><em class="bandera spusa">Peliculas Eroticas en Ingles</em> </span>
                           <div class="fixyear">
                              <h2>Sevices Militaires XxX (2017)</h2>
                              <span class="genero">Hardcore </span>
                           </div>
                           <div class="pshd dino poab bg txts5">
                              <div class="divTituloTool"><strong>Ver Sevices Militaires XxX (2017) Online</strong></div>
                              <div class="divSinopsis">
                                 <p><strong class="reproh1">Pelicula Sevices Militaires XxX (2017) , </strong>Durante 90 días los soldados se verán obligados a pasar en un búnker aislado del ejército, completamente aislado del mundo exterior. Esta idea del...</p>
                              </div>
                              <div class="share">
                                 <div><a onclick="window.open ('http://www.facebook.com/sharer.php?u=http://www.tvpelis.tv/sevices-militaires-xxx-2017/', 'Facebook', 'toolbar=0, status=0, width=650, height=450');" class="icon-facebook" rel="nofollow"></a></div>
                                 <div><a onclick="javascript:window.open('https://twitter.com/intent/tweet?original_referer=http://www.tvpelis.tv/sevices-militaires-xxx-2017/&amp;text=Sevices Militaires XxX (2017)&amp;tw_p=tweetbutton&amp;url=http://www.tvpelis.tv/sevices-militaires-xxx-2017/', 'Twitter', 'toolbar=0, status=0, width=650, height=450');" class="icon-twitter" rel="nofollow"></a></div>
                                 <div><a href="https://plus.google.com/share?url=http://www.tvpelis.tv/sevices-militaires-xxx-2017/" onclick="javascript:window.open(this.href,'', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');return false;" class="icon-google-plus" rel="nofollow"></a></div>
                              </div>
                           </div>
                        </article>
    '''
    logger.info("pelisalacarta.pelistv peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<article id="mt-\d+">(.*?)</article>'
    matches = re.compile(patron,re.DOTALL).findall(data)

 #  <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>

    for match in matches:

        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
#        url = "http://www.tripledeseo.com/"+url
#       idioma = scrapertools.find_single_match(match,'<div class="idiomas"><div class="([^"]+)"')
#        calidad = scrapertools.find_single_match(match,'<div class="calidad"><span class="">(.*?)<')
        title = scrapertools.find_single_match(match,'alt="([^"]+)"')
#        title = title+idioma+calidad

#        title = title.replace("Ver Película","").replace("ver película","").replace("ver pelicula","").replace("Online Gratis","")
#        title = scrapertools.htmlclean(title).strip()
        plot = scrapertools.find_single_match(match,'<p class=\'story\'>(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'src="([^"]+)"')
#        thumbnail = "http://www.tripledeseo.com/"+thumbnail

        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")

        # Añade al listado
        itemlist.append( Item(channel=__channel__, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''


        <a href="http://www.tvpelis.tv/genero/adultos/page/2/" rel="nofollow">Siguiente &raquo;</a></nav>
    '''

    # Extrae el paginador  <div class="naviright"><a href="http://www.peliculaseroticasonline.tv/page/2/">Siguiente &raquo;</a>



    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" rel="nofollow">Siguiente &raquo;</a></nav>')
#    next_page_url = "http://www.tripledeseo.com/"+next_page_url
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__ , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

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
