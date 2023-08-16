# -*- coding: utf-8 -*-
# -*- Channel AnimeFLV -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

from modules import renumbertools

IDIOMAS = AlfaChannelHelper.IDIOMAS_ANIME
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS
forced_proxy_opt = None

canonical = {
             'channel': 'animeflv', 
             'host': config.get_setting("current_host", 'animeflv', default=''), 
             'host_alt': ["https://www3.animeflv.net/"], 
             'host_black_list': ["https://animeflv.sh/", "https://www1.animeflv.bz/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'cf_assistant_get_source': True, 'CF_stat': True, 
             'CF': True, 'CF_test': True, 'alfa_s': True
            }

clone = config.get_setting("use_clone", channel="animeflv")
if clone:
    clone = False
    config.set_setting("use_clone", clone, channel="animeflv")
"""
'host_alt': ["https://www3.animeflv.net/", "https://animeflv.sh/"], 
host = canonical['host'] if canonical['host'] and canonical['host'] not in canonical['host_alt'] \
                         else canonical['host_alt'][0] if not clone else canonical['host_alt'][1]
"""
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/anime'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['ListAnimes']}]), 
                       ('find_all', [{'tag': ['article'], 'class': ['Anime']}])]), 
         'categories': {}, 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\&page=\d+', '&page=%s']], 
         'last_page': dict([('find', [{'tag': ['ul'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['li'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),  
         'year': {}, 
         'season_episode': {}, 
         'seasons': {},
         'season_num': {}, 
         'seasons_search_num_rgx': [['(?i)-(\d+)\w*-(?:season)', None]], 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['script'], 'string': re.compile('var\s*episodes\s*=\s*\[')}]), 
                           ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': 'var\s*episodes\s*=\s*([^;]+);', '@EVAL': True}])]) \
                           if not clone else \
                     dict([('find', [{'tag': ['ul'], 'class': ['ListCaps']}]), 
                           ('find_all', [{'tag': ['li'], 'class': ['fa-play-circle']}])]),
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['script'], 'type': ['text/javascript'], 'string': re.compile('var\s*videos\s*=\s*\{')}]), 
                             ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': 'var\s*videos\s*=\s*([^;]+);', '@JSON': 'DEFAULT'}])]) \
                             if not clone else \
                       dict([('find', [{'tag': ['ul'], 'class': ['CapiTnv']}]), 
                             ('find_all', [{'tag': ['li']}])]),
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', ''], ['(?i)\d+\w*\s*season', ''], ['(?i)ova|anime|especial\w*\s*|special\w*\s*|\s*\(tv\)', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'join_dup_episodes':False, 'IDIOMAS_TMDB': {0: 'es', 1: 'ja', 2: 'es'}}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    order = 'title' if not clone else '3'

    itemlist.append(Item(channel=item.channel, action="list_all", title="Últimos Episodios",
                         url=host, thumbnail="https://i.imgur.com/w941jbR.png", c_type='episodios'))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Últimos Animes",
                         url=host, thumbnail="https://i.imgur.com/hMu5RR7.png", c_type='series'))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Animes",
                         url=host + "browse?order=%s&page=1" % order, thumbnail='https://i.imgur.com/50lMcjW.png', 
                         c_type='series', extra="list"))

    itemlist.append(Item(channel=item.channel, action="section", title=" - [COLOR paleturquoise]Por Género[/COLOR]",
                         url=host + "browse", thumbnail='https://i.imgur.com/Xj49Wa7.png',
                         c_type='series', extra="genre" if not clone else "genres"))

    itemlist.append(Item(channel=item.channel, action="section", title=" - [COLOR paleturquoise]Por Tipo[/COLOR]",
                         url=host + "browse", thumbnail='https://i.imgur.com/0O5U8Y0.png',
                         c_type='series', extra="type" if not clone else "Tipo"))

    itemlist.append(Item(channel=item.channel, action="section", title=" - [COLOR paleturquoise]Por Año[/COLOR]",
                         url=host + "browse", thumbnail='https://i.imgur.com/XzPIQBj.png',
                         c_type='series', extra="year"))

    itemlist.append(Item(channel=item.channel, action="section", title=" - [COLOR paleturquoise]Por Estado[/COLOR]",
                         url=host + "browse", thumbnail='https://i.imgur.com/7LKKjSN.png',
                         c_type='series', extra="status"))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail='https://i.imgur.com/4jH5gpT.png'))


    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                         folder=False, thumbnail=get_thumb("next.png")))

    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                         thumbnail=get_thumb("setting_0.png")))

    itemlist = renumbertools.show_option(item.channel, itemlist)
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def configuracion(item):
    from platformcode import platformtools

    ret = platformtools.show_channel_settings()

    return platformtools.itemlist_refresh()


def section(item):
    logger.info()

    findS = finds.copy()

    if not clone:
        findS['categories'] = dict([('find', [{'tag': ['select'], 'name': ['%s[]' % item.extra]}]), 
                                    ('find_all', [{'tag': ['option']}])])
    else:
        findS['categories'] = dict([('find', [{'tag': ['span'], 'class': ['load_%s' % item.extra.replace('genres', 'gneres')]}]), 
                                    ('find_previous', [{'tag': ['div'], 'class': ['btn-group']}]), 
                                    ('find_all', [{'tag': ['label']}])])

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    
    if item.extra == "list":
        findS['controls']['jump_page'] = True
        if not clone:
            item.last_page_correction = -10
        elif not item.last_page: item.last_page = 158

    elif item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['ul'], 'class': ['ListEpisodios']}]), 
                              ('find_all', [{'tag': ['li']}])])

    elif item.extra and item.extra not in ["novedades"] and not item.last_page:
        item.url = item.url.replace(host, '')
        if not clone:
            item.url = '%sbrowse?%s[]=%s&order=default&page=1' % (host, item.extra, item.url)
            item.url = item.url.replace('[', '%5B').replace(']', '%5D')
        else:
            item.url = '%sbrowse?%s=%s&order=1&page=1' % (host, item.extra, item.url)

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
                elem_json['url'] = elem.a.get('href', '')
                elem_json['title'] = elem.find('strong', class_='Title').get_text(strip=True)
                elem_json['thumbnail'] = elem.find('img').get('src', '')
                try:
                    elem_json['season'] = int(scrapertools.find_single_match(elem_json['title'], '(?i)(\d+)\w*\s*season') or 1)
                    elem_json['episode'] = int(scrapertools.find_single_match(elem.find('span', class_='Capi').get_text(strip=True), '\d+') or 1)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'

            else:
                elem_json['url'] = elem.a.get('href', '')
                elem_json['mediatype'] = elem.find("span", class_="Type").get_text(strip=True)
                elem_json['mediatype'] = 'tvshow' if tv_path in elem_json['url'] and not 'Película' in elem_json['mediatype'] else 'movie'
                elem_json['thumbnail'] = elem.find("img").get('src', '')
                info = elem.find("div", class_="Description").get_text('|', strip=True).split('|')
                elem_json['title'] = info[0]
                elem_json['plot'] = info[-2] if not info[-2].isdigit() else ''

                if elem_json['mediatype'] == 'tvshow':
                    try:
                        elem_json['context'] = renumbertools.context(item)
                        season = int(scrapertools.find_single_match(elem_json['title'], '(?i)(\d+)\w*\s*season') or 1)
                        if season > 1:
                            elem_json['season'] = season
                            elem_json['mediatype'] = 'season'
                    except Exception:
                        pass

            elem_json['quality'] = '*'
        
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
    if not clone:
        soup = AHkwargs.get('soup', '')
        try:
            info = eval(scrapertools.find_single_match(str(soup), 'var\s*anime_info\s*=\s*([^;]+);'))
        except:
            info = ['', '', item.url.split('/')[-1], '']

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if isinstance(elem, list):
                elem_json['url'] = '%sver/%s-%s' % (host, info[2], elem[0])
                elem_json['episode'] = int(elem[0] or 1)
            else:
                elem_json['url'] = elem.a.get('href', '')
                elem_json['episode'] = int(scrapertools.find_single_match(elem.a.p.get_text(strip=True), '\d+') or 1)
                elem_json['thumbnail'] = elem.a.img.get('src', '')

            elem_json['season'] = item.contentSeason
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 
                                                               elem_json['season'], elem_json['episode'])
            elem_json['title'] = "{}x{:02d}".format(season, episode)

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

    if not clone and 'ver/' not in item.url:
        item.url = item.url.split('/')[-1]
        item.url = "%sver/%s-1" % (host, item.url)
    elif clone and item.contentType != 'episode':
        item.url = item.url.split('/')[-1]
        item.url = "%s%s-1" % (host, item.url)

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    servers = {'dood': 'doodstream', 'stape': 'streamtape', 'aparat': 'aparatcam', 'fembed': '', 'embedsito': '',
               'our server': '', 'xstreamcdn': '', 'animeid': '', 'openupload': ''}

    if isinstance(matches_int, _dict):
        for lang, links in list(matches_int.items()):

            for elem in links:
                elem_json = {}
                #logger.error(elem)

                try:
                    elem_json['server'] = elem.get('server', '').lower()
                    elem_json['server'] = servers.get(elem_json['server'], elem_json['server'])
                    if not elem_json['server']: continue

                    elem_json['url'] = elem.get('code', '')
                    if 'redirector' in elem_json['url']:
                        new_data = AlfaChannel.create_soup(elem_json['url'], soup=False, **kwargs).data
                        elem_json['url'] = scrapertools.find_single_match(new_data, 'window.location.href\s*=\s*"([^"]+)"')
                    elif 'animeflv.net/embed' in elem_json['url'] or 'gocdn.html' in elem_json['url']:
                        elem_json['url'] = elem_json['url'].replace('embed', 'check').replace('gocdn.html#', 'gocdn.php?v=')
                        json_data = AlfaChannel.create_soup(elem_json['url'], soup=False, json=True, **kwargs).json
                        elem_json['url'] = json_data.get('file', '')

                    elem_json['language'] = IDIOMAS.get(lang.lower(), "VOSE")
                    elem_json['language'] = '*%s' % elem_json['language']

                    elem_json['title'] = '%s'

                    matches.append(elem_json.copy())

                except Exception:
                    logger.error(elem)
                    logger.error(traceback.format_exc())
                    continue

    else:
        for elem in matches_int:
            elem_json = {}
            #logger.error(elem)

            try:
                elem_json['server'] = elem.get('title', '').lower()
                elem_json['server'] = servers.get(elem_json['server'], elem_json['server'])
                if not elem_json['server']: continue

                elem_json['url'] = elem.get('data-video', '')
                if not elem_json['url'].startswith('http'): elem_json['url'] = 'https:%s' % elem_json['url']
                if 'redirector' in elem_json['url']:
                    new_data = AlfaChannel.create_soup(elem_json['url'], soup=False, **kwargs).data
                    elem_json['url'] = scrapertools.find_single_match(new_data, 'window.location.href\s*=\s*"([^"]+)"')
                elif 'animeflv.net/embed' in elem_json['url'] or 'gocdn.html' in elem_json['url']:
                    elem_json['url'] = elem_json['url'].replace('embed', 'check').replace('gocdn.html#', 'gocdn.php?v=')
                    json_data = AlfaChannel.create_soup(elem_json['url'], soup=False, json=True, **kwargs).json
                    elem_json['url'] = json_data.get('file', '')

                elem_json['language'] = ['VOSE']

                elem_json['title'] = '%s'

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


def get_page_num(item):
    logger.info()
    # Llamamos al método que salta al nº de página seleccionado

    return AlfaChannel.get_page_num(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        texto = texto.replace(" ", "+")
        item.url = "%sbrowse?q=%s" % (host, texto)
        #item.post = "value=%s&limit=100" % texto

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
            item.c_type = 'series'
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
