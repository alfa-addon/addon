# -*- coding: utf-8 -*-
# -*- Channel EntrePeliculasySeries -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb, jsontools
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools
from bs4 import BeautifulSoup

host = 'https://entrepeliculasyseries.io/'

IDIOMAS = {"latino": "LAT", "castellano": "CAST", "subtitulado": "VOSE"}
list_language = list(set(IDIOMAS.values()))
list_quality = []
list_servers = ['mega', 'fembed', 'vidtodo', 'gvideo']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Peliculas",  action="sub_menu",
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu",
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    if item.title == "Peliculas":
        mode = "movie"
        itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'peliculas',
                             thumbnail=get_thumb('all', auto=True)))
    else:
        mode = "tv"
        itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host + 'series-recientes',
                             thumbnail=get_thumb('last', auto=True)))

        itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'series',
                             thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="genres", section='genre', mode=mode,
                         thumbnail=get_thumb('genres', auto=True)))
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup



def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("ul", class_="list-movie").find_all("li", class_="item")

    for elem in matches:
        url = elem.a["href"]
        title = elem.h2.text
        year = scrapertools.find_single_match(elem.h4.text, "(\d{4})")
        thumb = elem.a.img["src"]


        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={'year': year})

        if "/serie" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("a", class_="nextpostslink")["href"]

        if url_next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                                 section=item.section))
    except:
        pass

    return itemlist


def genres(item):
    logger.info()
    itemlist = list()

    action = 'list_all'
    soup = create_soup(host).find("nav", class_="Menu").find("li", class_=re.compile("AAIco-%s menu-category" % item.mode))

    matches = soup.find("ul", class_="sub-menu").find_all("li")
    for elem in matches:
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title, url=url, action=action, section=item.section))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="select-season").find_all("option")
    infoLabels = item.infoLabels

    for elem in matches:
        season = elem["value"]
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName
                             ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()
    season = item.infoLabels["season"]
    soup = create_soup(item.url).find("ul", id="season-%s" % season)
    matches = soup.find_all("article")
    infoLabels = item.infoLabels

    for elem in matches:
        url = elem.a["href"]
        episode = scrapertools.find_single_match(elem.h2.text, "\d+x(\d+)")
        title = "%sx%s" % (infoLabels["season"], episode)
        infoLabels["episode"] = episode

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    matches = soup.find_all("div", class_=re.compile(r"option-lang"))

    for elem in matches:
        lang = elem.h3.text.lower().strip()

        if lang == "descargar":
            continue

        for opt in elem.find_all("li", class_="option"):
            server = opt.text.lower().strip()
            url = opt["data-link"]

            itemlist.append(Item(channel=item.channel, title=server.capitalize(), url=url, server=server, action="play",
                                 language=IDIOMAS.get(lang, 'LAT'), infoLabels=item.infoLabels))

    itemlist = sorted(itemlist, key=lambda it: it.language)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url, action="add_pelicula_to_library", extra="findvideos",
                     contentTitle=item.contentTitle))

    return itemlist


def search_results(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("li", class_="xxx TPostMv")

    for elem in matches:
        url = elem.a["href"]
        title = elem.h2.text
        thumb = elem.img["data-src"]
        year = "-"
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if "/serie" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def search(item, texto):
    logger.info()

    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto

        if texto != '':
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys

        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'ver-peliculas-online'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas-de-animacion'
        elif categoria == 'terror':
            item.url = host + 'peliculas-de-terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def play(item):
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'window.location="([^"]+)"')
    if not url.startswith("http"):
        url = "https:" + url
    item.server = ""
    itemlist.append(item.clone(url=url))

    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist

