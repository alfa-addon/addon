# -*- coding: utf-8 -*-
# -*- Channel PelisForte -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

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

host = 'https://pelisforte.co/'

IDIOMAS = {'Sub': 'VOSE', 'Lat': 'LAT', 'Cast': 'CAST'}
list_language = list(IDIOMAS.values())
list_servers = ['evoload', 'fembed', 'uqload']
list_quality = []


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")

    return soup


# def mainlist(item):
#     logger.info()
#
#     autoplay.init(item.channel, list_servers, list_quality)
#
#     itemlist = list()
#
#     itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu',
#                          thumbnail=get_thumb('movies', auto=True), type=1))
#
#     itemlist.append(Item(channel=item.channel, title='Series', action='sub_menu',
#                          thumbnail=get_thumb('tvshows', auto=True), type=2))
#
#     itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
#                          thumbnail=get_thumb("search", auto=True)))
#
#     autoplay.show_option(item.channel, itemlist)
#
#     return itemlist


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Novedades", action="list_all",
                         url=host + "pelicula",
                         thumbnail=get_thumb("newest", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all",
                         url=host + "pelis/idiomas/castellano",
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all",
                         url=host + "pelis/idiomas/espanol-latino",
                         thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all",
                         url=host + "pelis/idiomas/subtituladas",
                         thumbnail=get_thumb("vose", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb("genres", auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title="Años", action="year", thumbnail=get_thumb('year', auto=True),
                         url=host + "peliculas"))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()
    if item.type:
        item.url += '?tr_post_type=%s' % item.type
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="MovieList NoLmtxt Rows AX A06 B04 C03 E20")

    if not matches:
        return itemlist

    for elem in soup.find_all("article"):
        url = elem.a["href"]
        title = fix_title(elem.a.h3.text)
        try:
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem.find("img")["data-src"])
        except:
            thumb = elem.find("img")["src"]

        year = ''
        quality = ''
        if not "-serie-" in url:
            try:
                year = elem.find("span", class_="Year").text
            except:
                pass

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})
        new_item.contentTitle = title
        new_item.action = "findvideos"
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def year(item):
    import datetime
    logger.info()

    itemlist = list()

    now = datetime.datetime.now()
    c_year = now.year + 1

    l_year = c_year - 21
    year_list = list(range(l_year, c_year))

    for year in year_list:
        year = str(year)
        url = '%s?s=trfilter&trfilter=1&years[]=%s,' % (host, year)

        itemlist.append(Item(channel=item.channel, title=year, url=url,
                             action="list_all"))
    itemlist.reverse()
    return itemlist


def section(item):
    logger.info()
    import string

    itemlist = list()

    soup = create_soup(item.url)
    if item.title == "Generos":
        data = soup.find("li", id="menu-item-77")
    elif item.title == "Años":
        data = soup.find("div", class_="trsrcbx")

    matches = data.find("ul").find_all("li")
    for elem in matches:
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                             url=url, type=item.type))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("ul", id="fenifdev-lang-ul")
    logger.debug(soup)
    if not matches:
        return itemlist
    infoLabels = item.infoLabels

    for elem in matches:
        lang = ""
        try:
            logger.debug(elem.find("div").text)
            lang = elem.find("div").text.lower()
            if "latino" in lang:
                lang = IDIOMAS.get("Lat", "VOSE")
            elif "subtitulado" in lang:
                lang = IDIOMAS.get("Sub", "VOSE")
            elif "castellano" in lang:
                lang = IDIOMAS.get("Cast", "VOSE")
        except:
            continue
        opts = elem.find_all("li")
        for opt in opts:
            logger.debug(opt)
            logger.debug(opt.text.split("-"))
            srv = opt.text.split("-")[1].strip()
            opt_id = opt["data-tplayernv"]

            itemlist.append(Item(channel=item.channel, title=srv, url=item.url, action='play', server=srv, opt=opt_id,
                                 infoLabels=infoLabels, language=lang))

    #downlist = get_downlist(item, data)
    #itemlist.extend(downlist)

    itemlist = sorted(itemlist, key=lambda i: (i.language, i.server))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(
            itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist



def play(item):
    logger.info()
    itemlist = list()

    if not item.opt:
        if host in item.url:
            item.url = httptools.downloadpage(item.url, ignore_response_code=True).url

        itemlist.append(item.clone(url=item.url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)

        return itemlist

    soup = create_soup(item.url).find("div", class_="TPlayerTb", id=item.opt)
    url = scrapertools.find_single_match(str(soup), 'src="([^"]+)"')
    url = re.sub("amp;|#038;", "", url)
    url = create_soup(url).find("div", class_="Video").iframe["src"]
    itemlist.append(item.clone(url=url, server=""))
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            return list_all(item)
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def fix_title(title):
    title = re.sub(r'\((.*)', '', title)
    title = re.sub(r'\[(.*?)\]', '', title)
    return title


def get_downlist(item, data):
    import base64
    logger.info()

    downlist = list()
    servers = {'drive': 'gvideo', '1fichier': 'onefichier'}

    soup = data.find("tbody").find_all("tr")
    infoLabels = item.infoLabels

    for tr in soup:
        burl = tr.a["href"].split('?l=')[1]
        try:
            for x in range(7):
                durl = base64.b64decode(burl).decode('utf-8')
                burl = durl
        except:
            url = burl

        info = tr.span.findNext('span')
        info1 = info.findNext('span')

        srv = info.text.strip().lower()
        srv = servers.get(srv, srv)

        lang = info1.text.strip()
        lang = IDIOMAS.get(lang, lang)

        quality = info1.findNext('span').text

        downlist.append(Item(channel=item.channel, title=srv, url=url, action='play', server=srv,
                             infoLabels=infoLabels, language=lang, quality=quality))

    return downlist

