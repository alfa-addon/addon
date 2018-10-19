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

IDIOMAS = {"Castellano":"CAST","Latino":"LAT","Subtitulado":"VOSE","Ingles":"VO"}

host = 'http://pelis24.mobi'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Recientes" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url="http://peliculas-porno-gratis.com/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def categorias(item):
        itemlist = []
        data = scrapertools.cachePage(item.url)

#        <li id="menu-item-225" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-225"><a href="http://pelis24.mobi/genero/movies-accion/">Acción</a></li>


        patron  = '<li id="menu-item-\d+".*?<a href="([^<]+)">(.*?)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

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

# <li class="col-md-12 itemlist">
# <div class="list-score">Estreno</div>
# <div class="col-xs-2">
# <div class="row">
# <a href="http://pelis24.mobi/pelicula/aliados-allie-2016-online/" title="Aliados (Allied) (2016)">
# <img src="http://image.tmdb.org/t/p/w300/s7DBLUzrrNDfzfNjuJ1tS8GcfOw.jpg" title="Aliados (Allied) (2016)" alt="Aliados (Allied) (2016)"/>
# </a>
# </div>
# </div>
# <div class="col-xs-10">
# <a href="http://pelis24.mobi/pelicula/aliados-allie-2016-online/" title="Aliados (Allied) (2016)">
# <h2 class="title-list">Aliados (Allied) (2016)</h2>
# </a>
# <div class="clear"></div>
# <p class="main-info-list">Película de 2016</p>
# <p class="text-list">1942. Segunda Guerra Mundial. Max (Brad Pitt) es un espía del bando aliado que se enamora de Marianne (Marion Cotillard), una compañera francesa, tras una peligrosa misión en el norte de África. La pareja comienza una relación amorosa hasta que ...</p>
# </div>
# </li

    patron = '<div class="col-xs-2">.*?<a href="([^"]+)" title="([^<]+) \((\d+)\)">.*?<img src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,scrapedtitle,scrapedyear,scrapedthumbnail in matches:
        title = scrapedtitle + " (" + scrapedyear + ")"
        itemlist.append(item.clone(title=title, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail , contentTitle=scrapedtitle, infoLabels={'year':scrapedyear} ))

# <div class='wp-pagenavi'><span class='current'>1</span><a rel='nofollow' class='page larger' href='http://ciberstar.com/page/2?s=aliados'>2</a></div></div>
# </div> <a rel='nofollow' class=previouspostslink' href='http://ciberstar.com/page/2?s=casa'>Siguiente &rsaquo;</a>

#        "Next page >>" <a href="http://pelis24.mobi/page/2/?s=la" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a>
    try:
        patron  = '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="sub_search", title="[COLOR blue]" + "Next page >>" + "[/COLOR]" , url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
# <div class="col-mt-5 postsh">
# <div class="poster-media-card">
# <a href="http://pelis24.mobi/pelicula/que-le-dijiste-dios-2014/" title="¿Qué le dijiste a Dios? (2014)">
# <div class="poster">
# <div class="title">
# <span class="under-title">¿Qué le dijiste a Dios? (2014)</span>
# </div>
# <span class="rating">
# <i class="glyphicon glyphicon-star"></i><span class="rating-number">4</span>
# </span>
# <div class="poster-image-container">
# <img width="300" height="428" src="http://image.tmdb.org/t/p/w90/rxORUWlntFGFkV8dOqeTiLRWJ8l.jpg" title="¿Qué le dijiste a Dios? (2014)" alt="¿Qué le dijiste a Dios? (2014)"/>
# </div>
# </div>
# </a>
# </div>                    + "[COLOR red]" + calidad + "[/COLOR]"

    patron  = '<div class="col-mt-5 postsh">.*?<a href="([^<]+)" title="([^<]+) \((\d+)\)">.*?src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedyear,scrapedthumbnail  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle

        title = scrapedtitle + " (" + scrapedyear + ") "
        thumbnail = scrapedthumbnail
        plot = ""
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#           <a href="http://pelis24.mobi/page/2/" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a

    try:
        patron  = '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


    # <li><a href="#embed1" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9kcml2ZS5nb29nbGUuY29tL29wZW4_aWQ9MEIwU2pqaGc2WmR3eFR6UmpYMUJzWmtOV1JqUQ&value=Z2Q&thumb=aHR0cHM6Ly9pbWFnZS50bWRiLm9yZy90L3AvdzUzM19hbmRfaDMwMF9iZXN0djIvZVJkY0ZEb1duWjVoaWE3cHRVT092eVBEbEUwLmpwZw" class="Español" data-toggle="tab">Español</a></li>
    # <li><a href="#embed2" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9kcml2ZS5nb29nbGUuY29tL29wZW4_aWQ9MEIwU2pqaGc2WmR3eFR6UTVhREJoUW1sSVF6QQ&value=Z2Q&thumb=aHR0cHM6Ly9pbWFnZS50bWRiLm9yZy90L3AvdzUzM19hbmRfaDMwMF9iZXN0djIvbjRWMllZQ0NMa0w2Q05lNkpuV2hiWjVEUzJ3LmpwZw" class="Latino" data-toggle="tab">Latino</a></li>
    # <li><a href="#embed3" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9kcml2ZS5nb29nbGUuY29tL29wZW4_aWQ9MEIwU2pqaGc2WmR3eGFYaGhjM0JzTnpKalRUQQ&value=Z2Q&thumb=aHR0cHM6Ly9pbWFnZS50bWRiLm9yZy90L3AvdzUzM19hbmRfaDMwMF9iZXN0djIvbjRWMllZQ0NMa0w2Q05lNkpuV2hiWjVEUzJ3LmpwZw" class="Subtitulado" data-toggle="tab">Subtitulado</a></li>
    # <li><a href="#embed4" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9Pdjk2VENWTWxycy8&value=b3U" class="Latino" data-toggle="tab">Latino</a></li>
    # <li><a href="#embed5" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9rSEV6elV3Q2hTWQ&value=b3U" class="Español" data-toggle="tab">Español</a></li>
    # <li><a href="#embed6" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC96SXJXUW9MU05HQQ&value=b3U" class="Subtitulado" data-toggle="tab">Subtitulado</a></li>
    # <li><a href="#embed7" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly93d3cucmFwdHUuY29tL2VtYmVkL0ZGQURGUkVUS0M&value=b3U" class="Latino" data-toggle="tab">Latino</a></li>
    # <li><a href="#embed8" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly93d3cucmFwdHUuY29tL2VtYmVkL0ZGQURHMkRJM1g&value=b3U" class="Subtitulado" data-toggle="tab">Subtitulado</a></li>
    # <li><a href="#embed9" data-src="http://pelis24.mobi/redirect/?id=aHR0cHM6Ly93d3cucmFwdHUuY29tL2VtYmVkL0ZGQURGMk82VTM&value=b3U" class="Español" data-toggle="tab">Español</a></li>	</ul>


			# <tr>
			# <td><a href="https://openload.co/f/qo4HCJ5hVsk/Resident_Evil_Cap%C3%ADtulo_final_%282017%29_-_Latino_720p.avi.mp4" class="btn btn-xs btn-info" rel="nofollow" target="_blank" style="min-width: 86px;"><span style="margin-right: 2px;" class="glyphicon glyphicon-play" aria-hidden="true"></span> Opcion 1</a></td>
			# <td><img src="http://www.google.com/s2/favicons?domain=https://openload.co/f/qo4HCJ5hVsk/Resident_Evil_Cap%C3%ADtulo_final_%282017%29_-_Latino_720p.avi.mp4" title="Openload" style="margin: 0 3px 0 0;" /><span>Openload</span></td>
			# <td>Latino</td>
			# <td>HD Rip 720p</td>
            #
			# </tr>

    patron  = '<td><a href="([^"]+)".*?title="([^"]+)".*?<td>(.*?)</td>.*?<td>(.*?)</td>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,scrapedtitle,idioma,calidad  in matches:
        title = scrapedtitle + " [" + idioma + "] " + "[COLOR red]" + calidad + "[/COLOR]"
        itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    if config.get_library_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
#    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
