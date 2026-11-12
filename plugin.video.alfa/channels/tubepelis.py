# -*- coding: utf-8 -*-
# -*- Channel TubePelis -*-
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

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'tubepelis', 
             'host': config.get_setting("current_host", 'tubepelis', default=''), 
             'host_alt': ["https://www.tubepelis.com/"], 
             'host_black_list': [], 
             # 'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'cf_assistant': False, 'CF_stat': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "pelicula/"
tv_path = 'serie'
language = ['LAT']
url_replace = []

finds = {
         'find': {'find_all': [{'tag': ['div'], 'class': ['gap-3']}]},     #'id': re.compile(r"^browse_\d+")}]},
         'categories': {'find_all': [{'tag': ['a'], 'href': [re.compile(r"/categoria/[a-z-]+")]}]},     #'id': re.compile(r"^browse_\d+")}]},
         'search': {}, 
         'get_language': {'find': [{'tag': ['span'], 'class': ['lang']}]}, 
         'get_language_rgx': r'(?:flags\/||d{4}\/\d{2}\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/\d+', '/%s'], [r'page=\d+', 'page=%s']], 
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['flex gap-2']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], 
                                           '@ARG': 'href', '@TEXT': r'page[/=](\d+)'}])]), 
         'year': {'find': [{'tag': ['span'], 'class': ['year']}], 'get_text': [{'tag': '', '@STRIP': True, '@TEXT': r'(\d+)'}]}, 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tag': ['li'], 'class': ['sel-temp']}]}, 
         'season_num': {'find': [{'tag': ['a'], '@ARG': 'data-season'}]}, 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['article'], 'class': ['post dfx fcl episodes fa-play-circle lg']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'id': re.compile(r"^ms\d+")}]}, 
         'title_clean': [[r'(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         [r'[\(|\[]\s*[\)|\]]', ''], [r'folder', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real-*|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'cnt_tot': 24, 'url_base64': False, 'add_video_to_videolibrary': True, 
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
    
    itemlist.append(Item(channel=item.channel, title='Estrenos', action='list_all', url=host + 'estrenos.html?q=&a=8&page=1', #
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    itemlist.append(Item(channel=item.channel, title='Peliculas', action='list_all', url=host + 'inc/php/buscar.php?q=&a=0&sort=recent&page=1', #
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    itemlist.append(Item(channel=item.channel, title='Mas Vistas', action='list_all', url=host + 'inc/php/buscar.php?q=&a=0&sort=views&page=1', #
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    itemlist.append(Item(channel=item.channel, title="Géneros", action="section", url=host, 
                         thumbnail=get_thumb('genres', auto=True), extra='generos'))
    itemlist.append(Item(channel=item.channel, title="Año", action="anno", url=host, 
                         thumbnail=get_thumb('year', auto=True), extra='generos'))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True),  c_type='search'))
    
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
        
        elem_json = {}
        
        try:
            url = elem.get("href", '')
            url = scrapertools.find_single_match(url, 'categoria/([a-z-]+)')
            elem_json['url'] = "%sinc/php/buscar.php?q=%s&a=3&page=1" %(item.url, url)
            elem_json['title'] = elem.get_text(strip=True).replace('folder', '')
                                                                
            if elem.img: elem_json['thumbnail'] = elem.img.get('data-thumb_url', '') or elem.img.get('data-original', '') \
                                                                                     or elem.img.get('data-src', '') \
                                                                                     or elem.img.get('src', '')
        
        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        matches.append(elem_json.copy())
    
    return matches


def anno(item):
    logger.info()
    from datetime import datetime
    
    itemlist = []
    
    now = datetime.now()
    year = int(now.year)
    while year >= 1937:
        itemlist.append(item.clone(title="%s" %year, action="list_all", url= "%sbuscar/?q=%s&a=1&page=1" % (item.url,year), c_type='peliculas'))
        year -= 1
    
    return itemlist


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
            if "item-center" in elem['class']: continue
            elem_json['url'] = elem.a.get("href", "")
            if item.c_type == 'peliculas' and tv_path in elem_json['url']: continue
            # if item.c_type == 'series' and movie_path in elem_json['url']: continue
            elem_json['title'] = elem.img.get("alt", "")
            elem_json['thumbnail'] = elem.img['src']
            elem_json['year'] = elem.find('div', class_='gap-2').find('span').get_text(strip=True) if elem.find('div', class_='gap-2').find('span') else ''
        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        
        matches.append(elem_json.copy())
    
    return matches


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            url = elem.iframe.get('data-src', '') or  elem.iframe.get('src', '')
            url = url.replace('%3D', '=')
            elem_json['url'] = AlfaChannel.convert_url_base64(url, '')
            elem_json['server'] = ''
            elem_json['language'] = ''
        except Exception:
            logger.error(server)
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        
        matches.append(elem_json.copy())
    
    return matches, langs


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    try:
        texto = texto.replace(" ", "+")
        item.url = '%sinc/php/buscar.php?q=%s&a=0&sort=recent&page=1' % (item.url, texto)
        
        if texto:
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

