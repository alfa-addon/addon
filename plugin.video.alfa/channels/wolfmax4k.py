# -*- coding: utf-8 -*-
# -*- Channel WolfMax4K -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay, renumbertools

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_T
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_T

cf_assistant = False
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'wolfmax4k', 
             'host': config.get_setting("current_host", 'wolfmax4k', default=''), 
             'host_alt': ["https://wolfmax4k.com/"], 
             'host_black_list': [], 
             'pattern': '<a\s*href="([^"]+)"\s*class="navbar-brand\s*me-xl-4\s*me-lg-3\s*text-gray-900">', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt,  
             'cf_assistant': cf_assistant, 'CF_stat': True, 'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': False
            }
host = canonical['host'] or canonical['host_alt'][0]
host_torrent = host
host_search = host.replace('https://', 'https://admin.')
channel = canonical['channel']
categoria = channel.capitalize()
plot = '[COLOR hotpink][B]Atención:[/B][/COLOR] requiere un browser tipo '
plot +='[COLOR yellow]Chrome, Firefox, Opera[/COLOR] para descargar los archivos [COLOR hotpink].torrent[/COLOR]'

timeout = config.get_setting('timeout_downloadpage', channel)
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/movie"
tv_path = '/serie'
docu_path = '/documentales'
pr_tv_path = '/programas-tv'
tele_path = '/telenovelas'
anime_path = '/animacion-manga'
infantil_path = '/animacion-infantil'
language = ['CAST']
url_replace = []

finds = {'find': {'find_all': [{'tag': ['div'], 'class': ['col-lg-2']}]}, 
         'sub_menu': {}, 
         'categories': {}, 
         'search': {'get_text': [{'tag': '', '@STRIP': False, '@JSON': 'DEFAULT'}]}, 
         'get_language': {}, 
         'get_language_rgx': '(?:flags\/|\/images\/)(\w+)(?:-[^\.]+)?\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': [], 
         'next_page': {}, 
         'next_page_rgx': [['\&pg=\d+', '&pg=%s'], ['\/\d+$', '/%s']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['mod-pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], '@ARG': 'href', '@TEXT': '\/(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'class': ['tabs']}]), 
                          ('find_all', [{'tag': ['summary']}])]), 
         'season_num': {}, 
         'seasons_search_num_rgx': [], 
         'seasons_search_qty_rgx': [], 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'class': ['tabs']}]), 
                          ('find_all', [{'tag': ['li']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['layout-section pb-3']}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*imax', ''],
                         ['(?i)[\[|\(]?\d{3,4}p[\]|\)]?|[\[|\(]?(?:4k|3d|uhd|hdr)[\]|\)]?', ''], 
                         ['(?i)[-|\(]?\s*HDRip\)?|microHD|\(?BR-LINE\)?|\(?HDTS-SCREENER\)?', ''], 
                         ['(?i)\(?BDRip\)?|\(?BR-Screener\)?|\(?DVDScreener\)?|\(?TS-Screener\)?|[\(|\[]\S*\.*$', ''],
                         ['(?i)Castellano-*|Ingl.s|Trailer|Audio|\(*SBS\)*|\[*\(*dvd\s*r\d*\w*\]*\)*|[\[|\(]*dv\S*[\)|\]]*', ''], 
                         ['(?i)Dual|Subt\w*|\(?Reparado\)?|\(?Proper\)?|\(?Latino\)?|saga(?:\s*del)?', ''], 
                         ['(?i)(?:\s*&#8211;)?\s*-?\s*temp.*?\d+.*', ''], ['\d?\d?&#.*', ''], ['\d+[x|×]\d+.*', ''], 
                         ['[\(|\[]\s*[\)|\]]', ''], ['(?i)(?:libro|volumen)?\s+\d{1,2}$', ''], ['(?i)\s+ts|\s+sub\w*|\s+\(*vos.*\)*', ''], 
                         ['(?i)s\d{1,2}e\d{1,3}', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', ''], 
                           ['(?i)\d+\.\d+', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'url_base64': True, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'host_torrent': host_torrent, 'duplicates': [], 'btdigg_service': True},
         'timeout': timeout,
         'btdigg_cfg': [{'url': host + 'peliculas/bluray/', 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path}, 
                        {'url': host + 'peliculas/bluray-1080p/', 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path}, 
                        {'url': host + 'peliculas/4k-2160p/', 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path},
                        {'url': host + 'series/720p/', 'c_type': 'series', 'cnt_tot': 3, 'tv_path': tv_path},
                        {'url': host, 'c_type': 'search_token', 'find': {'find': [{'tag': ['form'], 'class': ['form-search']}], 
                                                                         'find_all': [{'tag': ['input'], '@POS': [1], '@ARG': 'value'}]}}, 
                        {'url': host_search + 'admin/admpctn/app/data.find.php', 'post': 'token=%s&cidr=0&c=0&l=100&pg=1&q=', 
                                'c_type': 'search', 'cnt_tot': 3, 'movie_path': movie_path, 'tv_path': tv_path, 
                                'find': {'get_text': [{'tag': '', '@STRIP': False, '@JSON': 'DEFAULT'}]}}]}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", c_type='peliculas', 
                    url=host + 'peliculas/', thumbnail=get_thumb("channels_movie.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", c_type='series', 
                    url=host + 'series/', thumbnail=get_thumb("channels_tvshow.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Otros", c_type='documentales', 
                    url=host, thumbnail=get_thumb("channels_documentary.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", c_type='search', 
                    url=host_search + 'admin/admpctn/app/data.find.php', thumbnail=get_thumb("search.png")))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                    folder=False, thumbnail=get_thumb("next.png")))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                    thumbnail=get_thumb("setting_0.png")))

    itemlist = renumbertools.show_option(item.channel, itemlist, status=canonical.get('renumbertools', False))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)                                # Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools

    ret = platformtools.show_channel_settings()

    return platformtools.itemlist_refresh()
    
    
def submenu(item):
    logger.info()

    itemlist = []

    if item.c_type == 'peliculas':
        itemlist.append(Item(channel=item.channel, title="Todas las Películas", 
                             action="list_all", url=item.url, 
                             thumbnail=get_thumb('movies', auto=True), c_type=item.c_type, contentPlot=item.plot))
        
        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: Bluray[/COLOR]", 
                             action="list_all", url=item.url + 'bluray/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: Bluray 720p[/COLOR]", 
                             action="list_all", url=item.url + 'bluray-720p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: Bluray 1080p[/COLOR]", 
                             action="list_all", url=item.url + 'bluray-1080p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: 4K[/COLOR]", 
                             action="list_all", url=item.url + '4k-2160p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

    if item.c_type == 'series':
        itemlist.append(Item(channel=item.channel, title="Todas las Series (episodios)", 
                             action="list_all", url=item.url + '480p/', 
                             thumbnail=get_thumb('movies', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: HDTV[/COLOR]", 
                             action="list_all", url=item.url + '480p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))
                             
        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: HDTV 720p[/COLOR]", 
                             action="list_all", url=item.url + '720p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: WEB-DL 1080p[/COLOR]", 
                             action="list_all", url=item.url + '1080p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: 4K[/COLOR]", 
                             action="list_all", url=item.url + '4k-2160p/', 
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, contentPlot=item.plot))

    if item.c_type == 'documentales':
        itemlist.append(Item(channel=item.channel, title="Documentales (episodios)", 
                             action="list_all", url=host + docu_path.lstrip('/') + '/', 
                             thumbnail=get_thumb('documental', auto=True), c_type='documentales', contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Programas TV (episodios)", 
                             action="list_all", url=host + pr_tv_path.lstrip('/') + '/', 
                             thumbnail=get_thumb('tvshows', auto=True), c_type='documentales', contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Telenovelas (episodios)", 
                             action="list_all", url=host + tele_path.lstrip('/') + '/', 
                             thumbnail=get_thumb('telenovelas', auto=True), c_type='documentales', contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Animación y Manga (episodios)", 
                             action="list_all", url=host + anime_path.lstrip('/') + '/', 
                             thumbnail=get_thumb('anime', auto=True), c_type='documentales', contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title="Animación Infantil (episodios)", 
                             action="list_all", url=host + infantil_path.lstrip('/') + '/', 
                             thumbnail=get_thumb('infantil', auto=True), c_type='documentales', contentPlot=item.plot))

    return itemlist


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    headers = {}
    
    if item.category_new == 'newest':
        findS['controls']['cnt_tot'] = 40

    if item.c_type == 'search':
        if '%s' in item.post:
            soup = AlfaChannel.create_soup(host, alfa_s=True, **kwargs)
            token = soup.find('form', class_='form-search').find_all('input')[1].get('value', '') if soup.find('form', class_='form-search') else ''
            if not token: 
                logger.error('No hay TOKEN para búsquedas: %s' % soup.find('form', class_='form-search'))
            item.post = item.post % token
        headers['Referer'] = host
        findS['controls']['force_find_last_page'] = [0, 0, 'post']
                
    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, headers=headers, generictools=True, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    if item.c_type == 'search':
        if not isinstance(matches_int, _dict):
            return matches
        if not matches_int.get('response', False):
            return matches

        results = int(matches_int.get('data', {}).get('pgcount', 0))

        if results:
            AlfaChannel.last_page = int((results / findS['controls']['cnt_tot']) + 0.9999)
            matches_int = matches_int.get('data', {}).get('datafinds', {})['0'].copy()

            for key, elem in list(matches_int.items()):
                elem_json = {}
                #logger.error(elem)

                elem_json['url'] = elem.get("guid", "")
                elem_json['quality'] = '*%s' % elem.get("calidad", "")
                elem_json['title'] = elem.get("torrentName", "")
                elem_json['thumbnail'] = elem.get("image", "")

                elem_json['mediatype'] = 'movie'
                if scrapertools.find_single_match(elem_json['title'], r'(?i)Cap.(\d+)(\d{2})'):
                    elem_json['mediatype'] = 'episode'
                    try:
                        sxe = scrapertools.find_single_match(elem_json['title'], r'(?i)Cap.(\d+)(\d{2})')
                        elem_json['season'] = int(sxe[0] or 1)
                        elem_json['episode'] = int(sxe[1] or 1)

                    except Exception:
                        logger.error(elem)
                        elem_json['season'] =  1
                        elem_json['episode'] =  1
                elem_json['title'] = re.sub(r'\s*\[[^\]]+\](?:\s*\[*[^\]]+\])?', '', elem_json['title']).strip()
                elem_json['broadcast'] = plot

                if not elem_json.get('url'): continue

                matches.append(elem_json.copy())

        return matches

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if not elem.find('div', class_='card-body'): continue
            elem_json['url'] = elem.a.get("href", "")
            
            elem_json['mediatype'] = 'tvshow' if tv_path in elem_json['url'] else 'movie'
            if item.c_type == 'peliculas' and elem_json['mediatype'] != 'movie': continue
            if item.c_type == 'series' and elem_json['mediatype'] != 'tvshow': continue

            elem_json['title'] = elem.find('div', class_='card-body').find('h3', class_='title').get_text(strip=True)
            if scrapertools.find_single_match(elem_json['title'], '\s*\[([^\]]+)\]'):
                elem_json['quality'] = '*%s' % scrapertools.find_single_match(elem_json['title'], r'\[([^\]]+)\]')
                elem_json['title'] = re.sub(r'\s*\[[^\]]+\](?:\s*\[*[^\]]+\])?', '', elem_json['title']).strip()
            else:
                elem_json['quality'] = '*%s' % elem.find('div', class_='quality').get_text(strip=True).replace('Otros', '').replace('Series', '')
            elem_json['thumbnail'] = elem.find('img').get("src", "")
            elem_json['language'] = language
            elem_json['year'] = scrapertools.find_single_match(elem_json['title'], '\((\d{4})\)') or '-'
            if elem_json['mediatype'] != 'tvshow' and elem_json['year'] == '-' and elem.find('span', class_='fdi-type'):
                elem_json['year'] = elem.find('span', class_='fdi-type').get_text(strip=True)
            elem_json['broadcast'] = plot

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url'): continue

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
    patron_season = r'(?i)temp\w*\s*(\d+)'

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['season'] = scrapertools.find_single_match(elem.get_text(strip=True), patron_season)
            elem_json['url'] = item.url

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
    patron_epis = r'(?i)temp\w*\s*\[\s*(\d+)\s*\]\s*cap\w*\s*\[\s*(\d+)\s*\]'
    pass_list = item.password or {}

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if not elem.a and not elem.a.get_text(strip=True): continue
            info = elem.a.get_text('|', strip=True)
            if not scrapertools.find_single_match(info, patron_epis): continue
            sxe = scrapertools.find_single_match(info, patron_epis)
            elem_json['season'] = int(sxe[0])
            if elem_json['season'] != item.contentSeason: continue
            elem_json['episode'] = int(sxe[1])

            elem_json['url'] = elem.a.get('href', '')

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
    
    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            if not elem.find('a', class_='glow-on-hover'): continue
            elem_json['url'] = elem.find('a', class_='glow-on-hover').get('href', '')
            elem_json['server'] = 'torrent'
            elem_json['quality'] = item.quality
            elem_json['language'] = item.language
            elem_json['torrent_info'] = ''
            elem_json['broadcast'] = plot

            if elem.find('a', class_='buttonPassword'):
                elem_json['password'] = elem.find('a', class_='buttonPassword').get('href', '')
                elem_json['torrent_info'] = 'RAR-'

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())

        if not elem_json.get('url', ''): 
            continue

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

    try:
        if texto:
            item.post = 'token=%s&cidr=0&c=0&l=100&pg=1&q=' + texto
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        import sys
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
    item.extra = "novedades"
    item.action = "list_all"
    
    try:
        if categoria in ['peliculas', 'torrent', '4k']:
            item.url = host + 'peliculas/4k-2160p/' if categoria == '4k' else host + 'peliculas/'
            item.c_type = "peliculas"

            itemlist = list_all(item)

            if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
