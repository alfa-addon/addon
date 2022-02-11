# -*- coding: utf-8 -*-
# -*- Channel Danimados -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
import base64
import re
PY3 = False

if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int

from channels import filtertools
from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger
from channelselector import get_thumb
from lib.AlfaChannelHelper import CustomChannel

IDIOMAS = {'la': 'LAT', 'sub': 'VOSE'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['fembed', 'mega', 'yourupload', 'streamsb', 'mp4upload', 'mixdrop', 'uqload']
list_quality = []

canonical = {
             'channel': 'danimados', 
             'host': config.get_setting("current_host", 'danimados', default=''), 
             'host_alt': ["https://www.d-animados.com/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = CustomChannel(host, tv_path="/series", canonical=canonical)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host + "series",
                         thumbnail=get_thumb("last", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series Animadas", action="list_all", url=host + "series/?type=TV+Show",
                         thumbnail=get_thumb("tvshows", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Anime", action="list_all", url=host + "series/?type=Anime",
                         thumbnail=get_thumb("anime", auto=True)))

    # itemlist.append(Item(channel=item.channel, title="Doramas", action="sub_menu", url=host + "doramas?categoria=dorama",
    #                      thumbnail=get_thumb("doramas", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all", url=host + "series/?type=Movie",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="alpha",
                         url=host + "lista-de-la-a-a-la-z/", thumbnail=get_thumb("alphabet", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url)
    matches = soup.find_all("article")

    for elem in matches:
        url = elem.a["href"]
        title = elem.a["title"]
        thumb = elem.img["src"]
        c_type = elem.find("div", class_="typez").text

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, action="seasons", c_type=c_type,
                        infoLabels={"year": "-"})

        if c_type != "Movie":
            new_item.contentSerieName = title
        else:
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        item.url = re.sub("\?|\&|page=\d+|type=\w+", "", item.url)
        next_page = soup.find("a", class_="r")["href"]
        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=item.url + next_page,
                                 action='list_all'))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()
    base_url = host + "series"
    soup = AlfaChannel.create_soup(base_url)
    filters = soup.find_all("ul", class_="dropdown-menu")
    if item.title == "Generos":
        base_url += "?genre[]=%s"
        filter_id = 0

    matches = filters[filter_id].find_all("input")

    for elem in matches:
        title = elem["value"].capitalize()
        url = base_url % elem["value"]

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all"))

    return itemlist

def alpha(item):

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url).find("div", class_="lista")

    matches = soup.find_all("a")

    for elem in matches:
        url = elem["href"]
        title = elem.text.capitalize()
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all"))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    if item.c_type == "Movie":
        return episodesxseason(item)
    soup = AlfaChannel.create_soup(item.url)
    matches = soup.find("div", class_="eplister").find_all("div", class_="epl-num")
    season_list = list()
    infoLabels = item.infoLabels

    for elem in matches:
        if item.c_type == "TV Show":
            season_number = elem.text[0]
            if season_number in season_list:
                continue
            season_list.append(season_number)
        else:
            season_number = 1

        title = "Temporada %s" % season_number
        infoLabels["season"] = season_number
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseason",
                             infoLabels=infoLabels, c_type=item.c_type))
        if item.c_type != "TV Show":
            break

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    itemlist = itemlist[::-1]

    itemlist = AlfaChannel.add_serie_to_videolibrary(item, itemlist)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url)
    matches = soup.find("div", class_="eplister").find_all("li")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in matches:

        title_name = elem.find("div", class_="epl-title").text

        if item.c_type != "Movie":
            epi_data = re.split(r"\D+", elem.find("div", class_="epl-num").text)
            if len(epi_data) > 1:
                if int(epi_data[0]) != season:
                    continue
            else:
                epi_data.insert(0, "1")
            if len(epi_data) > 1:
                epi_num = epi_data[1]
            else:
                epi_num = epi_data[0]
            title = "%sx%s - %s" % (season, epi_num, title_name)
            infoLabels["episode"] = epi_num
        else:
            title = title_name

        url = elem.a["href"]
        lang = elem.find("div", class_="epl-sub").text.lower()
        if "latino" in lang:
            lang = "la"
        else:
            lang = "sub"
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             language=IDIOMAS.get(lang, "VOSE"), infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if item.c_type == "Movie":
        return findvideos(itemlist[0])
    else:
        return itemlist[::-1]


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url)
    matches = soup.find("select", class_="mirror").find_all("option", {"data-index": True})
    for elem in matches:

        enc = elem.get("value", "")
        url = BeautifulSoup(base64.b64decode(enc).decode("utf-8")).iframe["src"]
        itemlist.append(Item(channel=item.channel, title="%s", url=url, action="play", language=item.language,
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    if "monoschinos" in item.url:
        data = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(data, "file: '([^']+)'")

        itemlist.append(item.clone(url=url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)
    else:
        itemlist.append(item)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
