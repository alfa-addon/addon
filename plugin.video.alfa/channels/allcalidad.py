# -*- coding: utf-8 -*-

import sys, base64
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from channelselector import get_thumb
from modules import autoplay
from modules import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


IDIOMAS = {'Latino': 'Latino'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['fembed', 'streamtape', 'gvideo', 'Jawcloud']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'allcalidad', 
             'host': config.get_setting("current_host", 'allcalidad', default=''), 
             'host_alt': ["https://allcalidad.re"],
             'host_black_list': ["https://allcalidad.si", "https://allcalidad.ms/", "https://allcalidad.ms",
                                 "https://allcalidad.is", "https://allcalidad.ac"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
__channel__ = canonical['channel']

encoding = "utf-8"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = []
    
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host + "api/rest/listing?post_type=movies&posts_per_page=16&page=", extra="", pagina = 1, thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos", url = host + "peliculas", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "search/" , pagina=1, thumbnail = get_thumb("search", auto = True)))
    
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
            item.url = host + '/category/animacion/'
        elif categoria == 'terror':
            item.url = host + '/category/torror/'
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
    #https://allcalidad.re/api/rest/search?post_type=movies%2Ctvshows%2Canimes&query=star&posts_per_page=16&page=1
    item.url = host + "api/rest/search?post_type=movies%2Ctvshows%2Canimes&query=" + texto + "&posts_per_page=16&page=" #%texto #+ "/?page="
    item.pagina = 1
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos(item):
    logger.info()
    
    itemlist = []
    
    data = httptools.downloadpage(item.url, encoding=encoding, canonical=canonical).data
    sub = scrapertools.find_single_match(data, "(?ims)genres:({.*?}}),")
    j = jsontools.load(sub)
    
    for genero in j:
        #https://allcalidad.re/api/rest/listing?tax=genres&term=familia&page=1&post_type=movies%2Ctvshows%2Canimes&posts_per_page=16
        url = host + "api/rest/listing?tax=genres&term=" + j[genero]["slug"] + "&post_type=movies%2Ctvshows%2Canimes&posts_per_page=16"
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = j[genero]["name"],
                             url = url + "&page=",
                             pagina = 1,
                             ))
    #return itemlist[::-1] //orden inverso
    return itemlist


def peliculas(item):
    logger.info()
    
    itemlist = []

    item.busca = ""
    data = httptools.downloadpage(item.url + "%s" %item.pagina, encoding=encoding, canonical=canonical).json["data"]["posts"]
    
    for pelis in data:
        url = host + "peliculas/" + pelis["slug"]
        idioma = "Latino"
        mtitulo = pelis["title"] + " (" + idioma + ")"
        item.infoLabels['year'] = "-"
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitulo,
                                   contentTitle = pelis["original_title"],
                                   thumbnail = "",
                                   url = url,
                                   contentType="movie",
                                   language = idioma,
                                   _id = pelis["_id"],
                                   ))
    
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    #url_pagina = scrapertools.find_single_match(data, 'class="page larger" href="([^"]+)')
    #if url_pagina != "":
    paginax = "Pagina: %s" %(item.pagina + 1)
    itemlist.append(Item(channel = item.channel, action = "peliculas", title = paginax, url = item.url, pagina = item.pagina + 1,
                        extra=item.extra,
                        busca=item.busca,
))
    
    return itemlist


def findvideos(item):
    logger.info()
    
    itemlist = []
    encontrado = []
    
    data = httptools.downloadpage(host + "api/rest/player?post_id=%s&_any=1" %item._id, encoding=encoding, forced_proxy_opt=forced_proxy_opt, canonical=canonical).json["data"]["embeds"]
    
    for servidores in data:
        itemlist.append(Item(
                        channel=item.channel,
                        contentTitle=item.contentTitle,
                        contentThumbnail=item.thumbnail,
                        infoLabels=item.infoLabels,
                        language="Latino",
                        title='%s', action="play",
                        url=servidores["url"]
                       ))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist and item.contentChannel != "videolibrary":
        itemlist.append(Item(channel=item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))

        # Opción "Añadir esta película a la videoteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                 ))
    return itemlist


def play(item):
    
    item.thumbnail = item.contentThumbnail
    
    return [item]
