# -*- coding: utf-8 -*-
# -*- Channel SeriesAnimadas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'latino': 'LAT', 'audio latino': 'LAT', 'sub español':'VOSE', 'subtitulado':'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'directo',
    'openload',
]

canonical = {
             'channel': 'seriesanimadas', 
             'host': config.get_setting("current_host", 'seriesanimadas', default=''), 
             'host_alt': ["https://ww2.animedesho.com/"], 
             'host_black_list': ["https://animedesho.com/", "https://seriesanimadas.org/"], 
              'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', canonical['channel'])
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', canonical['channel'])


def mainlist(item):
    logger.info()
    
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title='Nuevos Capitulos', url=host + 'home', action='new_episodes', type='tvshows',
                         thumbnail=get_thumb('new_episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'series/estrenos', action='list_all',
                         type='tvshows',
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'series', action='list_all', type='tvshows',
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
    
    data = httptools.downloadpage(url, ignore_response_code=True, canonical=canonical).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    
    return data

def list_all(item):
    logger.info()
    
    itemlist = []

    data = get_source(item.url)
    patron = '<article class=".*?">.*? href="([^"]+)".*?<img src="([^"]+)".*?<h3 class="card-tvshow__title">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapedtitle
        season = scrapertools.find_single_match(title, '(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season')
        if not season:
            season = scrapertools.find_single_match(title, '(?i)season\s*(\d+)')
        title = re.sub('(?i)\s*\d+\s*(?:st|nd|rd|th)\s+season', '', title)
        title = re.sub('(?i)season\s*\d+', '', title)
        
        thumbnail = scrapedthumbnail
        url = scrapedurl
        action = 'seasons'

        new_item = Item(channel=item.channel,
                        action=action,
                        title=title,
                        url=url,
                        contentSerieName=title,
                        thumbnail=thumbnail,
                        contentType='tvshow'
                        )
        if season: new_item.contentSeason = int(season)

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    #  Paginación
    url_next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data = get_source(item.url)
    patron = '<div class="season__title">Temporada (\d+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    if len(matches) == 0:
        item.type = 'Anime'
        return episodesxseasons(item)
    
    infoLabels = item.infoLabels
    
    for season in matches:
        try:
            infoLabels['season'] = int(season)
        except:
            infoLabels['season'] = infoLabels['season'] or 1
        title = 'Temporada %s' % infoLabels['season']
        
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels, contentType='season'))
    
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
    infoLabels = item.infoLabels

    data = get_source(item.url)

    if item.type == 'Anime':
        season = 1
        infoLabels['season'] = infoLabels['season'] or season
        patron = '<a class="episodie-list" href="([^"]+)" .*?</i> Episodio (\d+).*?</span>'
    else:
        season = item.infoLabels['season']
        patron = 'class="episodie-list" href="([^"]+)" title=".*?Temporada %s .*?pisodio (\d+).*?">' % season
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        patron = 'class="episodie-list" href="([^"]+)" title=".*?pisodio (\d+).*?">'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, episode in matches:
        try:
            infoLabels['episode'] = int(episode)
        except:
            infoLabels['episode'] = 1
        
        url = scrapedurl
        title = '%sx%s - Episodio %s' % (season, infoLabels['episode'], episode)

        itemlist.append(Item(channel=item.channel, title= title, url=url,
                             action='findvideos', infoLabels=infoLabels, contentType='episode'))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist[::-1]

def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<div\s*class="card-episodie\s*shadow-sm">\s*<a\s*href="([^"]+)".*?imgsrc="([^"]+)"\s*alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        
        pat = r'^(.*?)\s*(?:Episodio)?\s*(\d+)\s*(.*)'
        ctitle, ep, lang = scrapertools.find_single_match(scrapedtitle, pat)
        season = scrapertools.find_single_match(ctitle, '(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season')
        if not season:
            season = scrapertools.find_single_match(ctitle, '(?i)season\s*(\d+)')
        serie_title = re.sub('(?i)\s*\d+\s*(?:st|nd|rd|th)\s+season', '', ctitle)
        serie_title = re.sub('(?i)season\s*\d+', '', serie_title)
        serie_title = re.sub('(?i)Episodio\s*\d+', '', serie_title)
        title = '%s: %sx%s' % (ctitle, season or 1, str(ep).zfill(2))
        language = IDIOMAS.get(lang.lower(), 'VOSE')

        if not config.get_setting('unify'):
            title += '[COLOR khaki] (%s)[/COLOR]' % language
        
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl,
                             thumbnail=scrapedthumb, contentSerieName=serie_title.strip(),
                             contentType='episode', contentSeason=int(season or 1), contentEpisodeNumber=int(ep or 1), 
                             language=language, action='findvideos'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    return itemlist

def findvideos(item):
    logger.info()
    
    itemlist = []
    
    data = get_source(item.url)
    
    patron = 'video\[(\d+)\] = .*?src="([^"]+)".*?;'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for option, scrapedurl in matches:
        lang = scrapertools.find_single_match(data, '"#option%s">([^<]+)<' % str(option)).strip()
        language = IDIOMAS.get(lang.lower(), 'VOSE')
        
        quality = ''
        title = '%s (%s)'

        if 'redirect' in scrapedurl:
            url_data = httptools.downloadpage(scrapedurl).data
            url = scrapertools.find_single_match(url_data,'var redir = "([^"]+)";')
            if not url:
                url = scrapertools.find_single_match(url_data,'window.location.href = "([^"]+)";')
                
        else:
            url = scrapedurl
        
        if url != '':
            itemlist.append(
                Item(channel=item.channel, url=url, title=title, action='play', quality=quality,
                     language=language, infoLabels=item.infoLabels))

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
        return list_all(item)
    else:
        return []


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
