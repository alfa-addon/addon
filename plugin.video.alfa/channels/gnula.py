# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = "http://gnula.nu/"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Estrenos", action="peliculas",
                         url= host +"peliculas-online/lista-de-peliculas-online-parte-1/", viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, title="Generos", action="generos", url= host + "generos/lista-de-generos/"))
    itemlist.append(Item(channel=item.channel, title="Recomendadas", action="peliculas",
                         url= host + "peliculas-online/lista-de-peliculas-recomendadas/", viewmode="movie"))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<spa[^>]+>Lista de g(.*?)/table')

    patron = '<strong>([^<]+)</strong> .<a href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for genero, scrapedurl in matches:
        title = scrapertools.htmlclean(genero)
        plot = ""
        url = item.url + scrapedurl
        thumbnail = ""
        itemlist.append(Item(channel = item.channel,
                             action = 'peliculas',
                             title = title,
                             url = url,
                             thumbnail = thumbnail,
                             plot = plot,
                             viewmode = "movie"))

    itemlist = sorted(itemlist, key=lambda item: item.title)

    return itemlist


def peliculas(item):
    logger.info()

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    patron  = '<a class="Ntooltip" href="([^"]+)">([^<]+)<span><br[^<]+'
    patron += '<img src="([^"]+)"></span></a>(.*?)<br'

    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedurl, scrapedtitle, scrapedthumbnail, resto in matches:
        plot = scrapertools.htmlclean(resto).strip()
        title = scrapedtitle + " " + plot
        contentTitle = scrapedtitle
        url = item.url + scrapedurl
        itemlist.append(Item(channel = item.channel,
                             action = 'findvideos',
                             title = title,
                             url = url,
                             thumbnail = scrapedthumbnail,
                             plot = plot,
                             hasContentDetails = True,
                             contentTitle = contentTitle,
                             contentType = "movie",
                             context = ["buscar_trailer"]
                             ))
    return itemlist


def findvideos(item):
    logger.info("item=" + item.tostring())
    itemlist = []

    # Descarga la página para obtener el argumento
    data = httptools.downloadpage(item.url).data
    item.plot = scrapertools.find_single_match(data, '<div class="entry">(.*?)<div class="iframes">')
    item.plot = scrapertools.htmlclean(item.plot).strip()
    item.contentPlot = item.plot
    patron = 'Ver película online.*?>.*?>([^<]+)'
    scrapedopcion = scrapertools.find_single_match(data, patron)
    titulo_opcional = scrapertools.find_single_match(scrapedopcion, ".*?, (.*)").upper()
    bloque  = scrapertools.find_multiple_matches(data, 'contenedor_tab.*?/table')
    cuenta = 0
    for datos in bloque:
        cuenta = cuenta + 1
        patron = '<em>(opción %s.*?)</em>' %cuenta
        scrapedopcion = scrapertools.find_single_match(data, patron)
        titulo_opcion = "(" + scrapertools.find_single_match(scrapedopcion, "op.*?, (.*)").upper() + ")"
        if "TRAILER" in titulo_opcion or titulo_opcion == "()":
            titulo_opcion = "(" + titulo_opcional + ")"
        urls = scrapertools.find_multiple_matches(datos, '(?:src|href)="([^"]+)')
        titulo = "Ver en %s " + titulo_opcion
        for url in urls:
            itemlist.append(Item(channel = item.channel,
                                 action = "play",
                                 contentThumbnail = item.thumbnail,
                                 fulltitle = item.contentTitle,
                                 title = titulo,
                                 url = url
                                 ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
