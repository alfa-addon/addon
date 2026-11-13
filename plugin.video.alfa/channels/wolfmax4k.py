# -*- coding: utf-8 -*-
# -*- Channel WolfMax4K -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import urlparse as alfa_urlparse
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay, renumbertools

from core import filetools

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_T
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_T

cf_assistant = False if AlfaChannelHelper.IS_ASSISTANT_INSTALLED else False
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'wolfmax4k', 
             'host': config.get_setting("current_host", 'wolfmax4k', default=''), 
             'host_alt': ["https://wolftorrent.com"], 
             'host_black_list': ["https://wolfmax4k.com/"], 
             'pattern': r'<a\s*href="([^"]+)"\s*class="navbar-brand\s*me-xl-4\s*me-lg-3\s*text-gray-900">', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF_proxy_alt': False, 'cf_assistant': cf_assistant, 'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': False
            }
host = canonical['host'] or canonical['host_alt'][0]
host_torrent = host
host_search = host
channel = canonical['channel']
categoria = channel.capitalize()
plot = '[COLOR hotpink][B]Atención:[/B][/COLOR] requiere un browser tipo '
plot +='[COLOR yellow]Chrome, Firefox, Opera[/COLOR] para descargar los archivos [COLOR hotpink].torrent[/COLOR]'

timeout = config.get_setting('timeout_downloadpage', channel)
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
episode_path = '/episodio'
docu_path = '/documental'
tele_path = '/telenovela'
anime_path = '/animacion'
api_catalogo = 'api/catalogo'
language = ['CAST']
url_replace_seasons = [[tv_path, tv_path+'s'], [docu_path, docu_path+'es'], [tele_path, tele_path+'s'], [anime_path, anime_path+'es']]
url_replace = []

finds = {'find': {'find_all': [{'tag': ['article'], 'class': ['wolf-card']}]}, 
         'sub_menu': {}, 
         'categories': {}, 
         'search': {'find_all': [{'tag': ['article'], 'class': ['wolf-card']}]}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': [], 
         'next_page': {}, 
         'next_page_rgx': [[r'pagina=\d+', 'pagina=%s']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['wolf-catalog-meta'], '@TEXT': r'(?i)P.gina\s*\d+\s*de\s*(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tag': ['article'], 'class': ['wolf-card']}]}, 
         'season_num': {}, 
         'seasons_search_num_rgx': [], 
         'seasons_search_qty_rgx': [], 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'class': ['wolf-episodes']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['wolf-episode']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['layout-section pb-3']}]}, 
         'title_clean': [[r'(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*imax', ''],
                         [r'(?i)[\[|\(]?\d{3,4}p[\]|\)]?|[\[|\(]?(?:4k|3d|uhd|hdr)[\]|\)]?', ''], 
                         [r'(?i)[-|\(]?\s*HDRip\)?|microHD|\(?BR-LINE\)?|\(?HDTS-SCREENER\)?', ''], 
                         [r'(?i)\(?BDRip\)?|\(?BR-Screener\)?|\(?DVDScreener\)?|\(?TS-Screener\)?|[\(|\[]\S*\.*$', ''],
                         [r'(?i)Castellano-*|Ingl.s|Trailer|Audio|\(*SBS\)*|\[*\(*dvd\s*r\d*\w*\]*\)*|[\[|\(]*dv\S*[\)|\]]*', ''], 
                         [r'(?i)Dual|Subt\w*|\(?Reparado\)?|\(?Proper\)?|\(?Latino\)?|saga(?:\s*del)?', ''], 
                         [r'(?i)(?:\s*&#8211;)?\s*-?\s*temp.*?\d+.*', ''], [r'\d?\d?&#.*', ''], [r'\d+[x|×]\d+.*', ''], 
                         [r'[\(|\[]\s*[\)|\]]', ''], [r'(?i)(?:libro|volumen)?\s+\d{1,2}$', ''], [r'(?i)\s+ts|\s+sub\w*|\s+\(*vos.*\)*', ''], 
                         [r'(?i)s\d{1,2}e\d{1,3}', '']],
         'quality_clean': [[r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', ''], 
                           [r'(?i)\d+\.\d+', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'url_base64': True, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'host_torrent': host_torrent, 'duplicates': [], 'btdigg_service': True},
         'timeout': timeout,
         'btdigg_cfg': [{'url': alfa_urlparse.build_url(host, 'peliculas', query='pagina=1&calidad=DVDRip'), 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path},
                        {'url': alfa_urlparse.build_url(host, 'peliculas', query='pagina=1&calidad=BluRay-1080p'), 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path},
                        {'url': alfa_urlparse.build_url(host, 'peliculas', query='pagina=1&calidad=4K'), 'c_type': 'peliculas', 'cnt_tot': 1, 'movie_path': movie_path},
                        {'url': alfa_urlparse.build_url(host, 'series', query='pagina=1&calidad=HDTV-720p'), 'c_type': 'series', 'cnt_tot': 3, 'tv_path': tv_path},
                        {'url': host, 'c_type': 'search_token', 'find': {'find_all': [{'tag': ['article'], 'class': ['wolf-card']}]}}, 
                        {'url': alfa_urlparse.build_url(host_search, 'buscar', query='pagina=1&q=%s&Buscar=Buscar'),
                                   'c_type': 'search', 'cnt_tot': 3, 'movie_path': movie_path, 'tv_path': tv_path, 
                                   'find': {'find_all': [{'tag': ['article'], 'class': ['wolf-card']}]}}]}

AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", c_type='peliculas', c_path=movie_path, 
                    url=alfa_urlparse.build_url(host, 'peliculas'), thumbnail=get_thumb("channels_movie.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", c_type='series', c_path=tv_path, 
                    url=alfa_urlparse.build_url(host, 'series'), thumbnail=get_thumb("channels_tvshow.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Documentales", c_type='documentales', c_path=docu_path, 
                    url=alfa_urlparse.build_url(host, 'documentales'), thumbnail=get_thumb("channels_documentary.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Animaciones", c_type='animaciones', c_path=anime_path, 
                    url=alfa_urlparse.build_url(host, 'animaciones'), thumbnail=get_thumb("channels_anime.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Telenovelas", c_type='telenovelas', c_path=tele_path, 
                    url=alfa_urlparse.build_url(host, 'telenovelas'), thumbnail=get_thumb("channels_latino.png"), contentPlot=plot))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", c_type='search', 
                    url=host_search, thumbnail=get_thumb("search.png")))

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
                             thumbnail=get_thumb("channels_movie.png"), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Estrenos[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='dias=2&pagina=1'),
                             thumbnail=get_thumb('on_the_air.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Géneros[/COLOR]", 
                             action="section", url=item.url, extra = "genero", 
                             thumbnail=get_thumb('genres.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidades[/COLOR]", 
                             action="section", url=item.url, extra = "calidad", 
                             thumbnail=get_thumb('search_star.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Añadidas últimos Días[/COLOR]", 
                             action="section", url=item.url, extra = "dias", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Años[/COLOR]", 
                             action="section", url=item.url, extra = "year", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Alfabeto[/COLOR]", 
                             action="section", url=item.url, extra = "Alfabético", 
                             thumbnail=get_thumb('channels_movie_az.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    elif item.c_type == 'series':
        itemlist.append(Item(channel=item.channel, title="Todas las Series", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'),
                             thumbnail=get_thumb('channels_tvshow.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Últimos Episodios[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'), extra = "episodios",
                             thumbnail=get_thumb('on_the_air.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: HDTV[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='calidad=HDTV&pagina=1'), extra = "calidad",
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))
                             
        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: HDTV 720p[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='calidad=HDTV-720p&pagina=1'), extra = "calidad",
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: WEB-DL 1080p[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='calidad=HDTV-1080p&pagina=1'), extra = "calidad",
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Calidad: 4K[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='calidad=4K&pagina=1'), extra = "calidad",
                             thumbnail=get_thumb('quality', auto=True), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Añadidas últimos Días[/COLOR]", 
                             action="section", url=item.url, extra = "dias", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Alfabeto[/COLOR]", 
                             action="section", url=item.url, extra = "Alfabético", 
                             thumbnail=get_thumb('channels_tvshow_az.png'), c_type=item.c_type, contentPlot=item.plot))

    elif item.c_type == 'documentales':
        itemlist.append(Item(channel=item.channel, title="Todas los Documentales", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'),
                             thumbnail=get_thumb('channels_documentary.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Últimos Episodios[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'), extra = "episodios",
                             thumbnail=get_thumb('on_the_air.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Añadidos últimos Días[/COLOR]", 
                             action="section", url=item.url, extra = "dias", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Alfabeto[/COLOR]", 
                             action="section", url=item.url, extra = "Alfabético", 
                             thumbnail=get_thumb('channels_tvshow_az.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    elif item.c_type == 'animaciones':
        itemlist.append(Item(channel=item.channel, title="Todas las Animaciones", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'),
                             thumbnail=get_thumb('channels_anime.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Últimos Episodios[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'), extra = "episodios",
                             thumbnail=get_thumb('on_the_air.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Añadidas últimos Días[/COLOR]", 
                             action="section", url=item.url, extra = "dias", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Alfabeto[/COLOR]", 
                             action="section", url=item.url, extra = "Alfabético", 
                             thumbnail=get_thumb('channels_tvshow_az.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    elif item.c_type == 'telenovelas':
        itemlist.append(Item(channel=item.channel, title="Todas las Telenovelas", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'),
                             thumbnail=get_thumb('channels_latino.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Últimos Episodios[/COLOR]", 
                             action="list_all", url=alfa_urlparse.build_url(item.url, query='pagina=1'), extra = "episodios",
                             thumbnail=get_thumb('on_the_air.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]Añadidas últimos Días[/COLOR]", 
                             action="section", url=item.url, extra = "dias", 
                             thumbnail=get_thumb('years.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

        itemlist.append(Item(channel=item.channel, title=" - [COLOR paleturquoise]por Alfabeto[/COLOR]", 
                             action="section", url=item.url, extra = "Alfabético", 
                             thumbnail=get_thumb('channels_tvshow_az.png'), c_type=item.c_type, c_path=item.c_path, contentPlot=item.plot))

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    if item.extra == "genero":
        findS['categories'] = dict([('find', [{'tag': ['div'], 'class': ['wolf-filter-genre-options']}]), 
                                    ('find_all', [{'tag': ['input']}])])

    elif item.extra == "calidad":
        findS['categories'] = dict([('find', [{'tag': ['legend'], 'class': ['sr-only'], 'string': re.compile('Calidad')}]), 
                                    ('find_next', [{'tag': ['div'], 'class': ['wolf-choice-options']}]),
                                    ('find_all', [{'tag': ['input']}])])

    elif item.extra == "Alfabético":
        itemlist = []

        for letra in ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                      'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:

            itemlist.append(item.clone(action="list_all", title=letra, url=alfa_urlparse.build_url(item.url, query=[('letra', u'{}'.format(letra)), ('pagina', '1')])))

        return itemlist

    elif item.extra == "dias":
        from platformcode.platformtools import dialog_numeric
        
        dias = dialog_numeric(0, "Introduzca el nº de Días de antiguedad", default="")
        item.url = alfa_urlparse.build_url(item.url, query=[('dias', u'{}'.format(dias)), ('pagina', '1')])

        return list_all(item)

    elif item.extra == "year":
        from platformcode.platformtools import dialog_numeric
        
        year = dialog_numeric(0, "Introduzca el Año de búsqueda", default="")
        item.url = alfa_urlparse.build_url(item.url, query=[('anyo_desde', u'{}'.format(year)), ('anyo_hasta', u'{}'.format(year)), ('pagina', '1')])

        return list_all(item)

    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        if not elem.get('value'): continue
        elem_json = {}
        #logger.error(elem)

        elem_json['url'] = alfa_urlparse.build_url(item.url, query=[(u'{}'.format(item.extra), u'{}'.format(elem['value'])), ('pagina', '1')])
        elem_json['title'] = elem['value']
        elem_json['c_type'] = item.c_type

        matches.append(elem_json.copy())

    return matches


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.category_new == 'newest':
        findS['controls']['cnt_tot'] = 40

    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, generictools=True, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    patter_quality = r'\[(\w+)\]'
    patter_title = r'(?i)\s*\-\s*\d+.\s*t\w*(?:\s*\[\w+\])?'
    patter_sxe = r'(?i)(\d{1,2})x(\d{1,4})'
    tvshow_list = []

    """
    soup = AHkwargs.get('soup', '')
    cursor = ''
    if soup.find('section', class_='wolf-catalog') and soup.find('section', class_='wolf-catalog').get('data-catalog-checkpoint'):
        cursor = soup.find('section', class_='wolf-catalog').get('data-catalog-checkpoint', '')
    elif soup.find('section', class_='wolf-search-page') and soup.find('section', class_='wolf-search-page').get('data-catalog-checkpoint'):
        cursor = soup.find('section', class_='wolf-search-page').get('data-catalog-checkpoint', '')
    elif isinstance(soup, _dict) and soup.get('cursor'):
        cursor = soup['cursor']
    if cursor:
        if not item.url_save: item.url_save = item.url
        item.url = host + 'api/catalogo'
        item.post = {"url": item.url_save.replace(host.rstrip('/'), ''), "checkpoint": cursor}
        item.headers = {'Referer': item.url_save}
        AlfaChannel.last_page = 999
    """

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if not elem.find('a', class_='wolf-card-poster'): continue
            elem_json['url'] = elem.a.get("href", "")

            elem_json['mediatype'] = 'movie' if movie_path in elem_json['url'] else 'tvshow'

            if item.c_path not in elem_json['url']: continue

            elem_json['title'] = elem.find('div', class_='wolf-card-content').find('h3', class_='wolf-card-title').get_text(strip=True)
            #elem_json['title'] = elem.a.get("alt", "")
            elem_json['thumbnail'] = elem.find('img').get("src", "")
            elem_json['language'] = language
            elem_json['year'] = '-'
            if elem.find('div', class_='wolf-card-content').find('p', class_='wolf-card-meta'):
                elem_json['year'] = scrapertools.find_single_match(elem.find('div', class_='wolf-card-content')\
                                                .find('p', class_='wolf-card-meta').get_text(strip=True), r'\d{4}')
            elem_json['broadcast'] = plot

            if elem_json['mediatype'] == 'movie':
                elem_json['matches_cached'] = []
                elem_json['quality'] = ''
                for quality in elem.find_all('li', class_='wolf-card-file'):
                    quality_json = {}
                    #logger.error(quality)

                    quality_json['url'] = quality.a.get("href", "").replace(movie_path, '/descarga'+movie_path).replace(tv_path, '/descarga'+tv_path)
                    quality_json['title'] = elem_json['title']
                    quality_json['quality'] = quality.a.get_text(strip=True)
                    elem_json['quality'] += '%s, ' % quality_json['quality']
                    if quality.find('span', class_='wolf-card-size'):
                        quality_json['size'] = quality.find('span', class_='wolf-card-size').get_text(strip=True)
                    quality_json['language'] = elem_json['language']
                    quality_json['year'] = elem_json['year']
                    quality_json['mediatype'] = elem_json['mediatype']
                    quality_json['server'] = 'torrent'

                    elem_json['matches_cached'].append(quality_json)

                elem_json['quality'] = elem_json['quality'].rstrip('%s, ')
            
            else:
                quality_save = 'HDTV'
                if elem.find('a', class_='wolf-card-format'):
                    quality_save = elem.find('a', class_='wolf-card-format').get_text('|', strip=True).split('|')[-1]
                elem_json['quality'] = '*%s' % quality_save
                elem_json['title'] = re.sub(patter_title, '', elem_json['title'])
                if elem_json['title'] + elem_json['quality'] in tvshow_list: continue
                tvshow_list += [elem_json['title'] + elem_json['quality']]
                
                if item.extra == 'episodios':
                    elem_json['mediatype'] = 'episode'
                    
                    episode_json = {}
                    elem_json['matches_cached'] = []
                    for episode in elem.find_all('li', class_='wolf-card-file'):
                        episode_json = {}
                        #logger.error(episode)

                        episode_json['url'] = elem_json['url'] = episode.a.get("href", "").replace(item.c_path+episode_path, '/descarga'+item.c_path)
                        episode_json['title'] = elem_json['title']
                        episode_json['quality'] = elem_json['quality'] = '*%s' % (episode.a.get_text('|', strip=True).split('|')[-1] \
                                                                                  or elem_json['quality'])
                        episode_json['language'] = elem_json['language']
                        episode_json['info'] = episode.get('data-wolf-episode-id', '')
                        if not episode_json['info']: continue
                        episode_json['size'] = episode.find('span', class_='wolf-card-size').get_text(strip=True)
                        episode_json['mediatype'] = 'episode'
                        episode_json['server'] = 'torrent'
                        try:
                            episode_json['season'], episode_json['episode'] = scrapertools.find_single_match(
                                episode.a.get_text('|', strip=True).split('|')[0], patter_sxe
                            )
                            episode_json['season'] = elem_json['season'] = int(episode_json['season'])
                            episode_json['episode'] = elem_json['episode'] = int(episode_json['episode'])
                            break

                        except Exception:
                            logger.error(episode)
                            logger.error(traceback.format_exc())
                            continue

                    if episode_json.get('episode'):
                        elem_json['matches_cached'].append(episode_json)

                else:
                    elem_json['url'], x = filetools.split(elem_json['url'])
                    elem_json['url'] = AlfaChannel.do_url_replace(elem_json['url'], url_replace_seasons)
                    elem_json['url'] = '%s?q=%s&calidad=%s' % (elem_json['url'], 
                                        scrapertools.slugify(elem_json['title'].replace(' ', '+'), convert=['+=+']), 
                                        quality_save)

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
    patron_season = r'(?i)(\d{1,2})x\d{1,4}'
    patter_title = r'(?i)\s*\-\s*\d+.\s*t\w*(?:\s*\[\w+\])?'

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            elem_json['season'] = elem.find('a', class_='wolf-card-format').get_text('|', strip=True).split('|')[0]
            elem_json['season'] = scrapertools.find_single_match(elem_json['season'], patron_season)
            elem_json['url'] = elem.a.get("href", "")
            elem_json['title'] = elem.find('div', class_='wolf-card-content').find('h3', class_='wolf-card-title').get_text(strip=True)
            elem_json['title'] = re.sub(patter_title, '', elem_json['title'])
            if scrapertools.slugify(elem_json['title']) != scrapertools.slugify(item.contentSerieName): continue

            elem_json['quality'] = elem.find('a', class_='wolf-card-format').get_text('|', strip=True).split('|')[-1]
            elem_json['quality'] = AlfaChannel.find_quality(elem_json, item)
            if elem_json['quality'] != item.quality: continue

        except Exception:
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
    patter_sxe = r'(?i)(\d{1,2})x(\d{1,4})'
    pass_list = item.password or {}

    for elem in matches_int:
        elem_json = {}
        elem_json['matches_cached'] = []
        episode_json = {}
        #logger.error(elem)

        try:
            url_split = elem.a.get("href", "").strip('/').split('/')
            elem_json['url'] = episode_json['url'] = '/descarga/%s/%s' % (url_split[0], url_split[-1])

            try:
                elem_json['season'], elem_json['episode'] = scrapertools.find_single_match(
                    elem.a.get_text('|', strip=True).split('|')[0], patter_sxe
                )
                elem_json['season'] = episode_json['season'] = int(elem_json['season'])
                elem_json['episode'] = episode_json['episode'] = int(elem_json['episode'])

                if elem_json['season'] != item.contentSeason: continue
            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

            elem_json['size'] = episode_json['size'] = elem.find('span', class_='wolf-episode-size').get_text(strip=True)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        elem_json['mediatype'] = episode_json['mediatype'] = 'episode'
        elem_json['server'] = episode_json['server'] = 'torrent'
        elem_json['language'] = episode_json['language'] = item.language
        elem_json['quality'] = episode_json['quality'] = item.quality
        elem_json['torrent_info'] = episode_json['torrent_info'] = elem_json.get('torrent_info', '')

        elem_json['matches_cached'].append(episode_json.copy())
        matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    findS = finds.copy()
    matches_cached = []

    if item.matches_cached:
        findS['findvideos'] = {'no-op': []}
        matches_cached = item.matches_cached[:]
        del item.matches_cached

    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, data=matches_cached, langs='CAST',
                                         finds=findS, verify_links=False, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info(langs)

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        if isinstance(elem, _dict):
            elem_json = elem.copy()

        else:
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

    texto = texto.replace(" ", "%20")

    try:
        if texto:
            item.c_type = "search"
            item.texto = texto
            #item.url = host_search + 'buscar?pagina=1&q=%s&Buscar=Buscar' % texto
            item.url = alfa_urlparse.build_url(host_search, u'buscar/{}'.format(texto))
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
            item.url = alfa_urlparse.build_url(host, 'peliculas', query='pagina=1&calidad=4K') if categoria == '4k' else alfa_urlparse.build_url(host, 'peliculas', query='pagina=1')
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
