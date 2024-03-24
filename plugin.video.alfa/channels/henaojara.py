# -*- coding: utf-8 -*-
# -*- Channel HenaoJara -*-
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
             'channel': 'henaojara', 
             'host': config.get_setting("current_host", 'henaojara', default=''), 
             'host_alt': ['https://www.henaojara.com/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = 'ver/category/pelicula/'
tv_path = 'ver/category/categorias/'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['MovieList']}]), 
                       ('find_all', [{'tag': ['li']}])]), 
         'categories': dict([('find', [{'tag': ['div'], 'id': ['categories-3']}]),
                             ('find_all', [{'tag': ['li']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['wp-pagenavi']}]),
                            ('find_all', [{'tag': ['a'], 'class': ['page-numbers'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tagOR': ['div'], 'class': ['AA-Season']},
                                  {'tag': ['a'], 'class': ['Button STPb Current']}]},
         'season_num': dict([('find', [{'tag': ['span']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True}])]),
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find_all', [{'tag': ['div'], 'class': ['TPTblCn'], '@DO_SOUP': True},
                          {'tag': ['tr']}])]),
         'episode_num': [], 
         'episode_clean': [['(?i)\s*-\s*Proximo\s*Capitulo\:?\s*(\d+-[A-Za-z]+-\d+)', ''],
                           ['(?i)HD|Español Castellano|Sub Español|Español Latino', '']], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['TPlayerTb']}]},
         'title_clean': [['(?i)HD|Español Castellano|Sub Español|Español Latino|ova\s+\d+\:|OVA\s+\d+|\:|\((.*?)\)|\s19\d{2}|\s20\d{2}', ''],
                         ['(?i)\s*Temporada\s*\d+', '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
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

    itemlist.append(Item(channel=item.channel, title='Últimos Animes', url=host, action='list_all',
                         thumbnail=get_thumb('newest', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'ver/category/categorias/', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'ver/category/pelicula/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host, 
                         thumbnail=get_thumb('categories', auto=True), extra='categorías'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

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
        findS['find'] = dict([('find', [{'tag': ['ul'], 'class': ['MovieList Rows BX B06 C04 E03 NoLmtxt Episodes']}]), 
                              ('find_all', [{'tag': ['li']}])])

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:

            if item.c_type == 'episodios':
                sxe = elem.find("span", class_="ClB").get_text(strip=True)
                try:
                    season, episode = sxe.split('x')
                    elem_json['season'] = int(season)
                    elem_json['episode'] = int(episode)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'

                nextChapterDateRegex = r'(?i)\s*-\s*Proximo\s*Capitulo\:?\s*(\d+-[A-Za-z]+-\d+)'
                proximo = elem.find('figcaption').get_text(strip=True)
                if re.search(nextChapterDateRegex, proximo):
                    nextChapterDate = scrapertools.find_single_match(proximo, nextChapterDateRegex)
                    elem_json['next_episode_air_date'] = nextChapterDate

            elem_json['title'] = elem.find("h3", class_="Title").get_text(strip=True)
            elem_json['language'] = get_lang_from_str(elem_json['title'])
            """ alternativamente mira: elem_json['language'] = '*%s' % elem_json['title'] AH busca el el idioma o la calidad si lo precedes con '*' """                                                                                          

            seasonPattern = '(?i)\s*Temporada\s*(\d+)'
            temporada = elem.find("span", class_="Year").get_text(strip=True) if elem.find("span", class_="Year") else elem_json['title']
            if re.search(seasonPattern, temporada):
                elem_json['season'] = int(scrapertools.find_single_match(temporada, seasonPattern))
                if elem_json['season'] > 1:
                    elem_json['title_subs'] = [' [COLOR %s][B]%s[/B][/COLOR] ' \
                                              % (AlfaChannel.color_setting.get('movies', 'white'), 'Temporada %s' % elem_json['season'])]

            elem_json['url'] = elem.find("article", class_="TPost C").a.get('href', '')

            # En episodios permite desde el menú contextual ir a la Serie
            if item.c_type == 'episodios' and elem_json['url']:
                elem_json['go_serie'] = {'url': re.sub('x\d+', '', elem_json['url']).replace('episode', 'season')}

            try:
                Qlty = elem.find("span", class_="Qlty").get_text(strip=True)
            except Exception:
                Qlty = ''

            if not elem_json.get('mediatype'):
                elem_json['mediatype'] = 'tvshow' if not "pelicula" in elem_json['title'] and Qlty not in ["PELICULA", "ESTRENO"] else 'movie'

            if item.c_type == 'series' and elem_json['mediatype'] == 'movie':
                continue
            if item.c_type == 'peliculas' and elem_json['mediatype'] == 'tvshow':
                continue

            if elem_json['mediatype'] == 'movie':
                elem_json['action'] = 'seasons'

            try:
                elem_json['thumbnail'] = elem.find(["noscript", "span"]).find("img").get("src", "")
            except Exception:
                pass

            try:
                elem_json['year'] = elem.find("span", class_="Date AAIco-date_range").get_text(strip=True)
            except Exception:
                elem_json['year'] = '-'

            elem_json['quality'] = 'HD'

            if elem.find("div", class_=["Description"]): 
                elem_json['plot'] = elem.find("div", class_=["Description"]).p.get_text(strip=True)

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
    
    # Asi lee los datos correctos de TMDB
    titleSeason = item.contentSeason
    if matches_int and titleSeason == 1:
        titleSeason = get_title_season(item.url, soup)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        try:
            info = elem.find("td", class_="MvTbTtl")
            elem_json['url'] = info.a.get("href", "")
            if not re.search(r'%sx\d+\/$' % str(item.contentSeason), elem_json['url']): continue
            elem_json['title'] = info.a.get_text(strip=True)
            episode = int(elem.find("span", class_="Num").get_text(strip=True) or 1)

            elem_json['season'], elem_json['episode'] = renumbertools.numbered_for_trakt(item.channel, 
                                                        item.contentSerieName, titleSeason, episode)

            nextChapterDateRegex = r'(?i)\s*-\s*Proximo\s*Capitulo\:?\s*(\d+-[A-Za-z]+-\d+)'
            if re.search(nextChapterDateRegex, elem_json['title']):
                nextChapterDate = scrapertools.find_single_match(elem_json['title'], nextChapterDateRegex)
                elem_json['next_episode_air_date'] = nextChapterDate

            try:
                elem_json['thumbnail'] = elem.find(["noscript", "span"]).find("img").get("src", "")
            except Exception:
                pass

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

    def add_match(url):
        url = check_hjstream(url)
        # logger.info(iframeUrl, True)
        uriData = AlfaChannel.urlparse(url)
        if re.search(r'hqq|netuplayer|krakenfiles|hj.henaojara.com|streamhj.top', uriData.hostname, re.IGNORECASE):
            return
        elem_json = {}
        elem_json['url'] = url
        elem_json['title'] = '%s'
        elem_json['language'] = item.language
        elem_json['quality'] = 'HD'
        if not elem_json.get('url'): return
        matches.append(elem_json.copy())

    for elem in matches_int:
        # logger.error(elem)

        try:
            content = elem.get_text(strip=True)
            if content != '':
                elem = AlfaChannel.do_soup(scrapertools.htmlparser(content)).iframe
            else:
                elem = elem.iframe

            url = elem.get('src', '')
            if url == "" or not url.startswith('http'):
                continue

            iframeData = AlfaChannel.create_soup(url, hide_infobox=True, **kwargs)
            if not iframeData:
                continue

            iframe = iframeData.find("iframe")
            if not iframe:
                continue

            iframeUrl = iframe.get('src', '')

            if iframeUrl != "":
                if "multiplayer" in iframeUrl:
                    videos = multiplayer_findvideos(iframeUrl)
                    for url in videos:
                        add_match(url)
                else:
                    add_match(iframeUrl)

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


# henaojara usa varios scripts para embeber algunos enlaces en diferentes subdominios de hjstream.xyz,
# esta funcion se encarga de extraer el enlace del servidor original a partir de los parámetros de la url,
# en el parámetro v (v=xxxx), a veces en texto plano, a veces en base64.
def check_hjstream(url):
    logger.info()

    if "hjstream.xyz" in url:
        queryData = AlfaChannel.parse_qs(AlfaChannel.urlparse(url).query)
        if "v" in queryData:
            v = queryData["v"][0]

            if v.startswith('https'):
                url = scrapertools.htmlparser(v)
            else:
                decurl = base64.b64decode(v).decode("utf-8")
                if decurl.startswith('https'):
                    url = scrapertools.htmlparser(decurl)
    return url

def get_lang_from_str(string):

    if 'latino' in string.lower():
        lang = 'Latino'
    elif 'castellano' in string.lower():
        lang = 'Castellano'
    elif 'audio español' in string.lower():
        lang = ['Latino', 'Castellano']
    else:
        lang = 'VOSE'

    return lang

# Algunas series tienen la temporada en el titulo, lo cual hace que TMDB devuelva los datos incorrectos
# Ya que por defecto la temporada se obtiene de otro lado, esto crea una ambigüedad.
# Esta funcion se usa para extraer el numero de temporada correcto del titulo en la url
def get_title_season(url, soup):
    logger.info()

    season = 1
    seasonPattern = '(?i)temporada(?:-|\s*)(\d+)-?'
    
    if re.search(seasonPattern, url):
        season = int(scrapertools.find_single_match(url, seasonPattern))

    elif soup.find("div", class_="TPTblCn") and soup.find("div", class_="TPTblCn").find_previous('div', class_="Title"):
        season_name = soup.find("div", class_="TPTblCn").find_previous('div', class_="Title").get_text(strip=True)

        if re.search(seasonPattern, season_name):
            season = int(scrapertools.find_single_match(season_name, seasonPattern))

    return season

def multiplayer_findvideos(url):
    kwargs["soup"] = False
    data = AlfaChannel.create_soup(url, hide_infobox=True, **kwargs)
    return scrapertools.find_multiple_matches(data.data, r'loadVideo\(\'(.*?)\'\)')