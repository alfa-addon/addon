# -*- coding: utf-8 -*-
# -*- Channel Flizz Movies -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from lib.AlfaChannelHelper import dict
from lib.AlfaChannelHelper import DictionaryAllChannel
from lib.AlfaChannelHelper import traceback, base64, re
from lib.AlfaChannelHelper import Item, get_thumb, config, logger, autoplay, servertools

SERVERS = {'vidhide': 'vidhidepro', 'turboviplay': 'emturbovid', 
           'abyss': '', 'krakenfiles': '', 'flizzmovies' : '', 'dood': 'doodstream'}
IDIOMAS = {'audio latino': 'LAT', 'audiolatino': 'LAT', 'castellano': 'CAST', 'subtitulada': 'VOSE'}
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['vidguard', 'vidhidepro', 'streamwish', 'emturbovid']
forced_proxy_opt = ''

canonical = {
             'channel': 'flizzmovies', 
             'host': config.get_setting("current_host", 'flizzmovies', default=''), 
             'host_alt': ['https://flizzmovies.org/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'peliculas/page/1'
tv_path = ''
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['container_cards']}]), 
                       ('find_all', [{'tag': ['a']}])]), 
         'categories': dict([('find_all', [{'tag': ['ul'], 'class': ['cnt'], '@POS': [0], '@DO_SOUP': True},
                             {'tag': ['a']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['/\d+$', '/%s']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a','div'], 'class': ['link', 'link current'], '@POS': [-3], '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {},
         'season_num': {},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': '', 
         'episode_url': '', 
         'episodes': {}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['div'], 'class': ['options no_select']}]), 
                             ('find_all', [{'tag': ['a'], 'class': ['reportbtn']}])]),
         'title_clean': [],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'IDIOMAS_TMDB': {0: 'es', 1: 'ja', 2: 'es'}, 'join_dup_episodes': False, 'season_TMDB_limit': False, 'jump_page': True}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Películas', url=host+movie_path, action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='movies'))

    itemlist.append(Item(channel=item.channel, title='Películas por Género',  action='section', url=host, 
                         thumbnail=get_thumb('genres', auto=True), extra='generos', c_type='movies'))

    itemlist.append(Item(channel=item.channel, title='Películas por Año',  action='section', url=host, 
                         thumbnail=get_thumb('year', auto=True), extra='year', c_type='movies'))
    
    itemlist.append(Item(channel=item.channel, title='Películas por Idioma',  action='section', url=host, 
                         thumbnail=get_thumb('language', auto=True), extra='language', c_type='movies'))
    
    itemlist.append(Item(channel=item.channel, title='Películas por Calidad',  action='section', url=host, 
                         thumbnail=get_thumb('quality', auto=True), extra='quality', c_type='movies'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()

    if item.extra == 'year':
        findS['categories'] = dict([('find_all', [{'tag': ['ul'], 'class': ['cnt'], '@POS': [1], '@DO_SOUP': True},
                                    {'tag': ['a']}])])
    elif item.extra == 'language':
        findS['categories'] = dict([('find_all', [{'tag': ['a'], 'class': ['lang']}])])
    elif item.extra == 'quality':
        findS['categories'] = dict([('find_all', [{'tag': ['ul'], 'class': ['qualcnt'], '@POS': [0], '@DO_SOUP': True},
                                    {'tag': ['a']}])])
 
    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int:
        elem_json = {}
        if item.extra == 'quality':
            elem_json['title'] = elem.get_text().strip()
        elif item.extra == 'language':
            elem_json['title'] = elem.img['alt'].strip()
            elem_json['title'] = IDIOMAS.get(elem_json['title'], elem_json['title'])
            elem_json['thumbnail'] = get_thumb(elem_json['title'], auto=True)
        else:
            elem_json['title'] = elem.li.div.find(string=True, recursive=False).strip()
        elem_json['url'] = elem.get('href', '')
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:

            elem_json['mediatype'] = 'movie'
            elem_json['title'] = elem.find('div', class_="card_title").p.find(string=True, recursive=False).strip()
            elem_json['url'] = elem.get('href', '')
            if item.c_type == 'search':
                elem_json['thumbnail'] = elem.find('img').get("src", "")
            else:
                elem_json['thumbnail'] = elem.find('img', class_="load").get("data-src", "")
            elem_json['year'] = '-'
            elem_json['context'] = autoplay.context

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                             verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()
    matches = []

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            # <a class="reportbtn" data-id="117727" data-type="Reproductor" data-lang="Audio Latino" data-num="1" data-server="abyss">
            elem_json['server'] = elem.get('data-server', '')
            elem_json['server'] = SERVERS.get(elem_json['server'], elem_json['server'])
            if not elem_json['server']: continue
            elem_json['language'] = elem.get('data-lang', '').lower()
            elem_json['language'] = IDIOMAS.get(elem_json['language'], elem_json['language'])
            elem_json['url'] = item.url + '?id=' + elem.get('data-id', '') + '&num=' + elem.get('data-num', '')
            elem_json['title'] = '%s'

            if not elem_json.get('url'): continue
            matches.append(elem_json.copy())

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

    return matches, langs


def play(item):
    logger.info()
    itemlist = []
    video_data = re.search(r'\?id\=(\d+)\&num\=(\d+)', item.url)
    if video_data:
        item.url = item.url.replace(video_data.group(0), '')
        id = video_data.group(1)
        num = video_data.group(2)
        kwargs['soup'] = False
        kwargs['post'] = {'idF': id, 'ajax': num}
        try:
            data_json = AlfaChannel.create_soup(item.url, **kwargs).json
        except Exception:
            return itemlist
        if data_json and data_json.get('link', ''):
            itemlist.append(item.clone(url=data_json['link']))
    return itemlist


def get_page_num(item):
    logger.info()
    # Llamamos al método que salta al nº de página seleccionado

    return AlfaChannel.get_page_num(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    try:
        if texto:
            item.c_type = 'search'
            item.post = {'s': texto}
            item.url = host
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []