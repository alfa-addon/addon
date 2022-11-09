# -*- coding: utf-8 -*-
# -*- Channel Cuevana2Español -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import base64
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DooPlay

list_language = ["LAT", "CAST"]
list_quality = []
list_servers = ['fembed', 'streamtape', 'streamlare', 'zplayer']

canonical = {
             'channel': 'cuevana2espanol', 
             'host': config.get_setting("current_host", 'cuevana2espanol', default=''), 
             'host_alt': ["https://cuevana2espanol.com/"], 
             'host_black_list': [], 
             'pattern': '<link\s*rel="alternate"\s*type="[^"]+"\s*title="[^"]+"\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = DooPlay(host, movie_path="ver-pelicula-online/", canonical=canonical)


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Ultimas", url=host + 'ver-pelicula-online/', action="list_all",
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Destacadas", url=host + 'calificaciones/', action="list_all",
                         thumbnail=get_thumb('destacadas', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mas Vistas", url=host + 'tendencias/', action="list_all",
                         thumbnail=get_thumb('more watched', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabético", url=host, action="alpha",
                         thumbnail=get_thumb('alphabet', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", url=host + '?s=', action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def alpha(item):
    logger.info()

    itemlist = list()
    letters = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for letter in letters:
        itemlist.append(Item(channel=item.channel, title=letter, letter=letter.lower(), action="list_alpha"))

    return itemlist


def list_alpha(item):
    logger.info()

    itemlist = list()
    base_url = "https://cuevana2espanol.com/wp-json/dooplay/glossary/?term=%s&nonce=4a91f28386&type=all" % item.letter
    json_data = httptools.downloadpage(base_url).json
    for elem in json_data.values():

        itemlist.append(Item(channel=item.channel, title=elem["title"], url=elem["url"], action="findvideos",
                             thumbnail=elem["img"], contentTitle=elem["title"], infoLabels={"year": elem["year"]}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    srv_dict = {"clase b": "fembed", "hqq": "netu", "clase z": "zplayer"}
    soup = AlfaChannel.create_soup(item.url)
    matches = soup.find_all("a", class_="options")

    for elem in matches:
        opt = elem["href"][1:]
        lang = "LAT" if item.infoLabels["original_language"] != "es" else "CAST"
        srv = re.sub("servidor", "", elem.text.lower()).strip()

        v_url = scrapertools.find_single_match(soup.find("div", id=opt).iframe["src"], 'h=([^"]+)')
        url = ""
        if not v_url:
            v_url = scrapertools.find_single_match(soup.find("div", id=opt).iframe["src"], 'url=([^"]+)').encode("utf-8")
            url = base64.urlsafe_b64decode(v_url + b"==" if PY3 else "==")

        if srv in srv_dict.keys():
            srv = srv_dict[srv]
        itemlist.append(Item(channel=item.channel, title=srv.capitalize(), action='play', url=url, v_url=v_url,
                             server=srv.capitalize(), language=lang, infoLabels=item.infoLabels))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()

    if not item.url:
        item.server = ""
        p_url = "https://player.cuevana2espanol.com/sc/r.php"
        item.url = httptools.downloadpage(p_url, post={"h": item.v_url}, follow_redirects=False).headers["location"]
        itemlist = servertools.get_servers_itemlist([item])
    elif item.server.lower() == "zplayer":
        item.url += "|referer=%s" % host
        itemlist = [item]
    
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        if texto != '':
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
        if categoria == 'peliculas':
            item.url = host + 'ver-pelicula-online'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist