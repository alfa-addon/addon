# -*- coding: utf-8 -*-
# -*- Channel YTS -*-
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
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_T
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_T
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'yts', 
             'host': config.get_setting("current_host", 'yts', default=''), 
             'host_alt': ['https://en.yts-official.com', "https://en.yts.lu/"], 
             'host_black_list': ["https://ytstv.me/", "https://ytstvmovies.co/", "https://yts.mx/"], 
             'pattern': '<ul\s*class="nav-links">\s*<li>\s*<a\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'host_alt_findb': [1, 2, 9]
            }
host = canonical['host'] or canonical['host_alt'][0]
host_torrent = host
channel = canonical['channel']
categoria = channel.capitalize()

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "movie"
tv_path = 'tv'
language = ['VOS']
url_replace = []

finds = {'find': dict([('find', [{'tag': ['body']}]), 
                       ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'DEFAULT'}])]), 
         'sub_menu': {}, 
         'categories': {},
         'search': {},
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': [], 
         'next_page': {}, 
         'next_page_rgx': [['page\=\d+', 'page=%s']], 
         'last_page': dict([('find', [{'tag': ['body']}]), 
                            ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'total_pages|DEFAULT'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['body']}]), 
                          ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'seasons|DEFAULT'}])]), 
         'season_num': {},
         'seasons_search_num_rgx': [], 
         'seasons_search_qty_rgx': [], 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['body']}]), 
                           ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'hits|DEFAULT'}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['body']}]), 
                             ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'hits|DEFAULT'}])]), 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*imax|\s*Series?\s*\d{4}?|\s*Shows?\s*\d{4}?', ''],
                         ['(?i)[\[|\(]?\d{3,4}p[\]|\)]?|[\[|\(]?(?:4k|3d|uhd|hdr)[\]|\)]?', ''], 
                         ['(?i)[-|\(]?\s*HDRip\)?|microHD|\(?BR-LINE\)?|\(?HDTS-SCREENER\)?', ''], 
                         ['(?i)\(?BDRip\)?|\(?BR-Screener\)?|\(?DVDScreener\)?|\(?TS-Screener\)?|[\(|\[]\S*\.*$', ''],
                         ['(?i)Castellano-*|Ingl.s|Trailer|Audio|\(*SBS\)*|\[*\(*dvd\s*r\d*\w*\]*\)*|[\[|\(]*dv\S*[\)|\]]*', ''], 
                         ['(?i)Dual|Subt\w*|\(?Reparado\)?|\(?Proper\)?|\(?Latino\)?|saga(?:\s*del)?', ''], 
                         ['(?i)(?:\s*&#8211;)?\s*temp.*?\d+.*', ''], ['\d?\d?&#.*', ''], ['\d+[x|×]\d+.*', ''], 
                         ['[\(|\[]\s*[\)|\]]', ''], ['(?i)(?:libro|volumen)?\s+\d{1,2}$', ''], ['(?i)season\s*\d+\s*comp\w*\s*', ''], 
                         ['(?i)season\s*\d+\s*full\w*\s*epi\w*\s*', ''], ['(?i)\s*season\s*\d{1,2}\s*epi\w*\s*\d*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'url_base64': True, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 
                      'host_torrent': host_torrent, 'duplicates': []},
         'timeout': timeout}

AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = []
    plot = ''

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Películas", action="sub_menu", url=host, 
                         thumbnail=get_thumb("channels_movie.png"), c_type="peliculas", c_path=movie_path, contentPlot=plot))

    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu", url=host, 
                         thumbnail=get_thumb("channels_tvshow_hd.png"), c_type="series", c_path=tv_path, contentPlot=plot))

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

    itemlist = []

    if item.c_type == 'peliculas':
        itemlist.append(Item(channel=item.channel, title="[B]Buscar...[/B]", action="search", 
                         url=host + '?api=search&mode=movie&page=1&q=', thumbnail=get_thumb("search.png"), c_type="search", 
                         category=categoria, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Explorar Películas", 
                             action="list_all", url=item.url + "?api=popular&mode=movie&page=1&sort=primary_release_date.desc", 
                             thumbnail=get_thumb('popular.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    if item.c_type == 'series':
        itemlist.append(Item(channel=item.channel, title="[B]Buscar...[/B]", action="search", 
                         url=host + '?api=search&mode=tv&page=1&q=', thumbnail=get_thumb("search.png"), c_type="search", 
                         category=categoria, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Explorar Series", 
                             action="list_all", url=item.url + "?api=popular&mode=tv&page=1&sort=primary_release_date.desc", 
                             thumbnail=get_thumb('tvshows', auto=True), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Rating[/COLOR]" % item.c_type.title(), 
                         action="list_all", url=item.url + '?api=top_rated&mode=%s&page=1&sort=primary_release_date.desc' % item.c_path, 
                         thumbnail=get_thumb('top_rated.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Tendencia[/COLOR]" % item.c_type.title(), 
                         action="list_all", url=item.url + '?api=trending&mode=%s&page=1&sort=primary_release_date.desc&time=week' % item.c_path, 
                         thumbnail=get_thumb('news.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s en Proyección[/COLOR]" % item.c_type.title(), 
                         action="list_all", url=item.url + '?api=%s&mode=%s&page=1&sort=primary_release_date.desc' \
                         % ('now_playing' if item.c_path in ['movie'] else 'on_the_air', item.c_path), 
                         thumbnail=get_thumb('now_playing.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Género[/COLOR]" % item.c_type.title(), 
                         action="section", url=item.url, extra='Géneros', 
                         thumbnail=get_thumb('genres.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Año[/COLOR]" % item.c_type.title(), 
                         action="section", url=item.url + '?api=discover&mode=%s&page=1&sort=primary_release_date.desc&genre=0&year=' % item.c_path,  
                         extra='Año', thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Idiomas[/COLOR]" % item.c_type.title(), 
                         action="section", url=item.url, extra='Idiomas', 
                         thumbnail=get_thumb('channels_vos.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    if item.c_type == 'peliculas':
        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Estudios[/COLOR]" % item.c_type.title(), 
                             action="section", url=item.url, extra='Estudios', 
                             thumbnail=get_thumb('favorites.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Colecciones[/COLOR]" % item.c_type.title(), 
                             action="section", url=item.url, extra='Colecciones', 
                             thumbnail=get_thumb('channels_frequents.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    if item.c_type == 'series':
        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]%s por Plataformas[/COLOR]" % item.c_type.title(), 
                             action="section", url=item.url, extra='Networks', 
                             thumbnail=get_thumb('favorites.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    pattern_section = r'(?:)var\s*MENU\s*=\s*({[^;]+});'
    extras = {'Géneros': ['Genres', 'genres', 'discover'], 'Idiomas': ['Countries', 'origin', 'discover'], 
              'Estudios': ['Studios', 'company', 'discover'], 'Networks': ['Networks', 'network', 'discover'],
              'Colecciones': ['Collections', 'id', 'collection']}
    matches = {}

    if item.extra == 'Año':
        from platformcode.platformtools import dialog_numeric

        year = dialog_numeric(0, "Introduzca el Año de búsqueda", default="")
        item.url += year

        return list_all(item)
    
    else:
        response = AlfaChannel.create_soup(host, soup=False, json=False)

        if response.sucess:
            data = (scrapertools.find_single_match(response.data, pattern_section) or '{}')
            data = AlfaChannel.convert_script_to_json(data)

            if isinstance(data, _dict):
                data = data.get(item.c_path, {})
                if data:
                    for block in data:
                        if not extras.get(item.extra) or block.get('title', '') != extras[item.extra][0]: continue
                        for elem in block.get('items', []):
                            if elem.get('l', '') and elem.get('p', {}).get(extras[item.extra][1], ''):
                                value = elem['p'][extras[item.extra][1]]
                                matches[elem['l']] = '?api=%s&mode=%s&page=1&sort=primary_release_date.desc&year=0&%s=%s' \
                                                     % (extras[item.extra][2], item.c_path, extras[item.extra][1], value)

    return AlfaChannel.section(item, finds=findS, section_list=matches,**kwargs)


def list_all(item):
    logger.info()
                
    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    url_base_movie = '?api=torrents&mode=movie&name=%s&year=%s&quality=all'
    url_base_tv = '?api=tv_details&id=%s'

    for elem in matches_int.get('results', []) or matches_int.get('parts', []):
        elem_json = {}
        #logger.error(elem)

        try: 
            elem_json['title'] = elem.get("title", "") or elem.get("original_title", "") or elem.get("original_name", "")
            elem_json['language'] =  '*%s' % elem.get("original_language", "en")
            elem_json['thumbnail'] = elem.get("backdrop_path", "")
            elem_json['info'] = elem.get("id", "")
            elem_json['plot'] = elem.get("overview", "")
            elem_json['year'] = 0
            if scrapertools.find_single_match(elem.get('release_date', '-'), '(\d{4})'):
                elem_json['year'] = int(scrapertools.find_single_match(elem['release_date'], '(\d{4})'))
            elem_json['mediatype'] = 'movie' if movie_path in item.url else 'tvshow'
            if movie_path in item.url:
                elem_json['url'] = url_base_movie % (elem_json['title'], elem_json['year'])
            else:
                 elem_json['url'] = url_base_tv % elem_json['info']
            if not elem_json['year']: elem_json['year'] = "-"

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url'): continue

        matches.append(elem_json.copy())

    return matches


def seasons(item):
    logger.info()

    findS = finds.copy()
    url_base = '?api=torrents&mode=tv&name=%s&year=%s&quality=all'

    finds['season_url'] = url_base % (item.contentSerieName.replace(' ', '%20'), item.infoLabels.get('year', 0))

    return AlfaChannel.seasons(item, finds=finds, **kwargs)


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item, data=[]):
    logger.info()

    kwargs['matches_post_get_video_options'] = findvideos_matches

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, generictools=True, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    findS = finds.copy()
    matches = []
    elem_json_list = {}
    pattern_sxe = r'(?i)S(\d{2})E(\d{2})'
    pattern_dn = '(?i)&dn=([^\&]+)&'

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            try:
                elem_json['title'] = elem.get('title', '')
                try:
                    if scrapertools.find_single_match(elem_json['title'], pattern_sxe):
                        elem_json['season'], elem_json['episode'] = scrapertools.find_single_match(elem_json['title'], pattern_sxe)
                        elem_json['season'] = int(elem_json['season'])
                        elem_json['episode'] = int(elem_json['episode'])
                    else:
                        continue
                except Exception:
                    logger.error(elem)
                    logger.error(traceback.format_exc())
                    continue
                if elem_json['season'] != item.contentSeason: continue

                elem_json['url'] = elem.get('magnetUrl', '')
                elem_json['quality'] = AlfaChannel.do_unquote(elem_json['url'], pattern_dn) or elem.get('title', '')
                if '4k' in elem_json['quality'].lower(): elem_json['quality'] = '*4K'
                elif '2160' in elem_json['quality']: elem_json['quality'] = '*4K'
                elif '1080' in elem_json['quality']: elem_json['quality'] = '*1080p'
                elif '720' in elem_json['quality']: elem_json['quality'] = '*720p'
                elif 'hdtv' in elem_json['quality'].lower(): elem_json['quality'] = '*HDTV'
                else: elem_json['quality'] = '*HDTV'

                elem_json['size'] = elem.get('bytes', 0)
                if elem_json['size']:
                    elem_json['size'] = elem_json['torrent_info'] = '%s GB' % round(elem_json['size'] / (1024*1024*1024), 2)
                if elem.get('seeds'): elem_json['torrent_info'] += ', Seeds: %s' % elem['seeds']

            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

            elem_json['language'] = item.language
            elem_json['mediatype'] = 'episode'
            elem_json['server'] = 'torrent'

            elem_json_list[elem_json['episode']] = True

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        matches.append(elem_json.copy())

    last_episode_to_air = item.infoLabels.get('last_episode_to_air', '')
    if last_episode_to_air:
        for x in range(1, last_episode_to_air+1):
            if x not in elem_json_list:
                elem_json = {}

                elem_json['title'] = item.contentSerieName
                elem_json['season'] = item.contentSeason
                elem_json['episode'] = x
                elem_json['url'] = 'magnet:VOID'
                elem_json['quality'] = ''
                elem_json['language'] = item.language
                elem_json['mediatype'] = 'episode'
                #elem_json['server'] = 'torrent'

                matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    findS = AHkwargs.get('finds', finds)
    pattern_dn = '(?i)&dn=([^\&]+)&'
    pattern_quality = r'(?i)(?:%s\)*\]*|4k|imax|2160|1080|720|webrip)([^$]*$)'
    matches = []

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if elem_json.get('mediatype', '') == 'episode':
                elem_json = elem.copy()

            else:
                elem_json['url'] = elem.get('magnetUrl', '')
                elem_json['title'] = AlfaChannel.do_unquote(scrapertools.find_single_match(elem_json['url'], pattern_dn)) or elem.get('title', '')
                elem_json['quality'] = scrapertools.find_single_match(elem_json['title'], pattern_quality % item.infoLabels.get('year', ''))
                elem_json['quality'] = elem_json['quality'].strip().strip('.').strip('(').strip(')').strip('[').strip(']')\
                                                           .strip('V3').strip('mkv').strip('.').strip() \
                                                           or elem_json['title']
                elem_json['language'] = item.language
                elem_json['size'] = elem.get('bytes', 0)
                if elem_json['size']:
                    elem_json['size'] = elem_json['torrent_info'] = '%s GB' % round(elem_json['size'] / (1024*1024*1024), 2)
                if elem.get('seeds'): elem_json['torrent_info'] += ', Seeds: %s' % elem['seeds']

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())

        if not elem_json.get('url', ''): 
            continue
        elem_json['server'] = 'torrent'

        matches.append(elem_json.copy())

    return matches, langs


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    texto = texto.replace(" ", "%20")

    try:
        if texto:
            item.url += texto
            item.c_type = 'search'
            item.texto = texto
            itemlist = list_all(item)

            return itemlist
        else:
            return []

    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []