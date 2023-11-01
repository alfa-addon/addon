# -*- coding: utf-8 -*-
# -*- Channel Veronline -*-
# -*- Created for Alfa Addon -*-
# -*- By DieFeM -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = AlfaChannelHelper.IDIOMAS_ANIME
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
# forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'veronline', 
             'host': config.get_setting("current_host", 'veronline', default=''), 
             'host_alt': ['https://www.veronline.cc/'], 
             'host_black_list': [], 
             # 'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/movies"
tv_path = '/series'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['div'], 'id': ['dle-content']}]), 
                       ('find_all', [{'tag': ['div'], 'class': ['shortstory-in']}])]), 
         'categories': dict([('find', [{'tag': ['ul'], 'class': ['genreSeries']}]),
                             ('find_all', [{'tag': ['a']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page-\d+.html', '/page-%s.html']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pages-numbers']}]),
                            ('find_all', [{'tag': ['a'], '@POS': [-1]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'class': ['season-list']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['shortstory-in']}])]),
         'season_num': dict([('find', [{'tag': ['figcaption']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': 'Temporada\s+(\d+)'}])]),
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': host, 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'class': ['episode-list']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['saision_LI2']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['player']}]},
         'title_clean': [],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
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

    itemlist.append(Item(channel=item.channel, title='Nuevos Capítulos', url=host, action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series-online/page-1.html', action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Géneros',  action='section', url=host, 
                         thumbnail=get_thumb('genres', auto=True), extra='generos'))

    itemlist.append(Item(channel=item.channel, title='A-Z, 0-9',  action='section', url=host, 
                         thumbnail=get_thumb('alphabet', auto=True), extra='az'))

    itemlist.append(Item(channel=item.channel, title='Año',  action='section', url=host, 
                         thumbnail=get_thumb('year', auto=True), extra='year'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    
    if item.extra == 'az':
        findS['categories'] = dict([('find_all', [{'tag': ['ul'], 'class': ['Mn19', 'MnAZ'], '@DO_SOUP': True},
                                                  {'tag': ['a']}])])

    if item.extra == 'year':
        findS['categories'] = dict([('find', [{'tag': ['ul'], 'class': ['options']}]),
                                    ('find_all', [{'tag': ['a']}])])
 
    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int:
        # logger.error(elem)
        elem_json = {}
        elem_json['title'] = elem.find(text=True, recursive=False)
        elem_json['url'] = elem.get('href', '')
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['div'], 'class': ['left']}]), 
                              ('find_all', [{'tag': ['a']}])])

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:

            if item.c_type == 'episodios':
                elem_json['title'] = elem.get_text(strip=True)

                elem_json['title'], \
                elem_json['season'], \
                elem_json['episode'] = scrapertools.find_single_match(elem.get_text(strip=True), 
                                                                      '(?i)(.*?)\s+-\s+T\s+(\d+)\s+Capítulo\s+(\d+)')
                
                elem_json['season'] = int(elem_json['season'])
                elem_json['episode'] = int(elem_json['episode'])

                elem_json['url'] = elem.get('href', '')
                elem_json['mediatype'] = 'episode'

                # En episodios permite desde el menú contextual ir a la Serie
                elem_json['go_serie'] = {'url': re.sub('-temporada.*', '.html', elem_json['url'])}
            else:
                elem_json['title'] = elem.find("h4", class_="short-link").a.get_text(strip=True)
                elem_json['url'] = elem.find("h4", class_="short-link").a.get('href', '')
                elem_json['mediatype'] = 'tvshow'
                elem_json['thumbnail'] = elem.find("div", class_="short-images").find("img").get("src", "")

            elem_json['year'] = '-'
            elem_json['quality'] = 'HD'
            elem_json['context'] = autoplay.context

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): continue

        matches.append(elem_json.copy())

    return matches


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item, matches_post=seasons_matches, **kwargs)


def seasons_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int:
        elem_json = {}
        logger.error(elem)
        try:
            elem_json['url'] = elem.find("a").get("href", "")
            elem_json['title'] = elem.find("figcaption").get_text(strip=True)
            elem_json['season'] = int(elem_json['title'].replace('Temporada ','') or 1)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())
        logger.info(matches, True)
    return matches


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item, **AHkwargs):
    logger.info()

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    soup = AHkwargs.get('soup', {})

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            elem_json['url'] = elem.a.get("href", "")
            elem_json['title'] = elem.a.span.get_text(strip=True)
            elem_json['season'] = (item.contentSeason or 1)
            elem_json['episode'] = int(elem_json['title'].replace('Episodio ','') or 1)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()

    kwargs['matches_post_episodes'] = episodesxseason_matches

    itemlist = AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                             verify_links=False, findvideos_proc=True, **kwargs)

    return [i for i in itemlist if "Directo" not in i.title]


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)

        try:
            elem_json['url'] = elem.get('data-url', '')
            if not elem_json['url'].startswith('/streamer/'):
                continue
            elem_json['url'] = elem_json['url'].replace('/streamer/', '')
            elem_json['url'] = base64.b64decode(elem_json['url']).decode("utf-8")
            elem_json['language'] = get_lang_from_str(elem.find("img").get('src', ''))
            elem_json['title'] = '%s'
            elem_json['quality'] = 'HD'

            if not elem_json.get('url'): continue
            matches.append(elem_json.copy())

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

    return matches, langs


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        # https://docs.python.org/2/library/urllib.html#urllib.quote_plus (escapa los caracteres de la busqueda para usarlos en la URL)
        texto = AlfaChannel.do_quote(texto, '', plus=True) 
        item.url = item.url + "recherche?q=" + texto

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


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = canonical['channel']

    try:
        if categoria in ['series']:
            item.url = host
            item.c_type = 'episodios'
            item.extra = "novedades"
            item.action = "list_all"
            itemlist = list_all(item)

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc())
        return []

    return itemlist


def get_lang_from_str(string):

    if 'latino' in string.lower():
        lang = 'Latino'
    elif 'de' in string.lower():
        lang = 'Castellano'
    else:
        lang = 'VOSE'

    return lang