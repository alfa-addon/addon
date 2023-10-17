# -*- coding: utf-8 -*-
# -*- Channel Playhub -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from core import httptools, servertools, tmdb
from platformcode import logger, config
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from channels import filtertools
from core.jsontools import json

if PY3:
    import urllib.parse as urllib
    from alfaresolver_py3 import yacc
else:
    import urllib
    from alfaresolver import yacc

canonical = {
             'channel': 'playhub', 
             'host': config.get_setting("current_host", 'playhub', default=''), 
             'host_alt': ["https://playhublite.com/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

list_language = ["Subtitulado", "Latino", "Castellano"]
list_quality = ['HD']
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
tmdb_thumb_path = 'https://image.tmdb.org/t/p/original{}'


def read_api(path = '/', query = {}):
    logger.info()
    q = {}
    q['language'] = 'es-ES'
    if query:
        q.update(query)
    query_string = urllib.urlencode(q)

    url = "https://api.playhublite.com/api/v2{}?{}".format(path, query_string)
    logger.info(url, True)
    referer = host

    response = httptools.downloadpage(url, referer=referer, ignore_response_code=True, hide_infobox=True)
    if response.code != 200:
        return False
    return json.loads(response.data)


def read_api_links(c_type, sid, season = 1, episode = 1):
    logger.info()
    if c_type == "episode":
        token = "{}-{}-{}".format(sid, season, episode)
    else:
        token = "{}".format(sid)

    url = "https://api.embedhub.xyz/api/v2/haley?token={}".format(encode_base64(token))
    # logger.info(url, True)
    referer = host

    headers = {'x-hub':'6KGXRDnpdu2gvhOo'}

    response = httptools.downloadpage(url, headers=headers, referer=referer, ignore_response_code=True, hide_infobox=True)
    if response.code != 200:
        return False
    encrypted = json.loads(response.data)

    return yacc(encrypted["data"])


def encode_base64(string):
    from base64 import b64encode
    return b64encode(string.encode('utf8')).decode('utf8')


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="list_all",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         c_type='episode'))

    itemlist.append(Item(channel=item.channel, title="Series",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         c_type='series'))

    add_home_categories(item, itemlist, 'serie')

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         c_type='movies'))

    add_home_categories(item, itemlist, 'movie')

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def add_home_categories(item, itemlist, c_type):
    logger.info()

    data_json = read_api()
    thumbs = {'serie': 'tvshows', 'movie': 'movies'}
    for index, home_item in enumerate(data_json['home']):
        if home_item['type'] == c_type:
            itemlist.append(Item(channel=item.channel, title=home_item['title'],
                                 action="list_all",
                                 thumbnail=get_thumb(thumbs[c_type], auto=True),
                                 index=index, c_type=home_item['type']))


def list_all(item):
    logger.info()

    itemlist = list()

    pagination = False

    if item.c_type in ['series', 'movies']:
        pagination = True
        page = 1
        if item.page:
            page = item.page
        data_json = read_api(path = '/{}'.format(item.c_type), query = {'page':page})
        content_list = data_json['data']
    else:
        data_json = read_api()

    if not data_json:
        return itemlist

    if item.c_type in ['serie', 'movie']:
        index = item.index
        content_list = data_json['home'][index]['data']
    elif item.c_type == 'episode':
        content_list = data_json['episodes']

    for content in content_list:

        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel

        if item.c_type in ['movie', 'movies']:
            item_args['c_type'] = 'movie'
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = content['title']
            item_args['title'] = content['title']
            item_args['_id'] = content['id']
            item_args['action'] = 'findvideos'
            img_path = content['poster_path']
        elif item.c_type == "episode":
            item_args['c_type'] = 'episode'
            item_args['contentType'] = 'episode'
            item_args['contentSerieName'] = content['serie']['name']
            item_args['action'] = 'findvideos'
            infoLabels['season'] = content['season_number']
            infoLabels['episode'] = content['episode_number']
            item_args['title'] = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item_args['contentSerieName'])
            item_args['_id'] = content['serie_id']
            img_path = content['still_path']
        else:
            item_args['contentType'] = 'tvshow'
            item_args['contentSerieName'] = content['name']
            item_args['title'] = content['name']
            item_args['action'] = 'seasons'
            item_args['_id'] = content['id']
            img_path = content['poster_path']

        item_args['infoLabels'] = infoLabels
        item_args['thumbnail'] = tmdb_thumb_path.format(img_path)

        new_item = Item(**item_args)
        new_item.context = filtertools.context(new_item, list_language, list_quality)
        new_item.context.extend(autoplay.context)
        # logger.info(new_item, True)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    # Paginacion
    if pagination and data_json['next_page_url']:
        itemlist.append(item.clone(
                                   action="list_all",
                                   title=">> {} {}".format(config.get_localized_string(30992), page),
                                   page=page+1,
                                   thumbnail=get_thumb("next.png")
                                   ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    if templist[0].contentSeason:
        for tempitem in templist:
            itemlist += seasons(tempitem)[:-1]
    else:
        itemlist = templist[:-1]

    return itemlist


def seasons(item):
    logger.info()

    itemlist = []

    if not isinstance(item.contentSeason, int):
        data_json = read_api(path = '/series/{}'.format(item._id))

        if not data_json:
            return []

        if len(data_json['seasons']) == 1:
            return seasons(item.clone(contentSeason=data_json['seasons'][0]['season_number']))

        for season in data_json['seasons']:
            new_item = item.clone(
                    contentSeason=season['season_number'], 
                    title=(config.get_localized_string(60027) % season['season_number']) if season['season_number'] > 0 else config.get_localized_string(70483),
                    contentPlot=data_json['overview'], 
                    thumbnail=tmdb_thumb_path.format(data_json['poster_path']), 
                    contentType='season'
                )

            itemlist.append(new_item)

        return itemlist

    data_json = read_api(path = '/seasons/{}/{}'.format(item._id, item.contentSeason))
    infoLabels = item.infoLabels
    for episode in data_json['episodes']:
        infoLabels['season'] = episode['season_number']
        infoLabels['episode'] = episode['episode_number']
        title = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item.contentSerieName)
        thumbnail = tmdb_thumb_path.format(episode['still_path'])
        itemlist.append(Item(channel=item.channel, contentType='episode', title=title, contentSerieName=item.contentSerieName, _id=item._id,
                             thumbnail=thumbnail, action='findvideos', c_type='episode', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title=config.get_localized_string(70146), _id=item._id,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def search(item, texto):
    logger.info()

    try:
        if texto != '':
            itemlist = list()
            data_json = read_api(path = '/search', query = {'q':texto})
            if not data_json:
                return itemlist

            itemlist += search_result(item.clone(c_type='movies'), data_json['movies'])
            itemlist += search_result(item.clone(c_type='series'), data_json['series'])

            return itemlist
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def search_result(item, data):
    logger.info()

    itemlist = list()

    for content in data:
        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel

        if item.c_type == 'movies':
            item_args['c_type'] = 'movie'
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = content['title']
            item_args['title'] = content['title']
            item_args['_id'] = content['id']
            item_args['action'] = 'findvideos'
            img_path = content['poster_path']
        else:
            item_args['contentType'] = 'tvshow'
            item_args['contentSerieName'] = content['name']
            item_args['title'] = content['name']
            item_args['action'] = 'seasons'
            item_args['_id'] = content['id']
            img_path = content['poster_path']

        item_args['infoLabels'] = infoLabels
        item_args['thumbnail'] = tmdb_thumb_path.format(img_path)

        new_item = Item(**item_args)
        new_item.context = filtertools.context(new_item, list_language, list_quality)
        new_item.context.extend(autoplay.context)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    content_list = []

    if item.c_type == 'movie':
        content_list = read_api_links(item.c_type, item._id)
    elif item.c_type == 'episode':
        content_list = read_api_links(item.c_type, item._id, item.infoLabels['season'], item.infoLabels['episode'])

    if not content_list:
        return itemlist

    content_list = sorted(content_list, key=lambda x: x['language'], reverse=True)

    # logger.info(content_list, True)
    
    for video in content_list:
        itemlist.append(Item(channel=item.channel, title='%s', url=video['url'], action='play', quality=video['quality'],
                             language=video['language'], infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools

    itemlist = [i for i in itemlist if i.title != "Directo"]

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(70146),
                             _id=item._id, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    # logger.info(categoria, True)
    if categoria in ['series', 'anime']:
        item = Item(channel=canonical['channel'],
                    c_type='episode')
        itemlist = list_all(item)
    if categoria == 'peliculas':
        item = Item(channel=canonical['channel'],
                    index=2, c_type='movie')
        itemlist = list_all(item)
    return itemlist
