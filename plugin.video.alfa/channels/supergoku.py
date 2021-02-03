# -*- coding: utf-8 -*-
import sys
import re
import datetime

from bs4 import BeautifulSoup
from core.tmdb import Tmdb
from core import httptools, scrapertools, servertools, tmdb, jsontools
from core.scrapertools import unescape
from core.item import Item, InfoLabels
from platformcode import config, logger, platformtools
from channelselector import get_thumb

host = 'https://supergoku.com'
IDIOMAS = {'VOSE': 'VOSE', 'LAT': 'Latino'}
list_language = list(IDIOMAS.keys())
month = {'Jan':'01', 'Feb':'02', 'Mar':'03',    #---Alternativa para obtener meses (hay bug con datetime.strptime en Kodi)---#
         'Apr':'04', 'May':'05', 'Jun':'06',
         'Jul':'07', 'Aug':'08', 'Sep':'09',
         'Oct':'10', 'Nov':'11', 'Dec':'12'}

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            action = "newest",
            channel = item.channel,
            fanart = item.fanart,
            title = "Nuevos capítulos",
            thumbnail = get_thumb("new episodes", auto=True),
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "recomended",
            title = "Animes recomendados",
            thumbnail = get_thumb("recomended", auto=True),
            url = host
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "popular",
            title = "Animes populares",
            thumbnail = get_thumb("favorites", auto=True),
            url = host
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "more_watched",
            title = "Animes mas vistos",
            thumbnail = get_thumb("more watched", auto=True),
            url = host + '/tvshows/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "Animes",
            thumbnail = get_thumb("anime", auto=True),
            url = host + '/categoria/anime/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "Películas",
            thumbnail = get_thumb("movies", auto=True),
            url = host + '/categoria/pelicula/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "OVAs",
            thumbnail = get_thumb("anime", auto=True),
            url = host + '/categoria/ova/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "ONAs",
            thumbnail = get_thumb("anime", auto=True),
            url = host + '/categoria/ona/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "Cortos",
            thumbnail = get_thumb("anime", auto=True),
            url = host + '/categoria/corto/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "Especiales",
            thumbnail = get_thumb("anime", auto=True),
            url = host + '/categoria/especial/'
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            fanart = item.fanart,
            param = "genres",
            title = "Géneros",
            thumbnail = get_thumb("genres", auto=True),
            url = host + '/tvshows/'
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            fanart = item.fanart,
            param = "airtime",
            title = "Filtrar por año/estado",
            thumbnail = get_thumb("year", auto=True),
            url = host + '/tvshows/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "allanimes",
            title = "Todos los animes",
            thumbnail = get_thumb("all", auto=True),
            url = host + '/tvshows/'
        )
    )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            fanart = item.fanart,
            title = "Buscar",
            thumbnail = get_thumb("search", auto=True),
            url = host + '/?s='
        )
    )
    return itemlist

def create_soup(url, post=None, headers=None):
    logger.info()

    data = httptools.downloadpage(url, post=post, headers=headers).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup

def newest(item):
    item.param = "newepisodes"
    item.url = host
    return list_all(item)

def filter_by_selection(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    soup = create_soup(item.url)
    if item.param == "genres":
        section = soup.find('ul', class_ = 'genres falsescroll')
    elif item.param == "airtime":
        section = soup.find('ul', class_ = 'releases falsescroll')
    for article in section.children:
        itemlist.append(
            Item(
                action = 'list_all',
                channel = item.channel,
                param = '',
                title = str(article.a.string),
                url = str(article.a['href'])
            )
        )
    return itemlist

def labeler(item):
    logger.info()
    oldtitle = ''
    if item.contentSerieName:
        oldtitle = item.contentSerieName
    else:
        oldtitle = item.contentTitle
    # Excepción(es) por algunas cosas que TMDB suele retornar erróneamente.
    # Estas en particular, las retorna mal en muchos de los canales que se busca cuando no hay año correcto
    year_exceptions = {'(?i)Yuru Camp': '2018', '(?i)One Piece': '1999', '(?i)Shingeki no Kyojin': '2013', '(?i)Higurashi no Naku Koro ni': '2020'}
    title_exceptions = {'(?i)Bem': 'Bem: Become Human'}

    title = item.infoLabels['title']
    for title_exc, title_replace in title_exceptions.items():
        if scrapertools.find_single_match(title, title_exc):
            if item.contentTitle:
                item.contentTitle = title_replace
            if item.contentSerieName:
                item.contentSerieName = title_replace
    for title_exc, year_replace in year_exceptions.items():
        if scrapertools.find_single_match(title, title_exc):
            item.infoLabels['year'] = year_replace

    tmdb.set_infoLabels(item, seekTmdb = True)
    if not item.infoLabels['tmdb_id']:
        oldcontentType = item.contentType
        year = item.infoLabels['year']
        #---Probamos como serie pero sin el año---#
        item.contentTitle = ''
        item.contentType = 'tv'
        item.contentSerieName = oldtitle
        item.infoLabels['year'] = ''
        tmdb.set_infoLabels(item, seekTmdb = True)

        if not item.infoLabels['tmdb_id']:
            #---Probamos si es película en vez de serie (con año)---#
            item.contentSerieName = ''
            item.contentTitle = oldtitle
            item.contentType = 'movie'
            item.infoLabels['year'] = year
            item.infoLabels['filtro'] = scrapertools.find_single_match(item.fanart, '(?is)/[^/]+\.(?:jpg|png)')
            tmdb.set_infoLabels(item, seekTmdb = True)

            if not item.infoLabels['tmdb_id']:
                special_rubbish = ['(?is)(:.+?)']
                #---Si aún no da, tratamos con casos especiales---#
                item.contentType = oldcontentType
                if oldcontentType == 'tv':
                    item.contentSerieName = oldtitle
                    item.contentTitle = ''
                else:
                    item.contentSerieName = ''
                    item.contentTitle = oldtitle

                if item.contentSerieName:
                    for rubbish in special_rubbish:
                        item.contentSerieName = re.sub(rubbish, '', oldtitle)
                        tmdb.set_infoLabels(item, seekTmdb = True)
                        if item.infoLabels['tmdb_id']:
                            break
                        else:
                            #---Con título especial, probamos si es película en vez de serie---#
                            item.contentSerieName = ''
                            item.contentTitle = oldtitle
                            item.contentType = 'movie'
                            tmdb.set_infoLabels(item, seekTmdb = True)
                            if not item.infoLabels['tmdb_id']:
                                #---Con título especial, probamos como serie pero sin el año---#
                                item.contentSerieName = oldtitle
                                item.contentTitle = ''
                                item.contentType = oldcontentType
                                item.infoLabels['year'] = ''
                                tmdb.set_infoLabels(item, seekTmdb = True)
                else:
                    for rubbish in special_rubbish:
                        item.contentSerieName = re.sub(rubbish, '', oldtitle)
                        return
                        tmdb.set_infoLabels(item, seekTmdb = True)
                        if item.infoLabels['tmdb_id']:
                            break
                        else:
                            #---Con título especial, probamos si es serie en vez de película---#
                            item.contentSerieName = oldtitle
                            item.contentTitle = ''
                            item.contentType = 'tv'
                            tmdb.set_infoLabels(item, seekTmdb = True)
                            if not item.infoLabels['tmdb_id']:
                                #---Con título especial, probamos como pelicula pero sin el año---#
                                item.contentSerieName = ''
                                item.contentTitle = oldtitle
                                item.contentType = oldcontentType
                                item.infoLabels['year'] = ''
                                tmdb.set_infoLabels(item, seekTmdb = True)
            if not item.infoLabels['tmdb_id']:
                item.contentType = oldcontentType
                if item.contentType == 'tv':
                    item.contentSerieName = oldtitle
                else:
                    item.contentTitle = oldtitle
    return item

def set_infoLabels_async(itemlist):
    import threading

    threads_num = config.get_setting("tmdb_threads", default=20)
    semaforo = threading.Semaphore(threads_num)
    lock = threading.Lock()
    r_list = list()
    i = 0
    l_hilo = list()

    def sub_thread(_item, _i):
        semaforo.acquire()
        ret = labeler(_item)
        semaforo.release()
        r_list.append((_i, _item, ret))

    for item in itemlist:
        t = threading.Thread(target = sub_thread, args = (item, i))
        t.start()
        i += 1
        l_hilo.append(t)

    # esperar q todos los hilos terminen
    for x in l_hilo:
        x.join()

    # Ordenar lista de resultados por orden de llamada para mantener el mismo orden q itemlist
    r_list.sort(key=lambda i: i[0])

    # Reconstruir y devolver la lista solo con los resultados de las llamadas individuales
    return [ii[2] for ii in r_list]

def process_title(old_title, getWithTags = False, get_contentTitle = False, get_lang = False):
    logger.info()
    stupid_little_things = {'(?is)[\–]+':'', '(?is)[\/]+':'', '(?is)([\(]).+?([\)])':'', '(?is)\s+\s':' ', '\(':'', '\)':''}
    trash =  {'(?is)ova[s]?':'[OVA]', '(?is)(?:\(|\))':'', '(?is)pelicula':'[Película]',
               '(?is)(audio latino|latino)':'LAT', '(?is)sub español':'VOSE',
               '(?is)fandub':'[Fandub]', '(?is)mini anime':'', '(?is)(especiales|especial)':'[Especiales]',
               '(?i)\d\w\w Season':''}
    # title_rubbish = ['(?is)(\s?(?:19|20)\d\d)', '(?is)\s[0-9].+?\s.*?(?:Season)?']

    for pattern, replacement in stupid_little_things.items():
        old_title = re.sub(pattern, replacement, old_title)

    old_title = old_title.strip()
    contentTitle = old_title
    title = old_title
    langs = []

    for pattern, key in trash.items():
        if scrapertools.find_single_match(contentTitle, pattern):
            if key in IDIOMAS:
                langs.append(key)
                title = re.sub(pattern, '[{}]'.format(IDIOMAS[key]), contentTitle)
            else:
                title = re.sub(pattern, '[{}]'.format(key), contentTitle)
            contentTitle = re.sub(pattern, '', contentTitle)
    
    contentTitle = contentTitle.strip()
    title = title.strip()

    if getWithTags and get_contentTitle and get_lang:
        return title, contentTitle, langs
    elif getWithTags and get_contentTitle:
        return title, contentTitle
    elif getWithTags and get_contentTitle:
        return title, langs
    elif getWithTags:
        return title
    else:
        return contentTitle

def get_next_page(data):
    pattern = '<span class=.current.+?a href=["|\'](.+?)["|\'] class="inactive"'
    match = scrapertools.find_single_match(data, pattern)
    if match != '':
        return match
    else:
        return False

def list_all(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    soup = create_soup(item.url)
    sectionptn = ''
    pattern = ''
    matches = []
    genericvalues = {'recomended':  True,  'more_watched': True,
                     'popular':     True,  'search':       True,
                     'newepisodes': False, 'allanimes':    False,
                     '': False}

    #==================Fase 1: Detección de patrones==================#
    # Obtenemos la sección especifica (evita conflictos con regex)    #
    # Verificamos qué parte de la función se llama                    #
    # para usar el patrón corecto (o generalizamos)                   #
    # Reciclamos patrones donde sea posible                           #

    # ===== Patrones de novedades (nuevos episodios) =====
    if item.param == 'newepisodes':
        section = soup.find('div', class_='animation-2 items')
        pattern += '(?s)img src="([^"]+).+?'            # thumb & season
        pattern += 'href="([^"]+).+?'                   # url
        pattern += '/span>(?:.*?(\d+?|))<.+?'           # epnum
        pattern += 'class="data".+?h3>(.*?)<.+?'        # title

    elif genericvalues[item.param] == True:
        pattern += '(?s)img src="(.+?)".+?'             # thumb
        pattern += 'data-src="([^"]+).+?'               # fanart

        if item.param == 'recomended' or item.param == 'more_watched':
            pattern += 'href="([^"]+).+?<.+?'           # url

            if item.param == 'recomended':              # == Patrones de recomendados ==
                pattern += 'class="title.+?>(.*?)<.+?'  # title (recomended)
                section = soup.find('div', id='slider-tvshows')

            elif item.param == 'more_watched':          # == Patrones de mas vistos ==
                pattern += 'a href.+?>([^<]+)'          # title (more_watched)
                section = soup.find('div', class_='items featured')

        elif item.param == 'popular':                   # == Patrones de populares ==
            section = soup.find('div', class_='items featured')
            pattern += 'h3><a href="([^"]+).+?'         # url (popular)
            pattern += '>(.+?)<.*?'                     # title (popular)

        elif item.param == 'search':                    # == Patrones de resultados de búsqueda ==
            section = soup.find('div', class_='search-page')
            pattern += 'href="([^"]+).+?'               # url (search)
            pattern += '>(.+?)<.+?'                     # title (search)
    elif item.param == 'allanimes':
        section = soup.find('div', id='archive-content')
    else:
        section = soup.find('div', class_='items')
    if pattern == '':                                                                    # == Patrón genérico para páginas comunes ==
        pattern += '(?s)img src="([^"]+).+?'                                             # thumb
        pattern += 'class="Categoria\w+[^"]+.+?(?:div class=(?:"|\')(\w+?[^"]+)|\w+).+?' # contentType
        pattern += '(?:div class=(?:"|\')estado\w+.+?div class=(?:"|\')([^"]+)).+?'      # status (opcional para películas)
        pattern += 'class="data".+?href="([^"]+)[^>]+?'                                  # url
        pattern += '>([^<]+).+?'                                                         # title
        pattern += '(?:span>([^<]+?)<.+?'                                                # airdate
        pattern += 'class="metadata".+?<span>(\d+?)</span>|</span>).+?'                  # year (útil con películas)
        pattern += 'class="text[^>]+?(?:>([^<]+?)<|><).+?'                               # plot
        pattern += '(?:class="mta.+?>(.*?)</div>|(?:</div>))'                            # genres (unscraped)
    section = str(section)

    matchrows = scrapertools.find_multiple_matches(section, '(?is)<article.+?</article>')
    for i in matchrows:
        matches.append(scrapertools.find_multiple_matches(i, pattern)[0])

    #==============Fase 2: Asignación de valores==============#
    # Como cada sección da distintos niveles de información,  #
    # se necesita un ciclo for diferente según el caso        #
    listitem = Item()

    # >>>> Ciclo para nuevos episodios (lleva directo a findvideos) <<<< #
    if item.param == "newepisodes":
        for scpthumb, scpurl, scpepnum, scptitle in matches:
            conType = ''
            infoLabels = {}
            title, contentTitle, langs = process_title(scptitle.strip(), getWithTags = True, get_contentTitle = True, get_lang = True)
            if scpepnum is not '':
                infoLabels['episode'] = int(scpepnum)
                conType = 'tvshow'
            else:
                conType = 'movie'
            # -----Casi nunca devuelve temporada, pero en raro caso que sí----- #
            scpseason = scrapertools.find_single_match(scpurl, 'season.(\d+)')
            if str(scpseason) is not None:
                infoLabels['season'] = scpseason
            else:
                infoLabels['season'] = None
            itemlist.append(
                Item(
                    action = "findvideos",
                    channel = item.channel,
                    contentSerieName = contentTitle,
                    contentTitle = contentTitle,
                    contentType = conType,
                    infoLabels = infoLabels,
                    language = langs,
                    title = title,
                    thumbnail = scpthumb,
                    url = scpurl
                )
            )

    # >>>> Ciclo para secciones similares (dan 4 variables en mismo orden) <<<< #
    elif genericvalues[item.param]:
        for scpthumb, scpfanart, scpurl, scptitle in matches:
            title, contentTitle, langs = process_title(scptitle.strip(), getWithTags = True, get_contentTitle = True, get_lang = True)
            itemlist.append(
                Item(
                    action = "seasons",
                    channel = item.channel,
                    contentSerieName = contentTitle,
                    contentTitle = contentTitle,
                    contentType = 'tvshow',
                    language = langs,
                    title = title,
                    thumbnail = scpthumb,
                    url = scpurl
                )
            )

    # >>>> Ciclo para secciones genéricas (casi cualquier página fuera de la principal) <<<< #
    else:
        for scpthumb, scpcontentType, scpstatus, scpurl, scptitle, scpairdate, scpyear, scpplot, scpgenres in matches:
            title, contentTitle, langs = process_title(scptitle.strip(), getWithTags = True, get_contentTitle = True, get_lang = True)
            conSerieName = ''
            conType = ''
            conTitle = ''
            infoLabels = {}
            infoLabels['plot'] = scpplot
            infoLabels['status'] = scpstatus.strip().title()
            infoLabels['year'] = scpyear

            date = scrapertools.find_multiple_matches(scpairdate, '(.+?). (\d|\d\d). (\d\d\d\d)')
            if date:
                date = date[0]
                infoLabels['last_air_date'] = date[2] + '-' + month[date[0]] + '-' + date[1]
                infoLabels['premiered'] = infoLabels['last_air_date']
            if scpgenres:
                genpatn = '(?s)a href="(?:[^"]+)+.+?>([^<]+)'
                genmatch = scrapertools.find_multiple_matches(scpgenres, genpatn)
                infoLabels['genre'] = unescape(genmatch[0]).strip()
                for i in range(len(genmatch) - 1):
                    infoLabels['genre'] += ', ' + unescape(genmatch[i + 1]).strip()
            if scpcontentType == 'pelicula':
                conType = 'movie'
                conTitle = contentTitle
            else:
                conType = 'tvshow'
                conSerieName = contentTitle

            itemlist.append(
                Item(
                    action = "seasons",
                    channel = item.channel,
                    contentSerieName = conSerieName,
                    contentTitle = conTitle,
                    contentType = conType,
                    infoLabels = infoLabels,
                    language = langs,
                    param = item.param,
                    title = title,
                    thumbnail = scpthumb,
                    url = scpurl
                )
            )

    #================================Fase 3: Corrección de valores============================#
    #----------Corregir si es una película en vez de serie o casos raros en el título---------#
    #---Corregir el título según tmdb y limpiar según el contenido (si es serie o película)---#

    set_infoLabels_async(itemlist)
    for i in itemlist:
        #---Quitamos números de episodio y espacios inútiles---#
        if i.contentType == 'movie':
            i.contentTitle = i.infoLabels['title']
            i.contentSerieName = ''
        else:
            i.contentSerieName = i.infoLabels['title']
            i.contentTitle = ''
        if i.infoLabels['episode']:
            pretext = ''
            if i.infoLabels['season'] is not '':
                pretext += 'S' + str(i.infoLabels['season'])
            pretext += 'E' + str(i.infoLabels['episode'])
            i.title = pretext + ': ' + i.title

    #======================Fase 4: Asignación de paginador (si aplica)======================#
    #---Si se encuentra otra página, se agrega un paginador (solo los items con páginas)---#

    if not genericvalues[item.param]:
        nextpage = get_next_page(data)
        if nextpage:
            itemlist.append(
                Item(
                    action = 'list_all',
                    channel = item.channel,
                    param = item.param,
                    title = '[COLOR=yellow]Siguiente página >[/COLOR]',
                    url = nextpage
                )
            )
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []

    if item.contentTitle:
        itemlist.extend(findvideos(item, add_to_videolibrary = True))
    else:
        seasons_list = seasons(item, add_to_videolibrary = True)
        for season in seasons_list:
            itemlist.extend(episodios(season, add_to_videolibrary = True))
    return itemlist

def seasons(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    section = soup.find('div', id='seasons')

    for article in section.children:
        if not article.find('li', class_="none"):
            infoLabels = item.infoLabels
            seasontitle = str(article.find('span', class_='title').contents[0])
            if not infoLabels['last_air_date'] and not infoLabels['premiered']:
                date = scrapertools.find_multiple_matches(str(article.find('span', class_='title').i.string), '(.+?)\. (\d\d).+?(\d+)')[0]
                infoLabels['last_air_date'] = date[2] + '-' + month[date[0]] + '-' + date[1]
                infoLabels['premiered'] = infoLabels['last_air_date']
            if not infoLabels['plot']:
                plot = str(soup.find('div', id='info').find('div', class_='wp-content').p.contents[0])
                if plot:
                    infoLabels['plot'] = plot
            contentType = item.contentType
            title = item.title

            # --- Si buscamos nº de temporada y es película, devolverá la cadena 'PELI' en vez de número --- #
            if 'PELI' in seasontitle:
                contentType = 'movie'
            else:
                if 'Especial' in item.title:
                    seasonnum = '0'
                else:
                    seasonnum = scrapertools.find_single_match(seasontitle, '(?is)\s(\d+)')
                if seasonnum:
                    contentType = 'tvshow'
                    infoLabels['season'] = int(seasonnum)
                    if int(seasonnum) == 0:
                        title = 'Especiales de ' + item.contentSerieName
                    else:
                        title = 'Temporada ' + str(seasonnum)
                else:
                    contentType = 'movie'
            itemlist.append(
                item.clone(
                    action = 'episodios',
                    contentType = contentType,
                    episode_data = str(article),
                    infoLabels = infoLabels,
                    title = title
                )
            )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    itemlist.reverse()      # Empieza por el último capítulo, así que se revierte la lista

    if len(itemlist) == 1 and not add_to_videolibrary:
        itemlist = episodios(itemlist[0], add_to_videolibrary)
    if len(itemlist) > 0 and config.get_videolibrary_support() and not itemlist[0].contentType == 'movie' and not add_to_videolibrary:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = "episodesxseason",
                title = '[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(70092)),
                url = item.url
            )
        )
    return itemlist

def episodios(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    if item.episode_data or item.param == 'pager':
        soup = BeautifulSoup(item.episode_data, "html5lib", from_encoding="utf-8")
    else:
        soup = create_soup(item.url)
        soup = soup.find('div', id='episodes')
        seasons = soup.find_all('div', class_='se-c')
        for season in seasons:
            seasonnum = scrapertools.find_single_match(str(season.find('span', class_='title').contents[0]), '(?is)\s(\d+)')
            if seasonnum:
                if item.infoLabels['season'] == int(seasonnum):
                    soup = season
    episodes = soup.find('ul', class_='episodios')

    remainingitems = None
    if len(episodes.contents) > 30 and not add_to_videolibrary:
        remainingitems = BeautifulSoup('<ul class="episodios"></ul>', "html5lib", from_encoding="utf-8")
        remainingcount = int(len(episodes.contents) - 30)
        i = 0
        while i < remainingcount:
            remainingitems.find('ul', class_='episodios').append(episodes.li.extract())
            i += 1

    for episode in episodes.children:
        contentType = item.contentType
        infoLabels = item.infoLabels
        infoLabels['title'] = ''
        epname = str(episode.find('div', class_='episodiotitle').a.string)
        epnum = scrapertools.find_single_match(epname, '(?is)(\d+)')
        title = str(episode.find(class_='episodiotitle').a.string)
        if not contentType == 'movie':
            if 'MOVIE' in epnum:
                contentType = 'movie'
            elif epnum:
                infoLabels['episode'] = int(epnum)
        itemlist.append(
            item.clone(
                action = 'findvideos',
                contentType = contentType,
                infoLabels = infoLabels,
                title = title,
                thumbnail = str(episode.find('img', class_='lazyload')['data-src']),
                url = str(episode.find(class_='episodiotitle').a['href'])
            )
        )

    itemlist.reverse()
    tmdb.set_infoLabels(itemlist, seekTmdb = True)

    for i in itemlist:
        if i.infoLabels['episode'] and i.infoLabels['title']:
            ss_and_ep = scrapertools.get_season_and_episode('{}x{}'.format(str(i.infoLabels['season']), str(i.infoLabels['episode'])))
            i.title = '{}: {}'.format(ss_and_ep, i.infoLabels['title'])
        elif i.infoLabels['episode']:
            ss_and_ep = scrapertools.get_season_and_episode('{}x{}'.format(str(i.infoLabels['season']), str(i.infoLabels['episode'])))
            i.title = '{}: {}'.format(ss_and_ep, i.title)

    if remainingitems:
        itemlist.append(
            item.clone(
                action = 'episodios',
                episode_data = str(remainingitems),
                param = 'pager',
                title = '[COLOR=yellow]Siguiente página >[/COLOR]'
            )
        )

    if len(itemlist) == 1 and (not add_to_videolibrary or item.contentType == 'movie'):
        return findvideos(itemlist[0], add_to_videolibrary)
    else:
        return itemlist

def findvideos(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    base_url = 'https://supergoku.com/wp-json/dooplayer/v1/post/'
    postnum = scrapertools.find_single_match(data, '(?is)data-post=.(\d+).*?')
    srcsection = scrapertools.find_single_match(data, '(?is)playeroptionsul.+?</ul>')
    srccount = scrapertools.find_multiple_matches(srcsection, '(?is)<li .+?data-nume=["|\'](.+?)["|\']')
    urls = ''
    for i in range(len(srccount)):
        composed_url = '{}{}?type=tv&source={}'.format(base_url, postnum, srccount[i])
        response = jsontools.load(httptools.downloadpage(composed_url).data)
        if not response['embed_url'].startswith('http'):
            response['embed_url'] = 'https:{}'.format(response['embed_url'])
        urls = '{}{}\n'.format(urls, response['embed_url'])
    temp_item = item
    itemlist.extend(servertools.find_video_items(item = temp_item, data = urls))
    itemlist = servertools.get_servers_itemlist(itemlist, None, True)
    for it in itemlist:
        it.title = '[{}] {}'.format(it.server.title(), it.contentTitle)

    if len(itemlist) > 0 and config.get_videolibrary_support() and not add_to_videolibrary \
    and item.contentTitle and item.contentType == 'movie':
        itemlist.append(
            Item(
                action = "add_pelicula_to_library",
                channel = item.channel,
                contentTitle = item.contentTitle,
                extra = "episodesxseason",
                title = '[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(70092)),
                url = item.url
            )
        )
    return itemlist

def search(item, text):
    logger.info()
    itemlist = []
    if text != '':
        try:
            text = scrapertools.slugify(text)
            text = text.replace('-', '+')
            item.url += text
            item.param = "search"
            return list_all(item)
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
            return itemlist