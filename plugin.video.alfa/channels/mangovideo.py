# -*- coding: utf-8 -*-
# -*- Channel MangoVideo -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAdultChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = {}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_quality_movies = []
list_quality_tvshow = []
list_servers = []
forced_proxy_opt = 'ProxySSL'

# https://xxxscenes.net  https://www.netflixporno.net   https://mangoporn.net   https://speedporn.net


canonical = {
             'channel': 'mangovideo', 
             'host': config.get_setting("current_host", 'mangovideo', default=''), 
             'host_alt': ["https://mangoporn.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []

finds = {'find': {'find_all': [{'tag': ['article']}]},     # , 'class': ['movies']             'id': re.compile(r"^browse_\d+")}]},
         'categories': dict([('find', [{'tag': ['li'], 'class': ['genres']}]), 
                             ('find_all', [{'tag': ['li']}])]),
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': dict([('find', [{'tag': ['div','ul'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], '@ARG': 'href'}])]), 
         'next_page_rgx': [['\/page\/\d+', '\/page\/%s'], ['&page=\d+', '&page=%s']], 
         'last_page': {}, 
         'plot': {}, 
             # matches = soup.find('div', id='pettabs').find_all('a')

         'findvideos': dict([('find', [{'tag': ['div'], 'id': 'pettabs'}]),
                             ('find_all', [{'tag': ['a'], '@ARG': 'href'}])]),
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                            # 'list_all_thumbnail': dict([('find', [{'tagOR': ['img'], '@ARG': 'data-wpfc-original-src'},
                                                                  # {'tagOR': ['img'], '@ARG': 'src'}])]),
                            # 'list_all_quality': dict([('find', [{'tag': ['span'], 'class': ['video-o-hd']}]),
                                                      # ('get_text', [{'strip': True}])]),
                            # 'section_cantidad': dict([('find', [{'tag': ['div'], 'class': ['category-videos']}]),
                                                      # ('get_text', [{'strip': True}])])
                           },
         'controls': {'url_base64': False, 'cnt_tot': 36, 'reverse': False, 'profile': 'default'},  ##'jump_page': True, ##Con last_page  aparecerá una línea por encima de la de control de página, permitiéndote saltar a la página que quieras
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="list_all", url=host + "genres/porn-movies/page/1/"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=host + "/ratings/page/1/"))
    itemlist.append(Item(channel=item.channel, title="Trending" , action="list_all", url=host + "/trending/page/1/"))
    itemlist.append(Item(channel=item.channel, title="Año" , action="section", url=host + "genres/porn-movies/page/1/" , extra="Año"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="section", url=host + "genres/porn-movies/page/1/" , extra="Canal"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="section", url=host + "genres/porn-movies/page/1/", extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + "genres/porn-movies/"))
    
    itemlist.append(Item(channel=item.channel, title="-----------------------------------------------" ))
    itemlist.append(Item(channel=item.channel, title="Videos" , action="submenu", url=host + "xxxporn/"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=item.url))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=item.url + "ratings/page/1/"))
    itemlist.append(Item(channel=item.channel, title="Trending" , action="list_all", url=item.url + "trending/page/1/"))
    itemlist.append(Item(channel=item.channel, title="Año" , action="section",url=item.url , extra="Año"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",url=item.url))
    return itemlist





def section(item):
    logger.info()
    
    findS = finds.copy()
    if item.extra == 'Canal':
        findS['categories'] =  dict([('find', [{'tag': ['div'], 'class': ['menu-main-menu-container']}]), 
                                               ('find_all', [{'tag': ['a'], 'href': re.compile(r"/studios/[A-z0-9-]+")}])]) 
    if item.extra == 'Año':
        findS['next_page'] = {}
        findS['controls']['cnt_tot'] = 9999
        findS['categories'] =  dict([('find', [{'tag': ['nav'], 'class': ['releases']}]), 
                                               ('find_all', [{'tag': ['li']}])]) 

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    findS['controls']['action'] = 'findvideos'
    
    return AlfaChannel.list_all(item, finds=findS, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        
        try:
            
            elem_json['url'] = elem.a.get('href', '')
            elem_json['title'] = elem.h3.get_text(strip=True) if elem.h3 else elem.find('div', class_='title').get_text(strip=True)
            elem_json['thumbnail'] = elem.img.get('data-wpfc-original-src', '') or elem.img.get('data-original', '') \
                                     or elem.img.get('data-src', '') \
                                     or elem.img.get('src', '')
            elem_json['stime'] = elem.find(class_='duration').get_text(strip=True) if elem.find(class_='duration') else ''
            elem_json['premium'] = elem.find('i', class_='premiumIcon') \
                                     or elem.find('span', class_=['ico-private', 'premium-video-icon']) or ''
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
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
        
        try:
            elem_json['url'] = elem
            elem_json['language'] = ''
            
            soup = AlfaChannel.create_soup(item.url, **kwargs)
            pornstars = soup.find('div', class_='content').find_all('a', href=re.compile(r"/(?:cast|pornstar)/[A-z0-9-]+"))
            if pornstars:
                for x, value in enumerate(pornstars):
                    pornstars[x] = value.get_text(strip=True)
                pornstar = ', '.join(pornstars)
                # elem_json['star'] = AlfaChannel.unify_custom('', item, {'play': pornstar})
                elem_json['plot'] = pornstar
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
        
        if not elem_json.get('url', ''): continue
        matches.append(elem_json.copy())
    
    return matches, langs


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%spage/1/?s=%s" % (item.url, texto.replace(" ", "+"))
    
    try:
        if texto:
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
