# -*- coding: utf-8 -*-
# -*- Channel Comamos Ramen -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
import re

from bs4 import BeautifulSoup
from core import httptools, scrapertools, servertools, jsontools, tmdb
from core.item import Item
from platformcode import config, logger, unify
from channelselector import get_thumb

host = 'https://comamosramen.com'
apihost = 'https://fapi.comamosramen.com/api'
server_list = {'dood': 'doodstream', 'stream': 'streamtape', 'mixdrop(celular)': 'mixdrop', 'voe': 'voe', 'okru': 'okru', 'zplayer': 'zplayer'}
server_urls = {'doodstream': 'https://dood.to/e/', 'streamtape': 'https://streamtape.com/e/', 'mixdrop': 'https://mixdrop.to/e/',
               'voe': 'https://voe.sx/e/', 'okru': 'https://ok.ru/videoembed/', 'zplayer': 'https://v2.zplayer.live/embed/'}

# Funcionalidad de pelis desactivada por ahora, las películas parecen no funcionales/no parecen haber

def get_source(url, soup=False, json=False, **opt):
    logger.info()

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
            url = '{}/categorias/Peliculas/48'.format(apihost)
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
    # """
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
    # """
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
    item.channel = 'comamosramen'
    if categoria in ['peliculas']:
        item.list_type = 'pelicula'
        item.url = '{}/categorias/Peliculas/48'.format(apihost)
    else:
        item.list_type = 'novedades'
        item.url = '{}/ultimos/48'.format(apihost)
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
    letters = soup.find('nav', class_='navbar bg-main-color d-flex justify-content-end').find('div', class_='ml-40').find_all('a')
    for letter in letters:
        itemlist.append(
            Item(
                action = 'list_all',
                channel = item.channel,
                list_type = 'data',
                title = letter.text.upper(),
                url = '{}{}/48'.format(apihost, letter['href'])
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
        if 'latino' in array[1].lower():
            language = 'LAT'
        else:
            language = ''
    else:
        language = 'VOSE'
    title = array[0].strip()
    for exc, repl in exceptions.items():
        if scrapertools.find_single_match(title.lower(), exc):
            title = repl
    return title, language

def list_all(item):
    logger.info()
    itemlist = []
    matches = []
    if item.list_type in ['pais', 'pelicula', 'categorias', 'data', 'buscar', 'novedades']:
        # El JSON viene desde el API, la mayoría de info ya vendrá en el JSON
        json = get_source(item.url, json=True)

        for j in json:
            contentType = 'tvshow' if j.get('extras', {}).get('ultimoCap') else 'movie'
            title, language = set_lang(j['uniqid'].split('-', 1)[1])
            _id = j['uniqid'].split('-', 1)

            action = 'seasons'
            contentSerieName = title if contentType == 'tvshow' else None
            contentTitle = title
            status = j['estado']
            thumb = 'https://img.comamosramen.com/{}-medium.webp'.format(j['img'])
            url = '{}/v/{}'.format(host, '{}-{}'.format(_id[0], _id[1].replace('-', '%20')))
            viewType = 'episodes' if contentType == 'tvshow' else 'files'

            matches.append([action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url, viewType])

    else:
        # La sección cambió drásticamente, requiere reconstrucción
        logger.debug("\n" + str(soup.prettify()))
        raise Exception('Item malformado, list_type no válido')
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
    soup = get_source(item.url.replace('-', '/'), soup=True, ignore_response_code=True)
    json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)

    # Buscamos el "content_id", requerido para búsqueda en la API de la página
    # Actualización: Esto ya no funciona, la API cambió y no deja buscar por ID
    # content_id = json['props']['pageProps'].get('id')
    # Obtenemos el JSON con los episodios desde la API para clasificar temporadas (vienen en lotes)
    # NOTA: API para buscar episodios no da resultados, verificar después
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
            if 'Audio Latino' in seriesdata['metadata'].get('tags'):
                language = 'LAT'

        if seriesdata.get('type'):
            if seriesdata['type'].lower() in ['pelicula']:
                contentType = 'movie'
            else:
                contentType = 'tvshow'
        else:
            contentType = ''

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

    if not item.videolibrary:
        tmdb.set_infoLabels(itemlist, seekTmdb=True)

    # Si es peli, mandamos directo a findvideos
    if len(itemlist) == 1 and item.contentType == 'movie':
        return findvideos(itemlist[0])
    else:
        return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

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
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
            return itemlist
