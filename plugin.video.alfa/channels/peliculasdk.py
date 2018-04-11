# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from platformcode import logger
from platformcode import config
from core import tmdb

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'peliculasdk')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'peliculasdk')

host = "http://www.peliculasdk.com"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(channel=item.channel, title="[COLOR orange]Estrenos[/COLOR]", action="peliculas", url= host + "/ver/estrenos",
             fanart="http://s24.postimg.org/z6ulldcph/pdkesfan.jpg",
             thumbnail="http://s16.postimg.org/st4x601d1/pdkesth.jpg"))
    itemlist.append(
        Item(channel=item.channel, title="[COLOR orange]PelisHd[/COLOR]", action="peliculas", url= host + "/calidad/HD-720/",
             fanart="http://s18.postimg.org/wzqonq3w9/pdkhdfan.jpg",
             thumbnail="http://s8.postimg.org/nn5669ln9/pdkhdthu.jpg"))
    itemlist.append(
        Item(channel=item.channel, title="[COLOR orange]Pelis HD-Rip[/COLOR]", action="peliculas", url= host + "/calidad/HD-320",
             fanart="http://s7.postimg.org/3pmnrnu7f/pdkripfan.jpg",
             thumbnail="http://s12.postimg.org/r7re8fie5/pdkhdripthub.jpg"))
    itemlist.append(
        Item(channel=item.channel, title="[COLOR orange]Pelis Audio español[/COLOR]", action="peliculas", url= host + "/idioma/Espanol/",
             fanart="http://s11.postimg.org/65t7bxlzn/pdkespfan.jpg",
             thumbnail="http://s13.postimg.org/sh1034ign/pdkhsphtub.jpg"))
    itemlist.append(
        Item(channel=item.channel, title="[COLOR orange]Buscar...[/COLOR]", action="search", url= host + "/calidad/HD-720/",
             fanart="http://s14.postimg.org/ceqajaw2p/pdkbusfan.jpg",
             thumbnail="http://s13.postimg.org/o85gsftyv/pdkbusthub.jpg"))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")

    item.url = host + "/index.php?s=%s&x=0&y=0" % (texto)

    try:
        return buscador(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
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
    patron = '<div class="karatula".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="tisearch"><a href="([^"]+)">'
    patron += '([^<]+)<.*?'
    patron += 'Audio:(.*?)</a>.*?'
    patron += 'Género:(.*?)</a>.*?'
    patron += 'Calidad:(.*?),'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedthumbnail, scrapedurl, scrapedtitle, scrapedlenguaje, scrapedgenero, scrapedcalidad in matches:
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        scrapedcalidad = re.sub(r"<a href.*?>|</a>|</span>", "", scrapedcalidad).strip()
        scrapedlenguaje = re.sub(r"<a href.*?>|</a>|</span>", "", scrapedlenguaje).strip()
        if not "Adultos" in scrapedgenero and not "Adultos" in scrapedlenguaje and not "Adultos" in scrapedcalidad:
            scrapedcalidad = "[COLOR orange]" + scrapedcalidad + "[/COLOR]"
            scrapedlenguaje = "[COLOR orange]" + scrapedlenguaje + "[/COLOR]"
            title = scrapedtitle + "-(Idioma: " + scrapedlenguaje + ")" + "-(Calidad: " + scrapedcalidad + ")"
            title = "[COLOR white]" + title + "[/COLOR]"
            scrapedtitle = scrapedtitle.split("(")[0].strip()
            itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action="findvideos",
                                 thumbnail=scrapedthumbnail, contentTitle = scrapedtitle, infoLabels={'year':year},
                                 fanart="http://s18.postimg.org/h9kb22mnt/pdkfanart.jpg", library=True, folder=True))
    tmdb.set_infoLabels(itemlist, True)
    try:
        next_page = scrapertools.get_match(data,
                                           '<span class="current">.*?<a href="(.*?)".*?>Siguiente &raquo;</a></div>')
        itemlist.append(Item(channel=item.channel, action="buscador", title="[COLOR red]siguiente>>[/COLOR]", url=next_page,
                             thumbnail="http://s6.postimg.org/uej03x4r5/bricoflecha.png",
                             fanart="http://s18.postimg.org/h9kb22mnt/pdkfanart.jpg", folder=True))
    except:
        pass
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|&#.*?;", "", data)
    patron = 'style="position:relative;"> '
    patron += '<a href="([^"]+)" '
    patron += 'title="([^<]+)">'
    patron += '<img src="([^"]+)".*?'
    patron += 'Audio:(.*?)</br>.*?'
    patron += 'Calidad:(.*?)</br>.*?'
    patron += 'Género:.*?tag">(.*?)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedlenguaje, scrapedcalidad, scrapedgenero in matches:
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        scrapedtitle = re.sub(r"\(\d+\)", "", scrapedtitle).strip()
        scrapedcalidad = re.sub(r"<a href.*?>|</a>", "", scrapedcalidad).strip()
        scrapedlenguaje = re.sub(r"<a href.*?>|</a>", "", scrapedlenguaje).strip()
        scrapedlenguaje = scrapedlenguaje.split(',')
        if not "Adultos" in scrapedgenero and not "Adultos" in scrapedlenguaje and not "Adultos" in scrapedcalidad:
            scrapedtitle = scrapedtitle
            itemlist.append(Item(channel=item.channel,
                                 title=scrapedtitle,
                                 url=scrapedurl,
                                 action="findvideos",
                                 thumbnail=scrapedthumbnail,
                                 fanart="http://s18.postimg.org/h9kb22mnt/pdkfanart.jpg", library=True, folder=True,
                                 language=scrapedlenguaje,
                                 quality=scrapedcalidad,
                                 contentTitle = scrapedtitle,
                                 infoLabels={'year':year}
                                 ))
    tmdb.set_infoLabels(itemlist)
    ## Paginación
    next_page = scrapertools.get_match(data, '<span class="current">.*?<a href="(.*?)".*?>Siguiente &raquo;</a></div>')
    itemlist.append(Item(channel=item.channel, action="peliculas", title="[COLOR red]siguiente>>[/COLOR]", url=next_page,
                         thumbnail="http://s6.postimg.org/uej03x4r5/bricoflecha.png",
                         fanart="http://s18.postimg.org/h9kb22mnt/pdkfanart.jpg", folder=True))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"<!--.*?-->", "", data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    bloque_tab = scrapertools.find_single_match(data, '<div id="verpelicula">(.*?)<div class="tab_container">')
    patron = '<li><a href="#([^<]+)"><span class="re">\d<\/span><span class="([^<]+)"><\/span><span class=.*?>([^<]+)<\/span>'
    check = re.compile(patron, re.DOTALL).findall(bloque_tab)
    servers_data_list = []
    patron = '<div id="(tab\d+)" class="tab_content"><script type="text/rocketscript">(\w+)\("([^"]+)"\)</script></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) == 0:
        patron = '<div id="(tab\d+)" class="tab_content"><script>(\w+)\("([^"]+)"\)</script></div>'
        matches = re.compile(patron, re.DOTALL).findall(data)
    for check_tab, server, id in matches:
        if check_tab in str(check):
            idioma, calidad = scrapertools.find_single_match(str(check), "" + check_tab + "', '(.*?)', '(.*?)'")
            servers_data_list.append([server, id, idioma, calidad])
    url = host + "/Js/videod.js"
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = data.replace('<iframe width="100%" height="400" scrolling="no" frameborder="0"', '')
    patron = 'function (\w+)\(id\).*?'
    patron += 'data-src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for server, url in matches:
        for enlace, id, idioma, calidad in servers_data_list:
            if server == enlace:
                video_url = re.sub(r"embed\-|\-.*?x.*?\.html|u\'|\'\(", "", str(url))
                video_url = re.sub(r"'\+codigo\+'", "", video_url)
                video_url = video_url.replace('embed//', 'embed/')
                video_url = video_url + id
                if "goo.gl" in video_url:
                    try:
                        from unshortenit import unshorten
                        url = unshorten(video_url)
                        video_url = scrapertools.get_match(str(url), "u'([^']+)'")
                    except:
                        continue
                title = "Ver en: %s [" + idioma + "][" + calidad + "]"
                itemlist.append(
                    item.clone(title=title, url=video_url, action="play",
                         thumbnail=item.category,
                         language=idioma, quality=calidad))
    tmdb.set_infoLabels(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
        infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                      'title': item.fulltitle}
        itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                             action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                             text_color="0xFFff6666",
                             thumbnail='http://imgur.com/0gyYvuC.png'))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'castellano':
            item.url = host + "idioma/Espanol/"
            item.action = "peliculas"
        itemlist = peliculas(item)
        if itemlist[-1].action == "peliculas":
            itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist
