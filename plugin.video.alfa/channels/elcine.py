# -*- coding: utf-8 -*-
# -*- Channel elCine -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import scrapertools
from core import servertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


IDIOMAS = {'latino': 'LAT', 'castellano': 'CAST', 'subtitulada': 'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'doodstream',
    'evoload'
    ]

host = 'https://elcine.online/'


def mainlist(item):

    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Todas', url=host, action='list_all',
                    thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + 'buscar-pelicula/',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def section(item):
    logger.info()

    itemlist = list()
    soup = create_soup(host)

    if item.title == "Generos":
        matches = soup.find_all("a", class_="dropdown-item", href=re.compile("/genero/"))
    if item.title == "Por Año":
        matches = soup.find_all("a", class_="dropdown-item", href=re.compile("/peliculas-del-"))
    for elem in matches:
        title = elem.text

        url = host + elem["href"]
        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="video-block section-padding").find_all("div", class_="video-card")

    for elem in matches:

        lang = elem.find("div", class_="lenguaje").text.lower()
        info = elem.find("div", class_="video-title").a
        title, year = scrapertools.find_single_match(info.text, "([^/(]+) \((\d{4})\)")
        url = host + info["href"]
        thumb = elem.find("img", class_="img-fluid")["data-src"]

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, language=IDIOMAS.get(lang, "VOSE"),
                        infoLabels={"year": year})

        if "serie/" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = host + soup.find("a", class_="page-link", title="Next page")["href"]
    except:
        return itemlist

    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    # srv_list = {"fembed": "fembed", "playstp": "streamtape", "stream": "mystream", "goplay": "gounlimited",
    #             "drive": "gvideo", "meplay": "netutv", "evoplay": "netutv", "uqload": "uqload"}
    #
    soup = create_soup(item.url)

    matches = soup.find("div", class_="float-left").find_all("a", class_="dropdown-item")

    if not matches:
        return itemlist

    for elem in matches:
        url = scrapertools.find_single_match(elem["onclick"], "setURL\('([^']+)'\)")
        if "player.123movies" in url:
            continue

        lang = elem.text.split(" - ")[1]

        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                        language=IDIOMAS.get(lang.lower(), "VOSE"), infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist)

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
        texto = texto.replace(" ", "%20")
        item.url = item.url + texto + "/1"

        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'genero/animaci%C3%B3n/1'
        elif categoria == 'terror':
            item.url = host + 'genero/terror/1'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
