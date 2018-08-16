# -*- coding: utf-8 -*-
# -*- Channel SeriesAnimadas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import base64

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from lib import jsunpack
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'latino': 'LAT', 'subtitulado':'VOSE'}
list_language = IDIOMAS.values()

list_quality = []

list_servers = [
    'directo',
    'openload',
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'seriesanimadas')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'seriesanimadas')

host = 'https://www.seriesanimadas.net/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Nuevos Capitulos', url=host, action='new_episodes', type='tvshows',
                         thumbnail=get_thumb('new_episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'series?', action='list_all', type='tvshows',
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'series?', action='list_all', type='tvshows',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + 'search?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = '<article class=".*?">.*?<a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)">.*?'
    patron +='<span class="year">(\d{4})</span>.*?<span class="(?:animes|tvs)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, scrapedtype in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        url = scrapedurl
        if scrapedtype == 'Anime':
            action = 'episodesxseasons'
        elif scrapedtype == 'Serie':
            action = 'seasons'

        new_item = Item(channel=item.channel,
                        action=action,
                        title=title,
                        url=url,
                        contentSerieName=scrapedtitle,
                        thumbnail=thumbnail,
                        type=scrapedtype,
                        infoLabels={'year':year})

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'li><a href="([^"]+)" rel="next">&raquo;</a>')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='<li class="gridseason"><a href="([^"]+)"><span class="title">Temporada (\d+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
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

    data=get_source(item.url)
    patron='<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    if item.type == 'Anime':
        season = '1'
    else:
        season = item.infoLabels['season']
    episode = len(matches)
    for scrapedurl, scrapedtitle in matches:
        infoLabels['episode'] = episode
        url = scrapedurl
        title = scrapedtitle.replace(' online', '')
        title = '%sx%s - %s' % (season, episode, title)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))
        episode -= 1
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist[::-1]

def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article class="contenedor">.*?<a href="([^"]+)" title=".*?">.*?data-src="([^"]+)" alt="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumb,
                             action='findvideos'))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = 'video\[\d+\] = .*?src="([^"]+)".*?;'
    matches = re.compile(patron, re.DOTALL).findall(data)
    option = 1
    for scrapedurl in matches:
        lang = scrapertools.find_single_match(data, '"#option%s">([^<]+)<' % str(option)).strip()
        lang = lang.lower()
        if lang not in IDIOMAS:
            lang = 'subtitulado'
        quality = ''
        title = '%s %s'

        if 'redirector' in scrapedurl:
            url_data = httptools.downloadpage(scrapedurl).data
            url = scrapertools.find_single_match(url_data,'window.location.href = "([^"]+)";')
        else:
            url = scrapedurl
        if url != '':
            itemlist.append(
                Item(channel=item.channel, url=url, title=title, action='play', quality=quality,
                     language=IDIOMAS[lang], infoLabels=item.infoLabels))
            option += 1
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
         itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)

    patron = '<div class="search-results__img"><a href="([^"]+)" title=".*?"><img src="([^"]+)".*?'
    patron += '<h2>([^<]+)</h2></a><div class="description">([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle, scrapedplot in matches:

        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb
        plot = scrapedplot
        new_item=Item(channel=item.channel, title=title, url=url, contentSerieName=title, thumbnail=thumbnail,
                      plot=plot, action='seasons')
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'movies/'
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        item.type='movies'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
