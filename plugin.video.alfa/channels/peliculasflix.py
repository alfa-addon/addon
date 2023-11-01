# -*- coding: utf-8 -*-
# -*- Channel Peliculasflix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    from alfaresolver_py3 import rayo
else:
    from alfaresolver import rayo

from core import httptools, servertools, tmdb
from platformcode import logger, config
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from channels import filtertools
from core.jsontools import json

canonical = {
             'channel': 'peliculasflix', 
             'host': config.get_setting("current_host", 'peliculasflix', default=''), 
             'host_alt': ["https://peliculasflix.co/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

IDIOMAS = {"Castellano": "cast", "Latino": "lat", "Subtitulado": "vose"}
list_language = list(IDIOMAS.keys())
list_quality = ['HD']
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
tmdb_thumb_path = 'https://image.tmdb.org/t/p/original{}'
items_per_page = 10


def read_api(query):
    logger.info()

    post = json.dumps(query)

    url = "https://fluxcedene.net/api/gql"

    referer = host

    headers = {
                'Content-Type':'application/json',
                'x-access-platform':rayo()
              }

    response = httptools.downloadpage(url, headers=headers, post=post, referer=referer, ignore_response_code=True, hide_infobox=True)
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
                         url=host, c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title="Por Género",
                         action="genres",
                         thumbnail=get_thumb('genres', auto=True),
                         url=host, c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title="Por Idioma",
                         action="languages",
                         thumbnail=get_thumb('language', auto=True),
                         url=host, c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host,
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def languages(item):
    logger.info()
    languages = get_all_languages()
    itemlist = list()

    for lang in languages:
        itemlist.append(Item(channel=item.channel, title=lang['name'],
                             action="list_all", code_flix=lang['code_flix'],
                             thumbnail=get_thumb(IDIOMAS[lang['name']], auto=True),
                             url=host, c_type='peliculas'))

    return itemlist


def genres(item):
    logger.info()
    query = {
            "variables":{},
             "query":"{\n"
            +"  listGenres(filter: {platform: \"peliculasgo\"}, sort: NUMBER_DESC) {\n"
            +"    name\n"
            +"    _id\n"
            +"    slug\n"
            +"    platforms {\n"
            +"      _id\n"
            +"      platform\n"
            +"      number\n"
            +"      image_default\n"
            +"      image_tmdb\n"
            +"      image_custom\n"
            +"      __typename\n"
            +"    }\n"
            +"    __typename\n"
            +"  }\n"
            +"}\n"
            }

    itemlist = list()

    data_json = read_api(query)

    if not data_json:
        return itemlist

    for genre in data_json['data']['listGenres']:
        itemlist.append(Item(channel=item.channel, title=genre['name'],
                             action="list_all", slug=genre['slug'],
                             url=host, c_type='peliculas'))

    return itemlist


def list_all(item):
    logger.info()
    # logger.info(item, True)
    page = 1
    if item.page:
        page = item.page

    if item.c_type == 'peliculas':
        addfilter = {}
        addfilter["isPublish"] = True
        if item.slug:
            addfilter["genres"] = [{'slug':item.slug}]
        if item.code_flix:
            addfilter["bylanguages"] = [str(item.code_flix)]
        query = {
                "operationName":"listMovies",
                "variables":{"perPage":32,"sort":"CREATEDAT_DESC","filter":addfilter,"page":page},
                "query":"query listMovies($page: Int, $perPage: Int, $sort: SortFindManyFilmInput, $filter: FilterFindManyFilmInput) {\n"
                        +"  paginationFilm(page: $page, perPage: $perPage, sort: $sort, filter: $filter) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      currentPage\n"
                        +"      hasNextPage\n"
                        +"      hasPreviousPage\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      title\n"
                        +"      name\n"
                        +"      overview\n"
                        +"      runtime\n"
                        +"      slug\n"
                        +"      name_es\n"
                        +"      poster_path\n"
                        +"      poster\n"
                        +"      languages\n"
                        +"      release_date\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}\n"
                }

    return list_all_query(item, query)


def list_all_query(item, query):
    logger.info()

    itemlist = list()

    data_json = read_api(query)

    if not data_json:
        return itemlist

    page_info = []
    # logger.info(item.c_type, True)
    # logger.info(json.dumps(data_json, indent=4), True)
    content_list = []

    if item.c_type == 'search':
        content_list = data_json['data']['searchFilm']

    if item.c_type == 'peliculas':
        content_list = data_json['data']['paginationFilm']['items']
        page_info = data_json['data']['paginationFilm']['pageInfo']

    # logger.info(json.dumps(content_list, indent=4), True)

    if not content_list:
        return itemlist

    for pelicula in content_list:
        if not pelicula.get('languages','') or not any(pelicula['languages']):
            continue
        # logger.info("Languages = {}".format(pelicula['languages']), True)
        item_args = {}

        item_args['channel'] = item.channel
        item_args['slug'] = pelicula['slug']
        item_args['context'] = autoplay.context
        item_args['language'] = get_language_list(pelicula['languages'])
        item_args['contentType'] = 'movie'
        item_args['contentTitle'] = pelicula['name']
        item_args['title'] = pelicula['name']
        item_args['plot'] = pelicula['overview']
        item_args['action'] = 'findvideos'
        item_args['thumbnail'] = tmdb_thumb_path.format(pelicula['poster_path'])
        
        # logger.info(item_args, True)

        new_item = Item(**item_args)

        new_item.context = filtertools.context(new_item, list_language, list_quality)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    # Paginacion
    if page_info:
        if page_info['hasNextPage']:
            itemlist.append(item.clone(
                                       action="list_all",
                                       title=">> {} {}".format(config.get_localized_string(30992), page_info['currentPage']),
                                       page=page_info['currentPage']+1,
                                       thumbnail=get_thumb("next.png")
                                       ))

    return itemlist


def search(item, texto):
    logger.info()

    try:
        if texto != '':
            query = {
                    "operationName":"searchAll",
                    "variables":{"input":texto},
                    "query":"query searchAll($input: String!) {\n"
                        +"  searchFilm(input: $input, limit: 10) {\n"
                        +"    _id\n"
                        +"    slug\n"
                        +"    title\n"
                        +"    name\n"
                        +"    overview\n"
                        +"    languages\n"
                        +"    name_es\n"
                        +"    poster_path\n"
                        +"    poster\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}\n"
                    }
            return list_all_query(item, query)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info()

    itemlist = []

    query = {
            "operationName":"detailFilm",
            "variables":{"slug":item.slug},
            "query":"query detailFilm($slug: String!) {\n  detailFilm(filter: {slug: $slug}) {\n"
                        +"    name\n"
                        +"    title\n"
                        +"    name_es\n"
                        +"    overview\n"
                        +"    languages\n"
                        +"    popularity\n"
                        +"    backdrop_path\n"
                        +"    backdrop\n"
                        +"    links_online {\n"
                        +"      _id\n"
                        +"      server\n"
                        +"      lang\n"
                        +"      link\n"
                        +"      page\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}\n"}

    data_json = read_api(query)
    if not data_json:
        return itemlist
    # logger.info(json.dumps(data_json, indent=4), True)
    content_list = data_json['data']['detailFilm']['links_online']

    # logger.info(json.dumps(content_list, indent=4), True)

    if not content_list:
        return itemlist

    content_list = sorted(content_list, key=lambda x: x['lang'], reverse=True)

    for video in content_list:
        itemlist.append(Item(channel=item.channel, title='%s', url=video['link'], action='play', quality='HD',
                             language=get_language_string(video['lang']), infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools

    itemlist = [i for i in itemlist if i.title != "Directo"]

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(70146),
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def get_all_languages():
    logger.info()

    lang_data = [
        {
            "code_flix": "38",
            "name": "Latino"
        },
        {
            "code_flix": "37",
            "name": "Castellano"
        },
        {
            "code_flix": "192",
            "name": "Subtitulado"
        }
    ]
    # logger.info(json.dumps(data_json, indent=4), True)
    return lang_data


def get_language_list(code_list):
    logger.info()
    languages = get_all_languages()
    lang_list = []
    for code in code_list:
        # logger.info(code, True)
        try:
            if code == 'en':
                lang_list.append('subtitulado')
            else:
                if PY3:
                    lang_list.append(next(filter(lambda lang: lang['code_flix'] == code, languages))['name'])
                else:
                    lang_list.append(filter(lambda lang: lang['code_flix'] == code, languages)[0]['name'])
        except:
            logger.error("The code list could not be parsed : {}".format(str(code_list)))
    # logger.info(lang_list, True)
    return lang_list


def get_language_string(code):
    languages = get_all_languages()
    if code == 'en':
        return 'subtitulado'
    if PY3:
        return next(filter(lambda lang: lang['code_flix'] == code, languages))['name']
    else:
        return filter(lambda lang: lang['code_flix'] == code, languages)[0]['name']
