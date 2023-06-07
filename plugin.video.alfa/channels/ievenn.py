# -*- coding: utf-8 -*-
# -*- Channel Ievenn -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

import re
import traceback
if not PY3: _dict = dict; from collections import OrderedDict as dict

from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel

IDIOMAS = {'es': 'CAST', 'en': 'VO'}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_quality_movies = ['DVDR', 'HDRip', 'VHSRip', 'HD', '2160p', '1080p', '720p', '4K', '3D', 'Screener', 'BluRay']
list_quality_tvshow = ['HDTV', 'HDTV-720p', 'WEB-DL 1080p', '4KWebRip']
list_servers = ['okru', 'youtube']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'ievenn', 
             'host': config.get_setting("current_host", 'ievenn', default=''), 
             'host_alt': ["https://ievenn.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/movie"
tv_path = '/show'
language = []
url_replace = []

finds = {'find': {'find_all': [{'tag': ['article']}]}, 
         'categories': {}, 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '(?:images\/|-)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['navigation pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], '@ARG': 'href', '@TEXT': '\/(\d+)\/'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['ul'], 'class': ['filter']}]), 
                          ('find_all', [{'tag': ['li']}])]), 
         'season_num': dict([('find', [{'tag': ['a']}]), 
                             ('get_text', [{'tag': '', '@STRIP': False}])]), 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'id': ['season-episodes']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['flickr item left home-thumb-item']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['div'], 'class': ['entry-media penci-entry-media']}]), 
                             ('find_all', [{'tag': ['iframe']}])]), 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 12, 
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

    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("cast", auto=True),
            title="Español",
            url=host + "seccion/cine/cine-espanol/", 
            c_type='peliculas'
        )
    )

    itemlist.append(
        Item(
            action="section",
            channel=item.channel,
            thumbnail=get_thumb("genres", auto=True),
            title=" - [COLOR paleturquoise]Por Género[/COLOR]",
            url=host,
            extra="Español",
            c_type='peliculas'
        )
    )

    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("vo", auto=True),
            title="Idioma Original",
            url=host + "seccion/cine/cine-english/", 
            c_type='peliculas'
        )
    )

    itemlist.append(
        Item(
            action="section",
            channel=item.channel,
            thumbnail=get_thumb("genres", auto=True),
            title=" - [COLOR paleturquoise]Por Género[/COLOR]",
            url=host,
            extra="VO",
            c_type='peliculas'
        )
    )
    """
    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("vo", auto=True),
            title="Kids Español",
            url=host + "seccion/kids/kids-espanol/", 
            c_type='peliculas'
        )
    )

    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("vo", auto=True),
            title="Kids Inglés",
            url=host + "seccion/kids/kids-english/", 
            c_type='peliculas'
        )
    )
    """
    itemlist.append(
        Item(
            action="search",
            channel=item.channel,
            thumbnail=get_thumb("search", auto=True),
            url=host + "?s=",
            title="Buscar...",
            c_type='peliculas'
        )
    )

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()
    
    if item.extra == "Español":
        findS['categories'] = dict([('find', [{'tag': ['li'], 'id': ['menu-item-2407931']}]), 
                                    ('find_all', [{'tag': ['li']}])])
    else:
        findS['categories'] = dict([('find', [{'tag': ['li'], 'id': ['menu-item-2407932']}]), 
                                    ('find_all', [{'tag': ['li']}])])

    return AlfaChannel.section(item, finds=findS, **kwargs)


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
            elem_json['url'] = elem.a.get('href', '')
            info = elem.find("h2").a.get_text(strip=True).split(" – ")
            elem_json['title'] = info[0]
            if len(info) == 3:
                elem_json['year'] = info[1]
                elem_json['language'] = '*%s' % IDIOMAS.get(info[2][:2].lower(), "LAT")
            else:
                elem_json['year'] = "-"
                elem_json['language'] = 'CAST'
            elem_json['thumbnail'] = "https:" + scrapertools.find_single_match(elem.a.get("style", ""), "url\(([^\)]+)\);")
            elem_json['quality'] = '*'

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json['url']: continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, generictools=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['url'] = elem.get('src', '')
            elem_json['server'] = ''
            elem_json['title'] = '%s'
            elem_json['quality'] = '*'

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): continue

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
        item.url += texto

        if texto:
            item.c_type = "peliculas"
            item.texto = texto
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    itemlist = []
    item = Item()
    item.c_type = "peliculas"
    
    try:
        if categoria in ['peliculas']:
            item.url = host + "seccion/cine/cine-espanol/"
        elif categoria == 'latino':
            item.url = host + "idioma/latino/"
        elif categoria == 'castellano':
            item.url = host + "idioma/castellano"
        elif categoria == 'infantiles':
            item.url = host + 'animacion'
        elif categoria == 'terror':
            item.url = host + 'terror'

        itemlist = list_all(item)
        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc())
        return []

    return itemlist