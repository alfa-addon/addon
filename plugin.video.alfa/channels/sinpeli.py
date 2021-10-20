# -*- coding: utf-8 -*-
# -*- Channel SinPeli -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64
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

host = 'https://www.sinpeli.com/'

IDIOMAS = {'la': 'LAT', 'ca': 'CAST', 'su': 'VOSE'}
list_idiomas = list(set(IDIOMAS.values()))

list_servers = ['okru', 'yourupload', 'mega']
list_quality = []


def get_source(url, soup=False, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(
        Item(
            action="list_all",
            channel=item.channel,
            thumbnail=get_thumb("All", auto=True),
            title="Todas",
            url=host)
    )

    itemlist.append(
        Item(
            action="by_languages",
            channel=item.channel,
            thumbnail=get_thumb("language", auto=True),
            title="Idiomas",
            url=host)
    )

    itemlist.append(
        Item(
            action="by_quality",
            channel=item.channel,
            thumbnail=get_thumb("quality", auto=True),
            title="Calidad",
            url=host)
    )


    itemlist.append(
        Item(
            action="section",
            channel=item.channel,
            thumbnail=get_thumb("genres", auto=True),
            title="Generos",
            url=host
        )
    )

    itemlist.append(
        Item(
            action="search",
            channel=item.channel,
            thumbnail=get_thumb("search", auto=True),
            url=host + "?s=",
            title="Buscar..."
        )
    )

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def by_languages(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Castellano", url=host + "idioma/castellano/", action="list_all",
                         thumbnail=get_thumb("cast", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Castellano AC3 5.1", url=host + "idioma/castellano/", action="list_all",
                         thumbnail=get_thumb("cast", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Latino", url=host + "idioma/latino/", action="list_all",
                         thumbnail=get_thumb("lat", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Latino AC3 5.1", url=host + "idioma/latino51/", action="list_all",
                         thumbnail=get_thumb("lat", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Subtitulado", url=host + "idioma/subtitulado/", action="list_all",
                         thumbnail=get_thumb("vose", auto=True)))

    return itemlist


def by_quality(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="1080p", url=host + "calidad/1080p/", action="list_all",
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="720p", url=host + "calidad/720p/", action="list_all",
                         thumbnail=get_thumb("cast", auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()
    soup = get_source(item.url, soup=True)
    matches = soup.find_all("article", class_="TPost C")
    if not matches:
        return itemlist

    for elem in soup.find_all("article"):

        url = elem.a["href"]
        title = elem.a.h3.text
        thumb = elem.find("img")
        thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
        try:
            lang = elem.find("span", class_="languages").text.strip()[:2]
        except:
            lang = "la"
        try:
            year = scrapertools.find_single_match(title,'\((\d{4})\)')
        except:
            year = "-"

        contentTitle = re.sub("(year)", "", title).strip()

        new_item = Item(
            channel=item.channel,
            infoLabels={"year": year},
            thumbnail=thumb,
            title=title,
            contentTitle=contentTitle,
            url=url,
            language=IDIOMAS.get(lang.lower(), "LAT"),
            action="findvideos",
        )

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find("span", class_="current").next_sibling["href"]

        itemlist.append(
            Item(
                channel=item.channel,
                title="Siguiente >>",
                url=next_page,
                action='list_all'
            )
        )
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    if item.title == "Generos":
        soup = get_source(item.url, soup=True).find("ul", class_="sub-menu")
        action = "list_all"

    for elem in soup.find_all("li"):
        url = elem.a["href"]
        title = elem.a.text

        itemlist.append(
            Item(
                action=action,
                channel=item.channel,
                title=title,
                url=url
            )
        )

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    infoLabels = item.infoLabels
    soup = get_source(item.url, soup=True).find("ul", class_="TPlayerNv").find_all("li")

    for btn in soup:
        b_data = btn["data-player"]
        srv = btn.span.text.lower()
        if "trailer" in srv.lower():
            continue
        try:
            lang = btn.span.next_sibling.text[:2]
        except:
            lang = "la"

        itemlist.append(
            Item(
                action='play',
                channel=item.channel,
                infoLabels=infoLabels,
                language=IDIOMAS.get(lang.lower(), "LAT"),
                b_data=b_data,
                server=srv,
                title=srv,
                url=item.url
            )
        )

    itemlist = sorted(itemlist, key=lambda i: i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and (
                not item.videolibrary or item.extra != 'findvideos'):
            itemlist.append(
                Item(
                    action="add_pelicula_to_library",
                    contentTitle=item.contentTitle,
                    channel=item.channel,
                    extra="findvideos",
                    title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                    url=item.url
                )
            )

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    try:
        url = BeautifulSoup(base64.b64decode(item.b_data.encode("utf-8")), "html5lib").iframe["src"]
        item.url = url
        item.server = ""
        itemlist.append(item)
        itemlist = servertools.get_servers_itemlist(itemlist)
    except:
        pass

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


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host
        elif categoria == 'latino':
            item.url = host + "idioma/latino/"
        elif categoria == 'castellano':
            item.url = host + "idioma/castellano"
        elif categoria == 'infantiles':
            item.url = host + 'animacion'
        elif categoria == 'terror':
            item.url = host + 'terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist