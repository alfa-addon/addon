# -*- coding: utf-8 -*-
# -*- Channel TioDonghua -*-
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
             'channel': 'tiodonghua', 
             'host': config.get_setting("current_host", 'tiodonghua', default=''), 
             'host_alt': ['https://tiodonghua.com/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'peliculas/'
tv_path = 'genero/donghua/'
language = []
url_replace = []
seasonPattern = '(?i)((?:\s+Season|\s+cour|\s+Part|\s+Movie|)' \
                +'\s+\d{1,2}' \
                +'(?:[a-z]{2}\s+Season|[a-z]{2}\s+cour|[a-z]{2}\s+Season\s+Part\s+\d+|)' \
                +'(?:\s+extra\s+edition|\s+specials|\s+ova|)' \
                +'(?:\s+Sub\s+Español|\s+Legendado\s+Portugués|))$'

finds = {'find': dict([('find', [{'tag': ['div'], 'class': ['items']}]),
                       ('find_all', [{'tag': ['article'], 'class': ['item']}])]),
         'categories': {},
         'search': dict([('find', [{'tag': ['div'], 'class': ['search-page']}]),
                         ('find_all', [{'tag': ['article']}])]), 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {},
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}]),
                            ('find_all', [{'tag': ['span'], '@POS': [0]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '\s+(\d+)$'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['seasons']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['se-c']}])]),
         'season_num': dict([('find', [{'tag': ['span'], 'class': ['se-t']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True}])]),
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': host,
         'episode_url': '',
         'episodes': dict([('find_all', [{'tag': ['ul'], 'class': ['episodios'], '@DO_SOUP': True},
                          {'tag': ['li']}])]),
         'episode_num': [], 
         'episode_clean': [['(?i)pt/br', '']], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['div'], 'id': ['playeroptions']}]),
                           ('find_all', [{'tag': ['li']}])]),
         'title_clean': [[seasonPattern, ''], ['(?i)Sub Español|Legendado Portugués', '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 30, 
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

    itemlist.append(Item(channel=item.channel, title='Nuevos Donghuas', url=host + 'donghua/', action='list_all',
                         thumbnail=get_thumb('newest', auto=True), c_type='newest'))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'genero/donghua/', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'peliculas/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    # itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host, 
                         # thumbnail=get_thumb('categories', auto=True), extra='categorías'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True), c_type='search'))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    return AlfaChannel.section(item, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'episodios':
        findS['find'] = dict([('find_all', [{'tag': ['article'], 'class': ['episodes']}])])
        
    if item.c_type == 'newest':
        findS['find'] = dict([('find', [{'tag': ['div'], 'id': ['archive-content']}]),
                              ('find_all', [{'tag': ['article'], 'class': ['item']}])])

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)

        try:
            if item.c_type == 'episodios':
                spans = elem.find_all('span')
                if re.search('(?i)(Youko|Bilibili|Tencent|Iqiyi)', spans[0].get_text(strip=True)): continue
                season, episode = scrapertools.find_single_match(spans[1].get_text(strip=True), '^T(\d+)\s+E(\d+)')
                elem_json['season'] = int(season or 1)
                elem_json['episode'] = int(episode or 1)
                elem_json['title'] = spans[2].get_text(strip=True)
                elem_json['mediatype'] = 'episode'
                elem_json['url'] = elem.find("a").get('href', '')
            elif item.c_type == 'search':
                info = elem.find("div", class_="title").a
                elem_json['title'] = info.get_text(strip=True)
                elem_json['url'] = info.get('href', '')
                elem_json['plot'] = elem.find("div", class_="contenido").p.get_text(strip=True)
                elem_json['thumbnail'] = elem.find("div", class_="thumbnail").a.img.get("data-src", "")
                mtype = elem.find("div", class_="thumbnail").a.span.get_text(strip=True)
                elem_json['mediatype'] = 'tvshow' if not mtype == 'Película' and 'Película' not in elem_json['plot'] else 'movie'
            elif item.c_type == 'peliculas':
                elem_json['title'] = elem.find("h3").get_text(strip=True)
                elem_json['url'] = elem.find("a").get('href', '')
                elem_json['thumbnail'] = elem.find("img").get("data-src", "")
                elem_json['mediatype'] = 'movie'
            else:    
                elem_json['title'] = elem.find("h3").a.get_text(strip=True)
                elem_json['url'] = elem.find("h3").a.get('href', '')
                elem_json['thumbnail'] = elem.find("img").get("data-src", "")
                elem_json['mediatype'] = 'tvshow'
            
            if re.search(seasonPattern, elem_json['title']):
                seasonStr = scrapertools.find_single_match(elem_json['title'], seasonPattern)
                seasonStr = scrapertools.find_single_match(seasonStr, '(\d{1,2})')
                if elem_json['mediatype'] == 'tvshow':
                    elem_json['season'] = int(seasonStr)
                    seasonStr = 'Temporada %s' % elem_json['season']
                elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                          % (AlfaChannel.color_setting.get('movies', 'white'), seasonStr)]

            elem_json['language'] = get_lang_from_str(elem_json['title'])
            elem_json['year'] = '-'
            elem_json['quality'] = 'HD'
            
            elem_json['context'] = renumbertools.context(item)
            elem_json['context'].extend(autoplay.context)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json.get('url', ''): 
            continue

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
    
    # Asi lee los datos correctos de TMDB
    titleSeason = item.contentSeason
    if matches_int and titleSeason == 1:
        titleSeason = get_title_season(soup)

    for elem in matches_int:
        elem_json = {}
        
        # logger.error(elem)
        try:
            season, episode = elem.find("div", class_="numerando").get_text(strip=True).split(' - ')
            if titleSeason == item.contentSeason and int(season) != item.contentSeason: continue
            # logger.info("contentSeason %d, season %d, titleSeason %d" % (item.contentSeason, int(season or 1), titleSeason), True)
            elem_json['season'], elem_json['episode'] = renumbertools.numbered_for_trakt(item.channel, 
                                                        item.contentSerieName, titleSeason, int(episode or 1))
            info = elem.find("div", class_="episodiotitle")
            elem_json['url'] = info.a.get("href", "")
            elem_json['title'] = info.a.get_text(strip=True)
            portugues = scrapertools.find_single_match(elem_json['title'], '(?i)(PT\/BR)$')
            if portugues:
                # La verdad es que no se que poner aqui, pero no es Version Original Subtitulada en Español ¿VOSP entonces?
                elem_json['language'] = 'VOS Portugués'
            else:
                elem_json['language'] = 'VOSE'
            elem_json['thumbnail'] = elem.find("div", class_="imagen").img.get("data-src", "")
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
            kwargs['post'] = 'action=doo_player_ajax&post=%s&nume=%s&type=%s' \
                             % (elem.get('data-post', ''), elem.get('data-nume', ''), elem.get('data-type', ''))

            kwargs['soup'] = False
            kwargs['json'] = True

            iframeData = AlfaChannel.create_soup(AlfaChannel.doo_url, hide_infobox=True, **kwargs)
            if not iframeData: continue
            if not iframeData.get('embed_url', ''): continue
            url = check_embed_url(iframeData['embed_url'])
            if url == "": continue

            if re.search(r'vidguard.to|hqq.ac|modagamers.com|'
                         +'digitalxona.com|animetemaefiore.club|sbface.com|'
                         +'guccihide.com|terabox.com|sharezweb.com|'
                         +'cuyplay.com|vgembed.com|ahvsh.com|videopress.com|tioplayer.com|videa.hu|embedgram.com',
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


def get_lang_from_str(string):

    if 'portugués' in string.lower():
        lang = 'portugues'
    else:
        lang = 'VOSE'

    return lang
    
def check_embed_url(embed_url):
    if embed_url == '':
        return ''
    if not embed_url.startswith('https'):
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        else:
            embed_soup = AlfaChannel.do_soup(embed_url)
            if embed_soup:
                if embed_soup.iframe:
                    embed_url = embed_soup.iframe.get('src', '')
                    if embed_url.startswith('//'):
                        embed_url = 'https:' + embed_url
                else:
                    # logger.info('Embed Soup: ' + str(embed_soup), True)
                    embed_url = ''
            else:
                # logger.info('Embed URL: ' + embed_url, True)
                embed_url = ''

    return embed_url


# Algunas series tienen la temporada en el titulo, lo cual hace que TMDB devuelva los datos incorrectos
# Ya que por defecto la temporada se obtiene de otro lado, esto crea una ambigüedad.
# Esta funcion se usa para extraer el numero de temporada correcto del titulo
def get_title_season(soup):
    logger.info()
    # logger.info('SOUP: ' + str(soup), True)
    season = 1
    if soup.find("div", class_="data") and soup.find("div", class_="data").find("h1"):
        title = soup.find("div", class_="data").find("h1").get_text(strip=True)

        if re.search(seasonPattern, title):
            seasonStr = scrapertools.find_single_match(title, seasonPattern)
            season = int(scrapertools.find_single_match(seasonStr, '(\d{1,2})'))

    return season