# -*- coding: utf-8 -*-

import math
import os
import re
import unicodedata
import urllib

from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from platformcode import config, logger


def mainlist(item):
    logger.info()
    check_bg = item.action

    if str(check_bg) == "":
        check_bg = "bglobal"
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="[COLOR yellow][B]Películas[/B][/COLOR]", action="peliculas",
                         url="http://www.miltorrents.com", thumbnail="http://imgur.com/46ZzwrZ.png",
                         fanart="http://imgur.com/y4nJyZh.jpg"))
    title = "[COLOR firebrick][B]Buscar[/B][/COLOR]" + "  " + "[COLOR yellow][B]Peliculas[/B][/COLOR]"
    itemlist.append(Item(channel=item.channel, title="         " + title, action="search", url="",
                         thumbnail="http://imgur.com/JdSnBeH.png", fanart="http://imgur.com/gwjawWV.jpg",
                         extra="peliculas" + "|" + check_bg))

    itemlist.append(Item(channel=item.channel, title="[COLOR slategray][B]Series[/B][/COLOR]", action="peliculas",
                         url="http://www.miltorrents.com/series", thumbnail="http://imgur.com/sYpu1KF.png",
                         fanart="http://imgur.com/LwS32zX.jpg"))

    title = "[COLOR firebrick][B]Buscar[/B][/COLOR]" + "  " + "[COLOR slategray][B]Series[/B][/COLOR]"
    itemlist.append(Item(channel=item.channel, title="         " + title, action="search", url="",
                         thumbnail="http://imgur.com/brMIPlT.png", fanart="http://imgur.com/ecPmzDj.jpg",
                         extra="series" + "|" + check_bg))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    if item.extra:
        if item.extra.split("|")[0] == "series":
            item.url = "http://www.miltorrents.com/series/?pTit=%s&pOrd=FE" % (texto)
        else:
            item.url = "http://www.miltorrents.com/?pTit=%s&pOrd=FE" % (texto)

        item.extra = "search" + "|" + item.extra.split("|")[1] + "|" + texto

        try:
            return peliculas(item)
        # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
        except:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
            return []
    else:
        if item.contentType != "movie":
            item.url = "http://www.miltorrents.com/series/?pTit=%s&pOrd=FE" % (texto)
            check_sp = "tvshow"
        else:
            item.url = "http://www.miltorrents.com/?pTit=%s&pOrd=FE" % (texto)
            check_sp = "peliculas"
        item.extra = "search" + "|""bglobal" + "|" + texto + "|" + check_sp
        try:
            return peliculas(item)
        # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
        except:
            import sys
            for line in sys.exc_info():
                logger.error("%s" % line)
                return []

def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"Independance", "Independence", data)
    if "serie" in item.url:
        patron = '<div class="corner-episode">(.*?)<\/div>.*?<a href="([^"]+)".*?image:url\(\'([^"]+)\'.*?"tooltipbox">(.*?)<br'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if item.extra.split("|")[0] == "search":
            check_bg = item.action
        for episodio, url, thumbnail, title in matches:
            title = title.decode('latin1').encode('utf8')
            title_fan = title.strip()
            trailer = title_fan + " " + "series" + "trailer"
            title_f = "[COLOR slategray][B]" + title.strip() + "[/B][/COLOR]" + "  " + "[COLOR floralwhite][B]" + episodio + "[/B][/COLOR]"
            trailer = urllib.quote(trailer)
            extra = trailer + "|" + title_fan + "|" + " " + "|" + "pelicula"
            itemlist.append(Item(channel=item.channel, title=title_f, url=url, action="findvideos", thumbnail=thumbnail,
                                 fanart="http://imgur.com/NrZNOTN.jpg", extra=extra, folder=True, contentSerieName= title))
    else:
        patron = '<div class="moviesbox">(.*?)<a href="([^"]+)".*?image:url\(\'([^"]+)\'.*?<span class="tooltipbox">([^<]+)<i>\((\d\d\d\d)\)'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for p_rating, url, thumbnail, title, year in matches:

            try:
                rating = scrapertools.get_match(p_rating, '<div class="moviesbox_rating">(.*?)<img')
            except:
                rating = "(Sin puntuacion)"
            title = title.decode('latin1').encode('utf8')
            title_fan = re.sub(r"\[.*?\]|\(.*?\)|\d&#.*?;\d+|-|Temporada.*?Completa| ;|(Sin puntuacion)", "", title)
            try:
                check_rating = scrapertools.get_match(rating, '(\d+).')
                if int(check_rating) >= 5 and int(check_rating) < 8:
                    rating = "[COLOR springgreen][B]" + rating + "[/B][/COLOR]"
                elif int(check_rating) >= 8 and int(check_rating) < 10:
                    rating = "[COLOR yellow][B]" + rating + "[/B][/COLOR]"
                elif int(check_rating) == 10:
                    rating = "[COLOR orangered][B]" + rating + "[/B][/COLOR]"
                else:
                    rating = "[COLOR crimson][B]" + rating + "[/B][/COLOR]"
            except:
                rating = "[COLOR crimson][B]" + rating + "[/B][/COLOR]"
            if "10." in rating:
                rating = re.sub(r'10\.\d+', '10', rating)
            title_f = "[COLOR gold][B]" + title + "[/B][/COLOR]" + "  " + rating
            trailer = title_fan + " " + "trailer"
            trailer = urllib.quote(trailer)
            extra = trailer + "|" + title_fan + "|" + year + "|" + "pelicula"
            itemlist.append(Item(channel=item.channel, title=title_f, url=url, action="findvideos", thumbnail=thumbnail,
                                 fanart="http://imgur.com/Oi1mlFn.jpg", extra=extra, folder=True, contentTitle= title, infoLabels={'year':year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    ## Paginación
    patronvideos = '<div class="pagination">.*?<a href="#">.*?<\/a><\/span><a href="([^"]+)"'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    if len(matches) > 0:
        url = matches[0]
        itemlist.append(Item(channel=item.channel, action="peliculas", title="[COLOR khaki]siguiente[/COLOR]", url=url,
                             thumbnail="http://imgur.com/fJzoytz.png", fanart="http://imgur.com/3AqH1Zu.jpg",
                             folder=True))
    return itemlist


def capitulos(item):
    logger.info()
    itemlist = []
    data = item.extra
    thumbnail = scrapertools.get_match(data, 'background-image:url\(\'([^"]+)\'')
    thumbnail = re.sub(r"w185", "original", thumbnail)
    patron = '<a href="([^"]+)".*?<i>(.*?)<\/i>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, capitulo in matches:
        capitulo = re.sub(r"Cap.*?tulo", "", capitulo)
        capitulo = "[COLOR floralwhite][B]" + capitulo + "[/B][/COLOR]"
        if capitulo == item.extra.split("|")[4]:
            continue
        if not ".jpg" in item.extra.split("|")[2]:
            fanart = item.show.split("|")[0]
        else:
            fanart = item.extra.split("|")[2]
        itemlist.append(Item(channel=item.channel, title=capitulo, action="findvideos", url=url, thumbnail=thumbnail,
                             extra="fv2" + "|" + item.extra.split("|")[3], show=item.show, category=item.category,
                             fanart=fanart, folder=True))
    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def findvideos(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)

    if not "serie" in item.url:
        thumbnail = item.category
    else:
        thumbnail = ''

    patronbloque_enlaces = '<div class="detail_content_subtitle">(.*?)<\/div>(.*?)<div class="torrent_sep">'
    matchesenlaces = re.compile(patronbloque_enlaces, re.DOTALL).findall(data)
    if len(matchesenlaces) == 0:
        thumb = ""
        check = ""
        itemlist.append(
            Item(channel=item.channel, title="[COLOR crimson][B]No hay Torrent[/B][/COLOR]", action="mainlist", url="",
                 fanart=item.show.split("|")[0], thumbnail=thumbnail, folder=False))
    for calidad_bloque, bloque_enlaces in matchesenlaces:
        calidad_bloque = dhe(calidad_bloque)
        calidad_bloque = ''.join((c for c in unicodedata.normalize('NFD', unicode(calidad_bloque.decode('utf-8'))) if
                                  unicodedata.category(c) != 'Mn'))
        if "Alta" in calidad_bloque:
            title = 'Alta Definicion'
            title = "                                           [COLOR yellow][B]" + title + "[/B][/COLOR]"
        elif "estandar" in calidad_bloque:
            title = 'Definicion Estandar'
            title = "                                       [COLOR mediumaquamarine][B]" + title + "[/B][/COLOR]"
        else:
            title = 'Screener'
            title = "                                                  [COLOR slategray][B]" + title + "[/B][/COLOR]"
        itemlist.append(
            Item(channel=item.channel, title=title, action="mainlist", url="", fanart=item.show.split("|")[0],
                 thumbnail=thumbnail, folder=False))
        if "serie" in item.url:
            thumb = scrapertools.get_match(data, '<div class="detail_background2".*?url\(([^"]+)\)')
            patron = '\:showDownload.*?(http.*?)\''
            matches = re.compile(patron, re.DOTALL).findall(bloque_enlaces)
            for url in matches:
                calidad = ""
                try:
                    if not url.endswith(".torrent") and not "elitetorrent" in url:
                        if url.endswith("fx"):
                            url = httptools.downloadpage(url, follow_redirects=False)
                            url = url.headers.get("location")
                            if url.endswith(".fx"):
                                url = httptools.downloadpage(url, follow_redirects=False)
                                url = url.headers.get("location")

                            url = " http://estrenosli.org" + url

                        else:
                            if not url.endswith(".mkv"):
                                url = httptools.downloadpage(url, follow_redirects=False)
                                url = url.headers.get("location")

                    torrents_path = config.get_videolibrary_path() + '/torrents'

                    if not os.path.exists(torrents_path):
                        os.mkdir(torrents_path)
                    try:
                        urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
                        urllib.urlretrieve(url, torrents_path + "/temp.torrent")
                        pepe = open(torrents_path + "/temp.torrent", "rb").read()
                    except:
                        pepe = ""
                    if "used CloudFlare" in pepe:
                        try:
                            urllib.urlretrieve("http://anonymouse.org/cgi-bin/anon-www.cgi/" + url.strip(),
                                               torrents_path + "/temp.torrent")
                            pepe = open(torrents_path + "/temp.torrent", "rb").read()
                        except:
                            pepe = ""
                    torrent = decode(pepe)
                    logger.debug('el torrent %s' % torrent)
                    try:
                        name = torrent["info"]["name"]
                        sizet = torrent["info"]['length']
                        sizet = convert_size(sizet)
                    except:
                        name = "no disponible"
                    try:
                        check_video = scrapertools.find_multiple_matches(str(torrent["info"]["files"]),
                                                                         "'length': (\d+)}")
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
                        size = sizet
                        ext_v = re.sub(r"-.*? bytes|.*?\[.*?\].|'|.*?COM.|.*?\.es.|.*?\[.*?\]|.*?\(.*?\)\.|.*?\.", "",
                                       name)
                        try:
                            os.remove(torrents_path + "/temp.torrent")
                        except:
                            pass
                except:
                    size = "en estos momentos..."
                    ext_v = "no disponible"
                if "Alta" in calidad_bloque:
                    title = "[COLOR navajowhite][B]" + calidad + "[/B][/COLOR]" + " " + "[COLOR peachpuff]( Video [/COLOR]" + "[COLOR peachpuff]" + ext_v + " -- " + size + " )[/COLOR]"
                elif "estandar" in calidad_bloque:
                    title = "[COLOR lavender][B]" + calidad + "[/B][/COLOR]" + " " + "[COLOR azure]( Video [/COLOR]" + "[COLOR azure]" + ext_v + " -- " + size + " )[/COLOR]"
                else:
                    title = "[COLOR gainsboro][B]" + calidad + "[/B][/COLOR]" + " " + "[COLOR silver]( Video [/COLOR]" + "[COLOR silver]" + ext_v + " -- " + size + " )[/COLOR]"
                if "rar" in ext_v:
                    ext_v = ext_v + " -- No reproducible"
                    size = ""
                item.title = re.sub(r"\[.*?\]", "", item.title)
                temp_epi = scrapertools.find_multiple_matches(item.title, '(\d+)x(\d+)')
                for temp, epi in temp_epi:
                    check = temp + "x" + epi
                    if item.extra.split("|")[0] == "fv2":
                        extra = item.extra.split("|")[1] + "|" + " " + "|" + temp + "|" + epi
                    else:
                        extra = item.extra + "|" + temp + "|" + epi

                    itemlist.append(Item(channel=item.channel, title=title, action="play", url=url, server="torrent",
                                         thumbnail=thumbnail, extra=item.extra, show=item.show,
                                         fanart=item.show.split("|")[0], folder=False))
        else:
            patron = '<a href=.*?(http.*?)\'\).*?<i>(.*?)<i>(.*?)<\/i>'
            matches = re.compile(patron, re.DOTALL).findall(bloque_enlaces)
            for url, calidad, peso in matches:
                try:
                    if not url.endswith(".torrent") and not "elitetorrent" in url:
                        if url.endswith("fx"):
                            url = httptools.downloadpage(url, follow_redirects=False)
                            url = url.headers.get("location")
                            if url.endswith(".fx"):
                                url = httptools.downloadpage(url, follow_redirects=False)
                                url = url.headers.get("location")
                            url = " http://estrenosli.org" + url
                        else:
                            if not url.endswith(".mkv"):
                                url = httptools.downloadpage(url, follow_redirects=False)
                                url = url.headers.get("location")
                    torrents_path = config.get_videolibrary_path() + '/torrents'
                    if not os.path.exists(torrents_path):
                        os.mkdir(torrents_path)
                    urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
                    urllib.urlretrieve(url, torrents_path + "/temp.torrent")
                    pepe = open(torrents_path + "/temp.torrent", "rb").read()
                    if "used CloudFlare" in pepe:
                        try:
                            urllib.urlretrieve("http://anonymouse.org/cgi-bin/anon-www.cgi/" + url.strip(),
                                               torrents_path + "/temp.torrent")
                            pepe = open(torrents_path + "/temp.torrent", "rb").read()
                        except:
                            pepe = ""
                    torrent = decode(pepe)
                    try:
                        name = torrent["info"]["name"]
                    except:
                        name = "no disponible"
                    try:
                        check_video = scrapertools.find_multiple_matches(str(torrent["info"]["files"]),
                                                                         "'length': (\d+)}")
                        size = max([int(i) for i in check_video])
                        for file in torrent["info"]["files"]:
                            manolo = "%r - %d bytes" % ("/".join(file["path"]), file["length"])
                            if str(size) in manolo:
                                video = manolo
                        ext_v = re.sub(r"-.*? bytes|\.*?\[.*?\]\.|'|\.*?COM.|.*?\[.*?\]|\(.*?\)|.*?\.", "", video)
                        try:
                            os.remove(torrents_path + "/temp.torrent")
                        except:
                            pass
                    except:
                        ext_v = re.sub(r"-.*? bytes|.*?\[.*?\].|'|.*?COM.|.*?\.es\.|.*?\[.*?\]|.*?\(.*?\)\.|.*?\.", "",
                                       name)
                        try:
                            os.remove(torrents_path + "/temp.torrent")
                        except:
                            pass
                except:
                    size = "en estos momentos..."
                    ext_v = "no disponible"
                if "rar" in ext_v:
                    ext_v = ext_v + " -- No reproducible"
                calidad = re.sub(r"</i>", "", calidad)
                if "Alta" in calidad_bloque:
                    title = "[COLOR khaki][B]" + calidad + "[/B][/COLOR]" + "[COLOR darkkhaki][B]" + " -  " + peso + "[/B][/COLOR]" + " " + "[COLOR lemonchiffon]( Video [/COLOR]" + "[COLOR lemonchiffon]" + ext_v + " )[/COLOR]"
                elif "estandar" in calidad_bloque:
                    title = "[COLOR darkcyan][B]" + calidad + "[/B][/COLOR]" + "[COLOR cadetblue][B]" + " -  " + peso + "[/B][/COLOR]" + " " + "[COLOR paleturquoise]( Video [/COLOR]" + "[COLOR paleturquoise]" + ext_v + " )[/COLOR]"
                else:
                    title = "[COLOR dimgray][B]" + calidad + "[/B][/COLOR]" + "[COLOR gray][B]" + " -  " + peso + "[/B][/COLOR]" + " " + "[COLOR lightslategray]( Video [/COLOR]" + "[COLOR lightslategray]" + ext_v + " )[/COLOR]"
                itemlist.append(Item(channel=item.channel, title=title, action="play", url=url, server="torrent",
                                     thumbnail=thumbnail, extra=item.extra, show=item.show,
                                     fanart=item.show.split("|")[0], folder=False))
    if "serie" in item.url and item.extra.split("|")[0] != "fv2":
        title_info = 'Temporadas'
        title_info = "[COLOR springgreen][B]" + title_info + "[/B][/COLOR]"
        itemlist.append(Item(channel=item.channel, title="                                             " + title_info,
                             action="mainlist", url="", fanart=item.show.split("|")[0], thumbnail=thumbnail,
                             folder=False))
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
        patron = 'class="contactlinkh">(.*?)<\/a><\/div>(.*?)</div></div></div>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for temporadas, bloque_capitulos in matches:
            thumbnail = scrapertools.get_match(bloque_capitulos, 'background-image:url\(\'([^"]+)\'')
            thumbnail = re.sub(r"w185", "original", thumbnail)
            itemlist.append(Item(channel=item.channel, title="[COLOR chartreuse][B]" + temporadas + "[/B][/COLOR]",
                                 action="capitulos", url=item.url, thumbnail=thumbnail,
                                 extra="fv2" + "|" + bloque_capitulos + "|" + thumb + "|" + item.extra + "|" + check,
                                 show=item.show, fanart=item.show.split("|")[0], category=item.category, folder=True))
    return itemlist


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


def convert_size(size):
    if (size == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])
