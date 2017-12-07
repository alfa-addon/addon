# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

__modo_grafico__ = config.get_setting('modo_grafico', "ver-pelis")
host = "http://ver-pelis.me"


def mainlist(item):
    logger.info()
    itemlist = []
    global i
    i = 0
    itemlist.append(
        item.clone(title="[COLOR oldlace]Películas[/COLOR]", action="scraper", url=host + "/ver/",
                   thumbnail="http://imgur.com/36xALWc.png", fanart="http://imgur.com/53dhEU4.jpg",
                   contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Películas por año[/COLOR]", action="categoria_anno",
                               url=host, thumbnail="http://imgur.com/36xALWc.png", extra="Por año",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Películas en Latino[/COLOR]", action="scraper",
                               url=host + "/ver/latino/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Películas en Español[/COLOR]", action="scraper",
                               url=host + "/ver/subtituladas/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Películas Subtituladas[/COLOR]", action="scraper",
                               url=host + "/ver/espanol/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Por Género[/COLOR]", action="categoria_anno",
                               url=host, thumbnail="http://imgur.com/36xALWc.png", extra="Categorias",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))

    itemlist.append(itemlist[-1].clone(title="[COLOR orangered]Buscar[/COLOR]", action="search",
                                       thumbnail="http://imgur.com/ebWyuGe.png", fanart="http://imgur.com/53dhEU4.jpg",
                                       contentType="tvshow"))

    return itemlist


def categoria_anno(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'mobile_menu.*?(%s.*?)</ul>' % item.extra)
    patron = '(?is)<li.*?a href="([^"]+)'
    patron += '.*?title="[^"]+">([^<]+)'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in match:
        itemlist.append(Item(
            channel=item.channel,
            action="scraper",
            title=titulo,
            url=url
        ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/ver/buscar?s=" + texto
    item.extra = "search"
    if texto != '':
        return scraper(item)


def scraper(item):
    logger.info()
    itemlist = []
    url_next_page = ""
    global i
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="thumb cluetip".*?href="([^"]+)".*?src="([^"]+)" alt="([^"]+)".*?"res">([^"]+)</span>'
    patron = scrapertools.find_multiple_matches(data, patron)
    if len(patron) > 20:
        if item.next_page != 20:
            url_next_page = item.url
            patron = patron[:20]
            next_page = 20
            item.i = 0
        else:
            patron = patron[item.i:][:20]
            next_page = 20
            url_next_page = item.url
    for url, thumb, title, cuality in patron:
        title = re.sub(r"Imagen", "", title)
        titulo = "[COLOR floralwhite]" + title + "[/COLOR]" + " " + "[COLOR crimson][B]" + cuality + "[/B][/COLOR]"
        title = re.sub(r"!|\/.*", "", title).strip()

        if item.extra != "search":
            item.i += 1
        itemlist.append(item.clone(action="findvideos", title=titulo, url=url, thumbnail=thumb, fulltitle=title,
                                   contentTitle=title, contentType="movie", library=True))

    ## Paginación
    if url_next_page:
        itemlist.append(item.clone(title="[COLOR crimson]Siguiente >>[/COLOR]", url=url_next_page, next_page=next_page,
                                   thumbnail="http://imgur.com/w3OMy2f.png", i=item.i))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data_post = scrapertools.find_single_match(data, "type: 'POST'.*?id: (.*?),slug: '(.*?)'")
    if data_post:
        post = 'id=' + data_post[0] + '&slug=' + data_post[1]
        data_info = httptools.downloadpage(host + '/ajax/cargar_video.php', post=post).data
        patron = """</i> ([^<]+)"""
        patron += """.*?<a onclick=\"load_player\('([^']+)"""
        patron += """','([^']+)', ([^']+),.*?REPRODUCIR\">([^']+)</a>"""
        enlaces = scrapertools.find_multiple_matches(data_info, patron)
        for server, id_enlace, name, number, idioma_calidad in enlaces:
            server = server.strip()
            if "SUBTITULOS" in idioma_calidad and not "P" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("SUBTITULOS", "VO")
                idioma_calidad = idioma_calidad.replace("VO", "[COLOR orangered] VO[/COLOR]")
            elif "SUBTITULOS" in idioma_calidad and "P" in idioma_calidad:
                idioma_calidad = "[COLOR indianred] " + idioma_calidad + "[/COLOR]"

            elif "LATINO" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("LATINO", "[COLOR red]LATINO[/COLOR]")
            elif "Español" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("Español", "[COLOR crimson]ESPAÑOL[/COLOR]")
            if "HD" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("HD", "[COLOR crimson] HD[/COLOR]")
            elif "720" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("720", "[COLOR firebrick] 720[/COLOR]")
            elif "TS" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("TS", "[COLOR brown] TS[/COLOR]")

            elif "CAM" in idioma_calidad:
                idioma_calidad = idioma_calidad.replace("CAM", "[COLOR darkkakhi] CAM[/COLOR]")

            url = host + "/ajax/video.php?id=" + id_enlace + "&slug=" + name + "&quality=" + number

            if not "Ultra" in server:
                server = "[COLOR cyan][B]" + server + " [/B][/COLOR]"
                extra = ""
            else:
                server = "[COLOR yellow][B]Gvideo [/B][/COLOR]"
                extra = "yes"
            title = server.strip() + "  " + idioma_calidad
            itemlist.append(Item(
                channel=item.channel,
                action="play",
                title=title,
                url=url,
                fanart=item.fanart,
                thumbnail=item.thumbnail,
                fulltitle=item.fulltitle,
                extra=extra,
                folder=True
            ))
        if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
            infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                          'title': item.infoLabels['title']}
            itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                                 text_color="0xFFf7f7f7",
                                 thumbnail='http://imgur.com/gPyN1Tf.png'))
    else:
        itemlist.append(
            Item(channel=item.channel, action="", title="[COLOR red][B]Upps!..Archivo no encontrado...[/B][/COLOR]",
                 thumbnail=item.thumbnail))
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\\', '', data)
    item.url = scrapertools.find_single_match(data, 'src="([^"]+)"')
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'window.location="([^"]+)"')
    if item.extra == "yes":
        data = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(data, '(?is)iframe src="([^"]+)"')
    videolist = servertools.find_video_items(data=url)
    for video in videolist:
        itemlist.append(Item(
            channel=item.channel,
            url=video.url,
            server=video.server,
            fulltitle=item.fulltitle,
            thumbnail=item.thumbnail,
            action="play"
        ))

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/ver/'
        elif categoria == 'terror':
            item.url = host + "/categoria/de-terror.htm"
        elif categoria == 'castellano':
            item.url = host + "/ver/espanol/"

        elif categoria == 'latino':
            item.url = host + "/ver/latino/"
        else:
            return []

        itemlist = scraper(item)
        if itemlist[-1].title == "[COLOR crimson]Siguiente >>[/COLOR]":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
