# -*- coding: UTF-8 -*-

import re

from modules import autoplay
from modules import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core import urlparse
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib.alfa_assistant import is_alfa_installed

forced_proxy_opt = 'ProxySSL'

cf_assistant = "force" if is_alfa_installed() else False
forced_proxy_opt = None if cf_assistant else 'ProxyCF'
cf_debug = True

canonical = {
             'channel': 'asialiveaction', 
             'host': config.get_setting("current_host", 'asialiveaction', default=''), 
             'host_alt': ["https://asialiveaction.com"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': cf_assistant, 
             'cf_assistant_ua': True, 'cf_assistant_get_source': True if cf_assistant == 'force' else False, 
             'cf_no_blacklist': True, 'cf_removeAllCookies': False if cf_assistant == 'force' else True,
             'cf_challenge': False, 'cf_returnkey': 'url', 'cf_partial': True, 'cf_debug': cf_debug, 
             'cf_cookies_names': {'cf_clearance': False},
             'CF_if_assistant': True if cf_assistant is True else False, 'retries_cloudflare': -1, 
             'CF_stat': True if cf_assistant is True else False, 'session_verify': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': True
            }
host = canonical['host'] or canonical['host_alt'][0]

IDIOMAS = {"1387-1": "CAST", "1388-1": "LAT", "1385-1": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gvideo', 'openload','streamango']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas",
                         thumbnail=get_thumb("movies", auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=peliculas")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas - Latino",
                         thumbnail=get_thumb("lat", auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=peliculas&idioma%5B%5D=audio-latino")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas - Castellano",
                         thumbnail=get_thumb("cast", auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=peliculas&idioma%5B%5D=audio-espanol")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas - Subtitulado",
                         thumbnail=get_thumb("vose", auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=peliculas&idioma%5B%5D=subtitulado")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Series", 
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=series")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Series - Latino", 
                         thumbnail=get_thumb('lat', auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=series&idioma%5B%5D=audio-latino")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Series - Castellano", 
                         thumbnail=get_thumb('cast', auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=series&idioma%5B%5D=audio-espanol")))
    itemlist.append(Item(channel=item.channel, action="list_all", title="Series - Subtitulado", 
                         thumbnail=get_thumb('vose', auto=True),
                         url=urlparse.urljoin(host, "/navegacion/?tipo%5B%5D=series&idioma%5B%5D=subtitulado")))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", 
                         thumbnail=get_thumb("search", auto=True), 
                         url=host))
    
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    if texto != "":
        texto = urlparse.quote(texto)
        item.url = "%s?s=%s" % (host, texto)

    try:
        return list_all(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def list_all(item):
    logger.info()
    itemlist = []
    soup = httptools.downloadpage(item.url, canonical=canonical, soup=True).soup
    
    if not soup:
        return itemlist
    
    for elem in soup.find_all("li", class_="splide__slide"):
        thumbnail = elem.a.div.img['src']
        title = elem.a.div.h5.text.strip()
        url = elem.a['href']
        if url:
            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumbnail)
                        
            if elem.find("span", class_="flag-tv"):
                new_item.contentType = 'tvshow'
                new_item.contentSerieName = title
                new_item.action = 'episodios'
            else:
                new_item.contentType = 'movie'
                new_item.contentTitle = title
                new_item.action = 'episodios'
                new_item.year = '-'
            
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    #pagination
    pagination = soup.find("div", class_="paginado")
    if pagination:
        pages = pagination.find_all("a")
        if pages:
            url_next_page = pages[-1]['href']
    
            if len(itemlist) > 0 and url_next_page:
                if not url_next_page.startswith(host):
                    url_data = urlparse.urlparse(item.url)
                    url_data = url_data._replace(query=str(url_next_page).lstrip('?'))
                    url_next_page = urlparse.urlunparse(url_data)
                    
                if url_next_page != item.url:
                    itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = list()
    soup = httptools.downloadpage(item.url, canonical=canonical, soup=True).soup
    infoLabels = item.infoLabels.copy()
    if not soup:
        return itemlist
    
    for elem in soup.find_all("div", class_="episodio-unico"):
        url = elem.a['href']
        episode = elem.a.b.find(string=True, recursive=False).strip()
        if "Episodio" in episode:
            episode = episode.replace("Episodio ", "")
            infoLabels['season'] = 1
            infoLabels['episode'] = episode
            itemlist.append(item.clone(action='findvideos',
                                       url=url, 
                                       title="%sx%s - %s" % (infoLabels['season'], infoLabels['episode'], item.contentSerieName),
                                       infoLabels=infoLabels,
                                       contentType='episode'))
        else:
            itemlist.append(item.clone(action='findvideos',
                                       url=url))
    
    for elem in soup.find_all("div", class_="episodio-group"):
        episode = elem.button.b.find(string=True, recursive=False).strip()
        if "Episodio" in episode:
            episode = episode.replace("Episodio ", "")
            infoLabels['season'] = 1
            infoLabels['episode'] = episode
            new_item = item.clone(action='findvideos',
                                  title="%sx%s - %s" % (infoLabels['season'], infoLabels['episode'], item.contentSerieName),
                                  infoLabels=infoLabels,
                                  contentType='episode')
        else:
            new_item = item.clone(action='findvideos')
        
        for version in elem.find_all("li"):
            autor = version.a.b.find(string=True, recursive=False).strip()
            itemlist.append(new_item.clone(plot="Versión de: %s" % autor, url=version.a['href']))
    
    if item.contentType == 'tvshow':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != "episodios":
            itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                                url=item.url, action="add_serie_to_library", extra="episodios",
                                contentSerieName=item.contentSerieName))
        return itemlist
    else:
        if len(itemlist) == 1:
            return findvideos(itemlist[0])
        else:
            return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, canonical=canonical).data
    if not data:
        return itemlist
    videos_data = scrapertools.find_single_match(data, 'var\s+allVideos\s+=\s+([^;]+);')
    if not videos_data:
        return itemlist
    from ast import literal_eval
    try:
        videos_dict = literal_eval(videos_data)
    except Exception as e:
        logger.error("Error parsing videos data: %s", e)
        return itemlist
    # {"1385-1":[["FM","https:\/\/filemoon.sx\/e\/wekudhsephgh",0,0],["NT","https:\/\/hqq.ac\/e\/bUNXem0zMlBDODgzMjc2NFZWNFhDdz09",0,0]],"1387-1":[["FM","https:\/\/filemoon.sx\/e\/4aytx3t9s127",0,0],["NT","https:\/\/hqq.ac\/e\/YkNXQTYrREJYdGxxUVNHaU5MSDYvUT09",0,0]]}
    for video in videos_dict:
        lang = IDIOMAS.get(video, video)
        matches = [entry[1] for entry in videos_dict[video]]
        for url in matches:
            url = urlparse.unquote(url)
            url = str(url).replace("\\/", "/")
            itemlist.append(item.clone(action="play", title="%s", language=lang, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
