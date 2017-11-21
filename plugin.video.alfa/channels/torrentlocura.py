# -*- coding: utf-8 -*-

import re
import urllib
import urlparse



from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = "http://torrentlocura.com/"


def mainlist(item):
    logger.info()

    thumb_movie = get_thumb("channels_movie.png")
    thumb_tvshow = get_thumb("channels_tvshow.png")
    thumb_anime = get_thumb("channels_anime.png")
    thumb_search = get_thumb("search.png")

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host,
                         thumbnail=thumb_movie, pattern="peliculas"))
    itemlist.append(
        Item(channel=item.channel, action="submenu", title="Series", url=host,
             thumbnail=thumb_tvshow, pattern="series"))
    itemlist.append(
        Item(channel=item.channel, action="anime", title="Anime", url=host,
             thumbnail=thumb_anime, pattern="anime"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host + "buscar",
                         thumbnail=thumb_search))

    return itemlist


def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.post = "q=%s" % texto
        item.pattern = "buscar-list"
        itemlist = listado2(item)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def anime(item):
    logger.info()
    itemlist = []
    title = "Anime"
    url = host + "anime"
    itemlist.append(item.clone(channel=item.channel, action="listado", title=title, url=url,
                               pattern="pelilist"))
    itemlist.append(
        item.clone(channel=item.channel, action="alfabeto", title=title + " [A-Z]", url=url,
                   thumbnail=item.thumbnail[:-4] + "_az.png", pattern="pelilist"))

    return itemlist


def submenu(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    # data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    pattern = '<li><a href="%s%s/">.*?<ul>(.*?)</ul>' % (host, item.pattern)
    data = scrapertools.get_match(data, pattern)

    pattern = '<a href="([^"]+)".*?>([^>]+)</a>'
    matches = re.compile(pattern, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = scrapedurl

        if item.pattern in title.lower():
            itemlist.append(item.clone(channel=item.channel, action="listado", title=title, url=url,
                                       pattern="pelilist"))
            itemlist.append(
                item.clone(channel=item.channel, action="alfabeto", title=title + " [A-Z]", url=url,
                           thumbnail=item.thumbnail[:-4] + "_az.png", pattern="pelilist"))

    return itemlist


def alfabeto(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    # data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    pattern = '<ul class="alfabeto">(.*?)</ul>'
    data = scrapertools.get_match(data, pattern)

    patron = '<a href="([^"]+)"[^>]+>([^>]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.upper()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, pattern=item.pattern))

    return itemlist


def listado(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    # logger.debug("data %s " % data)
    next_page = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a class="current" href.*?'
                                                     '<a\s*href="([^"]+)">')
    # logger.debug("data %s " % next_page)

    pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
    data = scrapertools.get_match(data, pattern)
    # logger.debug("data %s " % data)
    pattern = '<li><a href="(?P<url>[^"]+)" title="(?P<title_to_fix>[^"]+)".*?<img src="(?P<img>[^"]+)"[^>]+>' \
              '<h2.*?>\s*(?P<title>.*?)\s*</h2><span>(?P<quality>[^<]*)</span>'

    matches = re.compile(pattern, re.DOTALL).findall(data)
    # logger.debug("data %s " % matches)

    for url, title_to_fix, thumb, title, quality in matches:
        # fix encoding for title
        title = title.replace("ï¿½", "ñ")

        # title is the clean way but it doesn't work if it's a long, so we have to use title_to_fix
        title_fix = False
        if title.endswith(".."):
            title = title_to_fix
            title_fix = True

        if ".com/series" in url:
            if title_fix:
                title = scrapertools.find_single_match(title, '([^-]+)')
                title = title.replace("Ver online", "", 1).replace("Ver en linea", "", 1). \
                    replace("Descarga Serie HD", "", 1).strip()

            show = title

            #TODO quitar calidad del titulo

            if quality:
                title = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumb,
                                 quality=quality, context=["buscar_trailer"], show=show))

        else:
            if title_fix:
                title = title.replace("Descargar", "", 1).strip()
                if title.endswith("gratis"):
                    title = title[:-6].strip()

            if quality:
                title = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                 quality=quality, context=["buscar_trailer"]))

    if next_page:
        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente", url=next_page,
                             pattern="pagination", thumbnail=get_thumb("next.png")))

    return itemlist


def listado2(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    list_chars = [["Ã±", "ñ"]]

    for el in list_chars:
        data = re.sub(r"%s" % el[0], el[1], data)

    try:
        # logger.debug("data %s " % data)
        get, post = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a class="current" href.*?'
                                                         '<a\s*href="([^"]+)"(?:\s*onClick=".*?\'([^"]+)\'.*?")')
    except:
        post = False

    if post:
        # logger.debug("post %s" % post)
        # logger.debug("item.post %s" % item.post)
        if "pg" in item.post:
            item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
            # logger.debug("item.post %s" % item.post)
        else:
            item.post += "&pg=%s" % post
            # logger.debug("item.post %s" % item.post)

    # logger.debug("data %s " % next_page)

    pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
    data = scrapertools.get_match(data, pattern)
    # logger.debug("data %s " % data)

    pattern = '<li><a href="(?P<url>[^"]+)".*?<img src="(?P<img>[^"]+)"[^>]+>.*?<h2.*?>\s*(?P<title>.*?)\s*</h2>'

    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url, thumb, title in matches:
        # fix encoding for title
        title = scrapertools.htmlclean(title)
        title = title.replace("ï¿½", "ñ")

        # logger.debug("\n\nu %s " % url)
        # logger.debug("\nb %s " % thumb)
        # logger.debug("\nt %s " % title)

        # title is the clean way but it doesn't work if it's a long, so we have to use title_to_fix
        # title_fix = False
        # if title.endswith(".."):
        #     title = title_to_fix
        #     title_fix = True

        # no mostramos lo que no sean videos
        if "/juego/" in url or "/varios/" in url:
            continue

        if ".com/series" in url:
            # title = scrapertools.find_single_match(title, '([^-]+)')
            # title = title.replace("Ver online", "", 1).replace("Ver en linea", "", 1). \
            #     replace("Descarga Serie HD", "", 1).strip()

            show = title
            # if quality:
            #     title = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumb,
                                 context=["buscar_trailer"], show=show))

        else:
            # title = title.replace("Descargar", "", 1).strip()
            # if title.endswith("gratis"):
            #     title = title[:-6].strip()

            # if quality:
            #     title = "%s [%s]" % (title, quality)

                itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                     context=["buscar_trailer"]))

    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado2", title=">> Página siguiente",
                                   thumbnail=get_thumb("next.png")))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    # logger.debug("data %s " % data)
    pattern = '<ul class="%s">(.*?)</ul>' % "pagination"  # item.pattern
    pagination = scrapertools.find_single_match(data, pattern)
    # logger.debug("pagination %s" % pagination)
    if pagination:
        pattern = 'Next</a></li><li><a href="(.*?)(\d+)">Last</a>'
        url, last_page = scrapertools.find_single_match(pagination, pattern)
        # logger.debug("data %s " % last_page)
        list_pages = []
        for x in range(1, int(last_page) + 1):
            list_pages.append("%s%s" % (url, x))
            # logger.debug("data %s%s" % (url, x))
            # logger.debug("list_pages %s" % list_pages)
    else:
        list_pages = [item.url]

    for index, page in enumerate(list_pages):
        logger.debug("Loading page %s/%s url=%s" % (index, len(list_pages), page))
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(page).data)
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

        pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"  # item.pattern
        data = scrapertools.get_match(data, pattern)
        # logger.debug("data %s " % data)

        pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img src="(?P<thumb>[^"]+)".*?<h2[^>]+>(?P<info>.*?)</h2>'
        matches = re.compile(pattern, re.DOTALL).findall(data)
        # logger.debug("data %s " % matches)

        for url, thumb, info in matches:
            # logger.debug("info %s" % info)

            if "<span" in info:  # new style
                pattern = ".*?[^>]+>.*?Temporada\s*(?P<season>\d+)\s*Capitulo(?:s)?\s*(?P<episode>\d+)" \
                          "(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)</span>\s*Calidad\s*<span[^>]+>" \
                          "[\[]\s*(?P<quality>.*?)\s*[\]]</span>"
                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]

                if match["episode2"]:
                    multi = True
                    title = "%s (%sx%s-%s) [%s][%s]" % (item.show, match["season"], str(match["episode"]).zfill(2),
                                                        str(match["episode2"]).zfill(2), match["lang"],
                                                        match["quality"])
                else:
                    multi = False
                    title = "%s (%sx%s) [%s][%s]" % (item.show, match["season"], str(match["episode"]).zfill(2),
                                                     match["lang"], match["quality"])

            else:  # old style
                pattern = "\[(?P<quality>.*?)\].*?\[Cap.(?P<season>\d+)(?P<episode>\d{2})(?:_(?P<season2>\d+)" \
                          "(?P<episode2>\d{2}))?.*?\].*?(?:\[(?P<lang>.*?)\])?"

                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]
                # logger.debug("data %s" % match)

                str_lang = ""
                if match["lang"] is not None:
                    str_lang = "[%s]" % match["lang"]

                if match["season2"] and match["episode2"]:
                    multi = True
                    if match["season"] == match["season2"]:

                        title = "%s (%sx%s-%s) %s[%s]" % (item.show, match["season"], match["episode"],
                                                          match["episode2"], str_lang, match["quality"])
                    else:
                        title = "%s (%sx%s-%sx%s) %s[%s]" % (item.show, match["season"], match["episode"],
                                                             match["season2"], match["episode2"], str_lang,
                                                             match["quality"])
                else:
                    title = "%s (%sx%s) %s[%s]" % (item.show, match["season"], match["episode"], str_lang,
                                                   match["quality"])
                    multi = False

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                 quality=item.quality, multi=multi, contentSeason=match["season"],
                                 contentEpisodeNumber=match["episode"]))

    # order list
    if len(itemlist) > 1:
        return sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    item.plot = scrapertools.find_single_match(data, '<div class="post-entry" style="height:300px;">(.*?)</div>')
    item.plot = scrapertools.htmlclean(item.plot).strip()
    item.contentPlot = item.plot

    link = scrapertools.find_single_match(data, 'href.*?=.*?"http:\/\/(?:tumejorserie|tumejorjuego).*?link=([^"]+)"')
    if link != "":
        link = host + link
        logger.info("torrent=" + link)
        itemlist.append(
            Item(channel=item.channel, action="play", server="torrent", title="Vídeo en torrent", fulltitle=item.title,
                 url=link, thumbnail=servertools.guess_server_thumbnail("torrent"), plot=item.plot, folder=False,
                 parentContent=item))

    patron = '<div class=\"box1\"[^<]+<img[^<]+<\/div[^<]+<div class="box2">([^<]+)<\/div[^<]+<div class="box3">([^<]+)'
    patron += '<\/div[^<]+<div class="box4">([^<]+)<\/div[^<]+<div class="box5"><a href=(.*?) rel.*?'
    patron += '<\/div[^<]+<div class="box6">([^<]+)<'

    #patron = "<div class=\"box1\"[^<]+<img[^<]+</div[^<]+"
    #patron += '<div class="box2">([^<]+)</div[^<]+'
    #patron += '<div class="box3">([^<]+)</div[^<]+'
    #patron += '<div class="box4">([^<]+)</div[^<]+'
    #patron += '<div class="box5">(.*?)</div[^<]+'
    #patron += '<div class="box6">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    itemlist_ver = []
    itemlist_descargar = []

    for servername, idioma, calidad, scrapedurl, comentarios in matches:
        title = "Mirror en " + servername + " (" + calidad + ")" + " (" + idioma + ")"
        servername = servername.replace("uploaded", "uploadedto").replace("1fichier", "onefichier")
        if comentarios.strip() != "":
            title = title + " (" + comentarios.strip() + ")"
        url = urlparse.urljoin(item.url, scrapedurl)
        mostrar_server = servertools.is_server_enabled(servername)
        if mostrar_server:
            thumbnail = servertools.guess_server_thumbnail(title)
            plot = ""
            logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")
            action = "play"
            if "partes" in title:
                action = "extract_url"
            new_item = Item(channel=item.channel, action=action, title=title, fulltitle=title, url=url,
                            thumbnail=thumbnail, plot=plot, parentContent=item, server = servername)
            if comentarios.startswith("Ver en"):
                itemlist_ver.append(new_item)
            else:
                itemlist_descargar.append(new_item)

    for new_item in itemlist_ver:
        itemlist.append(new_item)

    for new_item in itemlist_descargar:
        itemlist.append(new_item)

    return itemlist


def extract_url(item):
    logger.info()

    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = "Enlace encontrado en " + videoitem.server + " (" + scrapertools.get_filename_from_url(
            videoitem.url) + ")"
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist


def play(item):
    logger.info()

    if item.server != "torrent":
        itemlist = servertools.find_video_items(data=item.url)

        for videoitem in itemlist:
            videoitem.title = "Enlace encontrado en " + videoitem.server + " (" + scrapertools.get_filename_from_url(
                videoitem.url) + ")"
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
    else:
        itemlist = [item]

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        item.pattern = 'pelilist'
        if categoria == 'torrent':
            item.url = host+'peliculas/'

            itemlist = listado(item)
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()
            item.url = host+'series/'
            itemlist.extend(listado(item))
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

