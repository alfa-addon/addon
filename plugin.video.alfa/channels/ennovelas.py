# -*- coding: utf-8 -*-
# -*- Channel Ennovelas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import traceback

from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel

IDIOMAS = {'la': 'LAT', 'sub': 'VOSE', 'es': 'CAST'}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_quality_movies = []
list_quality_tvshow = ['HDTV', 'HDTV-720p', 'WEB-DL 1080p', '4KWebRip']
list_servers = ['fembed', 'mega', 'yourupload', 'streamsb', 'mp4upload', 'mixdrop', 'uqload']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'ennovelas', 
             'host': config.get_setting("current_host", 'ennovelas', default=''), 
             'host_alt': ["https://www.zonevipz.com/"], 
             'host_black_list': ["https://www.ennovelas.com/"], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*rel="?stylesheet"?'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant_if_proxy': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/category'
language = ['LAT']
url_replace = []

finds = {'find': {'find': [{'tag': ['div'], 'class': ['section-content']}], 
                  'find_all': [{'tag': ['div'], 'class': ['video-post']}]},
         'categories': {}, 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '(?:flags\/||d{4}\/\d{2}\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\&page=\d+', '&page=%s']], 
         'last_page': {'find': [{'tag': ['div'], 'class': ['paging']}], 
                       'find_all': [{'tag': ['a'], '@POS': [-2]}], 'get_text': [{'tag': '', '@STRIP': True}]}, 
         'year': {}, 
         'season_episode': {}, 
         'seasons': {}, 
         'season_num': {}, 
         'seasons_search_num_rgx': [['(?i)\+(\d+)(?:\+temp[^$]*)?$', None]], 
         'seasons_search_qty_rgx': None, 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['div'], 'class': ['videobox']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real-*|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': True, 
                      'duplicates': [['(?i)\+\d+(?:\+temp[^$]*)?$', '']]},
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", 
                         url=host + "?op=categories_all&per_page=30&page=1",
                         c_type='series', thumbnail=get_thumb("all", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios" , action="list_all", 
                         url= host + "just_added.html",
                         c_type='episodios', thumbnail=get_thumb('new_episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?op=categories_all&name=",
                         c_type='search', thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_movies + list_quality_tvshow)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = {'find_all': [{'tag': ['div'], 'class': ['videobox']}]}

    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if item.c_type == 'episodios':
                elem_json['title'] = elem.find('a', style=True).get_text(strip=True)
                patron = '(?i)\s+(\d+)\s+temp\w*\s+(?:-\s+)?cap\w+\s+(\d+)'
                if scrapertools.find_single_match(elem_json['title'], patron):
                    elem_json['season'], elem_json['episode'] = scrapertools.find_single_match(elem_json['title'], patron)
                    elem_json['title'] = re.sub(patron, '', elem_json['title'])
                
                if not elem_json.get('season'):
                    patron = '(?i)\s+-\s+cap\w+\s+(\d+)'
                    if scrapertools.find_single_match(elem_json['title'], patron):
                        elem_json['season'] = 1
                        elem_json['episode'] = scrapertools.find_single_match(elem_json['title'], patron)
                        elem_json['title'] = re.sub(patron, '', elem_json['title'])

                elem_json['season'] = int(elem_json['season'] or 1)
                elem_json['episode'] = int(elem_json['episode'] or 1)

            elem_json['url'] = elem.a.get("href", "")
            if not elem_json.get('title'): elem_json['title'] = re.sub('\s+\d+$', '', elem.find('p').get_text(strip=True))
            elem_json['thumbnail'] = elem.find("div", style=True).get("style", "")
            elem_json['thumbnail'] = scrapertools.find_single_match(elem_json['thumbnail'], ":\s*url\('*([^']+)'*\)")

        except:
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


def episodesxseason(item):
    logger.info()
    
    item.url = '%s&op=search&per_page=9999&page=1' % item.url.replace('category/', '?cat_name=').replace('+', '%20')

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['title'] = elem.find('a', style=True).get_text(strip=True)
            patron = '(?i)\s+(\d+)\s+temp\w*\s+(?:-\s+)?cap\w+\s+(\d+)'
            if scrapertools.find_single_match(elem_json['title'], patron):
                elem_json['season'], elem_json['episode'] = scrapertools.find_single_match(elem_json['title'], patron)
                elem_json['title'] = re.sub(patron, '', elem_json['title'])
            
            if not elem_json.get('season'):
                patron = '(?i)\s+-\s+cap\w+\s+(\d+)'
                if scrapertools.find_single_match(elem_json['title'], patron):
                    elem_json['season'] = 1
                    elem_json['episode'] = scrapertools.find_single_match(elem_json['title'], patron)
                    elem_json['title'] = re.sub(patron, '', elem_json['title'])

            elem_json['season'] = int(elem_json['season'] or 1)
            elem_json['episode'] = int(elem_json['episode'] or 1)

            elem_json['url'] = elem.a.get("href", "")

            elem_json['thumbnail'] = elem.find("div", style=True).get("style", "")
            elem_json['thumbnail'] = scrapertools.find_single_match(elem_json['thumbnail'], ":\s*url\('*([^']+)'*\)")
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if elem_json.get('season', 0) != item.contentSeason: continue
        if not elem_json.get('url', ''): continue
 
        matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()
    
    item.matches = []
    kwargs['soup'] = False

    data = AlfaChannel.create_soup(item.url, **kwargs).data

    patron = 'src\s*:\s*"([^"]+).*?res\s*:\s*(\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    #logger.error(matches)
    #logger.error(data)
    
    for scrapedurl, scrapedquality in matches:
        elem_json = {}

        elem_json['url'] = scrapedurl
        elem_json['quality'] = '*%s' % scrapedquality
 
        if not elem_json['url']: continue

        item.matches.append(elem_json.copy())

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto):
    logger.info()
    
    try:
        texto = texto.replace(" ", "+")
        item.url = host + "?op=categories_all&name=" + texto

        if texto:
            item.c_type = "search"
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
