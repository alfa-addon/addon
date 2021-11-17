# -*- coding: utf-8 -*-
# -*- Channel 123Pelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import codecs

from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DooPlay

IDIOMAS = {"es": "CAST", "mx": "LAT", "en": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ["directo", "fembed", "mixdrop", "doodstream", "clipwatching", "cloudvideo"]

host = "https://123pelis.fun/"
AlfaChannel = DooPlay(host, tv_path="/serie")


def mainlist(item):
    logger.info()


    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="sub_menu",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu",
                         thumbnail=get_thumb("tvshows", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", url=host + "tag/castellano", action="list_all",
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", url=host + "tag/latino", action="list_all",
                         thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", url=host + "tag/subtitulado", action="list_all",
                         thumbnail=get_thumb("vose", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", url=host + "?s=", action="search",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()
    if item.title == "Peliculas":
        get_type = "movies"
    else:
        get_type = "tv"

    itemlist.append(Item(channel=item.channel, title="Todas", url=host+item.title.lower()[:-1], action="list_all",
                         thumbnail=get_thumb("all", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mas Vistas", url=host + "tendencias/?get=%s" % get_type,
                         action="list_all", thumbnail=get_thumb("more watched", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Netflix", url=host + "tag/%s-netflix" % item.title.lower()[:-1],
                         action="list_all", thumbnail=get_thumb("more watched", auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, postprocess=set_filter)


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item)


def episodesxseason(item):
    logger.info()

    return AlfaChannel.episodes(item)


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup, matches = AlfaChannel.get_video_options(item.url)
    if not matches:
        return itemlist
    for elem in matches:
        if "youtube" in elem.find("span", class_="server").text:
            continue

        data = AlfaChannel.get_data_by_post(elem).json

        lang = elem.find("span", class_="flag").img["data-src"]
        lang = scrapertools.find_single_match(lang, r"flags/([^\.]+)\.png")

        if not data:
            continue
        url = data["embed_url"]
        if "hideload" in url:
            url = unhideload(url)
        if "pelis123" in url:
            itemlist.extend(get_premium(item, url, lang))
        elif not "onlystream" in url:
            if "zplayer" in url:
                url += "|referer=%s" % host
            itemlist.append(Item(channel=item.channel, title="%s", action="play", url=url,
                                 language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))
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


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != "":
            return AlfaChannel.search_results(item)
        else:
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
        if categoria in ["peliculas"]:
            item.url = host + "pelicula"
        elif categoria == "castellano":
            item.url = host + "tag/castellano"
        elif categoria == "latino":
            item.url = host + "tag/latino"
        itemlist = list_all(item)

        if itemlist[-1].title == "Siguiente >>":
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_premium(item, url, lang):
    logger.info()

    itemlist = list()

    from lib.generictools import dejuice
    try:
        data = httptools.downloadpage(url, timeout=5).data
        dejuiced = dejuice(data)
    except:
        return itemlist
    
    patron = r'"file":"([^"]+)","label":"(\d+P)"'
    matches = re.compile(patron, re.DOTALL).findall(dejuiced)
    for url, qlty in matches:
        itemlist.append(Item(channel=item.channel, title="%s", action="play", url=url,
                             language=IDIOMAS.get(lang, "VOSE"), quality=qlty, infoLabels=item.infoLabels))

    return itemlist


def unhideload(url):
    logger.info()
    server_dict = {"ad": "https://videobin.co/embed-",
                   "jd": "https://clipwatching.com/embed-",
                   #"vd": "https://jetload.net/e/",
                   "ud": "https://dood.watch/e/",
                   "ld": "https://dood.watch/e/",
                   "gd": "https://mixdrop.co/e/",
                   "hd": "https://stream.kiwi/e/",
                   "kd": "https://play.pelis123.fun/e/",
                   "pd": "https://cloudvideo.tv/embed-",
                   "md": "https://feurl.com/v/",
                   }

    server = scrapertools.find_single_match(url, r"(\wd)=")
    server = server_dict.get(server, server)
    hash_ = url.split("=")[1].split("&")[0]
    inv = hash_[::-1]
    result = codecs.decode(inv, "hex").decode("utf-8")
    url = "%s%s" % (server, result)

    return url


def set_filter(*args):
    logger.info()

    args[2].context = filtertools.context(args[3], list_language, list_quality)

    return args[2]