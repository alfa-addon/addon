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

host = 'https://xxxmoviestream.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Recientes" , action="peliculas", url=host + "/?filtre=date&cat=0"))
    itemlist.append( Item(channel=item.channel, title="Mas vistas" , action="peliculas", url=host + "/?display=extract&filtre=views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/?display=extract&filtre=rate"))


    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def categorias(item):
        itemlist = []
        data = scrapertools.cachePage(item.url)


# <li class="border-radius-5 box-shadow">
#                 <img width="210" height="142" src="data:image/gif;base64,R0lGODdhAQABAPAAAP///wAAACwAAAAAAQABAEACAkQBADs=" data-lazy-src="https://xxxmoviestream.com/wp-content/uploads/2017/12/1-149-210x142.jpg" class="attachment-thumb_site size-thumb_site wp-post-image" alt="" title="Teen Wet Asses 2" /><noscript><img width="210" height="142" src="https://xxxmoviestream.com/wp-content/uploads/2017/12/1-149-210x142.jpg" class="attachment-thumb_site size-thumb_site wp-post-image" alt="" title="Teen Wet Asses 2" /></noscript>
#                 <a href="https://xxxmoviestream.com/category/movies/anal/" title="Anal"><span>Anal</span></a>
#
#                 <span class="nb_cat border-radius-5">1367 videos</span>
#             </li>


        patron  = '<li class="border-radius-5 box-shadow">.*?src="([^"]+)".*?<a href="([^"]+)" title="([^"]+)">.*?<span class="nb_cat border-radius-5">(\d+) videos</span>'
        matches = re.compile(patron,re.DOTALL).findall(data)

        for scrapedthumbnail,scrapedurl,scrapedtitle,number in matches:
            scrapedplot = ""
            title = scrapedtitle + " (" + number +")"
#            scrapedthumbnail = ""
            itemlist.append( Item(channel=item.channel, action="peliculas", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

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

#        "Next page >>" <li><a href="https://xxxmoviestream.com/page/2/?filtre=date&#038;cat=0">Next &rsaquo;</a></li>
    try:
        patron  = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a>'
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


# <li class="border-radius-5 box-shadow">
#     <div class="left">
#         <img width="210" height="142" src="data:image/gif;base64,R0lGODdhAQABAPAAAP///wAAACwAAAAAAQABAEACAkQBADs=" data-lazy-src="https://xxxmoviestream.com/wp-content/uploads/2018/03/1-13-210x142.jpg" class="attachment-thumb_site size-thumb_site wp-post-image" alt="" title="Brown Bunnies 18" /><noscript><img width="210" height="142" src="https://xxxmoviestream.com/wp-content/uploads/2018/03/1-13-210x142.jpg" class="attachment-thumb_site size-thumb_site wp-post-image" alt="" title="Brown Bunnies 18" /></noscript>
#         <a href="https://xxxmoviestream.com/brown-bunnies-18/" title="Brown Bunnies 18"><span>Brown Bunnies 18</span></a>
#             <div class="listing-infos">
#                     <!-- Views -->
#                     <div class="views-infos" style="width: 49%;">1 <span class="views-img"></span></div>
#                     <!-- Time -->
#                         <div class="time-infos" style="background: none; border-right: none; width: 50%;"> - <span class="time-img-img"></span></div>
#
#         </div><!-- .listing-infos -->
#
#     </div><!-- .left -->
#     <div class="right">
#         <p>Cast: Anya Ivy, Lisa Tiffian, Monique Symone, Porsha Carrera, Yasmine de Leon, Yasmine DeLeon Brown Bunnies Vol. 18 Porsha Carrera &#8211; Deep in dat chocolate pussy!!!! Monique Symone &#8211; Big tit ebony pounded hardcore!!! Lisa Tiffian &#8211; Thick ebony pussy gets railed!!! Yasmine De Leon &#8211; Thick ebony swallows all of that cum!!! Anya Ivy &#8211; Mocha skinned cutie interracial fucking!!!</p>
#     </div><!-- .right -->
# </li>

#                + "[COLOR red]" + calidad + "[/COLOR]"

    patron  = '<li class="border-radius-5 box-shadow">.*?src="([^"]+)" class="attachment-thumb_site size-thumb_site wp-post-image" alt="".*?<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail,scrapedurl,scrapedtitle  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle
        contentTitle = title
#        title = scrapedtitle + " (" + scrapedyear + ") "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#                   <li><a href="https://xxxmoviestream.com/page/3/?display=extract&#038;filtre=views">Next &rsaquo;</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)">Next &rsaquo;</a></li>')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.get_match(data,'<div class="video-embed">(.*?)</div>')


# <div class="video-embed">
# <iframe src="https://xtheatre.net/wp-content/plugins/wp-rocket/inc/front/img/blank.gif" data-lazy-src="https://streamango.com/embed/rbbpqqbbnpeptbmc/1234BgTtsRndAs42_MP4_mp4" scrolling="no" frameborder="0" width="700" height="430" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>
# </div>
# </div>

    patron  = 'data-lazy-src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        title = scrapedurl
        itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))
    return itemlist


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
