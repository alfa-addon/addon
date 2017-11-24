# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Películas", action="menupeliculas",
                         url="http://www.bajui.org/descargas/categoria/2/peliculas",
                         fanart=item.fanart))
    itemlist.append(Item(channel=item.channel, title="Series", action="menuseries",
                         fanart=item.fanart))
    itemlist.append(Item(channel=item.channel, title="Documentales", action="menudocumentales",
                         fanart=item.fanart))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",
                         fanart=item.fanart))
    return itemlist


def menupeliculas(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Películas - Novedades", action="peliculas", url=item.url,
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(
        Item(channel=item.channel, title="Películas - A-Z", action="peliculas", url=item.url + "/orden:nombre",
             fanart=item.fanart, viewmode="movie_with_plot"))

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data, '<ul class="submenu2 subcategorias">(.*?)</ul>')
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title in matches:
        scrapedurl = urlparse.urljoin(item.url, url)
        itemlist.append(Item(channel=item.channel, title="Películas en " + title, action="peliculas", url=scrapedurl,
                             fanart=item.fanart, viewmode="movie_with_plot"))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url="", fanart=item.fanart))
    return itemlist


def menuseries(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Series - Novedades", action="peliculas",
                         url="http://www.bajui.org/descargas/categoria/3/series",
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Series - A-Z", action="peliculas",
                         url="http://www.bajui.org/descargas/categoria/3/series/orden:nombre",
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Series - HD", action="peliculas",
                         url="http://www.bajui.org/descargas/subcategoria/11/hd/orden:nombre",
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url="",
                         fanart=item.fanart))
    return itemlist


def menudocumentales(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Documentales - Novedades", action="peliculas",
                         url="http://www.bajui.org/descargas/categoria/7/docus-y-tv",
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Documentales - A-Z", action="peliculas",
                         url="http://www.bajui.org/descargas/categoria/7/docus-y-tv/orden:nombre",
                         fanart=item.fanart, viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url="",
                         fanart=item.fanart))
    return itemlist


def search(item, texto, categoria=""):
    logger.info(item.url + " search " + texto)
    itemlist = []
    url = item.url
    texto = texto.replace(" ", "+")
    logger.info("categoria: " + categoria + " url: " + url)
    try:
        item.url = "http://www.bajui.org/descargas/busqueda/%s"
        item.url = item.url % texto
        itemlist.extend(peliculas(item))
        return itemlist
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item, paginacion=True):
    logger.info()
    url = item.url
    data = httptools.downloadpage(url).data
    patron = '<li id="ficha-\d+" class="ficha2[^<]+'
    patron += '<div class="detalles-ficha"[^<]+'
    patron += '<span class="nombre-det">Ficha\: ([^<]+)</span>[^<]+'
    patron += '<span class="categoria-det">[^<]+</span>[^<]+'
    patron += '<span class="descrip-det">(.*?)</span>[^<]+'
    patron += '</div>.*?<a href="([^"]+)"[^<]+'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for title, plot, url, thumbnail in matches:
        scrapedtitle = title
        scrapedplot = clean_plot(plot)
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = urlparse.urljoin("http://bajui.org/", thumbnail.replace("_m.jpg", "_g.jpg"))
        itemlist.append(
            Item(channel=item.channel, action="enlaces", title=scrapedtitle, fulltitle=title, url=scrapedurl,
                 thumbnail=scrapedthumbnail, plot=scrapedplot, extra=scrapedtitle, context="4|5",
                 fanart=item.fanart, viewmode="movie_with_plot"))
    patron = '<a href="([^"]+)" class="pagina pag_sig">Siguiente \&raquo\;</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin("http://www.bajui.org/", matches[0])
        pagitem = Item(channel=item.channel, action="peliculas", title=">> Página siguiente", url=scrapedurl,
                       fanart=item.fanart, viewmode="movie_with_plot")
        if not paginacion:
            itemlist.extend(peliculas(pagitem))
        else:
            itemlist.append(pagitem)

    return itemlist


def clean_plot(scrapedplot):
    scrapedplot = scrapedplot.replace("\n", "").replace("\r", "")
    scrapedplot = re.compile("TÍTULO ORIGINAL[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("AÑO[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Año[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("DURACIÓN[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Duración[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("PAIS[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("PAÍS[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Pais[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("País[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("DIRECTOR[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("DIRECCIÓN[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Dirección[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("REPARTO[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Reparto[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Interpretación[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("GUIÓN[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Guión[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("MÚSICA[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Música[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("FOTOGRAFÍA[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Fotografía[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("PRODUCTORA[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Producción[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Montaje[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Vestuario[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("GÉNERO[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("GENERO[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Genero[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Género[^<]+<br />", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("PREMIOS[^<]+<br />", re.DOTALL).sub("", scrapedplot)

    scrapedplot = re.compile("SINOPSIS", re.DOTALL).sub("", scrapedplot)
    scrapedplot = re.compile("Sinopsis", re.DOTALL).sub("", scrapedplot)
    scrapedplot = scrapertools.htmlclean(scrapedplot)
    return scrapedplot


def enlaces(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    try:
        item.plot = scrapertools.get_match(data, '<span class="ficha-descrip">(.*?)</span>')
        item.plot = clean_plot(item.plot)
    except:
        pass

    try:
        item.thumbnail = scrapertools.get_match(data, '<div class="ficha-imagen"[^<]+<img src="([^"]+)"')
        item.thumbnail = urlparse.urljoin("http://www.bajui.org/", item.thumbnail)
    except:
        pass

    patron = '<div class="box-enlace-cabecera"[^<]+'
    patron += '<div class="datos-usuario"><img class="avatar" src="([^"]+)" />Enlaces[^<]+'
    patron += '<a class="nombre-usuario" href="[^"]+">([^<]+)</a[^<]+</div>[^<]+'
    patron += '<div class="datos-act">Actualizado. ([^<]+)</div>.*?'
    patron += '<div class="datos-boton-mostrar"><a id="boton-mostrar-\d+" class="boton" href="javascript.mostrar_enlaces\((\d+)\,\'([^\']+)\'[^>]+>Mostrar enlaces</a></div>[^<]+'
    patron += '<div class="datos-servidores"><div class="datos-servidores-cell">(.*?)</div></div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for thumbnail, usuario, fecha, id, id2, servidores in matches:
        patronservidores = '<img src="[^"]+" title="([^"]+)"'
        matches2 = re.compile(patronservidores, re.DOTALL).findall(servidores)
        lista_servidores = ""
        for servidor in matches2:
            lista_servidores = lista_servidores + servidor + ", "
        lista_servidores = lista_servidores[:-2]
        scrapedthumbnail = item.thumbnail
        scrapedurl = "http://www.bajui.org/ajax/mostrar-enlaces.php?id=" + id + "&code=" + id2
        scrapedplot = item.plot
        scrapedtitle = "Enlaces de " + usuario + " (" + fecha + ") (" + lista_servidores + ")"

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle=item.title, url=scrapedurl,
                 thumbnail=scrapedthumbnail, plot=scrapedplot, context="4|5",
                 fanart=item.fanart))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.plot = item.plot
        videoitem.thumbnail = item.thumbnail
        videoitem.fulltitle = item.fulltitle

        try:
            parsed_url = urlparse.urlparse(videoitem.url)
            fichero = parsed_url.path
            partes = fichero.split("/")
            titulo = partes[len(partes) - 1]
            videoitem.title = titulo + " - [" + videoitem.server + "]"
        except:
            videoitem.title = item.title

    return itemlist
