# -*- coding: utf-8 -*-
# -*- Channel Comamos Ramen -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group (SistemaRayoXP)-*-

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

def create_soup(url, post=None, headers=None):
    logger.info()
    data = httptools.downloadpage(url, post=post, headers=headers).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            action = "newest",
            channel = item.channel,
            fanart = item.fanart,
            title = "Novedades",
            thumbnail = get_thumb("newest", auto=True)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pelicula',
            title = "Películas",
            thumbnail = get_thumb("movies", auto=True),
            url = '{}/peliculas'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'categorias',
            title = "Equipo Ramen",
            thumbnail = get_thumb("doramas", auto=True),
            url = '{}/categorias/Equipo%20Ramen'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'categorias',
            title = "BL",
            thumbnail = get_thumb("doramas", auto=True),
            url = '{}/categorias/BL'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "country",
            channel = item.channel,
            fanart = item.fanart,
            title = "Por país",
            thumbnail = get_thumb("country", auto=True)
        )
    )
    itemlist.append(
        Item(
            action = "alpha",
            channel = item.channel,
            fanart = item.fanart,
            title = "Por letra",
            thumbnail = get_thumb("alphabet", auto=True),
            url = host
        )
    )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            fanart = item.fanart,
            title = "Buscar",
            thumbnail = get_thumb("search", auto=True)
        )
    )
    # itemlist.append(
        # Item(
            # action = "list_all",
            # channel = item.channel,
            # fanart = item.fanart,
            # list_type = 'doramasmp4',
            # title = "De DoramasMP4",
            # thumbnail = get_thumb("doramas", auto=True),
            # url = '{}/origen/doramasmp4'.format(host)
        # )
    # )
    # itemlist.append(
        # Item(
            # action = "list_all",
            # channel = item.channel,
            # fanart = item.fanart,
            # list_type = 'anime',
            # title = "Animes",
            # thumbnail = get_thumb("anime", auto=True),
            # url = '{}/animes'.format(host)
        # )
    # )
    return itemlist

def newest(categoria):
    logger.info()
    item = Item()
    item.channel = 'comamosramen'
    if categoria in ['peliculas']:
        item.list_type = 'pelicula'
        item.url = '{}/peliculas'.format(apihost)
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
            title = "China (CDramas)",
            thumbnail = '{}/iconos/3-01.svg'.format(host),
            url = '{}/pais/China'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Corea del Sur (KDrama)",
            thumbnail = '{}/iconos/02-01.svg'.format(host),
            url = '{}/pais/Corea%20del%20Sur'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Japón (Dorama)",
            thumbnail = '{}/iconos/4-01.svg'.format(host),
            url = '{}/pais/Jap%C3%B3n'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Tailandia (Lakorn)",
            thumbnail = '{}/iconos/8-01.svg'.format(host),
            url = '{}/pais/Tailandia'.format(host)
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            list_type = 'pais',
            title = "Filipinas",
            thumbnail = '',
            url = '{}/pais/Filipinas'.format(host)
        )
    )
    return itemlist

def alpha(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    letters = soup.find('nav', class_='container navbar bg-white').find('div', class_='ml-d-27').find_all('a')
    for letter in letters:
        itemlist.append(
            Item(
                action = 'list_all',
                channel = item.channel,
                list_type = 'data',
                title = letter.text.upper(),
                url = '{}{}'.format(host, letter['href'])
            )
        )
    return itemlist

def set_lang(title):
    exceptions = {'vivo': '#Saraitda'}
    array = title.encode().decode().split('|')
    if len(array) > 1:
        if 'latino' in array[1].lower():
            language = 'LAT'
        else:
            language = ''
    else:
        language = ''
    title = array[0].strip()
    for exc, repl in exceptions.items():
        if exc in title.lower():
            title = repl
    return title, language

def list_all(item):
    logger.info()
    itemlist = []
    matches = []
    if item.list_type in ['pais', 'pelicula', 'categorias', 'data', 'buscar', 'novedades']:
        if item.list_type in ['pais', 'pelicula', 'categorias', 'data']:
            soup = create_soup(item.url)
            json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)['props']['pageProps']['data']
            if item.list_type in ['pelicula']:
                contentType = 'movie'
            elif item.list_type in ['categorias', 'pais', 'data']:
                contentType = 'tvshow'
            container = soup.find('div', class_='container wrapper').find('div', class_='row')
            items = container.find_all('a', class_='mb-3')
            for i, it in enumerate(items):
                j = json[i]
                action = 'seasons'
                status = j['estado']
                title, language = set_lang(it.find('span', class_='text-dark').text)
                if contentType == 'movie':
                    contentSerieName = None
                    contentTitle = title
                else:
                    contentSerieName = title
                    contentTitle = None
                thumb = 'https://img.comamosramen.com/{}-high.webp'.format(j['img'])
                url = '{}{}'.format(host, it['href'])
                matches.append([action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url])
        elif item.list_type in ['buscar', 'novedades']:
            json = httptools.downloadpage(item.url).json
            contentType = ''
            for j in json:
                action = 'seasons'
                status = j['estado']
                title, language = set_lang(j['uniqid'].split('-', 1)[1])
                if contentType == 'movie':
                    contentSerieName = None
                    contentTitle = title
                else:
                    contentSerieName = title
                    contentTitle = None
                thumb = 'https://img.comamosramen.com/{}-high.webp'.format(j['img'])
                id_ = j['uniqid'].split('-', 1)
                url = '{}/ver/{}'.format(host, '{}-{}'.format(id_[0], id_[1].replace('-', '%20')))
                matches.append([action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url])
    else:
        logger.debug("\n" + str(soup.prettify()))
        raise Exception('No soportado (¿Cambio de estructura?)')
        return

    for action, contentSerieName, contentTitle, contentType, language, status, title, thumb, url in matches:
        it = Item(
                action = action,
                contentType = contentType,
                channel = item.channel,
                language = language,
                title = unify.add_languages(title, language),
                thumbnail = thumb,
                url = url
            )
        if contentSerieName:
            it.contentSerieName = contentSerieName
        elif contentTitle:
            it.contentTitle = contentTitle
        itemlist.append(it)
    return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    json = jsontools.load(soup.find('script', id='__NEXT_DATA__').text)
    content_id = json['props']['pageProps'].get('id')
    if not content_id:
        id_ = item.url.replace(host, '').split('/')[2].split('-', 1)
        content_id = '{}-{}'.format(id_[0], id_[1].replace('-', '%20'))
    episodios = httptools.downloadpage('https://fapi.comamosramen.com/api/byUniqId/{}'.format(content_id)).json
    seasons = []
    for episodio in episodios['temporadas']:
        if len(seasons) > 0 and seasons[-1]['temporada'] == int(episodio['temporada']):
            seasons[-1]['episodios'].append(episodio)
        else:
            seasons.append({'temporada': int(episodio['temporada']), 'episodios': []})
            seasons[-1]['episodios'].append(episodio)

    for season in seasons:
        title, language = set_lang(episodios.get('titulo'))
        ogtitle = title
        # if scrapertools.find_single_match(ogtitle, '(?is)Título original (.*?)\n'):
            # ogtitle = scrapertools.find_single_match(ogtitle, '(?is)Título original (.*?)\n')
        if item.language:
            language = item.language
        if episodios.get('categorias'):
            if 'Audio Latino' in episodios.get('categorias'):
                language = 'LAT'
        if episodios.get('tipo'):
            if episodios.get('tipo') in ['pelicula']:
                contentType = 'movie'
            else:
                contentType = 'tvshow'
        else:
            contentType = ''
        infoLabels = {'year': episodios.get('año')}
        it = Item(
                action = 'episodesxseason',
                channel = item.channel,
                contentType = contentType,
                infoLabels = infoLabels,
                json_episodios = season['episodios'],
                language = language,
                plot = episodios.get('descripcion'),
                thumbnail = item.thumbnail,
                title = unify.add_languages((config.get_localized_string(60027) % str(season['temporada'])), language),
                url = item.url
            )
        if contentType == 'movie':
            it.contentTitle = ogtitle
        else:
            it.contentSeason = season['temporada']
            it.contentSerieName = ogtitle
        # unify.title_format(it)
        itemlist.append(it)
    if not item.videolibrary:
        tmdb.set_infoLabels(itemlist, True, force_no_year = True)
    if len(itemlist) == 1:
        itemlist = episodesxseason(itemlist[0])
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

    if not item.contentType == 'movie':
        seasons_list = seasons(item)
        if len(seasons_list) > 0:
            if isinstance(seasons_list[0], list):
                for season in seasons_list:
                    itemlist.extend(episodesxseason(season))
            else:
                return seasons_list
    else:
        itemlist.extend(findvideos(item))
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    episodios = item.json_episodios
    for episodio in episodios:
        infoLabels = item.infoLabels
        language = 'VOSE'
        if not item.language:
            if episodio.get('estado'):
                if 'SUBT' in episodio.get('estado'):
                    language = 'VOSE'
        else:
            language = item.language
        it = Item(
                action = 'findvideos',
                channel = item.channel,
                infoLabels = infoLabels,
                language = language,
                thumbnail = item.thumbnail,
                title = episodio['capitulo'],
                urls = episodio['opciones'],
                url = item.url
            )
        if not item.contentType == 'movie':
            it.contentSeason = item.contentSeason
            it.contentEpisodeNumber = episodio['capitulo']
        itemlist.append(it)
    if not item.videolibrary:
        tmdb.set_infoLabels(itemlist, True)
    for it in itemlist:
        it.title = unify.add_languages('{}x{}: {}'.format(it.contentSeason, it.contentEpisodeNumber, it.contentTitle), it.language)
    if len(itemlist) == 1 and item.contentType == 'movie':
        return findvideos(itemlist[0])
    else:
        return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    if item.videolibrary:
        return seasons(item)
    servers = item.urls
    for option in servers:
        url = ''
        server = server_list.get(option['opcion'].lower())
        url = '{}{}'.format(server_urls.get(server, ''), option['url'])
        if not server:
            continue
        serv_name = servertools.get_server_name(server)
        new_item = Item(
            action = 'play',
            channel = item.channel,
            infoLabels = item.infoLabels,
            language = item.language,
            server = server,
            thumbnail = item.thumbnail,
            title = unify.add_languages('{}: {}'.format(config.get_localized_string(60335), serv_name.title()), item.language),
            url = url
        )
        if hasattr(item, 'fanart'):
            new_item.fanart = item.fanart
        if item.contentPlot:
            new_item.contentPlot = item.contentPlot
        if not item.contentType == 'movie':
            unify.title_format(new_item)
        itemlist.append(new_item)
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
