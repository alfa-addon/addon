# -*- coding: utf-8 -*-
# -*- Channel DoramasYT -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse
import re
import urllib
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

host = 'https://www.doramasyt.com/'
IDIOMAS = {'la': 'LAT', 'sub': 'VOSE'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['okru', 'streamtape', 'fembed', 'uqload', 'videobin']
list_quality = []


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


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="En Emisión", action="list_all", url=host + "emision",
                         thumbnail=get_thumb("on air", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Doramas", action="sub_menu", url=host + "doramas",
                         thumbnail=get_thumb("doramas", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="sub_menu", url=host + "categoria/pelicula",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section",
                         url=host + "doramas", thumbnail=get_thumb("alphabet", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section",
                         url=host + "doramas", thumbnail=get_thumb("year", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "search?q=",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all",
                         url=item.url, thumbnail=get_thumb("all", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         url=item.url, thumbnail=get_thumb("genres", auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="row").find_all("article")

    for elem in matches:
        url = elem.a["href"]
        title = elem.h3.text
        try:
            year = elem.find("span", class_="fecha").text
        except:
            year = ""
        content = elem.find("span", class_="category").text

        new_item = Item(channel=item.channel, url=url, title=title,
                             action="episodios", infoLabels= {"year": year})

        if not "pelicula" in content.lower():
            new_item.contentSerieName = title
        else:
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    # Paginación

    try:
        next_page = soup.find("ul", class_="pagination").find("a", class_="page-link", text="Sig")["href"]
        next_page = scrapertools.find_single_match(item.url, "([^\?]+)\??") + next_page
        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    if item.title == "Generos":
        data = soup.find("div", {"aria-labelledby": "genreMenuButton"})
    elif item.title == "Por Años":
        data = soup.find("div", {"aria-labelledby": "yearMenuButton"})
    else:
        data = soup.find("div", {"aria-labelledby": "letterMenuButton"})

    matches = data.find_all("a")
    for elem in matches[1:]:
        title = elem.text
        url = host + elem["href"]
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all"))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="SerieCaps")
    matches = soup.find_all("a")
    infoLabels = item.infoLabels
    for elem in matches:
        url = elem["href"]
        epi_num = scrapertools.find_single_match(url, "episodio-(\d+)")
        infoLabels["season"] = 1
        infoLabels["episode"] = epi_num
        title = "1x%s - Episodio %s" %(epi_num, epi_num)
        if "sub" in elem.text.lower():
            language = IDIOMAS.get("sub", "VOSE")
        elif "latino" in elem.text.lower():
            language = IDIOMAS.get("la", "VOSE")

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             language=language, infoLabels=infoLabels))

    if item.contentTitle and len(itemlist) == 1:
        return findvideos(itemlist[0])
    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = itemlist[::-1]
    if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0 and not item.foldereps:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("li", class_="Button")

    for elem in matches:
        srv = elem["title"]
        if srv.lower() == "ok":
            srv = "okru"
        opt_id = elem["data-tplayernv"]

        itemlist.append(Item(channel=item.channel, url=item.url, title=srv, server=srv, action="play",
                             opt=opt_id, language=item.language, infoLabels=item.infolabels))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find("div", class_="TPlayerTb", id=item.opt)
    if not soup.find("iframe"):
        soup = BeautifulSoup(soup.text)

    url = soup.find("iframe")["src"]
    url = urllib.unquote(scrapertools.find_single_match(url, "url=([^&]+)"))
    if "monoschinos" in url:
        data = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(data, "file: '([^']+)'")

    itemlist.append(item.clone(url=url, server=""))
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