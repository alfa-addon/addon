# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger

host = "https://grantorrent.com/"

dict_url_seasons = dict()
__modo_grafico__ = config.get_setting('modo_grafico', 'grantorrent')


def mainlist(item):
    logger.info()

    thumb_movie = get_thumb("channels_movie.png")
    thumb_tvshow = get_thumb("channels_tvshow.png")

    itemlist = list()
    itemlist.append(
        Item(channel=item.channel, title="Peliculas", action="peliculas", thumbnail=thumb_movie))
    itemlist.append(
        Item(channel=item.channel, title="Series", action="series", thumbnail=thumb_tvshow))

    return itemlist


def peliculas(item):
    logger.info()

    thumb_search = get_thumb("search.png")

    itemlist = list()
    itemlist.append(item.clone(channel=item.channel, title="Novedades", action="listado", url=host))
    # itemlist.append(item.clone(channel=item.channel, title="Filtrar películas", action="listado", url=host))
    itemlist.append(item.clone(channel=item.channel, title="Buscar", action="search", url=host, media="película",
                               thumbnail=thumb_search))

    return itemlist


def series(item):
    logger.info()

    thumb_search = get_thumb("search.png")

    itemlist = list()
    itemlist.append(item.clone(channel=item.channel, title="Novedades", action="listado", url=host + "series/"))
    # itemlist.append(item.clone(channel=item.channel, title="Filtrar series", action="listado", url=host))
    itemlist.append(item.clone(channel=item.channel, title="Buscar", action="search", url=host + "series/",
                               media="serie", thumbnail=thumb_search))

    return itemlist


def search(item, texto):
    logger.info("texto:" + texto)
    texto = texto.replace(" ", "+")
    itemlist = []

    try:
        url = "%s?s=%s" % (item.url, texto)
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(url).data)
        # logger.debug("data %s \n\n" % data)

        video_section = scrapertools.find_single_match(data, '<div class="contenedor-imagen">(.*?</div>)</div></div>')

        pattern = '<a href="(?P<url>[^"]+)"><img.*?src="(?P<thumb>[^"]+)".*?class="bloque-inferior">' \
                  '\s*(?P<title>.*?)\s*</div>'

        matches = re.compile(pattern, re.DOTALL).findall(video_section)

        for url, thumb, title in matches:
            if item.media == "serie":
                action = "episodios"
            else:
                action = "findvideos"
            itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumb,
                                 contentTitle=title, contentType="movie"))

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def listado(item):
    logger.info()

    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    # logger.debug("data %s \n\n" % data)

    video_section = scrapertools.find_single_match(data, '<br><div class="contenedor-home">(.*?</div>)</div></div>')
    # logger.debug("data %s \n\n" % video_section)

    pattern = '<a href="(?P<url>[^"]+)"><img.*?src="(?P<thumb>[^"]+)".*?.*?class="bloque-superior">\s*' \
              '(?P<quality>.*?)\s*<div class="imagen-idioma">\s*<img src=".*?icono_(?P<lang>[^\.]+).*?<div class=' \
              '"bloque-inferior">\s*(?P<title>.*?)\s*</div><div class="bloque-date">\s*(?P<date>.*?)\s*</div>'

    matches = re.compile(pattern, re.DOTALL).findall(video_section)

    for url, thumb, quality, lang, title, date in matches:
        title = scrapertools.htmlclean(title)
        title = re.sub(r"\s{2}", " ", title)

        if "/series" in item.url:
            if quality:
                title2 = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="episodios", title=title2, url=url, thumbnail=thumb,
                                 quality=quality, contentTitle=title, contentType="tvshow"))
        else:

            if quality:
                title2 = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title2, url=url, thumbnail=thumb,
                                 quality=quality, contentTitle=title, contentType="movie"))

    pagination = scrapertools.find_single_match(data, '<div class="nav-links">(.*?)</ul>')
    if pagination:
        next_page = scrapertools.find_single_match(pagination, "class='page-numbers current'.*?<a.*?href='([^']+)'")
        # logger.debug("next %s" % next_page)
        if next_page:
            itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente", url=next_page,
                                 thumbnail=get_thumb("next.png")))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    dict_data = dict()
    dict_data, item = get_episodes(item, dict_data)

    for key in dict_data.keys():
        d = dict_data[key]
        quality = "[%s]" % "][".join(d["quality"])

        d["s_e"] = re.sub(r"\(Contrase.*?\)\s*", "NO REPRODUCIBLE-RAR", d["s_e"])
        title = "%s [%s] %s" % (d["s_e"], d["lang"], quality)
        # logger.debug("%s" % d["s_e"])

        if "temporada" in d["s_e"].lower():
            regex = re.compile('temporada\s*', re.I)
            d["s_e"] = regex.sub("", d["s_e"])
            season = scrapertools.find_single_match(d["s_e"], "(\d+)")
            episode = 1
        else:
            season, episode = scrapertools.find_single_match(d["s_e"], "(\d+)&#215;(\d+)")

        itemlist.append(item.clone(action="findvideos", title=title, thumbnail=item.thumbnail, url=d["url"],
                                   server="torrent", contentSeason=season, contentEpisodeNumber=episode,
                                   contentType="tvshow", fulltitle=item.title, quality=d["quality"], lang=d["lang"]))

    # order list
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    except:
        pass

    return itemlist


def get_episodes(item, dict_data):
    global dict_url_seasons

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    # logger.debug("data %s \n\n" % data)
    if item.contentTitle != "":
        title = scrapertools.find_single_match(data, '<h3 class="bold">.*?original:\s*(.*?)[.]</h3>')
        year = scrapertools.find_single_match(data, '<h3 class="bold">\s*Estreno:\s*(\d+)[.]</h')
        # logger.debug("title es %s" % title)
        if title:
            item.contentTitle = title
            item.show = title
        if year:
            item.infoLabels['year'] = year

    links_section = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')
    # logger.debug("data %s \n\n" % links_section)

    pattern = 'icono_.*?png" title="(?P<lang>.*?)" [^>]+></td><td>(?P<s_e>.*?)</td><td>(?P<quality>.*?)</td><td>' \
              '<a class="link" href="(?P<url>[^"]+)"'
    matches = re.compile(pattern, re.DOTALL).findall(links_section)
    for lang, s_e, quality, url in matches:
        if s_e + lang not in dict_data:
            dict_data[s_e + lang] = {"url": [url], "lang": lang, "s_e": s_e,
                                     "quality": [quality]}
        else:
            if quality not in dict_data[s_e+lang]["quality"]:
                dict_data[s_e + lang]["quality"].append(quality)
                dict_data[s_e + lang]["url"].append(url)

    url_to_check = scrapertools.find_single_match(links_section, '</table><p><a.*?href="([^"]+)".*?>\s*Temporada.*?</a>')
    # logger.debug("url es %s " % url_to_check)

    # if url doesn't exist we add it into the dict
    if url_to_check and url_to_check not in dict_url_seasons:
        dict_url_seasons[url_to_check] = False

    for key, value in dict_url_seasons.items():
        if not value:
            item.url = key
            dict_url_seasons[key] = True
            dict_data, item = get_episodes(item, dict_data)

    # logger.debug("URL_LIST es %s " % dict_url_seasons)

    return dict_data, item


def findvideos(item):
    logger.info()
    itemlist = []

    if item.contentType == "movie":

        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
        # logger.debug("data %s \n\n" % data)

        if item.contentTitle != "":
            title = scrapertools.find_single_match(data, '<div class="titulo_page_exit">(.*?)[.]</div>')
            year = scrapertools.find_single_match(data, '<div class="ano_page_exit">(\d+)</div>')
            logger.debug("title es %s" % title)
            if title:
                item.contentTitle = title
                item.show = title
            if year:
                item.infoLabels['year'] = year

        links_section = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')
        # logger.debug("data %s \n\n" % data)

        pattern = 'icono_.*?png" title="(?P<lang>.*?)" [^>]+></td><td>(?P<quality>.*?)</td><td>(?P<size>.*?)</td><td>' \
                  '<a class="link" href="(?P<url>[^"]+)"'
        matches = re.compile(pattern, re.DOTALL).findall(links_section)

        for lang, quality, size, url in matches:
            title = "[%s] [%s] (%s)" % (lang, quality, size)

            itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=item.thumbnail, server="torrent",
                                       fulltitle=item.title))

        try:
            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        except:
            pass

    else:
        for index, url in enumerate(item.url):
            title = "%sx%s [%s] [%s]" % (item.contentSeason, item.contentEpisodeNumber, item.lang, item.quality[index])
            itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=item.thumbnail, server="torrent",
                                       quality=item.quality[index]))

    return itemlist
