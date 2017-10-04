# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger

host = 'http://www.sipeliculas.com'


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(item.clone(title="Novedades", action="lista", url=host + "/cartelera/"))
    itemlist.append(item.clone(title="Actualizadas", action="lista", url=host + "/peliculas-actualizadas/"))
    itemlist.append(item.clone(title="Recomendadas", action="lista", url=host + "/peliculas-recomendadas/"))
    itemlist.append(item.clone(title="Categorias", action="menuseccion", url=host, extra="/online/"))
    itemlist.append(item.clone(title="Año", action="menuseccion", url=host, extra="/estrenos-gratis/"))
    itemlist.append(item.clone(title="Alfabetico", action="alfabetica", url=host + '/mirar/'))
    itemlist.append(item.clone(title="Buscar", action="search", url=host + "/ver/"))

    return itemlist


def alfabetica(item):
    logger.info()
    itemlist = []
    for letra in "1abcdefghijklmnopqrstuvwxyz":
        itemlist.append(item.clone(title=letra.upper(), url=item.url + letra, action="lista"))

    return itemlist


def menuseccion(item):
    logger.info()
    itemlist = []
    seccion = item.extra
    data = httptools.downloadpage(item.url).data

    if seccion == '/online/':
        data = scrapertools.find_single_match(data,
                                              '<h2 class="[^"]+"><i class="[^"]+"></i>Películas por géneros<u class="[^"]+"></u></h2>(.*?)<ul class="abc">')
        patron = '<li ><a href="([^"]+)" title="[^"]+"><i class="[^"]+"></i>([^<]+)</a></li>'
    elif seccion == '/estrenos-gratis/':
        data = scrapertools.find_single_match(data, '<ul class="lista-anio" id="lista-anio">(.*?)</ul>')
        patron = '<li ><a href="([^"]+)" title="[^"]+">([^<]+)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, extra in matches:
        itemlist.append(Item(channel=item.channel, action='lista', title=extra, url=scrapedurl))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    listado = scrapertools.find_single_match(data,
                                             '<div id="sipeliculas" class="borde"><div class="izquierda">(.*?)<div class="derecha"><h2')
    patron = '<a class="i" href="(.*?)".*?src="(.*?)".*?title=.*?>(.*?)<.*?span>(.*?)<.*?<p><span>(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(listado)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year,  plot in matches:
        itemlist.append(Item(channel=item.channel, action='findvideos', title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=plot, contentTitle=scrapedtitle, extra=item.extra,
                             infoLabels ={'year':year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion
    if itemlist != []:
        patron = '<li[^<]+<a href="([^"]+)" title="[^"]+">Siguiente[^<]+</a></li>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if matches:
            itemlist.append(
                item.clone(title="Pagina Siguiente", action='lista', url=urlparse.urljoin(host, matches[0])))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = item.url + texto
    if texto != '':
        return lista(item)
    else:
        return []


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    listado1 = scrapertools.find_single_match(data,
                                              '<div class="links" id="ver-mas-opciones"><h2 class="h2"><i class="[^"]+"></i>[^<]+</h2><ul class="opciones">(.*?)</ul>')
    patron1 = '<li ><a id="([^"]+)" rel="nofollow" href="([^"]+)" title="[^"]+" alt="([^"]+)"><span class="opcion"><i class="[^"]+"></i><u>[^<]+</u>[^<]+</span><span class="ico"><img src="[^"]+" alt="[^"]+"/>[^<]+</span><span>([^"]+)</span><span>([^"]+)</span></a></li>'
    matches = matches = re.compile(patron1, re.DOTALL).findall(listado1)
    for vidId, vidUrl, vidServer, language, quality in matches:
        server = servertools.get_server_name(vidServer)
        if 'Sub' in language:
            language='sub'
        itemlist.append(Item(channel=item.channel, action='play', url=vidUrl, extra=vidId,
                             title='Ver en ' + vidServer + ' | ' + language + ' | ' + quality,
                             thumbnail=item.thumbnail, server=server, language=language, quality=quality ))

    listado2 = scrapertools.find_single_match(data, '<ul class="opciones-tab">(.*?)</ul>')
    patron2 = '<li ><a id="([^"]+)" rel="nofollow" href="([^"]+)" title="[^"]+" alt="([^"]+)"><img src="[^"]+" alt="[^"]+"/>[^<]+</a></li>'
    matches = matches = re.compile(patron2, re.DOTALL).findall(listado2)
    for vidId, vidUrl, vidServer in matches:
        server = servertools.get_server_name(vidServer)
        itemlist.append(Item(channel=item.channel, action='play', url=vidUrl, extra=vidId, title='Ver en ' + vidServer,
                             thumbnail=item.thumbnail, server=server))

    for videoitem in itemlist:
        videoitem.fulltitle = item.title
        videoitem.folder = False

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    video = httptools.downloadpage(host + '/ajax.public.php', 'acc=ver_opc&f=' + item.extra).data
    logger.info("video=" + video)
    enlaces = servertools.findvideos(video)
    if enlaces:
        logger.info("server=" + enlaces[0][2])
        thumbnail = servertools.guess_server_thumbnail(video)
        # Añade al listado de XBMC
        itemlist.append(
            Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=enlaces[0][1],
                 server=enlaces[0][2], thumbnail=thumbnail, folder=False))

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/cartelera/'
        elif categoria == 'infantiles':
            item.url = host + "/online/animacion"
        elif categoria == 'terror':
            item.url = host + "/online/terror/"
        else:
            return []

        itemlist = lista(item)
        if itemlist[-1].title == "» Siguiente »":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist