# -*- coding: utf-8 -*-
# -*- Channel PornHub -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

import re
import traceback
if not PY3: _dict = dict; from collections import OrderedDict as dict

from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DictionaryAdultChannel

IDIOMAS = {}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_quality_movies = []
list_quality_tvshow = []
list_servers = []
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'pornhub', 
             'host': config.get_setting("current_host", 'pornhub', default=''), 
             'host_alt': ["https://es.pornhub.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
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

finds = {'find': dict([('find', [{'tagOR': ['ul'], 'id': ['mostRecentVideosSection']}, 
                                 {'tagOR': ['ul'], 'class': ['row-5-thumbs']}, 
                                 {'tag': ['li'], 'class': ['sniperModeEngaged']}]), ('find_parent', [{'tag': []}]), 
                       ('find_all', [{'tag': ['li'], 'class': ['pcVideoListItem']}])]),
         'categories': {'find_all': [{'tag': ['div'], 'class': ['category-wrapper', 'channelsWrapper']}]}, 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': dict([('find', [{'tag': ['div'], 'class': ['paginationGated']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1], '@ARG': 'href'}])]), 
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': {}, 
         'plot': {}, 
         'findvideos': {}, 
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''], ['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'controls': {'url_base64': False, 'cnt_tot': 30, 'reverse': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    itemlist = []
    plot = 'Canal de pruebas de [COLOR yellow][B]AlfaChannelHelper[/B][/COLOR]'

    itemlist.append(Item(channel=item.channel, action="list_all", title="Novedades", url="%svideo?o=cm" % host, 
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Mas visto", url="%svideo?o=mv" % host, 
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Mejor valorado", url="%svideo?o=tr" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Recomendado", url="%srecommended" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Caliente", url="%svideo?o=ht" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Mas largo", url="%svideo?o=lg" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Castellano", url="%slanguage/spanish" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))
    itemlist.append(Item(channel=item.channel, action="section", title="Canal", url="%schannels?o=tr" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot, extra="Canal"))
    itemlist.append(Item(channel=item.channel, action="section", title="PornStar", url="%spornstars?o=t" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot, extra="PornStar"))
    itemlist.append(Item(channel=item.channel, action="section", title="Categorias", url="%scategories" % host,
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot, extra="Categorias"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host, 
                         fanart=item.fanart, thumbnail=item.thumbnail, contentPlot=plot))

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    if item.extra == 'PornStar':
        findS['categories'] = dict([('find', [{'tag': ['ul'], 'class': ['popular-pornstar']}]), 
                                    ('find_all', [{'tag': ['div'], 'class': ['wrap']}])])
        findS['url_replace'] = [['(\/(?:pornstar|model)\/[^$]+$)', r'\1/videos']]

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()
    '''usar primero “profile=default” en AH, A PESAR DE tener “list_all_matches” y luego llama a “list_all_matches'''
    findS['controls']['profile'] = 'default'
    return AlfaChannel.list_all(item, matches_post=list_all_matches, finds=findS, **kwargs)  #  añadido  finds=findS


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    ''' Carga desde AHkwargs la clave “matches” resultado de la ejecución del “profile=default” en AH. 
        En “matches_int” sigue pasando los valores de siempre. '''
    matches_org = AHkwargs.get('matches', [])
    findS = AHkwargs.get('finds', finds)
    ''' contador para asegurar que matches_int y matches_org van sincronizados'''
    x = 0
    for elem in matches_int:
        '''carga el valor del json que ya viene procesado del “profile=default” en AH'''
        elem_json = matches_org[x].copy() if x+1 <= len(matches_org) else {}

        try:
            '''filtros que deben coincidir con los que tiene el “profile=default” en AH para que no descuadren las dos listas  '''
            if elem.find('div', class_='thumbTextPlaceholder'): continue   
            data = elem.find('div', class_='usernameWrap')
            if 'channels' in data.a['href']:
                elem_json['canal'] = data.get_text(strip=True)
                elem_json['extra'] = 'casa'
            else:
                elem_json['star'] = data.get_text(strip=True)

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        '''filtros que deben coincidir con los que tiene el “profile=default” en AH para que no descuadren las dos listas'''
        if not elem.a.get('href', ''): continue 
        
        '''guarda json modificado '''
        matches.append(elem_json.copy())
        '''se suma al contador de registros procesados VÁLIDOS'''
        x += 1

    return matches


def findvideos(item):
    logger.info()

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def play(item):
    logger.info()
    itemlist = []
    
    soup = AlfaChannel.create_soup(item.url, **kwargs)
    if soup.find_all('a', class_="pstar-list-btn"): 
        pornstars = soup.find_all('a', class_="pstar-list-btn")
        for x, value in enumerate(pornstars):
            pornstars[x] = value.get_text(strip=True)
        
        pornstar = ' & '.join(pornstars)
        if item.extra:
            lista = item.contentTitle.split('[/COLOR]')
            pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
            pornstar = pornstar.replace('[/COLOR]', '')
            pornstar = ' %s' %pornstar
            lista.insert (2, pornstar)
            item.contentTitle = '[/COLOR]'.join(lista)
        else:
            color = AlfaChannel.color_setting.get('rating_3', '')
            txt = scrapertools.find_single_match(item.contentTitle, "%s\]([^\[]+)"  % color)
            if not txt.lower() in pornstar.lower():
                pornstar = "%s & %s" %(txt,pornstar)
            item.contentTitle = re.sub(r"%s][^\[]+"  % color, "%s]{0}".format(pornstar) % color, item.contentTitle)
    
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    item.url = "%svideo/search?search=%s&o=mr" % (host, texto)

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


