# -*- coding: utf-8 -*-

import sys, base64
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from channelselector import get_thumb
from modules import autoplay
from channels import filtertools
from core import httptools
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
    
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host + "/movies/page/", extra="", pagina = 1, thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos_years", url = host, extra = "menu-item-object-category", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "generos_years", url = host, extra = "menu-item-object-release-year", thumbnail = get_thumb("year", auto = True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host, pagina=1, thumbnail = get_thumb("search", auto = True)))
    
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
    item.url = host + "page/"
    item.busca = "?s=%s" %texto
    item.pagina = 1
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos_years(item):
    logger.info()
    
    itemlist = []
    
    data = httptools.downloadpage(item.url, encoding=encoding, canonical=canonical).data
    patron  = '(?ims)%s.*?' %item.extra
    patron += 'href="([^"]+)'
    patron += '">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for url, titulo in matches:
        if not url.startswith("http"): url = host + url
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url + "/page/",
                             pagina = 1,
                             ))
    return itemlist[::-1]


def peliculas(item):
    logger.info()
    
    itemlist = []
    if item.extra == "busca":
        data = httptools.downloadpage(item.url + "%s%s" %(item.pagina, item.busca), encoding=encoding, canonical=canonical).data
    else:
        item.busca = ""
        data = httptools.downloadpage(item.url + "%s" %item.pagina, encoding=encoding, canonical=canonical).data
    patron  = '(?ims)data-movie-id=.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'oldtitle="([^"]+)".*?'
    patron += 'jt-info">(\w+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for url, titulo, annio in matches:
        if "Premium" in titulo or "Suscripci" in titulo:
            continue
        idioma = "Latino"
        mtitulo = titulo + " (" + idioma + ")"
        item.infoLabels['year'] = annio
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitulo,
                                   contentTitle = titulo,
                                   thumbnail = "",
                                   url = url,
                                   contentType="movie",
                                   language = idioma
                                   ))
    
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    url_pagina = scrapertools.find_single_match(data, 'class="page larger" href="([^"]+)')
    if url_pagina != "":
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
    
    data = httptools.downloadpage(item.url, encoding=encoding, forced_proxy_opt=forced_proxy_opt, canonical=canonical).data
    patron  = 'data-url="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for url in matches:
        # data = httptools.downloadpage(url, canonical=canonical).data
        # patron = "var url = '([^']+)'"
        # url = scrapertools.find_single_match(data, patron)
        
        itemlist.append(Item(
                        channel=item.channel,
                        contentTitle=item.contentTitle,
                        contentThumbnail=item.thumbnail,
                        infoLabels=item.infoLabels,
                        language="Latino",
                        title='%s', action="play",
                        url=url
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


def clear_url(url):
    
    if PY3 and isinstance(url, bytes):
        url = "".join(chr(x) for x in bytes(url))
    url = url.replace("fembed.com/v","fembed.com/f").replace("mega.nz/embed/","mega.nz/file/").replace("streamtape.com/e/","streamtape.com/v/").replace("v2.zplayer.live/download","v2.zplayer.live/embed")
    if "streamtape" in url:
        url = scrapertools.find_single_match(url, '(https://streamtape.com/v/\w+)')
    
    return url


def play(item):
    
    item.thumbnail = item.contentThumbnail
    
    return [item]
