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
    itemlist.append(Item(channel = item.channel, action="list_all", title = "     Estrenos", url=host + "/estrenos", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, action="list_all", title = "     Ultimas", url=host + "/peliculas-mas-vistas", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, action="list_all", title = "     Películas", url=host + "/peliculas", thumbnail=get_thumb('movie', auto=True)))
    itemlist.append(Item(channel = item.channel, action="generos"  , title = "     Por género", url=host, thumbnail=get_thumb('genere', auto=True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Series:", text_bold = True))
    itemlist.append(Item(channel = item.channel, action="last_episodes", title = "     Ultimos episodios", url=host + "/serie", thumbnail=get_thumb('tvshow', auto=True)))
    itemlist.append(Item(channel = item.channel, action="last_tvshows",  title = "     Ultimas series", url=host + "/serie", type_tvshow="tabserie-1", thumbnail=get_thumb('tvshow', auto=True)))
    itemlist.append(Item(channel = item.channel, action="last_tvshows",  title = "     Mas vistas", url=host + "/serie", type_tvshow="tabserie-4", thumbnail=get_thumb('tvshow', auto=True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host, thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []
    infoLabels = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Ultimos Episodios.*?</ul>')
    patron  = '(?is)<a href="([^"]+)'
    patron += '.*?src="([^"]+)'
    patron += '.*?"Title">([^<]+)'
    patron += '.*?<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapeddate in matches:
        season, episode = scrapertools.get_season_and_episode(scrapedtitle).split("x")
        infoLabels = {"episode":episode, "season":season}
        contentSerieName = scrapertools.find_single_match(scrapedtitle, '(.*?) \d')
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   infoLabels = infoLabels,
                                   contentSerieName = contentSerieName,
                                   thumbnail = "https://" + scrapedthumbnail,
                                   title = scrapedtitle + " %s" %scrapeddate,
                                   url = host + scrapedurl,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    return itemlist


def last_tvshows(item):
    logger.info()
    itemlist = []
    url = item.url
    if not item.page: item.page = 1
    if not item.extra: url += "?page=%s" %item.page
    data = httptools.downloadpage(url).data
    bloque = scrapertools.find_single_match(data, 'id="%s".*?</ul>' %item.type_tvshow)
    patron  = '(?is)TPost C.*?<a href="([^"]+)'
    patron += '.*?src="([^"]+)'
    patron += '.*?"Title">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        itemlist.append(item.clone(channel = item.channel,
                                   action = "seasons",
                                   contentSerieName = scrapedtitle,
                                   thumbnail = "https://" + scrapedthumbnail,
                                   title = scrapedtitle,
                                   url = host + scrapedurl,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    item.page += 1
    url_pagina = scrapertools.find_single_match(data, 'page=%s' %item.page)
    if url_pagina != "":
        pagina = "Pagina: %s" %item.page
        itemlist.append(Item(channel = item.channel, action = "last_tvshows", page=item.page, title = pagina, type_tvshow = item.type_tvshow, url = item.url))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = []
    infoLabels = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?is)<option value="(\d+).*?>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedid, scrapedtitle in matches:
        infoLabels = {"season": scrapedid}
        itemlist.append(item.clone(channel = item.channel,
                                   action = "episodesxseasons",
                                   id = scrapedid,
                                   infoLabels = infoLabels,
                                   contentSerieName = item.contentSerieName,
                                   season = scrapedid,
                                   title = scrapedtitle,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    itemlist = sorted(itemlist, key=lambda i: i.season)
    if config.get_videolibrary_support() and len(itemlist) > 0 and "serie" in item.url:
        itemlist.append(Item(channel=item.channel, title = ""))
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = []
    infoLabels = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'season-%s.*?</ul>' %item.id)
    patron  = '(?is)<a href="([^"]+)'
    patron += '.*?src="([^"]+)'
    patron += '.*?"Title">([^<]+)'
    patron += '.*?<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapeddate in matches:
        season, episode  = scrapertools.get_season_and_episode(scrapedtitle).split("x")
        infoLabels = {"episode":episode, "season":season}
        contentSerieName = scrapertools.find_single_match(scrapedtitle, '(.*?) \d')
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   episode = episode,
                                   infoLabels = infoLabels,
                                   contentSerieName = contentSerieName,
                                   title = scrapedtitle,
                                   thumbnail = scrapedthumbnail,
                                   url = host + scrapedurl
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    itemlist = sorted(itemlist, key=lambda i: i.episode)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search.html?keyword=" + texto
    item.extra = "busca"
    if texto != '':
        return list_all(item)
    else:
        return []


def list_all(item):
    logger.info()
    itemlist = []
    url = item.url
    if not item.page: item.page = 1
    if not item.extra: url += "?page=%s" %item.page
    data = httptools.downloadpage(url, encoding=encoding).data
    patron  = '(?is)TPost C.*?<a href="([^"]+)'
    patron += '.*?data-src="([^"]+)'
    patron += '.*?"Title">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.entityunescape(scrapedtitle)
        item.infoLabels['year'] = "-"
        if "serie" in scrapedurl:
            itemlist.append(item.clone(channel = item.channel,
                                    action = "seasons",
                                    title = scrapedtitle,
                                    contentSerieName = scrapedtitle,
                                    thumbnail = "https://" + scrapedthumbnail,
                                    url = host + scrapedurl,
                                    ))
        else:
            itemlist.append(item.clone(channel = item.channel,
                                    action = "findvideos",
                                    title = scrapedtitle,
                                    contentType = "movie",
                                    contentTitle = scrapedtitle,
                                    thumbnail = "https://" + scrapedthumbnail,
                                    url = host + scrapedurl,
                                    ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    item.page += 1
    url_pagina = scrapertools.find_single_match(data, 'page=%s' %item.page)
    if url_pagina != "":
        pagina = "Pagina: %s" %item.page
        itemlist.append(Item(channel = item.channel, action = "list_all", page=item.page, title = pagina, url = item.url))

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
    if "hydrax.net" in item.url:
        data = httptools.downloadpage(item.url, headers={"Referer" : item.url}).data
        v = scrapertools.find_single_match(item.url, 'v=(\w+)')
        post = "slug=%s&dataType=mp4"  %v
        data = httptools.downloadpage("https://ping.iamcdn.net/", post = post).data
        data = httptools.downloadpage("https://geoip.redirect-ads.com/?v=%s" %v, headers={"Referer" : item.url}).data
        
    if "damedamehoy" in item.url:
        item.url, id = item.url.split("#")
        new_url = "https://damedamehoy.xyz/details.php?v=%s" % id
        v_data = httptools.downloadpage(new_url).json
        item.url = v_data["file"]
        item.server = "directo"
    if "pelisplus.icu" in item.url:
        data = httptools.downloadpage(item.url).data
        item.url = scrapertools.find_single_match(data, "file: '([^']+)")
        if not item.url:
            item.url = scrapertools.find_single_match(data, '(?is)<iframe id="embedvideo" src="(https://[^"]+)')
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
        itemlist = list_all(item)
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
                             action = "list_all",
                             extra = "generos",
                             title = titulo,
                             url = url
                             ))
    return itemlist
