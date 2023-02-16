# -*- coding: utf-8 -*-
# -*- Channel UltraPelisHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import traceback

from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel, DooPlay

IDIOMAS = {'la': 'LAT', 'mx': 'LAT', 'ca': 'CAST', 'su': 'VOSE', 'en': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_quality_movies = ['HD', '1080p']
list_quality_tvshow = ['HDTV', 'HDTV-720p', 'WEB-DL 1080p', '4KWebRip']
list_servers = ['fembed', 'uqload',]

canonical = {
             'channel': 'ultrapelishd', 
             'host': config.get_setting("current_host", 'ultrapelishd', default=''), 
             'host_alt': ["https://ultrapelishd.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
forced_proxy_opt = 'ProxyCF'

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
language = ['LAT']
url_replace = []

AlfaChannel_class = DooPlay(host, canonical=canonical, channel=canonical['channel'], language=language, idiomas=IDIOMAS, 
                            list_language=list_language, list_servers=list_servers, url_replace=url_replace, debug=debug)
finds = AlfaChannel_class.finds
finds['controls']['add_video_to_videolibrary'] = True

AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'genre/estrenos-hd/', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'pelicula/', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Netflix', url=host + 'genre/netflix/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section', url=host,
                         thumbnail=get_thumb('genres', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True), c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_movies + list_quality_tvshow)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    findS = finds.copy()

    findS['categories']['find'][0]['id'][0] = 'menu-item-1957'

    return AlfaChannel.section(item, finds=findS, **kwargs)


def list_all(item):
    logger.info()

    findS = finds.copy()

    if item.c_type == 'search':
        findS['find'] = findS.get('search', findS['find'])
        findS['controls']['get_lang'] = True
        return AlfaChannel.list_all(item, matches_post=AlfaChannel_class.list_all_matches, **kwargs)

    return AlfaChannel.list_all(item, matches_post=AlfaChannel_class.list_all_matches, finds=findS, **kwargs)


def findvideos(item):
    logger.info()

    findS = finds.copy()

    findS['controls']['get_lang'] = True

    return AlfaChannel.get_video_options(item, item.url, matches_post=AlfaChannel_class.findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, finds=findS, **kwargs)


def actualizar_titulos(item):
    logger.info()
    from lib.generictools import update_title
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item


def search(item, texto):
    logger.info()
    
    try:
        texto = texto.replace(" ", "+")
        item.url = host + '?s=' + texto

        if texto != '':
            item.c_type = "search"
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'genre/estrenos-hd/'
        elif categoria == 'infantiles':
            item.url = host + 'genre/infantil/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        itemlist = list_all(item)
        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
