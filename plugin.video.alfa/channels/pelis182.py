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
             'host_alt': ["https://pelis182.net/"], 
             'host_black_list': ["https://pelis182.com/", "https://www.pelis182.com/"], 
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
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title='Películas', url=host +"?p182_catalog=movies&catalog_page=1", action='list_all',
                         thumbnail=get_thumb('movies', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'category/series/', action='list_all', c_type = "tvshow",
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
        matches = soup.find('div', class_='genre-menu__panel').find_all("a")
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    for elem in matches:
        name = elem.getText(strip=True)
        url = elem["href"]
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
        season = ""
        url = elem.a["href"]
        title = elem.h3.text.strip()
        match = elem.find("div", class_='p182-card__meta').span
        if match:
            year = match.text.strip()
        else:
            year = "-"
        title = re.sub(r'\s+\(.*?\)\s*$', '', title)
        season_pattern = r'(?i)\s+–\s+Temporada\s+(\d+)'
        season = scrapertools.find_single_match(title, season_pattern)
        if item.c_type and item.c_type != 'search': 
            c_type = item.c_type
        else:
            c_type = "tvshow" if season else "movie"
        thumbnail = elem.find("div", class_='p182-card__image')["style"]
        
        new_item = Item(channel=item.channel,
                        thumbnail=thumbnail,
                        title=title,
                        url=url,
                        infoLabels={"year": year})
        
        if c_type == "movie":
            new_item.infoLabels={"year": year}
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = "movie"
        elif c_type == "tvshow":
            new_item.infoLabels={"year": "-"}
            name = re.sub(season_pattern, '', title)
            new_item.title = title
            new_item.contentSerieName = name
            new_item.contentSeason = season
            new_item.action = "episodios"
            new_item.contentType = "tvshow"
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        itemlist.append(item.clone(action="list_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = list()
    
    try:
        soup = create_soup(item.url)
        # matches = soup.find_all("div", class_="tab_content")
        matches = soup.find_all("button", class_="server-button")
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
        # patern = r'(?i)tab-(\d+)-t(\d+)x(\d+)'
        patern = r'(?i)t(\d+)x(\d+)'
        res = re.search(patern, elem.text, flags=re.DOTALL)
        if res:
            episode = res.group(2)
        else:
            episode = index + 1
            
        infoLabels["episode"] = episode
        
        url = elem["data-iframe"]
        url = scrapertools.find_single_match(url, 'src="([^"]+)"')
        
        itemlist.append(
            item.clone(
                action = "findvideos",
                infoLabels = infoLabels,
                title = "Episodio {}".format(episode),
                url = url,
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
    
    soup = create_soup(item.url)
    url = soup.iframe['src']
    
    itemlist.append(Item(channel=item.channel, server="lauchacohete", title='%s', 
                         action='play', url=url,
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