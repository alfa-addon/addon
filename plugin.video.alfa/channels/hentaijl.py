# -*- coding: utf-8 -*-
# -*- Channel HentaiJL -*-
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

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'hentaijl', 
             'host': config.get_setting("current_host", 'hentaijl', default=''), 
             'host_alt': ["https://hentaijl.com/"], 
             'host_black_list': [],
             'pattern': '<ul\s*class="Menu">\s*<li\s*class="Current">\s*<a\s*href="([^"]+)"',
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'directorio-hentai?tipo[]=3&order=default'
tv_path = 'directorio-hentai?tipo[]=1&tipo[]=7&order=default'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['ListAnimes']}]), 
                       ('find_all', [{'tag': ['li']}])]), 
         'categories': dict([('find', [{'tag': ['select'], 'id': ['genre_select']}]),
                             ('find_all', [{'tag': ['option']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\?page=\d+', '?page=%s']],
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}]),
                            ('find_all', [{'tag': ['a'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {},
         'season_num': {},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': host, 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['script'], 'string': re.compile('var\s*episodes\s*=\s*\[')}]),
                           ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': 'var\s*episodes\s*=\s*([^;]+);', '@EVAL': True}])]),
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['script'], 'string': re.compile('var\s*video \s*=\s*\[')}]),
                             ('get_text', [{'tag': '', '@STRIP': True, '@TEXT_M': "video\[\d+\]\s*=\s*'([^']+)'", '@DO_SOUP': True}])]),
         'title_clean': [['(?i)Español|Latino', ''],
                         ['(?i)\s*(?:temporada|season)\s*\d+', ''],
                         ['(?i)\s+(?:\(|)Sin\s+Censura(?:\)|)', '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
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

    itemlist.append(Item(channel=item.channel, title='Estrenos', url=host + 'directorio-hentai?page=1&estado[]=2&order=updated', action='list_all',
                         thumbnail=get_thumb('premieres', auto=True), extra='estrenos'))

    itemlist.append(Item(channel=item.channel, title='Hentai', url=host + 'directorio-hentai?page=1&tipo[]=1&tipo[]=7&order=updated', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Latino', url=host + 'directorio-hentai?page=1&genre[]=71&order=updated', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='JAV', url=host + 'directorio-hentai?page=1&tipo[]=2&order=updated', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host + 'directorio-hentai?page=1', 
                         thumbnail=get_thumb('categories', auto=True), extra='categorías'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    return AlfaChannel.section(item, matches_post=section_matches, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        # logger.error(elem)
        elem_json = {}
        elem_json['title'] = elem.get_text(strip=True)
        elem_json['url'] = '%sdirectorio-hentai?page=1&genre[]=%s&order=updated' % (host, elem.get('value', ''))
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['ul'], 'class': ['ListEpisodios AX Rows A06 C04 D03'], 'id': ''}]), 
                              ('find_all', [{'tag': ['li']}])])

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
                # logger.error(elem)
                url = elem.a.get('href', '')
                try:
                    elem_json['season'] = get_title_season(url)
                    elem_json['episode'] = elem.a.find("span", class_="Capi").get_text(strip=True)
                    elem_json['episode'] = scrapertools.find_single_match(elem_json['episode'], '(?i)(?:Episodio|Cap(?:i|í)tulo)\s+(\d+)')
                    elem_json['episode'] = int(elem_json['episode'] or 1)
                except Exception as error:
                    # handle the exception
                    logger.error("An exception occurred: {}".format(error))
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'
                elem_json['title'] = elem.find("strong", class_="Title").get_text(strip=True)
                elem_json['url'] = url
                elem_json['thumbnail'] = elem.find("img").get("src", "")
            else:
                elem_json['title'] = elem.find("h3", class_="Title").get_text(strip=True)
                elem_json['url'] = elem.find("article").a.get('href', '')
                elem_json['mediatype'] = 'tvshow'
                
                seasonPattern = '(?i)\s+(?:temporada|season)\s+(\d+)'
                if re.search(seasonPattern, elem_json['title']):
                    elem_json['season'] = int(scrapertools.find_single_match(elem_json['title'], seasonPattern))
                    if elem_json['season'] > 1:
                        elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                                  % (AlfaChannel.color_setting.get('movies', 'white'), 'Temporada %s' % elem_json['season'])]

                elem_json['plot'] = elem.find("div", class_=["Description"]).find_all("p")[2].get_text(strip=True)
                elem_json['thumbnail'] = elem.find("figure").find("img").get("src", "")

            elem_json['language'] = get_lang_from_str(elem_json['title'])
            elem_json['year'] = '-'
            elem_json['quality'] = 'HD'

            elem_json['context'] = autoplay.context

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json['url']: continue

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
    titleSeason = get_title_season(soup.find('script', string=re.compile('var\s*anime_info\s*=\s*\[')).string)
    if titleSeason != item.contentSeason:
        return matches
    
    # logger.error(item)
    for x, (episode, url, thumbnail, movie_data) in enumerate(matches_int):
        elem_json = {}
        # logger.error(matches_int[x])
        
        try:
            elem_json['title'] = 'Episodio %s' % episode
            elem_json['url'] = "%s/%s" % (item.url, url)
            elem_json['thumbnail'] = thumbnail
            
            elem_json['season'] = titleSeason
            elem_json['episode'] = episode
        
        except Exception:
            logger.error(matches_int[x])
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()

    kwargs['matches_post_episodes'] = episodesxseason_matches

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)

        try:
            elem_json['url'] = elem.find('iframe').get('src', '')

            if re.search(r'hqq|netuplayer|krakenfiles', elem_json['url'], re.IGNORECASE):
                continue

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
        item.url = host + 'directorio-hentai?page=1&q=' + texto

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


def get_lang_from_str(string):

    if 'latino' in string.lower():
        lang = 'Latino'
    elif 'español' in string.lower():
        lang = 'Castellano'
    else:
        lang = 'VOSE'

    return lang

# Algunas series tienen la temporada en el titulo, lo cual hace que TMDB devuelva los datos incorrectos
# Ya que por defecto la temporada se obtiene de otro lado, esto crea una ambigüedad.
# Esta funcion se usa para extraer el numero de temporada correcto del titulo en la url
def get_title_season(url):
    logger.info()

    season = 1
    seasonPattern = '(?i)temporada(?:-|\s*)(\d+)-?'

    if re.search(seasonPattern, url):
        season = int(scrapertools.find_single_match(url, seasonPattern))

    return season