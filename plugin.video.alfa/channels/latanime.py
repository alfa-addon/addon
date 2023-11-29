# -*- coding: utf-8 -*-
# -*- Channel Latanime -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

from modules import renumbertools

IDIOMAS = {"Castellano": "Castellano", "Latino": "Latino", "Catalán": "Catalán", "VOSE": "VOSE"}
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
#forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'latanime', 
             'host': config.get_setting("current_host", 'latanime', default=''), 
             'host_alt': ['https://latanime.org'], 
             'host_black_list': [], 
             # 'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = '/animes?p=1'
language = []
url_replace = []

season_pattern = '(?i)((?:\s+Season\s+\d{1,2}|' \
                        +'\s+cour\s+\d{1,2}|' \
                        +'\s+Part\s+\d{1,2}|' \
                        +'\s+Movie\s+\d{1,2}|' \
                        +'\s+S\d{1,2}|' \
                        +'\s+\d{1,2}[a-z]{2}\s+Season|' \
                        +'\s+\d{1,2}[a-z]{2}\s+cour|' \
                        +'\s+\d{1,2}[a-z]{2}\s+Season\s+Part\s+\d{1,2}))'
normalize_pattern = '(?i)\s+(?:\(|)(iii|ii|iv' \
                                 +'|2 temporada|3 temporada' \
                                 +'|temporada 0|temporada 1|temporada 2|temporada 3|temporada 4' \
                                 +'|primera temporada|segunda temporada|tercera temporada' \
                                 +'|first season|second season|third season|fourth season)(?:\)|)'
lang_pattern = '(?i)(?:\sLatino|\sCastellano|\s1080p|\sCatal(a|á)n|)(?:\s\+\sOva|)(?:\s-\sCapitulo\s\d+|)'

finds = {'find': dict([('find_all', [{'tag': ['div'], 'class': ['col-md-4 col-lg-3 col-xl-2 col-6 my-3']}])]), 
         'categories': dict([('find_all', [{'tag': ['select'], 'class': ['form-select'], '@POS': [0], '@DO_SOUP': True},
                             {'tag': ['option']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\?p=\d+', '?p=%s']],
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}]),
                            ('find_all', [{'tag': ['a'], 'class': ['page-link'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {}, 
         'season_num': {}, 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find_all', [{'tag': ['div'], 'class': ['cap-layout']}])]),
         'episode_num': [], 
         'episode_clean': [[lang_pattern, ''],[normalize_pattern, ''],[season_pattern, '']], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['a'], 'class': ['play-video']}]},
         'title_clean': [[lang_pattern, ''],[normalize_pattern, ''],[season_pattern, '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 30, 
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

    itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=host, action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))

    itemlist.append(Item(channel=item.channel, title='Últimos Animes', url=host, action='list_all',
                         thumbnail=get_thumb('newest', auto=True), c_type='novedades'))
    
    itemlist.append(Item(channel=item.channel, title='En Emisión', url=host + '/emision?p=1', action='list_all',
                         thumbnail=get_thumb('on air', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Directorio', url=host + tv_path, action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Directorio por Año',  action='section', url=host + tv_path, 
                         thumbnail=get_thumb('year', auto=True), extra='fecha', c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Directorio por Género',  action='section', url=host + tv_path, 
                         thumbnail=get_thumb('genres', auto=True), extra='genero', c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Directorio por Letra',  action='section', url=host + tv_path, 
                         thumbnail=get_thumb('alphabet', auto=True), extra='letra', c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Directorio por Categoria',  action='section', url=host + tv_path, 
                         thumbnail=get_thumb('categories', auto=True), extra='categoria', c_type='series'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()

    if item.extra == 'genero':
        findS['categories'] = dict([('find_all', [{'tag': ['select'], 'class': ['form-select'], '@POS': [1], '@DO_SOUP': True},
                                    {'tag': ['option']}])])
    if item.extra == 'letra':
        findS['categories'] = dict([('find_all', [{'tag': ['select'], 'class': ['form-select'], '@POS': [2], '@DO_SOUP': True},
                                    {'tag': ['option']}])])
    if item.extra == 'categoria':
        findS['categories'] = dict([('find_all', [{'tag': ['select'], 'class': ['form-select'], '@POS': [3], '@DO_SOUP': True},
                                    {'tag': ['option']}])])
    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    for elem in matches_int[1:]:
        # logger.error(elem)
        elem_json = {}
        elem_json['title'] = elem.find(text=True, recursive=False)
        elem_json['url'] = item.url + '&' + item.extra + '=' + elem.get('value', '')
        matches.append(elem_json.copy())

    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find_all', [{'tag': ['div'], 'class': ['col-6 col-md-6 col-lg-3 mb-3']}])])
        findS['controls']['cnt_tot'] = 36

    if item.c_type == 'novedades':
        findS['find'] = dict([('find', [{'tag': ['div'], 'class': ['owl-two']}]), 
                              ('find_all', [{'tag': ['div'], 'class': ['item']}])])
        findS['controls']['cnt_tot'] = 10

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            if item.c_type == 'episodios':
                try:
                    ext = elem.find("h2", class_="mt-2").get_text(strip=True)
                    episode, elem_json['title'] = ext.split(' - ', 1)
                    elem_json['episode'] = int(episode or 1)
                    elem_json['thumbnail'] = elem.find("img").get("data-src", "")
                except Exception as error:
                    # handle the exception
                    logger.error("An exception occurred: {}".format(error))
                    continue
                elem_json['mediatype'] = 'episode'
            else:
                if item.c_type == 'novedades':
                    elem_json['title'] = elem.find("a").get('title', '')
                else:
                    elem_json['title'] = elem.find("h3", class_="my-1").get_text(strip=True)
                info = elem.find("span", class_="opacity-75")
                if info and re.search('(?i)Pel[i|í]cula', info.get_text(strip=True)):
                    elem_json['mediatype'] = 'movie'
                else:
                    elem_json['mediatype'] = 'tvshow'
                    elem_json['thumbnail'] = elem.find("img").get("src", "")

            elem_json['language'] = get_lang_from_str(elem_json['title'])

            elem_json['title'] = normalize_season(elem_json['title'])

            if re.search(season_pattern, elem_json['title']):
                seasonStr = scrapertools.find_single_match(elem_json['title'], season_pattern)
                if seasonStr:
                    elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                              % (AlfaChannel.color_setting.get('movies', 'white'), seasonStr.strip())]
                    if elem_json['mediatype'] in ['tvshow', 'episode']:
                        elem_json['season'] = int(scrapertools.find_single_match(seasonStr, '(\d{1,2})') or 1)

            elem_json['url'] = elem.find("a").get('href', '')

            # En episodios permite desde el menú contextual ir a la Serie
            if item.c_type == 'episodios' and elem_json['url']:
                elem_json['go_serie'] = {'url': re.sub('-episodio-\d+$', '', elem_json['url']).replace('ver', 'anime')}
            
            if elem_json['mediatype'] == 'movie':
                elem_json['action'] = 'seasons'

            elem_json['year'] = '-'
            elem_json['quality'] = 'HD'

            elem_json['context'] = renumbertools.context(item)
            elem_json['context'].extend(autoplay.context)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): continue

        matches.append(elem_json.copy())

    return matches


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item, **kwargs)


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item, **AHkwargs):
    logger.info()

    """ Aquí le decimos a qué función tienen que saltar para las películas de un solo vídeo """
    kwargs['matches_post_get_video_options'] = findvideos
    soup = AHkwargs.get('soup', '')

    return AlfaChannel.episodes(item, data=soup, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    soup = AHkwargs.get('soup', {})
    
    # Asi lee los datos correctos de TMDB
    titleSeason = item.contentSeason
    if matches_int and titleSeason == 1:
        titleSeason = get_title_season(soup)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            elem_json['url'] = elem.find_parent("a").get("href", "")
            elem_json['title'] = elem.get_text(strip=True)
            # logger.error(elem_json['title'])
            episode = int(scrapertools.find_single_match(elem_json['title'], '(\d+)$') or 1)
            elem_json['season'], elem_json['episode'] = renumbertools.numbered_for_trakt(item.channel, 
                                                        item.contentSerieName, titleSeason, episode)

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
            data = elem.get("data-player", "")
            if data:
                elem_json['url'] = base64.b64decode(data).decode('utf-8')
                # logger.error(elem_json['url'])
            if not elem_json.get('url'): continue

            elem_json['title'] = '%s'
            elem_json['language'] = item.language
            elem_json['quality'] = 'HD'

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
        item.url = item.url + "/buscar?p=1&q=" + texto

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
        if categoria in ['anime']:
            item.url = host
            item.c_type = 'episodios'
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
    elif 'castellano' in string.lower():
        lang = 'Castellano'
    elif 'catalán' in string.lower():
        lang = 'Catalán'
    else:
        lang = 'VOSE'

    return lang


# La temporada viene dada en diferentes formatos
# Esta función se encarga de reemplazar los mas raros por formatos mas comunes
def normalize_season(title):
    logger.info()
    if re.search(normalize_pattern, title):
        # logger.info('Title: ' + title, True)
        for f, r in [['iii', 'S3'],['ii', 'S2'],['iv', 'S4'],
                     ['primera temporada', 'S1'],['segunda temporada', 'S2'],['tercera temporada', 'S3'],
                     ['temporada 0', 'S0'],['temporada 1', 'S1'],['temporada 2', 'S2'],['temporada 3', 'S3'],['temporada 4', 'S4'],
                     ['2 temporada', 'S2'],['3 temporada', 'S3'],
                     ['first season', 'S1'],['second season', 'S2'],['third season', 'S3'],['fourth season', 'S4']]:
            m = scrapertools.find_single_match(title, '(?i)(\s+(?:\(|){}(?:\)|))'.format(f))
            if m:
                title = re.sub(re.escape(m), ' '+r, title)
                # logger.info('MATCH FOUND: ' + m + ', REPLACING WITH ' + ' '+r + ', Result: ' + title, True)
                break

    return title


# Las series tienen la temporada en el título
# La temporada se obtiene normalmente del item.season enviado por la lista anterior,
# Pero puede darse la url a una serie desde un item que no especifica temporada (p.ej: go_serie)
# Esta funcion se usa para extraer el numero de temporada correcto del título
def get_title_season(soup):
    logger.info()

    season = 1

    if soup.find("h2"):
        title = soup.find("h2").get_text(strip=True)

        title = normalize_season(title)

        if re.search(season_pattern, title):
            seasonStr = scrapertools.find_single_match(title, season_pattern)
            if seasonStr:
                # logger.error("title = {}, season str = {}".format(title, seasonStr))
                season = int(scrapertools.find_single_match(seasonStr, '(\d{1,2})') or 1)

    return season