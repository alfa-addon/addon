# -*- coding: utf-8 -*-
# -*- Channel DoramasMP4 -*-
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
from lib import jsunpack
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


IDIOMAS = {'sub': 'VOSE', 'VO': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['viwol', 'voe', 'mixdrop', 'doodstream']

canonical = {
             'channel': 'doramasmp4', 
             'host': config.get_setting("current_host", 'doramasmp4', default=''), 
             'host_alt': ["https://www35.doramasmp4.com/"], 
             'host_black_list': ["https://www34.doramasmp4.com/"], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Destacadas", action="list_all",
                         url=host,
                         thumbnail=get_thumb('hot', auto=True), pos=2))

    itemlist.append(Item(channel=item.channel, title="Ultimos", action="list_all",
                         url=host,
                         thumbnail=get_thumb('last', auto=True), pos=3))

    itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="list_all",
                         url=host, thumbnail=get_thumb('new episodes', auto=True), pos=1))

    itemlist.append(Item(channel=item.channel, title="Variedades", action="list_all",
                         url=host,
                         thumbnail='', pos=5))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         url=host,
                         thumbnail=get_thumb('movies', auto=True), pos=4))

    itemlist.append(Item(channel=item.channel, title='Buscar...', action="search", url=host + 'api/web/autocomplete/titles',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


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


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id="content")
    matches = soup.find_all("div", class_="swiper-container")[item.pos].find_all("div", class_="swiper-slide")

    for elem in matches:
        url = elem.a["href"]
        title = elem.find("div", class_="card-title").text.strip()
        year = elem.find("div", class_="card-subtitle").text.strip()
        if item.pos == 1:
            content_title = title
            title = "%s - %s" % (title, year)
        thumb = elem.img["src"]

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if item.pos != 4:

            if item.pos == 1:
                new_item.contentSerieName = content_title
                new_item.action = "findvideos"
            else:
                new_item.contentSerieName = title
                new_item.action = "episodios"
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div",itemprop="episode")

    matches = soup.find_all("div", class_="_episode")

    infoLabels = item.infoLabels

    for elem in matches:
        url = elem.a["href"]
        epi_num = elem["data-number"]
        infoLabels["season"] = 1
        infoLabels["episode"] = epi_num
        title = "1x%s - Episodio %s" % (epi_num, epi_num)

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    infoLabels = item.infoLabels

    data = httptools.downloadpage(item.url, canonical=canonical).data
    media_data = jsontools.load(scrapertools.find_single_match(data, 'var links =([^;]+)'))

    for media in media_data["online"]:
        if media["subtitle"]["value"] == "es":
            lang = "VOSE"
        else:
            lang = "VO"
        srv = media["server"]["name"].lower()
        url = media["link"].replace("/link/", "/redirect/")

        if srv == "veo":
            srv = "voe"
        if url:
            new_item = Item(channel=item.channel, title=srv, url=url, server=srv,
                            action='play', language=lang, infoLabels=infoLabels)

            itemlist.append(new_item)

    #itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()

    url = httptools.downloadpage(item.url, add_referer=True).url

    item.url = url

    return [item]


def search_results(item):
    logger.info()

    itemlist = list()

    post = {"search": item.text, "limit": 30}
    results = httptools.downloadpage(item.url, post=post, canonical=canonical).json
    for elem in results:
        url = host + elem["slug"]
        title = elem["title"]
        thumb = "https://cdn.doramasmp4.com/storage/resize/posters/350x500@" + elem["poster"]

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb)

        if elem["type"] != "movie":
            new_item.contentSerieName = title
            new_item.action = "episodios"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.text = texto
        if texto != '':
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
