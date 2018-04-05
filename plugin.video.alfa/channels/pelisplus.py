# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from core import servertools

host = "http://www.pelisplus.tv/"

IDIOMA = {'latino': 'Latino'}
list_language = IDIOMA.values()

list_quality = ['1080p',
                '720p',
                '480p',
                '360p',
                '240p',
                'default'
                ]
list_servers = [
    'gvideo',
    'openload',
    'thevideos'
]


def get_source(url):

    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(
        item.clone(title="Peliculas",
                   action="sub_menu",
                   thumbnail=get_thumb('movies', auto=True),
                   ))

    itemlist.append(
        item.clone(title="Series",
                   action="sub_menu",
                   thumbnail=get_thumb('tvshows', auto=True),
                   ))

    itemlist.append(
            item.clone(title="Buscar", action="search", url=host + 'busqueda/?s=',
                       thumbnail=get_thumb('search', auto=True),
                       ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = []

    content = item.title.lower()
    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               url=host + '%s/ultimas-%s/' % (content, content),
                               thumbnail=get_thumb('all', auto=True),
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               url=host + '%s/' % content,
                               thumbnail=get_thumb('genres', auto=True),
                               ))

    return itemlist


def list_all(item):
    logger.info()

    itemlist=[]

    data = get_source(item.url)
    patron = '(?:</a>|Posters>)<a href=(.*?) class=Posters.*?data-title=(.*?) data.*?src=(.*?) alt'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:

        url = scrapedurl
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        thumbnail = scrapedthumbnail

        filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w154", "")
        filtro_list = {"poster_path": filtro_thumb}
        filtro_list = filtro_list.items()
        new_item=(
            Item(channel=item.channel,
                 action='findvideos',
                 title=title,
                 url=url,
                 thumbnail=thumbnail,
                 infoLabels={'filtro': filtro_list},
                 context=autoplay.context
                 ))
        if 'serie' not in url:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
        else:
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'seasons'
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagination
    if itemlist != []:
        next_page = scrapertools.find_single_match(data, '<li><a href=([^ ]+) rel=next>&raquo;</a>')
        if next_page != '':
            itemlist.append(item.clone(action="list_all",
                                       title='Siguiente >>>',
                                       url=host+next_page,
                                       thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'
                                       ))
    return itemlist


def generos(item):

    logger.info()
    itemlist = []
    data = get_source(item.url)
    if 'series' not in item.url:
        clean_genre = 'PELÍCULAS DE'
    else:
        clean_genre = 'SERIES DE'

    patron = '<h2 class=Heading--carousel> %s(.*?) <a class=Heading-link title=View All href=(.*?)><' % clean_genre
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:

        url = scrapedurl
        title = scrapedtitle
        if 'agregadas' not in title.lower():
            itemlist.append(
                Item(channel=item.channel,
                     action="list_all",
                     title=title,
                     url=url,
                     ))
    return itemlist


def seasons(item):
    logger.info()

    itemlist = []
    templist = []
    data = get_source(item.url)
    serie_id = scrapertools.find_single_match(data, '<div class=owl-carousel data-serieid=(.*?)>')

    patron = 'class=js-season-item> SEASON<span>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for season in matches:
        contentSeasonNumber = season
        infoLabels['season']=season
        itemlist.append(Item(channel=item.channel, action="episodes", title='Temporada %s' % season,
                             serie_id=serie_id, contentSeasonNumber=contentSeasonNumber,
                             serie_url=item.url, infoLabels=infoLabels))

    if item.extra == 'seasons':
        for tempitem in itemlist:
            templist += episodes(tempitem)
    else:
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_serie_to_library",
                 extra="seasons",
                 contentSerieName=item.contentSerieName,
                 contentSeasonNumber=contentSeasonNumber
                 ))
    if item.extra == 'seasons':
        return templist
    else:
        return itemlist


def episodes(item):
    logger.info()

    itemlist= []

    url = host+'api/episodes?titleId=%s&seasonNumber=%s' % (item.serie_id, item.contentSeasonNumber)

    data = jsontools.load(httptools.downloadpage(url).data)
    episode_list = data['titles']
    infoLabels = item.infoLabels
    for episode in episode_list:

        url = item.serie_url+episode['friendlyTitle4Url']
        thumbnail = episode['url_image']
        plot = episode['shortDescription']
        contentEpisodeNumber = episode['tvSeasonEpisodeNumber']
        title = '%sx%s - %s' % (item.contentSeasonNumber, contentEpisodeNumber, episode['title'])
        infoLabels['episode']=contentEpisodeNumber

        itemlist.append(Item(channel=item.channel, action='findvideos', title=title, url=url, thumbnail=thumbnail,
                             plot=plot, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist



def findvideos(item):
    logger.info()

    itemlist = []


    data = get_source(item.url)

    itemlist.extend(servertools.find_video_items(data=data))

    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.language = IDIOMA['latino']
        videoitem.title = '[%s] [%s]' % (videoitem.server, videoitem.language)
        videoitem.infoLabels = item.infoLabels

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url, action="add_pelicula_to_library", extra="findvideos",
                     contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + 'busqueda/?s=' + texto

    try:
        if texto != '':
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + 'peliculas/ultimas-peliculas/'

        elif categoria == 'infantiles':
            item.url = host + 'peliculas/animacion/'

        elif categoria == 'terror':
            item.url = host + 'peliculas/terror/'

        elif categoria == 'documentales':
            item.url = host + 'documentales/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
