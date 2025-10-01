# -*- coding: utf-8 -*-
# -*- Channel Cuevana2español -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from channelselector import get_thumb
from modules import autoplay
from modules import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

list_quality = []
list_servers_black = {"netu"}
list_serversx = {'filemoon' : 'filemoon', 'vidhide' : 'vidhidepro'}
list_servers = ['streamwish', 'filemoon', 'voes', 'doodstream', 'streamtape', 'plushstream', 'vidhide']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'cuevana2espanol', 
             'host': config.get_setting("current_host", 'cuevana2espanol', default=''), 
             'host_alt': ["https://www.cuevana2espanol.net/"], 
             'host_black_list': ["https://www.cuevana2espanol.icu/", "https://cuevana2espanol.com/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt,  
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

encoding = "utf-8"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
language = []
url_replace = []

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=host+'archives/movies/', 
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Series',  action='sub_menu', url=host+'archives/series/', 
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Últimas', url=item.url + "page/", action='list_all', pagina=1,
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Estrenos', url=item.url+'releases/page/', action='list_all', pagina=1, 
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Top Semana', url=item.url+'top/week/page/', action='list_all', pagina=1, 
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Top Día', url=item.url+'top/day/page/', action='list_all', pagina=1,
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))
    
    if item.c_type == 'peliculas':
        itemlist.append(Item(channel=item.channel, title='Generos', action='section', url=host,
                             thumbnail=get_thumb('genres', auto=True), c_type=item.c_type))
    else:
        itemlist.append(Item(channel=item.channel, title='Episodios', action='list_all', url=host+'archives/episodes',
                             thumbnail=get_thumb('episodes', auto=True), c_type='episodios'))

    return itemlist


def section(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(host + "_next/static/chunks/170-415b9c38dc5af95d.js", encoding="unicode_escape").data
    
    data = data.decode('unicode_escape')
    patron = 'href:"(/genres/.+?)".+?children:"(.+?)"'
    logger.info("patron: %s" %(type(patron)))
    logger.info("data: %s" %type(data))
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for url, title in matches:
        itemlist.append(Item(channel=item.channel, title=title, action='list_all', url=host+url+"/page/", pagina=1,
                             thumbnail=get_thumb('episodes', auto=True) ))

    genres = {'Acción': 'genres/accion/', 
              'Animación': 'genres/animacion/', 
              'Crimen': 'genres/crimen/', 
              'Familia': 'genres/familia/', 
              'Misterio': 'genres/misterio/', 
              'Suspense': 'genres/suspenso/', 
              'Aventura': 'genres/aventura/', 
              'Ciencia Ficción': 'genres/ciencia-ficcion/', 
              'Drama': 'genres/drama/', 
              'Fantasía': 'genres/fantasia/', 
              'Romance': 'genres/romance/', 
              'Terror': 'genres/terror/'
              }

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url + "%s" %item.pagina, canonical=canonical).data
    patron  = '(?ims)(?:bdOz3|_LFJR).*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<h3>([^<]+).*?'
    patron += '<span>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for url, title, annio in matches:
        idioma = "Latino"
        item.infoLabels['year'] = annio
        title = scrapertools.unescape(title)
        url = "%s%s" %(host, url)
        new_item = Item(channel=item.channel, url=url, title=title, thumbnail="", c_type =item.c_type,
                        language=idioma, infoLabels={"year": annio})
        if "series" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, True)
    
    url_pagina = scrapertools.find_single_match(data, 'class="page-link" href="([^"]+)')
    if url_pagina != "":
        paginax = "Pagina: %s" %(item.pagina + 1)
        itemlist.append(Item(channel = item.channel, action = "list_all", title = paginax, url = item.url, pagina = item.pagina + 1))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    seasons = ""
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = '(?ims)type="application/json">(.*?)</script><script'
    match = scrapertools.find_single_match(data, patron)
    json_data = jsontools.load(match)["props"]["pageProps"]["post"]["seasons"]
    for elem in json_data:
        if elem.get('number', '') > 0:
            season = elem['number']
            title = "Temporada %s" % season
            infoLabels["season"] = int(season)
            itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseason",
                                 language=item.language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist[:-1]:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = '(?ims)type="application/json">(.*?)</script><script'
    match = scrapertools.find_single_match(data, patron)
    json_data = jsontools.load(match)
    temporadas = json_data["props"]["pageProps"]["post"]["seasons"]
    for temporada in temporadas:
        if temporada['number'] == season:
            episodios = temporada["episodes"]
            break
    for elem in episodios:
        cap = elem['number']
        url = "%s/seasons/%s/episodes/%s" %(item.url, season, cap)
        title = "%sx%s" % (season, cap)
        infoLabels["episode"] = cap
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                               language=item.language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = [];
    
    data = httptools.downloadpage(item.url, canonical=canonical).data
    
    patron  = '(?ims)type="application/json">(.*?)</script><script'
    match = scrapertools.find_single_match(data, patron)
    
    if "/series/" in item.url:
        json_data = jsontools.load(match)["props"]["pageProps"]["episode"]["players"]
    else:
        json_data = jsontools.load(match)["props"]["pageProps"]["post"]["players"]
    for lang in json_data:
        for info_url in json_data[lang]:
            server = info_url["cyberlocker"]
            if server in list_servers_black: continue
            if server in list_serversx.keys(): server = list_serversx[server]
            qlty = info_url["quality"]
            url = info_url["result"]
            # logger.info("%s %s %s %s" %(lang, server, qlty, url))
            itemlist.append(Item(
                            channel=item.channel,
                            contentTitle=item.contentTitle,
                            contentThumbnail=item.thumbnail,
                            infoLabels=item.infoLabels,
                            language=lang,
                            title='%s' %server,
                            action="play",
                            url=url,
                           ))
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    data = httptools.downloadpage(item.url, encoding=encoding).data
    patron = "var url = '([^']+)"
    match = scrapertools.find_single_match(data, patron)
    item.url = match
    return [item]


def search(item, texto, **AHkwargs):
    logger.info()
    
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + 'search?q=' + texto
        
        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []
    
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'archives/movies'

        itemlist = list_all(item)

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
