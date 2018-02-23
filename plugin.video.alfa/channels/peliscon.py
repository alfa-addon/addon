# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

__modo_grafico__ = config.get_setting('modo_grafico', "peliscon")

host = "http://peliscon.com"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        item.clone(title="[COLOR aqua][B]Películas[/B][/COLOR]", action="scraper", url= host + "/peliculas/",
                   thumbnail="http://imgur.com/FrcWTS8.png", fanart="http://imgur.com/MGQyetQ.jpg",
                   contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR aqua][B]Series[/B][/COLOR]", action="scraper",
                                       url= host + "/series/", thumbnail="http://imgur.com/FrcWTS8.png",
                                       fanart="http://imgur.com/i41eduI.jpg", contentType="tvshow"))
    itemlist.append(item.clone(title="[COLOR aqua][B]       Últimos capitulos[/B][/COLOR]", action="ul_cap",
                               url= host + "/episodios/", thumbnail="http://imgur.com/FrcWTS8.png",
                               fanart="http://imgur.com/i41eduI.jpg", contentType="tvshow"))
    itemlist.append(itemlist[-1].clone(title="[COLOR crimson][B]Buscar[/B][/COLOR]", action="search",
                                       thumbnail="http://imgur.com/FrcWTS8.png", fanart="http://imgur.com/h1b7tfN.jpg"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=" + texto
    item.extra = "search"
    try:
        return buscador(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def buscador(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = scrapertools.find_multiple_matches(data,
                                                '<div class="result-item">.*?href="([^"]+)".*?alt="([^"]+)".*?<span class=".*?">([^"]+)</span>.*?<span class="year">([^"]+)</span>')
    for url, title, genere, year in patron:
        if "Serie" in genere:
            checkmt = "tvshow"
            genere = "[COLOR aqua][B]" + genere + "[/B][/COLOR]"
        else:
            checkmt = "movie"
            genere = "[COLOR cadetblue][B]" + genere + "[/B][/COLOR]"
        titulo = "[COLOR crimson]" + title + "[/COLOR]" + " [ " + genere + " ] "
        if checkmt == "movie":
            new_item = item.clone(action="findvideos", title=titulo, url=url, fulltitle=title, contentTitle=title,
                                  contentType="movie", library=True)
        else:
            new_item = item.clone(action="findtemporadas", title=titulo, url=url, fulltitle=title, contentTitle=title,
                                  show=title, contentType="tvshow", library=True)
        new_item.infoLabels['year'] = year
        itemlist.append(new_item)
    try:
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for item in itemlist:
            if not "Siguiente >>" in item.title:
                if "0." in str(item.infoLabels['rating']):
                    item.infoLabels['rating'] = "[COLOR indianred]Sin puntuacíon[/COLOR]"
                else:
                    item.infoLabels['rating'] = "[COLOR springgreen]" + str(item.infoLabels['rating']) + "[/COLOR]"
                item.title = item.title + "  " + str(item.infoLabels['rating'])
    except:
        pass
    ## Paginación
    next = scrapertools.find_single_match(data, '<div class=\'resppages\'><a href="([^"]+)"')
    if len(next) > 0:
        url = next
        itemlist.append(item.clone(title="[COLOR springgreen][B]Siguiente >>[/B][/COLOR]", action="buscador", url=url))
    return itemlist


def scraper(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.contentType == "movie":
        patron = scrapertools.find_multiple_matches(data,
                                                    '<div class="poster">.*?src="(.*?)" alt=.*?href="(.*?)">.*?'
                                                    '<h4>(.*?)<\/h4>.*?img\/flags\/(.*?)\.png.*?imdb.*?<span>(.*?)>')
        for thumb, url, title, language, year in patron:
            titulo = title
            title = re.sub(r"!|¡", "", title)
            title = title.replace("Autosia", "Autopsia")
            title = re.sub(r"&#8217;|PRE-Estreno", "'", title)
            new_item = item.clone(action="findvideos", title="[COLOR aqua]" + titulo + "[/COLOR]", url=url,
                                  fulltitle=title, contentTitle=title, contentType="movie", extra=year, library=True,
                                  language= language, infoLabels={'year':year})
            itemlist.append(new_item)
    else:
        patron = scrapertools.find_multiple_matches(data,
                                                    '<div class="poster">.*?src="(.*?)" alt=.*?href="(.*?)">.*?'
                                                    '<h4>(.*?)<\/h4>.*?<span>(.*?)<')
        for thumb, url, title, year in patron:
            titulo = title.strip()
            title = re.sub(r"\d+x.*", "", title)
            new_item = item.clone(action="findtemporadas", title="[COLOR aqua]" + titulo + "[/COLOR]", url=url,
                                  thumbnail=thumb, fulltitle=title, contentTitle=title, show=title,
                                  contentType="tvshow", library=True, infoLabels={'year':year})
            itemlist.append(new_item)
    ## Paginación
    next = scrapertools.find_single_match(data, '<div class=\'resppages\'><a href="([^"]+)"')
    if len(next) > 0:
        url = next
        itemlist.append(
            item.clone(title="[COLOR springgreen][B]Siguiente >>[/B][/COLOR]", thumbnail="http://imgur.com/a7lQAld.png",
                       url=url))
    try:
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for item in itemlist:
            if not "Siguiente >>" in item.title:
                if "0." in str(item.infoLabels['rating']):
                    item.infoLabels['rating'] = "[COLOR indianred]Sin puntuacíon[/COLOR]"
                else:
                    item.infoLabels['rating'] = "[COLOR springgreen]" + str(item.infoLabels['rating']) + "[/COLOR]"
                item.title = item.title + "  " + str(item.infoLabels['rating'])
    except:
        pass
    return itemlist


def ul_cap(item):
    itemlist = []
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = scrapertools.find_multiple_matches(data,
                                                '<div class="poster">.*?<img src="([^"]+)" alt="([^"]+):.*?href="([^"]+)"><span class="b">(\d+x\d+)<\/span>')
    for thumb, title, url, cap in patron:
        temp = re.sub(r"x\d+", "", cap)
        epi = re.sub(r"\d+x", "", cap)
        titulo = title.strip() + "--" + "[COLOR red][B]" + cap + "[/B][/COLOR]"
        title = re.sub(r"\d+x.*", "", title)
        new_item = item.clone(action="findvideos", title="[COLOR aqua]" + titulo + "[/COLOR]", url=url, thumbnail=thumb,
                              fulltitle=title, contentTitle=title, show=title, contentType="tvshow", temp=temp, epi=epi,
                              library=True)
        itemlist.append(new_item)
    ## Paginación
    next = scrapertools.find_single_match(data, '<div class=\'resppages\'><a href="([^"]+)"')
    if len(next) > 0:
        url = next
        itemlist.append(
            item.clone(title="[COLOR springgreen][B]Siguiente >>[/B][/COLOR]", thumbnail="http://imgur.com/a7lQAld.png",
                       url=url))
    try:
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

        for item in itemlist:

            if not "Siguiente >>" in item.title:

                if "0." in str(item.infoLabels['rating']):
                    item.infoLabels['rating'] = "[COLOR indianred]Sin puntuacíon[/COLOR]"
                else:
                    item.infoLabels['rating'] = "[COLOR springgreen] (" + str(item.infoLabels['rating']) + ")[/COLOR]"
                item.title = item.title + "  " + str(item.infoLabels['rating'])
    except:
        pass
    return itemlist


def findtemporadas(item):
    logger.info()
    itemlist = []
    if not item.temp:
        check_temp = None
    else:
        check_temp = "yes"
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if len(item.extra.split("|")):
        if len(item.extra.split("|")) >= 4:
            fanart = item.extra.split("|")[2]
            extra = item.extra.split("|")[3]
            try:
                fanart_extra = item.extra.split("|")[4]
            except:
                fanart_extra = item.extra.split("|")[3]
            try:
                fanart_info = item.extra.split("|")[5]
            except:
                fanart_extra = item.extra.split("|")[3]
        elif len(item.extra.split("|")) == 3:
            fanart = item.extra.split("|")[2]
            extra = item.extra.split("|")[0]
            fanart_extra = item.extra.split("|")[0]
            fanart_info = item.extra.split("|")[1]
        elif len(item.extra.split("|")) == 2:
            fanart = item.extra.split("|")[1]
            extra = item.extra.split("|")[0]
            fanart_extra = item.extra.split("|")[0]
            fanart_info = item.extra.split("|")[1]
    else:
        extra = item.extra
        fanart_extra = item.extra
        fanart_info = item.extra
    try:
        logger.info(fanart_extra)
        logger.info(fanart_info)
    except:
        fanart_extra = item.fanart
        fanart_info = item.fanart

    bloque_episodios = scrapertools.find_multiple_matches(data, 'Temporada (\d+) <i>(.*?)</div></li></ul></div></div>')
    for temporada, bloque_epis in bloque_episodios:
        item.infoLabels = item.InfoLabels
        item.infoLabels['season'] = temporada
        itemlist.append(item.clone(action="epis",
                                   title="[COLOR cornflowerblue][B]Temporada [/B][/COLOR]" + "[COLOR darkturquoise][B]" + temporada + "[/B][/COLOR]",
                                   url=bloque_epis, contentType=item.contentType, contentTitle=item.contentTitle,
                                   show=item.show, extra=item.extra, fanart_extra=fanart_extra, fanart_info=fanart_info,
                                   datalibrary=data, check_temp=check_temp, folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    if config.get_videolibrary_support() and itemlist:
        if len(bloque_episodios) == 1:
            extra = "epis"
        else:
            extra = "epis###serie_add"

        infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'], 'tvdb_id': item.infoLabels['tvdb_id'],
                      'imdb_id': item.infoLabels['imdb_id']}
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", text_color="0xFFe5ffcc",
                             action="add_serie_to_library", extra="", url=item.url,
                             contentSerieName=item.fulltitle, infoLabels=infoLabels,
                             thumbnail='http://imgur.com/3ik73p8.png', datalibrary=data))
    return itemlist


def epis(item):
    logger.info()
    itemlist = []
    if item.extra == "serie_add":
        item.url = item.datalibrary
    patron = scrapertools.find_multiple_matches(item.url, '<div class="imagen"><a href="([^"]+)".*?"numerando">(.*?)<')
    for url, epi in patron:
        episodio = scrapertools.find_single_match(epi, '\d+ - (\d+)')
        item.infoLabels['episode'] = episodio
        epi = re.sub(r" - ", "X", epi)
        itemlist.append(
            item.clone(title="[COLOR deepskyblue]Episodio " + "[COLOR red]" + epi, url=url, action="findvideos",
                       show=item.show, fanart=item.extra, extra=item.extra, fanart_extra=item.fanart_extra,
                       fanart_info=item.fanart_info, check_temp=item.check_temp, folder=True))
    if item.extra != "serie_add":
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for item in itemlist:
            item.fanart = item.extra
            if item.infoLabels['title']: title = "[COLOR royalblue]" + item.infoLabels['title'] + "[/COLOR]"
            item.title = item.title + " -- \"" + title + "\""
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    if item.temp:
        url_epis = item.url
    data = httptools.downloadpage(item.url).data
    if item.contentType != "movie":
        if not item.infoLabels['episode']:
            capitulo = scrapertools.find_single_match(item.title, '(\d+x\d+)')
            url_capitulo = scrapertools.find_single_match(data,
                                                          '<a href="(http://www.divxtotal.com/wp-content/uploads/.*?' + capitulo + '.*?.torrent)')
            if len(item.extra.split("|")) >= 2:
                extra = item.extra
            else:
                extra = item.fanart
        else:
            capitulo = item.title
            url_capitulo = item.url
        try:
            fanart = item.fanart_extra
        except:
            fanart = item.extra.split("|")[0]
        url_data = scrapertools.find_multiple_matches(data, '<div id="option-(.*?)".*?src="([^"]+)"')
        for option, url in url_data:
            server, idioma = scrapertools.find_single_match(data,
                                                            'href="#option-' + option + '">.*?</b>(.*?)<span class="dt_flag">.*?flags/(.*?).png')
            if not item.temp:
                item.infoLabels['year'] = None
            if item.temp:
                capitulo = re.sub(r".*--.*", "", capitulo)
                title = "[COLOR darkcyan][B]Ver capítulo [/B][/COLOR]" + "[COLOR red][B]" + capitulo + "[/B][/COLOR]"
                new_item = item.clone(title=title, url=url, action="play", fanart=fanart, thumbnail=item.thumbnail,
                                      server_v=server, idioma=idioma, extra=item.extra, fulltitle=item.fulltitle,
                                      folder=False)
                new_item.infoLabels['episode'] = item.epi
                new_item.infoLabels['season'] = item.temp
                itemlist.append(new_item)
                itemlist = servertools.get_servers_itemlist(itemlist)
            else:
                title = "[COLOR darkcyan][B]Ver capítulo [/B][/COLOR]" + "[COLOR red][B]" + capitulo + "[/B][/COLOR]" + "  " + "[COLOR darkred]" + server + " ( " + idioma + " )" + "[/COLOR]"
                itemlist.append(Item(channel=item.channel, title=title, url=url, action="play", fanart=fanart,
                                     thumbnail=item.thumbnail, extra=item.extra, fulltitle=item.fulltitle,
                                     folder=False))
        if item.temp:
            tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
            for item in itemlist:
                if item.infoLabels['title']: title_inf = "[COLOR royalblue]" + item.infoLabels['title'] + "[/COLOR]"
                item.title = item.title + " -- \"" + title_inf + "\"" + "  " + "[COLOR darkred]" + item.server_v + " ( " + item.idioma + " )" + "[/COLOR]"
        if item.infoLabels['episode'] and item.library or item.temp and item.library:
            thumbnail = scrapertools.find_single_match(item.extra, 'http://assets.fanart.tv/.*jpg')
            if thumbnail == "":
                thumbnail = item.thumbnail
            if not "assets.fanart" in item.fanart_info:
                fanart = item.fanart_info
            else:
                fanart = item.fanart
            if item.temp:
                item.infoLabels['tvdb_id'] = item.tvdb
        if item.temp and not item.check_temp:
            url_epis = re.sub(r"-\dx.*", "", url_epis)
            url_epis = url_epis.replace("episodios", "series")
            itemlist.append(
                Item(channel=item.channel, title="[COLOR salmon][B]Todos los episodios[/B][/COLOR]", url=url_epis,
                     action="findtemporadas", server="torrent",
                     thumbnail=item.infoLabels['thumbnail'],
                     contentType=item.contentType, contentTitle=item.contentTitle, InfoLabels=item.infoLabels,
                     thumb_art=item.thumb_art, thumb_info=item.thumbnail, fulltitle=item.fulltitle,
                     library=item.library, temp=item.temp, folder=True))
    else:
        url_data = scrapertools.find_multiple_matches(data, '<div id="option-(.*?)".*?src="([^"]+)"')
        for option, url in url_data:
            server, idioma = scrapertools.find_single_match(data,
                                                            'href="#option-' + option + '">.*?</b>(.*?)<span class="dt_flag">.*?flags/(.*?).png')
            title = server + " ( " + idioma + " )"
            item.infoLabels['year'] = None

            itemlist.append(Item(channel=item.channel, title="[COLOR dodgerblue][B]" + title + " [/B][/COLOR]", url=url,
                                 action="play", fanart=item.fanart, thumbnail=item.thumbnail, extra=item.extra,
                                 InfoLabels=item.infoLabels, folder=True))

        if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
            infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                          'title': item.infoLabels['title']}
            itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, fanart=item.extra.split("|")[0],
                                 infoLabels=infoLabels, text_color="0xFFe5ffcc",
                                 thumbnail='http://imgur.com/3ik73p8.png'))
    return itemlist


def play(item):
    itemlist = []
    videolist = servertools.find_video_items(data=item.url)
    for video in videolist:
        itemlist.append(
            Item(channel=item.channel, title="[COLOR saddlebrown][B]" + video.server + "[/B][/COLOR]", url=video.url,
                 server=video.server, action="play", fanart=item.fanart, thumbnail=item.thumbnail, extra=item.extra,
                 InfoLabels=item.infoLabels, folder=False))
    return itemlist


def get_year(url):
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    year = scrapertools.find_single_match(data, 'Fecha de lanzamiento.*?, (\d\d\d\d)')
    if year == "":
        year = "1111"
    return year
