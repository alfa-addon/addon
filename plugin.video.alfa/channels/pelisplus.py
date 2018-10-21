# -*- coding: utf-8 -*-
# -*- Channel Pelisplus -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib import generictools

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()

list_quality = []

list_servers = [
    'directo',
    'openload',
    'rapidvideo',
    'streamango',
    'vidlox',
    'vidoza'
    ]

host = 'https://www.pelisplus.to/'

def get_source(url, referer=None):
    logger.info()
    if referer == None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="Peliculas",
                         action="sub_menu",
                         thumbnail=get_thumb('movies', auto=True),
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Series",
                         action="sub_menu",
                         thumbnail=get_thumb('tvshows', auto=True),
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Buscar", action="search", url=host + 'search/?s=',
                         thumbnail=get_thumb('search', auto=True),
                         ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()
    itemlist = []

    content = item.title.lower()

    itemlist.append(Item(channel=item.channel,
                         title="Ultimas",
                         action="list_all",
                         url=host + '%s/estrenos' % content,
                         thumbnail=get_thumb('last', auto=True),
                         type=content
                         ))

    itemlist.append(Item(channel=item.channel,title="Todas",
                         action="list_all",
                         url=host + '%s' % content,
                         thumbnail=get_thumb('all', auto=True),
                         type=content
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         type=content
                         ))
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<div class="Posters">(.*?)</(?:ul|a></div>)')
    patron = 'href="([^"]+)".*?src="([^"]+)".*?<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        title = scrapedtitle
        thumbnail = scrapedthumbnail
        filter_thumb = thumbnail.replace("https://image.tmdb.org/t/p/w300", "")
        filter_list = {"poster_path": filter_thumb}
        filter_list = filter_list.items()
        url = scrapedurl

        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels={'filtro':filter_list})

        if item.type == 'peliculas' or 'serie' not in url:
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = scrapedtitle

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    next_page_pattern = '<a class="page-link" href="([^"]+)" data-ci-pagination-page="\d+" rel="next">&gt;</a>'
    url_next_page = scrapertools.find_single_match(full_data, next_page_pattern)
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='data-toggle="tab">TEMPORADA (\d+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
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

    season = item.infoLabels['season']
    data=get_source(item.url)
    season_data = scrapertools.find_single_match(data, 'id="pills-vertical-%s">(.*?)</div>' % season)

    patron='href="([^"]+)".*?block">Capitulo (\d+) - ([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(season_data)

    infoLabels = item.infoLabels

    for scrapedurl, scrapedepisode, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def section(item):
    logger.info()
    itemlist=[]
    data = get_source(host)
    genres_data = scrapertools.find_single_match(data, '>Generos<(.*?)</ul>')
    patron = 'href="\/\w+\/([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(genres_data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = '%s/%s/%s' % (host, item.type, scrapedurl)
        itemlist.append(Item(channel=item.channel, url=url, title=title, action='list_all', type=item.type))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)

    servers_page = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    data = get_source(servers_page)
    patron = '<a href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for enc_url in matches:
        url_data = get_source(enc_url, referer=item.url)
        hidden_url = scrapertools.find_single_match(url_data, '<iframe src="([^"]+)"')
        if 'server' in hidden_url:
            hidden_data = get_source(hidden_url)
            url = scrapertools.find_single_match(hidden_data, '<iframe src="([^"]+)"')

        else:
            url = hidden_url
            if 'pelishd.tv' in url:
                vip_data = httptools.downloadpage(url, headers={'Referer':item.url}, follow_redirects=False).data
                dejuiced = generictools.dejuice(vip_data)
                url = scrapertools.find_single_match(dejuiced, '"file":"([^"]+)"')

        language = 'latino'
        if not config.get_setting('unify'):
            title = ' [%s]' % language.capitalize()
        else:
            title = ''
        itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', language=IDIOMAS[language],
        infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url += texto

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
            item.url = host + 'peliculas/estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/generos/animacion/'
        elif categoria == 'terror':
            item.url = host + 'peliculas/generos/terror/'
        item.type='peliculas'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist