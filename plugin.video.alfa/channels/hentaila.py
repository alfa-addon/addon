# -*- coding: utf-8 -*-
import sys
import xbmcgui

from bs4 import BeautifulSoup
from core import httptools, scrapertools, servertools, tmdb
from core.item import Item
from platformcode import config, logger, platformtools
from channelselector import get_thumb
from modules import autoplay

canonical = {
             'channel': 'hentaila', 
             'host': config.get_setting("current_host", 'hentaila', default=''), 
             'host_alt': ["https://hentaila.com"], 
             'host_black_list': ["https://www3.hentaila.com", "https://www4.hentaila.com"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
host = host.rstrip("/")

IDIOMAS = {'VOSE': 'VOSE'}
list_language = list(IDIOMAS.values())
list_servers = ['mega', 'fembed', 'mp4upload', 'yourupload', 'sendvid']
list_quality = []

def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(
        Item(
            action = "newest",
            channel = item.channel,
            fanart = item.fanart,
            title = "Novedades",
            thumbnail = get_thumb("newest", auto=True),
            viewType = "videos"
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            title = "Populares",
            thumbnail = get_thumb("more watched", auto=True),
            url = host + "/catalogo?order=popular"
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            title = "Destacados de la semana",
            thumbnail = get_thumb("hot", auto=True),
            url = host + "/catalogo?order=score"
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "newepisodes",
            title = "Nuevos episodios",
            thumbnail = get_thumb("new episodes", auto=True),
            url = host
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel =  item.channel,
            fanart = item.fanart,
            title = "Estrenos próximos",
            thumbnail = get_thumb("premieres", auto=True),
            url = host + "/catalogo?order=latest_released"
        )
    )
    itemlist.append(
        Item(
            action = "categories",
            channel = item.channel,
            fanart = item.fanart,
            title = "Directorio Hentai (Categorías)",
            thumbnail = get_thumb("categories", auto=True),
            url = host,
            viewType = "–"
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            title = "Todos",
            thumbnail = get_thumb("all", auto=True),
            url = host + "/catalogo"
        )
    )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            title = "Buscar...",
            thumbnail = get_thumb("search", auto=True),
            url = host
        )
    )
    itemlist.append(
        Item(
            action = "setting_channel",
            channel = item.channel,
            plot = "Configurar canal",
            title = "Configurar canal", 
            thumbnail = get_thumb("setting_0.png")
        )
    )
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def setting_channel(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def categories(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            fanart = item.fanart,
            param = "genre",
            plot = "Yuri, Yaoi, Tentáculos, Lolis, Vanilla, Netorare, Súcubos, Ahegao, etc.",
            thumbnail = get_thumb("genres", auto=True),
            title = "Por género"
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            fanart = item.fanart,
            param = "alphabet",
            plot = "A-Z",
            thumbnail = get_thumb("alphabet", auto=True),
            title = "Por letra"
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            fanart = item.fanart,
            param = "",
            plot = "Adiós, píxeles y barras negras 7u7",
            thumbnail = get_thumb("adults", auto=True),
            title = "Sin censura",
            url = host + "/catalogo?uncensored="
        )
    )
    itemlist.append(
        Item(
            action = "filter_by_selection",
            channel = item.channel,
            fanart = item.fanart,
            param = "status",
            plot = "En emisión y finalizados",
            thumbnail = get_thumb("on air", auto=True),
            title = "Por estado"
        )
    )
    itemlist.append(
        Item(
            action = "set_adv_filter",
            channel = item.channel,
            fanart = item.fanart,
            filters = {'genre': '', 'alphabet': '', 'censor': '', 'status': '', 'orderby': ''},
            param = "",
            plot = "Refinar la búsqueda combinando género, estado, sin censura, etc.",
            thumbnail = get_thumb("categories", auto=True),
            title = "Combinar criterios"
        )
    )
    return itemlist


def create_soup(url, post=None, headers=None):
    logger.info()

    data = httptools.downloadpage(url, post=post, headers=headers, canonical=canonical).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def newest(categoria):
    item = Item()
    item.action = "newest"
    item.channel = "hentaila"
    item.param = ""
    item.thumbnail = get_thumb("newest", auto=True)
    item.title = "Novedades"
    item.url = host + "/catalogo?order=latest_released"
    return list_all(item)


def list_all(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)

    if item.param == "newepisodes":
        soup = soup.find('section', class_='from-mute col-span-full grid items-start gap-4 bg-radial-[closest-side] py-3')

    if item.param == "episodes":
        soup = soup.find('section', class_='from-mute col-span-full grid items-start gap-6 bg-radial-[closest-side] py-3')

    articles = soup.find_all('article', class_='group/item')
    for article in articles:
        infoLabels = {}
        thumb = article.find('img')['src']
        if not thumb.startswith('http'):
            thumb = host + thumb
        if item.param in ["newepisodes", "episodes"]:
            if item.param == "episodes":
                contentSerieName = item.contentSerieName
            else:
                contentSerieName = article.find('div', class_='text-2xs').string.strip()
            episode = article.select_one('span.text-lead.font-bold')
            infoLabels = {}
            infoLabels['season'] = 1
            infoLabels['episode'] = int(episode.string) if episode else 1
            title = "{}x{} {}".format(infoLabels['season'], infoLabels['episode'], contentSerieName)
            contentType = 'episode'
            action = "findvideos"
        else:
            contentType = 'tvshow'
            contentSerieName = article.find('h3', class_='line-clamp-2').string.strip()
            title = contentSerieName
            action = "episodios"
        url = host + article.find('a', href=True)['href']
        itemlist.append(
            Item(
                action = action,
                channel = item.channel,
                contentType = contentType,
                contentSerieName = contentSerieName,
                fanart = item.fanart,
                infoLabels = infoLabels,
                title = title,
                thumbnail = thumb,
                url = url
            )
        )
        # logger.debug("title='%s', url='%s', thumb='%s'" % (title, url, thumb))
    # Paginación
    next_page = soup.find('a', class_='btn', string='Â»')
    if next_page:
        next_page_url = next_page['href']
        if not next_page_url.startswith('http'):
            next_page_url = host + next_page_url
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                fanart = item.fanart,
                title = "Siguiente página",
                thumbnail = get_thumb("next page", auto=True),
                url = next_page_url
            )
        )

    tmdb.set_infoLabels(itemlist, True, include_adult=True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    itemlist.extend(episodesxseason(item))
    return itemlist


def episodesxseason(item):
    logger.info()
    item.param = "episodes"
    return list_all(item)


def findvideos(item):
    logger.info()
    itemlist = []
    data_js = scrapertools.find_multiple_matches(
        httptools.downloadpage(item.url, canonical=canonical).data,
        r'\{server:"[^"]+",url:"([^"]+)"\}'
    )
    
    # logger.debug("data_js= %s" % data_js)
    for url in data_js:
        itemlist.append(
            item.clone(
                action = "play",
                title = '%s',
                url = url
            )
        )

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    
    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools

    itemlist = [i for i in itemlist if i.title != "Directo"]
    
    autoplay.start(itemlist, item)
    
    return itemlist


def search(item, texto):
    logger.info()

    if texto != '':
        texto = texto.replace(" ", "+")
        item.url = "%s/catalogo?search=%s" % (host, texto)
        return list_all(item)
    else:
        return []


def filter_by_selection(item, clearUrl=False):
    logger.info()
    itemlist = []
    if item.param == 'genre':
        # {id:4,name:"Casadas",slug:"casadas"}
        data = httptools.downloadpage(host + "/catalogo", canonical=canonical).data
        pattern = r'\{id:\d+,name:"([^"]+)",slug:"([^"]+)"\}'
        result = scrapertools.find_multiple_matches(data, pattern)
        matches = []
        for name, slug in result:
            matches.append(('?genre={}'.format(slug), name))
    elif item.param == 'alphabet':
        alphabet = "0ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        matches = []
        for char in alphabet:
            matches.append(('?letter={}'.format(char), char))
    elif item.param == 'censor':
        matches = [('?uncensored=', 'Solo sin censura')]
    elif item.param == 'status':
        matches = [('?status=emision', 'Solo en emisión'),
                   ('?status=finalizado', 'Solo finalizados')]
    elif item.param == 'orderby':
        matches = [('?order=popular', 'Ordenar por popularidad'),
                   ('?order=latest_released', 'Ordenar por más recientes')]
    for url, title in matches:
        # logger.debug("url {}, title {}".format(url, title), True)
        if clearUrl is True:
            url = url.replace('?', '')
        else:
            url = '{}/catalogo{}'.format(host, url)
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                title = title,
                fanart = item.fanart,
                url = url,
            )
        )
    return itemlist


def set_adv_filter(item):
    logger.info()
    genreitems = filter_by_selection(Item(param = "genre"), clearUrl = True)
    genres = ['Predeterminado (todos)']
    for i in genreitems:
        genres.append(i.title)
    result = platformtools.dialog_select('Elige un género', genres, useDetails=False)
    if result != -1 and result != 0:
        item.filters['genre'] = genreitems[result - 1]
    elif result == -1:
        return True

    alphaitems = filter_by_selection(Item(param = "alphabet"), clearUrl = True)
    letters = []
    letters.append('Predeterminado (todas)')
    for i in alphaitems:
        letters.append(i.title)
    result = platformtools.dialog_select('Elige una letra inicial', letters, useDetails=False)
    if result != -1 and result != 0:
        item.filters['alphabet'] = alphaitems[result - 1]
    elif result == -1:
        return True

    censorstates = filter_by_selection(Item(param = "censor"), clearUrl = True)
    censor = []
    censor.append('Predeterminado (con y sin censura)')
    for i in censorstates:
        censor.append(i.title)
    result = platformtools.dialog_select('Elige el tipo de censura', censor, useDetails=False)
    if result != -1 and result != 0:
        item.filters['censor'] = censorstates[result - 1]
    elif result == -1:
        return True

    statusstates = filter_by_selection(Item(param = "status"), clearUrl = True)
    statuses = []
    statuses.append('Predeterminado (ambos)')
    for i in statusstates:
        statuses.append(i.title)
    result = platformtools.dialog_select('Elige el estado de emisión', statuses, useDetails=False)
    if result != -1 and result != 0:
        item.filters['status'] = statusstates[result - 1]
    elif result == -1:
        return True

    statusstates = filter_by_selection(Item(param = "orderby"), clearUrl = True)
    statuses = []
    statuses.append('Predeterminado (ambos)')
    for i in statusstates:
        statuses.append(i.title)
    result = platformtools.dialog_select('Elige cómo ordenar los resultados', statuses, useDetails=False)
    if result != -1 and result != 0:
        item.filters['orderby'] = statusstates[result - 1]

    if item.filters['genre'] or item.filters['alphabet'] or item.filters['censor'] or item.filters['status'] or item.filters['orderby']:
        filtered_url = host + '/catalogo'
        current_filter = ''
        isset_filter = False
        if item.filters['genre'] != '':
            current_filter += "Género: " + item.filters['genre'].title + ". "
            filtered_url += '?' + item.filters['genre'].url
            isset_filter = True
        if item.filters['alphabet'] != '':
            current_filter += 'Inicial: ' + item.filters['alphabet'].title + '. '
            separator = '&' if isset_filter else '?'
            filtered_url += separator + item.filters['alphabet'].url
            isset_filter = True
        if item.filters['censor'] != '':
            current_filter += 'Censura: ' + item.filters['censor'].title + '. '
            separator = '&' if isset_filter else '?'
            filtered_url += separator + item.filters['censor'].url
            isset_filter = True
        if item.filters['status'] != '':
            current_filter += 'Estado: ' + item.filters['status'].title + '. '
            separator = '&' if isset_filter else '?'
            filtered_url += separator + item.filters['status'].url
            isset_filter = True
        if item.filters['orderby'] != '':
            current_filter += 'Estado: ' + item.filters['orderby'].title + '. '
            separator = '&' if isset_filter else '?'
            filtered_url += separator + item.filters['orderby'].url
        filteritem = Item(
            channel =  item.channel,
            fanart = item.fanart,
            param = '',
            url = filtered_url
        )
        return list_all(filteritem)
    else:
        return True