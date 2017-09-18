# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger, config

host = "http://www.peliculasrey.com/"

def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Recientes", url=host))
    itemlist.append(Item(channel=item.channel, action="PorFecha", title="Año de Lanzamiento", url=host))
    itemlist.append(Item(channel=item.channel, action="Idiomas", title="Idiomas", url=host))
    itemlist.append(Item(channel=item.channel, action="calidades", title="Por calidad", url=host))
    itemlist.append(Item(channel=item.channel, action="generos", title="Por género", url=host))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...", url=host))

    return itemlist


def PorFecha(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="lanzamiento">(.*?)</section>')

    # Extrae las entradas (carpetas)
    patron = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fulltitle=title, viewmode="movie"))

    return itemlist


def Idiomas(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="idioma">(.*?)</section>')

    # Extrae las entradas (carpetas)
    patron = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fulltitle=title, viewmode="movie"))

    return itemlist


def calidades(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="calidades">(.*?)</section>')

    # Extrae las entradas (carpetas)
    patron = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fulltitle=title, viewmode="movie"))

    return itemlist


def generos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="generos">(.*?)</section>')
    patron = '<a href="([^"]+).*?title="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        thumbnail = ""
        plot = ""
        url = urlparse.urljoin(item.url, scrapedurl)
        if "Adulto" in title and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fulltitle=title, viewmode="movie"))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto

    try:
        # return buscar(item)
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    tabla_pelis = scrapertools.find_single_match(data,
                                                 'class="section col-17 col-main grid-125 overflow clearfix">(.*?)</div></section>')
    patron = '<img src="([^"]+)" alt="([^"]+).*?href="([^"]+)'

    matches = re.compile(patron, re.DOTALL).findall(tabla_pelis)
    itemlist = []

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        fulltitle = scrapedtitle.replace(scrapertools.find_single_match(scrapedtitle, '\([0-9]+\)' ), "")
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             title = scrapedtitle,
                             url = scrapedurl,
                             thumbnail = scrapedthumbnail, 
                             plot = "",
                             fulltitle = fulltitle
                             ))

    next_page = scrapertools.find_single_match(data, 'rel="next" href="([^"]+)')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=">> Página siguiente", url=next_page, folder=True,
                 viewmode="movie"))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    patron = 'hand" rel="([^"]+).*?title="(.*?)".*?<span>([^<]+)</span>.*?</span><span class="q">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    encontrados = []
    itemtemp = []

    for scrapedurl, server_name, language, quality in matches:
        if scrapedurl in encontrados:
            continue
        encontrados.append(scrapedurl)
        language = language.strip()
        quality = quality.strip()
        if "pelismundo" in scrapedurl:
            data = httptools.downloadpage(scrapedurl, add_referer = True).data
            patron = 'sources.*?}],'
            bloque = scrapertools.find_single_match(data, patron)
            patron = 'file.*?"([^"]+)".*?label:"([^"]+)"'
            match = scrapertools.find_multiple_matches(bloque, patron)
            for scrapedurl1, scrapedlabel1 in match:
               itemtemp.append([scrapedlabel1, scrapedurl1])
            itemtemp.sort(key=lambda it: int(it[0].replace("p", "")))
            for videoitem in itemtemp:
                itemlist.append(Item(channel = item.channel,
                                     action = "play",
                                     extra = "hdvids",
                                     fulltitle = item.fulltitle,
                                     server = "directo",
                                     thumbnail = item.thumbnail,
                                     title = "%s (" + language + ") (" + videoitem[0] + ")",
                                     url = videoitem[1],
                                     language = language,
                                     quality = videoitem[0]
                                     ))
        else:
            itemlist.append(Item(channel=item.channel,
                                 action = "play",
                                 extra = "",
                                 fulltitle = item.fulltitle,
                                 title = "%s (" + language + ") (" + quality + ")",
                                 thumbnail = item.thumbnail,
                                 url = scrapedurl,
                                 folder = False,
                                 language = language,
                                 quality = quality
                                 ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
