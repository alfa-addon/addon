# -*- coding: utf-8 -*-
# -*- Channel EstrenosPapaya -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse  # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
else:
    import urllib  # Usamos el nativo de PY2 que es más rápido
    import urlparse

import re

from channels import filtertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from channels import autoplay
from core.item import Item
from platformcode import config, logger
from bs4 import BeautifulSoup

host = "https://www.estrenospapaya.com/"


IDIOMAS = {'es': 'Español', 'lat': 'Latino', 'in': 'Inglés', 'ca': 'Catalán', 'sub': 'VOSE', 'Español Latino': 'Latino',
           'Español Castellano': 'Español', 'Sub Español': 'VOSE'}

list_idiomas = list(IDIOMAS.values())

list_quality = list()

list_servers = ['streamtape', 'mixdrop', 'evoload']


def mainlist(item):
    logger.info()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = list()
    
    itemlist.append(
        Item(title="Nuevos Capitulos", channel=item.channel, action="sub_menu",
             thumbnail=get_thumb("news.png")))

    itemlist.append(
        Item(action="list_all", title="Series Nuevas", channel=item.channel,
             thumbnail=get_thumb("channels_tvshow.png"), extra="nuevas", url=host + "lista-series-estrenos/"))

    itemlist.append(
        Item(action="list_all", title="Las Más Vistas", channel=item.channel,
             thumbnail=get_thumb("channels_all.png"), url=host + "/lista-series-populares/"))

    itemlist.append(Item(action="search", title="Buscar", url= host + "busqueda.php",
                         channel=item.channel, thumbnail=get_thumb("search.png")))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(
        Item(action="new_episodes", title="Latino",
             url=host + "estreno-serie-espanol-latino/",
             channel=item.channel, thumbnail=get_thumb("channels_latino.png"),
             extra_lang="Latino", first=0))

    itemlist.append(
        Item(action="new_episodes", title="Castellano",
             url=host + "estreno-serie-castellano/", channel=item.channel,
             thumbnail=get_thumb("channels_spanish.png"), extra_lang="Español", first=0))

    itemlist.append(
        Item(action="new_episodes", title="Subtitulado",
             url=host + "estreno-serie-sub-espanol/", channel=item.channel,
             thumbnail=get_thumb("channels_vos.png"), extra_lang="VOSE", first=0))

    return itemlist


def create_soup(url, post=None, unescape=False):
    logger.info()

    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    matches = soup.find("div", id="resultsat").find_all("div", class_="esprinc")

    for elem in matches:
        url = host + scrapertools.find_single_match(elem.get("onclick", ""), "href='([^']+)")
        title = re.sub(r" \(.*?\)", "", elem.a.text).strip()
        thumb = host + elem.img.get("src", "")
        plot = elem.find("div", class_="essin").text.strip()
        context = filtertools.context(item, list_idiomas, list_quality)
        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=title, action="seasons", url=url,
                             thumbnail=thumb, plot=plot, context=context))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def new_episodes(item):
    logger.info()

    itemlist = list()

    if not item.post:
        soup = create_soup(item.url)
    else:
        soup = create_soup(item.url, post={"searchquery": item.post})

    language = item.extra_lang

    matches = soup.find("div", class_="cajita").find_all("div", class_="capitulo-caja")

    next = True
    first = item.first
    last = first + 20

    if last > len(matches):
        last = len(matches)
        next = False

    for elem in matches[first:last]:

        url = host + scrapertools.find_single_match(elem.get("onclick", ""), "'/([^']+)'")
        if not item.post:
            info = elem.find("div", class_="preopacidad")
            action = "findvideos"
        else:
            info = elem.find("div", class_="capitulo-info")
            action = "seasons"

        img_info = elem.find("div", class_="capitulo-imagen").get("style", "")
        title = re.sub(r'[\ \n]{2,}|\(.*\)', "", info.text).replace('"', " ").strip()
        c_title = scrapertools.find_single_match(title, r"\d+x\d+ ([^$]+)")
        if not c_title:
            c_title = title
        thumb = host + scrapertools.find_single_match(img_info, "url\('([^']+)")

        new_item = Item(channel=item.channel, action=action, title=title, url=url,
                        thumbnail=thumb, language=language, contentSerieName=c_title)

        if item.post:
            new_item.context = filtertools.context(item, list_idiomas, list_quality)

        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if next:
        url_next_page = item.url
        first = last
    else:
        return itemlist

    if len(matches) > 20:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='new_episodes',
                             first=first))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()

    infoLabels = item.infoLabels

    soup = create_soup(item.url)
    matches = soup.find_all("div", class_="ucap")

    for elem in matches:
        season = scrapertools.find_single_match(elem.get("id", ""), "(\d+)")
        title = "Temporada %s" % season
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseason",
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
         action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def get_languages(data_lang):
    logger.info()
    lang_list = list()
    langs = data_lang.find_all("img")

    for lang in langs:
        lang = scrapertools.find_single_match(lang.get("src", ""), "(\w+)\.png")
        lang_list.append(IDIOMAS.get(lang, "VOSE"))
    return lang_list


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = list()

    infoLabels = item.infoLabels
    season = infoLabels["season"]
    matches = create_soup(item.url).find("div", id="hoh%s" % season).find_all("div", class_="ucapname")

    for elem in matches:
        data_lang = elem.find_next_sibling()
        langs = get_languages(data_lang)
        url = host + elem.a.get("href", "")
        title = elem.a.text.strip()
        epi_num = scrapertools.find_single_match(url.lower(), "capitulo-(\d+)")
        infoLabels["episode"] = epi_num
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", language=langs,
                             infoLabels=infoLabels))

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.post = texto
        item.first = 0
        if texto != '':
            return new_episodes(item)
        else:
            return []
    #Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info("url: %s" % item.url)

    itemlist = list()

    matches = create_soup(item.url).find_all("div", class_="mtos")

    for elem in matches:
        try:
            url = host + elem.a.get("href", "")
        except:
            continue
        lang = get_languages(elem.find("div", class_="didioma"))
        srv = elem.find("div", class_="dservidor").text.strip().capitalize()
        itemlist.append(Item(channel=item.channel, title=srv, url=url, action="play", server=srv, language=lang,
                             infoLabels=item.infoLabels))

    itemlist = sorted(itemlist, key=lambda i: i.language)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


def play(item):
    logger.info("play: %s" % item.url)
    itemlist = []
    if not host in item.url:
        itemlist.append(item.clone())
        itemlist = servertools.get_servers_itemlist(itemlist)

        return itemlist

    data = httptools.downloadpage(item.url, headers={'Referer': item.url}).data

    item.server = ''
    item.url = scrapertools.find_single_match(data, "location.href='([^']+)'")
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist
