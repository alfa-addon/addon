# -*- coding: utf-8 -*-
# -*- Channel Doramasflix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


from core import jsontools, httptools, servertools, tmdb
from platformcode import logger, config
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from modules import filtertools
from core.jsontools import json

TAG_CHANNEL_LANGUAGE_DATA = "channel_language_data"

canonical = {
             'channel': 'doramasflix', 
             'host': config.get_setting("current_host", 'doramasflix', default=''), 
             'host_alt': ["https://doramasflix.co/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

list_language = ["Subtitulado", "Latino", "Castellano", "Coreano", "Japonés", "Mandarín", "Tailandés", "Filipino", "Indonesio", "Vietnamita", "Portugués"]
list_quality = ['HD']
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
tmdb_thumb_path = 'https://image.tmdb.org/t/p/original{}'
items_per_page = 10


def read_api(query):
    logger.info()

    post = json.dumps(query)
    
    # logger.error(post)

    url = "https://sv7.fluxcedene.net/graphql"

    referer = host

    headers = {
                'Content-Type':'application/json'
              }

    response = httptools.downloadpage(url, headers=headers, post=post, referer=referer, ignore_response_code=True, hide_infobox=True)
    if response.code != 200:
        return False
    return json.loads(response.data)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel, title="Doramas",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=host, c_type='doramas'))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host, c_type='peliculas'))
                         
    itemlist.append(Item(channel=item.channel, title="TvShows",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=host, c_type='TvShows'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host,
                         thumbnail=get_thumb('search', auto=True),
                         c_type='search'))
                         
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()
    # logger.info(item, True)
    page = 1
    if item.page:
        page = item.page

    if item.c_type in ['doramas', 'TvShows']:
        addfilter = {}
        addfilter["isTVShow"] = False if item.c_type == 'doramas' else True
        # logger.info(addfilter, True)
        query = {
                "operationName":"PaginationDorama",
                "variables":{"page":page,"limit":items_per_page,"filter":addfilter},
                "query":"query PaginationDorama($sort: SortDorama, $limit: Int, $filter: FilterDoramasInput, $page: Int) {\n"
                        +"  paginationDorama(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                        +"    hasNextPage\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      isTVShow\n"
                        +"      poster_path\n"
                        +"      poster\n"
                        +"      backdrop_path\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
                }

    if item.c_type == 'peliculas':
        addfilter = {}
        query = {
                "operationName":"PaginationMovie",
                "variables":{"page":page,"limit":items_per_page,"filter":addfilter},
                "query":"query PaginationMovie($sort: SortMovie, $limit: Int, $filter: FilterMoviesInput, $page: Int) {\n"
                        +"  paginationMovie(sort: $sort, limit: $limit, filter: $filter, page: $page) {\n"
                        +"    hasNextPage\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      slug\n"
                        +"      languages\n"
                        +"      poster_path\n"
                        +"      poster\n"
                        +"      backdrop_path\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
                }

    return list_all_query(item, query, page)


def list_all_query(item, query, page):
    logger.info()

    itemlist = list()

    data_json = read_api(query)

    if not data_json:
        return itemlist

    page_info = False

    content_list = []

    if item.c_type == 'ultimos_episodios':
        content_list = data_json['data']['premiereEpisodes']

    if item.c_type == 'search':
        content_list = data_json['data']['searchDorama']
        content_list.extend(data_json['data']['searchMovie'])

    if item.c_type == 'peliculas':
        content_list = data_json['data']['paginationMovie']['items']
        page_info = data_json['data']['paginationMovie']['hasNextPage']

    if item.c_type in ['doramas', 'TvShows']:
        content_list = data_json['data']['paginationDorama']['items']
        page_info = data_json['data']['paginationDorama']['hasNextPage']

    if not content_list:
        return itemlist

    if item.c_type != 'ultimos_episodios':
        languages = get_all_languages()

    for dorama in content_list:
        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel
        item_args['url'] = dorama['_id']
        item_args['extra'] = dorama['slug']
        
        item_args['context'] = autoplay.context
        if dorama.get('languages',''):
            item_args['language'] = get_language_list(languages, dorama['languages'])

        if dorama['__typename'] == "Movie":
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = dorama['name']
            item_args['title'] = dorama['name']
            item_args['action'] = 'findvideos'
            img_path = dorama['poster_path'] if dorama.get('poster_path', '') else dorama['backdrop_path']
        elif dorama['__typename'] == "EpisodeMin":
            item_args['contentType'] = 'episode'
            item_args['contentSerieName'] = dorama['serie_name']
            item_args['action'] = 'findvideos'
            infoLabels['season'] = dorama['season_number']
            infoLabels['episode'] = dorama['episode_number']
            item_args['title'] = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item_args['contentSerieName'])
            img_path = dorama['still_path']
        else:
            item_args['contentType'] = 'tvshow'
            item_args['contentSerieName'] = dorama['name']
            item_args['title'] = dorama['name']
            item_args['action'] = 'seasons'
            img_path = dorama['poster_path'] if dorama.get('poster_path', '') else dorama.get('backdrop_path', '')

        infoLabels['filtro'] = img_path
        item_args['infoLabels'] = infoLabels
        item_args['thumbnail'] = tmdb_thumb_path.format(img_path)
        
        # logger.info(item_args, True)

        new_item = Item(**item_args)

        new_item.context = filtertools.context(new_item, list_language, list_quality)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)
    
    # Paginacion
    if page_info:
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

    season = 1 if not item.contentSeason else item.contentSeason

    query = {"operationName":"detailSeasonExtra",
             "variables":{"slug":item.extra,"season_number":season},
             "query":"query detailSeasonExtra($slug: String!, $season_number: Int!) {\n"
                    +"  listSeasons(sort: NUMBER_ASC, filter: {serie_slug: $slug}) {\n"
                    +"    slug\n"
                    +"    season_number\n"
                    +"    poster_path\n"
                    +"    serie_backdrop_path\n"
                    +"    air_date\n"
                    +"    serie_name\n"
                    +"    trailer\n"
                    +"    backdrop\n"
                    +"    overview\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    emision\n"
                    +"    pause\n"
                    +"    uploading\n"
                    +"    commingSoon\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"  listEpisodes(\n"
                    +"    sort: NUMBER_ASC\n"
                    +"    filter: {serie_slug: $slug, season_number: $season_number}\n"
                    +"  ) {\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    slug\n"
                    +"    serie_name\n"
                    +"    serie_id\n"
                    +"    still_path\n"
                    +"    air_date\n"
                    +"    season_number\n"
                    +"    episode_number\n"
                    +"    languages\n"
                    +"    backdrop\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"}

    data_json = read_api(query)
    if not data_json:
        return []
    # logger.info(json.dumps(data_json, indent=4), True)

    itemlist = []

    # He encontrado alguna serie que venian las temporadas duplicadas
    clean_up_seasons(data_json['data']['listSeasons'])
    
    if not item.contentSeason and len(data_json['data']['listSeasons']) > 1:
        try:
            for season in data_json['data']['listSeasons']:
                new_item = item.clone(
                        contentSeason=season['season_number'], 
                        title=(config.get_localized_string(60027) % season['season_number']) if season['season_number'] > 0 else config.get_localized_string(70483),
                        contentPlot=season['overview'], 
                        thumbnail=tmdb_thumb_path.format(season['poster_path']), 
                        contentType='season'
                    )

                itemlist.append(new_item)
        except:
            pass

        return itemlist

    infoLabels = item.infoLabels.copy()
    try:
        for episode in data_json['data']['listEpisodes']:
            infoLabels['season'] = int(episode['season_number']) or 1
            infoLabels['episode'] = int(episode['episode_number']) or 1
            title = "{0}x{1} Episodio {1}".format(infoLabels['season'], infoLabels['episode'])
            new_item = Item(
                channel = item.channel,
                title = title,
                url = episode['_id'],
                extra = episode['slug'],
                action = 'findvideos',
                infoLabels = infoLabels,
                contentType = 'episode'
            )
            itemlist.append(new_item)
    except:
        pass

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.videolibrary:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                title = config.get_localized_string(70146),
                url = item.url,
                slug = item.slug
            )
        )

    return itemlist


def clean_up_seasons(seasons_list):
    season_number_set = set()
    for i in seasons_list[:]:
        if i['season_number'] in season_number_set:
            seasons_list.remove(i)
        else:
            season_number_set.add(i['season_number'])


def search(item, texto):
    logger.info()

    try:
        if texto != '':
            query = {
                    "operationName":"searchAll",
                    "variables":{"input":texto},
                    "query":"query searchAll($input: String!) {\n"
                            +"  searchDorama(input: $input, limit: 5) {\n"
                            +"    _id\n"
                            +"    slug\n"
                            +"    languages\n"
                            +"    name\n"
                            +"    name_es\n"
                            +"    poster_path\n"
                            +"    rating\n"
                            +"    poster\n"
                            +"    episode_time\n"
                            +"    __typename\n"
                            +"  }\n"
                            +"  searchMovie(input: $input, limit: 5) {\n"
                            +"    _id\n"
                            +"    name\n"
                            +"    name_es\n"
                            +"    languages\n"
                            +"    slug\n"
                            +"    runtime\n"
                            +"    rating\n"
                            +"    poster_path\n"
                            +"    poster\n"
                            +"    __typename\n"
                            +"  }\n"
                            +"}"
                    }
            return list_all_query(item, query, 1)
        else:
            return []
    except Exception as e:
        logger.error(str(e))
        return []


def new_episodes(item):
    logger.info()
    query = {
            "operationName":"premiereEpisodes",
            "variables":{"limit":20},
            "query":"query premiereEpisodes($limit: Float!) {\n"
                    +"  premiereEpisodes(limit: $limit) {\n"
                    +"    _id\n"
                    +"    air_date\n"
                    +"    serie_name\n"
                    +"    serie_name_es\n"
                    +"    slug\n"
                    +"    still_path\n"
                    +"    season_number\n"
                    +"    episode_number\n"
                    +"    still_image\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"
            }
    item.c_type='ultimos_episodios'
    return list_all_query(item, query, 1)


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # logger.info(categoria, True)
    if categoria == 'series':
        itemlist = new_episodes(item)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    content_list = []
    query = {        
            "operationName":"listProblemsItem",
            "variables":{"problem_id":item.url},
            "query":"query listProblemsItem($problem_id: ID!) {\n"
                    +"  listProblems(\n"
                    +"    filter: {problem_id: $problem_id}\n"
                    +"  ) {\n"
                    +"    server{\n"
                    +"      link\n"
                    +"      lang\n"
                    +"    }\n"
                    +"  }\n"
                    +"}"
            }
    data_json = read_api(query)

    
    if not data_json:
        return itemlist


    for server in data_json['data']['listProblems']:
        if not server['server'] in content_list:
            if server['server'] and not in_dictlist(content_list, 'link', server['server']['link']):
                # logger.error(server['server'])
                content_list.append(server['server'])

    # logger.info(json.dumps(content_list, indent=4), True)

    if not content_list:
        return itemlist

    languages = get_all_languages()

    content_list = sorted(content_list, key=lambda x: x['lang'], reverse=True)

    for video in content_list:
        itemlist.append(Item(channel=item.channel, title='%s', url=video['link'], action='play', quality='HD',
                             language=get_language_string(languages, video['lang']), infoLabels=item.infoLabels))

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


def in_dictlist(dictlist, key, value):
    logger.info()
    for entry in dictlist:
        if entry[key] == value:
            return True
    return False


def get_all_languages():
    logger.info()

    lang_data = get_lang_data()
    if lang_data:
        return lang_data

    query = {"operationName":"listLanguages",
            "query":"query listLanguages {\n"
                    +"  listLanguages {\n"
                    +"    name\n"
                    +"    code_flix\n"
                    +"  }\n"
                    +"}"}

    data_json = read_api(query)
    if not data_json:
        return []
    lang_data = data_json['data']['listLanguages']
    save_lang_data(lang_data)
    # logger.info(json.dumps(data_json, indent=4), True)
    return lang_data


def get_language_list(languages, code_list):
    if not languages:
        return []
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


def get_language_string(languages, code):
    if not languages:
        return ""
    if code == 'en':
        return 'subtitulado'
    if PY3:
        return next(filter(lambda lang: lang['code_flix'] == code, languages))['name']
    else:
        return filter(lambda lang: lang['code_flix'] == code, languages)[0]['name']


def get_lang_data():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)


def save_lang_data(lang_data):
    logger.info()
    result, json_data = jsontools.update_node(lang_data, canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)
    return result
