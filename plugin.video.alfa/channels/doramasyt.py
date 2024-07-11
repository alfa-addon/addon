# -*- coding: utf-8 -*-
# -*- Channel DoramasYT -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
import base64
import re
import traceback
from os.path import basename

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int

from channels import filtertools
from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from core.jsontools import json
from modules import autoplay
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'la': 'LAT', 'sub': 'VOSE'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['okru', 'streamtape', 'fembed', 'uqload', 'videobin']
list_quality = []

canonical = {
             'channel': 'doramasyt', 
             'host': config.get_setting("current_host", 'doramasyt', default=''), 
             'host_alt': ["https://www.doramasyt.com/"], 
             'host_black_list': [], 
             'pattern': '<link\s*rel="shortcut\s*icon"\s*href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def create_soup(url, referer=None, unescape=False, ignore_response_code=True):
    logger.info()

    data = httptools.downloadpage(url, headers={'Referer': referer}, ignore_response_code=ignore_response_code, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def read_api(url):
    logger.info()
    
    soup = create_soup(url)
    
    caplist = soup.find("section", class_="caplist")
    url_pagination = caplist["data-ajax"]
    serie_id = basename(url_pagination)
    
    post = dict()
    post["_token"] = soup.find("meta", {"name":"csrf-token"})["content"]
    post["p"] = '1'
    
    api_url = "https://www.doramasyt.com/ajax/caplist/" + serie_id
    
    referer = host

    headers = {
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
              }

    response = httptools.downloadpage(api_url, headers=headers, post=post, referer=referer, ignore_response_code=True, hide_infobox=True)

    if response.code != 200:
        return False
    return json.loads(response.data)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="En Emisión", action="list_all", url=host + "emision",
                         thumbnail=get_thumb("on air", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Doramas", action="sub_menu", url=host + "doramas?categoria=dorama",
                         thumbnail=get_thumb("doramas", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="sub_menu", url=host + "doramas?categoria=pelicula",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", section="letra",
                         url=host + "doramas?categoria=dorama", thumbnail=get_thumb("alphabet", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section", section="fecha",
                         url=host + "doramas?categoria=dorama", thumbnail=get_thumb("year", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "buscar?q=",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all",
                         url=item.url, thumbnail=get_thumb("all", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", section="genero",
                         url=item.url, thumbnail=get_thumb("genres", auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("li", class_="col mb-3 ficha_efecto")

    for elem in matches:
        try:
            season = 0
            url = elem.a["href"]
            lang, title = clear_title(elem.find("h3").text)

            season = scrapertools.find_single_match(title, '(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season')
            if not season:
                season = scrapertools.find_single_match(title, '(?i)(?:season|temporada)\s*(\d+)')
            title = re.sub('(?i)\s*\d+\s*(?:st|nd|rd|th)\s+season', '', title)
            title = re.sub('(?i)\s*(?:season|temporada)\s*\d+', '', title)

            thumb = elem.img["data-src"]
            year = c_type = ''
            year = elem.find("span").text
            if " · " in year:
                c_type, year = elem.find("span").text.split(" · ", 1)

            new_item = Item(channel=item.channel, title=title, url=url, action="episodios", language=lang,
                            thumbnail=thumb, infoLabels={"year": year})

            if c_type.lower() in ["live action", "pelicula"] or 'pelicula' in item.url:
                new_item.contentTitle = title
                new_item.contentType = 'movie'
                if not year: new_item.infoLabels['year'] = '-'
            else:
                new_item.contentSerieName = title
                new_item.contentType = 'tvshow'
                if season: new_item.contentSeason = int(season)
        except:
            logger.error(elem)
            logger.error(traceback.format_exc())
            continue

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("a", rel="next")["href"]
        if url_next_page and len(itemlist) > 8:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))
    except:
        pass

    return itemlist


def section(item):

    itemlist = list()

    soup = create_soup(item.url)

    matches = soup.find("select", {"name": "%s" % item.section}).find_all("option")

    for elem in matches[1:]:

        url = "%s&%s=%s" % (item.url, item.section, elem["value"])
        title = elem["value"].capitalize()
        
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all"))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    infoLabels = item.infoLabels

    try:
        caplist = read_api(item.url)
        for elem in caplist["caps"]:
            url = elem["url"]
            infoLabels["season"] = item.contentSeason or 1
            infoLabels["episode"] = int(elem["episodio"])
            title = "{0}x{1} - Episodio {1}".format(infoLabels["season"], infoLabels["episode"])
            
            itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos", language=item.language,
                                 infoLabels=infoLabels))
        
        if item.contentTitle and len(itemlist) == 1:
            return findvideos(itemlist[0])
        
        tmdb.set_infoLabels_itemlist(itemlist, True)
        
        if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0 and not item.foldereps:
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                     extra1='library'))
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
    
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("button", class_="play-video")

    for elem in matches:
        url = base64.b64decode(elem["data-player"]).decode("utf-8")

        itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language=item.language,
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_idiomas)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()

    itemlist = list()

    if "monoschinos" in item.url:
        data = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(data, "file: '([^']+)'")

        itemlist.append(item.clone(url=url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)
    else:
        itemlist.append(item)

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


def clear_title(title):
    
    if 'latino' in title.lower():
        lang = 'Latino'
    elif 'castellano' in title.lower():
        lang = 'Castellano'
    else:
        lang = 'VOSE'

    title = re.sub(r'(?i)\s*(Audio|Latino|Castellano|\((.*?)\))', '', title)
    title = re.sub(r'\s:', ':', title)

    return lang, title
