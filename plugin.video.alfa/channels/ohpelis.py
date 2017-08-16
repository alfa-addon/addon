# -*- coding: utf-8 -*-
# -*- Channel OH-PELIS -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.ohpelis.com'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0 Chrome/58.0.3029.110',
    'Referer': host}


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Peliculas",
                   action='movies_menu'
                   ))

    itemlist.append(
        item.clone(title="Series",
                   action='series_menu'
                   ))

    itemlist.append(
        item.clone(title="Buscar",
                   action="search",
                   url='http://www.ohpelis.com/?s=',
                   ))

    return itemlist


def series_menu(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Series",
                   action="list_all",
                   url=host + '/series/',
                   extra='serie'
                   ))

    return itemlist


def movies_menu(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Todas",
                   action="list_all",
                   url=host + '/peliculas/'
                   ))

    itemlist.append(
        item.clone(title="Generos",
                   action="section",
                   url=host, extra='genres'))

    itemlist.append(
        item.clone(title="Por año",
                   action="section",
                   url=host, extra='byyear'
                   ))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data

    patron = '<div class="poster"><a href="(.*?)"><img src="(.*?)" alt="(.*?)"><\/a>.*?<span>(\d{4})<\/span>.*?'
    patron += '<div class="texto">(.*?)<div'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedplot in matches:
        title = scrapedtitle
        plot = scrapedplot
        thumbnail = scrapedthumbnail
        url = scrapedurl
        year = scrapedyear
        new_item = (item.clone(title=title,
                               url=url,
                               thumbnail=thumbnail,
                               plot=plot,
                               infoLabels={'year': year}
                               ))
        if item.extra == 'serie':
            new_item.action = 'seasons'
            new_item.contentSerieName = title
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion
    next_page = scrapertools.find_single_match(data, '<link rel="next" href="(.*?) />')
    if next_page:
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=next_page,
                             thumbnail=get_thumb("next.png")))
    return itemlist


def section(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data

    if item.extra == 'genres':
        patron = '<li class="cat-item cat-item-\d+"><a href="(.*?)" >(.*?)<\/a> <i>\d+<\/i>'
    elif item.extra == 'byyear':
        patron = '<li><a href="(http:\/\/www\.ohpelis\.com\/release.*?)">(.*?)<\/a><\/li>'
    elif item.extra == 'alpha':
        patron = '<li><a href="(http:\/\/www\.ohpelis\.com\/.*?)" >(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = scrapedurl
        itemlist.append(Item(channel=item.channel,
                             action='list_all',
                             title=title,
                             url=url
                             ))

    return itemlist


def search_list(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '><div class="result-item">.*?<a href="(.*?)"><img src="(.*?)" alt="(.*?)" \/><span class="(.*?)".*?'
    patron += '<span class="year">(.*?)<\/span>.*?<p>(.*?)<\/p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtype, scrapedyear, scrapedplot in matches:
        title = scrapedtitle
        plot = scrapedplot
        thumbnail = scrapedthumbnail
        url = scrapedurl
        year = scrapedyear
        new_item = item.clone(action='',
                              title=title,
                              url=url,
                              thumbnail=thumbnail,
                              plot=plot,
                              infoLabels={'year': year})
        if scrapedtype == 'movies':
            new_item.action = 'findvideos'
            new_item.contentTitle = title
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = title

        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return search_list(item)


def seasons(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<span class="se-t(?: "| se-o")>(.*?)<\/span><span class="title">(.*?) <i>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedseason, scrapedtitle in matches:
        title = scrapedtitle
        contentSeasonNumber = scrapedseason
        infoLabels['season'] = scrapedseason
        itemlist.append(item.clone(title=title,
                                   contentSeasonNumber=contentSeasonNumber,
                                   action='episodesxseason',
                                   infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                                   url=item.url,
                                   action="add_serie_to_library",
                                   extra='episodes',
                                   contentSerieName=item.contentSerieName,
                                   ))
    return itemlist


def episodes(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="numerando">(\d+) - (\d+)<\/div><div class="episodiotitle"><a href="(.*?)">(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    num_ep = 1
    for scrapedseason, scrapedepisode, scrapedurl, scrapedtitle in matches:
        season = scrapedseason
        contentEpisodeNumber = num_ep
        url = scrapedurl
        title = '%sx%s - %s' % (season, num_ep, scrapedtitle)
        itemlist.append(item.clone(title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   action='findvideos',
                                   infoLabels=infoLabels
                                   ))
        num_ep += 1
    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    season = item.contentSeasonNumber
    data = httptools.downloadpage(item.url).data
    patron = '<div class="numerando">%s - (\d+)<\/div><div class="episodiotitle"><a href="(.*?)">(.*?)<\/a>' % season
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    num_ep = 1
    for scrapedepisode, scrapedurl, scrapedtitle in matches:
        title = '%sx%s - %s' % (season, num_ep, scrapedtitle)
        url = scrapedurl
        infoLabels['episode'] = num_ep
        itemlist.append(item.clone(title=title,
                                   url=url,
                                   contentEpisodeNumber=num_ep,
                                   action='findvideos',
                                   infoLabels=infoLabels))
        num_ep += 1

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.channel = item.channel
        if videoitem.server != 'youtube':
            videoitem.title = item.title + ' (%s)' % videoitem.server
        else:
            videoitem.title = 'Trailer en %s' % videoitem.server
        videoitem.action = 'play'

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))

    return itemlist


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/release/2017/'

        elif categoria == 'infantiles':
            item.url = host + '/genero/infantil/'

        itemlist = list_all(item)
        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
