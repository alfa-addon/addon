# -*- coding: utf-8 -*-

import os
import re
import urllib

from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'}
host = "http://www.divxtotal.co"

__modo_grafico__ = config.get_setting('modo_grafico', "divxtotal")


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="[COLOR orange][B]Películas[/B][/COLOR]", action="scraper",
                               url = host + "/peliculas/", thumbnail="http://imgur.com/A4zN3OP.png",
                               fanart="http://imgur.com/fdntKsy.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR orange][B]        Películas HD[/B][/COLOR]", action="scraper",
                               url = host + "/peliculas-hd/", thumbnail="http://imgur.com/A4zN3OP.png",
                               fanart="http://imgur.com/fdntKsy.jpg", contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR orange][B]Series[/B][/COLOR]", action="scraper",
                                       url = host + "/series/", thumbnail="http://imgur.com/GPX2wLt.png",
                                       contentType="tvshow"))

    itemlist.append(itemlist[-1].clone(title="[COLOR orangered][B]Buscar[/B][/COLOR]", action="search",
                                       thumbnail="http://imgur.com/aiJmi3Z.png"))
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
    data = httptools.downloadpage(item.url, headers=header, cookies=False).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<tr><td class="text-left"><a href="([^"]+)" title="([^"]+)">.*?-left">(.*?)</td>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, title, check in matches:
        if "N/A" in check:
            checkmt = "tvshow"
        else:
            checkmt = "movie"
        titulo = title
        title = re.sub(r"!|¡|HD|\d+\d+\d+\d+|\(.*?\).*\[.*?]\]", "", title)
        title = re.sub(r"&#8217;|PRE-Estreno", "'", title)
        if checkmt == "movie":
            new_item = item.clone(action="findvideos", title=titulo, url=url, fulltitle=title, contentTitle=title,
                                  contentType="movie", library=True)
        else:
            if item.extra == "search":
                new_item = item.clone(action="findtemporadas", title=titulo, url=url, fulltitle=title,
                                      contentTitle=title, show=title, contentType="tvshow", library=True)
            else:
                new_item = item.clone(action="findvideos", title=titulo, url=url, fulltitle=title, contentTitle=title,
                                      show=title, contentType="tvshow", library=True)
        new_item.infoLabels['year'] = get_year(url)
        itemlist.append(new_item)
        ## Paginación
    next = scrapertools.find_single_match(data, "<ul class=\"pagination\">.*?\(current\).*?href='([^']+)'")
    if len(next) > 0:
        url = next
        itemlist.append(item.clone(title="[COLOR springgreen][B]Siguiente >>[/B][/COLOR]", action="buscador", url=url))
    try:
        from core import tmdb
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


def scraper(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=header, cookies=False).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.contentType == "movie":
        patron = '<tr><td><a href="([^"]+)" title="([^"]+)".*?\d+-\d+-([^"]+)</td><td>'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, title, year in matches:
            titulo = re.sub(r"\d+\d+\d+\d+|\(.*?\).*", "", title)
            title = re.sub(r"!|¡|HD|\d+\d+\d+\d+|\(.*?\).*", "", title)
            title = title.replace("Autosia", "Autopsia")
            title = re.sub(r"&#8217;|PRE-Estreno", "'", title)
            new_item = item.clone(action="findvideos", title="[COLOR orange]" + titulo + "[/COLOR]", url=url,
                                  fulltitle=title, contentTitle=title, contentType="movie", extra=year, library=True)
            new_item.infoLabels['year'] = get_year(url)
            itemlist.append(new_item)
    else:
        patron  = '(?s)<p class="secconimagen"><a href="([^"]+)"'
        patron += ' title="[^"]+"><img src="([^"]+)".*?'
        patron += 'rel="bookmark">([^<]+)<'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, thumb, title in matches:
            titulo = title.strip()
            title = re.sub(r"\d+x.*|\(.*?\)", "", title)
            new_item = item.clone(action="findvideos", title="[COLOR orange]" + titulo + "[/COLOR]", url=url,
                                  thumbnail=thumb,
                                  fulltitle=title, contentTitle=title, show=title, contentType="tvshow", library=True)
            new_item.infoLabels['year'] = get_year(url)
            itemlist.append(new_item)
    ## Paginación
    next = scrapertools.find_single_match(data, "<ul class=\"pagination\">.*?\(current\).*?href='([^']+)'")
    if len(next) > 0:
        url = next

        itemlist.append(
            item.clone(title="[COLOR springgreen][B]Siguiente >>[/B][/COLOR]", thumbnail="http://imgur.com/a7lQAld.png",
                       url=url))
    try:
        from core import tmdb
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


def findtemporadas(item):
    logger.info()
    itemlist = []
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
    bloque_episodios = scrapertools.find_multiple_matches(data, 'Temporada (\d+).*?<\/a>(.*?)<\/table>')
    for temporada, bloque_epis in bloque_episodios:
        item.infoLabels = item.InfoLabels
        item.infoLabels['season'] = temporada
        itemlist.append(item.clone(action="epis",
                                   title="[COLOR saddlebrown][B]Temporada [/B][/COLOR]" + "[COLOR sandybrown][B]" + temporada + "[/B][/COLOR]",
                                   url=bloque_epis, contentType=item.contentType, contentTitle=item.contentTitle,
                                   show=item.show, extra=item.extra, fanart_extra=fanart_extra, fanart_info=fanart_info,
                                   datalibrary=data, folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    for item in itemlist:
        item.fanart = fanart
        item.extra = extra
    if config.get_videolibrary_support() and itemlist:
        if len(bloque_episodios) == 1:
            extra = "epis"
        else:
            extra = "epis###serie_add"

        infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'], 'tvdb_id': item.infoLabels['tvdb_id'],
                      'imdb_id': item.infoLabels['imdb_id']}
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", text_color="0xFFe5ffcc",
                             action="add_serie_to_library", extra=extra, url=item.url,
                             contentSerieName=item.fulltitle, infoLabels=infoLabels,
                             thumbnail='http://imgur.com/xQNTqqy.png', datalibrary=data))
    return itemlist


def epis(item):
    logger.info()
    itemlist = []
    if item.extra == "serie_add":
        item.url = item.datalibrary
    patron = '<td><img src=".*?images\/(.*?)\.png".*?href="([^"]+)" title="">.*?(\d+x\d+).*?td>'
    matches = scrapertools.find_multiple_matches(item.url, patron)
    for idioma, url, epi in matches:
        episodio = scrapertools.find_single_match(epi, '\d+x(\d+)')
        item.infoLabels['episode'] = episodio
        itemlist.append(
            item.clone(title="[COLOR orange]" + epi + "[/COLOR]" + "[COLOR sandybrown] " + idioma + "[/COLOR]", url=url,
                       action="findvideos", show=item.show, fanart=item.extra, extra=item.extra,
                       fanart_extra=item.fanart_extra, fanart_info=item.fanart_info, folder=True))
    if item.extra != "serie_add":
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for item in itemlist:
            item.fanart = item.extra
            if item.infoLabels['title']: title = "[COLOR burlywood]" + item.infoLabels['title'] + "[/COLOR]"
            item.title = item.title + " -- \"" + title + "\""
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.contentType != "movie":
        if not item.infoLabels['episode']:
            capitulo = scrapertools.find_single_match(item.title, '(\d+x\d+)')
            patron = '<a href="(' + host + '/wp-content/uploads/.*?' + capitulo + '.*?.torrent)'
            url_capitulo = scrapertools.find_single_match(data, patron)
            if len(item.extra.split("|")) >= 2:
                extra = item.extra
            else:
                extra = item.fanart
        else:
            capitulo = item.title
            url_capitulo = item.url

        ext_v, size = ext_size(url_capitulo)
        try:
            fanart = item.fanart_extra
        except:
            fanart = item.extra.split("|")[0]
        itemlist.append(Item(channel=item.channel,
                             title="[COLOR chocolate][B]Ver capítulo " + capitulo + "[/B][/COLOR]" + "-" + "[COLOR khaki] ( Video" + "[/COLOR]" + " " + "[COLOR khaki]" + ext_v + "[/COLOR]" + " " + "[COLOR khaki] " + size + " )" + "[/COLOR]",
                             url=url_capitulo, action="play", server="torrent", fanart=fanart, thumbnail=item.thumbnail,
                             extra=item.extra, fulltitle=item.fulltitle, folder=False))
        if item.infoLabels['episode'] and item.library:
            thumbnail = scrapertools.find_single_match(item.extra, 'http://assets.fanart.tv/.*jpg')
            if thumbnail == "":
                thumbnail = item.thumbnail
            if not "assets.fanart" in item.fanart_info:
                fanart = item.fanart_info
            else:
                fanart = item.fanart
            itemlist.append(Item(channel=item.channel, title="[COLOR darksalmon][B]       info[/B][/COLOR]",
                                 action="info_capitulos", fanart=fanart, thumbnail=item.thumb_art,
                                 thumb_info=item.thumb_info, extra=item.extra, show=item.show,
                                 InfoLabels=item.infoLabels, folder=False))
        if not item.infoLabels['episode']:
            itemlist.append(
                Item(channel=item.channel, title="[COLOR moccasin][B]Todos los episodios[/B][/COLOR]", url=item.url,
                     action="findtemporadas", server="torrent",
                     thumbnail=item.thumbnail, extra=item.extra + "|" + item.thumbnail, contentType=item.contentType,
                     contentTitle=item.contentTitle, InfoLabels=item.infoLabels, thumb_art=item.thumb_art,
                     thumb_info=item.thumbnail, fulltitle=item.fulltitle, library=item.library, folder=True))
    else:
        url = scrapertools.find_single_match(data, '<h3 class="orange text-center">.*?href="([^"]+)"')
        item.infoLabels['year'] = None
        ext_v, size = ext_size(url)
        itemlist.append(Item(channel=item.channel,
                             title="[COLOR saddlebrown][B]Torrent [/B][/COLOR]" + "-" + "[COLOR khaki] ( Video" + "[/COLOR]" + " " + "[COLOR khaki]" + ext_v + "[/COLOR]" + " " + "[COLOR khaki] " + size + " )" + "[/COLOR]",
                             url=url, action="play", server="torrent", fanart=item.fanart, thumbnail=item.thumbnail,
                             extra=item.extra, InfoLabels=item.infoLabels, folder=False))

        if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
            infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                          'title': item.infoLabels['title']}
            itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                                 text_color="0xFFe5ffcc",
                                 thumbnail='http://imgur.com/xQNTqqy.png'))
    return itemlist


def info_capitulos(item, images={}):
    logger.info()
    try:
        url = "http://thetvdb.com/api/1D62F2F90030C444/series/" + str(item.InfoLabels['tvdb_id']) + "/default/" + str(
            item.InfoLabels['season']) + "/" + str(item.InfoLabels['episode']) + "/es.xml"
        if "/0" in url:
            url = url.replace("/0", "/")
        from core import jsontools
        data = httptools.downloadpage(url).data
        if "<filename>episodes" in data:
            image = scrapertools.find_single_match(data, '<Data>.*?<filename>(.*?)</filename>')
            image = "http://thetvdb.com/banners/" + image
        else:
            try:
                image = item.InfoLabels['episodio_imagen']
            except:
                image = "http://imgur.com/ZiEAVOD.png"

        foto = item.thumb_info
        if not ".png" in foto:
            foto = "http://imgur.com/PRiEW1D.png"
        try:
            title = item.InfoLabels['episodio_titulo']
        except:
            title = ""
        title = "[COLOR red][B]" + title + "[/B][/COLOR]"

        try:
            plot = "[COLOR peachpuff]" + str(item.InfoLabels['episodio_sinopsis']) + "[/COLOR]"
        except:
            plot = scrapertools.find_single_match(data, '<Overview>(.*?)</Overview>')
            if plot == "":
                plot = "Sin información todavia"
        try:
            rating = item.InfoLabels['episodio_vote_average']
        except:
            rating = 0
        try:
            if rating >= 5 and rating < 8:
                rating = "[COLOR yellow]Puntuación[/COLOR] " + "[COLOR springgreen][B]" + str(rating) + "[/B][/COLOR]"
            elif rating >= 8 and rating < 10:
                rating = "[COLOR yellow]Puntuación[/COLOR] " + "[COLOR yellow][B]" + str(rating) + "[/B][/COLOR]"
            elif rating == 10:
                rating = "[COLOR yellow]Puntuación[/COLOR] " + "[COLOR orangered][B]" + str(rating) + "[/B][/COLOR]"
            else:
                rating = "[COLOR yellow]Puntuación[/COLOR] " + "[COLOR crimson][B]" + str(rating) + "[/B][/COLOR]"
        except:
            rating = "[COLOR yellow]Puntuación[/COLOR] " + "[COLOR crimson][B]" + str(rating) + "[/B][/COLOR]"
        if "10." in rating:
            rating = re.sub(r'10\.\d+', '10', rating)
    except:
        title = "[COLOR red][B]LO SENTIMOS...[/B][/COLOR]"
        plot = "Este capitulo no tiene informacion..."
        plot = "[COLOR yellow][B]" + plot + "[/B][/COLOR]"
        image = "http://s6.postimg.org/ub7pb76c1/noinfo.png"
        foto = "http://s6.postimg.org/nm3gk1xox/noinfosup2.png"
        rating = ""
    ventana = TextBox2(title=title, plot=plot, thumbnail=image, fanart=foto, rating=rating)
    ventana.doModal()


def tokenize(text, match=re.compile("([idel])|(\d+):|(-?\d+)").match):
    i = 0
    while i < len(text):
        m = match(text, i)
        s = m.group(m.lastindex)
        i = m.end()
        if m.lastindex == 2:
            yield "s"
            yield text[i:i + int(s)]
            i = i + int(s)
        else:
            yield s


def decode_item(next, token):
    if token == "i":
        # integer: "i" value "e"
        data = int(next())
        if next() != "e":
            raise ValueError
    elif token == "s":
        # string: "s" value (virtual tokens)
        data = next()
    elif token == "l" or token == "d":
        # container: "l" (or "d") values "e"
        data = []
        tok = next()
        while tok != "e":
            data.append(decode_item(next, tok))
            tok = next()
        if token == "d":
            data = dict(zip(data[0::2], data[1::2]))
    else:
        raise ValueError
    return data


def decode(text):
    try:
        src = tokenize(text)
        data = decode_item(src.next, src.next())
        for token in src:  # look for more tokens
            raise SyntaxError("trailing junk")
    except (AttributeError, ValueError, StopIteration):
        try:
            data = data
        except:
            data = src
    return data


def convert_size(size):
    import math
    if (size == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])


def get_year(url):
    data = httptools.downloadpage(url, headers=header, cookies=False).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    year = scrapertools.find_single_match(data, '<h3>.*?(\d+\d+\d+\d+)')
    if year == "":
        year = " "
    return year


def ext_size(url):
    torrents_path = config.get_videolibrary_path() + '/torrents'
    if not os.path.exists(torrents_path):
        os.mkdir(torrents_path)
    try:
        urllib.urlretrieve("http://anonymouse.org/cgi-bin/anon-www.cgi/" + url, torrents_path + "/temp.torrent")
        pepe = open(torrents_path + "/temp.torrent", "rb").read()
    except:
        pepe = ""
    torrent = decode(pepe)
    try:
        name = torrent["info"]["name"]
        sizet = torrent["info"]['length']
        sizet = convert_size(sizet)
    except:
        name = "no disponible"
    try:
        check_video = scrapertools.find_multiple_matches(str(torrent["info"]["files"]), "'length': (\d+)}")
        size = max([int(i) for i in check_video])
        for file in torrent["info"]["files"]:
            manolo = "%r - %d bytes" % ("/".join(file["path"]), file["length"])
            if str(size) in manolo:
                video = manolo
        size = convert_size(size)
        ext_v = re.sub(r"-.*? bytes|.*?\[.*?\].|'|.*?COM.|.*?\[.*?\]|\(.*?\)|.*?\.", "", video)
        try:
            os.remove(torrents_path + "/temp.torrent")
        except:
            pass
    except:
        try:
            size = sizet
            ext_v = re.sub(r"-.*? bytes|.*?\[.*?\].|'|.*?COM.|.*?\.es.|.*?\[.*?\]|.*?\(.*?\)\.|.*?\.", "", name)
        except:
            size = "NO REPRODUCIBLE"
            ext_v = ""
        try:
            os.remove(torrents_path + "/temp.torrent")
        except:
            pass
    if "rar" in ext_v:
        ext_v = ext_v + " -- No reproducible"
        size = ""
    return ext_v, size


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = host + '/peliculas/'
            item.contentType="movie"
        itemlist = scraper(item)
        if itemlist[-1].title == "[COLOR springgreen][B]Siguiente >>[/B][/COLOR]":
            itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist
