# -*- coding: utf-8 -*-
# -*- Channel RetroSeriesTV -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


host = 'https://retroseriestv.com/'

# IDIOMAS = {'la': 'LAT', 'es': 'Cast'}
# list_language = IDIOMAS.values()
# list_quality = []
# list_servers = ['openload']


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host + 'seriestv/', thumbnail=get_thumb('all',
                                                                                                         auto=True)))

    itemlist.append(item.clone(title="Generos", action="section", url=host, thumbnail=get_thumb('genres', auto=True),
                               section='genres'))

    itemlist.append(item.clone(title="Por Año", action="section", url=host, thumbnail=get_thumb('year', auto=True),
                               section='year'))

    itemlist.append(item.clone(title="Alfabetico", action="section", url=host, thumbnail=get_thumb('alphabet', auto=True),
                               section='abc'))

    itemlist.append(item.clone(title="Buscar", action="search", url=host+'?s=',
                               thumbnail=get_thumb('search', auto=True)))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<article id=post-.*?<a href=(.*?)><img src=(.*?) alt=(.*?)><.*?<span>(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:

        url = scrapedurl
        contentSerieName = scrapedtitle
        thumbnail = scrapedthumbnail
        itemlist.append(item.clone(action='seasons',
                                   title=contentSerieName,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentSerieName=contentSerieName,
                                   infoLabels={'year':year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'rel=next.*?href=(.*?) ')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))
    return itemlist

def section(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '<ul class=%s(.*?)</ul>' % item.section)
    patron = '<a href=(.*?)>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl.strip()
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=url, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<span class=title>Temporada(\d+) <'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle in matches:
        infoLabels = item.infoLabels
        infoLabels['season'] = scrapedtitle
        title = 'Temporada %s' % scrapedtitle
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist

def episodesxseason(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    infoLabels = item.infoLabels
    season = infoLabels['season']
    patron = '<img src=([^>]+)></a></div><div class=numerando>%s - (\d+)</div>' % season
    patron += '<div class=episodiotitle><a href=(.*?)>(.*?)</a><'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedepi, scrapedurl, scrapedtitle in matches:

        title = '%sx%s - %s' % (season, scrapedepi, scrapedtitle)
        infoLabels['episode'] = scrapedepi
        if scrapedepi > 0:
            itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action='findvideos',
                            infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = 'id=([^ ]+) class=play-box-iframe .*?src=(.*?) frameborder=0.*?'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, scrapedurl in matches:
        #language = scrapertools.find_single_match(data, '#%s.*?dt_flag><img src=.*?flags/(.*?).png' % option)
        #title = '%s [%s]'
        language = ''
        title = '%s'
        SerieName = item.contentSerieName
        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=SerieName, url=scrapedurl,
                             action='play', language=language, infoLabels=item.infoLabels))

    #itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server.capitalize(), i.language))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

def search_results(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article.*?<a href=(.*?)><img src=(.*?) alt=(.*?)><.*?year>(.*?)<.*?<p>(.*?)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, scrapedplot in matches:

        url = scrapedurl
        contentSerieName = scrapedtitle.replace(' /','')
        thumbnail = scrapedthumbnail
        itemlist.append(item.clone(action='seasons',
                                   title=contentSerieName,
                                   url=url,
                                   thumbnail=thumbnail,
                                   plot=scrapedplot,
                                   contentSerieName=contentSerieName,
                                   infoLabels={'year':year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return search_results(item)
    else:
        return []
