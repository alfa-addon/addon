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

host = 'http://peliculasz.com'

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

#        <li id="menu-item-3221" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-3221"><a href="http://ciberstar.com/category/accion">Accion</a></li>

        patron  = '<li class="menu-item"> <a href="([^<]+)">(.*?)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/tag/%s" % texto

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

    patron = '<li class="s-item">.*?src="([^"]+)" alt="([^"]+)">.*?<a href="(.*?)".*?<span class="year">(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail,scrapedtitle,scrapedurl,scrapedyear in matches:
        title = scrapedtitle + " (" + scrapedyear + ")"
        itemlist.append(item.clone(title=title, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail , contentTitle=scrapedtitle, infoLabels={'year':scrapedyear} ))

# <div class='wp-pagenavi'><span class='current'>1</span><a rel='nofollow' class='page larger' href='http://ciberstar.com/page/2?s=aliados'>2</a></div></div>
# </div> <a rel='nofollow' class=previouspostslink' href='http://ciberstar.com/page/2?s=casa'>Siguiente &rsaquo;</a>

#        "Next page >>"
    try:
        patron  = 'href=\'([^\']+)\'>Siguiente &rsaquo;</a>'
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


    patron  = '<div class="item">.*?<a href="([^<]+)" title="([^<]+) \((\d+)\)">.*?<img src="(.*?)".*?<span class=\'qlabel ([^<]+)\'>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedyear,scrapedthumbnail,calidad  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle

        title = scrapedtitle + " (" + scrapedyear + ") " + "[COLOR red]" + calidad + "[/COLOR]"
        thumbnail = scrapedthumbnail
        plot = ""
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#       "Next page >>"        <li><a href="http://peliculasz.com/ver/casa/page/2">Siguiente &rsaquo;</a>

    try:
        patron  = '<li><a href="([^"]+)">Siguiente &rsaquo;</a>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

    patron  = '<li class="">.*?<a href="([^<]+)">.*?alt="(.*?)".*?alt="(.*?)".*?</span><span>(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,scrapedtitle,idioma,calidad  in matches:
        title = scrapedtitle + "  [" + idioma + "] [" + calidad + "]"
        itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = item.contentTitle))
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
