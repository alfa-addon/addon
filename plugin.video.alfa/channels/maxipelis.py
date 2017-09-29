# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa
# ------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb

host = 'http://www.maxipelis.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/pelicula"))

    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

    try:
        return sub_search(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron = '<div class="thumbnail animation-2"> <a href="([^"]+)"> <img src="([^"]+)" alt="(.*?)" />.*?'
    patron +='<div class="contenido"><p>(.*?)</p>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url,img,name,plot  in matches:
        itemlist.append(item.clone(channel=item.channel, action="findvideos", title=name, url=url,  plot=plot,
                                   thumbnail=img))

    paginacion = scrapertools.find_single_match(data, '<div class=\'resppages\'><a href="([^"]+)" ><span class="'
                                                      'icon-chevron-right"></span>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion))

    return itemlist

def categorias(item):
        logger.info()
        itemlist = []
        data = httptools.downloadpage(item.url).data

        patron  = '<li class="cat-item"><a href="([^"]+)".*?>(.*?)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=host + scrapedurl,
                                  thumbnail=scrapedthumbnail , plot=scrapedplot))

        return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="poster">.*?src="(.*?)" alt="(.*?)">.*?'
    patron += '"quality">(.*?)<.*?href="(.*?)".*?<span>(\d{4}).*?"texto">(.*?)<.*?'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedquality, scrapedurl, scrapedyear, scrapedplot in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        contentTitle = scrapedtitle
        quality = scrapedquality
        year = scrapedyear
        plot = scrapedplot
        if quality == "" or year=="" :
            title = contentTitle
        else:
            title = contentTitle +  " (" + year + ")  " + "[COLOR red]" + quality + "[/COLOR]"

        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, plot=plot,
                        contentTitle = contentTitle , infoLabels={'year':year} )

        if year:
            tmdb.set_infoLabels_item(new_item)
        itemlist.append(new_item)
    try:
        patron  = '<a href="([^"]+)" ><span class="icon-chevron-right"></span></a></div>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Siguiente >>" , text_color="yellow",
                              url=next_page[0]))

    except: pass
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<tr><td> <a class="link_a" href="([^"]+)".*?<td> (.*?)</td><td> (.*?)</td><td> (.*?)</td>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, server, calidad, idioma in matches:
        server = servertools.get_server_from_url(url)
        title = '%s [%s] [%s] [%s]' % (item.contentTitle, server, calidad, idioma)
        itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=url, language = idioma,
                                   contentTitle = item.contentTitle, quality = calidad, server = server))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Agregar esta pelicula a la Videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle = item.contentTitle))
    return itemlist

# def play(item):
#     logger.info()
#     itemlist = servertools.find_video_items(data=item.url)
#
#     for videoitem in itemlist:
#         videoitem.title = item.title
#         videoitem.fulltitle = item.fulltitle
#         videoitem.thumbnail = item.thumbnail
#         videoitem.channel = item.channel
#         videoitem.
#     return itemlist
