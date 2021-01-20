# -*- coding: utf-8 -*-
# -*- Channel VerAnime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import codecs

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay

IDIOMAS = {"audio castellano": "CAST", "audio latino": "LAT", "subtitulado": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ["aparatcam", "streamtape", "fembed", "mixdrop", "doodstream", "clipwatching"]

host = "https://veranime.top/"


def mainlist(item):
    logger.info()


    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Últimos Capitulos", action="latest",
                         url=host + 'episodio/',
                         thumbnail=get_thumb("new episodes", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="list_all",
                         url=host + "online/",
                         thumbnail=get_thumb("anime", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all",
                         url=host + "pelicula/",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Live Action", action="list_all",
                         url=host + "genero/live-action/",
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all",
                         url=host + "genero/audio-latino/",
                         thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all",
                         url=host + "genero/anime-castellano/",
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Blu-Ray/DVD", action="list_all",
                         url=host + "genero/blu-ray/",
                         thumbnail=get_thumb("quality", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Más Vistas", action="list_all",
                         url=host + "tendencias/",
                         thumbnail=get_thumb("more watched", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mejor Valoradas", action="list_all",
                         url=host + "ratings/",
                         thumbnail=get_thumb("more voted", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", url=host + "?s=", action="search",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    data = httptools.downloadpage(url, headers={"Referer": referer}).data

    if 'Javascript is required' in data:
        from channels import cliver
        cliver.js2py_conversion(data, ".veranime.top")
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", id="archive-content")
    for elem in matches.find_all("article", id=re.compile(r"^post-\d+")):

        info_1 = elem.find("div", class_="poster")
        info_2 = elem.find("div", class_="data")

        thumb = info_1.img["data-src"]
        title = info_1.img["alt"]
        title = re.sub("VOSE", "", title)
        url = info_1.a["href"]
        filtro_tmdb = list({"original_language": "ja"}.items())
        try:
            year = info_2.find("span", text=re.compile(r"\d{4}")).text.split(",")[-1]
        except:
            year = '-'
        new_item = Item(channel=item.channel, url=url, title=title, thumbnail=thumb,
                        infoLabels={"year": year.strip(), 'filtro': filtro_tmdb})

        if "online" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    try:
        next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action="list_all"))
    except:
        pass

    return itemlist


def latest(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="animation-2 items")

    for elem in matches.find_all("article", id=re.compile(r"^post-\d+")):
        info = elem.find("div", class_="poster")

        thumb = info.img["data-src"]
        title = re.sub('Cap \d+.*', '', info.img["alt"]).strip()
        url = info.a["href"]

        
        stitle = info.find("div", class_="epiposter").text
        stitle = stitle.replace('Episodio ', '1x')

        try:
            tag = info.find("span", class_="quality").text
        except:
            tag = ""

        ftitle = title +': '+ stitle
        if tag:
            ftitle += '[COLOR silver] (%s)[/COLOR]' % tag
        
        
        filtro_tmdb = list({"original_language": "ja"}.items())

        itemlist.append(Item(channel=item.channel, title=ftitle, url=url,
                             action="findvideos", thumbnail=thumb, 
                             contentSerieName=title))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    try:
        next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action="latest"))
    except:
        pass

    return itemlist

def seasons(item):
    logger.info()

    itemlist = list()
    page = create_soup(item.url)
    tags = get_tags(page, item.contentSerieName)
    soup = page.find("div", id="seasons")

    matches = soup.find_all("div", class_="se-c")

    infoLabels = item.infoLabels

    for elem in matches:
        season = elem.find("span", class_="se-t").text
        title = "Temporada %s %s" % (season, tags)
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             context=filtertools.context(item, list_language, list_quality), infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id="seasons")

    matches = soup.find_all("div", class_="se-c")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in matches:
        if elem.find("span", class_="se-t").text != str(season):
            continue

        epi_list = elem.find("ul", class_="episodios")
        if 'no hay episodios para' in str(epi_list):
            return itemlist
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
    itemlist2 = list()
    servers = {'fcom': 'fembed', 'dood': 'doodstream', 
                'hqq': '', 'youtube': '', 'saruch': '',
                'supervideo': '', 'aparat': 'aparatcam'}
    headers = {"Referer": item.url}

    soup = create_soup(item.url)
    matches = soup.find("ul", id="playeroptionsul")
    if not matches:
        return itemlist
    for elem in matches.find_all("li"):
        
        server = elem.find("span", class_="server").text
        server = re.sub(r"\.\w{2,4}", "", server.lower())
        server = servers.get(server, server)
        
        if not server:
            continue

        doo_url = "%swp-json/dooplayer/v1/post/%s?type=%s&source=%s" % \
                 (host, elem["data-post"], elem["data-type"], elem["data-nume"])
        
        lang = elem.find("span", class_="title").text
        lang = re.sub(r'SERVER \d+ ', '', lang)
        language=IDIOMAS.get(lang.lower(), "VOSE")

        title = '%s [%s]' % (server.capitalize(), language)
        #Sistema movidy
        if lang.lower() == 'multiserver':
            data = httptools.downloadpage(doo_url, headers=headers).json
            url = data.get("embed_url", "")
            soup = create_soup(url).find("div", class_="OptionsLangDisp")

            for elem in soup.find_all("li"):
                url = elem["onclick"]
                server = elem.find("span").text
                lang = elem.find("p").text
                
                server = re.sub(r"\.\w{2,4}", "", server.lower())
                server = servers.get(server, server)
                if not server:
                    continue

                lang = re.sub(' -.*', '', lang)
                language=IDIOMAS.get(lang.lower(), "VOSE")

                url = scrapertools.find_single_match(url, r"\('([^']+)")
                stitle = ' [%s]' % language

                if url:
                    itemlist2.append(Item(channel=item.channel, title='%s'+stitle,
                                         action="play", url=url, language=language,
                                         infoLabels=item.infoLabelss))

        else:    
            itemlist.append(Item(channel=item.channel, title=title, action="play",
                            language=language, infoLabels=item.infoLabels,
                            server=server, headers=headers, url=doo_url))
    if itemlist2:
        itemlist = servertools.get_servers_itemlist(itemlist2, lambda x: x.title % x.server.capitalize())
    else:
        itemlist.sort(key=lambda i: (i.language, i.server))

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


def search_results(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    for elem in soup.find_all("div", class_="result-item"):

        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.img["alt"]
        year = elem.find("span", class_="year").text

        new_item = Item(channel=item.channel, url=url, title=title, thumbnail=thumb,
                        infoLabels={"year": year.strip()})

        if "online" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != "":
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def play(item):
    logger.info()
    itemlist = []
    
    if not item.headers:
        return [item]
    
    url = item.url
    header = item.headers
    item.server = ''
    
    data = httptools.downloadpage(url, headers=header).json
    url = data.get("embed_url", "")
    
    if url:
          item.url = url

    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    
    return itemlist

def get_tags(page, sname):
    tags = ""
    title = page.find("title").text
    logger.error('%s(.*?)Veranime' % sname)
    match = scrapertools.find_single_match(title, r'%s\s*(.*?)\|' % sname)
    if match:
        tags = '[COLOR gold]%s[/COLOR]' % match

    return tags