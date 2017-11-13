# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://www.peliculashindu.com/"


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Top Películas", url=urlparse.urljoin(host, "top")))
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host))
    itemlist.append(Item(channel=item.channel, action="explorar", title="Género", url=urlparse.urljoin(host, "genero")))
    itemlist.append(Item(channel=item.channel, action="explorar", title="Listado Alfabético",
                         url=urlparse.urljoin(host, "alfabetico")))
    # itemlist.append(Item(channel=item.channel, action="explorar", title="Listado por año", url=urlparse.urljoin(host, "año")))
    itemlist.append(Item(channel=item.channel, action="lista", title="Otras Películas (No Bollywood)",
                         url=urlparse.urljoin(host, "estrenos")))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "buscar-")))
    return itemlist


def explorar(item):
    logger.info()
    itemlist = list()
    url1 = item.title
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if 'Género' in url1:
        patron = '<div class="d">.+?<h3>Pel.+?neros<\/h3>(.+?)<\/h3>'
    if 'Listado Alfabético' in url1:
        patron = '<\/li><\/ul>.+?<h3>Pel.+?tico<\/h3>(.+?)<\/h3>'
    if 'Año' in url1:
        patron = '<ul class="anio"><li>(.+?)<\/ul>'
    data_explorar = scrapertools.find_single_match(data, patron)
    patron_explorar = '<a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data_explorar, patron_explorar)
    for scrapedurl, scrapedtitle in matches:
        if 'Acci' in scrapedtitle:
            scrapedtitle = 'Acción'
        if 'Anima' in scrapedtitle:
            scrapedtitle = 'Animación'
        if 'Fanta' in scrapedtitle:
            scrapedtitle = 'Fantasía'
        if 'Hist' in scrapedtitle:
            scrapedtitle = 'Histórico'
        if 'lico Guerra' in scrapedtitle:
            scrapedtitle = 'Bélico Guerra'
        if 'Ciencia' in scrapedtitle:
            scrapedtitle = 'Ciencia Ficción'
        itemlist.append(item.clone(action='lista', title=scrapedtitle, url=scrapedurl))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = item.url + texto
    # logger.info("item="+item.url)
    if texto != '':
        return lista(item)


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    data_mov= scrapertools.find_single_match(data,'<div id="cuerpo"><div class="iz">(.+)<ul class="pag">')
    patron = '<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)"'  # scrapedurl, scrapedthumbnail, scrapedtitle
    matches = scrapertools.find_multiple_matches(data_mov, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:  # scrapedthumbnail, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, action="findvideos",
                                   show=scrapedtitle))
    # Paginacion
    patron_pag = '<a href="([^"]+)" title="Siguiente .+?">'
    paginasig = scrapertools.find_single_match(data, patron_pag)
    logger.info("algoooosadf "+paginasig)

    next_page_url = host + paginasig

    if paginasig != "":
        item.url = next_page_url
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=next_page_url,
                             thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    itemlist.extend(servertools.find_video_items(data=data))
    logger.info("holaa" + data)
    patron_show = '<strong>Ver Pel.+?a([^<]+) online<\/strong>'
    show = scrapertools.find_single_match(data, patron_show)
    for videoitem in itemlist:
        videoitem.channel = item.channel
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.contentChannel!='videolibrary':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=show))

    return itemlist
