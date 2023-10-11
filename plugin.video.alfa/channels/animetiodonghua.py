# -*- coding: utf-8 -*-
# -*- Channel Anime TioDonghua -*-
# -*- Created for Alfa Addon -*-
# -*- By DieFeM -*-

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
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'animetiodonghua', 
             'host': config.get_setting("current_host", 'animetiodonghua', default=''), 
             'host_alt': ['https://anime.tiodonghua.com/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []
seasonPattern = '(?i)((?:\s+Season|\s+cour|\s+Part|\s+Movie|)' \
                +'\s+\d{1,2}' \
                +'(?:[a-z]{2}\s+Season|[a-z]{2}\s+cour|[a-z]{2}\s+Season\s+Part\s+\d+|)' \
                +'(?:\s+extra\s+edition|\s+specials|\s+ova|)' \
                +'(?:\s+Sub\s+Español|\s+Legendado\s+Portugués|))$'

finds = {'find': dict([('find', [{'tag': ['div'], 'class': ['listupd']}]), 
                       ('find_all', [{'tag': ['article']}])]), 
         'categories': dict([('find', [{'tag': ['ul'], 'class': ['genre']}]),
                             ('find_all', [{'tag': ['li']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}]),
                            ('find_all', [{'tag': ['a'], 'class': ['page-numbers'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {},
         'season_num': {},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'class': ['eplister']}]), 
                           ('find_all', [{'tag': ['li']}])]), 
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['select'], 'class': ['mirror']}]), 
                             ('find_all', [{'tag': ['option']}])]),
         'title_clean': [[seasonPattern, '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 10, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'IDIOMAS_TMDB': {0: 'es', 1: 'ja', 2: 'es'}, 'join_dup_episodes': False, 'season_TMDB_limit': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=host, action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))

    # itemlist.append(Item(channel=item.channel, title='Últimos Animes', url=host, action='list_all',
                         # thumbnail=get_thumb('newest', auto=True), c_type='series'))

    # itemlist.append(Item(channel=item.channel, title='Series', url=host + 'ver/category/categorias/', action='list_all',
                         # thumbnail=get_thumb('anime', auto=True), c_type='series'))

    # itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'ver/category/pelicula/', action='list_all',
                         # thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host, 
                         thumbnail=get_thumb('categories', auto=True), extra='categorías'))

    itemlist.append(Item(channel=item.channel, title='A-Z',  action='section', url=host, 
                         thumbnail=get_thumb('alphabet', auto=True), extra='az'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    
    if item.extra == 'az':
        findS['categories'] = dict([('find', [{'tag': ['ul'], 'class': ['az-list']}]), 
                                    ('find_all', [{'tag': ['a']}])])
 
    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['div'], 'class': ['listupd']}]), 
                              ('find_all', [{'tag': ['article']}])])

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        logger.error(elem)

        try:
            elem_json['title'] = elem.find("div", class_="tt").find(string=True).strip()
            elem_json['url'] = elem.find("a").get('href', '')
            elem_json['year'] = '-'
            elem_json['quality'] = 'HD'
            elem_json['thumbnail'] = elem.find("img").get("src", "")
            elem_json['mediatype'] = 'tvshow' if not re.search('(?i)pel[i|í]cula|movie', elem_json['title']) else 'movie'
            elem_json['language'] = '*VOSE'
   
            if elem_json['mediatype'] == 'movie':
                elem_json['action'] = 'seasons' 

            if re.search(seasonPattern, elem_json['title']):
                seasonStr = scrapertools.find_single_match(elem_json['title'], seasonPattern)
                season = int(scrapertools.find_single_match(seasonStr, '(\d{1,2})') or 1)
                if elem_json['mediatype'] == 'tvshow' or item.c_type == 'episodios':
                    elem_json['season'] = season
                if elem_json['mediatype'] == 'tvshow':
                    # seasonStr = 'Temporada %s' % season
                    elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                              % (AlfaChannel.color_setting.get('movies', 'white'), seasonStr)]

            if item.c_type == 'episodios':
                elem_json['episode'] = int(elem.find("span", class_="epx").get_text(strip=True).split(' ')[1])
                elem_json['mediatype'] = 'episode'

            elem_json['context'] = renumbertools.context(item)
            elem_json['context'].extend(autoplay.context)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): continue

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

    """ Aquí le decimos a qué función tienen que saltar para las películas de un solo vídeo """
    kwargs['matches_post_get_video_options'] = findvideos
    soup = AHkwargs.get('soup', '')

    return AlfaChannel.episodes(item, data=soup, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    soup = AHkwargs.get('soup', {})

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            elem_json['url'] = elem.a.get("href", "")
            elem_json['title'] = elem.find("div", class_="epl-title").get_text(strip=True)
            episode = int(elem.find("div", class_="epl-num").get_text(strip=True) or 1)
            season = get_title_season(soup)
            elem_json['language'] = item.language
            
            elem_json['season'], elem_json['episode'] = renumbertools.numbered_for_trakt(item.channel, 
                                                        item.contentSerieName, season, episode)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()

    kwargs['matches_post_episodes'] = episodesxseason_matches

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)

        try:
            url = check_embed_url(elem.get('value', '').strip())
            if url == '': continue
            
            if re.search(r'vidguard.to|hqq.ac|modagamers.com|'
                         +'digitalxona.com|animetemaefiore.club|sbface.com|'
                         +'guccihide.com|terabox.com|sharezweb.com|'
                         +'cuyplay.com|vgembed.com|ahvsh.com|videopress.com|'
                         +'tioplayer.com|videa.hu|embedgram.com|vgfplay.com|'
                         +'mixdroop.bz|tioanime.com',
                         url, re.IGNORECASE):
                continue
            
            elem_json['url'] = url
            elem_json['title'] = '%s'
            elem_json['language'] = item.language
            elem_json['quality'] = 'HD'

            if not elem_json.get('url'): continue
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


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        # https://docs.python.org/2/library/urllib.html#urllib.quote_plus (escapa los caracteres de la busqueda para usarlos en la URL)
        texto = AlfaChannel.do_quote(texto, '', plus=True) 
        item.url = item.url + "?s=" + texto

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
    item.channel = canonical['channel']

    try:
        if categoria in ['anime']:
            item.url = host
            item.c_type = 'episodios'
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


def check_embed_url(base64_iframe):
    if base64_iframe == '': return ''
    dec_iframe = base64.b64decode(base64_iframe).decode("utf-8")
    iframe_soup = AlfaChannel.do_soup(dec_iframe)
    if iframe_soup:
        if iframe_soup.iframe:
            url = iframe_soup.iframe.get('src', '')
            if url.startswith('//'):
                url = 'https:' + embed_url
        else:
            # logger.info('Soup: ' + str(iframe_soup), True)
            url = ''
    else:
        # logger.info('URL: ' + url, True)
        url = ''

    return url


# Esta funcion se usa para extraer el numero de temporada del título
def get_title_season(soup):
    logger.info()

    season = 1
    
    if soup.find("h1", class_="entry-title"):
        season_name = soup.find("h1", class_="entry-title").get_text(strip=True)

        if re.search(seasonPattern, season_name):
            seasonStr = scrapertools.find_single_match(season_name, seasonPattern)
            season = int(scrapertools.find_single_match(seasonStr, '(\d{1,2})'))

    return season