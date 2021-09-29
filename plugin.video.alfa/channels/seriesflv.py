# -*- coding: utf-8 -*-
# -*- Channel SeriesFLV -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
import base64
import re

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

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

host = 'https://seriesflv.xyz/'

IDIOMAS = {'esp': 'CAST', 'lat': 'LAT', 'sub': 'VOSE', "ing": 'VO'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['fembed', 'streamtape', 'cloudvideo', 'mixdrop']
list_quality = []


def create_soup(url, post=None, referer=None, unescape=False):
    logger.info()

    if post:
        data = httptools.downloadpage(url, post=post, headers={"referer": referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", action="novedades", url=host + "ver",
                         thumbnail=get_thumb("new episodes", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Ultimas series", action="list_all", url=host + "online-series-completas",
                         thumbnail=get_thumb("last", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb("genres", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Por Año", action="section",
                         thumbnail=get_thumb("year", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def novedades(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id="archive-content")

    for elem in soup.find_all("article"):
        languages = list()
        title = elem.find("span", class_="serie").text
        c_title = scrapertools.find_single_match(title, "([^\(]+)").strip()
        lang_data = elem.find_all("img")
        url = elem.a["href"]
        thumb = lang_data[0].get("src", "")
        for l_data in lang_data[1:]:
            languages.append(IDIOMAS.get(l_data.get("title", "sub")[:3].lower(), "VOSE"))
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", thumbnail=thumb,
                             contentSerieName=c_title, language=languages, infoLables={}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="content")
    for elem in matches.find_all("article", id=re.compile("post-\d+")):
        thumb = elem.img.get("src", "")
        elem = elem.find("div", class_="data")
        url = elem.h3.a["href"]
        title = scrapertools.find_single_match(elem.h3.a.text, "(.*)\(")

        itemlist.append(Item(channel=item.channel, url=url, title=title, contentSerieName=title, action="seasons", thumbnail=thumb, 
                        context=filtertools.context(item, list_idiomas, list_quality)))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    # Paginación

    try:
        next_page = soup.find("div", class_="pagination").find_all("a")[-1]["href"]
        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()
    base_url = "%s%s" % (host, "online-series-completas")
    soup = create_soup(base_url)

    if item.title == "Generos":
        matches = soup.find("ul", class_="genres scrolling")
    else:
        matches = soup.find("ul", class_="releases scrolling")

    for elem in matches.find_all("li"):
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url, first=0))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    base_url = "%s/wp-admin/admin-ajax.php" % host
    data = create_soup(item.url).find_all("script")[-2]
    al = scrapertools.find_single_match(data["src"], 'base64,(.*)')
    fa = base64.b64decode(al)
    id = scrapertools.find_single_match(fa, 'var id=(\d+)')
    post = {"action": "seasons", "id": id}
    soup = create_soup(base_url, post=post, referer=item.url)
    matches = soup.find_all("span", class_="se-t")
    infoLabels = item.infoLabels

    for elem in matches:
        season = elem.text
        title = "Temporada %s" % season
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             context=filtertools.context(item, list_idiomas, list_quality), infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    base_url = "%s/wp-admin/admin-ajax.php" % host
    data = create_soup(item.url).find_all("script")[-2]
    al = scrapertools.find_single_match(data["src"], 'base64,(.*)')
    fa = base64.b64decode(al)
    id = scrapertools.find_single_match(fa, 'var id=(\d+)')
    post = {"action": "seasons", "id": id}
    soup = create_soup(base_url, post=post, referer=item.url)

    matches = soup.find_all("div", class_="se-c")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in matches:
        if elem.find("span", class_="se-t").text != str(season):
            continue

        epi_list = elem.find("ul", class_="episodios")
        for epi in epi_list.find_all("li"):
            info = epi.find("div", class_="episodiotitle")
            url = info.a["href"]
            epi_name = info.a.text
            epi_num = epi.find("div", class_="numerando").text.split(" - ")[1]
            infoLabels["episode"] = epi_num
            title = "%sx%s - %s" % (season, epi_num, epi_name)

            itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                 infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("ul", id="playeroptionsul")

    for lang_data in matches.find_all("li"):
        lang = lang_data.find("span", class_="title").text[:3].lower()
        data_tab = lang_data.get("data-tab", "")
        post_data = soup.find("div", id=data_tab).find_all("li")
        for elem in post_data:
            srv = elem.find("span", class_="title").text.lower()
            post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
                    "type": elem["data-type"]}

            itemlist.append(Item(channel=item.channel, title="%s", action="play", post=post, ref=item.url, server=srv,
                                 language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != "findvideos":
            itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]",
                                 url=item.url, action="add_pelicula_to_library", extra="findvideos",
                                 contentTitle=item.contentTitle))

    return itemlist



def play(item):
    logger.info()

    itemlist = list()

    doo_url = "%swp-admin/admin-ajax.php" % host
    data = httptools.downloadpage(doo_url, post=item.post, headers={"referer": item.ref}).data
    try:
        url = BeautifulSoup(data, "html5lib").find("iframe")["src"]
    except:
        return

    if not url.startswith("http"):
        url = "https:%s" % url

    itemlist.append(item.clone(url=url, server=''))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []