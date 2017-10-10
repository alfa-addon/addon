# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://peliscity.com"

def mainlist(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    patron = 'cat-item.*?span>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    can = 0
    for cantidad in matches:
        can += int(cantidad.replace(".", ""))


    itemlist.append(
        Item(channel=item.channel, title="Películas: (%s)" %can, text_bold=True))
    itemlist.append(
        Item(channel=item.channel, title="    Últimas agregadas", action="agregadas", url= host,
             viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="    Peliculas HD", action="agregadas",
                         url= host + "/calidad/hd-real-720", viewmode="movie_with_plot"))
    itemlist.append(
        Item(channel=item.channel, title="    Listado por género", action="porGenero", url= host))
    itemlist.append(Item(channel=item.channel, title="    Buscar", action="search", url= host + "/?s="))
    itemlist.append(Item(channel=item.channel, title="    Idioma", action="porIdioma", url= host))

    return itemlist


def porIdioma(item):
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Castellano", action="agregadas",
                         url= host + "/idioma/espanol-castellano/", viewmode="movie_with_plot"))
    itemlist.append(
        Item(channel=item.channel, title="VOSE", action="agregadas", url= host + "/idioma/subtitulada/",
             viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Latino", action="agregadas",
                         url= host + "/idioma/espanol-latino/", viewmode="movie_with_plot"))

    return itemlist


def porGenero(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data

    patron = 'cat-item.*?href="([^"]+).*?>(.*?)<.*?span>([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for urlgen, genero, cantidad in matches:
        cantidad = cantidad.replace(".", "")
        titulo = genero + " (" + cantidad + ")"
        itemlist.append(Item(channel=item.channel, action="agregadas", title=titulo, url=urlgen, folder=True,
                             viewmode="movie_with_plot"))

    return itemlist


def search(item, texto):
    logger.info()
    texto_post = texto.replace(" ", "+")
    item.url = host + "/?s=" + texto_post

    try:
        return listaBuscar(item)
    # Se captura la excepci?n, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def agregadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;|"', "", data)

    patron = scrapertools.find_multiple_matches (data,'<divclass=col-mt-5 postsh>.*?Duración')

    for element in patron:
        info = scrapertools.find_single_match(element,
                                              "calidad>(.*?)<.*?ahref=(.*?)>.*?'reflectMe' src=(.*?)\/>.*?<h2>(.*?)"
                                              "<\/h2>.*?sinopsis>(.*?)<\/div>.*?Año:<\/span>(.*?)<\/li>")
        quality = info[0]
        url = info[1]
        thumbnail = info[2]
        title = info[3]
        plot = info[4]
        year = info[5].strip()

        itemlist.append(Item(channel=item.channel,
                             action='findvideos',
                             contentType = "movie",
                             fulltitle = title,
                             infoLabels={'year':year},
                             plot=plot,
                             quality=quality,
                             thumbnail=thumbnail,
                             title=title,
                             contentTitle = title,
                             url=url
                             ))
    # Paginación
    try:
        next_page = scrapertools.find_single_match(data,'tima>.*?href=(.*?) ><i')

        itemlist.append(Item(channel=item.channel, action="agregadas", title='Pagina Siguiente >>',
                             url=next_page.strip(),
                             viewmode="movie_with_plot"))
    except:
        pass

    return itemlist


def listaBuscar(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n", " ", data)
    logger.info("data=" + data)

    patron = 'class="row"> <a.*?="([^"]+).*?src="([^"]+).*?title="([^"]+).*?class="text-list">(.*?)</p>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, thumbnail, title, sinopsis in matches:
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title + " ", fulltitle=title, url=url,
                             thumbnail=thumbnail, show=title, plot=sinopsis))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    plot = item.plot

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    patron = 'cursor: hand" rel="(.*?)".*?class="optxt"><span>(.*?)<.*?width.*?class="q">(.*?)</span'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedidioma, scrapedcalidad in matches:
        idioma = ""
        title = "%s [" + scrapedcalidad + "][" + scrapedidioma +"]"
        if "youtube" in scrapedurl:
            scrapedurl += "&"
        quality = scrapedcalidad
        language = scrapedidioma
        if not ("omina.farlante1" in scrapedurl or "404" in scrapedurl):
            itemlist.append(
                Item(channel=item.channel, action="play", title=title, fulltitle=item.title, url=scrapedurl,
                     thumbnail=item.thumbnail, plot=plot, show=item.show, quality= quality, language=language, extra = item.thumbnail))
    itemlist=servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Opción "Añadir esta película a la biblioteca de KODI"
    if item.extra != "library":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 filtro=True, action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 infoLabels={'title': item.fulltitle}, fulltitle=item.title,
                                 extra="library"))
    return itemlist


def play(item):
    logger.info()
    item.thumbnail = item.extra
    return [item]
