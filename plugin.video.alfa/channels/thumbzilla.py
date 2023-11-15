# -*- coding: utf-8 -*-
# -*- Channel Thumbzilla -*-
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


canonical = {
             'channel': 'thumbzilla', 
             'host': config.get_setting("current_host", 'thumbzilla', default=''), 
             'host_alt': ["https://www.thumbzilla.com/"], 
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

finds = {'find': {'find_all': [{'tag': ['div'], 'class': ['phimage']}]},     #'id': re.compile(r"^browse_\d+")}]},
         'categories': {'find_all': [{'tag': ['li'], 'class': ['pornstars']}]}, 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': dict([('find', [{'tag': ['section', 'ul'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], '@ARG': 'href'}])]), 
         'next_page_rgx': [['&page=\d+', '&page=%s'], ['?page=\d+', '?page=%s']], 
         'last_page': {},
         'plot': {}, 
         'findvideos': {'find': [{'string': re.compile(r'"link_url":"[^"]+"')}]},
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                            'list_all_quality': dict([('find', [{'tag': ['span'], 'class': ['hd']}]),
                                                      ('get_text', [{'strip': True}])])
                           },
         'controls': {'url_base64': False, 'cnt_tot': 34, 'reverse': False, 'profile': 'default'},  ##'jump_page': True, ##Con last_page  aparecerá una línea por encima de la de control de página, permitiéndote saltar a la página que quieras
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel,  title="Más Calientes", action="list_all", url=host, thumbnail=get_thumb("channels_adult.png")))
   
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=host + "categories/all?o=cm&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mas Vistos" , action="list_all", url=host + "categories/all?o=mv&t=m&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=host + "categories/all?o=tr&t=m&page=1"))
    itemlist.append(Item(channel=item.channel, title="Tendencia" , action="list_all", url=host + "trending"))
    itemlist.append(Item(channel=item.channel, title="Featured" , action="list_all", url=host + "categories/all?page=1"))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="list_all", url=host + "categories/all?o=lg&page=1"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="section", url=host + "pornstars?page=1", extra="PornStar"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="section", url=host , extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    return itemlist


def section(item):
    logger.info()
    
    findS = finds.copy()
    findS['url_replace'] = [['(\/(?:categories|channels|models|pornstars)\/[^$]+$)', r'\1?o=cm&page=1']]
    if item.extra == 'Categorias':
        findS['categories'] = {'find_all': [{'tag': ['div'], 'class': ['checkHomepage']}]}
        findS['profile_labels']['section_cantidad']: dict([('find', [{'tag': ['span'], 'class': ['count']}]),
                                                           ('get_text', [{'strip': True}])])
    if item.extra == 'PornStar':
        findS['controls']['cnt_tot'] = 48 
    return AlfaChannel.section(item, finds=findS, **kwargs)
    
    # return AlfaChannel.section(item, **kwargs)


def list_all(item):
    logger.info()
    
    return AlfaChannel.list_all(item, **kwargs)


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def play(item):
    logger.info()
    itemlist = []
    
    soup = AlfaChannel.create_soup(item.url, **kwargs)
    
    if soup.find_all('a', href=re.compile("/pornstars/[A-z0-9-]+")):
        pornstars = soup.find_all('a', href=re.compile("/pornstars/[A-z0-9-]+"))
        for x, value in enumerate(pornstars):
            pornstars[x] = value.get_text(strip=True)
        pornstar = ' & '.join(pornstars)
        pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
        lista = item.contentTitle.split('[/COLOR]')
        pornstar = pornstar.replace('[/COLOR]', '')
        pornstar = ' %s' %pornstar
        lista.insert (2, pornstar)
        item.contentTitle = '[/COLOR]'.join(lista)
    
    
    url = ""
    patt = re.compile(r'"link_url":"([^"]+)"')
    data = soup.find(text=patt)
    video = scrapertools.find_single_match(data,'"link_url":"([^"]+)"').replace("\/", "/")
    matches = scrapertools.find_multiple_matches(data, ',"videoUrl":"([^"]+)","quality":"(\d+)"')
    for url, quality in matches:
        url = url.replace("\/", "/")
        if not "?validfrom=" in url: 
            continue
        else:
            itemlist.append(['.mp4 %s' %quality, url])
            itemlist.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    if not url:
        itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=video))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%stags/%s?o=mr&page=1" % (host, texto.replace(" ", "-"))
    
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
