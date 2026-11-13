# -*- coding: utf-8 -*-

from __future__ import division
from core import urlparse as alfa_urlparse
from builtins import range
import sys
import re
import base64
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core import urlparse
from core.item import Item
from platformcode import logger, config, unify, platformtools

forced_proxy_opt = 'ProxySSL'

IDIOMAS = {'3':'LAT','1':'VOSE'}
UNIFY_PRESET = config.get_setting("preset_style", default="Inicial")
color_setting = unify.colors_file[UNIFY_PRESET]

list_language = list(set(IDIOMAS.values()))

canonical = {
             'channel': 'jkanime', 
             'host': config.get_setting("current_host", 'jkanime', default=''), 
             'host_alt': ["https://jkanime.net/"], 
             'host_black_list': [], 
             'pattern': '<meta\s*property="og:url"\s*content="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             # 'set_tls': True, 'set_tls_min': False, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
host_save = host


def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(Item(channel=item.channel, thumbnail=get_thumb("new episodes", auto=True),action="ultimos_episodios", title="Últimos Episodios", url=host))
    itemlist.append(Item(channel=item.channel, thumbnail=get_thumb("tvshows", auto=True), action="list_all", title="Directorio (Todos)", url=alfa_urlparse.build_url(host, 'directorio')))
    itemlist.append(Item(channel=item.channel, thumbnail=get_thumb("categories", auto=True), action="categories", title="Directorio (Filtrado)", url=alfa_urlparse.build_url(host, 'directorio'), viewType="–"))
    itemlist.append(Item(channel=item.channel, thumbnail=get_thumb("search", auto=True),action="search", title="Buscar"))
    return itemlist


def categories(item):
    logger.info()
    itemlist = []
    
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "filtro",
            plot = "Fecha, nombre o popularidad",
            thumbnail = get_thumb("popularidad", auto=True),
            title = "Ordenar Por"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "tipo",
            plot = "Anime, película, especiales, ovas, onas",
            thumbnail = get_thumb("on air", auto=True),
            title = "Por tipo"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "genero",
            plot = "Accion, aventura, comedia, etc.",
            thumbnail = get_thumb("genres", auto=True),
            title = "Por género"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "estado",
            plot = "En emisión, finalizados o por estrenar",
            thumbnail = get_thumb("on air", auto=True),
            title = "Por estado"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "letra",
            plot = "A-Z",
            thumbnail = get_thumb("alphabet", auto=True),
            title = "Por letra"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "fecha",
            plot = "Año de lanzamiento original",
            thumbnail = get_thumb("year", auto=True),
            title = "Por año"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "demografia",
            plot = "Niños, shoujo, shounen, seinen, josei",
            thumbnail = get_thumb("genre", auto=True),
            title = "Demografia"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "temporada",
            plot = "Invierno, primavera, verano, otoño",
            thumbnail = get_thumb("on air", auto=True),
            title = "Temporada"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "categoria",
            plot = "Donghua, latino",
            thumbnail = get_thumb("idioma", auto=True),
            title = "Categoria"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            param = "orden",
            plot = "Ascendente, descendente",
            thumbnail = get_thumb("on air", auto=True),
            title = "Ordenar en modo"
        )
    )
    itemlist.append(
        Item(
            action = "set_adv_filter",
            channel = item.channel,
            plot = "Refinar la búsqueda combinando género, estado, etc.",
            thumbnail = get_thumb("categories", auto=True),
            title = "Combinar criterios"
        )
    )
    return itemlist


def filter_by_selection(item, soup='', clearUrl=False):
    logger.info()
    itemlist = []
    
    if soup == '':
        soup = httptools.downloadpage(alfa_urlparse.build_url(host, 'directorio'), canonical=canonical, soup=True).soup
    
    select = soup.find('select', attrs={'name':item.param})
    if select:
        options = select.find_all('option')
    
        for option in options:
            value = option.get('value', option.text)
            url = "%s=%s" % (item.param, value)
            title = option.text
            if not clearUrl:
                url = alfa_urlparse.build_url(host, 'directorio', query=url)
            itemlist.append(
                Item(
                    action = "list_all",
                    channel = item.channel,
                    title = title,
                    url = url,
                )
            )
    
    return itemlist


def set_adv_filter(item):
    logger.info()
    
    soup = httptools.downloadpage(alfa_urlparse.build_url(host, 'directorio'), canonical=canonical, soup=True).soup
    
    filtros = {'filtro','genero','letra','demografia','categoria','tipo','estado','fecha','temporada','orden'}
    valores = []
    
    for filtro in filtros:
        items = filter_by_selection(Item(param=filtro), soup, clearUrl=True)
        lista_filtro = []
        for i in items:
            lista_filtro.append(i.title)
        result = platformtools.dialog_select('Elige %s' % filtro, lista_filtro, useDetails=False)
        if result != -1 and result != 0:
            valores.append(items[result].url)

    query = "&".join(valores)
    filtered_url = alfa_urlparse.build_url(host, 'directorio', query=query)
    
    filteritem = Item(
        channel =  item.channel,
        url = filtered_url
    )
    return list_all(filteritem)


def list_all(item):
    logger.info()
    itemlist = []
        
    try:
        data = httptools.downloadpage(item.url, canonical=canonical).data
    except Exception as e:
        logger.error("Could not read directory page. Error: %s" % e)
        return itemlist
    
    if not re.search(r'var animes = ', data):
        return itemlist
    
    animes_data = scrapertools.find_single_match(data, 'var animes = (.*?);\n')
    
    if not animes_data:
        return itemlist
    
    try:
        import json
        animes = json.loads("[%s]" % animes_data)[0]
    except Exception as e:
        logger.error("Error evaluating animes data string: %s" % e)
        return itemlist
    
    for anime in animes['data']:
        item_args = {}
    
        item_args['channel'] = item.channel
        item_args['url'] = anime['url']
        item_args['plot'] = anime['synopsis']
        item_args['thumbnail'] = anime['image']

        if anime['tipo'] == "Pelicula":
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = anime['title']
            item_args['title'] = anime['title']
            item_args['url'] += "%s/" % 1
            item_args['action'] = 'findvideos'
        else:
            item_args['contentType'] = 'tvshow'
            c_title, season = get_season_from_title(anime['title'])
            item_args['contentSerieName'] = c_title
            item_args['contentSeason'] = int(season)
            item_args['title'] = c_title
            if item_args['contentSeason'] > 1:
                item_args['title'] += ' [COLOR %s][B]%s[/B][/COLOR] ' % \
                                    (color_setting.get('movies', 'white'), 
                                    'Temporada %s' % item_args['contentSeason'])
            item_args['action'] = 'episodios'

        new_item = Item(**item_args)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)
    
    # Paginacion
    if animes.get('next_page_url'):

        itemlist.append(item.clone(
                                    action="list_all",
                                    title=">> {} {}".format(config.get_localized_string(30992), animes.get('current_page','1')),
                                    url=animes.get('next_page_url'),
                                    thumbnail=get_thumb("next.png")
                                    ))

    return itemlist


def search(item, texto):
    logger.info()
    if texto != "":
        texto = urlparse.quote_plus(texto)
        item.url = alfa_urlparse.build_url(host, u'buscar/{}'.format(texto))
        try:
            return search_results(item)
        # Se captura la excepción, para no interrumpir al buscador global si un canal falla
        except Exception as e:
            logger.error("Error en la funcion search: " % e)
    return []


def ultimos_episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    
    patron = '<a href="([^"]+)">.+?<img.+?src="([^"]+)".+?'
    patron += 'badge-primary">Ep (\d+)</span>.+?card-title">(.+?)</h5>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedepisode, scrapedtitle in matches:
        c_title, season = get_season_from_title(scrapedtitle)
        title = "{}x{} {}".format(season, scrapedepisode, c_title)
        info = {}
        info['season'] = int(season)
        info['episode'] = int(scrapedepisode)
        itemlist.append(
            Item(channel=item.channel, InfoLabels=info, contentType='episode',
                 action="findvideos", title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                 show=c_title))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def search_results(item):
    logger.info()
    # Descarga la pagina
    data = httptools.downloadpage(item.url, canonical=canonical).data

    # Extrae las entradas
    patron = 'data-setbg="([^"]+)".+?'     # thumb
    patron += 'class="anime">(.+?)</.+?'   # type
    patron += 'h5><a\s+href="([^"]+)"'     # url
    patron += '>(.+?)</a'                  # title
    matches = scrapertools.find_multiple_matches(data, patron)
    itemlist = []
    for scrapedthumbnail, scrapedtype, scrapedurl, scrapedtitle in matches:
        infoLabels = {}
        item_args = {}
    
        item_args['channel'] = item.channel
        item_args['url'] = scrapedurl
        item_args['thumbnail'] = scrapedthumbnail

        if scrapedtype == "Pelicula":
            item_args['contentType'] = 'movie'
            item_args['contentTitle'] = scrapedtitle
            item_args['title'] = scrapedtitle
            item_args['action'] = 'findvideos'
        else:
            item_args['contentType'] = 'tvshow'
            c_title, season = get_season_from_title(scrapedtitle)
            item_args['contentSerieName'] = c_title
            item_args['contentSeason'] = int(season)
            item_args['title'] = c_title
            infoLabels['season'] = int(season)
            if item_args['contentSeason'] > 1:
                item_args['title'] += ' [COLOR %s][B]%s[/B][/COLOR] ' % \
                                    (color_setting.get('movies', 'white'), 
                                    'Temporada %s' % item_args['contentSeason'])
            item_args['action'] = 'episodios'

        item_args['infoLabels'] = infoLabels

        new_item = Item(**item_args)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, force_no_year=True, seekTmdb=True)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    # Descarga la pagina
    data = httptools.downloadpage(item.url, canonical=canonical).data
    scrapedid = scrapertools.find_single_match(data, 'data-anime="([^"]+)')
    token = scrapertools.find_single_match(data, 'name="csrf-token" content="([^"]+)')

    kwargs = {}
    kwargs['headers'] = {
                         'Origin': host.rstrip('/'),
                         'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                         'accept':'application/json, text/javascript, */*; q=0.01'
                        }
    kwargs['post'] = "_token=%s" % token
    kwargs['canonical'] = canonical
    
    epidodes_api_url = alfa_urlparse.build_url('https://jkanime.net', u'/ajax/episodes/{}/{}'.format(scrapedid, 1))
    
    data_json = httptools.downloadpage(epidodes_api_url, **kwargs).json

    episodes = data_json['data']
    
    last = int(data_json['last_page'])
    
    if 1 != last:
        for pag in range(2, last+1):
            epidodes_api_url = alfa_urlparse.build_url('https://jkanime.net', u'/ajax/episodes/{}/{}'.format(scrapedid, pag))
            nextpage = httptools.downloadpage(epidodes_api_url, **kwargs).json
            episodes += nextpage['data']
    
    for episode in episodes:
        infoLabels = item.infoLabels
        infoLabels["season"] = item.contentSeason
        infoLabels["episode"] = int(episode['number'])
        title = "%sx%s - %s" % (infoLabels["season"], infoLabels["episode"], episode['title'])
        url = alfa_urlparse.build_url(item.url, str(episode['number']), trailing_slash=True)
        itemlist.append(item.clone(action="findvideos", infoLabels=infoLabels, title=title, url=url))
        
    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="findvideos", title="Serie por estrenar", url="", folder=False))
    else:
        tmdb.set_infoLabels(itemlist, True)
    
    return itemlist


def findvideos(item):
    logger.info()
    
    itemlist = []
    
    try:
        data = httptools.downloadpage(item.url, canonical=canonical).data
    except Exception as e:
        logger.error("Could not read videos page. Error: %s" % e)
        return itemlist
    
    if not re.search(r'var servers = ', data):
        return itemlist
    
    videos = scrapertools.find_single_match(data, 'var servers = (.*?);\n')
    
    if not videos:
        return itemlist
    
    try:
        import ast
        videos = ast.literal_eval(videos)
    except Exception as e:
        logger.error("Error evaluating video data string: %s" % e)
        return itemlist
    
    for video in videos:
        try:
            url = base64.b64decode(video['remote']).decode("utf-8")
        except Exception as e:
            logger.error("Error decoding video string: %s" % e)
            continue
          
        if url:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', quality='HD',
                                language=get_language_string(video['lang']), infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools

    itemlist = [i for i in itemlist if i.title != "Directo"]
    
    return itemlist


def get_language_string(code):
    return IDIOMAS.get(str(code), 'VOSE')


def get_season_from_title(title):
    """
    Extracts the season number from the title.
    :param title: The title of the anime.
    :return: The title and the season number or 1 if not found.
    """
    
    patern1 = r'(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season'
    patern2 = r'(?i)(?:season|temporada|part|parte)\s*(\d+)'
    
    season = scrapertools.find_single_match(title, patern1)
    if not season:
        season = scrapertools.find_single_match(title, patern2)
        if season:
            title = re.sub(patern2, '', title)
    else:
        title = re.sub(patern1, '', title)
    
    return title.strip(), int(season) if season else 1