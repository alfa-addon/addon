# -*- coding: utf-8 -*-
# -*- Channel HenaoJara -*-
# -*- Created for Alfa Addon -*-
# -*- By DieFeM -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAllChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

"""  Esto no es necesario: utiliza AlfaChannel.urlparse o parse_qs para evitar imports innecesarios, ya que Python se puede volver loco por falta de recursos.  No estaban las funciones en AH pero las he añadido.
if PY3:
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
else:
    import urllib
    from urlparse import urlparse
    from urlparse import parse_qs
"""

IDIOMAS = AlfaChannelHelper.IDIOMAS_ANIME
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES
list_quality_tvshow = AlfaChannelHelper.LIST_QUALITY_TVSHOW
list_quality = list_quality_movies + list_quality_tvshow
list_servers = ['uqload', 'voe', 'streamtape', 'doodstream', 'okru', 'streamlare', 'wolfstream', 'mega']
forced_proxy_opt = 'ProxySSL'

""" No es necesario para este canal, en principio 'cf_assistant_if_proxy': True, 'cf_assistant_get_source': False, 'CF_stat': True, 'session_verify': False, """
canonical = {
             'channel': 'henaojara', 
             'host': config.get_setting("current_host", 'henaojara', default=''), 
             'host_alt': ['https://www.henaojara.com/'], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 15
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = '/ver/category/pelicula'
tv_path = '/ver/category/categorias'
language = []
url_replace = []

finds = {'find': dict([('find', [{'tag': ['ul'], 'class': ['MovieList']}]), 
                       ('find_all', [{'tag': ['li']}])]), 
                 """ 'tag' y 'class' son listas y puedes introducir más valores, siempre que luego no coicidan en la misma página.  Por ejemplo, aquí podrías poner:
                    'class': ['MovieList NoLmtxt Rows AX A06 B04 C03 E20', 'MovieList Rows BX B06 C04 E03 NoLmtxt Episodes']
                 y no te haría falta poner el código el "list_all".  Pero todavía se puede simplificar más.  En BS4 'class' internamente es tratoado como una lista donde el espacio es un separador, luego en este caso aparece como ['MovieList', 'NoLmtxt', 'Rows', etc...].  Esto quiere decir que siempre que el argunto que pongas en calss sea significativo y no ambiguo, puedes usar solo una entrada y no todo el "chorizo":
                    'class': ['MovieList'], que te valdría para los dos casos.
                Si 'MovieList' es ambiguo y tienes que cafificarlo mejor, entonces sí que tienes que pone todo el string.  Ojo que si usas ['MovieList', 'NoLmtxt'] es una función OR mientras que ['MovieList NoLmtxt Rows AX A06 B04 C03 E20'] es AND de todos sus componentes.  Por supuesto también podrías usar 'class': re.compile('MovieList NoLmtxt) o similar para comparar por parte del string.
                 """: '', 
         """ Ver línea 135-153 """: '', 
         'categories': dict([('find', [{'tag': ['div'], 'id': ['categories-3']}]),
                             ('find_all', [{'tag': ['li']}])]),
         'search': {}, 
         'get_language': {}, 
         'get_language_rgx': '', 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         """ Esta web require un '/' al final para el paginado. Hay webs que se ponen muy tontas por esto. """: '', 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']],
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['wp-pagenavi']}]),
                            ('find_all', [{'tag': ['a'], 'class': ['page-numbers'], '@POS': [-2]}]),
                            ('get_text', [{'tag': '', '@STRIP': True, '@TEXT': '(\d+)'}])]),
         'year': {}, 
         'season_episode': {}, 
         'seasons': {'find_all': [{'tag': ['div'], 'class': ['AABox']}]},
         'season_num': dict([('find', [{'tag': ['div'], 'class': ['AA-Season']}, 
                                       {'tag': ['span']}]), 
                             ('get_text', [{'tag': '', '@STRIP': True}])]),
         'seasons_search_num_rgx': '', 
         'seasons_search_qty_rgx': '', 
         'season_url': host, 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['div'], 'class': ['AABox']}]},
         'episode_num': [], 
         'episode_clean': [], 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['TPlayerTb']}]},
            """ Tratar de poner aquí todos los regex de limpieza para que AH lo haga luego automáticamente """: '', 
         'title_clean': [['(?i)HD|Español Castellano|Sub Español|Español Latino|ova\s+\d+\:|OVA\s+\d+|\:|\((.*?)\)|\s19\d{2}|\s20\d{2}', ''],
                         ['(?i)\s*Temporada\s*\d+', '']],
         'quality_clean': [],
         'language_clean': [], 
         'url_replace': [], 
            """ aunque en 'cnt_tot' puedes poner el valor que gustes, es recomendable ajustarse al tamaño habitual de la página en la web. por simple claridad en el debugging.
            'join_dup_episodes': False evita el intento de AH de reagrupar el mismo episodio con doferentes calidades.  Aquí no hace falta
            'season_TMDB_limit': False: Nuevo parámetro para que AH no rechaze temporadas que no estén en TMDB.  USAR CON PRECUACIÓN """: '', 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 'add_video_to_videolibrary': True, 'cnt_tot': 20, 
                      'get_lang': False, 'reverse': False, 'videolab_status': True, 'tmdb_extended_info': True, 'seasons_search': False, 
                      'IDIOMAS_TMDB': {0: 'es', 1: 'ja', 2: 'es'}, 'join_dup_episodes': False, 'season_TMDB_limit': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path=movie_path, tv_path=tv_path, canonical=canonical, finds=finds, 
                                   idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                   list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                   channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=host, action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))

    """ Esto es una sugenrecia de usabilidad.  Sé que está en Categorías, pero un acceso directo puede venir bien """
    itemlist.append(Item(channel=item.channel, title='Estrenos', url=host + 'ver/category/estrenos/', action='list_all',
                         thumbnail=get_thumb('premieres', auto=True), extra='estrenos'))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'ver/category/categorias/', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'ver/category/pelicula/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    """ Esto selleva en 'sectio' """
    itemlist.append(Item(channel=item.channel, title='Categorías',  action='section', url=host, 
                         thumbnail=get_thumb('categories', auto=True), extra='categorías'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist

""" Esta va en la función 'section' y prácticamente AH lo hace todo automático si se rellena finds[¡categories']
def categories_menu(item):
    logger.info()

    new_soup = AlfaChannel.create_soup(item.url, **kwargs)
    
    new_soup = new_soup.find(id="categories-3")
    resultset = new_soup.find_all("li") if new_soup else []

    itemlist = list()
    
    for elem in resultset:
        title = elem.a.text
        url = elem.a["href"]
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='list_all',
                             thumbnail=get_thumb('all', auto=True)))

    return itemlist
"""


def section(item):
    logger.info()

    return AlfaChannel.section(item, **kwargs)

""" Pongo al final el formato estándar que Veranime no tenía'
def newest(categoria):
    
    itemlist = []
    
    if categoria == 'anime':
        itemlist = list_all(Item(url=host,c_type='episodios'))
    return itemlist
"""


def list_all(item):
    logger.info()

    findS = finds.copy()
    """ Ver líneas 56-61
    if item.c_type == 'episodios':
        findS['find'] = dict([('find', [{'tag': ['ul'], 'class': ['MovieList Rows BX B06 C04 E03 NoLmtxt Episodes']}]), 
                              ('find_all', [{'tag': ['li']}])])
    """

    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=findS, **kwargs)


def list_all_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    """ Es insteresante dejar esta línea aunque no se use, ya que es solo un puntero y puede ser necesario en el futuro """
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            """ usa .get_text(strip=True) en vez de .text.  También puedes usar get_text(''|', strip=True).split('|') y recibes varios textos """
            if item.c_type == 'episodios':
                sxe = elem.find("span", class_="ClB").get_text(strip=True)
                try:
                    season, episode = sxe.split('x')
                    elem_json['season'] = int(season)
                    elem_json['episode'] = int(episode)
                except Exception:
                    elem_json['season'] = 1
                    elem_json['episode'] = 1
                elem_json['mediatype'] = 'episode'

            """ por estilo porpcura utilizar en lo posible directamente las etiquetas del diccionario elem_json: ahorramos memoria y cada etiqueta significa lo mismo en todos los canales. Eso nos permite también copiar trozos de un canal a otro sin preocuparnos de los nombre """
            elem_json['title'] = elem.find("h3", class_="Title").get_text(strip=True)
            elem_json['language'], elem_json['title'] = clear_title(elem_json['title'] )

            seasonPattern = '\s+Temporada\s+(\d+)'
            if re.search(seasonPattern, elem_json['title']):
                season = int(scrapertools.find_single_match(elem_json['title'], seasonPattern))
                if season > 1:
                    elem_json['season'] = season
                    elem_json['mediatype'] = 'season'
            """  Te sugiero que marques con 'temporada' solo los que sean season > 1, por claridad al usuario.  No hace falta que limpies 'title', ya lo hará AH, siempre que hayas puesto el regex en 'finds['title_clean']'
            Con el truco de las dos líea anteriores, hace la función del elem_json['plot_extend'].  Luego Generictools cambia automáticamente a elem_json['mediatype'] = 'tvshow' después de pintarlo
                c_title = re.sub(seasonPattern, '', c_title).strip()
                elem_json['plot_extend'] = '[COLOR blue][Temporada ' + season + '][/COLOR]'
            elem_json['title'] = c_title
            """

            elem_json['url'] = elem.find("article", class_="TPost C").a.get('href', '')

            try:
                Qlty = elem.find("span", class_="Qlty").get_text(strip=True)
            except Exception:
                Qlty = ''

            if not elem_json.get('mediatype'):
                elem_json['mediatype'] = 'tvshow' if not "pelicula" in elem_json['title'] and Qlty not in ["PELICULA", "ESTRENO"] else 'movie'

            if item.c_type == 'series' and elem_json['mediatype'] == 'movie':
                continue
            if item.c_type == 'peliculas' and elem_json['mediatype'] == 'tvshow':
                continue

            """ Intentaremos tratar la películas de un solo "episodio" de forma transparente para el usuario, pasando a Findvideos si solo hay 1"""
            if elem_json['mediatype'] == 'movie':
                elem_json['action'] = 'seasons'

            # logger.info(item.c_type + ', ' + elem_json['mediatype'], True)
            """ No hace falsta: AH lo hace automáticamente 
            thumbnail = elem.find("noscript").find("img").get("src", "")
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
            """
            elem_json['thumbnail'] = elem.find("noscript").find("img").get("src", "")

            try:
                elem_json['year'] = elem.find("span", class_="Date AAIco-date_range").get_text(strip=True)
            except Exception:
                elem_json['year'] = '-'

            elem_json['quality'] = 'HD'
            """ elem_json['language'] = lang"""
            if elem.find("div", class_=["Description"]): 
                elem_json['plot'] = elem.find("div", class_=["Description"]).p.get_text(strip=True)

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        if not elem_json['url']: continue

        matches.append(elem_json.copy())

    return matches


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


def episodesxseason(item, **AHkwargs):
    logger.info()

    """ Aquí le decimos a qué función tienen que saltar para las películas de un solo vídeo """
    kwargs['matches_post_get_video_options'] = findvideos
    soup = AHkwargs.get('soup', '')

    return AlfaChannel.episodes(item, data=soup, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem_season in matches_int:
        if elem_season.find("div", class_="AA-Season").span.get_text(strip=True) != str(item.contentSeason): continue

        try:
            epi_list = elem_season.find("div", class_="TPTblCn")
        except Exception:
            return matches

        for elem in epi_list.find_all("tr"):
            elem_json = {}
            logger.error(elem)

            try:
                info = elem.find("td", class_="MvTbTtl")
                elem_json['title'] = info.a.get_text(strip=True)
                lang, elem_json['title'] = clear_title(elem_json['title'])
                """ Esto lo he implementado con etiquetas obtenidas de TMDB y una modificación en Unify. Algunas veces falla TMDB, pero debería de valer
                nextChapterDateRegex = r'\s*-\s*(Proximo\s*Capitulo\s*\d+-[A-Za-z]+-\d+)'
                if re.search(nextChapterDateRegex, elem_json['title']):
                    nextChapterDate = scrapertools.find_single_match(elem_json['title'], nextChapterDateRegex)
                    elem_json['title'] = re.sub(nextChapterDateRegex, '', elem_json['title'])
                    elem_json['plot_extend'] = '[COLOR red][' + nextChapterDate + '][/COLOR]'
                 """

                elem_json['episode'] = int(elem.find("span", class_="Num").get_text(strip=True) or 1)
                elem_json['url'] = info.a.get("href", "")
                elem_json['season'] = item.contentSeason

                try:
                    elem_json['thumbnail'] = elem.find(["noscript", "span"]).find("img").get("src", "")
                except Exception:
                    pass

            except Exception:
                logger.error(elem)
                logger.error(traceback.format_exc())
                continue

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())

    return matches


def findvideos(item, **AHkwargs):
    logger.info()
    
    """ No es necesario con la moficiación hecha en AH
    # logger.info(item, True)
    if item.contentType == 'movie':
        return AlfaChannel.seasons(item, **kwargs)
    """

    kwargs['matches_post_episodes'] = episodesxseason_matches

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)

    for elem in matches_int:
        elem_json = {}
        # logger.error(elem)

        try:
            content = elem.get_text(strip=True)
            if content != '':
                elem = AlfaChannel.do_soup(scrapertools.htmlparser(content)).iframe
            else:
                elem = elem.iframe

            url = elem.get('src', '')
            if url == "" or not url.startswith('http'):
                continue

            iframeData = AlfaChannel.create_soup(url, hide_infobox=True, **kwargs)
            if not iframeData:
                continue

            iframe = iframeData.find("iframe")
            if not iframe:
                continue

            iframeUrl = iframe.get('src', '')

            if iframeUrl != "":
                iframeUrl = check_hjstream(iframeUrl)
                uriData = AlfaChannel.urlparse(iframeUrl)

                if re.search(r'embedwish|hqq|netuplayer|krakenfiles|hj.henaojara.com', uriData.hostname, re.IGNORECASE):
                    continue

                elem_json['url'] = iframeUrl
                elem_json['title'] = '%s'
                elem_json['language'] = item.language
                elem_json['quality'] = 'HD'

            if not elem_json.get('url'): continue
            matches.append(elem_json.copy())

        except Exception:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

    return matches, langs

def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        # https://docs.python.org/2/library/urllib.html#urllib.quote_plus (escapa los caracteres de la busqueda para usarlos en la URL)
        texto = AlfaChannel.do_quote(texto, '', plus=True) 
        item.url = item.url + "?s=" + texto

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel

    try:
        if categoria in ['anime']:
            item.url = host
            item.c_type = 'episodios'
            item.extra = "novedades"
            item.action = "list_all"
            itemlist = list_all(item)

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc())
        return []

    return itemlist


# henaojara usa varios scripts para embeber algunos enlaces en diferentes subdominios de hjstream.xyz,
# esta funcion se encarga de extraer el enlace del servidor original a partir de los parámetros de la url,
# en el parámetro v (v=xxxx), a veces en texto plano, a veces en base64.
def check_hjstream(url):
    logger.info()

    if "hjstream.xyz" in url:
        queryData = AlfaChannel.parse_qs(AlfaChannel.urlparse(url).query)
        if "v" in queryData:
            v = queryData["v"][0]

            if v.startswith('https'):
                url = scrapertools.htmlparser(v)
            else:
                decurl = base64.b64decode(v).decode("utf-8")
                if decurl.startswith('https'):
                    url = scrapertools.htmlparser(decurl)

    return url

def clear_title(title):

    if 'latino' in title.lower():
        lang = 'Latino'
    elif 'castellano' in title.lower():
        lang = 'Castellano'
    elif 'audio español' in title.lower():
        lang = ['Latino', 'Castellano']
    else:
        lang = 'VOSE'

    title = re.sub(r'^[P|p]el[i|í]cula |HD|Español Castellano|Sub Español|Español Latino|ova\s+\d+:|OVA\s+\d+|\:|\((.*?)\)| \s19\d{2}| \s20\d{2}', '', title)
    title = re.sub(r'\s:', ':', title)
    title = " ".join( title.split() )

    return lang, title