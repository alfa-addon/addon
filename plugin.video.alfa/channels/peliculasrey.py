# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger, config

host = "http://www.peliculasrey.com/"

def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Recientes", url=host))
    itemlist.append(Item(channel = item.channel,
                         action = "filtro",
                         title = "Año de Lanzamiento",
                         category = "lanzamiento"
                         ))
    itemlist.append(Item(channel = item.channel,
                         action = "filtro",
                         title = "Idiomas",
                         category = "idioma"
                         ))
    itemlist.append(Item(channel = item.channel,
                         action = "filtro",
                         title = "Por calidad",
                         category = "calidades"
                         ))
    itemlist.append(Item(channel = item.channel,
                         action = "filtro",
                         title = "Por género",
                         category = "generos"
                         ))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...", url=host))

    return itemlist


def filtro(item):
    logger.info(item.category)
    itemlist = []
    patron1 = '<section class="%s">(.*?)</section>' %item.category
    patron2 = '<a href="([^"]+).*?title="([^"]+)'
    data = httptools.downloadpage(host).data
    data = scrapertools.find_single_match(data, patron1)
    matches = scrapertools.find_multiple_matches(data, patron2)
    for scrapedurl, scrapedtitle in matches:
        if "Adulto" in scrapedtitle and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=scrapedtitle.strip(), url=scrapedurl,
                 viewmode="movie"))
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    tabla_pelis = scrapertools.find_single_match(data,
                                                 'class="section col-17 col-main grid-125 overflow clearfix">(.*?)</div></section>')
    patron = '<img src="([^"]+)" alt="([^"]+).*?href="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        year = scrapertools.find_single_match(scrapedtitle, "[0-9]{4}")
        fulltitle = scrapedtitle.replace(scrapertools.find_single_match(scrapedtitle, '\([0-9]+\)' ), "")
        item.infoLabels['year'] = year
        itemlist.append(item.clone(channel = item.channel,
                             action = "findvideos",
                             title = scrapedtitle,
                             url = scrapedurl,
                             thumbnail = scrapedthumbnail, 
                             plot = "",
                             fulltitle = fulltitle
                             ))
    tmdb.set_infoLabels(itemlist, True)
    next_page = scrapertools.find_single_match(data, 'rel="next" href="([^"]+)')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=">> Página siguiente", url=next_page, folder=True,
                 viewmode="movie"))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    encontrados = []
    data = httptools.downloadpage(item.url).data
    patron = 'hand" rel="([^"]+).*?title="(.*?)".*?<span>([^<]+)</span>.*?</span><span class="q">(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, server_name, language, quality in matches:
        if scrapedurl in encontrados:
            continue
        encontrados.append(scrapedurl)
        language = language.strip()
        quality = quality.strip()
        mq = "(" + quality + ")"
        if "http" in quality:
            quality = mq = ""
        titulo = "%s (" + language + ") " + mq
        itemlist.append(item.clone(channel=item.channel,
                             action = "play",
                             title = titulo,
                             url = scrapedurl,
                             folder = False,
                             language = language,
                             quality = quality
                             ))
    tmdb.set_infoLabels(itemlist, True)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist:
        itemlist.append(Item(channel=item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir pelicula a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail=item.thumbnail,
                                 fulltitle=item.fulltitle))   
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host

        elif categoria == 'documentales':
            item.url = host + "genero/documental/"

        elif categoria == 'infantiles':
            item.url = host + "genero/animacion-e-infantil/"

        elif categoria == 'terror':
            item.url = host + "genero/terror/"

        elif categoria == 'castellano':
            item.url = host + "idioma/castellano/"

        elif categoria == 'latino':
            item.url = host + "idioma/latino/"

        itemlist = peliculas(item)

        if itemlist[-1].action == "peliculas":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

