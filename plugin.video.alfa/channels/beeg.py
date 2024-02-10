# -*- coding: utf-8 -*-
# -*- Channel Beeg -*-
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

IDIOMAS = AlfaChannelHelper.IDIOMAS_A
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_A
list_quality_tvshow = []
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_A
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'beeg', 
             'host': config.get_setting("current_host", 'beeg', default=''), 
             'host_alt': ["https://beeg.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
url_api = "https://store.externulls.com"

# https://store.externulls.com/facts/tag?id=27173&limit=48&offset=0
# https://store.externulls.com/tag/facts/tags?get_original=true&slug=index

timeout = 5
kwargs = {}
kwargs['soup'] = False
kwargs['json'] = True
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []

finds = {'find': {},
         'categories': {}, 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [], 
         'last_page': {}, 
         'plot': {}, 
         'findvideos': {}, 
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''], ['(?i)\s*videos*\s*', ''], ['{', ''], ['}', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'controls': {'url_base64': False, 'cnt_tot': 24, 'reverse': False, 'custom_pagination': True}, 
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Útimos videos", action="list_all", url= url_api + "/facts/tag?id=27173&limit=48&offset=0"))
    itemlist.append(Item(channel=item.channel, title="Canal", action="section", url= url_api + "/tag/facts/tags?get_original=true&slug=index", extra="Canal"))
    itemlist.append(Item(channel=item.channel, title="Pornstar", action="section", url= url_api + "/tag/facts/tags?get_original=true&slug=index", extra="PornStar"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="section", url= url_api + "/tag/facts/tags?get_original=true&slug=index", extra="Categorias"))
    # itemlist.append(item.clone(title="Buscar...", action="search"))
    return itemlist


def section(item):
    logger.info()
    
    return AlfaChannel.section(item, matches_post=section_matches, **kwargs)


def section_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    if not item.orientation:
        item.orientation = "str"
    
    if "Categorias" in item.extra: 
        matches_int = matches_int.get('other', {}).copy()
    elif "Canal" in item.extra: 
        matches_int = matches_int.get('productions', {}).copy()
    else:
        matches_int = matches_int.get('human', {}).copy()
        logger.debug(matches_int)
    
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)
        
        try:
            elem_json['thumbnail'] = ""
            id = elem["id"]
            if elem.get("thumbs", ""):
                th2 = elem.get("thumbs", "")[-1] #[0]
                elem_json['thumbnail'] = "https://thumbs.externulls.com/photos/%s/to.webp" %th2.get('id', '')
            
            # if item.extra == 'Canal' and not elem_json['thumbnail']:
                # continue
            # if item.extra == 'PornStar' and not elem_json['thumbnail']:
                # continue
            
            elem_json['url'] = '%s/facts/tag?slug=%s&limit=48&offset=0' % (url_api, elem.get('tg_slug', '') )
            elem_json['title'] = elem.get('tg_name', '')
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue
        
        if not elem_json['url']: continue
        
        matches.append(elem_json.copy())
    
    return matches


def list_all(item):
    logger.info()
    
    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()
    matches = []
    
    findS = AHkwargs.get('finds', finds)
    
    page = int(scrapertools.find_single_match(item.url, '&offset=([0-9]+)')) + len(matches_int)
    AlfaChannel.next_page_url = re.sub(r"&offset=\d+", "&offset=%s" % page, item.url)
    
    for elem in matches_int:
        elem_json = {}
        
        try:
            id = elem["file"]['id']
            th2= elem["fc_facts"][0]['fc_thumbs']
            stime = elem["file"]["fl_duration"]
            stuff = elem["file"]["stuff"]
            if stuff.get("sf_name", ""):
                title = stuff["sf_name"]
            else:
                title = id
            
            tg_name =elem['tags'][0]['tg_name']
            if elem['tags'][0]['is_person']:
                elem_json['star'] = tg_name
            else:
                elem_json['canal'] = tg_name
            
            plot = ""
            if stuff.get("sf_story", ""):
                plot = stuff["sf_story"]
            
            elem_json['url'] = "%s%s" % (host, id)
            elem_json['title'] = title
            elem_json['thumbnail'] = "https://thumbs-015.externulls.com/videos/%s/%s.jpg" %(id, th2[0])
            elem_json['stime'] = stime
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
    
    item.url = "%sapi/videos.php?params=259200/%s/latest-updates/60/search..1.all..&s=%s&sort=latest-updates&date=all&type=all&duration=all" % (host,item.orientation, texto.replace(" ", "%20")) 
    
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
