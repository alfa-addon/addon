# -*- coding: utf-8 -*-
# -*- Channel Stream Gratis -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from lib.AlfaChannelHelper import dict
from lib.AlfaChannelHelper import DictionaryAllChannel
from lib.AlfaChannelHelper import traceback, base64
from lib.AlfaChannelHelper import Item, get_thumb, config, logger, autoplay

IDIOMAS = AlfaChannelHelper.IDIOMAS_ANIME
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['okru']
forced_proxy_opt = ''

canonical = {
             'channel': 'cinemundo', 
             'host': config.get_setting("current_host", 'cinemundo', default=''), 
             'host_alt': ['https://www.cinemundo.com.ar/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'list_page.php'
tv_path = ''
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['div'], 'id': ['pills-one-example1']}]), 
                       ('find_all', [{'tag': ['a'], 'class': ['d-inline-block position-relative stretched-link']}])]), 
         'categories': dict([('find_all', [{'tag': ['ul'], 'class': ['list-unstyled h-bg-1-dark'], '@POS': [0], '@DO_SOUP': True},
                             {'tag': ['span']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\?pagina=\d+', '?pagina=%s']],
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}]),
                            ('find_all', [{'tag': ['a'], 'class': ['page-link'], '@POS': [-1]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
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
         'findvideos': {'find_all': [{'tag': ['iframe']}]},
         'title_clean': [],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 25, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'IDIOMAS_TMDB': {0: 'es', 1: 'ja', 2: 'es'}, 'join_dup_episodes': False, 'season_TMDB_limit': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Películas', url=host + movie_path, action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='movies'))

    # consultas_page.php es una página que tiene menos contenido que las demas, pero sirve para hacer búsquedas por género y año
    # por lo que hace menos consultas a la base de datos, carga más rápido y es más liviana para el servidor
    itemlist.append(Item(channel=item.channel, title='Películas por Género',  action='section', url=host + 'consultas_page.php', 
                         thumbnail=get_thumb('genres', auto=True), extra='generos', c_type='movies'))

    itemlist.append(Item(channel=item.channel, title='Películas por Año',  action='section', url=host + 'consultas_page.php', 
                         thumbnail=get_thumb('year', auto=True), extra='year', c_type='movies'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()

    if item.extra == 'year':
        findS['categories'] = dict([('find_all', [{'tag': ['ul'], 'class': ['list-unstyled h-bg-1-dark'], '@POS': [1], '@DO_SOUP': True},
                                    {'tag': ['span']}])])
 
    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def make_search_url(texto):
    texto = base64.b64encode(str(texto).encode('utf8')).decode('utf8')
    return "{}find_page.php?str={}".format(host, texto)


def make_url(url):
    # single.php?ID=IWlogP7zRa6BN4udxGjv
    if 'single.php?ID=' in url:
        url = url.replace('single.php?ID=', 'video_maximizado.php?id_post=')
    if not url.startswith('http'):
        url = host + url
    return url


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int:
        elem_json = {}
        elem_json['title'] = elem.get_text(strip=True)
        elem_json['url'] = make_search_url(elem_json['title'])
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
            elem_json['title'] = elem.img.get('alt', '').strip()
            elem_json['url'] = make_url(elem.get('href', ''))
            elem_json['thumbnail'] = elem.img.get("src", "")
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
            elem_json['url'] = elem.get("src", "")
            elem_json['title'] = '%s'

            if not elem_json.get('url'): continue
            matches.append(elem_json.copy())

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

    return matches, langs


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    try:
        item.url = make_search_url(texto)

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []