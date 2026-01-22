# -*- coding: utf-8 -*-
# -*- Channel TubeOnLine -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

if not PY3: _dict = dict; from lib.AlfaChannelHelper import dict
from lib.AlfaChannelHelper import DictionaryAllChannel
from lib.AlfaChannelHelper import re, traceback
from lib.AlfaChannelHelper import Item, servertools, scrapertools, get_thumb, config, logger, filtertools, autoplay
# from lib.alfa_assistant import is_alfa_installed

IDIOMAS = {'eng': 'VOSE', "mx": "LAT", "es": "CAST",
           'container33': 'VOSE', "container11": "LAT", "container22": "CAST"}
list_language = list(set(IDIOMAS.values()))
list_quality_movies = ['HD']
list_quality_tvshow = list_quality_movies
list_quality = list_quality_movies
list_servers = [
    'filemoon',
    'bigwarp',
    'bestb',
    'vidoza',
    'doodstream',
    'uqload',
    'streamwish',
    'vidmoly',
    'voe'
    ]

# cf_assistant = "force" if is_alfa_installed() else False
cf_assistant = False
# forced_proxy_opt = None if cf_assistant else 'ProxyCF'
forced_proxy_opt = None
debug = config.get_setting('debug_report', default=False)

canonical = {
             'channel': 'tubeonline', 
             'host': config.get_setting("current_host", 'tubeonline', default=''), 
             'host_alt': ["https://www.tubeonline.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': cf_assistant, 
             'cf_assistant_ua': True, 'cf_assistant_get_source': True if cf_assistant == 'force' else False, 
             'cf_no_blacklist': True, 'cf_removeAllCookies': False if cf_assistant == 'force' else True,
             'cf_challenge': True, 'cf_returnkey': 'url', 'cf_partial': True, 'cf_debug': debug, 
             'cf_cookies_names': {'cf_clearance': False},
             'CF_if_assistant': True if cf_assistant is True else False, 'retries_cloudflare': -1, 
             'CF_stat': True if cf_assistant is True else False, 'session_verify': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': False
            }

host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "pelicula/"
tv_path = 'serie/'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tagOR': ['div'], 'id': ['archive-content']},
                                 {'tag': ['div'], 'class': ['items']}]), 
                       ('find_all', [{'tag': ['article'], 'id': re.compile("^post-\d+")}])]), 
         'categories': dict([('find', [{'tag': ['nav'], 'class': ['genres']}]), 
                             ('find_all', [{'tag': ['a']}])]),
         'search': {'find_all': [{'tag': ['div'], 'class': ['result-item']}]}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}, 
                                      {'tag': ['span']}]), 
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '\d*\s*de\s*(\d+)'}])]),  
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['se-c']}])]),
         'season_num': dict([('find', [{'tag': ['span'], 'class': ['se-t']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True}])]),
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': host, 
         'episode_url': '%sepisodio/%s-%sx%s', 
         'episodes': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['se-c']}])]),
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['ul'], 'id': re.compile("^container(?:11|22|33)$")}]},
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 30, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'IDIOMAS_TMDB': {0: 'es', 1: 'en', 2: 'es'}}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=host + 'episodio/', action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))
    
    itemlist.append(Item(channel=item.channel, title='Series', url=host + tv_path, action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', url=host + movie_path, action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Castellano', url=host + 'idioma/castellano/', action='list_all',
                         thumbnail=get_thumb('cast', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Latino', url=host + 'idioma/latino/', action='list_all',
                         thumbnail=get_thumb('latino', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Subtitulado', url=host + 'idioma/subtitulado/', action='list_all',
                         thumbnail=get_thumb('vose', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Géneros', action='section', url=host,
                         thumbnail=get_thumb('genres', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    itemlist = AlfaChannel.section(item, **kwargs)
    return [i for i in itemlist if "Porno" not in i.title]


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            plus18 = elem.find("a", text="Peliculas Porno +18")
            if plus18:
                continue
            
            if item.c_type == 'search':
                elem_json['url'] = elem.a.get('href', '')
                elem_json['title'] = elem.img.get("alt", '').replace('VOSE', '')
                elem_json['thumbnail'] = elem.img.get('data-src', '') or elem.img.get('src', '')
                if elem.find("span", class_="year"): elem_json['year'] = elem.find("span", class_="year").get_text(strip=True)
                elem_json['mediatype'] = 'tvshow' if "serie" in elem_json['url'] and not "pelicula" in elem_json['url'] else 'movie'

            else:
                if item.c_type == 'episodios':
                    sxe = elem.find("span", class_="b").getText(strip=True)
                    try:
                        season, episode = scrapertools.find_single_match(sxe, '(\d+)x(\d+)')
                        elem_json['season'] = int(season)
                        elem_json['episode'] = int(episode)
                    except Exception:
                        elem_json['season'] = 1
                        elem_json['episode'] = 1
                    elem_json['mediatype'] = 'episode'
                    elem_json['title'] = "%s - %s" % (sxe, elem.find("span", class_="c").getText(strip=True))
                else:
                    elem_json['title'] = elem.find("div", class_="poster").img.get("alt", '')

                elem_json['url'] = elem.find("a")['href']
                if not elem_json.get('mediatype'):
                    elem_json['mediatype'] = 'tvshow' if "serie" in elem_json['url'] and not "pelicula" in elem_json['url'] else 'movie'
                elem_json['thumbnail'] = elem.find("div", class_="poster").img.get('data-src', '') \
                                         or elem.find("div", class_="poster").img.get('src', '')
                try:
                    elem_json['year'] = elem.find("div", class_="data").find("span").get_text(strip=True)
                except Exception:
                     elem_json['year'] = '-'

            qlty = elem.find("span", class_="quality")
            if qlty:
                elem_json['quality'] = qlty.getText(strip=True)
            langs = elem.find("div", class_="idi")
            if langs:
                elem_json['language'] = get_languages(langs.find_all("img"))
            plot = elem.find("div", class_=["texto", "contenido"])
            if plot: 
                elem_json['plot'] = plot.get_text(strip=True)

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

    kwargs['matches_post_get_video_options'] = findvideos_matches
    soup = AHkwargs.get('soup', '')

    return AlfaChannel.episodes(item, data=soup, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem_season in matches_int:

        if elem_season.find("span", class_="se-t").get_text(strip=True) != str(item.contentSeason): continue
        epi_list = elem_season.find("ul", class_="episodios")

        if 'no hay episodios para' in str(epi_list):
            return matches

        for elem in epi_list.find_all("li"):
            elem_json = {}
            #logger.error(elem)

            try:
                info = elem.find("div", class_="episodiotitle")
                elem_json['url'] = info.a.get("href", "")
                elem_json['episode'] = int(elem.find("div", class_="numerando").get_text(strip=True).split("x")[1] or 1)
                elem_json['title'] = info.a.get_text(strip=True)
                elem_json['season'] = item.contentSeason
                elem_json['thumbnail'] = elem.img.get('data-src', '') or elem.img.get('src', '')

            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    kwargs['matches_post_episodes'] = episodesxseason_matches

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()
    
    matches = []
    
    soup = AHkwargs.get('soup', '')
    
    try:
        plus18 = soup.find("div", class_="sgeneros").find("a", text="Peliculas Porno +18")
        if plus18:
            return matches, langs
    except Exception:
        pass

    servers = {'strmup': 'bestb', 'hqq': '', 'asnwish': 'streamwish'}

    for lang_container in matches_int:
        language = IDIOMAS.get(lang_container["id"], "VOSE")
        for elem in lang_container.find_all("li"):
            elem_json = {}
            try:
                elem_json['server'] = re.sub(r"\.\w{2,4}", "", elem["data-name"].lower())
                elem_json['server'] = servers.get(elem_json['server'], elem_json['server'])
                if not elem_json['server']: continue
                elem_json['language'] = language
                elem_json['url'] = item.url
                elem_json['title'] = '%s'
                elem_json['extra'] = elem['data-url']
                matches.append(elem_json.copy())
            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

    return matches, langs


def play(item):
    logger.info()
    itemlist = list()
    try:
        kwargs['headers'] = {'Referer': item.url}
        kwargs['post'] = {"nombre": item.extra}
        new_soup = AlfaChannel.create_soup('https://www.tubeonline.net/wp-content/themes/dooplayorig123/inc/encriptar.php', **kwargs)
        url = new_soup.iframe["src"]
        itemlist.append(item.clone(url=url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)
    except Exception:
        logger.error(traceback.format_exc())

    return itemlist


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        texto = AlfaChannel.do_quote(texto, '', plus=True)
        item.url = item.url + "?s=" + texto

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
    
    logger.debug("AQUI HAY NIVEL " + categoria)

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = canonical['channel']

    try:
        if categoria == 'series':
            item.url = host + 'episodio/'
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


def get_languages(elems):
    langs = list()
    for elem in elems:
        lang = scrapertools.find_single_match(elem["src"].strip(), r'/([^/]+).png$')
        if lang:
            langs.append(IDIOMAS.get(lang, lang))
    return langs