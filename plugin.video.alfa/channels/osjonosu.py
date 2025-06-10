# -*- coding: utf-8 -*-
# -*- Channel osjonosu -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from lib.AlfaChannelHelper import dict
from lib.AlfaChannelHelper import DictionaryAllChannel, DooPlay
from lib.AlfaChannelHelper import Item, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = {"es": "CAST"}
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS
forced_proxy_opt = 'ProxyCF'

canonical = {
             'channel': 'osjonosu', 
             'host': config.get_setting("current_host", 'osjonosu', default=''), 
             'host_alt': ["https://osjonosu.es/"], 
             'host_black_list': ["https://oscar220374.com/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
language = ['CAST']
url_replace = []

AlfaChannel_class = DooPlay(host, canonical=canonical, channel=canonical['channel'], language=language, idiomas=IDIOMAS, 
                            list_language=list_language, list_servers=list_servers, url_replace=url_replace, debug=debug)
finds = AlfaChannel_class.finds
finds['controls']['add_video_to_videolibrary'] = True
finds['controls']['cnt_tot'] = 30

AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', url=host + 'peliculas/', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series/', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Sagas', action='section', url=host,
                         thumbnail=get_thumb('genres', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Infantil', url=host + 'genero/infantiles/', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Tendencia', url=host + 'tendencias/', action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True), c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    findS['categories']['find'][0]['id'][0] = 'menu-item-679'

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()
    
    findS['controls']['get_lang'] = True
    finds['get_language'] = {'find_all': [{'tag': ['div'], 'class': ['idioma'],  '@ARG': 'style'}]}
    finds['get_language_rgx'] = r'(?:flags\/|-)(?:mini_icon_|)(\w+)\.(?:png|jpg|jpeg|webp)'

    return AlfaChannel.list_all(item, matches_post=AlfaChannel_class.list_all_matches, postprocess=post_process_list_all, finds=findS, **kwargs)


def post_process_list_all(elem, new_item, item, **AHkwargs):
    if item.c_type == 'series':
        new_item.language = 'es'
    return new_item


def seasons(item):
    return AlfaChannel.seasons(item, postprocess=post_process_season)


def post_process_season(elem, new_item, item, **AHkwargs):
    new_item.contentChannel = item.channel
    return new_item


def episodesxseason(item, **AHkwargs):
    logger.info()

    """ Aquí le decimos a qué función tienen que saltar para las películas de un solo vídeo """
    kwargs['matches_post_get_video_options'] = findvideos

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    
    for elem in matches_int:
        elem_json = {}
        
        # logger.error(elem)
        try:
            season, episode = elem.find("div", class_="numerando").get_text(strip=True).split(' - ')
            if int(season) != item.contentSeason: continue
            
            elem_json['season'] = int(season or 1)
            elem_json['episode'] = int(episode or 1)
            
            info = elem.find("div", class_="episodiotitle")
            elem_json['url'] = info.a.get("href", "")
            elem_json['title'] = info.a.get_text(strip=True)
            elem_json['language'] = 'cast'
            elem_json['thumbnail'] = elem.find("div", class_="imagen").img.get("data-src", "")
        except Exception as e:
            logger.error(str(e))
            continue

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    findS = finds.copy()

    findS['controls']['get_lang'] = True
    
    return AlfaChannel.get_video_options(item, item.url, matches_post=AlfaChannel_class.findvideos_matches, postprocess=post_process_findvideos,
                                         verify_links=False, findvideos_proc=True, finds=findS, **kwargs)


def post_process_findvideos(elem, new_item, item, **AHkwargs):
    
    if "player.osjonosu" not in new_item.url:
        new_item.server = 'oculto' #este servidor no existe, esto me permite ocultar cualquier enlace que no sea de osjonosu (trailers).
    
    return new_item


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    try:
        texto = texto.replace(" ", "+")
        item.url = host + '?s=' + texto

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