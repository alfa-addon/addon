# -*- coding: utf-8 -*-
# -*- Channel LaMovie -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-


import ast
from core import httptools, servertools, tmdb, urlparse
from platformcode import logger, config
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from modules import filtertools
from core.jsontools import json

canonical = {
             'channel': 'lamovie', 
             'host': config.get_setting("current_host", 'lamovie', default=''), 
             'host_alt': ["https://la.movie/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]

list_language = ["Subtitulado", "Latino", "Castellano"]
list_quality = ['HD']
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']

def read_api(type = 'movie', filter = "", _id = 0, season = 1, page = 1, terms = "busca"):
    logger.info()

    try:
        url_filter = urlparse.urlencode({'filter':"{{{0}}}".format(filter)})
    except Exception as e:
        url_filter = urlparse.urlencode({'filter':"{}"})
        logger.error(str(e))

    url_terms = urlparse.quote_plus(str(terms))

    ######"https://la.movie/wp-api/v1/single/episodes/list?_id=7606&season=1&page=2&postsPerPage=15
    ######"https://la.movie/wp-api/v1/player?postId=29285&demo=0"
    ######"https://la.movie/wp-api/v1/search?filter=%7B%7D&postType=any&q=loca&postsPerPage=26"
    ######"https://la.movie/wp-api/v1/listing/movies?filter=%7B%22genres%22%3A%5B8%5D%7D&page=1&orderBy=latest&order=desc&postType=movies&postsPerPage=12"

    if type == 'season':
        url = "{0}wp-api/v1/single/episodes/list?_id={1}&season={2}&page={3}&postsPerPage=15".format(host, _id, season, page)
    elif type == 'links':
        url = "{0}wp-api/v1/player?postId={1}&demo=0".format(host, _id)
    elif type == 'search':
        url = "{0}wp-api/v1/search?{1}&postType=any&q={2}&postsPerPage=26".format(host, url_filter, url_terms)
    else:
        type = "{0}s".format(type)
        url = "{0}wp-api/v1/listing/{1}?{2}&page={3}&orderBy=latest&order=desc&postType={1}&postsPerPage=12".format(host, type, url_filter, page)

    referer = host

    response = httptools.downloadpage(url, referer=referer, ignore_response_code=True, hide_infobox=True)
    if response.code != 200:
        return False
    return json.loads(response.data)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         c_type='movie'))

    itemlist.append(Item(channel=item.channel, title="Series",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         c_type='tvshow'))

    itemlist.append(Item(channel=item.channel, title="Animes",
                         action="list_all",
                         thumbnail=get_thumb('anime', auto=True),
                         c_type='anime'))

    itemlist.append(Item(channel=item.channel, title="Por Genero",
                         action="submenu",
                         thumbnail=get_thumb('genres', auto=True),
                         extra='genres'))

    itemlist.append(Item(channel=item.channel, title="Por Año",
                         action="submenu",
                         thumbnail=get_thumb('year', auto=True),
                         extra='years'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()
    itemlist = list()
        
    itemlist.append(item.clone( title="Películas",
                                action="list_filter",
                                thumbnail=get_thumb('movies', auto=True),
                                c_type='movie'))

    itemlist.append(item.clone( title="Series",
                                action="list_filter",
                                thumbnail=get_thumb('tvshows', auto=True),
                                c_type='tvshow'))

    itemlist.append(item.clone( title="Animes",
                                action="list_filter",
                                thumbnail=get_thumb('anime', auto=True),
                                c_type='anime'))

    return itemlist


def list_filter(item):
    logger.info()
    from core import scrapertools
    
    itemlist = list()
    
    data = httptools.downloadpage(host).data
    site_config = scrapertools.find_single_match(data, r"siteConfig\s*=\s*([^<]+)")

    if site_config:

        site_config = site_config.replace(r"\/", "/")
        pattern = r"{0}:([^\n]+),".format(item.extra)
        filter_data = scrapertools.find_single_match(site_config, pattern)

        try:
            data = ast.literal_eval(filter_data)

            for filter in data:
                filter_string = "\"{0}\":[{1}]".format(item.extra, filter)

                itemlist.append(
                    item.clone(
                        title=str(data[filter]['name']).replace('&amp;', '&'),
                        action="list_all",
                        extra=filter_string
                    )
                )

        except Exception as e:
            logger.error(str(e))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()
    pagination = False
    filter = item.extra

    if item.c_type in ['movie', 'tvshow', 'anime']:
        page = 1
        if item.page:
            page = item.page
        data_json = read_api(type = item.c_type, filter = filter, page = page)
        content_list = data_json['data']['posts']
        pagination = data_json['data']['pagination']
        
    if item.c_type in ['search']:
        data_json = read_api(type = item.c_type, terms = item.terms)
        content_list = data_json['data']['posts']
        pagination = data_json['data']['pagination']

    if not data_json:
        return itemlist

    for content in content_list:

        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel
        
        if 'type' in content:
            item.c_type = content['type'].rstrip('s')

        if item.c_type in ['tvshow', 'episode', 'anime']:
            item_args['contentSerieName'] = content['original_title']
        else:
            item_args['contentTitle'] = content['original_title']

        if item.c_type == 'episode':
            infoLabels['season'] = content['season_number']
            infoLabels['episode'] = content['episode_number']
            item_args['title'] = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item_args['contentSerieName'])
        else:
            item_args['title'] = content['original_title']
            
        item_args['language'] = get_lang(content['lang'])
        item_args['action'] = 'findvideos' if item.c_type in ['movie','episode'] else 'seasons'  
        item_args['c_type'] = item.c_type
        item_args['contentType'] = 'tvshow' if item.c_type == 'anime' else item.c_type
        item_args['_id'] = content['_id']
        item_args['infoLabels'] = infoLabels

        new_item = Item(**item_args)
        new_item.context = filtertools.context(new_item, list_language, list_quality)
        new_item.context.extend(autoplay.context)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    # Paginacion
    if pagination and pagination['next_page_url']:
        itemlist.append(item.clone(
                                   action="list_all",
                                   title=">> {} {}/{}".format(config.get_localized_string(30992), pagination['current_page'], pagination['last_page']),
                                   page=page+1,
                                   thumbnail=get_thumb("next.png")
                                   ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []

    templist = seasons(item)

    if templist[0].contentSeason:
        for season in templist:
            itemlist += seasons(season)
            lastitem = itemlist[-1]
            while isinstance(lastitem.page, int):
                itemlist = itemlist[:-2]
                itemlist += seasons(lastitem)
                lastitem = itemlist[-1]
            itemlist = itemlist[:-1]
    else:
        itemlist += templist
        lastitem = itemlist[-1]
        while isinstance(lastitem.page, int):
            itemlist = itemlist[:-2]
            itemlist += seasons(lastitem)
            lastitem = itemlist[-1]
        itemlist = itemlist[:-1]

    return itemlist


def seasons(item):
    logger.info()

    itemlist = []

    if not isinstance(item.contentSeason, int):

        data_json = read_api(type = 'season', _id = item._id, season = 1, page = 1)

        if not data_json:
            return itemlist

        if len(data_json['data']['seasons']) == 1:
            return seasons(item.clone(contentSeason=data_json['data']['seasons'][0]))

        for season in data_json['data']['seasons'][::-1]:
            season = int(season or 1)
            new_item = item.clone(
                    contentSeason=season,
                    title=(config.get_localized_string(60027) % season) if season > 0 else config.get_localized_string(70483),
                    contentType='season'
                )

            itemlist.append(new_item)
            
        tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

        return itemlist

    page = 1
    if item.page:
        page = item.page

    data_json = read_api(type = 'season', _id = item._id, season = item.contentSeason, page = page)

    if not data_json:
        return itemlist

    infoLabels = item.infoLabels
    for episode in data_json['data']['posts']:
        infoLabels['season'] = episode['season_number']
        infoLabels['episode'] = episode['episode_number']
        itemlist.append(Item(channel=item.channel, contentType='episode', title=episode['title'], 
                             contentSerieName=item.contentSerieName, _id=episode['_id'],
                             action='findvideos', c_type='episode', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title=config.get_localized_string(70146), _id=item._id,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    # Paginacion
    try:
        pagination = data_json['data']['pagination']

        if pagination['next_page_url']:
            itemlist.append(
                item.clone(
                    contentSeason=item.contentSeason,
                    title=">> {} {}/{}".format(config.get_localized_string(30992), pagination['current_page'], pagination['last_page']),
                    page=page+1,
                    thumbnail=get_thumb("next.png"),
                    contentType='season'
                )
            )
    except Exception:
        pass

    return itemlist


def search(item, texto):
    logger.info()
    
    if texto != '':
        return list_all(item.clone(terms=texto))


def findvideos(item):
    logger.info()

    itemlist = []
    content_list = read_api(type = 'links', _id = item._id)
    
    if not content_list:
        return itemlist

    try:
        content = sorted(content_list['data']['embeds'], key=lambda x: x['lang'], reverse=True)
    except Exception as e:
        logger.error(str(e))
        return itemlist
    
    for video in content:
        itemlist.append(Item(channel=item.channel, title='%s', url=video['url'], action='play', quality=video['quality'],
                             language=video['lang'], infoLabels=item.infoLabels))

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


def get_lang(lang_ids):
    langs = list()

    lang_list = {"58651":"latino",
                 "58652":"ingles",
                 "58654":"japones",
                 "58655":"subtitulado",
                 "58653":"castellano"}

    for lang_id in lang_ids:
        langs.append(lang_list[str(lang_id)])

    if len(langs) == 0:
        langs.append('latino')

    return langs