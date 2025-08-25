# -*- coding: utf-8 -*-
# -*- Channel Yandispoiler -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-

import re
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core.jsontools import json
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from modules import filtertools
from modules import autoplay


IDIOMAS = {'sub': 'VOSE', "mx": "LAT", "es": "CAST"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'filemoon',
    'voe',
    'vidguard'
    ]

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'yandispoiler', 
             'host': config.get_setting("current_host", 'yandispoiler', default=''), 
             'host_alt': ["https://yandispoiler.net/"], 
             'host_black_list': [],
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1,
             'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': True, 'cf_assistant_if_proxy': True, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]

TIMEOUT = 30


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
        
    itemlist.append(Item(channel=item.channel, title='Nuevos Capítulos', url=host + 'episodios/', action='list_all',
                         thumbnail=get_thumb('new episodes', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series/', action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Películas', url=host + 'peliculas/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Latino', url=host + 'audios/latino/', action='list_all',
                         thumbnail=get_thumb('latino', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Castellano', url=host + 'audios/castellano/', action='list_all',
                         thumbnail=get_thumb('cast', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Subtitulado', url=host + 'audios/sub-espanol/', action='list_all',
                         thumbnail=get_thumb('vose', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, timeout=TIMEOUT, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=TIMEOUT, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def list_all(item):
    logger.info()

    itemlist = list()

    try:
        soup = create_soup(item.url)
        container = soup.find_all("div", class_="module-wrapper")
        container = container[-1] if container else soup.find("div", class_="page-body")
        matches = container.find_all("div", class_="item-box")
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist

    for elem in matches:
        url = elem.a["href"]
        title = elem.find("h3").getText(strip=True)
        c_type = elem.a["data-ptype"]  # movies, tvshows o episodes
        thumbnail = elem.img["src"]
        
        new_item = Item(channel=item.channel,
                        thumbnail=thumbnail,
                        title=title,
                        url=url)
        
        if c_type == "movies":
            new_item.infoLabels={"year": '-'}
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = "movie"
        elif c_type == "tvshows":
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.contentType = "tvshow"
        elif c_type == "episodes":
            new_item.contentSerieName = title
            new_item.action = "findvideos"
            new_item.contentType = "episode"
            #S1 EP11
            sxe = elem.select_one('span.season-desc')
            if sxe:
                episode_data = re.search(r'S(\d+)\s*EP(\d+)', sxe.text, flags=re.DOTALL)
                season, episode = (episode_data.group(1), episode_data.group(2)) if episode_data else (1, 1)
                season, episode = (int(season), int(episode))
            else:
                season, episode = (1, 1)
            new_item.contentSeason = season
            new_item.contentEpisodeNumber = episode
            # new_item.infoLabels={"season": season, "episode": episode}
            new_item.title = "{}x{} {}".format(season, episode, new_item.contentSerieName)
        else:
            continue
        
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    # Paginación
    try:
        pagination = soup.find("div", class_="pagination")
        if pagination:
            title = ">> {0}".format(config.get_localized_string(30992))
            total = pagination.find("span", class_="total").text  # "Página 1 de 11"
            match = re.search("Página\s+(\d+)\s+de\s+(\d+)", total, flags=re.DOTALL)
            if match:
                current = match.group(1)   # "1"
                total = match.group(2)   # "11"
                title = "{0} {1}/{2}".format(title, current, total)
                if int(current) == int(total):
                    return itemlist
            
            url = pagination.find_all("a")[-1]["href"]

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=get_thumb("next.png"),
                            action='list_all')
            
            itemlist.append(new_item)
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    return itemlist


def seasons(item):
    logger.info()
    
    itemlist = list()

    try:
        soup = create_soup(item.url)
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist

    for elem in soup.find_all("ul", class_="episodes-list"):
        season = scrapertools.find_single_match(elem["id"], r"season-listep-(\d+)")
        itemlist.append(
            item.clone(
                action = "episodesxseasons",
                contentType = 'season',
                contentSeason = int(season), 
                title = "Temporada %s" % season
            )
        )

    if len(itemlist) == 1:
        return episodesxseasons(itemlist[0])
    
    tmdb.set_infoLabels_itemlist(itemlist)

    itemlist = sorted(itemlist, key=lambda i: i.contentSeason)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                text_color = 'yellow',
                title = 'Añadir esta serie a la videoteca',
                url = item.url
            )
        )

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    templist = seasons(item)

    if config.get_videolibrary_support() and len(templist) > 0:
        templist = templist[:-1]
    
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()

    try:
        soup = create_soup(item.url)
        container = soup.find("ul", id="season-listep-{}".format(item.contentSeason))
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    if not container:
        return itemlist

    for index, elem in enumerate(container.find_all("li")):
        infoLabels = item.infoLabels or {}
        infoLabels["mediatype"] = "episode"
        infoLabels["season"] = item.contentSeason  
        thumb = elem.find("img")
        thumb = thumb["src"] if thumb else item.thumbnail
        title = elem.find("span", class_="ep-title")
        title = title.getText(strip=True) if title else "Episodio {}".format(index + 1)
        episode = title.split(" ")[-1]
        
        try:
            infoLabels["episode"] = int(episode)
        except ValueError:
            infoLabels["episode"] = index + 1

        itemlist.append(
            item.clone(
                action = "findvideos",
                infoLabels = infoLabels,
                title = title,
                thumbnail = thumb,
                url = elem.a["href"],
                contentType = 'episode',
                contentEpisodeNumber = infoLabels["episode"]
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = sorted(itemlist, key=lambda i: i.contentEpisodeNumber)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    
    soup = create_soup(item.url)

    for elem in soup.find_all("li", id=re.compile(r"player-option-\d+")):

        # logger.error(str(elem))
        post = {"action": "zeta_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
                "type": elem["data-type"]}
        headers = {"Referer": item.url}
        doo_url = "%swp-admin/admin-ajax.php" % host

        response = httptools.downloadpage(doo_url, timeout=TIMEOUT, post=post, 
                                          headers=headers, canonical=canonical, 
                                          hide_infobox=True)
        if response.code != 200:
            continue

        data_json = json.loads(response.data)
        
        if data_json.get('type', '') != "iframe":
            continue
        
        embed_url = data_json.get('embed_url', '')
                        
        iframe = BeautifulSoup(embed_url, "html5lib", from_encoding="utf-8")
        
        url = iframe.iframe["src"]
        
        lang = "VOSE"
        
        try:
            lang_icon_src = elem.find("span", class_="flag").img["src"]
            lang = extract_lang_from_url(lang_icon_src)
        except Exception as e:
            logger.error(str(e))
        
        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                                language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    
    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools
    itemlist = [i for i in itemlist if i.title != "Directo"]

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    
    try:
        if texto != '':
            texto = str(texto).replace(" ", "+")
            item.url = "{0}?s={1}".format(host, texto)
            item.c_type = "search"
            return list_all(item)
        else:
            return []
    except Exception as e:
        logger.error(str(e))
        return []


def newest(categoria):
    logger.info()

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = canonical['channel']

    try:
        if categoria in ['series']:
            item.url = host + 'episodios/'
            itemlist = list_all(item)

        if len(itemlist) > 0 and ">> {0}".format(config.get_localized_string(30992)) in itemlist[-1].title:
            itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except Exception as e:
        logger.error(str(e))
        return []

    return itemlist


def extract_lang_from_url(lang_flag_url):
    return scrapertools.find_single_match(lang_flag_url, "flags/((?:.+))\.png")