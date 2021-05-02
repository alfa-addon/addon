# -*- coding: utf-8 -*-
# -*- Channel SeriesKao -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from lib import jsunpack
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay


IDIOMAS = {'2': 'VOSE', "0": "LAT", "1": "CAST"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'gvideo',
    'fembed',
    'directo'
    ]

host = 'https://serieskao.tv/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=host + "pelicula",
                         thumbnail=get_thumb('movies', auto=True), type="pelicula"))
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    if item.title == "Peliculas":
        itemlist.append(Item(channel=item.channel, title='Ultimas', url=item.url + "/estrenos", action='list_all',
                             thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Recomendadas', url=item.url + "/mejor-valoradas",
                         action='list_all', thumbnail=get_thumb('recomendadas', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=item.url, action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True), url=item.url))

    itemlist.append(Item(channel=item.channel, title='Años', action='section',
                         thumbnail=get_thumb('years', auto=True), url=item.url))

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def get_language(lang_data):
    logger.info()

    language = list()

    lang_list = lang_data.find_all("span", class_="flag")
    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["style"], r'/flags/(.*?).png\)')
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    return language


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    if item.title == "Generos":
        matches = soup.find("ul",  class_="Ageneros")
        base_url = "%s/filtro/?genre=%s"
    else:
        matches = soup.find("ul", class_="Ayears")
        base_url = "%s/filtro/?year=%s"

    for elem in matches.find_all("li"):
        title = elem.text
        url =  base_url % (item.url, elem["data-value"])
        itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="content").find_all("article", id=re.compile(r"^post-\d+"))

    for elem in matches:
        url = elem.a["href"]
        title = elem.img["alt"]
        thumb = elem.img["data-srcset"]
        try:
            year = elem.p.text
        except:
            year = '-'

        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})

        if "series/" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find_all("div", class_="pagMovidy")[-1].a["href"]
    except:
        return itemlist

    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", id="seasons")

    matches = soup.find_all("div", class_="clickSeason")

    infoLabels = item.infoLabels

    for elem in matches:
        season = elem["data-season"]
        title = "Temporada %s" % season
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))

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
        if elem["data-season"] != str(season):
            continue

        epi_list = elem.find("ul", class_="episodios")
        for epi in epi_list.find_all("li"):
            info = epi.find("div", class_="episodiotitle")
            url = epi.a["href"]
            epi_name = info.find("div", class_="epst").text
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
    sub = ""
    soup = create_soup(item.url)
    matches = soup.find("div", class_="navEP2")
    if not matches:
        return itemlist

    for elem in matches.find_all("li", class_="dooplay_player_option"):

        post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
                "type": elem["data-type"]}
        headers = {"Referer": item.url}
        doo_url = "%swp-admin/admin-ajax.php" % host

        data = httptools.downloadpage(doo_url, post=post, headers=headers).data

        if not data:
            continue
        player_url = BeautifulSoup(data, "html5lib").find("iframe")["src"]

        player = httptools.downloadpage(player_url, headers={"referer": item.url}).data
        soup = BeautifulSoup(player, "html5lib")
        matches = soup.find_all("li", {"onclick": True})
        lang = soup.find("li", class_="SLD_A")["data-lang"]

        for elem in matches:
            url = base64.b64decode(elem["data-r"]).decode('utf-8')

            if "animekao.club/player.php" in url:
                url = url.replace("animekao.club/player.php?x", "player.premiumstream.live/player.php?id")
            elif "animekao.club/play.php" in url:
                url = url.replace("animekao.club/play.php?x", "hls.playerd.xyz/player.php?id")
            elif "https://animekao.club/playmp4" in url:
                file_id = scrapertools.find_single_match(url, "link=([A-z0-9]+)")
                post = {'link': file_id}
                hidden_url = 'https://animekao.club/playmp4/plugins/gkpluginsphp.php'
                dict_vip_url = httptools.downloadpage(hidden_url, post=post).json
                url = dict_vip_url['link']
            elif "animekao.club/reproductores" in url:
                v_id = scrapertools.find_single_match(url, "v=([A-z0-9_-]+)")
                url = "https://drive.google.com/file/d/%s/preview" % v_id
            elif "animekao.club/mf/" in url:
                unpacked = get_unpacked(url)
                url = scrapertools.find_single_match(unpacked, '"file":"([^"]+)"')
            elif "kaodrive" in url:
                new_data = httptools.downloadpage(url, add_referer=True).data
                v_id = scrapertools.find_single_match(new_data, 'var shareId = "([^"]+)"')
                url = "https://www.amazon.com/drive/v1/shares/%s" % v_id
            elif "playhydrax.com" in url:
                slug = scrapertools.find_single_match(url, 'v=(\w+)')
                post = "slug=%s&dataType=mp4" % slug
                try:
                    data = httptools.downloadpage("https://ping.iamcdn.net/", post=post).json
                    url = data.get("url", '')
                except:
                    url = None
                if not url:
                    continue
                    url = "https://www.%s" % base64.b64decode(url[-1:]+url[:-1]).decode('utf-8')
                    url += '|Referer=https://playhydrax.com/?v=%s&verifypeer=false' % slug
            elif "kplayer" in url:
                unpacked = get_unpacked(url)
                if not unpacked:
                    continue
                url = "https://kplayer.animekao.club/%s" % scrapertools.find_single_match(unpacked, '"file":"([^"]+)"')
                url = httptools.downloadpage(url, add_referer=True, follow_redirects=False).url



            itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                                 language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels, subtitle=sub))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def get_unpacked(url):
    logger.info()
    try:
        data = httptools.downloadpage(url, headers={"referer": host}, follow_redirects=False).data
    except:
        return None

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)

    return unpacked

def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto

        if texto != '':
            return list_all(item)
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
        if categoria in ['peliculas']:
            item.url = host + 'pelicula'
        elif categoria == 'infantiles':
            item.url = host + 'pelicula/filtro/?genre=animacion-2'
        elif categoria == 'terror':
            item.url = host + 'pelicula/filtro/?genre=terror-2/'
        item.first = 0
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
