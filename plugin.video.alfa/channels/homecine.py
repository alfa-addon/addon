# -*- coding: utf-8 -*-
# -*- Channel HomeCine -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = AlfaChannelHelper.IDIOMAS
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = []
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'homecine', 
             'host': config.get_setting("current_host", 'homecine', default=''), 
             'host_alt': ["https://www3.homecine.to/"], 
             'host_black_list': ["https://homecine.cc/", "https://www3.homecine.tv/", "https://homecine.tv/"], 
             'pattern': '<div\s*class="header-logo">[^>]*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ""
tv_path = 'series/'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['div'], 'class': ['movies-list']}]), 
                       ('find_all', [{'tag': ['div'], 'data-movie-id': re.compile(r"^\d+")}])]),
         'categories': {'find_all': [{'tag': ['li'], 'class': ['menu-item-object-category']}]}, 
         # 'categories': dict([('find', [{'tag': ['li'], 'id': ['menu-item-314']}]), 
                             # ('find_all', [{'tag': ['li']}])]), 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '(?:flags\/||d{4}\/\d{2}\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], 
                                           '@ARG': 'href', '@TEXT': 'page/(\d+)'}])]), 
         'year': dict([('find', [{'tag': ['a'], 'href': re.compile("/release-year/[0-9]+")}]), 
                       ('get_text', [{'strip': True, '@TEXT': '(\d+)'}])]), 
         'season_episode': '(?i)\s*Temporada\s*(\d+)\s*Capitulo\s*(\d+)', 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                          ('find_all', [{'tag': ['div'], 'class':['les-title']}])]),
         'season_num': {'find': [{'tag': ['a'], '@ARG': 'data-season'}]},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['div'], 'class': ['les-content']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'id': re.compile(r"^tab\d+")}]},
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real-*|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'profile_labels': {
                           },
         'controls': {'duplicates': [], 'cnt_tot': 40, 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 
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
    
    itemlist.append(Item(channel=item.channel,title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         c_type='peliculas', 
                         url='%s%s' % (host, 'peliculas-nuevas')
                         )
                    )
    
    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         c_type='peliculas', 
                         url='%s%s' % (host, 'peliculas-nuevas/')
                         )
                    )
    itemlist.append(Item(channel=item.channel,
                         title="Series",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         c_type='series', 
                         url='%s%s'% (host, 'series/')
                         )
                    )
    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         c_type='series', 
                         url='%s%s'% (host, 'series/')
                         )
                    )
    
    # itemlist.append(Item(channel=item.channel,
                         # title="Últimos Episodios",
                         # action="list_all",
                         # thumbnail=get_thumb('new episodes', auto=True),
                         # c_type='episodios', 
                         # url='%s%s'% (host, 'ver/')
                         # )
                    # )
    
    itemlist.append(Item(channel=item.channel,
                         title="Año",
                         action="anno",
                         thumbnail=get_thumb('year', auto=True),
                         # c_type='series', 
                         url=host
                         )
                    )
    
    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         url=host,
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search', 
                         )
                    )

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def section(item):
    logger.info()
    
    # return AlfaChannel.section(item, **kwargs)
    return AlfaChannel.section(item, matches_post=section_matches, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        
        try:
            
            elem_json['title'] = elem.a.get_text(strip=True)
            url = elem.a['href']
            url = url.split('/genre/')
            id = url[-1]
            if "series" in item.c_type:
                elem_json['url'] = "%spage/1?ptype=tvshows&tax_category[]=%s" %(item.url, id)
            else:
                elem_json['url'] = "%spage/1?ptype=post&tax_category[]=%s" %(item.url, id)
        
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
    while year >= 1922:
        itemlist.append(item.clone(title="%s" %year, action="list_all", url= "%srelease-year/%s" % (item.url,year)))
        year -= 1
    
    return itemlist


def list_all(item):
    logger.info()

    # return AlfaChannel.list_all(item, **kwargs)
    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            
            elem_json['info'] = elem['data-movie-id']
            elem_json['url'] = elem.a.get("href", "")
            elem_json['title'] = elem.h2.get_text(strip=True)
            elem_json['thumbnail'] = elem.img["data-original"] if elem.img.has_attr("data-original")\
                                     else elem.img["src"]
            elem_json['year'] =elem.find('a', href=re.compile("/release-year/[0-9]+")).get_text(strip=True) if elem.find('a', href=re.compile("/release-year/[0-9]+")) else '-' 
            
            if item.c_type == 'search' and not tv_path in elem_json['url']:
                elem_json['mediatype'] = 'movie'
        
        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        
        matches.append(elem_json.copy())
    
    return matches


def seasons(item):
    logger.info()
    
    # return AlfaChannel.seasons(item, **kwargs)
    return AlfaChannel.seasons(item, matches_post=seasons_matches, **kwargs)


def seasons_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        
        try:
        
            elem_json['season'] = elem.get_text(strip=True).replace('Season ', '')
            elem_json['title'] = "Temporada %s" %elem_json['season']
            elem_json['url'] = item.url
        
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
    
    sid = int(item.contentSeason or 1) - 1
    # season_id = 'season-%s' % sid
    logger.debug(matches_int[sid])
    
    for elem in matches_int[sid].find_all('a'):
        elem_json = {}
        
        try:
            elem_json['url'] = elem.get('href', '')
            elem_json['episode'] = elem.get_text(strip=True).replace('Episode ', '')
        
        except Exception:
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
    soup = AHkwargs.get('soup', {})
    
    idiomas = soup.find_all('a', href=re.compile(r"^#tab\d+"))
    
    for elem, lang in zip(matches_int, idiomas):
        elem_json = {}
        
        try:
            elem_json['url'] = elem.iframe.get("src", '')
            elem_json['language'] = lang.get_text('', strip=True).split("-")[-1]
            elem_json['server'] = ''
        
        except Exception:
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
    
    texto = texto.replace(" ", "+")
    item.url = item.url + '?s=' + texto
    
    try:
        if texto:
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# def newest(categoria, **AHkwargs):
    # logger.info()
    # kwargs.update(AHkwargs)
    
    # item = Item()
    # try:
        # if categoria in ['peliculas']:
            # item.url = host + 'peliculas'
        # elif categoria == 'infantiles':
            # item.url = host + 'genre/animacion/'
        # elif categoria == 'terror':
            # item.url = host + 'genre/terror/'
        # itemlist = list_all(item)
        # if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            # itemlist.pop()
    # except:
        # for line in sys.exc_info():
            # logger.error("{0}".format(line))
        # return []

    # return itemlist

