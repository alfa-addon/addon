# -*- coding: utf-8 -*-
# -*- Channel DangoToons -*-
# -*- Created for Pelisalacarta-ce (channel formerly named AniToonsTv) -*-
# -*- Updated and maintained by the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channels import renumbertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay

IDIOMAS = {'latino': 'Latino'}
list_language = list(IDIOMAS.values())
list_servers = [
                'okru',
                'rapidvideo'
                ]
list_quality = ['default']

canonical = {
             'channel': 'dangotoons', 
             'host': config.get_setting("current_host", 'dangotoons', default=''), 
             'host_alt': ["https://dangotoons.net/"], 
             'host_black_list': ["https://www.dangotoons.net/"], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def get_source(url, soup=False, json=False, unescape=False, **opt):
    logger.info()

    opt['canonical'] = canonical
    data = httptools.downloadpage(url, **opt)

    if 'function countdown' in data.data:
        urlparts = scrapertools.find_multiple_matches(data.data, "var identificador = '(.+?)'.+?location.href = '(.+?)'")[0]
        url = '%s%s' % (urlparts[1], urlparts[0])
        data = httptools.downloadpage(url, **opt)

    if json:
        data = data.json
    else:
        data = data.data
        data = scrapertools.unescape(data) if unescape else data
        data = BeautifulSoup(data, "html5lib", from_encoding="utf-8") if soup else data

    return data, url


def create_mainlist_item(data):
    
    category = data["category_dict"]
    data = data["data"]
    
    new_item = Item(
                    action = "list_all",
                    category = category["category"],
                    channel = category["channel"],
                    first = 0,
                    thumbnail = category["thumbnail"]
                )
    
    for key in data:
        new_item.__setattr__(key, data[key])
    
    return new_item


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    
    category_all = {"thumbnail": get_thumb("all", auto=True), "category": "series", "channel": item.channel}
    category_series = category_all
    category_series["thumbnail"] = get_thumb("tvshows", auto=True)
    category_movies = {"thumbnail": get_thumb("movies", auto=True), "category": "peliculas", "channel": item.channel}

    categories = [
        {"data" :  {"title": "Todos",
                    "url": host + "catalogo.php"},
                    "category_dict": category_all
        },
        {"data" :  {"title": "Anime",
                    "url": host + "catalogo.php?t=anime&g=&o=3"},
                    "category_dict": category_series
        },
        {"data" :  {"title": "Series Animadas",
                    "url": host + "catalogo.php?t=series-animadas&g=&o=3"},
                    "category_dict": category_series
        },
        {"data" :  {"title": "Series Animadas Adolescentes",
                    "url": host + "catalogo.php?t=series-animadas-r&g=&o=3"},
                    "category_dict": category_series
        },
        {"data" :  {"title": "Series Live Action",
                    "url": host + "catalogo.php?t=series-actores&g=&o=3"},
                    "category_dict": category_series
        },
        {"data" :  {"title": "Peliculas",
                    "url": host + "catalogo.php?t=peliculas&g=&o=3"},
                    "category_dict": category_movies
        },
        {"data" :  {"title": "Especiales",
                    "url": host + "catalogo.php?t=especiales&g=&o=3"},
                    "category_dict": category_movies
        }
    ]

    for category in categories:
        itemlist.append(create_mainlist_item(category))
    
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            first=0,
            thumbnail = get_thumb("search", auto=True),
            title = "Buscar"
        )
    )

    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host +"php/buscar.php"
    item.texto = texto

    if texto != '':
        return sub_search(item)
    else:
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    post = "b=" + item.texto
    headers = {"X-Requested-With":"XMLHttpRequest"}
    data, item.url = get_source(item.url, post=post, headers=headers)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    for match in soup.find_all("a"):
        itemlist.append(
            Item(
                action = "seasons",
                category = "series",
                channel = item.channel,
                contentSerieName = match.text,
                first = 0,
                title = match.text,
                url = match["href"]
            )
        )

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    soup, item.url = get_source(item.url, soup=True)
    match = soup.find("div", class_="listados")
    context = renumbertools.context(item)
    context2 = autoplay.context
    context.extend(context2)
    first = item.first
    last = first + 25
    matches = match.find_all("div", class_="serie")
    if last >= len(matches):
        last = len(matches)
    for elem in matches[first:last]:
        scrapedurl = elem.a["href"]
        try:
            scrapedthumbnail = elem.img["data-src"]
        except:
            scrapedthumbnail = ''
        scrapedtitle = elem.a.p.text
        scrapedplot = elem.find("span", class_="mini").text
        if item.category == "series":
            action = "seasons"
        else:
            action = "findvideos"
        itemlist.append(
            Item(
                action = action,
                category = item.category,
                channel = item.channel,
                contentSerieName = scrapedtitle,
                context = context,
                plot = scrapedplot,
                thumbnail = scrapedthumbnail,
                title = scrapedtitle,
                url = host + scrapedurl if not "://" in scrapedurl else scrapedurl
            )
        )

    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    url_next_page = item.url
    first = last

    if url_next_page and len(matches) > 26:
        itemlist.append(
            Item(
                action = 'list_all',
                category = item.category,
                channel = item.channel,
                first = first,
                title = "[COLOR cyan]Página Siguiente >>[/COLOR]",
                url = url_next_page
            )
        )
    return itemlist


def seasons(item):
    logger.info()
    itemlist = []
    soup, item.url = get_source(item.url, soup=True)

    match = soup.find("div", class_="listado")
    matches = match.find_all("div", class_="cajaTemporada")
    infoLabels = item.infoLabels

    if len(matches) == 0:
        title = "Temporada 1"
        infoLabels['season'] = 1

        itemlist.append(
            Item(
                action = "episodesxseason",
                channel = item.channel,
                contentSerieName = item.title,
                context = item.context,
                infoLabels = infoLabels,
                plot = item.plot,
                thumbnail = item.thumbnail,
                title = title,
                url = item.url
            )
        )

    else:

        for n, elem in enumerate(matches):
            n = n+1
            title = elem.find("div", class_="titulo").text
            infoLabels['season'] = n

            itemlist.append(
                Item(
                    action = "episodesxseason",
                    channel = item.channel,
                    contentSerieName = item.title,
                    context = item.context,
                    infoLabels = infoLabels,
                    plot = item.plot,
                    thumbnail = item.thumbnail,
                    title = title,
                    url = item.url
                )
            )

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                text_color = "yellow",
                title = 'Añadir esta serie a la videoteca',
                url = item.url
            )
        )

    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    data, item.url = get_source(item.url)
    soup = BeautifulSoup(data, "html5lib")
    match = soup.find("div", class_="listado")
    matches = match.find_all("div", class_="cajaTemporada")

    if len(matches) == 0:
        episodes = match.find("div", class_="cajaCapitulos")

    else:

        for elem in matches:
            if elem.find("div", class_="titulo").text != item.title: continue

            episodes = elem.find("div", class_="cajaCapitulos")

    infoLabels = item.infoLabels
    
    for n, episode in enumerate(episodes.find_all("li")):
        scrapedurl = "/"+episode.a["href"]
        scrapedtitle = episode.a.text
        infoLabels['episode'] = scrapedtitle.split(" - ")[0].split(": ")[1]

        # Parche para animes
        if infoLabels['season'] > 1 and n < 1 and infoLabels['episode'] > 1:
            infoLabels.update({'season': 1})

        title = "{}x{:02d} - {}".format(infoLabels['season'],infoLabels['episode'],scrapedtitle.split(" - ")[1])

        if host in item.url:
            url = "%s%s" % (host, scrapedurl)
        else:
            url = "%s%s" % ("/".join(item.url.split("/")[:3]), scrapedurl)

        itemlist.append(
            Item(
                action = "findvideos",
                contentSerieName = item.title,
                context = item.context,
                channel = item.channel,
                infoLabels = infoLabels,
                plot = item.plot,
                thumbnail = item.thumbnail,
                title = title,
                url = url
            )
        )
    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = list()
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data, item.url = get_source(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    url_videos = scrapertools.find_single_match(data, 'var q = \[ \[(.+?)\] \]')
    matches = scrapertools.find_multiple_matches(url_videos, '"(.+?)"')
    for url in matches:
        url=url.replace('\/', '/')
        itemlist.append(item.clone(url=url, action="play", title= "%s"))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    autoplay.start(itemlist, item)

    if item.category=="peliculas" and config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(
                action = "add_pelicula_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                text_color = "yellow",
                title = "Añadir esta película a la videoteca",
                url = item.url
            )
        )

    return itemlist
