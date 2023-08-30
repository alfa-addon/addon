# -*- coding: utf-8 -*-
# -*- Channel EstrenosCinesaa -*-
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

IDIOMAS = AlfaChannelHelper.IDIOMAS
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'estrenoscinesaa', 
             'host': config.get_setting("current_host", 'estrenoscinesaa', default=''), 
             'host_alt': ["https://www.estrenoscinesaa.com/"], 
             'host_black_list': [], 
             'pattern': '<link\s*rel="shortcut\s*icon"\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
channel = canonical['channel']
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', channel)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', channel, default='0') if __comprueba_enlaces__ else ''

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "movies/"
tv_path = 'tvshows/'
epi_path = 'episodes/'
language = ['CAST']
url_replace = []


finds = {'find': dict([('find', [{'tagOR': ['div'], 'id': ['archive-content']}, 
                                 {'tag': ['div'], 'class': ['content']}]), 
                       ('find_all', [{'tag': ['article'], 'id': re.compile(r"^post-\d+")}])]), 
         'categories': dict([('find', [{'tag': ['nav'], 'class': ['genres']}]), 
                             ('find_all', [{'tag': ['li'], 'class': ['cat-item']}])]), 
         'search': {'find_all': [{'tag': ['div'], 'class': ['result-item']}]}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}, 
                                      {'tag': ['span']}]), 
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(?i)\d+\s*de\s*(\d+)'}])]),  
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['se-c']}])]), 
         'season_num': {}, 
         'season_url': host, 
         'seasons_search_num_rgx': [['(?i)-(\d+)\w*-(?:season)', None]], 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['se-c']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'id': re.compile(r"^source-player-\d+")}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 30, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'join_dup_episodes':False, 'check_links': str(__comprueba_enlaces_num__)}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='list_all', url=host + movie_path, 
                         thumbnail=get_thumb('channels_movie.png'), c_type='peliculas'))
    itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]por Género[/COLOR]',  action='section', 
                         url=host, thumbnail=get_thumb('genres.png'), extra='generos'))

    itemlist.append(Item(channel=item.channel, title='Series',  action='list_all', url=host + tv_path, 
                         thumbnail=get_thumb('channels_tvshow.png'), c_type='series'))
    itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]Últimos Episodios[/COLOR]',  action='list_all', 
                         url=host + 'episodes', thumbnail=get_thumb('search_tvshow.png'), c_type='episodios'))

    itemlist.append(Item(channel=item.channel, title='Productoras',  action='sub_menu', url=host, 
                         thumbnail=get_thumb('search_star.png'), extra='productoras'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search.png")))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                         folder=False, thumbnail=get_thumb("next.png")))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                         thumbnail=get_thumb("setting_0.png")))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def configuracion(item):
    from platformcode import platformtools

    ret = platformtools.show_channel_settings()

    return platformtools.itemlist_refresh()


def sub_menu(item):
    logger.info()

    itemlist = list()

    if item.extra in ['productoras']:
        itemlist.append(Item(channel=item.channel, title='Marvel', url=host + 'genre/marvel/', action='list_all',
                             thumbnail=get_thumb('search_star.png'), c_type=item.c_type, extra='generos'))

        itemlist.append(Item(channel=item.channel, title='D.C', url=host + 'genre/d-c/', action='list_all',
                             thumbnail=get_thumb('search_star.png'), c_type=item.c_type, extra='generos'))

        itemlist.append(Item(channel=item.channel, title='StarWars', url=host + 'genre/starwars/', action='list_all',
                             thumbnail=get_thumb('search_star.png'), c_type=item.c_type, extra='generos'))

        itemlist.append(Item(channel=item.channel, title='Netflix', url=host + 'genre/netflix/', action='list_all',
                             thumbnail=get_thumb('search_star.png'), c_type=item.c_type, extra='generos'))

    return itemlist


def section(item):
    logger.info()

    return AlfaChannel.section(item, **kwargs)


def list_all(item):
    logger.info()
                
    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if item.c_type == 'episodios':
                try:
                    elem_json['url'] = elem.find('div', class_='season_m').a.get("href", "")
                    if not scrapertools.find_single_match(elem_json['url'], '(?i)(\d+)x(\d+)'): continue
                    elem_json['season'] = int(scrapertools.find_single_match(elem_json['url'], '(?i)(\d+)x\d+') or 1)
                    elem_json['episode'] = int(scrapertools.find_single_match(elem_json['url'], '(?i)\d+x(\d+)') or 1)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'
                elem_json['title'] = elem.find('div', class_='poster').img.get("alt", "").split(':')[0]
                elem_json['go_serie'] = {'url': re.sub('(?i)-(\d+)x(\d+)', '', elem_json['url']).replace(epi_path, tv_path)}

            elif item.c_type == 'search':
                elem_json['url'] = elem.a.get("href", "")
                elem_json['title'] = elem.img.get("alt", "")
                elem_json['year'] = elem.find("span", class_="year").get_text(strip=True) or '-'

            else:
                elem_json['url'] = elem.a.get("href", "")
                elem_json['year'] = scrapertools.find_single_match(elem.find('div', class_='metadata')\
                                                .get_text('|', strip=True), '(\d{4})\|') or '-'
                elem_json['plot'] = elem.find('div', class_='texto').get_text(strip=True)
                elem_json['title'] = elem.find('h3').get_text(strip=True)

            if item.c_type == 'peliculas' and movie_path not in elem_json['url']: continue
            if item.c_type == 'series' and tv_path not in elem_json['url']: continue
            if item.c_type == 'episodios' and epi_path not in elem_json['url']: continue
            elem_json['mediatype'] = 'movie' if movie_path in elem_json['url'] else (elem_json.get('mediatype') or 'tvshow')

            elem_json['thumbnail'] = elem.img.get("src", "")

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url'): continue

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

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, generictools=True, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        if elem.find("span", class_="se-t").get_text(strip=True) != str(item.contentSeason): continue

        epi_list = elem.find("ul", class_="episodios")
        for epi in epi_list.find_all("li"):
            #logger.error(epi)

            try:
                info = epi.find("div", class_="episodiotitle")
                elem_json['url'] = info.a.get("href", "")
                elem_json['season'] = item.contentSeason
                elem_json['episode'] = int(epi.find("div", class_="numerando").get_text(strip=True).split(" - ")[1] or 1)
                elem_json['title'] = "%sx%s - %s" % (elem_json['season'], str(elem_json['episode']).zfill(2), info.a.get_text(strip=True))

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

    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    soup = AHkwargs.get('soup', {})

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['url'] = elem.iframe.get('src', '') or elem.get_text(strip=True)
            elem_json['server'] = ''
            elem_json['title'] = '%s'

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())

        if not elem_json.get('url', '') or "mirrorace" in elem_json.get('url', '') or "waaw" in elem_json.get('url', ''):
            continue

        matches.append(elem_json.copy())

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

    texto = texto.replace(" ", "+")

    try:
        if texto:
            item.url = "%s/?s=%s" % (host, texto)
            item.texto = texto
            item.c_type = 'search'
            return list_all(item)
        else:
            return []
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
