# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from bs4 import BeautifulSoup
from core import httptools, jsontools, scrapertools, servertools, tmdb
from core.item import Item
from platformcode import config, logger
from channels import renumbertools, autoplay

CHANNEL_HOST = "https://www.animeid.tv/"

IDIOMAS = {'Latino': 'LAT', 'VOSE': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['animeid']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
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

    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)

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
        data = httptools.downloadpage(item.url, headers=headers).data
        data = data.replace("\\", "")
        patron = '{"id":"([^"]+)","text":"([^"]+)","date":"[^"]*","image":"([^"]+)","link":"([^"]+)"}'
        matches = scrapertools.find_multiple_matches(data, patron)

        for id, scrapedtitle, scrapedthumbnail, scrapedurl in matches:
            title = scrapedtitle
            url = urlparse.urljoin(item.url, scrapedurl)
            thumbnail = scrapedthumbnail
            plot = ""
            context = renumbertools.context(item)
            context2 = autoplay.context
            context.extend(context2)
            itemlist.append(
                Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail, plot=plot,
                     context=context, show=title, viewmode="movie_with_plot"))

        tmdb.set_infoLabels(itemlist, seekTmdb=True)
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
    data = scrapertools.find_single_match(data, '<ol class="reciente tab" data-tab="2">(.*?)</section>')
    patronvideos = '(?s)<a href="([^"]+)">.*?tipo\d+">([^<]+)</span>.*?<strong>([^<]+)</strong>'
    matches = scrapertools.find_multiple_matches(data, patronvideos)
    for url, tipo, title in matches:
        scrapedtitle = title + " (" + tipo + ")"
        scrapedurl = urlparse.urljoin(item.url, url)
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl,
                             context=context, show=title, viewmode="movie_with_plot"))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def novedades_episodios(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '(?is)<section class="lastcap">(.*?)</section>')
    patronvideos = '<article><a href="([^"]+)"><header>([^<]+).*?src="([^"]+)" class="cove'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)
    itemlist = []
    for url, title, thumbnail in matches:
        scrapedtitle = scrapertools.entityunescape(title)
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = thumbnail
        episodio = scrapertools.find_single_match(scrapedtitle, '\s+#(.*?)$')
        contentTitle = scrapedtitle.replace('#' + episodio, '')
        itemlist.append(Item(channel=item.channel, action="findvideos", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, show=contentTitle))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
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
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot, show=scrapedtitle, context=context,
                             viewmode="movie_with_plot"))
    itemlist = sorted(itemlist, key=lambda it: it.title)
    try:
        page_url = scrapertools.find_single_match(data, '<li><a href="([^"]+)">&gt;</a></li>')
        itemlist.append(Item(channel=item.channel, action="series", title="[COLOR cyan]>> Página siguiente[/COLOR]",
                             url=urlparse.urljoin(item.url, page_url), viewmode="movie_with_plot", thumbnail="",
                             plot=""))
    except:
        pass
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def episodios(item, final=True):
    logger.info()
    itemlist = []
    infoLabels=item.infoLabels
    data = httptools.downloadpage(item.url).data
    data_id = scrapertools.find_single_match(data, 'data-id="([^"]+)')
    CHANNEL_HEADERS = [
        ["Host", "m.animeid.tv"],
        ["X-Requested-With", "XMLHttpRequest"]
    ]
    page = 0
    while True:
        page += 1
        u = "https://m.animeid.tv/ajax/caps?id=%s&ord=DESC&pag=%s" % (data_id, page)
        data = httptools.downloadpage(u, headers=CHANNEL_HEADERS).data
        # Cuando ya no hay datos devuelve: "list":[]
        if '"list":[]' in data:
            break
        dict_data = jsontools.load(data)
        list = dict_data['list'][::-1]
        for dict in list:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.show, 1,
                                                               int(dict["numero"]))
            title = "%sx%s - %s" % (season, str(episode).zfill(2), dict["date"])
            infoLabels['season'] = season
            infoLabels['episode'] = episode
            itemlist.append(Item(action="findvideos",
                                 channel=item.channel,
                                 title=title,
                                 url=CHANNEL_HOST + dict['href'],
                                 thumbnail=item.thumbnail,
                                 show=item.show,
                                 infoLabels=infoLabels,
                                 viewmode="movie_with_plot"
                                 ))
    if config.get_videolibrary_support():
        itemlist.append(
            Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                 action="add_serie_to_library", extra="episodios", show=item.show))
        itemlist.append(
            Item(channel=item.channel, title="[COLOR white]Descargar todos los episodios de la serie[/COLOR]",
                 url=item.url,
                 action="download_all_episodes", extra="episodios", show=item.show))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = str(BeautifulSoup(httptools.downloadpage(item.url).data, "html5lib", from_encoding="utf-8"))
    url_anterior = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">« Capítulo anterior')
    url_siguiente = scrapertools.find_single_match(data, '<li class="b"><a href="([^"]+)">Siguiente capítulo »')
    data = scrapertools.find_single_match(data, '(?is)<ul id="partes">(.*?)</ul>')
    data = str(BeautifulSoup(data, "html5lib", from_encoding="utf-8").find('div', class_='parte')['data'])
    data = jsontools.load(data.replace("'", '"'))['v']
    patron = '(?is)src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    encontrados = ''
    for url in matches:
        if url not in encontrados:
            if scrapertools.find_single_match(url, '\w\d+.animeid.tv/netu.+?='):
                temp_data = httptools.downloadpage(url).data
                url = scrapertools.find_single_match(temp_data, patron)
            encontrados = '{};{}'.format(url, encontrados)
    temp_item = item
    itemlist.extend(servertools.find_video_items(item=temp_item, data=encontrados))
    # itemlist.extend(servertools.get_servers_itemlist(itemlist))
    for videoitem in itemlist:
        videoitem.action = "play"
        videoitem.channel = item.channel
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

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    if "vid=" in item.url:
        data = httptools.downloadpage(item.url).data
        logger.info("Intel11 %s" %data)
        url = scrapertools.find_single_match(data, '(?is)SRC="([^"]+)')
        logger.info("Intel22 %s" %url)
        if "clipwatching" in url:
            item.server = "clipwatching"
            item.url = url
    return [item]
