# -*- coding: utf-8 -*-
# -*- Channel DeTodoPeliculas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-

import re
import base64
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


IDIOMAS = {'sub': 'VOSE', "lat": "LAT", "cas": "CAST", "LAT": "LAT"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'filemoon',
    'voe',
    'vidguard'
    ]

forced_proxy_opt = 'ProxyCF'

canonical = {
             'channel': 'detodopeliculas', 
             'host': config.get_setting("current_host", 'detodopeliculas', default=''), 
             'host_alt': ["https://detodopeliculas.nu/"], 
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

    itemlist.append(Item(channel=item.channel, title='Generos', url=host, action='section',
                         thumbnail=get_thumb('genres', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Estrenos', url=host + 'peliculas-de-estreno/', action='list_all',
                         thumbnail=get_thumb('premieres', auto=True)))
        
    itemlist.append(Item(channel=item.channel, title='Novedades', url=host + 'novedades/', action='list_all',
                         thumbnail=get_thumb('newest', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Recomendadas', url=host + 'peliculas-recomendadas/', action='list_all',
                         thumbnail=get_thumb('recomended', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    if item.title == "Generos":
        matches = soup.find("li",  id="menu-item-228")

    for elem in matches.find_all("li"):
        itemlist.append(Item(channel=item.channel, title=elem.a.text, action="list_all", url=elem.a['href']))

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
    
    is_search = bool(item.c_type == "search")

    try:
        soup = create_soup(item.url)
        if is_search:
            matches = soup.find("div", class_="content").find_all("article")
        else:
            matches = soup.find("div", class_="content").find_all("article", id=re.compile(r"^post-\d+"))
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist

    for elem in matches:
        if is_search:
            data = elem.find("div", class_="title").a
            data_lang = elem.find_all("span", class_="flag")
        else:
            data = elem.find("div", class_="data").h3.a
            data_lang = elem.find_all("img", class_="banderas")

        url = data["href"]
        full_title = data.text
        year, title = clean_title(full_title)

        languages = set()
        try:
            for language in data_lang:
                lang = extract_lang_from_url(language['style']) if is_search else language['alt']
                languages.add(IDIOMAS.get(lang, "VOSE"))
        except Exception as e:
            logger.error(str(e))

        try:
            if is_search:
                thumbnail = elem.find("div", class_="thumbnail").a.img["src"]
            else:
                thumbnail = elem.find("div", class_="poster").img["data-lazy-src"]
        except Exception as e:
            thumbnail = ""
            logger.error(str(e))

        new_item = Item(channel=item.channel,
                        thumbnail=thumbnail,
                        title=title,
                        url=url,
                        infoLabels={"year": year},
                        language = list(languages),
                        contentTitle = title,
                        action = "findvideos",
                        contentType = 'movie')
        
        new_item.context = filtertools.context(item, list_language, list_quality)
        
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    # Paginación
    try:
        pagination = soup.find("div", class_="resppages")
        if pagination:
            title = ">> {0}".format(config.get_localized_string(30992))
            
            pages = soup.find("div", class_="pagination").span # Página 1 de 11
            if pages:
                match = re.search("Página\s+(\d+)\s+de\s+(\d+)", pages.text, flags=re.DOTALL)
                if match:
                    current = match.group(1)   # "1"
                    total = match.group(2)   # "11"
                    title = "{0} {1}/{2}".format(title, current, total)
            
            url = pagination.find_all("a")[-1]["href"]
                        
            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=get_thumb("next.png"),
                            action='list_all')
            
            if is_search:
                new_item.c_type = "search"
            
            itemlist.append(new_item)
    except Exception as e:
        logger.error("URL: {0}\nError: {1}".format(str(item.url), str(e)))
        return itemlist
    
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    
    soup = create_soup(item.url)

    for elem in soup.find_all("li", class_="dooplay_player_option"):

        # logger.error(str(elem))
        post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
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
        embed_player_url = 'https://detodopeliculas.nu/player/?id='

        if not str(embed_url).startswith(embed_player_url):
            continue
        
        encoded_url = str(embed_url).replace(embed_player_url, '')
        
        url = base64.b64decode(encoded_url).decode('utf-8')
        
        lang = "VOSE"
        
        try:
            lang_icon_src = elem.find("span", class_="flag").img["data-lazy-src"]
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
    try:
        if categoria in ['peliculas']:
            item = Item()
            item.c_type = 'peliculas'
            item.url = "{0}peliculas-de-estreno/".format(host)
            itemlist = list_all(item)
            if len(itemlist) > 0 and '>>' in itemlist[-1].title:
                itemlist.pop()
            return itemlist
        else:
            return []
    except Exception as e:
        logger.error(str(e))
        return []


def clean_title(title):
    match = re.search("\s+\(((?:19|20)[\d+]{2})\)$", title, flags=re.DOTALL)
    if match:
        full_match = match.group(0)  # " (1998)"
        year = match.group(1)   # "1998"
        title = title[:-len(full_match)]
    else:
        year = '-'
    return year, title


def extract_lang_from_url(lang_flag_url):
    return scrapertools.find_single_match(lang_flag_url, "flags/((?:.+))\.png")