# -*- coding: utf-8 -*-
# -*- Channel Pelitorrent -*-
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

import datetime

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_T
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_T
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'pelitorrent', 
             'host': config.get_setting("current_host", 'pelitorrent', default=''), 
             'host_alt': ["https://pelitorrent.com/"], 
             'host_black_list': ["https://pelitorrent.xyz/", "https://www.pelitorrent.com/"], 
             'pattern': "<link\s*rel='stylesheet'\s*id='menu-icons-extra-css'\s*href='([^']+)'", 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
host_torrent = host
channel = canonical['channel']
categoria = channel.capitalize()
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)     # Actualización sólo últ. Temporada?
min_temp = modo_ultima_temp if not modo_ultima_temp else 'continue'

timeout = config.get_setting('timeout_downloadpage', channel)
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/movies"
tv_path = '/series'
language = ['CAST']
url_replace = []

finds = {'find': dict([('find', [{'tag': ['div'], 'class': ['aa-cn']}]), 
                       ('find_all', [{'tag': ['article'], 'class': ['movies']}])]), 
         'sub_menu': {}, 
         'categories': {}, 
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': [], 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']],  
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2]}]), 
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'class': ['choose-season']}]), 
                       ('find_all', [{'tag': ['li'], 'class': ['sel-temp']}])]), 
         'season_num': {}, 
         'seasons_search_num_rgx': [], 
         'seasons_search_qty_rgx': [], 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['article'], 'class': ['episodes']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'profile_labels': {}, 
         'findvideos': dict([('find', [{'tag': ['div'], 'class': ['download-links']}, 
                                       {'tag': ['tbody']}]), 
                             ('find_all', [{'tag': ['tr']}])]), 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*imax', ''],
                         ['(?i)[\[|\(]?\d{3,4}p[\]|\)]?|[\[|\(]?(?:4k|3d|uhd|hdr)[\]|\)]?', ''], 
                         ['(?i)[-|\(]?\s*HDRip\)?|microHD|\(?BR-LINE\)?|\(?HDTS-SCREENER\)?', ''], 
                         ['(?i)\(?BDRip\)?|\(?BR-Screener\)?|\(?DVDScreener\)?|\(?TS-Screener\)?|[\(|\[]\S*\.*$', ''],
                         ['(?i)Castellano-*|Ingl.s|Trailer|Audio|\(*SBS\)*|\[*\(*dvd\s*r\d*\w*\]*\)*|[\[|\(]*dv\S*[\)|\]]*', ''], 
                         ['(?i)Dual|Subt\w*|\(?Reparado\)?|\(?Proper\)?|\(?Latino\)?|saga(?:\s*del)?', ''], 
                         ['(?i)(?:\s*&#8211;)?\s*temp.*?\d+.*', ''], ['\d?\d?&#.*', ''], ['\d+[x|×]\d+.*', ''], 
                         ['[\(|\[]\s*[\)|\]]', ''], ['(?i)(?:libro|volumen)?\s+\d{1,2}$', ''], 
                         ['(?i)\s*-?\s*\d{1,2}.?\s*-?\s*Temp\w*[^$]*$', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'min_temp': min_temp, 'url_base64': True, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'host_torrent': host_torrent, 'duplicates': [], 'join_dup_episodes': False},
         'timeout': timeout * 5}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="sub_menu", url=host, 
                         thumbnail=get_thumb("now_playing.png"), extra="novedades"))

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=host, 
                         thumbnail=get_thumb('channels_movie.png'), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Series',  action='sub_menu', url=host, 
                         thumbnail=get_thumb('channels_tvshow.png'), c_type='series'))

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
    year = datetime.datetime.now().year
    c_type = 'movies' if item.c_type == 'peliculas' else item.c_type
    type_ = '?type=%s' % c_type

    if item.extra in ['novedades']:
        itemlist.append(Item(channel=item.channel, title='Películas', 
                             url=host + 'peliculas/estrenos-%s/?type=movies' % year, action='list_all',
                             thumbnail=get_thumb('channels_movie.png'), c_type='peliculas', extra=item.extra))

        itemlist.append(Item(channel=item.channel, title='Series', 
                             url=host + 'peliculas/estrenos-%s/?type=series' % year, action='list_all',
                             thumbnail=get_thumb('channels_tvshow.png'), c_type='series', extra=item.extra))

    if item.c_type in ['peliculas', 'series']:
        itemlist.append(Item(channel=item.channel, title='Todas las %s' % item.c_type.title(), 
                             url=host + 'torrents-%s/' % item.c_type, action='list_all',
                             thumbnail=item.thumbnail, c_type=item.c_type))

        itemlist.append(Item(channel=item.channel, title='Más Vistas', 
                             url=AlfaChannel.doo_url, post='action=action_tr_movie_category&limit=48&post=%s&cate=all&mode=2' % c_type, 
                             action='list_all', thumbnail=item.thumbnail, c_type=item.c_type, extra='vistas'))

        if item.c_type in ['peliculas']:
            itemlist.append(Item(channel=item.channel, title='Clásicas', 
                                 url=host + '%s/cine-clasico/' % item.c_type, action='list_all',
                                 thumbnail=item.thumbnail, c_type=item.c_type))

        itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]Por Género[/COLOR]', 
                             url=host, action='section',
                             thumbnail=get_thumb('genres.png'), c_type=item.c_type, extra='Género'))

        itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]Por Año[/COLOR]', 
                             url=host, action='section',
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, extra='Año'))

        itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]Por [A-Z][/COLOR]', 
                             url=host, action='section',
                             thumbnail=get_thumb('channels_movie_az.png'), c_type=item.c_type, extra='Alfabético'))

    if item.c_type in ['peliculas']:
        itemlist.append(Item(channel=item.channel, title=' - [COLOR paleturquoise]Por Calidad[/COLOR]', 
                             url=host, action='section',
                             thumbnail=get_thumb('search_star.png'), c_type='peliculas', extra='Calidad'))

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()
    extra = {'Género': '29', 'Calidad': '133383'}
    c_type = 'movies' if item.c_type == 'peliculas' else item.c_type
    type_ = '?type=%s' % c_type

    if item.extra in extra:
        findS['categories'] = dict([('find', [{'tag': ['li'], 'id': ['menu-item-%s' % extra[item.extra]]}]), 
                                    ('find_all', [{'tag': ['li']}])])
        if item.extra == 'Género':
            findS['url_replace'] = [['($)', type_]]

    elif item.extra == 'Año':
        findS['categories'] = dict([('find', [{'tag': ['section'], 'id': ['torofilm_movies_annee-3']}]), 
                                    ('find_all', [{'tag': ['li']}])])
        findS['controls']['reverse'] =  True

    elif item.extra == 'Alfabético':
        itemlist = []

        for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                      'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:

            itemlist.append(item.clone(action="list_all", title=letra, url=item.url + 'letters/%s/' % letra))

        return itemlist

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()

    if item.extra in ['vistas']:
        findS['find'] = {'find_all': [{'tag': ['article'], 'class': ['post']}]}
                
    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, generictools=True, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['title'] = elem.find('h2').get_text(strip=True)
            if elem.find('img', class_=True): elem_json['thumbnail'] = elem.find('img', class_=True).get('src', '')
            if elem.find('span', class_='post-ql'): elem_json['quality'] = '*%s' % elem.find('span', class_='post-ql').get_text(strip=True)
            if elem.find('span', class_='post-ql') and elem.find('span', class_='post-ql').find('img'):
                elem_json['language'] = '*%s' % elem.find('span', class_='post-ql').find('img').get('src', '')
            elem_json['year'] = elem.find('span', class_='year').get_text(strip=True) if elem.find('span', class_='year') else '-'
            elem_json['url'] = elem.find('a', class_='lnk-blk').get('href', '')

            if item.c_type == 'peliculas' and movie_path not in elem_json['url']: continue
            if item.c_type == 'series' and tv_path not in elem_json['url']: continue

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url'): 
            continue

        matches.append(elem_json.copy())

    return matches


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item, matches_post=seasons_matches, **kwargs)


def seasons_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    soup = AHkwargs.get('soup', {})
    pass_list = {}
    pass_comments = soup.find('div', class_='comment-content').find_all(['h3', 'input']) if soup.find('div', class_='comment-content') else []

    for elem in pass_comments:
        #logger.error(elem)

        try:
            if 'h3' in str(elem):
                episode = quality = season = ''
                info = elem.get_text(strip=True)
                if not info: continue
                episode, quality, season = scrapertools.find_single_match(info, 
                                           '(?i)epi\w*\s*(\d{1,3})[^<]*(HDTV(?:-\d{3,4}p)?)[^<]*(\d{1,2})[^<]*temp\w*')
            else:
                if not info or not episode or not quality or not season: continue
                info = ''
                passw = elem.get('value', '') if elem.get('id', '') == 'txt_password' else ''
                if not passw: continue

                if not pass_list.get('%sx%s' % (season, episode)): 
                    pass_list.update({'%sx%s' % (season, episode): {quality: passw}})
                else:
                    pass_list['%sx%s' % (season, episode)][quality] = passw
                episode = quality = season = ''

        except:
            logger.error(elem)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['season'] = elem.find('a').get('data-season', 1)
            elem_json['url'] = AlfaChannel.doo_url
            elem_json['post'] = 'action=action_select_season&season=%s&post=%s' % (elem_json['season'], elem.find('a').get('data-post', ''))
            if pass_list: elem_json['password'] = pass_list

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

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

    kwargs['matches_post_get_video_options'] = findvideos_matches

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, generictools=True, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    pass_list = item.password or {}

    for elem in matches_int:
        elem_json = {}
        logger.error(elem)

        try:
            sxe = elem.find('span', class_='num-epi').get_text(strip=True).split('x')
            elem_json['season'] = int(sxe[0])
            if elem_json['season'] != item.contentSeason: continue
            elem_json['episode'] = int(sxe[1])

            elem_json['url'] = elem.a.get('href', '')
            elem_json['thumbnail'] = elem.find('img').get('src', '')
            last_episode_to_air = int(item.infoLabels['last_series_episode_to_air'].split('x')[1] \
                                      if item.infoLabels['last_series_episode_to_air'] else 1)
            if item.infoLabels['tmdb_id'] and host in elem_json['thumbnail'] \
                                          and item.infoLabels['number_of_seasons'] == elem_json['season'] \
                                          and (elem_json['episode'] > last_episode_to_air \
                                               #or elem.find('img').get('alt', '') in ['', 'Image '] \
                                               or 'noimg' in elem_json['thumbnail']):
                continue

            if pass_list.get('%sx%s' % (elem_json['season'], elem_json['episode'])):
                elem_json['password'] = pass_list['%sx%s' % (elem_json['season'], elem_json['episode'])]

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        elem_json['server'] = 'torrent'
        elem_json['language'] = item.language
        elem_json['quality'] = item.quality
        elem_json['size'] = ''
        elem_json['torrent_info'] = elem_json.get('torrent_info', '')

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
    soup = AHkwargs.get('soup', [])
    if soup.find('h4'): 
        sxe = ''
        if item.contentType in ['episode']:
            sxe = '%sx%s' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))
        if sxe in str(soup.find('h4')):
            item.password = soup.find('h4').find_next('input').get('value', '')

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        for x, td in enumerate(elem.find_all('td')):
            try:
                if x == 1:
                    elem_json['language'] = '*%s' % td.get_text(strip=True)
            
                if x == 2:
                    elem_json['quality'] = '*%s' % td.get_text(strip=True)

                if x == 3:
                    elem_json['url'] = td.a.get('href', '')

            except:
                logger.error(elem)
                logger.error(traceback.format_exc())

        elem_json['server'] = 'torrent'
        elem_json['size'] = ''
        elem_json['torrent_info'] = elem_json.get('torrent_info', '')
        elem_json['password'] = item.password

        if not elem_json.get('url', ''): 
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
            item.url = "%s?s=%s" % (host, texto)
            item.texto = texto
            item.c_type = 'search'
            return list_all(item)
        else:
            return []
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    year = datetime.datetime.now().year
    c_type = 'movies' if categoria in ['peliculas'] else categoria if categoria in ['series'] else ''
    type_ = '?type=%s' % c_type if c_type else ''

    try:
        if categoria in ['peliculas', 'series', 'torrent', '4k']:
            if categoria in ['peliculas', 'series', 'torrent']: item.url = host + 'peliculas/estrenos-%s/%s' % (year, type_)
            if categoria in ['4k']: item.url = host + 'peliculas/4kwebrip/?type=movies'
            item.c_type = categoria
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