# -*- coding: utf-8 -*-
# -*- Channel DoramedPlay -*-
# -*- BASED ON: Channel DramasJC -*-
# -*- Created for Alfa-addon -*-

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

IDIOMAS = {'VOSE': 'VOSE', 'LAT': 'LAT'}
list_language = list(IDIOMAS.values())
list_quality = []
list_quality_movies = ['HD', '1080p']
list_quality_tvshow = ['HDTV', 'HDTV-720p', 'WEB-DL 1080p', '4KWebRip']
list_servers = ['okru', 'mailru', 'openload']

canonical = {
             'channel': 'doramedplay', 
             'host': config.get_setting("current_host", 'doramedplay', default=''), 
             'host_alt': ["https://doramedplay.com/"], 
             'host_black_list': [], 
             'pattern': '<link\s*rel="stylesheet"\s*id="[^"]*"\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
forced_proxy_opt = 'ProxyCF'

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/movies"
tv_path = '/tvshows'
language = []
url_replace = []

AlfaChannel_class = DooPlay(host, canonical=canonical, channel=canonical['channel'], language=language, idiomas=IDIOMAS, 
                            list_language=list_language, list_servers=list_servers, url_replace=url_replace, debug=debug)
finds = AlfaChannel_class.finds
finds['controls']['add_video_to_videolibrary'] = True

AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(Item(channel=item.channel, title="Doramas", action="list_all", url=host+'tvshows/',
                         c_type='series', thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all", url=host+'movies/',
                         c_type='peliculas', thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabético", action="alfabetico", url=host,
                        thumbnail=get_thumb('alphabet', auto=True), c_type='peliculas'))

    #itemlist.append(Item(channel=item.channel, title="Generos", action="section",
    #                     url=host, thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host,
                               thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_movies + list_quality_tvshow)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):

    if item.title == "Generos":
        finds['categories']['find'][0]['id'][0] = 'menu-item-????'

    return AlfaChannel.section(item, finds=finds, **kwargs)


def alfabetico(item):
    logger.info()

    itemlist = []
    url = 'https://doramedplay.com/wp-json/dooplay/glossary/?term=%s&nonce=506f86d0fc&type=all'

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:

        itemlist.append(item.clone(action="list_all", title=letra, url=url % letra.lower(), json=True))

    return itemlist


def list_all(item):
    logger.info()

    findS = finds.copy()

    findS['year'] = {'find': [{'tag': ['span']}], 'get_text': [{'@TEXT': '(\d{4})'}]}

    if item.c_type == 'search':
        findS['find'] = findS.get('search', findS['find'])
        findS['year'] = {'find': [{'tag': ['span'], 'class': ['year']}], 'get_text': [{'@TEXT': '(\d{4})'}]}
        findS['controls']['get_lang'] = True
        return AlfaChannel.list_all(item, matches_post=AlfaChannel_class.list_all_matches, finds=findS, **kwargs)

    if item.json:
        findS['find'] = {'find': [{'tag': ['body']}], 'get_text': [{'@TEXT': '(.*?)$'}]}

    return AlfaChannel.list_all(item, matches_post=AlfaChannel_class.list_all_matches, finds=findS, **kwargs)


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

    return AlfaChannel.episodes(item, matches_post=AlfaChannel_class.episodesxseason_matches, **kwargs)


def findvideos(item):
    logger.info()

    findS = finds.copy()

    findS['get_language'] = {'find_all': [{'tag': ['img'], '@ARG': 'src'}]}

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=AlfaChannel_class.findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, finds=findS, **kwargs)


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto):
    logger.info()
    
    texto = texto.replace(" ", "+")
    item.url = item.url + '?s=' + texto

    try:
        if texto != '':
            item.c_type = "search"
            return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
