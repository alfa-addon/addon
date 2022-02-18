# -*- coding: utf-8 -*-
# -*- Channel Comamos Ramen -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
import re

from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config
from platformcode import logger
from platformcode import unify

server_list = {'dood': 'doodstream', 'stream': 'streamtape', 'mixdrop(celular)': 'mixdrop', 'voe': 'voe', 'okru': 'okru', 'zplayer': 'zplayer'}
server_urls = {'doodstream': 'https://dood.to/e/', 'streamtape': 'https://streamtape.com/e/', 'mixdrop': 'https://mixdrop.to/e/',
               'voe': 'https://voe.sx/e/', 'okru': 'https://ok.ru/videoembed/', 'zplayer': 'https://v2.zplayer.live/embed/'}

canonical = {
             'channel': 'comamosramen', 
             'host': config.get_setting("current_host", 'comamosramen', default=''), 
             'host_alt': ["https://comamosramen.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
domain = scrapertools.find_single_match(host, patron_domain)
apihost = 'https://fapi.%s/api' % domain


def get_source(url, soup=False, json=False, **opt):
    logger.info()

    opt['canonical'] = canonical
    data = httptools.downloadpage(url, **opt)

    if json:
        data = data.json
    else:
        data = data.data
        data = BeautifulSoup(data, "html5lib", from_encoding="utf-8") if soup else data

    return data


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            action = "newest",
            channel = item.channel,
            fanart = item.fanart,
            title = "Novedades",
            thumbnail = 'https://i.postimg.cc/fbq5wxxq/ahmya.png',
            viewType = 'videos'
        )
    )
    """
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pelicula',
            title = "Películas",
            thumbnail = 'https://i.postimg.cc/Xqdgcmtt/ramon9.png',
            url = '{}/pages/Peliculas'.format(host)
        )
    )
    """
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'categorias',
            title = "Equipo Ramen",
            thumbnail = 'https://i.postimg.cc/8k6wSfsw-/ramon12.png',
            url = '{}/categorias/Equipo%20Ramen/48'.format(apihost),
            viewType = 'videos'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'categorias',
            title = "Boy's Love",
            thumbnail = 'https://i.postimg.cc/X76L7NCW/ramon10.png',
            url = '{}/categorias/BL/48'.format(apihost),
            viewType = 'videos'
        )
    )
    itemlist.append(
        Item(
            action = "country",
            channel = item.channel,
            fanart = item.fanart,
            title = "Por país",
            thumbnail = 'https://i.postimg.cc/gkyDw9VZ/ramon4.png',
            viewType = 'videos'
        )
    )
    itemlist.append(
        Item(
            action = "alpha",
            channel = item.channel,
            fanart = item.fanart,
            title = "Por letra",
            thumbnail = 'https://i.postimg.cc/j5GXft3z/ramon2.png',
            url = host,
            viewType = 'videos'
        )
    )
    """
    itemlist.append(
        Item(
            action = "categories",
            channel = item.channel,
            fanart = item.fanart,
            title = "Categorías",
            thumbnail = 'https://i.postimg.cc/Xqdgcmtt/ramon9.png',
            url = '{}/categorias/'.format(host),
            viewType = 'videos'
        )
    )
    """
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            fanart = item.fanart,
            title = "Buscar",
            thumbnail = 'https://i.postimg.cc/kgnyKjsh/ramon13.png',
            viewType = 'videos'
        )
    )
    return itemlist


def newest(categoria):
    logger.info()
    item = Item()
    item.channel = canonical['channel']

    if categoria in ['peliculas']:
        item.list_type = 'pelicula'
        item.url = '{}p/peliculas'.format(host)

    else:
        item.list_type = 'novedades'
        item.url = '{}p/dramas'.format(host)

    return list_all(item)


def country(item):
    logger.info()
    itemlist = []

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "China (CDrama)",
            thumbnail = 'https://i.postimg.cc/tgf67D7f/3-01.png',
            url = '{}/categorias/Cdrama/48'.format(apihost)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Corea del Sur (KDrama)",
            thumbnail = 'https://i.postimg.cc/43ntJj4V/02-01.png',
            url = '{}/categorias/Kdrama/48'.format(apihost)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Japón (Dorama)",
            thumbnail = 'https://i.postimg.cc/9M779T7f/4-01.png',
            url = '{}/categorias/Dorama/48'.format(apihost)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Tailandia (Lakorn)",
            thumbnail = 'https://i.postimg.cc/FzbkW4G5/8-01.png',
            url = '{}/categorias/Lakorn/48'.format(apihost)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Filipinas",
            thumbnail = 'https://i.postimg.cc/nrfQGz4G/6-01.png',
            url = '{}/categorias/Filipinas/48'.format(apihost)
        )
    )

    return itemlist


def alpha(item):
    logger.info()

    itemlist = []
    soup = get_source(item.url, soup=True)
    letters = soup.select('nav.navbar.d-flex')[0].find_all('a')

    for letter in letters:
        itemlist.append(
            Item(
                action = 'list_all',
                channel = item.channel,
                list_type = 'data',
                title = letter.text.upper(),
                url = '{}{}/100'.format(apihost, letter['href'])
            )
        )

    return itemlist


def set_lang(title):
    """
        Función para asignación y corrección de títulos e idioma
    """
    # Funcionamiento de las excepciones:
    # En la clave va un patrón a buscar, en el valor va el título con el que se reemplazará
    exceptions = {'^vivo': '#Vivo'}
    
    # Buscamos si hay un "|", que divida en idioma
    array = title.encode().decode().split('|')

    if len(array) > 1:
        language = 'LAT' if 'latino' in array[1].lower() else ''

    else:
        language = 'VOSE'

    title = array[0].strip()

    for exc, repl in exceptions.items():
        title = repl if scrapertools.find_single_match(title.lower(), exc) else title

    return title, language


def list_all(item):
    logger.info()
    itemlist = []
    matches = []

    if apihost in item.url:
        # El JSON viene desde el API, la mayoría de info ya vendrá en el JSON
        json = get_source(item.url, json=True)

        for j in json:
            contentType = 'tvshow' if j.get('extras', {}).get('ultimoCap') else 'movie'
            title, language = set_lang(j['uniqid'].split('-', 1)[1])
            _id = j['uniqid'].split('-', 1)

            action = 'seasons' if contentType == 'tvshow' else 'findvideos'
            contentSerieName = title if contentType == 'tvshow' else None
            contentTitle = title
            status = j['estado']
            thumb = 'https://img.{}/{}-medium.webp'.format(domain, j['img'])
            url = '{}v/{}/{}'.format(host, _id[0], _id[1].replace('-', ' '))
            viewType = 'episodes' if contentType == 'tvshow' else 'files'

            matches.append([action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url, viewType])

    elif host in item.url:
        # El JSON vendrá en la página, incrustado como __NEXT_DATA__
        soup = get_source(item.url, soup=True)
        json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)
        json = json['props']['pageProps']['data']['sections'][0]['data']

        for j in json:
            contentType = 'tvshow' if j.get('lastEpisodeEdited') else 'movie'
            title, language = set_lang(j['title'])

            action = 'seasons' if contentType == 'tvshow' else 'findvideos'
            contentSerieName = title if contentType == 'tvshow' else None
            contentTitle = title
            thumb = 'https://img.{}/{}-medium.webp'.format(domain, j['img']['vertical'])
            url = '{}v/{}/{}/'.format(host, j['_id'], j['title'])
            url = '{}{}'.format(url, j['lastEpisodeEdited']) if contentType == 'tvshow' else url
            viewType = 'episodes' if contentType == 'tvshow' else 'files'

            status = []

            if j['status']['isOnAir']:
                status.append('En emisión')
            if j['status']['isOnAir']:
                status.append('Subtitulando')

            status = ", ".join(status)

            matches.append([action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url, viewType])

    else:
        # La sección cambió drásticamente, requiere reconstrucción
        soup = get_source(item.url, soup=True)
        logger.debug("\n" + str(soup.prettify()))
        return

    # Recorremos la lista construída de matches
    for action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url, viewType in matches:
        it = Item(
            action = action,
            contentType = contentType,
            channel = item.channel,
            language = language,
            title = unify.add_languages(title, language),
            thumbnail = thumb,
            url = url,
            viewType = viewType
        )

        # Determinación dinámica de contentType
        if contentType == 'tvshow':
            it.contentSerieName = contentSerieName

        elif contentTitle:
            it.contentTitle = contentTitle

        itemlist.append(it)

    return itemlist


def seasons(item):
    logger.info()
    itemlist = []
    seasons = []
    soup = get_source(item.url, soup=True, ignore_response_code=True)
    json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)

    # NOTE: API para buscar episodios no da resultados, verificar después
    # NOTE[2]: La API esta sigue sin funcionar. Probablemente la descartaré completamente
    # Buscamos el "content_id", requerido para búsqueda en la API de la página      # Esto ya no funciona, la API cambió y no deja buscar por ID
    # content_id = json['props']['pageProps'].get('id')
    # Obtenemos el JSON con los episodios desde la API para clasificar temporadas (vienen en lotes)
    # episodios = get_source('https://fapi.comamosramen.com/api/byUniqId/{}'.format(content_id), json=True)

    seriesdata = json['props']['pageProps']['data']
    seasons = seriesdata['seasons']

    # Recorremos la lista de temporadas para procesamiento
    for season in seasons:
        title, language = set_lang(seriesdata['title'])
        infoLabels = {'year': seriesdata['metadata'].get('year')}
        ogtitle = title

        if item.language:
            language = item.language

        elif seriesdata['metadata'].get('tags'):
            language = 'LAT' if 'Audio Latino' in seriesdata['metadata'].get('tags') else language

        contentType = 'movie' if seriesdata.get('type') and seriesdata['type'].lower() in ['pelicula'] else 'tvshow'

        it = Item(
            action = 'episodesxseason',
            channel = item.channel,
            contentType = contentType,
            contentSeason = season['season'],
            infoLabels = infoLabels,
            json_episodios = season['episodes'],
            language = language,
            plot = seriesdata['description'],
            thumbnail = item.thumbnail,
            title = (config.get_localized_string(60027) % str(season['season'])),
            url = item.url,
            viewType = 'episodes'
        )

        # Asignamos valores al item según su contentType
        if contentType == 'movie':
            it.contentTitle = ogtitle

        else:
            it.contentSeason = season['season']
            it.contentSerieName = ogtitle

        itemlist.append(it)

    # Asignamos las infoLabels (si aplica)
    if not item.videolibrary:
        tmdb.set_infoLabels(itemlist, True, force_no_year = True)

    # Si solo hay una temporada, retornamos directamente los episodios
    if len(itemlist) == 1:
        itemlist = episodesxseason(itemlist[0])
    
    if not len(itemlist) > 0:
        return []

    # Agregamos elemento "Agregar a videoteca"
    if len(itemlist) > 0 and config.get_videolibrary_support() and not itemlist[0].contentType == 'movie' and not item.videolibrary:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentType = 'tvshow',
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                title = '[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(60352)),
                url = item.url
            )
        )

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    item.videolibrary = True

    # Si es peli, retornamos enlaces
    if not item.contentType == 'movie':
        seasons_list = seasons(item)
        if len(seasons_list) > 0:
            if isinstance(seasons_list[0], list):
                for season in seasons_list:
                    itemlist.extend(episodesxseason(season))

            else:
                return seasons_list

    # Si es serie, retornamos los episodios
    else:
        itemlist.extend(findvideos(item))

    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    episodes = item.json_episodios

    for episode in episodes:
        infoLabels = item.infoLabels
        language = item.language if item.language else 'VOSE'

        it = Item(
            action = 'findvideos',
            channel = item.channel,
            contentType = item.contentType,
            infoLabels = infoLabels,
            language = language,
            thumbnail = item.thumbnail,
            title = item.title,
            urls = episode['players'],
            url = item.url,
            viewType = 'videos'
        )

        # Determinación dinámica de contentType
        if not item.contentType == 'movie':
            it.title = (config.get_localized_string(60036) % episode['episode'])
            it.contentEpisodeNumber = episode['episode']

        itemlist.append(it)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    # Si es peli, mandamos directo a findvideos
    if len(itemlist) == 1 and item.contentType == 'movie':
        return findvideos(itemlist[0])

    else:
        return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not item.urls:
        soup = get_source(item.url, soup=True)
        json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)
        seriesdata = json['props']['pageProps']['data']
        seasons = seriesdata['seasons']
        item.urls = seasons[0]['episodes'][0]['players']

    # Recorremos la lista de servidores
    for option in item.urls:
        server = server_list.get(option['name'].lower())
        # Si no hay server (server nuevo o inválido), continuamos
        if not server:
            continue
        url = '{}{}'.format(server_urls.get(server, ''), option['id'])
        serv_name = servertools.get_server_name(server)

        new_item = Item(
            action = 'play',
            channel = item.channel,
            infoLabels = item.infoLabels,
            language = item.language,
            server = server,
            thumbnail = item.thumbnail,
            title = '{}: {} {}'.format(config.get_localized_string(60335), serv_name.title(), unify.add_languages('', item.language)),
            url = url
        )

        # Chequeos (asignar fanart, plot y formatear títulos)
        if item.fanart and not new_item.fanart:
            new_item.fanart = item.fanart
        if item.contentPlot and not new_item.contentPlot:
            new_item.contentPlot = item.contentPlot
        if not item.contentType == 'movie':
            unify.title_format(new_item)
        itemlist.append(new_item)

    # Si es peli y podemos, agregamos el elemento "Agregar a videoteca"
    if len(itemlist) > 0 and config.get_videolibrary_support() and item.contentType == 'movie' and not item.videolibrary:
        itemlist.append(
            Item(
                action = "add_pelicula_to_library",
                channel = item.channel,
                contentType = "movie",
                contentTitle = item.contentTitle,
                extra = "findvideos",
                infoLabels = {'year': item.infoLabels.get('year')},
                title = "[COLOR yellow]{}[/COLOR]".format(config.get_localized_string(60353)),
                url = item.url,
                videolibrary = True
            )
        )
    return itemlist


def search(item, text):
    logger.info()
    itemlist = []

    if text:
        try:
            text = scrapertools.slugify(text)
            text = text.replace('-', '%20')
            item.url = '{}/buscar/{}/40'.format(apihost,text)
            item.list_type = 'buscar'
            return list_all(item)

        except Exception:
            import traceback
            logger.error(traceback.format_exc())
            return itemlist

