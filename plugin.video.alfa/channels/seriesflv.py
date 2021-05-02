# -*- coding: utf-8 -*-
# -*- Channel SeriesFLV -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse

from channels import filtertools
from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://seriesflv.org/'
IDIOMAS = {'es': 'CAST', 'esp': 'CAST', 'la': 'LAT', 'lat': 'LAT', 'sub': 'VOSE', 'espsub': 'VOSE', 'en': 'VO',
           'eng': 'VO', 'engsub': 'VOS'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['powvideo', 'gamovideo', 'streamplay', 'flashx', 'nowvideo', 'thevideo']
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

    itemlist.append(Item(channel=item.channel, title="Novedades", action="menu_novedades",
                         thumbnail=get_thumb("newest", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Ultimas series", action="latest", url=host,
                         thumbnail=get_thumb("last", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Más vistas", action="section", url=host,
                         thumbnail=get_thumb("more_watched", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Listado Alfabético", action="section", url=host,
                         thumbnail=get_thumb("alphabet", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def menu_novedades(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Castellano", action="novedades", url=host, lang_type="es"))
    itemlist.append(Item(channel=item.channel, title="Latino", action="novedades", url=host, lang_type="la"))
    itemlist.append(Item(channel=item.channel, title="VOSE", action="novedades", url=host, lang_type="sub"))
    itemlist.append(Item(channel=item.channel, title="VO", action="novedades", url=host, lang_type="en"))

    return itemlist


def novedades(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="body bg4")

    for elem in soup.find_all("a", class_="item-one"):
        if elem["lang"] != item.lang_type:
            continue
        url = elem["href"]
        c_title = elem.find("div", class_="i-title").text
        epi = elem.find("div", class_="box-tc").text
        lang = IDIOMAS.get(elem["lang"], "VOSE")
        title = "%s - %s" % (c_title, epi)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             contentSerieName=c_title, language=lang))


    return itemlist


def latest(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="body bg4")

    for elem in soup.find_all("article"):
        url = elem.a["href"]
        title = elem.find("div", class_="tit over txtc").text

        itemlist.append(Item(channel=item.channel, url=url, title=title, contentSerieName=title, action="seasons",
                        context=filtertools.context(item, list_idiomas, list_quality)))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    # Paginación

    try:
        next_page = soup.find("a", class_="next")["href"]

        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='latest'))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="sidebar left")

    if "Alfabético" not in item.title:
        value = soup.find_all("div", class_= lambda x: x and x.startswith("top-"))
    else:
        value = soup.find("div", id="letters").find_all("a")

    for elem in value:

        action = "latest"
        if "Alfabético" not in item.title:
            elem_data = elem.find_all("a")
            elem = elem_data[0] if len(elem_data) == 1 else elem_data[1]
            action = "seasons"
            url = elem["href"]
        else:
            url = urlparse.urljoin(host, elem["href"])

        title = elem.text

        new_item = Item(channel=item.channel, title=title, action=action, url=url)

        if "letra" not in url:
            new_item.contentSerieName = title
            new_item.context = filtertools.context(item, list_idiomas, list_quality)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id="capitulos")

    infoLabels = item.infoLabels

    for elem in soup.find_all("h4"):
        title = elem.a.text.strip()
        season = scrapertools.find_single_match(title, "(\d+)")
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName
                             ))

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

    soup = create_soup(item.url).find_all("div", class_="panel panel-default")[item.infoLabels["season"]-1]
    infoLabels = item.infoLabels
    for elem in soup.find_all("tr"):

        info = elem.find("a", class_="color4")
        if not info:
            continue
        url = info["href"]
        title = info.text
        infoLabels["episode"] = scrapertools.find_single_match(title, "\dx(\d+)")
        language = languages_from_flags(elem, "png")

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                             language=language, infoLabels=infoLabels))

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url, referer=host).find("table", class_="table table-hover").find("tbody")

    for elem in soup.find_all("tr"):
        link_data = elem.find("td", class_="linkComent")
        url = link_data.a["data-enlace"]
        server = link_data.a["data-server"]
        if server == "vidabc":
            server = "clipwatching"
        lang = link_data.a["data-language"]

        itemlist.append(Item(channel=item.channel, url=url, title=server, server=server, action="play",
                             language=IDIOMAS.get(lang, lang)))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


# def play(item):
#     logger.info()
#
#     itemlist = list()
#
#     try:
#         headers = {"referer": host}
#         url = httptools.downloadpage(urlparse.urljoin(host, item.url), headers=headers,
#                                      follow_redirects=False).headers["location"]
#         itemlist.append(item.clone(url=url, server=''))
#         itemlist = servertools.get_servers_itemlist(itemlist)
#
#         return itemlist
#
#     except:
#         return


def languages_from_flags(lang_data, ext):
    logger.info()
    language = list()

    lang_list = lang_data.find_all("img")

    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["src"], "(\w+).%s" % ext)
        language.append(IDIOMAS.get(lang, "VOSE"))

    return language


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return latest(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []