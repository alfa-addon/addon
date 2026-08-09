# -*- coding: utf-8 -*-
# -*- Channel AmigosPorn -*-
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

###    FALTA SERVER    https://amg.upns.live/#x6diue       https://upns.xyz/#x6diue
###    xfuntaxy        https://xfuntaxy.upns.xyz/#onaa9w   https://upns.xyz/#onaa9w 

canonical = {
             'channel': 'amigosporn', 
             'host': config.get_setting("current_host", 'amigosporn', default=''), 
             'host_alt': ["https://amigosporn.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 10
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []


finds = {'find': dict([('find', [{'tag': ['script'], 'id': ['__NEXT_DATA__']}]), 
                       ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'props,pageProps,videos|DEFAULT'}])]),
                 # {'find_all': [{'tag': ['a'], 'class': ['video-card']}]},
         'categories': {'find_all': [{'tag': ['a'], 'class': ['person-card','video-card']}]},
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {},
         'next_page_rgx': [['\?page=\d+', '?page=%s'], ['&page=\d+', '&page=%s']], 
         'last_page': dict([('find', [{'tag': ['nav', 'div'], 'class': ['pagination', 'taxonomy-pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-2], 
                                           '@ARG': 'href', '@TEXT': 'page(?:/|=)(\d+)'}])]), 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['script'], 'id': ['__NEXT_DATA__']}]), 
                             ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'props,pageProps,video|DEFAULT'}])]), 
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', ''],['Placeholder:\s*','']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                           },
         'controls': {'url_base64': False, 'cnt_tot': 24, 'reverse': False, 'profile': 'default'},  ##'jump_page': True, ##Con last_page  aparecerá una línea por encima de la de control de página, permitiéndote saltar a la página que quieras
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=host + "?page=1"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="section", url=host + "studios/?page=1", extra="Canal"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="section", url=host + "actresses/?page=1", extra="PornStar"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="section", url=host + "categories/", extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    findS['url_replace'] = [['(\/(?:categories|actress|studios)\/[^$]+$)', r'\1?page=1']]
    
    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    findS['controls']['action'] = 'findvideos'
    
    if item.c_type in ['search']:
        findS['find'] = dict([('find', [{'tag': ['body']}]), 
                              ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'results|DEFAULT'}])])
        # findS['last_page'] = dict([('find', [{'tag': ['body']}]), 
                                   # ('get_text', [{'tag': '', '@STRIP': False, '@JSON': 'total|DEFAULT'}])])
    
    return AlfaChannel.list_all(item, finds=findS, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    try:
        patron_pages = '\],\s*"total"\s*:\s*(\d+)\s*,\s*"page"\s*:(\d+)'
        items, pages = scrapertools.find_single_match(str(AHkwargs['soup']), patron_pages)
        AlfaChannel.last_page = int((int(items)+finds['controls']['cnt_tot']-1)/finds['controls']['cnt_tot'])
    except Exception:
        logger.error(traceback.format_exc())
    
    for elem in matches_int:
        elem_json = {}
        
        try:
            id = elem['id']
            elem_json['url'] = "%svideo/%s" %(host, id)
            elem_json['thumbnail'] = elem.get('poster_path', '')
            title = elem.get('title', '')
            elem_json['title'] = title.replace(elem.get('actress', '').strip(), '')
            elem_json['star'] = elem.get('actress', '').strip()
            elem_json['canal'] = elem.get('studio', '').strip()
        
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
    
    for elem, valor in matches_int.items():
        elem_json = {}
        
        try:
            if elem.startswith('iframe_url') and valor is not None:
                elem_json['url'] = valor
                elem_json['language'] = ''
            if elem.startswith('actress') and valor is not None:
                pornstar = valor
                pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
            if elem == 'studio' and valor is not None:
               canal = '[%s]' %valor
            item.plot = " %s \n  %s" %(canal, pornstar)

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())

        if not elem_json.get('url', ''): continue
        matches.append(elem_json.copy())

    return matches, langs


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%sapi/search?q=%s&page=1" % (host, texto.replace(" ", "+"))
    
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
