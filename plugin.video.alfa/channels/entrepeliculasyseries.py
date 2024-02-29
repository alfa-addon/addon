# -*- coding: utf-8 -*-
# -*- Channel EntrePeliculasySeries -*-
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
from datetime import datetime

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'entrepeliculasyseries', 
             'host': config.get_setting("current_host", 'entrepeliculasyseries', default=''), 
             'host_alt': ["https://entrepeliculasyseries.nz/"], 
             'host_black_list': ["https://entrepeliculasyseries.com/", 
                                 "https://entrepeliculasyseries.pro/", "https://entrepeliculasyseries.nu/"],   
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'search_active': None
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 10
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "movies/"
tv_path = 'series/'
language = []
url_replace = []
year = datetime.now().strftime('%Y')

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['post-lst']}]), 
                       ('find_all', [{'tag': ['article'], 'class': ['post']}])]),
         'categories': {'find_all': [{'tag': ['li'], 'class': ['cat-item']}]}, 
         'search': {}, 
         'get_language': dict([('find', [{'tag': ['span'], 'class': ["Lang"]}]), 
                               ('find_all', [{'tag': ['img']}])]),
         'get_language_rgx': '(?:flags\/|images\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], 
                                           '@ARG': 'href', '@TEXT': 'page/(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['MvTb-episodes']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['title']}])]), 
         'season_num': [], 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'id': ['MvTb-episodes']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['tt-bx']}])]), 
         'episode_num': {}, 
         'episode_clean': [], 
         'plot': {},
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['tt-player-cn']}]},
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu|calidad\s*', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', action='list_all', url=host + movie_path, 
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Series',  action='list_all', url=host +  tv_path, 
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Anime',  action='list_all', url=host + 'genero/animacion/', 
                         thumbnail=get_thumb('anime', auto=True), c_type='series', extra='anime'))
                         
    itemlist.append(Item(channel=item.channel, title='Dorama',  action='list_all', url=host + 'genero/dorama/', 
                         thumbnail=get_thumb('anime', auto=True), c_type='series', extra='dorama'))

    itemlist.append(Item(channel=item.channel, title="Por Año", action="sub_menu",
                         thumbnail=get_thumb('years.png') ))

    itemlist.append(Item(channel=item.channel, title="Géneros", action="section", url=host, 
                         thumbnail=get_thumb('channels_anime.png'), extra='generos'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True), c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()

    n = int(year) - 1928
    
    while n > 0:
        itemlist.append(Item(channel=item.channel, title=str(1928+n), action='list_all', url=host + "release/%s/" %str(1928+n), 
                         thumbnail=get_thumb('years.png') ))
        n -= 1

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    
    if 'Géneros' in item.title:
        for elem in matches_int:
            elem_json = {}
            #logger.error(elem)

            elem_json['url'] = elem.a.get('href', '')
            elem_json['title'] = elem.get_text(strip=True).replace("(", " (")

            matches.append(elem_json.copy())

    return matches or matches_int


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
            elem_json['url'] = elem.a.get('href', '').replace('#', '') or elem.find('a', class_="link-title").get('href', '')
            elem_json['title'] = elem.find('h2').get_text(strip=True).strip()
            elem_json['thumbnail'] = elem.img.get('data-src', '') or elem.img.get('src', '') \
                                                                  or elem.find('figure', class_='Objf').get('data-src', '')
            elem_json['year'] = elem.find('span', class_='tag').get_text(strip=True).strip()
            elem_json['plot'] = AlfaChannel.parse_finds_dict(elem, findS.get('plot', {}), c_type=item.c_type)
            
            if item.c_type == 'peliculas' and movie_path not in elem_json['url']: continue
            if item.c_type == 'series' and tv_path not in elem_json['url']: continue
            
            if not elem_json['url']: continue
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
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


def episodesxseason(item):
    logger.info()

    kwargs['matches_post_get_video_options'] = findvideos_matches

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        
        if elem.find("span").get_text(strip=True) != str(item.contentSeason): continue
        
        epi_list = elem.find("nav", class_="episodes-nv")
        for epi in epi_list.find_all("a"):
            
            try:
                elem_json['url'] = epi.get("href", "")
                elem_json['season'] = item.contentSeason or 1
                elem_json['episode'] = int(epi.span.get_text(strip=True).split(".")[-1] or 1)
                elem_json['title'] = "%sx%s" % (elem_json['season'], elem_json['episode'])
            
            except:
                logger.error(epi)
                logger.error(traceback.format_exc())
                continue
            
            if not elem_json.get('url', ''): continue
            
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
    
    findS = AHkwargs.get('finds', finds)
    
    servers = {'streamwish': 'streamwish', 'filelions': 'tiwikiwi', "stape": "streamtape", 
               "netu": "netu ", "filemoon": "tiwikiwi", "streamwish": "streamwish",
               "voex": "voe", "1fichier": "onefichier"}
    IDIOMAS = {'0': 'LAT', '1': 'CAST', '2': 'VOSE'}
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            url = elem.iframe.get('src', '')
            soup = AlfaChannel.create_soup(url)
            url = soup.find("div", class_="Video").iframe.get("src", '')
            if "/uqlink." in url:
                url = scrapertools.find_single_match(url, "id=([A-z0-9]+)")
                elem_json['url'] = "https://uqload.io/embed-%s.html" % url
                elem_json['language'] = ''
                elem_json['server'] = 'uqload'
                matches.append(elem_json.copy())
            else:
                soup = AlfaChannel.create_soup(url).find('div', class_='OptionsLangDisp')
                for elem in soup.find_all('li'):
                    lang = elem['data-lang']
                    url = elem['onclick']
                    server = elem.span.text.strip()
                    elem_json['url'] = scrapertools.find_single_match(url, "\('([^']+)'")
                    elem_json['server'] = servers.get(server, server)
                    elem_json['language'] = IDIOMAS.get(lang, lang)
                    matches.append(elem_json.copy())
        except:
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
    kwargs['forced_proxy_opt'] = canonical.get('search_active', 'ProxyCF')

    if not canonical.get('search_active'):
        itemlist = []
        itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Búsquedas bloqueadas por la Web:[/COLOR]", 
                        folder=False, thumbnail=get_thumb("next.png")))
        return itemlist

    try:
        texto = texto.replace(" ", "+")
        item.url = host + '?s=' + texto

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
