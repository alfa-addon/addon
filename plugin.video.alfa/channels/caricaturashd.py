# -*- coding: utf-8 -*-
# -*- Channel CaricaturasHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


IDIOMAS = {"latino": "LAT", "castellano": "CAST", "sub": "VOSE"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'doodstream',
    'upstream'
    ]

host = 'https://caricaturashd.net/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'ultimas-caricaturas/', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Peliculas', url=host + 'ultimas-peliculas/', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))


    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=item.url, action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True), url=item.url))

    return itemlist


def create_soup(url, post=None, unescape=False):
    logger.info()

    if post:
        data = httptools.downloadpage(url, post=post, add_referer=True).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host).find("ul", class_="menu")
    if item.title == "Generos":
        matches = soup.find("ul",  class_="sub-menu")

    for elem in matches.find_all("li"):
        title = elem.a.text
        url = elem.a["href"]
        if "peliculas" in item.url:
             url += "?type=movies"
        else:
            url += "?type=series"
        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url, genre=True))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    if item.search or item.genre:
        matches = soup.find("div", id="movies-a").find_all("article")
    else:
        matches = soup.find("section", class_="episodes").find_all("article")


    for elem in matches:

        url = elem.a["href"]
        thumb = "https:" + elem.find("img")["src"]
        title = elem.h2.text
        mode = elem.find("span", class_="watch").text

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": "-"})

        if "caricatura" in mode.lower():
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("a", text="NEXT")["href"]
    except:
        return itemlist

    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("section", class_="section episodes")

    matches = soup.find("ul", class_="aa-cnt sub-menu").find_all("li")

    infoLabels = item.infoLabels
    id = soup.find("div", id="res-ep")["data-object"]

    for elem in matches:
        season = elem.a["data-season"]
        post_id = elem.a["data-post"]

        title = elem.a.text
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons', post_id=post_id,
                             id=id, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()

    infoLabels = item.infoLabels
    base_url = "%swp-admin/admin-ajax.php" % host
    season = infoLabels["season"]

    post = {"action": "action_select_season", "season": season, "post": item.post_id, "object": item.id}
    soup = create_soup(base_url, post=post)

    matches = soup.find_all("article")

    for elem in matches:
        epi_name = elem.h2.text
        epi_num = scrapertools.find_single_match(elem.find("span", class_="year").text, "x(\d+)")
        title = "%sx%s - %s" % (season, epi_num, epi_name)
        url = elem.a["href"]
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist[::-1]


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="choose-options aa-drp").find_all("a")

    if not matches:
        return itemlist

    for elem in matches:
        lang = elem.find("span", class_="option").text.split(" - ")[1]
        opt = elem["href"][1:]
        enc_url = soup.find("div", id=opt)
        if enc_url.iframe.has_attr("data-src"):
            if host in enc_url.iframe["data-src"]:
                url = create_soup(enc_url.iframe["data-src"]).find("div", class_="Video").iframe["src"]
            elif "IFRAME SRC" in enc_url.iframe["data-src"]:
                url = scrapertools.find_single_match(enc_url.iframe["data-src"], 'IFRAME SRC="([^"]+)"')
        else:
            if host in enc_url.iframe["src"]:
                url = create_soup(enc_url.iframe["src"]).find("div", class_="Video").iframe["src"]
            else:
                url = enc_url.iframe["src"]

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
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.search=True
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
            item.url = host + 'ultimas-peliculas'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
