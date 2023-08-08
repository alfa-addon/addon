# -*- coding: utf-8 -*-
# -*- Channel HenaoJara -*-
# -*- Created for Alfa Addon -*-
# -*- By DieFeM -*-

from platformcode import logger
from platformcode import config
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channelselector import get_thumb
import sys
import base64
import re

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
else:
    import urllib
    from urlparse import urlparse
    from urlparse import parse_qs

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'henaojara', 
             'host': config.get_setting("current_host", 'henaojara', default=''), 
             'host_alt': ["https://www.henaojara.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = 'https://www.henaojara.com/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            thumbnail = get_thumb('search', auto=True),
            title = "Buscar",
            url = "%s%s" % (host, '?s='),
            viewType = "tvshows",
            sufix = ""
        )
    )

    itemlist.append(
        Item(
            action = "new_episodes",
            channel = item.channel,
            thumbnail = get_thumb('new_episodes', auto=True),
            title = "Nuevos Episodios",
            url = host,
            viewType = "episodes"
        )
    )

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            thumbnail = get_thumb('movies', auto=True),
            title = "Películas",
            url = host + 'ver/category/pelicula/',
            viewType = "movies"
        )
    )

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            thumbnail = get_thumb('tvshows', auto=True),
            title = "Series",
            url = host + 'ver/category/categorias/',
            viewType = "tvshows"
        )
    )

    itemlist.append(
        Item(
            channel = item.channel,
            title = "Categorías",
            action = "show_categories",
            thumbnail = get_thumb('categories', auto=True),
            url = host
        )
    )

    return itemlist


def show_categories(item):
    logger.info()

    data = get_source(item.url)
    patron = 'cat-item-\d+"><a href="([^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    itemlist = []

    for url, title in matches:
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                thumbnail = get_thumb('all', auto=True),
                title = title,
                url = url,
                viewType = "tvshows"
            )
        )

    return itemlist


def search(item, texto):
    logger.info()
    texto = urllib.quote_plus(texto, "") #https://docs.python.org/2/library/urllib.html#urllib.quote_plus (escapa los caracteres de la busqueda para usarlos en la URL)
    item.url = item.url + texto

    try:
        if texto != '':
            return list_all(item)
        else:
            return []

    except:
        for line in sys.exc_info():
            logger.error("%s" % line)

        return []


def newest(categoria):
    
    itemlist = []
    
    if categoria == 'anime':
        itemlist = new_episodes(Item(url=host))
    return itemlist


def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, 'Episodes">(.*?)</ul>')
    patron = 'href="([^"]+).*?src="([^"]+).*?class="ClB">(\d+)x(\d+).*?class="Title">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumbnail, season, episode, title in matches:

        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
            
        lang, c_title = clear_title(title)
        
        infoLabels = {}
        infoLabels['season'] = int(season or 1)
        infoLabels['episode'] = int(episode or 1)

        itemlist.append(
            Item(
                 channel = item.channel,
                 action = "findvideos",
                 url = url,
                 contentSerieName = c_title,
                 language = lang,
                 thumbnail = thumbnail,
                 contentType = 'episode',
                 infoLabels = infoLabels
            )
        )

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article.*?<a href="([^"]+)">.*?data-src="([^"]+)".*?class="Title">([^<]+).*?class="Qlty">([^<]+).*?class="Description"><p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumbnail, title, cType, plot in matches:

        if 'pelicula' in title.lower() or cType == 'ESTRENO':
            cType = 'PELICULA'

        if item.title == 'Series' and cType == 'PELICULA':
            continue

        if item.title == 'Películas' and cType != 'PELICULA':
            continue

        title = scrapertools.htmlparser(title)
        plot = scrapertools.htmlparser(plot)

        lang, c_title = clear_title(title)

        season = ''
        seasonPattern = '\s+Temporada\s+(\d+)'
        if re.search(seasonPattern, c_title):
            season = scrapertools.find_single_match(c_title, seasonPattern)
            c_title = re.sub(seasonPattern, '', c_title).strip()

        new_item = Item(
                action = 'episodes',
                channel = item.channel,
                plot = plot,
                thumbnail = thumbnail,
                title = c_title,
                language = lang,
                url = url
            )

        if cType == 'PELICULA':
            new_item.contentType = 'movie'
            new_item.contentTitle = c_title
        else:
            new_item.contentType = 'tv'
            new_item.contentSerieName = c_title
            new_item.contentSeasonNumber = season

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True, force_no_year=True)

    for item in itemlist:
        if item.contentType == 'list' and item.contentSeasonNumber != '':
            item.title += ' [COLOR blue][Temporada ' +  item.contentSeasonNumber + '][/COLOR]'

    # Paginacion
    next_patron = r'<a class="next page-numbers" href="([^"]+)">'
    next_page = scrapertools.find_single_match(data, next_patron)

    if next_page != '':
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                thumbnail = 'https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                title = "Siguiente página >>",
                url = "%s%s" % (host, next_page) if not host in next_page else next_page,
                viewType = item.viewType,
                sufix = item.sufix
            )
        )

    return itemlist


def episodes(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '"Num">(\d+).*?<a href="([^"]+)".*?<img.*?src="([^"]+).*?href="[^"]+">(.+?)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    infoLabels = item.infoLabels
    season = int(item.contentSeasonNumber or 1)
    
    for episode, url, thumbnail, title in matches:
        title = scrapertools.remove_htmltags(title)
        
        lang, c_title = clear_title(title)
        
        title = "%s - %s" % (episode, c_title)

        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
            
        infoLabels['season'] = season
        infoLabels['episode'] = int(episode or 1)
       
        new_item = Item(
                channel = item.channel,
                title = title,
                contentSerieName = item.contentSerieName,
                url = url,
                action = 'findvideos',
                language = item.language
            )

        if item.contentType != 'movie':
            new_item.contentType = 'episode'
            new_item.infoLabels = infoLabels
        
        itemlist.append(new_item)
    
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.htmlparser(data)
    patron = 'id="Opt\d+.*?iframe.*?src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url in matches:
        if url != '':
            url = scrapertools.htmlparser(url)
            iframedata = get_source(url)
            iframeUrl = scrapertools.find_single_match(iframedata, '<iframe.*?src="([^"]+)')

            if iframeUrl != "":
                iframeUrl = check_hjstream(iframeUrl)
                uriData = urlparse(iframeUrl)
                itemlist.append(
                    Item(
                        action = 'play',
                        channel = item.channel,
                        plot = 'Host: %s' % uriData.hostname,
                        infoLabels = item.infoLabels,
                        title = '%s',
                        url = iframeUrl,
                        viewType = item.viewType
                    )
                )

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    return itemlist


def get_source(url, json=False, unescape=True, **opt):
    logger.info()

    opt['canonical'] = canonical
    data = httptools.downloadpage(url, hide_infobox = True, **opt)

    if json:
        data = data.json
    else:
        data = data.data
        data = scrapertools.replace(r'\n|\r|\t|&nbsp;|<br>|\s{2,}|\(|\)', "", data) if unescape else data

    return data

# henaojara usa varios scripts para embeber algunos enlaces en diferentes subdominios de hjstream.xyz,
# esta funcion se encarga de extraer el enlace del servidor original a partir de los parámetros de la url,
# en el parámetro v (v=xxxx), a veces en texto plano, a veces en base64.
def check_hjstream(url):
    logger.info()

    if "hjstream.xyz" in url:
        queryData = parse_qs(urlparse(url).query)
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
    
    title = re.sub(r'HD|Español Castellano|Sub Español|Español Latino|ova\s+\d+:|OVA\s+\d+|\:|\((.*?)\)|\s19\d{2}|\s20\d{2}', '', title)
    title = re.sub(r'\s:', ':', title)
    title = " ".join( title.split() )

    return lang, title