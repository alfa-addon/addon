# -*- coding: utf-8 -*-
# -*- Channel AnimeFenix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools, autoplay
from channels import renumbertools
from core import tmdb


IDIOMAS = {'vose': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['directo', 'verystream', 'openload',  'streamango', 'uploadmp4', 'fembed']

host = "https://www.animefenix.com/"

def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", url=host, action="new_episodes",
                         thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Emision", url=host + 'animes?type%5B%5D=tv&estado%5B%5D=1',
                         action="list_all", thumbnail=get_thumb('on air', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Recientes", url=host, action="list_all",
                         thumbnail=get_thumb('recents', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Todas", url=host+'animes', action="list_all",
                        thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", url=host + 'animes?q=', action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def get_source(url, soup=False, referer=None, headers={}, unescape=False):
    logger.info()

    if referer: headers['referer'] = referer

    data = httptools.downloadpage(url, headers=headers).data
    data = scrapertools.unescape(data) if unescape else data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8") if soup else data

    return soup


def new_episodes(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True).find("div", class_="capitulos-grid")

    for elem in soup.find_all("div", "overarchingdiv"):
        title = elem.img["alt"]
        thumb = elem.img["src"]
        url = elem.a["href"]
        # name = elem.find("div", class_="overtitle").text
        name = title
        itemlist.append(Item(channel=item.channel, title=title, thumbnail=thumb, url=url, action="findvideos",
                             contentSerieName=name))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def episodios(item):
    logger.info()

    item.videolibrary = True
    itemlist = episodesxseason(item)
    
    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True).find("div", class_="column is-12")

    infoLabels = item.infoLabels

    for elem in soup.find_all("li"):
        url = elem.a["href"]
        epi_num = scrapertools.find_single_match(elem.span.text, "(\d+)")
        infoLabels['season'] = '1'
        infoLabels['episode'] = epi_num
        title = '1x%s - Episodio %s' % (epi_num, epi_num)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    itemlist = itemlist[::-1]

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.videolibrary:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True).find("div", class_="list-series")

    for elem in soup.find_all("article", class_="serie-card"):
        url = elem.a["href"]
        title = elem.a["title"]
        thumb = elem.img["src"]
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='episodesxseason',
                             thumbnail=thumb, contentSerieName=title, context=context))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    servers = {"6": "https://www.yourupload.com/embed/%s", "15": "https://mega.nz/embed/%s",
               "21": "https://www.burstcloud.co/embed/%s", "12": "https://ok.ru/videoembed/%s",
               "17": "https://videobin.co/embed-%s.html", "9": host + "stream/amz.php?v=%s",
               "11": host +"stream/amz.php?v=%s", "2": "https://www.fembed.com/v/%s",
               "3": "https://www.mp4upload.com/embed-%s.html", "4": "https://sendvid.com/embed/%s",
               "19": "https://videa.hu/player?v=%s"}

    soup = get_source(item.url, soup=True, unescape=True)

    pl = soup.find("div", class_="player-container")



    script = pl.find("script").text
    urls = scrapertools.find_multiple_matches(script, "src='([^']+)'")

    for url in urls:

        srv_id, v_id = scrapertools.find_single_match(url, "player=(\d+)&code=([^$]+)")
        if urllib.unquote(v_id).startswith("/"):
            v_id = v_id[1:]

        if srv_id not in servers:
            srv_data = get_source(url)
            url = scrapertools.find_single_match(srv_data, 'playerContainer.innerHTML .*?src="([^"]+)"')
        else:
            srv = servers.get(srv_id, "directo")
            if srv != "directo":
                url = srv % v_id

        if "/stream/" in url:
            data = get_source(url, referer=item.url)
            url = scrapertools.find_single_match(data, '"file":"([^"]+)"').replace('\\/', '/')
        if not url:
            continue
        url = urllib.unquote(url)
        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                             infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        try:
            return list_all(item)
        except:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
            return []

def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url=host
        itemlist = new_episodes(item)
    return itemlist
