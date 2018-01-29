# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

CHANNEL_HOST = "https://www.animeid.tv/"

def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(
        Item(channel=item.channel, action="novedades_series", title="Últimas series", url=CHANNEL_HOST))
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios",
                         url=CHANNEL_HOST, viewmode="movie_with_plot"))
    itemlist.append(
        Item(channel=item.channel, action="generos", title="Listado por genero", url=CHANNEL_HOST))
    itemlist.append(
        Item(channel=item.channel, action="letras", title="Listado alfabetico", url=CHANNEL_HOST))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar..."))

    return itemlist


def newest(categoria):
    itemlist = []
    item = Item()
    try:
        if categoria == 'anime':
            item.url = CHANNEL_HOST
            itemlist = novedades_episodios(item)
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    return itemlist


# todo ARREGLAR
def search(item, texto):
    logger.info()
    itemlist = []

    if item.url == "":
        item.url = CHANNEL_HOST + "ajax/search?q="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        headers = []
        headers.append(
            ["User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:19.0) Gecko/20100101 Firefox/19.0"])
        headers.append(["Referer", CHANNEL_HOST])
        headers.append(["X-Requested-With", "XMLHttpRequest"])
        data = scrapertools.cache_page(item.url, headers=headers)
        data = data.replace("\\", "")
        patron = '{"id":"([^"]+)","text":"([^"]+)","date":"[^"]*","image":"([^"]+)","link":"([^"]+)"}'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for id, scrapedtitle, scrapedthumbnail, scrapedurl in matches:
            title = scrapedtitle
            url = urlparse.urljoin(item.url, scrapedurl)
            thumbnail = scrapedthumbnail
            plot = ""
            itemlist.append(
                Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail, plot=plot,
                     show=title, viewmode="movie_with_plot"))

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def novedades_series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="series">(.*?)</section>')
    patronvideos = '(?s)<a href="([^"]+)">.*?tipo\d+">([^<]+)</span>.*?<strong>([^<]+)</strong>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    for url, tipo, title in matches:
        scrapedtitle = title + " (" + tipo + ")"
        scrapedurl = urlparse.urljoin(item.url, url)
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl,
                             show=title, viewmode="movie_with_plot"))
    return itemlist


def novedades_episodios(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<section class="lastcap">(.*?)</section>')
    patronvideos  = '(?s)<a href="([^"]+)">[^<]+<header>([^<]+).*?src="([^"]+)"[\s\S]+?<p>(.+?)</p>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    itemlist = []
    for url, title, thumbnail, plot in matches:
        scrapedtitle = scrapertools.entityunescape(title)
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = thumbnail
        scrapedplot = plot
        episodio = scrapertools.find_single_match(scrapedtitle, '\s+#(.*?)$')
        contentTitle = scrapedtitle.replace('#' + episodio, '')
        itemlist.append(Item(channel=item.channel, action="findvideos", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot, contentSeason=1, contentTitle=contentTitle))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<div class="generos">(.*?)</div>')
    patronvideos = '(?s)<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    for url, title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel, action="series", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 plot=scrapedplot, show=title, viewmode="movie_with_plot"))
    return itemlist


def letras(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<ul id="letras">(.*?)</ul>')
    patronvideos = '<li> <a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    itemlist = []
    for url, title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url, url)
        itemlist.append(
            Item(channel=item.channel, action="series", title=scrapedtitle, url=scrapedurl,
                 show=title, viewmode="movie_with_plot"))

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?s)<article class="item"[^<]+'
    patron += '<a href="([^"]+)"[^<]+<header>([^<]+)</header[^<]+.*?'
    patron += 'src="([^"]+)".*?<p>(.*?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, title, thumbnail, plot in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = thumbnail
        scrapedplot = plot
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot, show=scrapedtitle,
                             viewmode="movie_with_plot"))
    itemlist = sorted(itemlist, key=lambda it: it.title)
    try:
        page_url = scrapertools.find_single_match(data, '<li><a href="([^"]+)">&gt;</a></li>')
        itemlist.append(Item(channel=item.channel, action="series", title=">> Página siguiente",
                             url=urlparse.urljoin(item.url, page_url), viewmode="movie_with_plot", thumbnail="",
                             plot=""))
    except:
        pass
    return itemlist


def episodios(item, final=True):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data_id = scrapertools.find_single_match(data, 'data-id="([^"]+)')
    CHANNEL_HEADERS = [
    ["Host", "m.animeid.tv"],
    ["X-Requested-With", "XMLHttpRequest"]
    ]
    page = 0
    while True:
        page += 1
        u = "https://m.animeid.tv/ajax/caps?id=%s&ord=DESC&pag=%s" %(data_id, page)
        data = httptools.downloadpage(u, headers=CHANNEL_HEADERS).data
        # Cuando ya no hay datos devuelve: "list":[]
        if '"list":[]' in data:
            break
        dict_data = jsontools.load(data)
        list = dict_data['list']
        for dict in list:
             itemlist.append(Item(action = "findvideos",
                                  channel = item.channel,
                                  title = "1x" + dict["numero"] + " - " + dict["date"],
                                  url = CHANNEL_HOST + dict['href'],
                                  thumbnail = item.thumbnail,
                                  show = item.show,
                                  viewmode = "movie_with_plot"
                                  ))
    if config.get_videolibrary_support():
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show))
        itemlist.append(Item(channel=item.channel, title="Descargar todos los episodios de la serie", url=item.url,
                             action="download_all_episodes", extra="episodios", show=item.show))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url_anterior = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">« Capítulo anterior')
    url_siguiente = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">Siguiente capítulo »')
    data = scrapertools.find_single_match(data, '<ul id="partes">(.*?)</ul>').decode("unicode-escape")
    data = data.replace("\\/", "/").replace("%3A", ":").replace("%2F", "/")
    patron = '(https://www.animeid.tv/stream/[^/]+/\d+.[a-z0-9]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    encontrados = set()
    for url in matches:
        if url not in encontrados:
            itemlist.append(
                Item(channel=item.channel, action="play", title="[directo]", server="directo", url=url, thumbnail="",
                     plot="", show=item.show, folder=False))
            encontrados.add(url)
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.action = "play"
        videoitem.folder = False
        videoitem.title = "[" + videoitem.server + "]"
    if url_anterior:
        title_anterior = url_anterior.strip("/v/").replace('-', ' ').strip('.html')
        itemlist.append(Item(channel=item.channel, action="findvideos", title="Anterior: " + title_anterior,
                             url=CHANNEL_HOST + url_anterior, thumbnail=item.thumbnail, plot=item.plot, show=item.show,
                             fanart=item.thumbnail, folder=True))

    if url_siguiente:
        title_siguiente = url_siguiente.strip("/v/").replace('-', ' ').strip('.html')
        itemlist.append(Item(channel=item.channel, action="findvideos", title="Siguiente: " + title_siguiente,
                             url=CHANNEL_HOST + url_siguiente, thumbnail=item.thumbnail, plot=item.plot, show=item.show,
                             fanart=item.thumbnail, folder=True))
    return itemlist
