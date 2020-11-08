# -*- coding: utf-8 -*-
# -*- Channel CinemaHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core import servertools
from core.item import Item
from core import scrapertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


host = 'https://www.pelisplus24.xyz/'

IDIOMAS = {'mx': 'LAT', 'es': "CAST", "en": "VOSE", "jp": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality = list()
list_servers = ['vidia', 'upstream', 'vidtodo', 'clipwatching', 'mixdrop', 'mystream']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'peliculas-online/estrenos',
                         action='list_all', thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'ver-pelicula-online', action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
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


def get_language(lang_data):
    logger.info()

    language = list()

    lang_list = lang_data.find_all("span", class_="flag")
    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["style"], r'/flags/(.*?).png\)')
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    return language


def section(item):
    logger.info()

    itemlist = list()
    base_url = "%s%s" % (host, "ver-pelicula-online")
    soup = create_soup(base_url)

    if item.title == "Generos":
        matches = soup.find("ul", class_="genres falsescroll")
    else:
        matches = soup.find("ul", class_="releases scrolling")

    for elem in matches.find_all("li"):
        url = elem.a["href"]
        title = elem.a.text

        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url, first=0))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="content").find_all("article", id=re.compile(r"^post-\d+"))

    for elem in matches:
        langs = list()
        info_1 = elem.find("div", class_="poster")
        info_2 = elem.find("div", class_="data")

        thumb = info_1.find("img", {"alt":True})["src"]
        title = re.sub(r" \(.*?\)| \| .*", "", info_2.a.text)
        url = info_2.a["href"]
        try:
            lang_list = info_1.find("div", class_="langs").find_all("img")
            for lang in lang_list:
                langs.append(lang["title"])
        except:
            langs = ""
        try:
            year = info_2.find("span", text=re.compile(r"\d{4}")).text.split(",")[-1].strip()
        except:
            year = "-"

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", contentTitle=title,
                         thumbnail=thumb, language=langs,  infoLabels={"year": year}))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("div", class_="pagination").find("span", class_="current").next_sibling["href"]
    except:
        return itemlist

    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    soup = create_soup(item.url)
    matches = soup.find("div", class_="dooplay_player").find_all("div", id=re.compile(r"embed-\w+"))
    for opt_list in matches:
        opts = opt_list.find_all("li")
        lang = opt_list["id"].replace("embed-", "")
        if "trailer" in lang:
            continue
        for opt in opts:
            post = {"action": "doo_player_ajax", "post": opt["data-post"], "nume": opt["data-nume"],
                    "type": opt["data-type"]}
            headers = {"Referer": item.url}
            doo_url = "%swp-admin/admin-ajax.php" % host
            data = httptools.downloadpage(doo_url, post=post,  headers=headers).data
            url = BeautifulSoup(data, "html5lib").find("iframe")["src"]

            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play',
                                 language=IDIOMAS.get(lang, 'LAT'), infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

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
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def search_results(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    for elem in soup.find_all("article"):
        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.img["alt"]
        title = re.sub(r" \(.*?\)| \| .*", "", title)
        try:
            year = elem.find("span", class_="year").text
        except:
            year = '-'

        language = get_language(elem)

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", contentTitle=title,
                             thumbnail=thumb, language=language, infoLabels={'year': year}))


    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
    except:
        return itemlist

    itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='search_results'))

    return itemlist


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'peliculas-online/estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas-online/animacion/'
        elif categoria == 'terror':
            item.url = host + 'peliculas-online/terror/'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
