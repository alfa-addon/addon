# -*- coding: utf-8 -*-
# -*- Channel CinemaT4 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


list_language = ["LAT"]
list_quality = []
list_servers = ['amazon', 'gvideo', 'mega', 'mediafire']

host = "http://www.cinemat4.org/"


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Todas", url=host + 'pelicula', action="list_all",
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Años", action="section",
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", url=host + '?s=', action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

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
    matches = soup.find("div", class_="content")
    for elem in matches.find_all("article"):

        info_1 = elem.find("div", class_="poster")
        info_2 = elem.find("div", class_="data")

        thumb = info_1.img["src"]
        title = info_1.img["alt"]
        title = re.sub(r" \(.*", "", title)
        url = info_1.a["href"]
        try:
            year = info_2.find("span", text=re.compile(r"\d{4}")).text.split(",")[-1]
        except:
            pass
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             thumbnail=thumb, contentTitle=title, infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    try:
        next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host)

    if item.title == "Generos":
        matches = soup.find("ul", class_="sub-menu")
    elif item.title == "Años":
        matches = soup.find("ul", class_="releases")

    if not matches: return itemlist

    for elem in matches.find_all("li"):
        title = elem.a.text
        url = elem.a["href"]
        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", id="playeroptions")
    if not matches:
        return itemlist

    for elem in matches.find_all("li"):
        if not elem["data-nume"].isdigit():
            continue
        post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"]}
        headers = {"Referer": item.url}
        doo_url = "%swp-admin/admin-ajax.php" % host
        data = httptools.downloadpage(doo_url, post=post, headers=headers).data
        if not data:
            continue
        player_url = BeautifulSoup(data, "html5lib").find("iframe")["src"]
        if "https://api.cinemat4.org" in player_url:
            players = httptools.downloadpage(player_url).data
            infoplayers = jsontools.load(scrapertools.find_single_match(players, "infoPlayers = ([^;]+);"))

            for v_data in infoplayers["dub"]:
                url = v_data[1]

                if "amazon" in url:
                    sh = scrapertools.find_single_match(httptools.downloadpage(url).data, 'var shareId = "([^"]+)"')
                    url = "https://www.amazon.com/drive/v1/shares/%s?resourceVersion=V2&ContentType=JSON&asset=ALL" % sh

                itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                                     language="LAT", infoLabels=item.infoLabels))
        else:
            itemlist.append(Item(channel=item.channel, title='%s', action='play', url=player_url,
                                 language="LAT", infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search_results(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    for elem in soup.find_all("div", class_="result-item"):
        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.img["alt"]
        title = re.sub(r" \(.*", "", title)
        year = elem.find("span", class_="year").text

        itemlist.append(Item(channel=item.channel, title=title, contentTitle=title, url=url, thumbnail=thumb,
                             action='findvideos', infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
