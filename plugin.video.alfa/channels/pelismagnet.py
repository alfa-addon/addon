# -*- coding: utf-8 -*-

import re
import urllib

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = 'http://pelismag.net'
api = host + '/api'
api_serie = host + "/seapi"
api_temp = host + "/sapi"
__modo_grafico__ = config.get_setting("modo_grafico", "pelismagnet")


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="pelis", title="[B]Peliculas[/B]",
                         url=api + "?sort_by=''&page=0"))
    itemlist.append(Item(channel=item.channel, action="pelis", title="     Estrenos",
                         url=api + "?sort_by=date_added&page=0"))
    itemlist.append(Item(channel=item.channel, action="pelis", title="     + Populares", url=api + "?page=0"))
    itemlist.append(Item(channel=item.channel, action="pelis", title="     + Valoradas",
                         url=api + "?sort_by=rating&page=0"))
    itemlist.append(Item(channel=item.channel, action="menu_ord", title="     Ordenado por...",
                         url=api))
    itemlist.append(
        Item(channel=item.channel, action="search", title="     Buscar...", url=api + "?keywords=%s&page=0"))
    itemlist.append(Item(channel=item.channel, action="series", title="[B]Series[/B]",
                         url=api_serie + "?sort_by=''&page=0"))
    itemlist.append(Item(channel=item.channel, action="series", title="     Recientes",
                         url=api_serie + "?sort_by=date_added&page=0"))
    itemlist.append(Item(channel=item.channel, action="series", title="     + Populares", url=api_serie + "?page=0"))
    itemlist.append(Item(channel=item.channel, action="series", title="     + Valoradas",
                         url=api_serie + "?sort_by=rating&page=0"))
    itemlist.append(Item(channel=item.channel, action="menu_ord", title="     Ordenado por...",
                         url=api_serie))
    itemlist.append(Item(channel=item.channel, action="search", title="     Buscar...",
                         url=api_serie + "?keywords=%s&page=0"))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal"))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def menu_ord(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="menu_alf", title="Alfabético",
                         url=item.url))
    itemlist.append(Item(channel=item.channel, action="menu_genero", title="Género",
                         url=item.url))

    return itemlist


def menu_alf(item):
    logger.info()

    itemlist = []

    for letra in ['[0-9]', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                  'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        if 'series' in item.url:
            action = 'series'
        else:
            action = 'pelis'
        itemlist.append(Item(channel=item.channel, action=action, title=letra,
                             url=item.url + "?keywords=^" + letra + "&page=0"))

    return itemlist


def menu_genero(item):
    logger.info()

    itemlist = []
    # TODO: SOLO FUNCIONA POR AHORA A PARTIR DE KODI 17
    # httptools.downloadpage("https://kproxy.com/")
    # url = "https://kproxy.com/doproxy.jsp"
    # post = "page=%s&x=34&y=14" % urllib.quote(host + "/principal")
    # response = httptools.downloadpage(url, post, follow_redirects=False).data
    # url = scrapertools.find_single_match(response, '<meta http-equiv="refresh".*?url=([^"]+)"')
    data = httptools.downloadpage(host + "/principal").data

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)

    data = scrapertools.find_single_match(data, '<ul class="dropdown-menu.*?>(.*?)</ul>')
    patron = '<li><a href="genero/([^"]+)">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for genero, nombre in matches:
        itemlist.append(Item(channel=item.channel, action="series", title=nombre,
                             url=item.url + "?genre=" + genero + "&page=0"))

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    # TODO: SOLO FUNCIONA POR AHORA A PARTIR DE KODI 17
    # httptools.downloadpage("https://kproxy.com/")
    # url = "https://kproxy.com/doproxy.jsp"
    # post = "page=%s&x=34&y=14" % urllib.quote(item.url)
    # response = httptools.downloadpage(url, post, follow_redirects=False).data
    # url = scrapertools.find_single_match(response, '<meta http-equiv="refresh".*?url=([^"]+)"')
    data = httptools.downloadpage(item.url).data
    pos = data.find('[')
    if pos > 0: data = data[pos:]

    lista = jsontools.load(data)
    logger.debug(lista)
    if item.extra == "next":
        lista_ = lista[25:]
    else:
        lista_ = lista[:25]

    for i in lista_:

        punt = i.get("puntuacio", "")
        valoracion = ""
        if punt and not 0:
            valoracion = "  (Val: %s)" % punt

        title = "%s%s" % (i.get("nom", ""), valoracion)
        url = "%s?id=%s" % (api_temp, i.get("id", ""))

        thumbnail = ""
        fanart = ""
        if i.get("posterurl", ""):
            thumbnail = "http://image.tmdb.org/t/p/w342%s" % i.get("posterurl", "")
        if i.get("backurl", ""):
            fanart = "http://image.tmdb.org/t/p/w1280%s" % i.get("backurl", "")

        plot = i.get("info", "")
        if plot is None:
            plot = ""

        infoLabels = {'plot': plot, 'year': i.get("year"), 'tmdb_id': i.get("id"), 'mediatype': 'tvshow'}

        itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url,
                             thumbnail=thumbnail, fanart=fanart, infoLabels=infoLabels, contentTitle=i.get("nom"),
                             show=i.get("nom")))

    from core import tmdb
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if len(lista_) == 25 and item.extra == "next":
        url = re.sub(r'page=(\d+)', r'page=' + str(int(re.search('\d+', item.url).group()) + 1), item.url)
        itemlist.append(Item(channel=item.channel, action="series", title=">> Página siguiente", url=url))
    elif len(lista_) == 25:
        itemlist.append(
            Item(channel=item.channel, action="series", title=">> Página siguiente", url=item.url, extra="next"))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    # TODO: SOLO FUNCIONA POR AHORA A PARTIR DE KODI 17
    # httptools.downloadpage("https://kproxy.com/")
    # url = "https://kproxy.com/doproxy.jsp"
    # post = "page=%s&x=34&y=14" % urllib.quote(item.url)
    # response = httptools.downloadpage(url, post, follow_redirects=False).data
    # url = scrapertools.find_single_match(response, '<meta http-equiv="refresh".*?url=([^"]+)"')
    logger.debug(item)
    data = httptools.downloadpage(item.url).data
    pos = data.find('[')
    if pos > 0: data = data[pos:]

    data = jsontools.load(data)

    dict_episodes = dict()

    for i in data.get("temporadas", []):

        for j in i.get("capituls", []):

            numero = j.get("infocapitul", "%sx%s" % (i.get("numerotemporada", 0), j.get("numerocapitul", 0)))

            if numero not in dict_episodes:
                dict_episodes[numero] = {}
                dict_episodes[numero]["title"] = j.get("nomcapitul", "Episodio %s" % j.get("numerocapitul", ""))

                season = i.get("numerotemporada", 0)
                if type(season) == str:
                    season = 0
                dict_episodes[numero]["season"] = season

                episode = j.get("numerocapitul", 0)
                if type(episode) == str:
                    episode = 0
                dict_episodes[numero]["episode"] = episode

                if j.get("links", {}).get("magnet"):
                    dict_episodes[numero]["url"] = [j.get("links", {}).get("magnet")]
                    dict_episodes[numero]["quality"] = [j.get("links", {}).get("calitat", "")]

                dict_episodes[numero]["plot"] = j.get("overviewcapitul", "")

            else:
                if dict_episodes[numero]["title"] == "":
                    dict_episodes[numero]["title"] = j.get("nomcapitul", "Episodio %s" % j.get("numerocapitul", ""))

                if j.get("links", {}).get("magnet"):
                    dict_episodes[numero]["url"].append(j.get("links", {}).get("magnet"))
                    dict_episodes[numero]["quality"].append(j.get("links", {}).get("calitat", ""))

                if dict_episodes[numero]["plot"] == "":
                    dict_episodes[numero]["plot"] = j.get("overviewcapitul", "")

    for key, value in dict_episodes.items():
        list_no_duplicate = list(set(value["quality"]))
        title = "%s %s [%s]" % (key, value["title"], "][".join(list_no_duplicate))

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, url=dict_episodes[numero]["url"],
                 thumbnail=item.thumbnail, fanart=item.fanart, show=item.show, data=value,
                 contentSerieName=item.contentTitle, contentSeason=value["season"],
                 contentEpisodeNumber=value["episode"]))

    # order list
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

    return itemlist


def pelis(item):
    logger.info()

    itemlist = []
    # TODO: SOLO FUNCIONA POR AHORA A PARTIR DE KODI 17
    # httptools.downloadpage("https://kproxy.com/", add_referer=True)
    # url = "https://kproxy.com/doproxy.jsp"
    # post = "page=%s&x=34&y=14" % urllib.quote(item.url)
    # response = httptools.downloadpage(url, post, follow_redirects=False).data
    # url = scrapertools.find_single_match(response, '<meta http-equiv="refresh".*?url=([^"]+)"')
    data = httptools.downloadpage(item.url).data
    pos = data.find('[')
    if pos > 0: data = data[pos:]

    lista = jsontools.load(data)
    if item.extra == "next":
        lista_ = lista[25:]
    else:
        lista_ = lista[:25]

    for i in lista_:
        punt = i.get("puntuacio", "")
        valoracion = ""

        if punt and not 0:
            valoracion = "  (Val: %s)" % punt

        if i.get("magnets", {}).get("M1080", {}).get("magnet", ""):
            url = i.get("magnets", {}).get("M1080", {}).get("magnet", "")
            calidad = "%s" % i.get("magnets", {}).get("M1080", {}).get("quality", "")
        else:
            url = i.get("magnets", {}).get("M720", {}).get("magnet", "")
            calidad = "%s" % (i.get("magnets", {}).get("M720", {}).get("quality", ""))

        if not url:
            continue

        title = "%s %s%s" % (i.get("nom", ""), valoracion, calidad)

        thumbnail = ""
        fanart = ""
        if i.get("posterurl", ""):
            thumbnail = "http://image.tmdb.org/t/p/w342%s" % i.get("posterurl", "")
        if i.get("backurl", ""):
            fanart = "http://image.tmdb.org/t/p/w1280%s" % i.get("backurl", "")

        plot = i.get("info", "")
        if plot is None:
            plot = ""
        infoLabels = {'plot': plot, 'year': i.get("year"), 'tmdb_id': i.get("id")}

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, server="torrent",
                             contentType="movie", thumbnail=thumbnail, fanart=fanart, infoLabels=infoLabels,
                             contentTitle=i.get("nom"), quality=calidad))

    from core import tmdb
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if len(lista_) == 25 and item.extra == "next":
        url = re.sub(r'page=(\d+)', r'page=' + str(int(re.search('\d+', item.url).group()) + 1), item.url)
        itemlist.append(Item(channel=item.channel, action="pelis", title=">> Página siguiente", url=url))
    elif len(lista_) == 25:
        itemlist.append(
            Item(channel=item.channel, action="pelis", title=">> Página siguiente", url=item.url, extra="next"))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = item.url % texto.replace(' ', '%20')
        if "/seapi" in item.url:
            return series(item)
        else:
            return pelis(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info()

    itemlist = []

    if item.contentType == "movie":
        item.title = "Enlace Torrent"
        item.action = "play"
        itemlist.append(item)
    else:
        data = item.data

        for index, url in enumerate(data["url"]):
            quality = data["quality"][index]
            title = "Enlace torrent [%s]" % quality
            itemlist.append(item.clone(action="play", title=title, url=url, quality=quality))
            servertools.get_servers_itemlist(itemlist)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = api + "?sort_by=''&page=0"

            itemlist = pelis(item)
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()
            item.url = api_serie + "?sort_by=''&page=0"
            itemlist.extend(series(item))
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

