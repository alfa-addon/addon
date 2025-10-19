# -*- coding: utf-8 -*-
# -*- Channel pelis182 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-

import re
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from modules import autoplay

list_language = ["LAT"]

list_quality = []

list_servers = ['lauchacohete']

canonical = {
             'channel': 'pelis182', 
             'host': config.get_setting("current_host", 'pelis182', default=''), 
             'host_alt': ["https://www.pelis182.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Películas', url=host, action='list_all',
                         thumbnail=get_thumb('movies', auto=True)))
        
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'category/series/', action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Categorias', url=host, action='categories',
                         thumbnail=get_thumb('categories', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def categories(item):
    logger.info()
    
    itemlist = list()
    
    try:
        soup = create_soup(item.url)
        id_regex = re.compile(r"^menu-item-\d+")
        matches = soup.find_all("li", id=id_regex)
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist

    for elem in matches:
        name = elem.a.getText(strip=True)
        url = elem.a["href"]
        itemlist.append(item.clone(title=name, url=url, action="list_all"))
    
    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    try:
        soup = create_soup(item.url)
        matches = soup.find_all("article")
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist

    for elem in matches:
        url = elem.a["href"]
        title = elem.a["title"].strip()
        title = re.sub(r'\s+\(.*?\)\s*$', '', title)
        season_pattern = r'(?i)\s+–\s+Temporada\s+(\d+)'
        season = scrapertools.find_single_match(title, season_pattern)
        c_type = "tvshow" if season else "movie"
        thumbnail = elem.find("img")["src"]
        
        new_item = Item(channel=item.channel,
                        thumbnail=thumbnail,
                        title=title,
                        url=url)
        
        if c_type == "movie":
            new_item.infoLabels={"year": '-'}
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = "movie"
            new_item.url = findframe(url)
        elif c_type == "tvshow":
            title = re.sub(season_pattern, '', title)
            new_item.title = title
            new_item.contentSerieName = title
            new_item.contentSeason = season
            new_item.action = "episodios"
            new_item.contentType = "tvshow"
        
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    # Paginación
    try:
        pagination = soup.find("div", class_="nav-links")
        if pagination:
            title = ">> {0}".format(config.get_localized_string(30992))
            pages = pagination.find_all(class_="page-numbers")
            if pages:
                next = pagination.find(class_="next")
                total = pages[-2].text if next else pages[-1].text
                current = pagination.find(class_="current").text
                title = "{0} {1}/{2}".format(title, current, total)
                if int(current) == int(total):
                    return itemlist
                new_item = Item(channel=item.channel,
                                title=title,
                                url=next["href"],
                                thumbnail=get_thumb("next.png"),
                                action='list_all')
            
                itemlist.append(new_item)
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()

    try:
        soup = create_soup(item.url)
        matches = soup.find_all("div", class_="tab_content")
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    if not matches:
        return itemlist

    for index, elem in enumerate(matches):
        infoLabels = item.infoLabels or {}
        infoLabels["mediatype"] = "episode"
        infoLabels["season"] = item.contentSeason
        #tab-1-t5x2
        patern = r'(?i)tab-(\d+)-t(\d+)x(\d+)'
        res = re.search(patern, elem['id'], flags=re.DOTALL)
        if res:
            episode = res.group(3)
        else:
            episode = index + 1
        infoLabels["episode"] = episode

        itemlist.append(
            item.clone(
                action = "findvideos",
                infoLabels = infoLabels,
                title = "Episodio {}".format(episode),
                url = elem.find("iframe")["src"],
                contentType = 'episode',
                contentEpisodeNumber = infoLabels["episode"]
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(60352),
                             url=item.url, action="add_serie_to_library", extra="episodios",
                             contentSerieName=item.contentSerieName))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, server="lauchacohete", title='%s', 
                         action='play', url=item.url,
                         language="LAT", infoLabels=item.infoLabels))
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 \
        and item.extra != 'findvideos' and item.contentType == "movie":
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(70146),
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


def findframe(url):
    logger.info()

    try:
        soup = create_soup(url, referer=host)
        match = soup.find("div", class_="video-responsive").find("iframe")
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(url), str(e)))
        return ''
    
    if not match or not match.get("src", ""):
        return ''
    
    return match["src"]