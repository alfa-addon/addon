# -*- coding: utf-8 -*-
# -*- Channel PornGo -*-
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

#  https://www.porngo.com/  https://www.pornpapa.com/   https://www.titshub.com/  https://www.bigwank.tv/
#  https://www.porntry.com/
#  https://www.veryfreeporn.com/   https://www.porncake.com/  https://www.fapguru.com/

canonical = {
             'channel': 'porngo', 
             'host': config.get_setting("current_host", 'porngo', default=''), 
             'host_alt': ["https://www.porngo.com/"], 
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

finds = {'find': {'find_all': [{'tag': ['div'], 'class': ['thumb']}]},     #'id': re.compile(r"^browse_\d+")}]},
         'categories': {'find_all': [{'tag': ['div'], 'class': ['thumb']}]}, 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {},
         'next_page_rgx': [['\/\d+', '/%s/'], ['&page=\d+', '&page=%s']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], 
                                           '@ARG': 'href', '@TEXT': '(?:/|=)(\d+)'}])]), 
         'plot': {}, 
         'findvideos': dict([('find', [{'tag': ['li'], 'class': 'link-tabs-container', '@ARG': 'href'}]),
                             ('find_all', [{'tag': ['a'], '@ARG': 'href'}])]),
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                            # 'list_all_stime': dict([('find', [{'tag': ['span'], 'itemprop': ['thumb__duration']}]),
                                                    # ('get_text', [{'strip': True}])]),
                            # 'list_all_quality': dict([('find', [{'tag': ['span'], 'class': ['thumb__bage']}]),
                                                      # ('get_text', [{'strip': True}])]),
                            'section_cantidad': dict([('find', [{'tag': ['span'], 'class': ['thumb__duration']}]),
                                                      ('get_text', [{'strip': True}])])
                           },
         'controls': {'url_base64': False, 'cnt_tot': 20, 'reverse': False, 'profile': 'default'},
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="porngo" , action="submenu", url= "https://www.porngo.com/", chanel="porngo", thumbnail = "https://i.postimg.cc/p9dFtR2C/porngo.png", canal=True))
    itemlist.append(Item(channel=item.channel, title="pornpapa" , action="submenu", url= "https://www.pornpapa.com/", chanel="pornpapa", thumbnail = "https://i.postimg.cc/Y0cry05W/pornpapa.png", canal=True))
    itemlist.append(Item(channel=item.channel, title="porntry" , action="submenu", url= "https://www.porntry.com/", chanel="porntry", thumbnail = "https://i.postimg.cc/jSdvDGKJ/porntry.png", canal=True))
    itemlist.append(Item(channel=item.channel, title="porncake" , action="submenu", url= "https://www.porncake.com/", chanel="porncake", thumbnail = "https://i.postimg.cc/QxWS1pWj/porncake.png", canal=True))
    itemlist.append(Item(channel=item.channel, title="bigwank" , action="submenu", url= "https://www.bigwank.tv/", chanel="bigwank", thumbnail= "https://i.postimg.cc/N0DNJB4D/bigwank.png"))
    itemlist.append(Item(channel=item.channel, title="fapguru" , action="submenu", url= "https://www.fapguru.com/", chanel="fapguru", thumbnail = "https://i.postimg.cc/dQgpbQ2t/fapguru.png"))
    itemlist.append(Item(channel=item.channel, title="titshub" , action="submenu", url= "https://www.titshub.com/", chanel="titshub", thumbnail = "https://i.postimg.cc/T3GqZBh4/titshub.png"))
    itemlist.append(Item(channel=item.channel, title="veryfreeporn" , action="submenu", url= "https://www.veryfreeporn.com/", chanel="veryfreeporn", thumbnail = "https://i.postimg.cc/QNmTFVM0/veryfreeporn.png"))
    itemlist.append(Item(channel=item.channel, title="xxxfiles" , action="submenu", url= "https://www.xxxfiles.tv/", chanel="xxxfiles", thumbnail = "https://i.postimg.cc/ry0jBvN8/xxxfiles.png"))
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    
    config.set_setting("current_host", item.url, item.chanel)
    AlfaChannel.host = item.url
    AlfaChannel.canonical.update({'channel': item.chanel, 'host': AlfaChannel.host, 'host_alt': [AlfaChannel.host]})
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=item.url + "latest-updates/1/", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Mas Vistos" , action="list_all", url=item.url + "most-popular/1/", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=item.url + "top-rated/1/", chanel=item.chanel))
    if item.canal:
        itemlist.append(Item(channel=item.channel, title="Canal" , action="section", url=item.url + "sites/", extra="Canal", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Pornstar" , action="section", url=item.url + "models/most-viewed/", extra="PornStar", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="section", url=item.url + "categories/", extra="Categorias", chanel=item.chanel))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url, chanel=item.chanel))
    
    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    
    findS['url_replace'] = [['($)', '1/']]
    
    if item.extra == 'Canal':
        findS['controls']['cnt_tot'] = 7
        findS['categories'] = dict([('find', [{'tag': ['div'], 'data-ajax': ['']}]), 
                                    ('find_all', [{'tag': ['div'], 'class': ['main__row']}])])
        return AlfaChannel.section(item, finds=findS, matches_post=section_matches, **kwargs)
    if item.extra == 'Categorias':
        findS['categories'] = dict([('find', [{'tag': ['div'], 'class': ['letter-block']}]), 
                                    ('find_all', [{'tag': ['a']}])])
    
    return AlfaChannel.section(item, finds=findS, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    for elem in matches_int:
        
        elem_json = {}
        try:
            data = elem.find('div', class_=['block-related__bottom'])
            elem_json['url'] = data.a.get("href", '')
            elem_json['title'] = elem.h2.get_text(strip=True)
            if elem.img: elem_json['thumbnail'] = elem.img.get('data-thumb_url', '') or elem.img.get('data-original', '') \
                                                                                     or elem.img.get('data-src', '') \
                                                                                     or elem.img.get('src', '')
            elem_json['cantidad'] = data.a.get_text(strip=True)
        
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    
    if "/search/" in item.url:
        findS['controls']['cnt_tot'] = 10

    return AlfaChannel.list_all(item, finds=findS, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    for elem in matches_int:
        elem_json = {}
        try:
            elem_json['url'] = elem.a.get('href', '')
            elem_json['title'] = elem.a.get('title', '') \
                                 or elem.find(class_='title').get_text(strip=True) if elem.find(class_='title') else ''
            if not elem_json['title']:
                elem_json['title'] = elem.img.get('alt', '')
            elem_json['thumbnail'] = elem.img.get('data-thumb_url', '') or elem.img.get('data-original', '') \
                                     or elem.img.get('data-src', '') \
                                     or elem.img.get('src', '')
            elem_json['stime'] = elem.find(class_='thumb__duration').get_text(strip=True) if elem.find(class_='thumb__duration') else ''
            if elem.find('span', class_=['thumb__bage']):
                elem_json['quality'] = elem.find('span', class_=['thumb__bage']).get_text(strip=True)
            
            if elem.find('a',class_='video_channel'):
                elem_json['canal'] = elem.find('a',class_='video_channel').get_text(strip=True)
            pornstars = elem.find_all('a', href=re.compile("/models/[A-z0-9-]+/"))
            if pornstars:
                for x, value in enumerate(pornstars):
                    pornstars[x] = value.get_text(strip=True)
                elem_json['star'] = ' & '.join(pornstars)
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        matches.append(elem_json.copy())
    return matches


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%ssearch/%s/1/" % (host, texto.replace(" ", "-"))
    
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
