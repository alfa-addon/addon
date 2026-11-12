# -*- coding: utf-8 -*-
# -*- Channel AnimeJara -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Develop Group -*-

from core import urlparse as alfa_urlparse
import sys, math
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from lib.AlfaChannelHelper import dict
from lib.AlfaChannelHelper import DictionaryAllChannel
from lib.AlfaChannelHelper import re, traceback, base64, jsontools
from lib.AlfaChannelHelper import Item, scrapertools, get_thumb, config, logger, filtertools, autoplay, renumbertools

IDIOMAS = AlfaChannelHelper.IDIOMAS_ANIME
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['filemoon', 'lulustream', 'streamtape', 'streamwish', 'uqload', 'vidhidepro', 'voe']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'animejara', 
             'host': config.get_setting("current_host", 'animejara', default=''), 
             'host_alt': ['https://animejara.com/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []
home_page = 'inicio'

def div30(match):
    """
    Divide un número entre 30 y redondea hacia arriba.
    Retorna '1' por defecto si algo falla.
    """
    try:
        if not match:
            return '1'
        
        numero_str = match.group(1)
        if not numero_str:
            return '1'
        
        if not numero_str.isdigit():
            return '1'
        
        numero = int(numero_str)
        if numero == 0:
            return '1'
        
        return str(math.ceil(numero / 30))
    except (AttributeError, IndexError, ValueError, TypeError):
        logger.error("Error en div30 con match: %s" % match)
        return '1'
    

finds = {'find': dict([('find_all', [{'tag': ['a'], 'class': ['anime-card']}])]), 
         'categories': dict([('find', [{'tag': ['select'], 'id': ['filtro-tag']}]),
                             ('find_all', [{'tag': ['option']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [[r'\?paged=\d+', '?paged=%s']],
         'last_page': {'find': [{'tag': ['span'], 'id': ['total-animes'], '@SUB': [['(\d+)', div30]]}]},
         'year': {}, 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tag': ['div'], 'class': ['season-tab']}]},
         'season_num': {},
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['script'], 'string': re.compile('const\s+TEMPORADAS_DATA\s+=')}]),
                           ('get_text', [{'tag': '', '@STRIP': True, '@TEXT_M': "(?:ANIME_SLUG|TEMPORADAS_DATA)\s+=\s+(.+?);\s*\n",
                                          '@DO_SOUP': False}])]),
         'episode_num': [], 
         'episode_clean': [['(?i)\s*-\s*Proximo\s*Capitulo\:?\s*(\d+-[A-Za-z]+-\d+)', ''],
                           ['(?i)HD|Español Castellano|Sub Español|Español Latino', '']], 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['div'], 'class': ['botones-idioma']}]),
                             ('find_all', [{'tag': ['div'], 'class': 'lang-name'}])]),
         'title_clean': [['(?i)HD|Español Castellano|Sub Español|Español Latino|ova\s+\d+\:|OVA\s+\d+|\:|\((.*?)\)|\s19\d{2}|\s20\d{2}', ''],
                         ['(?i)\s*Temporada\s*\d+', '']],
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

    itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=alfa_urlparse.urljoin(host, home_page), action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='new_episodes'))

    itemlist.append(Item(channel=item.channel, title='Últimos Animes', url=alfa_urlparse.urljoin(host, home_page), action='list_all',
                         thumbnail=get_thumb('newest', auto=True), c_type='newest'))
    
    itemlist.append(Item(channel=item.channel, title='Series En Emision', url=alfa_urlparse.build_url(host, 'catalogo', query='paged=1&tipo=serie&estado=Emision'), action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))
    
    itemlist.append(Item(channel=item.channel, title='Series Finalizadas', url=alfa_urlparse.build_url(host, 'catalogo', query='paged=1&tipo=serie&estado=Finalizado'), action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Películas', url=alfa_urlparse.build_url(host, 'catalogo', query='paged=1&tipo=pelicula'), action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Generos',  action='section', url=alfa_urlparse.build_url(host, 'catalogo'),
                         thumbnail=get_thumb('genres', auto=True), extra='genre'))
    
    itemlist.append(Item(channel=item.channel, title='Años',  action='section', url=alfa_urlparse.build_url(host, 'catalogo'),
                         thumbnail=get_thumb('year', auto=True), extra='year'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = renumbertools.show_option(item.channel, itemlist, status=canonical.get('renumbertools', False))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    findS = finds.copy()
    
    findS['url_replace'] = [[r'(%s)' % re.escape(host), r'\1catalogo?paged=1&tag=']]
    
    if item.extra == 'year':
        findS['categories'] = dict([('find', [{'tag': ['select'], 'id': ['filtro-anio']}]),
                                    ('find_all', [{'tag': ['option']}])])
        findS['url_replace'] = [[r'(%s)' % re.escape(host), r'\1catalogo?paged=1&anio=']]
    
    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()
    
    if item.c_type == 'new_episodes':
        findS['find'] = dict([('find_all', [{'tag': ['a'], 'class': ['ep-card']}])])
    if item.c_type == 'newest':
        findS['find'] = dict([('find_all', [{'tag': ['a'], 'class': ['anime-card']}])])
    if item.extra == 'genre':
        kwargs['return_data_on_error'] = True

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []

    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        logger.error(elem)

        try:
            if item.c_type == 'new_episodes':
                sxe = elem.find("span", class_="ep-tag").get_text(strip=True)
                try:
                    season, episode = sxe.split('x')
                    elem_json['season'] = int(season)
                    elem_json['episode'] = int(episode)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'

                lang_tag = elem.find("span", class_="lang-tag")
                if lang_tag:
                    ep_langs = lang_tag.find_all("img")
                    elem_json['language'] = []
                    for ep_lang in ep_langs:
                        elem_json['language'].append(get_lang_from_str(ep_lang.attrs['alt']))
                
                elem_json['title'] = elem.find("div", class_="ep-name").get_text(strip=True)
            else:
                if item.c_type == 'newest':
                    season_tag = elem.find("div", class_="badge-season")
                    if season_tag:
                        if 'SEASON' in season_tag.get_text(strip=True):
                            elem_json['mediatype'] = 'tvshow'
                            elem_json['season'] = 1
                            season_tag = season_tag.get_text(strip=True).split(" ", 1)
                            if len(season_tag) == 2:
                                elem_json['season'] = int(season_tag[1]) or 1
                            if elem_json['season'] > 1:
                                elem_json['action'] = 'episodesxseason'
                                elem_json['title_subs'] = [
                                    ' [COLOR %s][B]%s[/B][/COLOR] ' % \
                                    (AlfaChannel.color_setting.get('movies', 'white'), 
                                    'Temporada %s' % elem_json['season'])
                                ]
                        else:
                            elem_json['mediatype'] = 'movie'
                else:
                    card_langs = elem.find("div", class_="card-langs")
                    if card_langs:
                        elem_json['language'] = []
                        card_langs = card_langs.find_all("img", class_="lang-icon")
                        for lang_img in card_langs:
                            elem_json['language'].append(get_lang_from_str(lang_img.attrs['alt']))
                    
                    try:
                        year = elem.find("span", class_="card-year").get_text(strip=True)
                    except Exception:
                        year = '-'
                    elem_json['year'] = year
                        
                    try:
                        meta_type = elem.find("span", class_="meta-type").get_text(strip=True)
                    except Exception:
                        meta_type = ''
                    
                    elem_json['mediatype'] = 'tvshow' if meta_type != "PELÍCULA" else 'movie'
                
                if item.c_type == 'series' and elem_json['mediatype'] == 'movie':
                    continue
                if item.c_type == 'peliculas' and elem_json['mediatype'] == 'tvshow':
                    continue
                
                elem_json['title'] = elem.find("h3", class_="card-title").get_text(strip=True)
            
            elem_json['url'] = elem.get('href', '')

            # En episodios permite desde el menú contextual ir a la Serie
            # https://animejara.com/episode/saikyou-no-ousama-nidome-no-jinsei-wa-nani-wo-suru-2x1/
            # https://animejara.com/anime/saikyou-no-ousama-nidome-no-jinsei-wa-nani-wo-suru
            if item.c_type == 'new_episodes' and elem_json['url']:
                elem_json['go_serie'] = {'url': re.sub('-\d+x\d+/$', '', elem_json['url']).replace('/episode/', '/anime/')}

            elem_json['quality'] = 'HD'
            elem_json['context'] = autoplay.context

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

    soup = AHkwargs.get('soup', '')

    return AlfaChannel.episodes(item, data=soup, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    if len(matches_int) is not 2:
        return matches
    
    ANIME_SLUG = matches_int[0].strip("'")
    try:
        TEMPORADAS_DATA = jsontools.load(matches_int[1].strip())
    except Exception:
        logger.error("Error al cargar TEMPORADAS_DATA")
        logger.error(matches_int[1])
        logger.error(traceback.format_exc())
        return matches
    
    soup = AHkwargs['soup']
    nextChapterDate = False
    proximos = soup.find_all('div', class_="proximo-item")
    if proximos and proximos[-1].span:
        fecha = proximos[-1].span.find(text=True, recursive=False).strip()
        # 11 Abril 2026
        nextChapterDateRegex = r'(?i)(\d+\s+[A-Za-z]+\s+\d+)'
        if re.search(nextChapterDateRegex, fecha):
            nextChapterDate = scrapertools.find_single_match(fecha, nextChapterDateRegex)
    
    for temporada in TEMPORADAS_DATA:
        try:
            season = int(temporada['numero_temporada'])
        except Exception:
            logger.error(temporada)
            logger.error(traceback.format_exc())
            continue
        
        if season != item.contentSeason: continue
        
        for i, episodio in enumerate(temporada['episodios']):
            elem_json = {}
            elem_json['season'] = season
            elem_json['episode'] = int(episodio['numero_episodio'])
            elem_json['url'] = alfa_urlparse.build_url('https://animejara.com', u'/episode/{}-{}x{}/'.format(ANIME_SLUG, elem_json['season'], elem_json['episode']))
            elem_json['title'] = 'Episodio %sx%s' % (elem_json['season'], elem_json['episode'])
            elem_json['language'] = [get_lang_from_str(lang) for lang in episodio.get('idiomas', [])]
            elem_json['quality'] = 'HD'
            if nextChapterDate:
                elem_json['next_episode_air_date'] = nextChapterDate

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()

    kwargs['return_data_on_error'] = True
    kwargs['matches_post_episodes'] = episodesxseason_matches
    
    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    
    try:
        pattern = re.compile('const\s+(?:movieLinks|enlaces)\s+=')
        jvscpt = response.soup.find('script', string=pattern).string.strip()
        match = scrapertools.find_single_match(str(jvscpt), r'(?:movieLinks|enlaces)\s+=\s+([^;]+);\s*\n')
        iframes_languages = jsontools.load(match)
    except Exception as e:
        logger.error("Error parsing videos data: %s", e)
        return matches

    def add_match(url, lang):
        uriData = AlfaChannel.urlparse(url)
        if re.search(r'hqq|netuplayer|krakenfiles', uriData.hostname, re.IGNORECASE):
            return
        elem_json = {}
        elem_json['url'] = url
        elem_json['title'] = '%s'
        elem_json['language'] = lang
        elem_json['quality'] = 'HD'
        if not elem_json.get('url'): return
        matches.append(elem_json.copy())
    
    for index, langbtn in enumerate(matches_int):
        language = get_lang_from_str(langbtn.get_text(strip=True))
        iframe_url = iframes_languages[index]
        videos = multiplayer_findvideos(iframe_url)
        for video_url in videos:
            add_match(video_url, language)

    return matches, langs


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        _url_query_texto = texto
        texto = AlfaChannel.do_quote(texto, '', plus=True) 
        item.url = alfa_urlparse.build_url(item.url, 'catalogo/', query=[('q', _url_query_texto)])

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
            item.url = alfa_urlparse.urljoin(host, home_page)
            item.c_type = 'new_episodes'
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

    if 'latino' in string.lower():
        lang = 'Latino'
    elif 'castellano' in string.lower():
        lang = 'Castellano'
    else:
        lang = 'VOSE'

    return lang


def multiplayer_findvideos(url):
    kwargs["canonical"] = {}
    kwargs["headers"] = {}
    kwargs["soup"] = False
    kwargs["canonical"]["proxy"] = False
    kwargs["canonical"]["proxy_web"] = False
    kwargs["headers"]["Referer"] = host
    data = AlfaChannel.create_soup(url, **kwargs)

    return scrapertools.find_multiple_matches(data.data, r'playVideo\(&quot;\s*(.+?)\s*&quot;\)')