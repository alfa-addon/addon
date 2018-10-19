# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (terrenoresidenziale)
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

#       http://terrenoresidenziale.com      http://peliculasyestrenos.net/
host = 'http://peliculasyestrenos.net/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Recientes" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Estrenos" , action="peliculas", url=host + "/categoria/ultimos-estrenos/#prim"))
    itemlist.append( Item(channel=item.channel, title="Castellano" , action="peliculas", url=host + "/idioma/castellano/#prim"))
    itemlist.append( Item(channel=item.channel, title="latino" , action="peliculas", url=host + "/idioma/latino/#prim"))
    itemlist.append( Item(channel=item.channel, title="VOS" , action="peliculas", url=host + "/idioma/subtitulada/#prim"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
#    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host+ "/?s=%s" % texto

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
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class="generos" >(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron  = '<a href="([^"]+)" class="box-link genero">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class="cols-2">(.*?)<h2 class="section-heading">LO MAS NUEVO</h2>')

    patron  = '<div class="poster"> <img alt="([^"]+) \((\d+)\)".*?src="([^"]+)".*?<a href="([^"]+)".*?<span class="calidad ([^"]+) ">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedtitle,scrapedyear,scrapedthumbnail,scrapedurl,calidad  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle+' ('+scrapedyear+') ' + "[COLOR red]" + calidad + "[/COLOR]"
        thumbnail = scrapedthumbnail
        plot = ""
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

    try:
        patron  = '<a class="nextpostslink" rel="next" href="([^"]+)">'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
#    data = scrapertools.get_match(data,'Streaming and Download Links:(.*?)</p>')

    patron = '<tr class="diary-entry-row film-watched">.*?margin-left:45px;">([^"]+)</div>.*?"has-icon idioma icon-([^"]+)".*?<td class="center"> <span>([^"]+)</span>.*?href="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedserver,scrapedidioma,calidad,scrapedurl in matches:
        scrapedplot = ""
        scrapedidioma = scrapedidioma.replace("Castellano", "CAS").replace("Latino", "LAT").replace("Subtitulada", "VOS")
        scrapedtitle = str(scrapedserver) + "[COLOR orange]" " (" + scrapedidioma + ") "+ "[/COLOR]" + "[COLOR red]" + calidad + "[/COLOR]"
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , plot="" , folder=True) )

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = item.contentTitle))
    return itemlist

def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.contentTitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
