# -*- coding: utf-8 -*-

import sys, base64
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import time
if PY3:
    import urllib.parse as urlparse
else:
    import urlparse
from channelselector import get_thumb
from channels import autoplay
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
list_servers = ['fembed', 'streamtape', 'fastplay', 'gvideo', 'netutv', 'Jawcloud']


__channel__='allcalidad'

host = "https://www1.cuevana3.video"
encoding = None

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Películas:", text_bold = True))
    itemlist.append(Item(channel = item.channel, action="peliculas", title = "     Estrenos", url=host + "/estrenos", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, action="peliculas", title = "     ültimas", url=host + "/peliculas-mas-vistas", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, action="peliculas", title = "     Películas", url=host + "/peliculas", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, action="generos"  , title = "     Por género", url=host, thumbnail=get_thumb('genere', auto=True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host, thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search.html?keyword=" + texto
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def peliculas(item):
    logger.info()
    itemlist = []
    if not item.page: item.page = 1
    if not item.extra: item.url += "?page=%s" %item.page
    data = httptools.downloadpage(item.url, encoding=encoding).data
    patron  = '(?is)TPost C.*?<a href="([^"]+)'
    patron += '.*?data-src="([^"]+)'
    patron += '.*?"Title">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
        item.infoLabels['year'] = "-"
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = scrapedtitle,
                                   contentTitle = scrapedtitle,
                                   thumbnail = "https://" + scrapedthumbnail,
                                   url = host + scrapedurl,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    item.page += 1
    url_pagina = scrapertools.find_single_match(data, 'page=%s' %item.page)
    if url_pagina != "":
        pagina = "Pagina: %s" %item.page
        itemlist.append(Item(channel = item.channel, action = "peliculas", page=item.page, title = pagina, url = item.url))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url, encoding=encoding).data
    bloques = scrapertools.find_multiple_matches(data, '(?is)open_submenu .*?</ul>' )
    for scrapedblock in bloques:
        lang = scrapertools.find_single_match(scrapedblock, 'span>([^<]+)')
        matches = scrapertools.find_multiple_matches(scrapedblock, 'data-video="([^"]+).*?cdtr.*?span>([^<]+)')
        for scrapedurl, scrapedtitle in matches:
            #if  "peliscloud" in scrapedtitle.lower(): continue
            if not scrapedurl.startswith("http"): scrapedurl = "http:" + scrapedurl
            itemlist.append(item.clone(
                            action = "play",
                            language = lang,
                            server = "",
                            title = scrapedtitle,
                            url = scrapedurl
                        ))

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
    logger.info()
    itemlist = []
    item.thumbnail = item.contentThumbnail
    if "damedamehoy" in item.url:
        item.url, id = item.url.split("#")
        new_url = "https://damedamehoy.xyz/details.php?v=%s" % id
        v_data = httptools.downloadpage(new_url).json
        item.url = v_data["file"]
        item.server = "directo"
    if "pelisplus.icu" in item.url:
        data = httptools.downloadpage(item.url).data
        item.url = scrapertools.find_single_match(data, "file: '([^']+)")
        logger.info("Intel22 %s" %item.url)
        if not item.url:
            logger.info("Intel33 %s" %item.url)
            item.url = scrapertools.find_single_match(data, '(?is)<iframe id="embedvideo" src="(https://[^"]+)')
        logger.info("Intel11 %s" %item.url)
    if "peliscloud.net" in item.url:
        dominio = urlparse.urlparse(item.url)[1]
        id = scrapertools.find_single_match(item.url, 'id=(\w+)')
        tiempo = int(time.time())
        item.url = "https://" + dominio + "/playlist/" + id + "/%s.m3u8" %tiempo
        data = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(data, '/hls/\w+/\w+') + "?v=%s" %tiempo
        item.url = "https://" + dominio + url
        data = httptools.downloadpage(url).data
        item.server = "oprem"
        return ([item])
    if item.url:
        itemlist = servertools.get_servers_itemlist([item])
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


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, encoding=encoding).data
    patron = '(?is)menu-item-object-category.*?<a href="([^"]+)'
    patron += '.*?">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, titulo in matches:
        if not url.startswith("http"): url = host + url
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             extra = "generos",
                             title = titulo,
                             url = url
                             ))
    return itemlist
