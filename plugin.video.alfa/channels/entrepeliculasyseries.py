# -*- coding: utf-8 -*-
# -*- Channel EntrePeliculasySeries -*-
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
from datetime import datetime

IDIOMAS = AlfaChannelHelper.IDIOMAS_T
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS

# forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'entrepeliculasyseries', 
             'host': config.get_setting("current_host", 'entrepeliculasyseries', default=''), 
             'host_alt': ["https://entrepeliculasyseries.nz/"], 
             'host_black_list': ['https://entrepeliculasyseries.pro/', 'https://entrepeliculasyseries.nu/'],   
             'pattern_proxy': '(?i)<div\s*class="TpRwCont\s*Container">', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, #'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 10
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "movies/"
tv_path = 'series/'
language = []
url_replace = []
year = datetime.now().strftime('%Y')

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['post-lst']}]), 
                       ('find_all', [{'tag': ['article'], 'class': ['post']}])]),
         'categories': {'find_all': [{'tag': ['li'], 'class': ['cat-item']}]}, 
         'search': {}, 
         'get_language': dict([('find', [{'tag': ['span'], 'class': ["Lang"]}]), 
                               ('find_all', [{'tag': ['img']}])]),
         'get_language_rgx': '(?:flags\/|images\/)(\w+)\.(?:png|jpg|jpeg|webp)', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': dict([('find', [{'tag': ['nav'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], 
                                           '@ARG': 'href', '@TEXT': 'page/(\d+)'}])]), 
         'year': {}, 
         'season_episode': {}, 
         'seasons': dict([('find', [{'tag': ['div'], 'id': ['MvTb-episodes']}]), 
                          ('find_all', [{'tag': ['div'], 'class': ['title']}])]), 
         'season_num': [], 
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'episode_url': '', 
         'episodes': dict([('find', [{'tag': ['div'], 'id': ['MvTb-episodes']}]), 
                           ('find_all', [{'tag': ['div'], 'class': ['tt-bx']}])]), 
         'episode_num': {}, 
         'episode_clean': [], 
         'plot': {},
         # 'plot': dict([('find', [{'tag': ['span'], 'class': ['lg margin-bottom']}]), 
                       # ('get_text', [{'tag': '', '@STRIP': True}])]), 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['tt-player-cn']}]},
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie|\s*\(\d{4}\)', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu|calidad\s*', '']],
         'language_clean': [], 
         'url_replace': [], 
         'profile_labels': {
                           },
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 24, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    # itemlist.append(Item(channel=item.channel, title='Perro andaluz', action='findvideos', url='https://entrepeliculasyseries.nz/movies/un-perro-andaluz/', 
                         # thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', action='list_all', url=host + movie_path, 
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))
    
    itemlist.append(Item(channel=item.channel, title='Series',  action='list_all', url=host +  tv_path, 
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))

    # itemlist.append(Item(channel=item.channel, title='Anime',  action='list_all', url=host + 'genero/animacion/', 
                         # thumbnail=get_thumb('anime', auto=True), c_type='series', extra='anime'))
                         
    # itemlist.append(Item(channel=item.channel, title='Dorama',  action='list_all', url=host + 'genero/dorama/', 
                         # thumbnail=get_thumb('anime', auto=True), c_type='series', extra='dorama'))

    itemlist.append(Item(channel=item.channel, title="Por Año", action="sub_menu",
                         thumbnail=get_thumb('years.png') ))

    itemlist.append(Item(channel=item.channel, title="Géneros", action="section", url=host, 
                         thumbnail=get_thumb('channels_anime.png'), extra='generos'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True), c_type='search'))

    # itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()

    n = int(year) - 1928
    
    while n > 0:
        itemlist.append(Item(channel=item.channel, title=str(1928+n), action='list_all', url=host + "release/%s/" %str(1928+n), 
                         thumbnail=get_thumb('years.png') ))
        n -= 1


    # itemlist.append(item.clone(title="Todas", action="list_all", url=item.url))

    # if item.c_type == "peliculas":
        # itemlist.append(item.clone(title="Por Año", action="section", thumbnail=get_thumb('years.png'), url=item.url))

        # itemlist.append(item.clone(title="Géneros", action="section", thumbnail=get_thumb('channels_anime.png')))

    # elif item.c_type == "series":
        # itemlist.append(item.clone(title="Últimas Series", action="list_all", url=host + 'series-recientes/', 
                                   # thumbnail=get_thumb('popular.png')))

        # itemlist.append(item.clone(title="Últimos Episodios", action="list_all", url=host + 'episodios/', 
                                   # thumbnail=get_thumb('on_the_air.png'), c_type='episodios'))

        # itemlist.append(item.clone(title="Episodios en Latino", action="list_all", url=host + 'capitulos-en-espanol-latino/', 
                                   # thumbnail=get_thumb('channels_latino.png'), c_type='episodios'))

        # itemlist.append(item.clone(title="Episodios en Castellano", action="list_all", url=host + 'capitulos-en-castellano/', 
                                   # thumbnail=get_thumb('channels_spanish.png'), c_type='episodios'))

        # itemlist.append(item.clone(title="Episodios Subtitulados", action="list_all", url=host + 'capitulos-en-sub-espanol/', 
                                   # thumbnail=get_thumb('channels_vos.png'), c_type='episodios'))

        # itemlist.append(item.clone(title='Productoras',  action='section', url=host + 'episodios/', 
                                   # thumbnail=get_thumb('channels_anime.png')))

        # itemlist.append(item.clone(title="Géneros", action="section", thumbnail=get_thumb('channels_anime.png')))

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()
    # findS['categories'] = dict([('find', [{'tag': ['div'], 'class': 'list-categories'}]), 
                                    # ('find_all', [{'tag': ['a']}])])

    # if 'Año' in item.title:
        # findS['categories'] = dict([('find', [{'tag': ['div'], 'class': ['Wdgt movies_annee']}]), 
                                    # ('find_all', [{'tag': ['li']}])])
        # findS['controls'].update({'reverse': True})

    # elif 'Productoras' in item.title:
        # findS['categories'] = dict([('find', [{'tag': ['ul'], 'class': ['owl-carousel']}]), 
                                    # ('find_all', [{'tag': ['li'], 'class': ['item']}])])

    # elif 'generos' in item.extra:
        # findS['categories'] = {'find_all': [{'tag': ['li'], 'class': ['cat-item']}]}

    return AlfaChannel.section(item, matches_post=section_matches, finds=findS, **kwargs)
    # return AlfaChannel.section(item, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    # if 'Año' in item.title:
        # for elem in matches_int:
            # elem_json = {}
            # logger.error(elem)

            # elem_json['url'] = elem.a["href"]
            # elem_json['title'] = elem.a.text

            # matches.append(elem_json.copy())

    # elif 'Productoras' in item.title:
        # for elem in matches_int:
            # elem_json = {}
            # logger.error(elem)

            # elem_json['url'] = elem.a.get('href', '')
            # elem_json['title'] = elem.find('div', class_="category-name").get_text(strip=True)
            # elem_json['title'] += ' (%s)' % elem.find('div', class_="category-description").get_text(strip=True)
            # elem_json['thumbnail'] = elem.find('img', class_="ico-category").get('src')
            # if AlfaChannel.response_proxy: elem_json['thumbnail'] = get_thumb('channels_anime.png')

            # matches.append(elem_json.copy())
    
    # if 'Géneros' in item.title:
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        elem_json['url'] = elem.a.get('href', '')
        # if '/%s' % item.c_type not in elem_json['url']:
            # if item.c_type == 'movies' and '/documentales' not in elem_json['url']:
                # continue
            # elif item.c_type == 'series':
                # continue
        elem_json['title'] = elem.get_text(strip=True).replace("(", " (")

        matches.append(elem_json.copy())

    return matches or matches_int


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    # sxe = ''
    logger.debug(matches_int[0])
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            # if item.c_type == 'episodios':
                # try:
                    # sxe = AlfaChannel.parse_finds_dict(elem, findS.get('season_episode', {}), c_type=item.c_type)
                    # if not sxe: continue
                    # elem_json['season'], elem_json['episode'] = sxe.split('x')
                    # elem_json['season'] = int(elem_json['season'] or 1)
                    # elem_json['episode'] = int(elem_json['episode'] or 1)
                # except:
                    # elem_json['season'] = 1
                    # elem_json['episode'] = 1
                # elem_json['year'] = '-'
                # AlfaChannel.get_language_and_set_filter(elem, elem_json)
                # if elem_json['language']:
                    # elem_json['language'] = '*%s' % elem_json['language']
                # else:
                    # elem_json['language'] = '*lat' if 'Latino' in item.title else '*cast' if 'Castellano' in item.title else '*sub'
            
            elem_json['url'] = elem.a.get('href', '').replace('#', '') or elem.find('a', class_="link-title").get('href', '')
            elem_json['title'] = elem.find('h2').get_text(strip=True).strip()
            elem_json['thumbnail'] = elem.img.get('data-src', '') or elem.img.get('src', '') or elem.find('figure', class_='Objf').get('data-src', '')
            elem_json['year'] = elem.find('span', class_='tag').get_text(strip=True).strip()
            # elem_json['year'] = elem_json.get('year', AlfaChannel.parse_finds_dict(elem, findS.get('year', {}), year=True, c_type=item.c_type))
            # elem_json['plot'] = AlfaChannel.parse_finds_dict(elem, findS.get('plot', {}), c_type=item.c_type)
            elem_json['year'] = elem.find('p', class_='entry-content').get_text(strip=True).strip()
            
            if item.c_type == 'peliculas' and movie_path not in elem_json['url']: continue
            if item.c_type == 'series' and tv_path not in elem_json['url']: continue
            # if item.c_type == 'episodios' and epi_path not in elem_json['url']: continue
            # elem_json['mediatype'] = 'movie' if movie_path in elem_json['url'] else (elem_json.get('mediatype') or 'tvshow')
            
            if not elem_json['url']: continue
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
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


def episodesxseason(item):
    logger.info()

    kwargs['matches_post_get_video_options'] = findvideos_matches

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)
        
        if elem.find("span").get_text(strip=True) != str(item.contentSeason): continue
        
        epi_list = elem.find("nav", class_="episodes-nv")
        for epi in epi_list.find_all("a"):
            
            try:
                elem_json['url'] = epi.get("href", "")
                elem_json['season'] = item.contentSeason
                elem_json['episode'] = epi.span.get_text(strip=True).split(".")[-1]
                elem_json['title'] = "%sx%s" % (elem_json['season'], elem_json['episode'])
            
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

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    servers = {'streamwish': 'streamwish', 'filelions': 'tiwikiwi', "stape": "streamtape", 
               "netu": "netu ", "filemoon": "tiwikiwi", "streamwish": "streamwish",
               "voex": "voe", "1fichier": "onefichier"}
    IDIOMAS = {'0': 'LAT', '1': 'CAST', '2': 'VOSE'}
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            url = elem.iframe.get('src', '')
            soup = AlfaChannel.create_soup(url)
            url = soup.find("div", class_="Video").iframe.get("src", '')
            if "/uqlink." in url:
                url = scrapertools.find_single_match(url, "id=([A-z0-9]+)")
                elem_json['url'] = "https://uqload.io/embed-%s.html" % url
                elem_json['language'] = ''
                elem_json['server'] = 'uqload'
                matches.append(elem_json.copy())
            else:
                soup = AlfaChannel.create_soup(url).find('div', class_='OptionsLangDisp')
                for elem in soup.find_all('li'):
                    lang = elem['data-lang']
                    url = elem['onclick']
                    server = elem.span.text.strip()
                    elem_json['url'] = scrapertools.find_single_match(url, "\('([^']+)'")
                    elem_json['server'] = servers.get(server, server)
                    elem_json['language'] = IDIOMAS.get(lang, lang)
                    matches.append(elem_json.copy())
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

    return matches, langs


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)
    

# def play(item):
    
    # itemlist = list()
    # kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'ignore_response_code': True, 'timeout': 5, 
              # 'canonical': {}, 'preferred_proxy_ip': '', 'soup': False, 'forced_proxy_opt': forced_proxy_opt}

    # id = scrapertools.find_single_match(item.url, "h=([^$]+)")
    # headers = item.headers or {"Referer": item.url}

    # post = None
    # base_url = item.url
    # url = ''
    
    # for x in range(2):
        # resp = AlfaChannel.create_soup(base_url, post=post, headers=headers, follow_redirects=False, **kwargs)
        # url = AlfaChannel.get_cookie(AlfaChannel.response_preferred_proxy_ip or base_url, '*nofernu')
        # if url:
            # url = AlfaChannel.do_unquote(url)
            # break
        
        # post = {"h": id}
        # base_url = "%sr.php" % host
        # if resp.code in AlfaChannel.REDIRECTION_CODES:
            # url = resp.headers.get("location", "")
            # break
    
    # if url and not url.startswith("http"):
        # url = "https:" + url
    # item.server = ""
    # itemlist.append(item.clone(url=url))

    # itemlist = servertools.get_servers_itemlist(itemlist)
    
    # return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    kwargs['forced_proxy_opt'] = 'ProxyCF'

    try:
        texto = texto.replace(" ", "+")
        item.url = host + '?s=' + texto

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# def newest(categoria, **AHkwargs):
    # logger.info()
    # kwargs.update(AHkwargs)

    # item = Item()
    # try:
        # if categoria == 'peliculas':
            # item.url = host + 'peliculas/'
        # elif categoria == 'infantiles':
            # item.url = host + 'peliculas-de-animacion/'
        # elif categoria == 'terror':
            # item.url = host + 'peliculas-de-terror/'
        # itemlist = list_all(item)
        # if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            # itemlist.pop()
    # except:
        # for line in sys.exc_info():
            # logger.error("{0}".format(line))
        # return []

    # return itemlist


# def play_netu(item):
    
    # domain = AlfaChannel.obtain_domain(item.url, scheme=True)
    
    # itemlist = list()
    # kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'ignore_response_code': True, 'timeout': 5, 
              # 'CF': True, 'canonical': {}, 'soup': False}
    
    # headers = {"Referer": item.url}
    # url = '%s?=&best=t' % item.url
    
    # resp = AlfaChannel.create_soup(url, headers=headers, follow_redirects=False, 
                                   # forced_proxy_opt=forced_proxy_opt, **kwargs)
    # if resp.code in AlfaChannel.REDIRECTION_CODES:
        # url = resp.headers.get("location", "")
    # else:
        # return []
    
    # headers = {"Referer": url}
    # domain_e = AlfaChannel.obtain_domain(url, scheme=True)
    # url = '%s/f/%s?http_referer=%s' % (domain_e, scrapertools.find_single_match(url, "\?v=([^$]+)"), AlfaChannel.do_quote(domain+'/'))
    # resp = AlfaChannel.create_soup(url, headers=headers, follow_redirects=False, 
                                   # forced_proxy_opt=forced_proxy_opt, **kwargs)
    
    url = scrapertools.find_single_match(resp.data, "self\.location\.replace\('([^']+)'").replace('#', '%23')
    # url = scrapertools.find_single_match(resp.data, "self\.location\.replace\('([^']+)'").split('&')[0]
    # url = AlfaChannel.urljoin(domain_e, url)
    # resp = AlfaChannel.create_soup(url, headers=headers, follow_redirects=False, 
                                   # forced_proxy_opt=forced_proxy_opt, **kwargs)
                                   
    # url = scrapertools.find_single_match(resp.data, "self\.location\.replace\('([^']+)'")
    # url = AlfaChannel.urljoin(domain_e, url)
    # resp = AlfaChannel.create_soup(url, headers=headers, follow_redirects=False, 
                                   # forced_proxy_opt=forced_proxy_opt, **kwargs)
    
    # logger.error(resp.data)
    
    # item.server = ""
    # itemlist.append(item.clone(url=url))
    
    # itemlist = servertools.get_servers_itemlist(itemlist)
    
    # return itemlist
