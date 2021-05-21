# -*- coding: utf-8 -*-
# -*- Channel CinematteFlix-*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


list_language = ["CAST", "VOSE"]

list_quality = []

list_servers = [
    'youtube',
    ]

host = 'https://www.cinematte.com.es/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + "category/videoclub", action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', url=host, action='section',
                         thumbnail=get_thumb('all', auto=True)))

    # itemlist.append(
    #     item.clone(title="Buscar...", action="search", url=host + 'search?q=', thumbnail=get_thumb("search", auto=True),
    #                extra='movie'))

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


def section(item):
    logger.info()
    itemlist = list()

    soup = create_soup(item.url).find_all("a", href=re.compile("/tag/"))

    for elem in soup:
        title = elem.text.lower().replace("cinematte ", "").capitalize()
        url = elem["href"]
        itemlist.append(Item(channel=item.channel, url=url, action="list_all", title=title))

    itemlist = sorted(itemlist, key=lambda i: i.title)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("article")

    for elem in matches:
        url = elem.h4.a["href"]

        try:
            title = clear_title(elem.h4.a.text.lower())
            title, year = scrapertools.find_single_match(title, "([^\|]+)\| (\d{4})?")
        except:
            continue
        if not year:
            year = "-"
        thumb = elem.img["src"]
        new_item = Item(channel=item.channel, title=title.capitalize(), thumbnail=thumb,
                        url=url, infoLabels={"year": year})
    #
        if "/coleccion" in url:
            new_item.action = "list_collection"
        else:
            if "serie" in url:
                new_item.contentSerieName = title
            else:
                new_item.contentTitle = title
            new_item.action = "findvideos"

    #
        itemlist.append(new_item)
    #     except:
    #         pass
    tmdb.set_infoLabels_itemlist(itemlist, True)
    #
    try:
        url_next_page = soup.find("a", class_="next page-numbers")["href"]
    except:
        return itemlist
    if len(itemlist):
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))
    #
    return itemlist


def clear_title(title):
    title = re.sub("(?:videoclub \| )?(?:ver )?(?:y descargar )?(?:pel.*?cula\S? de)?(?:pel.*?cula\S?)?(?:gratis)?(?:en tu videoclub )?(?:serie)?(?:online)?", "", title)
    return title.strip()


def list_collection(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    pag = soup.find("script", text=re.compile("var pagina"))
    if pag:
        url = scrapertools.find_single_match(pag.text, 'var pagina="([^"]+)"')
        return list_all(item.clone(url=url))

    matches = soup.find_all("iframe")
    cnt = 1
    for elem in matches:
        url = elem["src"]
        if "youtube" not in url:
            continue
        try:
            info_url = "https://www.youtube.com/oembed?url=%s&format=json" % url.replace("/embed/", "/watch?v=")
            info = httptools.downloadpage(info_url).json
            title = info["title"].replace(" HD", "")
            thumb = info["thumbnail_url"]
            ct = title
        except:
            ct = ""
            no_title = re.sub(r":|colección|'|\d+", "", item.title.lower()).strip()
            if cnt == 1:
                title = "%s" % (no_title)
            else:
                title = "%s %s" % (no_title, cnt)

            thumb = item.thumb
            cnt += 1

        itemlist.append(Item(channel=item.channel, title=title.capitalize(), contentTitle=ct, action="findvideos", url=url,
                             language=item.language, thumbnail=thumb, infoLabels={"year": "-"}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()

    if not "youtube" in item.url:
        soup = create_soup(item.url)
        urls = soup.find_all("iframe")
        for url in urls:
            url = url["src"]
            if "youtube" not in url:
                continue
            itemlist.append(Item(channel=item.channel, title="%s", action="play", url=url,
                                 language=item.language, infoLabels=item.infoLabels))
    else:
        itemlist.append(Item(channel=item.channel, title="%s", action="play", url=item.url,
                             language=item.language, infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != "findvideos":
            itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]",
                                 url=item.url, action="add_pelicula_to_library", extra="findvideos",
                                 contentTitle=item.contentTitle))

    return itemlist

