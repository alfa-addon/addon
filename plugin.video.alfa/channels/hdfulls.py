# -*- coding: utf-8 -*-
# -*- Channel HDFullS -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from builtins import chr
from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    from lib import alfaresolver_py3 as alfaresolver
else:
    from lib import alfaresolver

import re
from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


IDIOMAS = {'lat': 'LAT', 'spa': 'CAST', 'esp': 'CAST', 'sub': 'VOSE', 'espsub': 'VOSE', 'engsub': 'VOS', 'eng': 'VO'}
#IDIOMAS = {'lat': 'LAT', 'spa': 'CAST', 'espsub': 'VOSE', 'engsub': 'VOS', 'eng': 'VO'}
list_language = list(set(IDIOMAS.values()))
list_quality = ['HD1080', 'HD720', 'HDTV', 'DVDRIP', 'RHDTV', 'DVDSCR']
list_servers = ['flix555', 'clipwatching', 'gamovideo', 'powvideo', 'streamplay', 'vidoza', 'vidtodo', 'uptobox']

host = "https://hdfull.fm"


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, action="menupeliculas", title="Películas", url=host,
                         thumbnail=get_thumb('movies', auto=True), text_bold=True))
    itemlist.append(Item(channel=item.channel, action="menuseries", title="Series", url=host,
                         thumbnail=get_thumb('tvshows', auto=True), text_bold=True))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail=get_thumb('search', auto=True), text_bold=True))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

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


def get_source(url, referer=host, post=None):
    logger.info()
    if post:
        data = httptools.downloadpage(url, post=post, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data

    return data


def menupeliculas(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="list_all", title="Últimas Películas", url=host + "/movies",
                         thumbnail=get_thumb('last', auto=True), first=1))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas Estreno",
                         url=host + "/new-movies",  thumbnail=get_thumb('premieres', auto=True), first=1))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Películas Actualizadas",
                         url=host + "/updated-movies", thumbnail=get_thumb('updated', auto=True),
                         mode="movies", first=1))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Rating IMDB",
                         url=host + "/movies/imdb_rating", thumbnail=get_thumb('recomended', auto=True),
                         mode="movies", first=1))

    itemlist.append(Item(channel=item.channel, action="genres", title="Películas por Género",
                         thumbnail=get_thumb('genres', auto=True), tag='movies'))

    return itemlist


def menuseries(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="list_all", title="Últimas series", url=host + "/tv-shows",
                         thumbnail=get_thumb('last', auto=True), first=1))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Novelas Estreno",
                         url=host + "/tv-tags/soap", first=1,
                         thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Animes Estreno",
                         url=host + "/tv-tags/anime", first=1,
                         thumbnail=get_thumb('anime', auto=True)))

    itemlist.append(Item(channel=item.channel, action="list_all", title="Rating IMDB", url=host + "/tv-shows/imdb_rating",
                         thumbnail=get_thumb('recomended', auto=True), first=1))

    itemlist.append(Item(channel=item.channel, action="genres", title="Series por Género", url=host,
                         thumbnail=get_thumb('genres', auto=True), tag="tv"))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()
    next = True
    if not item.url.startswith(host):
        item.url = host+item.url
    if item.post:
        soup = BeautifulSoup(get_source(item.url, post=item.post), "html5lib", from_encoding="utf-8")
    else:
        soup = create_soup(item.url, referer=host)

    matches = soup.find_all("div", class_="span-6 inner-6 tt view")

    first = item.first
    last = first + 20

    if last > len(matches):
        last = len(matches)
        next = False

    for elem in matches[first:last]:
        lang = list()
        url = elem.a["href"]
        title = elem.find("a", class_="link")["title"]
        title = re.sub(r"\..*", "", title)
        thumb = elem.img["src"]

        new_item = Item(channel=item.channel, title=title, url=host+url, thumbnail=thumb, infoLabels={})

        if '/show/' in url:
            new_item.contentSerieName = title
            new_item.action = 'seasons'
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            lang_data = elem.find("div", class_="left").find_all("img")
            for l in lang_data:
                if l["src"]:

                    lang.append(IDIOMAS.get(lang_from_flag(l["src"], "/static/style/images/", "png"), ''))

            new_item.language = lang
            new_item.contentTitle = title
            new_item.infoLabels["year"] = "-"
            new_item.action = 'findvideos'

        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, True)

    if next:
        url_next_page = item.url
        first = last
    else:
        try:
            url_next_page = host + soup.find("ul", id="filter").find("a", class_="current").next_sibling["href"]
        except:
          url_next_page = False
          pass
        first = 0

    if url_next_page and len(matches) > 20:
        itemlist.append(Item(channel=item.channel,title="Siguiente >>", url=url_next_page, action='list_all',
                             first=first))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    data = get_source(item.url)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    matches = soup.find("ul", class_="filter")

    infoLabels = item.infoLabels

    for elem in matches.find_all("li"):

        season = elem.a.text.lower()

        if "todas" in season:
            continue
        elif season == "especiales":
            season = "0"
        infoLabels["season"] = season
        title = 'Temporada %s' % season
        url = host + elem.a["href"]

        itemlist.append(Item(channel=item.channel, title=title, url=url, action="episodesxseason", season=season,
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and itemlist and not item.videolibrary:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(60352)), url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    item.videolibrary = True
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = list()

    soup = create_soup(item.url, referer=host).find("div", id="season-episodes")
    matches = soup.find_all("div", class_="show-view")
    infoLabels = item.infoLabels

    for elem in matches:
        url = host + elem.a["href"]
        epi_num = scrapertools.find_single_match(url, "episode-(\d+)")
        infoLabels["episode"] = epi_num
        title = "%sx%s" % (infoLabels["season"], epi_num)
        itemlist.append(Item(channel=item.channel, url=url, action="findvideos", infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = sorted(itemlist, key=lambda i: i.language)
    return itemlist


def genres(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host, host).find_all("li", class_="dropdown")
    if "Películas" in item.title:
        matches = soup[1].find_all("li")
    else:
        matches = soup[0].find_all("li")

    for elem in matches:
        url = elem.a["href"]
        title = elem.text.strip()
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all", first=1))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    data = get_source(item.url)

    js_data = get_source("%s/static/style/js/jquery.hdfull.view.min.js" % host)

    data_js = get_source("%s/static/js/providers.js" % host)
    decoded = alfaresolver.jhexdecode(data_js).replace("'", '"')
    providers_pattern = 'p\[(\d+)\]\s?=\s?{"t":"([^"]+)","d":".*?","e":.function.*?,"l":.function.*?return "([^"]+)".*?};'
    providers = scrapertools.find_multiple_matches(decoded, providers_pattern)

    provs = {}

    for provider, e, l in providers:
        provs[provider] = [e, l]

    #try:
    data_decrypt = jsontools.load(alfaresolver.obfs(data, js_data))
    #except:
    #    return itemlist

    infolabels = item.infoLabels
    year = scrapertools.find_single_match(data, '<span>A&ntilde;o:\s*</span>.*?(\d{4})')
    infolabels["year"] = year

    matches = []

    for match in data_decrypt:
        if match['provider'] in provs:
            try:
                embed = provs[match['provider']][0]
                url = provs[match['provider']][1] + match['code']
                matches.append([match['lang'], match['quality'], url, embed])
            except:
                pass

    for idioma, calidad, url, embed in matches:
        idioma = IDIOMAS.get(idioma.lower(), idioma)
        calidad = unicode(calidad, "utf8").upper().encode("utf8")
        title = "%s (" + calidad + ")(" + idioma + ")"

        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url,
                             infoLabels=item.infoLabels, language=idioma, contentType=item.contentType,
                             quality=calidad))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda i: i.language)
    if config.get_videolibrary_support() and itemlist and not item.contentSerieName and not item.extra:
            itemlist.append(Item(channel=item.channel, title='[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(60353)),
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle=item.contentTitle, infoLabels=item.infoLabels, extra="findvideos"
                                 ))

    return itemlist


def lang_from_flag(lang_data, path, ext):
    logger.info()
    language = []
    """
    Obtiene los idiomas desde banderas en formatos del tipo url imagen por ejemplo "/img/banderas/es.png"

    lang_data: string conteniendo los idiomas puede ser 1 o mas
    path: string con la url donde se encuentra la bandera
    ext: string con la extension de la imagen sin el punto por ejemplo png

    Retorna una lista de idiomas si hubiese mas de 1 o un string en caso de ser solo 1
        """

    lang_list = scrapertools.find_multiple_matches(lang_data, '%s(.*?).%s' % (path, ext))
    if len(lang_list) == 1:
        return str(lang_list[0])
    else:
        for lang in lang_list:
            language.append(str(lang))
    return language


def search(item, texto):
    logger.info()

    try:
        item.post = {"menu": "search", "query": texto}
        item.title = "Buscar..."
        item.url = host + "/search"
        item.texto = texto
        item.first = 0
        return list_all(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []