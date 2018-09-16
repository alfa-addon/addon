# -*- coding: utf-8 -*-
import re

from channelselector import get_thumb
from platformcode import logger, config
from core import scrapertools, httptools
from core import servertools
from core import tmdb
from core.item import Item
from lib import unshortenit

host = "http://www.descargacineclasico.net"


def agrupa_datos(data):
    # Agrupa los datos
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|<!--.*?-->', '', data)
    data = re.sub(r'\s+', ' ', data)
    data = re.sub(r'>\s<', '><', data)
    return data


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Últimas agregadas", action="agregadas",
                         url=host, viewmode="movie_with_plot",
                               thumbnail=get_thumb('last', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Listado por género", action="porGenero",
                         url=host,
                               thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(
        Item(channel=item.channel, title="Buscar", action="search", url=host,
                               thumbnail=get_thumb('search', auto=True)))
    return itemlist


def porGenero(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<ul class="columnas">(.*?)</ul>'
    data = re.compile(patron,re.DOTALL).findall(data)
    patron = '<li.*?>.*?href="([^"]+).*?>([^<]+)'                                            
    matches = re.compile(patron,re.DOTALL).findall(data[0])
    for url,genero in matches:
        itemlist.append( Item(channel=item.channel , action="agregadas" , title=genero,url=url, viewmode="movie_with_plot"))
    return itemlist


def search(item,texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    try:
        return agregadas(item)
    # Se captura la excepci?n, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def agregadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    fichas = re.sub(r"\n|\s{2}","",scrapertools.get_match(data,'<div class="review-box-container">(.*?)wp-pagenavi'))
    patron = '<div class="post-thumbnail"><a href="([^"]+)".*?' # url
    patron+= 'title="([^"]+)".*?' # title
    patron+= 'src="([^"]+).*?'     # thumbnail
    patron+= '<p>([^<]+)'         # plot
    matches = re.compile(patron,re.DOTALL).findall(fichas)
    for url, title, thumbnail, plot in matches:
        title = title.replace("Descargar y ver Online","").strip()
        year = scrapertools.find_single_match(title, '\(([0-9]{4})')
        fulltitle = title.replace("(%s)" %year,"").strip()
        itemlist.append( Item(action="findvideos",
                              channel=item.channel,
                              contentSerieName="",
                              title=title+" ",
                              fulltitle=fulltitle ,
                              infoLabels={'year':year},
                              url=url ,
                              thumbnail=thumbnail,
                              plot=plot,
                              show=title) )
    tmdb.set_infoLabels(itemlist)
    # Paginación
    try:
        patron_nextpage = r'<a class="nextpostslink" rel="next" href="([^"]+)'
        next_page = re.compile(patron_nextpage,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="agregadas", title="Página siguiente >>" , url=next_page[0], viewmode="movie_with_plot") )
    except: pass
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.unescape(data)
    patron = '#div_\d_\D.+?<img id="([^"]+).*?<span>.*?</span>.*?<span>(.*?)</span>.*?imgdes.*?imgdes/([^\.]+).*?<a href=([^\s]+)'  #Añado calidad
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedidioma, scrapedcalidad, scrapedserver, scrapedurl in matches:
        while True:
            loc = httptools.downloadpage(scrapedurl, follow_redirects=False).headers.get("location", "")
            if not loc or "/ad/locked" in loc:
                break
            scrapedurl = loc
        scrapedurl = scrapedurl.replace('"','')
        scrapedurl, c = unshortenit.unshorten_only(scrapedurl)
        title = item.title + "_" + scrapedidioma + "_"+ scrapedserver + "_" + scrapedcalidad
        itemlist.append( item.clone(action="play",
                                    title=title,
                                    url=scrapedurl) )
    itemlist = servertools.get_servers_itemlist(itemlist)
    tmdb.set_infoLabels(itemlist)
    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
