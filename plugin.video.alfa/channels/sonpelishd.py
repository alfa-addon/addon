# -*- coding: utf-8 -*-
# -*- Channel SonPelisHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://sonpelishd.com/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Peliculas",
                               action="menu_peliculas",
                               thumbnail=get_thumb('movies', auto=True),
                               ))

    # itemlist.append(item.clone(title="Series",
    #                            action="menu_series",
    #                            thumbnail=get_thumb('tvshows', auto=True),
    #                            ))

    itemlist.append(item.clone(title="Buscar", action="search",
                               thumbnail=get_thumb('search', auto=True),
                               url=host + '?s='
                               ))

    return itemlist


def menu_peliculas(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=host + 'page/1/?s'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('genres', auto=True),
                               seccion='generos-pelicula'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='fecha-estreno'
                               ))

    itemlist.append(item.clone(title="Calidad",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('quality', auto=True),
                               seccion='calidad'
                               ))

    return itemlist


def menu_series(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="list_all", thumbnail=get_thumb('all', auto=True),
                               url=host + 'series/page/1/',
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'series/page/1/',
                               thumbnail=get_thumb('genres', auto=True),
                               seccion='generos-serie'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'series/page/1/',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='series-lanzamiento'
                               ))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'class=item.*?<a href=(.*?)><div class=image.*?src=(.*?) alt=(.*?) (?:\(\d{4}|width).*?'
    patron += 'fixyear><h2>(.*?)<\/h2>.*?calidad2>(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedquality in matches:
        url = scrapedurl
        action = 'findvideos'
        thumbnail = scrapedthumbnail
        plot = ''
        contentSerieName = ''
        contentTitle = scrapedtitle
        title = contentTitle
        quality = scrapedquality
        if scrapedquality != '':
            title = contentTitle + ' (%s)' % quality

        year = scrapedyear

        if 'series' in item.url or 'series' in url:
            action = 'seasons'
            contentSerieName = contentTitle
            quality = ''
        new_item = Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             plot=plot,
                             quality=quality,
                             infoLabels={'year': year}
                             )
        if 'series' not in item.url:
            new_item.contentTitle = contentTitle
        else:
            new_item.contentSerieName = contentSerieName
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data,
                                                   '<div class=pag_b><a href=(.*?)>Siguiente</a>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_all",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.seccion == 'generos-pelicula':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?)>(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion == 'generos-serie':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?\/series-genero\/.*?)>(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion in ['fecha-estreno', 'series-lanzamiento']:
        patron = '<li><a href=https://sonpelishd.com/fecha-estreno(.*?)>(.*?)<\/a>'
    elif item.seccion == 'calidad':
        patron = '<li><a href=https://sonpelishd.com/calidad(.*?)>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        thumbnail = ''
        if 'generos' in item.seccion:
            cantidad = re.sub(r'.*?<\/a> <span>', '', scrapedtitle)
            title = re.sub(r'<\/a> <span>|\d|\.', '', scrapedtitle)
            url = scrapedurl
            title = scrapertools.decodeHtmlentities(title)
            title = title + ' (%s)' % cantidad
        elif item.seccion in ['series-lanzamiento', 'fecha-estreno', 'calidad']:
            title = scrapedtitle
            url = 'https://sonpelishd.com/%s%s' % (item.seccion, scrapedurl)

        itemlist.append(item.clone(action='list_all',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail
                                   ))
    return itemlist


def seasons(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<span class=title>.*?- Temporada (.*?)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for temporada in matches:
        title = 'Temporada %s' % temporada
        contentSeasonNumber = temporada
        item.infoLabels['season'] = contentSeasonNumber
        itemlist.append(item.clone(action='episodiosxtemp',
                                   title=title,
                                   contentSeasonNumber=contentSeasonNumber
                                   ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             contentSeasonNumber=contentSeasonNumber
                             ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    patron = '<li><div class=numerando>(\d+).*?x.*?(\d+)<\/div>.*?<a href=(.*?)> (.*?)<\/a>.*?<\/i>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtemp, scrapedep, scrapedurl, scrapedtitle in matches:
        temporada = scrapedtemp
        title = temporada + 'x%s %s' % (scrapedep, scrapedtitle)
        url = scrapedurl
        contentEpisodeNumber = scrapedep
        item.infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   ))
    return itemlist


def episodiosxtemp(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    temporada = item.contentSeasonNumber
    patron = '<li><div class=numerando>%s.*?x.*?(\d+)<\/div>.*?<a href=(.*?)> (.*?)<\/a>.*?<\/i>' % temporada
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedep, scrapedurl, scrapedtitle in matches:
        title = temporada + 'x%s %s' % (scrapedep, scrapedtitle)
        url = scrapedurl
        contentEpisodeNumber = scrapedep
        item.infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    url_list = []
    itemlist = []
    duplicados = []
    data = get_source(item.url)
    src = data
    patron = '<iframe src=(.*?) scrolling'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
            lang = 'LAT'
            quality = item.quality
            title = '[%s] [%s]'
            if url != '':
                itemlist.append(item.clone(title=title, url=url, action='play', language=lang))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server, i.language))

    if item.infoLabels['mediatype'] == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle
                                 ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
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
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'page/1/?s'

        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'

        elif categoria == 'terror':
            item.url = host + 'category/terror/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data
