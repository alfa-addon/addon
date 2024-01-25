# -*- coding: utf-8 -*-
# -*- Channel PelisPedia -*-
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
             'channel': 'pelispedia', 
             'host': config.get_setting("current_host", 'pelispedia', default=''), 
             'host_alt': ["https://pelispedia.is/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
language = ['LAT']
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['post-lst']}]), 
                       ('find_all', [{'tag': ['li',], 'id': re.compile(r"^post-\d+")}])]),
         'categories': dict([('find', [{'tag': ['li'], 'id': ['menu-item-314']}]), 
                             ('find_all', [{'tag': ['li']}])]), 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '(?:flags\/||d{4}\/\d{2}\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': dict([('find', [{'tag': ['span'], 'class': ['Qlty']}]), 
                              ('get_text', [{'tag': '', '@STRIP': True}])]),  
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], 
                                           '@ARG': 'href', '@TEXT': '(?:/|=)(\d+)'}])]), 
         'year': dict([('find', [{'tag': ['span'], 'class': ['Year']}]), 
                       ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]), 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tag': ['li'], 'class': ['sel-temp']}]}, 
         'season_num': dict([('find', [{'tag': ['a']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]), 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['article']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['section'], 'class': ['player']}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real-*|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 18, 
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
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all", c_type='peliculas', 
                         url=host + "cartelera-peliculas/page/1", thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", c_type='series', 
                         url=host + "cartelera-series/page/1", thumbnail=get_thumb("all", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Géneros", action="section", url=host, c_type='series', 
                         thumbnail=get_thumb("genres", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url= host, c_type='search', 
                         thumbnail=get_thumb("search", auto=True)))
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def section(item):
    logger.info()
    
    return AlfaChannel.section(item, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    
    if item.extra == 'alpha':
        findS['find'] = {'find_all': [{'tag': ['tr']}]}
        findS['year'] = dict([('find', [{'tag': ['td'], 'class': ['MvTbTtl']}]), 
                              ('find_next', [{'tag': ['td']}]), 
                              ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])])
    
    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            if item.extra == 'alpha':
                if not elem.find("a", class_="MvTbImg"): continue
                elem_json['url'] = elem.find("a", class_="MvTbImg").get("href", "")
                elem_json['title'] = elem.find("td", class_="MvTbTtl").get_text(strip=True)
            else:
                elem_json['url'] = elem.a.get("href", "")
                elem_json['title'] = elem.h2.get_text(strip=True)
            elem_json['thumbnail'] = elem.find("img")
            elem_json['thumbnail'] = elem_json['thumbnail']["data-src"] if elem_json['thumbnail']\
                                               .has_attr("data-src") else elem_json['thumbnail']["src"]
            if elem.find('span', class_="Qlty"): elem_json['quality'] = '*%s' \
                                                 % elem.find('span', class_="Qlty").get_text(strip=True).replace('Desconocido', '')
            elem_json['year'] = elem_json.get('year', AlfaChannel.parse_finds_dict(elem, findS.get('year', {}), year=True, c_type=item.c_type))
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        
        matches.append(elem_json.copy())
    
    return matches


def seasons(item):
    logger.info()
    
    return AlfaChannel.seasons(item, matches_post=seasons_matches, **kwargs)


def seasons_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        
        try:
        
            elem_json['season'] = elem.a['data-season']
            elem_json['title'] = "Temporada %s" %elem_json['season']
            elem_json['url'] = AlfaChannel.doo_url
            elem_json['headers'] = {'Referer': item.url}
            elem_json['post'] = 'action=action_select_season&season=%s&post=%s' % (elem_json['season'], elem.a['data-post'])
        
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


def episodesxseason(item):
    logger.info()
    
    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    kwargs['matches_post_get_video_options'] = findvideos_matches
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        
        try:
            if 'href' not in str(elem): continue
            elem_json['url'] = elem.a.get('href', '')
            elem_json['title'] = elem.find("h2", class_="entry-title").get_text(strip=True)
            try:
                elem_json['season'], elem_json['episode'] = elem.find("span", class_="num-epi").get_text(strip=True).split('x')
                elem_json['season'] = int(elem_json['season'] or 1)
                elem_json['episode'] = int(elem_json['episode'] or 1)
                if elem_json['season'] != item.contentSeason: continue
            except:
                continue
            elem_json['thumbnail'] = elem.find("img").get('src', '')
        except:
            logger.error(elem)
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
    
    videos = matches_int[0].find_all('div', id=re.compile(r"^options-\d"))
    for x , value in enumerate(videos):
        videos[x] = value.iframe['data-src']
    langs = matches_int[0].find_all('span', class_='server')
    for x , value in enumerate(langs):
        langs[x] = value.text.strip().replace('-', '')
    
    elem_json = {}
    
    for url, lang in zip(videos, langs): 
        elem_json['url'] = url
        elem_json['language'] = lang
        elem_json['url'] = AlfaChannel.create_soup( elem_json['url'], referer=item.url).find("div", class_="Video").iframe.get("src", '')

        matches.append(elem_json.copy())

    return matches, {}


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    try:
        texto = texto.replace(" ", "+")
        
        if texto:
            item.url += "?s=" + texto
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

