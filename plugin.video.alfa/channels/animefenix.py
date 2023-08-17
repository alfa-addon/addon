# -*- coding: utf-8 -*-
# -*- Channel AnimeFenix -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-
# -*- Convertido a AH por DieFeM -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = {'vose': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['directo', 'verystream', 'openload',  'streamango', 'uploadmp4', 'burstcloud']
forced_proxy_opt = 'ProxyCF'

canonical = {
             'channel': 'animefenix', 
             'host': config.get_setting("current_host", 'animefenix', default=''), 
             'host_alt': ["https://animefenix.tv/"], 
             'host_black_list': ["https://www.animefenix.tv/", "https://www.animefenix.com/"], 
             'pattern': '<div\s*class="navbar-start">\s*<a\s*class="navbar-item"\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF_stat': False, 'session_verify': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'animes?type[]=movie&order=updated'
tv_path = 'animes?type[]=tv&order=updated'
language = []
url_replace = []
seasonPattern = '(?i)(?:\s+Season|)\s+(\d{1,2})(?:[a-z]{2}\s+Season|)$'

finds = {'find': dict([('find', [{'tag': ['div'], 'class': ['list-series']}]), 
                       ('find_all', [{'tag': ['article'], 'class': ['serie-card']}])]), 
         'categories': dict([('find', [{'tag': ['select'], 'id': ['genre_select']}]),
                             ('find_all', [{'tag': ['option']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\?page=\d+', '?page=%s']],
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination-list']}]),
                            ('find_all', [{'tag': ['a'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {},
         'season_num': {},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['ul'], 'class': ['anime-page__episode-list']}]),
                           ('find_all', [{'tag': ['a']}])]),
         'episode_num': [], 
         'episode_clean': [[seasonPattern, '']], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['script'], 'string': re.compile('var\s*tabsArray')}]),
                             ('get_text', [{'tag': '', '@STRIP': True, '@TEXT_M': "tabsArray\['\d+'\]\s*=\s*\"([^\"]+)\"", '@DO_SOUP': True}])]),
         'title_clean': [[seasonPattern, '']],
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

    itemlist.append(Item(channel=item.channel, title='Últimos Animes', url=host, action='list_all',
                         thumbnail=get_thumb('newest', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'animes?page=1&type[]=tv&order=updated', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'animes?page=1&type[]=movie&order=updated', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host + 'animes?page=1', 
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
        elem_json['url'] = '%sanimes?page=1&genre[]=%s&order=updated' % (host, elem.get('value', ''))
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['div'], 'class': ['capitulos-grid']}]), 
                              ('find_all', [{'tag': ['div'], 'class': ['item']}])])

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
                elem_json['title'] = elem.find("div", class_="overtitle").get_text(strip=True)
                try:
                    season = scrapertools.find_single_match(elem_json['title'], '\s+(\d+)$') or '1'
                    episode = elem.find("div", class_="overepisode").get_text(strip=True)
                    episode = scrapertools.find_single_match(episode, '\s+(\d+)$')
                    elem_json['season'] = int(season)
                    elem_json['episode'] = int(episode)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'
                elem_json['url'] = elem.find("div", class_="overarchingdiv").a.get('href', '')
                elem_json['go_serie'] = {'url': re.sub('(?:-\d+|)-\d+$', '', elem_json['url']).replace('ver/', '')}
            else:
                elem_json['title'] = elem.find("div", class_="title").h3.a.get_text(strip=True)
                elem_json['url'] = elem.find("figure", class_="image").a.get('href', '')

                try:
                    _type = elem.find("span", class_="type").get_text(strip=True)
                except Exception:
                    _type = ''

                if not elem_json.get('mediatype'):
                    elem_json['mediatype'] = 'tvshow' if _type != "Película" else 'movie'

                if item.c_type == 'series' and elem_json['mediatype'] == 'movie':
                    continue
                if item.c_type == 'peliculas' and elem_json['mediatype'] == 'tvshow':
                    continue
                
                if elem_json['mediatype'] == 'movie':
                    elem_json['action'] = 'seasons'
                else:
                    if re.search(seasonPattern, elem_json['title']):
                        elem_json['season'] = int(scrapertools.find_single_match(elem_json['title'], seasonPattern))
                        if elem_json['season'] > 1:
                            elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                                      % (AlfaChannel.color_setting.get('movies', 'white'), 'Temporada %s' % elem_json['season'])]

                # Todos los thumbs dan: "Failed: HTTP response code said error(22)"
                # try:
                    # elem_json['thumbnail'] = elem.find("figure", class_="image").a.img.get("src", "")
                # except Exception:
                    # pass

                # Esto se carga la busqueda en TMDB porque el año no coincide
                # try:
                    # elem_json['year'] = elem.find("span", class_="year").get_text(strip=True)
                # except Exception:
                    # elem_json['year'] = '-'

                elem_json['year'] = '-'
                elem_json['quality'] = 'HD'

                if elem.find("div", class_=["serie-card__information"]): 
                    elem_json['plot'] = elem.find("div", class_=["serie-card__information"]).p.get_text(strip=True)

            elem_json['language'] = 'VOSE'
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

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            elem_json['url'] = elem.get("href", "")
            epistr = elem.span.get_text(strip=True)
            elem_json['title'] = elem.get_text(strip=True).replace(epistr, '')
            elem_json['episode'] = int(scrapertools.find_single_match(epistr, '\s+(\d+)$') or 1)
            elem_json['season'] = item.contentSeason

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

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}

        try:
            iframeUrl = elem.find('iframe').get('src', '')
            elem_json['url'] = convertUrl(item, iframeUrl)
            if re.search(r'embedwish|hqq|netuplayer|krakenfiles|fireload', elem_json['url'], re.IGNORECASE):
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
        item.url = host + 'animes?page=1&q=' + texto

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
    item.channel = channel

    try:
        if categoria in ['anime']:
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


def convertUrl(item, iframeUrl, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    kwargs['soup'] = False
    kwargs['json'] = False
    kwargs['unescape'] = False
    kwargs['referer'] = item.url
    kwargs['hide_infobox'] = True
    kwargs['canonical'] = canonical
    kwargs['ignore_response_code'] = True
    kwargs['timeout'] = 10

    servers = {"6": "https://www.yourupload.com/embed/%s", "15": "https://mega.nz/embed/%s",
               "21": "https://www.burstcloud.co/embed/%s", "12": "https://ok.ru/videoembed/%s",
               "17": "https://videobin.co/embed-%s.html", "9": host + "stream/amz.php?v=%s",
               "11": host +"stream/amz.php?v=%s", "2": "https://www.fembed.com/v/%s",
               "3": "https://www.mp4upload.com/embed-%s.html", "4": "https://sendvid.com/embed/%s",
               "19": "https://videa.hu/player?v=%s", "23": "https://sbthe.com/e/%s"}

    srv_id, v_id = scrapertools.find_single_match(iframeUrl, "player=(\d+)&code=([^&]+)")

    if AlfaChannel.do_unquote(v_id, plus=False).startswith("/"):
        v_id = v_id[1:]

    if 'fireload' in v_id:
        url = v_id
        if not url.startswith('http'):
            url = 'https://' + url
    elif srv_id not in servers:
        srv_data = AlfaChannel.create_soup(url, **kwargs).data
        url = host.rstrip('/') + scrapertools.find_single_match(srv_data, 'playerContainer.innerHTML .*?src="([^"]+)"')
    else:
        srv = servers.get(srv_id, "directo")
        if srv != "directo":
            url = srv % v_id

    if "/stream/" in url:
        data = AlfaChannel.create_soup(url, **kwargs).data
        url = scrapertools.find_single_match(data, '"file":"([^"]+)"').replace('\\/', '/').replace('/stream/fl.php?v=', '')

    if not url or url == 'https://':
        return iframeUrl

    return AlfaChannel.do_unquote(url, plus=False)