# -*- coding: utf-8 -*-

import re
import urlparse

from core import scrapertools
from core import httptools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Ultimas Agregadas", action="listado2",
                         url="http://www.vepelis.com/pelicula/ultimas-peliculas",
                         extra="http://www.vepelis.com/pelicula/ultimas-peliculas"))
    itemlist.append(Item(channel=item.channel, title="Estrenos en DVD", action="listado2",
                         url="http://www.vepelis.com/pelicula/ultimas-peliculas/estrenos-dvd",
                         extra="http://www.vepelis.com/pelicula/ultimas-peliculas/estrenos-dvd"))
    itemlist.append(Item(channel=item.channel, title="Peliculas en Cartelera", action="listado2",
                         url="http://www.vepelis.com/pelicula/ultimas-peliculas/cartelera",
                         extra="http://www.vepelis.com/pelicula/ultimas-peliculas/cartelera"))
    itemlist.append(Item(channel=item.channel, title="Ultimas Actualizadas", action="listado2",
                         url="http://www.vepelis.com/pelicula/ultimas-peliculas/ultimas/actualizadas",
                         extra="http://www.vepelis.com/pelicula/ultimas-peliculas/ultimas/actualizadas"))
    itemlist.append(Item(channel=item.channel, title="Por Genero", action="generos", url="http://www.vepelis.com/"))
    itemlist.append(Item(channel=item.channel, title="Por Orden Alfabetico", action="alfabetico",
                         url="http://www.vepelis.com/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url="http://www.vepelis.com/"))
    return itemlist


def listarpeliculas(item):
    logger.info()

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    extra = item.extra

    # Extrae las entradas de la pagina seleccionada
    '''<td class="DarkText" align="center" valign="top" width="100px" height="160px" 
    style="background-color:#1e1e1e;" onmouseover="this.style.backgroundColor='#000000'" 
    onmouseout="this.style.backgroundColor='#1e1e1e'"><p style="margin-bottom: 3px;border-bottom:#ABABAB 1px solid"> 
                    	<a href="http://www.peliculasaudiolatino.com/movies/Larry_Crowne.html"><img 
                    	src="http://www.peliculasaudiolatino.com/poster/85x115/peliculas/movieimg/movie1317696842.jpg" 
                    	alt="Larry Crowne" border="0" height="115" width="85"></a>'''
    patron = '<td class=.*?<a '
    patron += 'href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for match in matches:
        scrapedurl = match[0]
        scrapedtitle = match[2]
        scrapedtitle = unicode(scrapedtitle, "iso-8859-1", errors="replace").encode("utf-8")
        scrapedthumbnail = match[1]
        scrapedplot = ""
        logger.info(scrapedtitle)

        # Añade al listado
        itemlist.append(Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                             url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, extra=extra, folder=True))

    # Extrae la marca de siguiente página
    patron = 'Anterior.*?  :: <a href="/../../.*?/page/([^"]+)">Siguiente '
    matches = re.compile(patron, re.DOTALL).findall(data)
    for match in matches:
        if len(matches) > 0:
            scrapedurl = extra + match
            scrapedtitle = "!Pagina Siguiente"
            scrapedthumbnail = ""
            scrapedplot = ""

            itemlist.append(
                    Item(channel=item.channel, action="listarpeliculas", title=scrapedtitle, fulltitle=scrapedtitle,
                         url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, extra=extra, folder=True))

    return itemlist


def findvideos(item):
    logger.info()
    # Descarga la página
    itemlist = []
    data = httptools.downloadpage(item.url).data

    itemlist.extend(servertools.find_video_items(data=data))

    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.quality = item.quality
        videoitem.language = item.language
        videoitem.action = 'play'

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    patron = '>.*?<li><a title="(.*?)" href="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for match in matches:
        scrapedurl = urlparse.urljoin("", match[1])
        scrapedurl = scrapedurl.replace(".html", "/page/0.html")
        extra = scrapedurl.replace("/page/0.html", "/page/")
        scrapedtitle = match[0]
        # scrapedtitle = scrapedtitle.replace("","")
        scrapedthumbnail = ""
        scrapedplot = ""
        logger.info(scrapedtitle)

        if scrapedtitle == "Eroticas +18":
            if config.get_setting("adult_mode") != 0:
                itemlist.append(Item(channel=item.channel, action="listado2", title="Eroticas +18",
                                     url="http://www.myhotamateurvideos.com", thumbnail=scrapedthumbnail,
                                     plot=scrapedplot, extra="", folder=True))
        else:
            if scrapedtitle <> "" and len(scrapedtitle) < 20 and scrapedtitle <> "Iniciar Sesion":
                itemlist.append(Item(channel=item.channel, action="listado2", title=scrapedtitle, url=scrapedurl,
                                     thumbnail=scrapedthumbnail, plot=scrapedplot, extra=extra, folder=True))

    itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return itemlist


def alfabetico(item):
    logger.info()
    # TODO Hacer esto correctamente
    extra = item.url
    itemlist = []
    itemlist.append(
            Item(channel=item.channel, action="listado2", title="0-9", url="http://www.vepelis.com/letra/09.html",
                 extra="http://www.vepelis.com/letra/09.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="A", url="http://www.vepelis.com/letra/a.html",
                         extra="http://www.vepelis.com/letra/a.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="B", url="http://www.vepelis.com/letra/b.html",
                         extra="http://www.vepelis.com/letra/b.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="C", url="http://www.vepelis.com/letra/c.html",
                         extra="http://www.vepelis.com/letra/c.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="E", url="http://www.vepelis.com/letra/d.html",
                         extra="http://www.vepelis.com/letra/d.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="D", url="http://www.vepelis.com/letra/e.html",
                         extra="http://www.vepelis.com/letra/e.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="F", url="http://www.vepelis.com/letra/f.html",
                         extra="http://www.vepelis.com/letra/f.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="G", url="http://www.vepelis.com/letra/g.html",
                         extra="http://www.vepelis.com/letra/g.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="H", url="http://www.vepelis.com/letra/h.html",
                         extra="http://www.vepelis.com/letra/h.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="I", url="http://www.vepelis.com/letra/i.html",
                         extra="http://www.vepelis.com/letra/i.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="J", url="http://www.vepelis.com/letra/j.html",
                         extra="http://www.vepelis.com/letra/j.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="K", url="http://www.vepelis.com/letra/k.html",
                         extra="http://www.vepelis.com/letra/k.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="L", url="http://www.vepelis.com/letra/l.html",
                         extra="http://www.vepelis.com/letra/l.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="M", url="http://www.vepelis.com/letra/m.html",
                         extra="http://www.vepelis.com/letra/m.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="N", url="http://www.vepelis.com/letra/n.html",
                         extra="http://www.vepelis.com/letra/n.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="O", url="http://www.vepelis.com/letra/o.html",
                         extra="http://www.vepelis.com/letra/o.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="P", url="http://www.vepelis.com/letra/p.html",
                         extra="http://www.vepelis.com/letra/p.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="Q", url="http://www.vepelis.com/letra/q.html",
                         extra="http://www.vepelis.com/letra/q.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="R", url="http://www.vepelis.com/letra/r.html",
                         extra="http://www.vepelis.com/letra/r.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="S", url="http://www.vepelis.com/letra/s.html",
                         extra="http://www.vepelis.com/letra/s.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="T", url="http://www.vepelis.com/letra/t.html",
                         extra="http://www.vepelis.com/letra/t.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="U", url="http://www.vepelis.com/letra/u.html",
                         extra="http://www.vepelis.com/letra/u.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="V", url="http://www.vepelis.com/letra/v.html",
                         extra="http://www.vepelis.com/letra/v.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="W", url="http://www.vepelis.com/letra/w.html",
                         extra="http://www.vepelis.com/letra/w.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="X", url="http://www.vepelis.com/letra/x.html",
                         extra="http://www.vepelis.com/letra/x.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="Y", url="http://www.vepelis.com/letra/y.html",
                         extra="http://www.vepelis.com/letra/y.html"))
    itemlist.append(Item(channel=item.channel, action="listado2", title="Z", url="http://www.vepelis.com/letra/z.html",
                         extra="http://www.vepelis.com/letra/z.html"))

    return itemlist


def listado2(item):
    logger.info()
    extra = item.extra
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = '<h2 class=titpeli.*?<a href=(.*?) title=(.*?)>.*?peli_img_img>.*?<img src=(.*?) alt.*?'
    patron += '<p>(.*?)<.*?Genero.*?:.*?(\d{4})<.*?png\/>(.*?)<.*?: (.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot, year, language, quality in matches:
        language = language.strip()
        itemlist.append(Item(channel=item.channel, action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                             url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, language=language,
                             quality=quality, infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    patron = '<span><b>(.*?)</b></span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for match in matches:
        nu = int(match[0]) + 1
        scrapedurl = extra + "?page=" + str(nu)
        scrapedtitle = "!Pagina Siguiente ->"
        scrapedthumbnail = ""
        itemlist.append(Item(channel=item.channel, action="listado2", title=scrapedtitle, fulltitle=scrapedtitle,
                             url=scrapedurl, thumbnail=scrapedthumbnail, extra=extra, folder=True))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "+")
    try:
        # Series
        item.url = "http://www.vepelis.com/buscar/?q=%s"
        item.url = item.url % texto
        item.extra = ""
        itemlist.extend(listado2(item))
        itemlist = sorted(itemlist, key=lambda Item: Item.title)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
