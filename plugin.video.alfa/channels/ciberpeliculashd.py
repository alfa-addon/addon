# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

__channel__='ciberpeliculashd'

host = "http://ciberpeliculashd.net"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host + "/?peli=1"))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "filtro", url = host, extra = "categories" ))
    itemlist.append(Item(channel = item.channel, title = "Por calidad", action = "filtro", url = host, extra = "qualitys"))
    itemlist.append(Item(channel = item.channel, title = "Por idioma", action = "filtro", url = host, extra = "languages"))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "/?s="))
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + "/?peli=1"
        elif categoria == 'infantiles':
            item.url = host + '/categories/animacion/?peli=1'
        elif categoria == 'terror':
            item.url = host + '/categories/terror/?peli=1'
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
    item.url = item.url + texto + "&peli=1"
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def filtro(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'uk-navbar-nav-subtitle taxonomy-menu-title">%s.*?</ul>' %item.extra
    bloque = scrapertools.find_single_match(data, patron)
    patron  = "href='([^']+)"
    patron += "'>([^<]+)"
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url + "/?peli=1"
                             ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'loop-posts".*?panel-pagination pagination-bottom')
    patron  = 'a href="([^"]+)".*?'
    patron += 'img alt="([^"]+)".*?'
    patron += '((?:http|https)://image.tmdb.org[^"]+)".*?'
    patron += 'a href="([^"]+)".*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedurl1 in matches:
        scrapedtitle = scrapedtitle.replace(" Online imagen","").replace("Pelicula ","")
        year = scrapertools.find_single_match(scrapedtitle, "\(([0-9]+)\)")
        if year:
            year = int(year)
        else:
            year = 0
        fulltitle = scrapertools.find_single_match(scrapedtitle, "(.*?) \(")
        itemlist.append(Item(action = "findvideos",
                             channel = item.channel,
                             fulltitle = fulltitle,
                             thumbnail = scrapedthumbnail,
                             infoLabels = {'year': year},
                             title = scrapedtitle,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    page = int(scrapertools.find_single_match(item.url,"peli=([0-9]+)")) + 1
    next_page = scrapertools.find_single_match(item.url,".*?peli=")
    next_page += "%s" %page
    itemlist.append(Item(action = "peliculas",
                         channel = item.channel,
                         title = "Página siguiente",
                         url = next_page
                         ))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'src=&quot;([^&]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl in matches:
        title = "Ver en: %s"
        itemlist.append(item.clone(action = "play",
                                   title = title,
                                   url = scrapedurl
                                   ))
    tmdb.set_infoLabels(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     fulltitle = item.fulltitle
                                     ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
