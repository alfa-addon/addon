# -*- coding: utf-8 -*-

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'flashx', 'openload', 'vimeo', 'netutv']


__channel__='allcalidad'

host = "http://allcalidad.com/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host, thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos_years", url = host, extra = "Genero", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "generos_years", url = host, extra = ">Año<", thumbnail = get_thumb("year", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Favoritas", action = "peliculas", url = host + "/favorites", thumbnail = get_thumb("favorites", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "?s=", thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'
        elif categoria == 'terror':
            item.url = host + 'category/torror/'
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos_years(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?s)%s(.*?)</ul></div>' %item.extra
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'href="([^"]+)'
    patron += '">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url
                             ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)short_overlay.*?<a href="([^"]+)'
    patron += '.*?img.*?src="([^"]+)'
    patron += '.*?title="(.*?)"'
    patron += '.*?(Idioma.*?)post-ratings'

    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumbnail, titulo, varios in matches:
        idioma = scrapertools.find_single_match(varios, '(?s)Idioma.*?kinopoisk">([^<]+)')
        number_idioma = scrapertools.find_single_match(idioma, '[0-9]')
        mtitulo = titulo
        if number_idioma != "":
            idioma = ""
        else:
            mtitulo += " (" + idioma + ")"
        year = scrapertools.find_single_match(varios, 'Año.*?kinopoisk">([^<]+)')
        year = scrapertools.find_single_match(year, '[0-9]{4}')
        if year:
            mtitulo += " (" + year + ")"
            item.infoLabels['year'] = int(year)
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitulo,
                                   fulltitle = titulo,
                                   thumbnail = thumbnail,
                                   url = url,
                                   contentTitle = titulo,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, 'next" href="([^"]+)')
    if url_pagina != "":
        pagina = "Pagina: " + scrapertools.find_single_match(url_pagina, "page/([0-9]+)")
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if not item.infoLabels["year"]:
        item.infoLabels["year"] = scrapertools.find_single_match(data, 'dateCreated.*?(\d{4})')
        if "orig_title" in data:
            contentTitle = scrapertools.find_single_match(data, 'orig_title.*?>([^<]+)<').strip()
            if contentTitle != "":
                item.contentTitle = contentTitle
    patron = '(?s)fmi(.*?)thead'
    bloque = scrapertools.find_single_match(data, patron)
    match = scrapertools.find_multiple_matches(bloque, '(?is)(?:iframe|script) .*?src="([^"]+)')
    for url in match:
        titulo = "Ver en: %s"
        if "goo.gl" in url:
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
        if "youtube" in url:
            titulo = "[COLOR = yellow]Ver trailer: %s[/COLOR]"
        if "ad.js" in url or "script" in url or "jstags.js" in url:
            continue
        elif "vimeo" in url:
            url += "|" + "http://www.allcalidad.com"
        itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 title = titulo,
                 url = url
                 ))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

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


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
