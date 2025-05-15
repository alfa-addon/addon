# -*- coding: utf-8 -*-
# -*- Channels Pelispanda, Yestorrent, Hacktorrent -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

from lib.alfa_assistant import is_alfa_installed

# Canal común con Kacktorrent, Pelispanda

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_T
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_T
forced_proxy_opt = 'ProxySSL'

cf_assistant = True if is_alfa_installed() else False
forced_proxy_opt = None if cf_assistant else 'ProxyCF'
debug = config.get_setting('debug_report', default=False)

canonical = {
             'channel': 'pelispanda', 
             'host': config.get_setting("current_host", 'pelispanda', default=''), 
             'host_alt': ['https://pelispanda.org/'], 
             'host_black_list': ['https://pelispanda.win/', 'https://pelispanda.re/', 'https://pelispanda.com/'], 
             'set_tls': True, 'set_tls_min': True, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': cf_assistant, 
             'cf_assistant_ua': True, 'cf_assistant_get_source': True if cf_assistant == 'force' else False, 
             'cf_no_blacklist': True, 'cf_removeAllCookies': False if cf_assistant == 'force' else True,
             'cf_challenge': True, 'cf_returnkey': 'url', 'cf_partial': True, 'cf_debug': debug, 
             'cf_cookies_names': {'cf_clearance': False},
             'CF_if_assistant': True if cf_assistant is True else False, 'retries_cloudflare': -1, 
             'CF_stat': True if cf_assistant is True else False, 'session_verify': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
channel = canonical['channel']
categoria = channel.capitalize()
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)     # Actualización sólo últ. Temporada?
min_temp = modo_ultima_temp if not modo_ultima_temp else 'continue'

timeout = config.get_setting('timeout_downloadpage', channel)
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/peliculas"
tv_path = '/series'
anime_path = '/animes'
language = ['LAT']
url_replace = []
posts_per_page = 36

finds = {'find': {'find_all': [{'tag': ['div'], 'class': ['col-6 col-sm-4 col-lg-3 col-xl-2']}]}, 
         'categories': {}, 
         'search': dict([('find', [{'tag': ['body']}]), 
                                   ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'results|DEFAULT'}])]), 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': dict([('find', [{'tag': ['ul'], 'class': True}]), 
                              ('get_text', [{'tag': '', '@STRIP': True}])]), 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\&page=\d+', '&page=%s']], 
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}, 
                                      {'tag': ['a'], 'class': ['next page-numbers']}]), 
                            ('find_previous', [{'tag': ['a'], 'class': ['page-numbers']}]), 
                            ('get_text', [{'@TEXT': '(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['body']}]), 
                          ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'downloads|DEFAULT'}])]), 
         'season_num': {}, 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['body']}]), 
                           ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'downloads|DEFAULT'}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['body']}]), 
                                       ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'downloads|DEFAULT'}])]), 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': min_temp, 'url_base64': True, 'add_video_to_videolibrary': True, 'cnt_tot': posts_per_page/2, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = []

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_animes = get_thumb("channels_anime.png")
    thumb_genero = get_thumb("genres.png")
    thumb_anno = get_thumb("years.png")
    thumb_calidad = get_thumb("top_rated.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all", 
                         url=host + 'wp-json/wpreact/v1/movies?posts_per_page=%s&page=1' % posts_per_page, 
                         thumbnail=thumb_pelis, c_type="peliculas"))
    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Por Género[/COLOR]", action="section", 
                         url=host + 'wp-content/themes/wpreact/assets/js/bundle.js', thumbnail=thumb_genero, 
                         extra='genero', c_type="peliculas"))
    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Por Idiomas[/COLOR]", action="section", 
                         url=host + 'wp-content/themes/wpreact/assets/js/bundle.js', thumbnail=thumb_calidad, 
                         extra='idioma', c_type="peliculas"))

    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", 
                         url=host + 'wp-json/wpreact/v1/series?posts_per_page=%s&page=1' % posts_per_page, 
                         thumbnail=thumb_series, c_type="series"))

    itemlist.append(Item(channel=item.channel, title="Animes", action="list_all", 
                         url=host + 'wp-json/wpreact/v1/animes?posts_per_page=%s&page=1' % posts_per_page, 
                         thumbnail=thumb_animes, extra='animes', c_type="series"))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         url=host, thumbnail=thumb_buscar, c_type="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                         folder=False, thumbnail=thumb_separador))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                         thumbnail=thumb_settings))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)                                # Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools

    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()

    return


def section(item):
    logger.info()

    patron = 'e\.createElement\("button",{"aria-label":"%s"(.*?\)\))\)\),' % item.extra
    patron_list = 'e\.createElement\("li",null,e\.createElement\(Le,{to:"([^"]+)"},"([^"]+)"\)\)'
    matches_int = []
    itemlist = []
    data = ''

    response = AlfaChannel.create_soup(item.url, soup=False, **kwargs)
    if response.sucess:
        data = scrapertools.find_single_match(response.data, patron)
        if data:
            matches_int = scrapertools.find_multiple_matches(data, patron_list)
            
            for url, title in matches_int:
                item_local = item.clone()
                #logger.error(elem)

                item_local.url = url.strip('/').split('/')[-1]
                if item.extra in ['genero']:
                    item_local.url = host + 'wp-json/wpreact/v1/category?category=%s&posts_per_page=%s&page=1' % (item_local.url, posts_per_page)
                elif item.extra in ['idioma']:
                    item_local.url = host + 'wp-json/wpreact/v1/movies?posts_per_page=%s&page=1&language=%s' % (posts_per_page, item_local.url)
                else:
                    continue
                
                item_local.title = scrapertools.decode_utf8_error(title)
                item_local.action = 'list_all'
                
                itemlist.append(item_local.clone())

    return itemlist


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.extra in ['genero']:
        findS['find'] = finds['search']

    elif item.c_type in ['peliculas', 'series'] or item.extra in ['animes', 'idioma']:
        findS['find'] = dict([('find', [{'tag': ['body']}]), 
                              ('get_text', [{'tag': '', '@STRIP': False, '@JSON': '%s|DEFAULT' \
                                                         % ('movies' if (item.c_type == 'peliculas' or item.extra in ['idioma']) \
                                                                     else item.extra or item.c_type)}])])

    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    try:
        patron_pages = '\],\s*"total"\s*\:\s*(\d+)\s*,\s*"pages"\s*:(\d+)\s*\}'
        items, pages = scrapertools.find_single_match(str(AHkwargs['soup']), patron_pages)
        AlfaChannel.last_page = int((int(items)+finds['controls']['cnt_tot']-1)/finds['controls']['cnt_tot'])
    except Exception:
        logger.error(traceback.format_exc())

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['mediatype'] = 'movie' if elem.get('type', 'pelicula') == 'pelicula' else 'tvshow'
            elem_json['title'] = elem.get('title', '')
            elem_json['url'] = '%swp-json/wpreact/v1/%s/%s/' % (host, elem_json['mediatype'] if elem_json['mediatype'] == 'movie' \
                                                                                             else 'serie' if item.extra != 'animes' \
                                                                                             else 'anime', elem.get('slug', ''))
            if elem_json['mediatype'] in ['tvshow']: elem_json['url'] = elem_json['url'] + 'related/'
            elem_json['thumbnail'] = elem.get('featured', '')
            elem_json['language'] = '*%s' % elem.get('language', '')
            if 'ingles' in item.url: elem_json['language'] = '%s, VOS' % elem_json['language']

            elem_json['year'] = elem.get('year', '-')
            if elem.get('tmdb_id', ''): elem_json['tmdb_id'] = elem['tmdb_id']

            matches.append(elem_json.copy())

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if item.extra in ['Idioma', 'anime']: AlfaChannel.filter_languages = 0

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


def episodesxseason(item):
    logger.info()

    kwargs['matches_post_get_video_options'] = findvideos_matches
    kwargs['headers'] = {'Referer': item.url}
    kwargs['error_check'] = False

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, generictools=True, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    if anime_path.rstrip('s') in item.url: AlfaChannel.filter_languages = 0

    for elem_season in matches_int:
        if not elem_season or elem_season[0].get('season', 0) != item.infoLabels['season']: continue
        
        for elem in elem_season:
            elem_json = {}
            #logger.error(elem)

            try:
                elem_json['season'] = elem.get('season', 0)
                elem_json['episode'] = elem.get('episode', 0)
                elem_json['server'] = 'torrent'
                elem_json['quality'] = '*%s' % elem.get('quality', '')
                elem_json['torrent_info'] = elem.get('size', '').replace('-', '')
                elem_json['url'] = elem.get('download_link', '')
                elem_json['language'] = '*%s' % elem.get('language', '')

                if not elem_json.get('url', ''): 
                    continue

                matches.append(elem_json.copy())

            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

    return matches


def findvideos(item):
    logger.info()

    kwargs['matches_post_episodes'] = episodesxseason_matches
    
    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=play, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    videolibrary = AHkwargs.get('videolibrary', False)

    if videolibrary:
        for x, (episode_num, _scrapedserver, _scrapedquality, _scrapedlanguage, scrapedsize, scrapedurl) in enumerate(matches_int):
            elem_json = {}
            #logger.error(elem)

            if item.infoLabels['mediatype'] in ['episode']:
                elem_json['season'] = item.infoLabels['season']
                elem_json['episode'] = episode_num
            if _scrapedserver not in ['torrent', 'Torrent', 'array', 'Array']:
                elem_json['server'] = 'torrent'
                elem_json['quality'] = _scrapedserver
                elem_json['language'] = _scrapedquality
            else:
                elem_json['server'] = _scrapedserver
                elem_json['quality'] = _scrapedquality
                elem_json['language'] = _scrapedlanguage
            if not elem_json['quality'].startswith('*'): elem_json['quality'] = '*%s' % elem_json['quality']
            if not elem_json['language'].startswith('*'): elem_json['language'] = '*%s' % elem_json['language']
            elem_json['url'] = scrapedurl
            elem_json['torrent_info'] = scrapedsize

            matches.append(elem_json.copy())
            item.emergency_urls[1][x] = elem_json.copy()

    else:
        for elem in matches_int:
            elem_json = {}
            #logger.error(elem)

            try:
                elem_json['server'] = 'torrent'
                elem_json['quality'] = '*%s' % elem.get('quality', '')
                elem_json['torrent_info'] = elem.get('size', '').replace('-', '')
                elem_json['url'] = elem.get('download_link', '')
                elem_json['language'] = '*%s' % elem.get('language', '')

                if not elem_json.get('url', ''): 
                    continue

                matches.append(elem_json.copy())

            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

    return matches, langs


def play(item):

    kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'timeout': 5, 'CF': True, 'canonical': {}, 'soup': False}

    if 'cinestart' in item.url:
        url, post = item.url.split('?')
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Referer': item.url}
        response = AlfaChannel.create_soup(url.replace('player.php', 'r.php'), post=post, headers=headers, 
                                           follow_redirects=False, hide_infobox=True, **kwargs)

        if response.code in AlfaChannel.REDIRECTION_CODES:
            item.url = '%s|Referer=%s' % (response.headers.get('location', ''), AlfaChannel.obtain_domain(item.url, scheme=True))

    return [item]


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    texto = texto.replace(" ", "+")
    busq = 'wp-json/wpreact/v1/search?query=%s&posts_per_page=%s&page=1' % (texto, posts_per_page)
    
    try:
        item.url = host + busq
        item.extra = 'search'

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []
    except Exception:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []
 
 
def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    itemlist = []
    item = Item()

    item.title = "newest"
    item.channel = channel
    if not item.infoLabels["year"]:
        import datetime
        item.infoLabels["year"] = datetime.datetime.now().year
    
    try:
        if categoria in ['peliculas', 'latino', 'torrent']:
            item.category_new = "newest"
            if categoria in ['peliculas', 'torrent']:
                item.url = host + "wp-json/wpreact/v1/released/"
            if categoria in ['latino']:
                item.url = host + "wp-json/wpreact/v1/movies?posts_per_page=%s&page=1&language=latino" % posts_per_page
            item.c_type = 'peliculas'
            item.extra = categoria
            item.extra2 = "novedades"
            item.action = "list_all"
            itemlist.extend(list_all(item))
                
        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
        
        if categoria in ['series']:
            item.category_new = "newest"
            item.url = host + "wp-json/wpreact/v1/%s?posts_per_page=%s&page=1" % (categoria, posts_per_page)
            item.c_type = 'series'
            item.extra = categoria
            item.extra2 = "novedades"
            item.action = "list_all"
            itemlist.extend(list_all(item))

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))

    return itemlist
