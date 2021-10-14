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

IDIOMAS = {'Subtitulado': 'VOSE', 'Latino': 'LAT', 'Castellano': 'CAST'}
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
                         url=host + "pelis/idiomas/subtituladas-p02",
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
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="post-lst")

    if not matches:
        return itemlist

    for elem in matches.find_all("article", class_="post"):
        url = elem.a["href"]
        title = fix_title(elem.h2.text)
        try:
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem.find("img")["data-src"])
        except:
            thumb = elem.find("img")["src"]

        year = '-'

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})
        new_item.contentTitle = title
        new_item.action = "findvideos"
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("a", text="SIGUIENTE")["href"]
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
        url = '%s/release/%s' % (host, year)

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
    matches = soup.find_all("a", class_="btn", href=re.compile("#options-\d+"))
    if not matches:
        return itemlist
    infoLabels = item.infoLabels

    for elem in matches:
        srv, lang = elem.find("span", class_="server").text.split("-")
        lang = lang.strip().split(" ")[-1]
        if srv.strip().lower() == "hlshd":
            srv = "Fembed"
        opt = soup.find("div", id="%s" % elem.get("href", "").replace("#", ""))
        url = opt.iframe.get("data-src")

        itemlist.append(Item(channel=item.channel, title=srv.strip(), url=url, action='play',
                             server=srv.strip(), infoLabels=infoLabels,
                             language=IDIOMAS.get(lang, "VOSE")))

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

    url = create_soup(item.url).find("div", class_="Video").iframe["src"]
    itemlist.append(item.clone(url=url, server=""))
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            item.search = True
            return list_all(item)
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def fix_title(title):
    title = re.sub(r'(/.*)| 1$', '', title)
    return title


def newest(categoria):
    logger.info()

    item = Item()
    #try:
    if categoria in ['peliculas']:
        item.url = host + "pelicula"
    elif categoria == 'latino':
        item.url = host + "pelis/idiomas/espanol-latino"
    elif categoria == 'castellano':
        item.url = host + "pelis/idiomas/castellano"
    elif categoria == 'infantiles':
        item.url = host + 'peliculas/animacion-p04'
    elif categoria == 'terror':
        item.url = host + 'peliculas/terror'
    itemlist = list_all(item)
    if itemlist[-1].title == 'Siguiente >>':
        itemlist.pop()
    # except:
    #     import sys
    #     for line in sys.exc_info():
    #         logger.error("{0}".format(line))
    #     return []

    return itemlist