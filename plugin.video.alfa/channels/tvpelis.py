# -*- coding: utf-8 -*-
# -*- Channel TvPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://www.tvpelis.tv/'

IDIOMAS = {'Latino': 'LAT', 'latino': 'LAT', 'Español':'CAST', 'castellano': 'CAST', 'Vose':'VOSE', 'vose':'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['xdrive', 'bitertv', 'okru']

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    logger.debug(data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Películas", action="movies_menu",
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", url=host+'genero/series/',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Documentales", action="list_all", url=host + 'genero/documentales/',
                         thumbnail=get_thumb('documental', auto=True)))

    # itemlist.append(Item(channel=item.channel, title="Latino", action="list_all", url=host + 'genero/latino/',
    #                      thumbnail=get_thumb('lat', auto=True)))
    #
    # itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all", url=host + 'genero/vose/',
    #                      thumbnail=get_thumb('vose', auto=True)))
    #
    # itemlist.append(Item(channel=item.channel, title="Generos", action="section",
    #                      thumbnail=get_thumb('genres', auto=True)))
    #
    # itemlist.append(Item(channel=item.channel, title="Por Años", action="section",
    #                      thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Buscar', action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def movies_menu(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host,
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all", url=host + 'genero/castellano/',
                         thumbnail=get_thumb('cast', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all", url=host + 'genero/latino/',
                         thumbnail=get_thumb('lat', auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all", url=host + 'genero/vose/',
                         thumbnail=get_thumb('vose', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Hindú", action="list_all", url=host + 'genero/hindu/',
                         thumbnail=get_thumb('hindu', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section",
                         thumbnail=get_thumb('year', auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data,
                                          "<div id='z1'><section><div id='main'><div class='breadcrumbs'>(.*?)</ul>")
    logger.debug(data)
    patron = 'article id=.*?<a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'class="selectidioma">(.*?)class="fixyear".*?class="genero">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, lang_data, type in matches:
        url = scrapedurl
        lang = get_language(lang_data)

        year = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
        scrapedtitle = scrapertools.find_single_match(scrapedtitle, '([^\(]+)\(?').strip()
        #scrapedtitle = scrapedtitle.replace('Latino','')
        scrapedtitle = re.sub('latino|español|sub|audio','', scrapedtitle.lower()).capitalize()
        if not config.get_setting('unify'):
            title = '%s %s' % (scrapedtitle, lang)
        else:
            title = scrapedtitle

        thumbnail = 'https:'+scrapedthumbnail

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail,  language = lang,
                        infoLabels={'year':year})

        logger.debug(type)
        if 'series' not in type.lower():
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
        else:
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'seasons'
        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion

    if itemlist != []:

        next_page = scrapertools.find_single_match(full_data, '<link rel="next" href="([^"]+)"')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>', url=next_page))

    return itemlist



def section(item):
    logger.info()

    itemlist = []
    data=get_source(host)
    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, '<h2>Categorias de Peliculas</h2>(.*?)</ul>')
        patron = 'href="([^"]+)"> <em>Peliculas de </em>([^<]+)<span>'

    if item.title == 'Por Años':
        data = scrapertools.find_single_match(data, '>Filtrar por A&ntilde;o</option>(.*?)</select>')
        patron = 'value="([^"]+)">Peliculas del A&ntilde;o (\d{4})<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel, title=title.strip(), url=url, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()
    itemlist=[]
    all_seasons = []
    data=get_source(item.url)
    patron='Temporada \d+'
    matches = re.compile(patron, re.DOTALL).findall(data)
    action = 'episodesxseasons'
    if len(matches) == 0:
        matches.append('1')
        action = 'aios'
    infoLabels = item.infoLabels

    for season in matches:
        season = season.lower().replace('temporada','')
        infoLabels['season']=season
        title = 'Temporada %s' % season
        if title not in all_seasons:
            itemlist.append(Item(channel=item.channel, title=title, url=item.url, action=action,
                                 infoLabels=infoLabels))
            all_seasons.append(title)
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


def aios(item):
    logger.info()

    itemlist = []

    data=get_source(item.url)
    patron='href="([^"]+)" rel="bookmark"><i class="fa icon-chevron-sign-right"></i>.*?Capitulo (?:00|)(\d+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedurl, scrapedepisode in matches:

        infoLabels['episode'] = scrapedepisode
        url = item.url+scrapedurl
        title = '%sx%s - Episodio %s' % (infoLabels['season'], infoLabels['episode'], infoLabels['episode'])

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', type=item.type,
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist




def episodesxseasons(item):
    logger.info()

    itemlist = []

    data=get_source(item.url)
    patron='<a href="([^"]+)".*?</i>.*?Temporada %s, Episodio (\d+) - ([^<]+)<' % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedurl, scrapedepisode, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', type=item.type,
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def get_language(lang_data):
    logger.info()
    language = []

    lang_list = scrapertools.find_multiple_matches(lang_data, '<em class="bandera sp([^"]+)"')
    for lang in lang_list:
        if not lang in IDIOMAS:
            lang = 'vose'
        lang = IDIOMAS[lang]
        if lang not in language:
            language.append(lang)
    return language

def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<div id="([^"]+)".?class="tab_part.*?">.?<iframe src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) == 0:
        patron = 'class="(rep)".*?src="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for option, player in matches:

        if 'ok.ru' in player:
            url = 'http:' + player
        elif 'rutube' in player:
            url = 'http:' + player + "|%s" % item.url
        elif 'http' not in player:
                hidden_data = get_source('%s%s' % (host, player))
                url = scrapertools.find_single_match(hidden_data, '<iframe src="([^"]+)"')
        else:
            url = player

        lang = scrapertools.find_single_match(data, '<li rel="%s">([^<]+)</li>' % option)
        if lang.lower() in  ['online', 'trailer']:
            continue
        if lang in IDIOMAS:
            lang = IDIOMAS[lang]

        if not config.get_setting('unify'):
            title = ' [%s]' % lang
        else:
            title = ''

        if url != '':
            itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', language=lang,
                                 infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url, action="add_pelicula_to_library", extra="findvideos",
                                 contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
        elif categoria == 'latino':
            item.url = host + 'filter?language=2'

        elif categoria == 'castellano':
            item.url = host + 'filter?language=1'

        elif categoria == 'infantiles':
            item.url = host + 'genre/25/infantil'
        elif categoria == 'terror':
            item.url = host + 'genre/15/terror'
        item.pages=3
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

