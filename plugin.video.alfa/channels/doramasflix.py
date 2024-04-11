# -*- coding: utf-8 -*-
# -*- Channel Doramasflix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    from alfaresolver_py3 import rayo
else:
    from alfaresolver import rayo

from core import jsontools, httptools, servertools, tmdb
from platformcode import logger, config, platformtools
from channelselector import get_thumb
from core.item import Item
from modules import autoplay
from channels import filtertools
from core.jsontools import json

TAG_CUSTOM_FILTERS_CONTROLS = "custom_filters_controls"
TAG_CUSTOM_FILTERS_SETTINGS = "custom_filters_settings"
TAG_CUSTOM_FILTERS_DCONFIGS = "custom_filters_dconfigs"
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

    url = "https://doraflix.fluxcedene.net/api/gql"

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

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    # Muestra lo mismo que entrar en la primera página de Doramas.
    # itemlist.append(Item(channel=item.channel, title="Últimos Doramas",
                         # action="list_all",
                         # thumbnail=get_thumb('last', auto=True),
                         # url=host, c_type='ultimos_doramas'))

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

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(70038)),
                         action="set_filters",
                         url=host,
                         thumbnail=get_thumb("setting_0.png")))
                         
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()
    # logger.info(item, True)
    page = 1
    if item.page:
        page = item.page

    # if item.c_type == 'ultimos_doramas':
        # query = {
                # "operationName":"listLastDoramas",
                # "variables":{"limit":items_per_page,"filter":{"isTVShow":False}},
                # "query":"query listLastDoramas($limit: Int, $filter: FilterFindManyDoramaInput) {\n"
                        # +"  listDoramas(limit: $limit, sort: _ID_DESC, filter: $filter) {\n"
                        # +"    _id\n"
                        # +"    name\n"
                        # +"    name_es\n"
                        # +"    slug\n"
                        # +"    languages\n"
                        # +"    isTVShow\n"
                        # +"    poster_path\n"
                        # +"    poster\n"
                        # +"    __typename\n"
                        # +"  }\n"
                        # +"}"
                # }

    if item.c_type in ['doramas', 'TvShows']:
        addfilter = {}
        addfilter["isTVShow"] = False if item.c_type == 'doramas' else True
        addfilter.update(get_filters())
        # logger.info(addfilter, True)
        query = {
                "operationName":"paginationDorama",
                "variables":{"page":page,"sort":"CREATEDAT_DESC","perPage":items_per_page,"filter":addfilter},
                "query":"query paginationDorama($page: Int, $perPage: Int, $sort: SortFindManyDoramaInput, $filter: FilterFindManyDoramaInput) {\n"
                        +"  paginationDorama(page: $page, perPage: $perPage, sort: $sort, filter: $filter) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      currentPage\n"
                        +"      hasNextPage\n"
                        +"      hasPreviousPage\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      languages\n"
                        +"      slug\n"
                        +"      rating\n"
                        +"      age_limit\n"
                        +"      backdrop_path\n"
                        +"      isTVShow\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
                }

    if item.c_type == 'peliculas':
        addfilter = get_filters()
        # logger.info(addfilter, True)
        query = {
                "operationName":"paginationMovie",
                "variables":{"page":page,"sort":"CREATEDAT_DESC","perPage":items_per_page,"filter":addfilter},
                "query":"query paginationMovie($page: Int, $perPage: Int, $sort: SortFindManyMovieInput, $filter: FilterFindManyMovieInput) {\n"
                        +"  paginationMovie(page: $page, perPage: $perPage, sort: $sort, filter: $filter) {\n"
                        +"    count\n"
                        +"    pageInfo {\n"
                        +"      currentPage\n"
                        +"      hasNextPage\n"
                        +"      hasPreviousPage\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    items {\n"
                        +"      _id\n"
                        +"      name\n"
                        +"      name_es\n"
                        +"      languages\n"
                        +"      slug\n"
                        +"      names\n"
                        +"      popularity\n"
                        +"      rating\n"
                        +"      backdrop_path\n"
                        +"      release_date\n"
                        +"      backdrop\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
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

    # if item.c_type == 'ultimos_doramas':
        # content_list = data_json['data']['listDoramas']

    if item.c_type == 'ultimos_episodios':
        content_list = data_json['data']['premiereEpisodes']

    if item.c_type == 'search':
        content_list = data_json['data']['searchDorama']
        content_list.extend(data_json['data']['searchMovie'])

    if item.c_type == 'peliculas':
        content_list = data_json['data']['paginationMovie']['items']
        page_info = data_json['data']['paginationMovie']['pageInfo']

    if item.c_type in ['doramas', 'TvShows']:
        content_list = data_json['data']['paginationDorama']['items']
        page_info = data_json['data']['paginationDorama']['pageInfo']

    # logger.info(json.dumps(content_list, indent=4), True)

    if not content_list:
        return itemlist

    if item.c_type != 'ultimos_episodios':
        languages = get_all_languages()

    for dorama in content_list:
        infoLabels = {}
        item_args = {}

        item_args['channel'] = item.channel
        item_args['url'] = dorama['_id']
        item_args['context'] = autoplay.context
        if dorama.get('languages',''):
            item_args['language'] = get_language_list(languages, dorama['languages'])

        if dorama['__typename'] == "Movie":
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = dorama['name']
            item_args['title'] = dorama['name']
            item_args['action'] = 'findvideos'
            img_path = dorama['poster_path'] if dorama.get('poster_path', '') else dorama['backdrop_path']
        elif dorama['__typename'] == "Episode":
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
            item_args['slug'] = dorama['slug']
            item_args['title'] = dorama['name']
            item_args['action'] = 'seasons'
            img_path = dorama['poster_path'] if dorama.get('poster_path', '') else dorama['backdrop_path']

        infoLabels['filtro'] = img_path
        item_args['infoLabels'] = infoLabels
        item_args['thumbnail'] = tmdb_thumb_path.format(img_path)
        
        # logger.info(item_args, True)

        new_item = Item(**item_args)

        new_item.context = filtertools.context(new_item, list_language, list_quality)

        changes = tmdb.set_infoLabels(new_item, force_no_year=True)
        # logger.info("{} changes en {}.".format(changes, new_item.title), True)
        if changes <= 0:
            set_detail(new_item)
        # if changes > 0:
            # logger.info(new_item.infoLabels, True)

        itemlist.append(new_item)

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


def set_detail(item):
    logger.info()
    if item.contentType not in ['movie', 'tvshow']:
        return

    if item.contentType == 'movie':
        query = {"operationName":"detailMovieById",
                 "variables":{"_id":item.url},
                 "query":"query detailMovieById($_id: MongoID!) {\n"
                        +"  detailMovieById(_id: $_id) {\n"
                        +"    _id\n"
                        +"    name\n"
                        +"    name_es\n"
                        +"    slug\n"
                        +"    cast\n"
                        +"    names\n"
                        +"    country\n"
                        +"    overview\n"
                        +"    languages\n"
                        +"    popularity\n"
                        +"    poster_path\n"
                        +"    vote_average\n"
                        +"    backdrop_path\n"
                        +"    release_date\n"
                        +"    rating\n"
                        +"    runtime\n"
                        +"    poster\n"
                        +"    backdrop\n"
                        +"    genres {\n"
                        +"      name\n"
                        +"      slug\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    labels {\n"
                        +"      name\n"
                        +"      slug\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"}

    if item.contentType == 'tvshow':
        query = {"operationName":"detailDoramaById",
                 "variables":{"_id":item.url},
                 "query":"query detailDoramaById($_id: MongoID!) {\n"
                        +"  detailDoramaById(_id: $_id) {\n"
                        +"    _id\n"
                        +"    name\n"
                        +"    slug\n"
                        +"    cast\n"
                        +"    names\n"
                        +"    name_es\n"
                        +"    rating\n"
                        +"    country\n"
                        +"    overview\n"
                        +"    episode_time\n"
                        +"    languages\n"
                        +"    poster_path\n"
                        +"    number_of_seasons\n"
                        +"    number_of_episodes\n"
                        +"    backdrop_path\n"
                        +"    first_air_date\n"
                        +"    episode_run_time\n"
                        +"    isTVShow\n"
                        +"    premiere\n"
                        +"    poster\n"
                        +"    uploaders\n"
                        +"    subbers\n"
                        +"    trailer\n"
                        +"    videos\n"
                        +"    backdrop\n"
                        +"    genres {\n"
                        +"      name\n"
                        +"      slug\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    labels {\n"
                        +"      name\n"
                        +"      slug\n"
                        +"      __typename\n"
                        +"    }\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"}
    
    data_json = read_api(query)

    if not data_json:
        return

    operation_name = query['operationName']
    content = data_json['data'][operation_name]
    # logger.info(json.dumps(content, indent=4), True)
    item.infoLabels['plot'] = content['overview']
    item.infoLabels['rating'] = content['rating']
    date = content['release_date'] if item.contentType == 'movie' else content['first_air_date']
    # logger.info("premiered {}".format(date), True)
    if date:
        y, m, d = date.split('-')
        item.infoLabels['premiered'] = "{}/{}/{}".format(d,m,y)
        item.infoLabels['year'] = y

    genre_names = []
    for genre in content['genres']:
        if isinstance(genre['name'], str):
            genre_names.append(genre['name'])
    if genre_names:
        item.infoLabels['genre'] = ', '.join(genre_names)
    item.thumbnail = tmdb_thumb_path.format(content['poster_path'])


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
    # logger.info(item, True)

    season = 1 if not item.contentSeason else item.contentSeason

    query = {"operationName":"detailSeasonExtra",
             "variables":{"slug":item.slug,"season_number":season},
             "query":"query detailSeasonExtra($slug: String!, $season_number: Float!) {\n"
                    +"  listSeasons(sort: NUMBER_ASC, filter: {serie_slug: $slug}) {\n"
                    +"    slug\n"
                    +"    season_number\n"
                    +"    poster_path\n"
                    +"    serie_backdrop_path\n"
                    +"    air_date\n"
                    +"    serie_name\n"
                    +"    trailer\n"
                    +"    poster\n"
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
                    +"    filter: {type_serie: \"dorama\", serie_slug: $slug, season_number: $season_number}\n"
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
                    +"    poster\n"
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
        for season in data_json['data']['listSeasons']:
            new_item = item.clone(
                    contentSeason=season['season_number'], 
                    title=(config.get_localized_string(60027) % season['season_number']) if season['season_number'] > 0 else config.get_localized_string(70483),
                    contentPlot=season['overview'], 
                    thumbnail=tmdb_thumb_path.format(season['poster_path']), 
                    contentType='season'
                )

            itemlist.append(new_item)
        
        return itemlist

    infoLabels = item.infoLabels
    for episode in data_json['data']['listEpisodes']:
        infoLabels['season'] = episode['season_number']
        infoLabels['episode'] = episode['episode_number']
        title = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], item.contentSerieName)
        url = episode['_id']
        thumbnail = tmdb_thumb_path.format(episode['still_path'])
        infoLabels['filtro'] = episode['still_path']
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', 
                             infoLabels=infoLabels, contentType='episode'))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title=config.get_localized_string(70146), url=item.url,
                 slug=item.slug, action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

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
            return list_all_query(item, query)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
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
                    +"    serie_poster\n"
                    +"    season_number\n"
                    +"    episode_number\n"
                    +"    still_image\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"
            }
    item.c_type='ultimos_episodios'
    return list_all_query(item, query)


def findvideos(item):
    logger.info()

    itemlist = []

    if item.contentType == 'movie':
        content_list = []
        query = {        
                "operationName":"listProblemsItem",
                "variables":{"problem_type":"movie","problem_id":item.url},
                "query":"query listProblemsItem($problem_type: EnumProblemProblem_type, $problem_id: MongoID!) {\n"
                        +"  listProblems(\n"
                        +"    filter: {problem_type: $problem_type, problem_id: $problem_id, WithServer: true}\n"
                        +"    sort: _ID_DESC\n"
                        +"  ) {\n"
                        +"    server\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
                }
        data_json = read_api(query)
        if not data_json:
            return itemlist
        valid_servers = get_valid_servers()
        if not valid_servers:
            return itemlist

        for server in data_json['data']['listProblems']:
            if server['server']['server'] in valid_servers:
                if not server['server'] in content_list:
                    if not in_dictlist(content_list, 'link', server['server']['link']):
                        content_list.append(server['server'])
    else:
        query = {
                "operationName":"detailEpisodeLinks",
                "variables":{"episode_id":item.url},
                "query":"query detailEpisodeLinks($episode_id: MongoID!) {\n"
                        +"  detailEpisode(filter: {_id: $episode_id}) {\n"
                        +"    links_online\n"
                        +"    __typename\n"
                        +"  }\n"
                        +"}"
                }

        data_json = read_api(query)
        if not data_json:
            return itemlist
        # logger.info(json.dumps(data_json, indent=4), True)
        content_list = data_json['data']['detailEpisode']['links_online']

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


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # logger.info(categoria, True)
    if categoria == 'series':
        itemlist = new_episodes(item)
    return itemlist


def get_valid_servers():
    logger.info()

    dc = get_detail_config()
    if not dc:
        return False

    server_ids, language_ids = dc

    valid_servers = []
    query = {
            "operationName":"listServers",
            "variables":{"_ids":server_ids},
            "query":"query listServers($_ids: [MongoID!]!) {\n"
                    +"  listServeresByIds(_ids: $_ids) {\n"
                    +"    _id\n"
                    +"    name\n"
                    +"    app\n"
                    +"    code_flix\n"
                    +"    __typename\n"
                    +"  }\n"
                    +"}"
            }

    data_json = read_api(query)

    if not data_json:
        return valid_servers

    # logger.info(json.dumps(data_json, indent=4), True)

    for server in data_json['data']['listServeresByIds']:
        if server['app']:
            valid_servers.append(server['code_flix'])

    return valid_servers


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

    dc = get_detail_config()
    if not dc:
        return False

    server_ids, language_ids = dc

    query = {"operationName":"listLanguages",
            "variables":{"_ids":language_ids},
            "query":"query listLanguages($_ids: [MongoID!]!) {\n"
                    +"  listLanguageesByIds(_ids: $_ids) {\n"
                    #+"    _id\n"
                    +"    name\n"
                    #+"    flag\n"
                    #+"    slug\n"
                    #+"    code\n"
                    +"    code_flix\n"
                    #+"    __typename\n"
                    +"  }\n"
                    +"}"}

    data_json = read_api(query)
    # logger.info(data_json, True)
    if not data_json:
        return []
    lang_data = data_json['data']['listLanguageesByIds']
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


def set_filters(item):
    if logger.info() == False:
        # Estamos en test, no mostramos nada
        return
    list_controls = get_controls_list()
    if not list_controls:
        return
    saved_filters = get_filters_from_file()
    if saved_filters:
        for control in list_controls:
            _id = control['id']
            control['default'] = saved_filters[_id]
    # logger.info(list_controls, True)

    custom_button = {"label":config.get_localized_string(70003),
                     "function":'default_opt',
                     "visible":True,
                     "close":True}

    platformtools.show_channel_settings(list_controls=list_controls, callback='save_filters_to_file', item=item,
                                        caption=config.get_localized_string(70038), custom_button=custom_button)


def default_opt(item, values):
    logger.info()
    # logger.info(values, True)
    reset_all_data()
    set_filters(item)


def get_detail_config():
    logger.info()

    dconfig = get_config_from_file()
    if dconfig:
        return dconfig['server_ids'], dconfig['language_ids']

    query = {"operationName":"detailConfig",
             "variables":{},
             "query":"query detailConfig {\n"
            +"  detailConfig(filter: {platform: \"doramasgo\"}) {\n"
            +"    name\n"
            +"    isMantein\n"
            +"    servers {\n"
            +"      name\n"
            +"      ref\n"
            +"      __typename\n"
            +"    }\n"
            +"    languages {\n"
            +"      name\n"
            +"      ref\n"
            +"      __typename\n"
            +"    }\n"
            +"    countries {\n"
            +"      name\n"
            +"      ref\n"
            +"      __typename\n"
            +"    }\n"
            +"    __typename\n"
            +"  }\n"
            +"}"}
    data_json = read_api(query)
    if not data_json:
        return False

    server_ids = list(i['ref'] for i in data_json['data']['detailConfig']['servers'])
    language_ids = list(i['ref'] for i in data_json['data']['detailConfig']['languages'])

    save_config_to_file({'server_ids':server_ids, 'language_ids':language_ids})

    return server_ids, language_ids


def get_filters_dict():
    logger.info()

    dc = get_detail_config()
    if not dc:
        return False

    server_ids, language_ids = dc

    return  {  'Paises': {'query': {"operationName":"listCountriesByPlatforms",
                                  "variables":{"platform":"doramasgo"},
                                  "query":"query listCountriesByPlatforms($platform: String!) {\n"
                                            +"  listCountriesByPlatforms(platform: $platform) {\n"
                                            +"    _id\n"
                                            +"    name\n"
                                            +"    slug\n"
                                            +"    flag\n"
                                            +"    code\n"
                                            +"    code_flix\n"
                                            +"    __typename\n"
                                            +"  }\n"
                                            +"}"},
                         'filter_key':'country',
                         'filter_val':'slug'},
               'Productoras':{'query':{"operationName":"listNetworks",
                                       "variables":{},
                                       "query":"query listNetworks {\n"
                                            +"  listNetworks(filter: {platform: \"doramasgo\"}, sort: NUMBER_DESC, limit: 30) {\n"
                                            +"    _id\n"
                                            +"    name\n"
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
                                            +"}"},
                              'filter_key':'networkId',
                              'filter_val':'_id'},
               'Géneros':{'query':{"operationName":"listGenres",
                                   "variables":{},
                                   "query":"query listGenres {\n"
                                            +"  listGenres(filter: {platform: \"doramasgo\"}, sort: NUMBER_DESC) {\n"
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
                                            +"}"},
                          'filter_key':'genreId',
                          'filter_val':'_id'},
               'Etiquetas':{'query':{"operationName":"listLabels",
                                     "variables":{},
                                     "query":"query listLabels {\n"
                                            +"  listLabels(filter: {platform: \"doramasgo\"}, sort: NUMBER_DESC) {\n"
                                            +"    _id\n"
                                            +"    name\n"
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
                                            +"}"},
                          'filter_key':'labelId',
                          'filter_val':'_id'},
               'Idioma':  {'query':{"operationName":"listLanguages",
                                    "variables":{"_ids":language_ids},
                                    "query":"query listLanguages($_ids: [MongoID!]!) {\n"
                                            +"  listLanguageesByIds(_ids: $_ids) {\n"
                                            +"    _id\n"
                                            +"    name\n"
                                            +"    flag\n"
                                            +"    slug\n"
                                            +"    code\n"
                                            +"    code_flix\n"
                                            +"    __typename\n"
                                            +"  }\n"
                                            +"}"},
                          'filter_key':'bylanguage',
                          'filter_val':'code_flix'}
              }


def get_controls_list():
    logger.info()
    # logger.info("Se ejecuta get_controls_list", True)

    controls = get_controls_from_file()
    if controls:
        return controls

    # logger.info("Se lee desde API", True)
    filters = get_filters_dict()
    if not filters:
        return False

    list_controls = list()

    for name in filters.keys():
        data_json = read_api(filters[name]['query'])
        if not data_json:
            continue
        operationName = filters[name]['query']['operationName']
        operation = operationName if operationName != "listLanguages" else "listLanguageesByIds"
        # logger.info(name, True)
        # logger.info(operation, True)
        data = data_json['data'][operation]
        # logger.info(data, True)
        filter_key = filters[name]['filter_key']
        filter_val = filters[name]['filter_val']
        lfilter = list(['SF'])
        lvalues = list(['Sin Filtro'])
        for values in data:
            lfilter.append(values[filter_val])
            lvalues.append(values['name'])
        # logger.info("{}={}".format(filter_key, filter_val), True)
        # logger.info(json.dumps(data_json, indent=4), True)

        list_controls.append( { "id": filter_key,
                                "type": "list",
                                "label": name,
                                "default": 0,
                                "enabled": True,
                                "visible": True,
                                "lfilter": lfilter,
                                "lvalues": lvalues } )

    if list_controls:
        save_controls_to_file(list_controls)

    return list_controls


def get_controls_from_file():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CUSTOM_FILTERS_CONTROLS)


def save_controls_to_file(list_controls):
    logger.info()
    result, json_data = jsontools.update_node(list_controls, canonical['channel'], TAG_CUSTOM_FILTERS_CONTROLS)
    return result


def get_filters_from_file():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CUSTOM_FILTERS_SETTINGS)


def save_filters_to_file(item, dict_data_saved):
    logger.info()
    result, json_data = jsontools.update_node(dict_data_saved, canonical['channel'], TAG_CUSTOM_FILTERS_SETTINGS)
    return result


def get_config_from_file():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CUSTOM_FILTERS_DCONFIGS)


def save_config_to_file(detail_config):
    logger.info()
    result, json_data = jsontools.update_node(detail_config, canonical['channel'], TAG_CUSTOM_FILTERS_DCONFIGS)
    return result


def get_filters():
    logger.info()
    filters = {}
    saved_filters = get_filters_from_file()
    if saved_filters:
        list_controls = get_controls_list()
        if list_controls:
            for control in list_controls:
                _id = control['id']
                index = saved_filters[_id]
                if index != 0:
                    filters[_id] = control['lfilter'][index]
    return filters


def get_lang_data():
    logger.info()
    return jsontools.get_node_from_file(canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)


def save_lang_data(lang_data):
    logger.info()
    result, json_data = jsontools.update_node(lang_data, canonical['channel'], TAG_CHANNEL_LANGUAGE_DATA)
    return result


def reset_all_data():
    logger.info()
    for node in [TAG_CUSTOM_FILTERS_CONTROLS,
                 TAG_CUSTOM_FILTERS_SETTINGS,
                 TAG_CUSTOM_FILTERS_DCONFIGS,
                 TAG_CHANNEL_LANGUAGE_DATA]:
        jsontools.update_node({}, canonical['channel'], node)
