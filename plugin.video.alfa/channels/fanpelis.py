# -*- coding: utf-8 -*-
# -*- Channel Fanpelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from channelselector import get_thumb
from core import servertools
from core.item import Item
from platformcode import config, logger
from lib.AlfaChannelHelper import PsyPlay
from channels import autoplay
from channels import filtertools


list_language = ['LAT']

list_quality = []

list_servers = [
    'fembed',
    'zplayer',
    'streamtape'
    ]

canonical = {
             'channel': 'fanpelis', 
             'host': config.get_setting("current_host", 'fanpelis', default=''), 
             'host_alt': ["https://fanpelis.la/"], 
             'host_black_list': ["https://fanpelis.ac/"], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = PsyPlay(host, movie_path="movies-hd", canonical=canonical)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel,
                         title="Peliculas",
                         action="list_all",
                         url=host + "movies-hd/",
                         thumbnail=get_thumb('movies', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Series",
                         action="list_all",
                         url=host + "series/",
                         thumbnail=get_thumb('tvshows', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         url=host,
                         thumbnail=get_thumb('genres', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Por Año",
                         action="section",
                         url=host,
                         thumbnail=get_thumb('year', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)
                         )
                    )

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def section(item):
    logger.info()

    if item.title == 'Generos':
        return AlfaChannel.section(item, menu_id="19")
    else:
        return AlfaChannel.section(item, menu_id="84669")


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item)


def episodesxseason(item):
    logger.info()

    return AlfaChannel.episodes(item)


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    urls = []
    from lib import players_parse

    soup, matches = AlfaChannel.get_video_options(item.url)

    for elem in matches:

        server = elem.string
        url = elem.a["data-url"]
        url = players_parse.player_parse(url, server, 'https://www.fembed.com')

        if url not in urls:
            itemlist.append(Item(channel=item.channel,
                                 title='%s',
                                 url=url,
                                 action='play',
                                 language="LAT",
                                 infoLabels=item.infoLabels))
            urls.append(url)

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_pelicula_to_library",
                             extra="findvideos",
                             contentTitle=item.contentTitle
                             )
                        )

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    try:
        if texto != '':
            item.url += texto
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host + "movies/"
        elif category == 'infantiles':
            item.url = host + 'genre/animacion'
        elif category == 'terror':
            item.url = host + 'genre/terror'
        itemlist = list_all(item)

        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
