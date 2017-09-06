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

    itemlist = list()
    itemlist.append(
        Item(channel=item.channel, action="ultimos_capitulos", title="Últimos Capitulos", url="http://jkanime.net/"))
    itemlist.append(Item(channel=item.channel, action="ultimos", title="Últimos", url="http://jkanime.net/"))
    itemlist.append(Item(channel=item.channel, action="letras", title="Listado Alfabetico", url="http://jkanime.net/"))
    itemlist.append(Item(channel=item.channel, action="generos", title="Listado por Genero", url="http://jkanime.net/"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar"))

    return itemlist


def ultimos_capitulos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data, '<ul class="ratedul">.+?</ul>')

    data = data.replace('\t', '')
    data = data.replace('\n', '')
    data = data.replace('/thumbnail/', '/image/')

    patron = '<img src="(http://cdn.jkanime.net/assets/images/animes/.+?)" .+?href="(.+?)">(.+?)<.+?span>(.+?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumb, scrapedurl, scrapedtitle, scrapedepisode in matches:
        title = scrapedtitle.strip() + scrapedepisode
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = scrapedthumb
        plot = ""
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 show=scrapedtitle.strip(), fulltitle=title))

    return itemlist


def search(item, texto):
    logger.info()
    if item.url == "":
        item.url = "http://jkanime.net/buscar/%s/"
    texto = texto.replace(" ", "+")
    item.url = item.url % texto
    try:
        return series(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def ultimos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data, '<ul class="latestul">(.*?)</ul>')

    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = ""
        plot = ""
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

        itemlist.append(
            Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail, plot=plot))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data, '<div class="genres">(.*?)</div>')

    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = ""
        plot = ""
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

        itemlist.append(
            Item(channel=item.channel, action="series", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 viewmode="movie_with_plot"))

    return itemlist


def letras(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data, '<ul class="animelet">(.*?)</ul>')

    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = ""
        plot = ""
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

        itemlist.append(
            Item(channel=item.channel, action="series", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 viewmode="movie_with_plot"))

    return itemlist


def series(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas
    patron = '<table class="search[^<]+'
    patron += '<tr[^<]+'
    patron += '<td[^<]+'
    patron += '<a href="([^"]+)"><img src="([^"]+)"[^<]+</a>[^<]+'
    patron += '</td>[^<]+'
    patron += '<td><a[^>]+>([^<]+)</a></td>[^<]+'
    patron += '<td[^>]+>([^<]+)</td>[^<]+'
    patron += '<td[^>]+>([^<]+)</td>[^<]+'
    patron += '</tr>[^<]+'
    patron += '<tr>[^<]+'
    patron += '<td>(.*?)</td>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedthumbnail, scrapedtitle, line1, line2, scrapedplot in matches:
        title = scrapedtitle.strip() + " (" + line1.strip() + ") (" + line2.strip() + ")"
        extra = line2.strip()
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        thumbnail = thumbnail.replace("thumbnail", "image")
        plot = scrapertools.htmlclean(scrapedplot)
        logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

        itemlist.append(
            Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail,
                 plot=plot, extra=extra, show=scrapedtitle.strip()))

    try:
        siguiente = scrapertools.get_match(data, '<a class="listsiguiente" href="([^"]+)" >Resultados Siguientes')
        scrapedurl = urlparse.urljoin(item.url, siguiente)
        scrapedtitle = ">> Pagina Siguiente"
        scrapedthumbnail = ""
        scrapedplot = ""

        itemlist.append(
            Item(channel=item.channel, action="series", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 plot=scrapedplot, folder=True, viewmode="movie_with_plot"))
    except:
        pass
    return itemlist


def get_pages_and_episodes(data):
    results = re.findall('href="#pag([0-9]+)">[0-9]+ - ([0-9]+)', data)
    if results:
        return int(results[-1][0]), int(results[-1][1])
    return 1, 0


def episodios(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    scrapedplot = scrapertools.get_match(data, '<meta name="description" content="([^"]+)"/>')
    scrapedthumbnail = scrapertools.find_single_match(data, '<div class="separedescrip">.*?src="([^"]+)"')

    idserie = scrapertools.get_match(data, "ajax/pagination_episodes/(\d+)/")
    logger.info("idserie=" + idserie)
    if " Eps" in item.extra and "Desc" not in item.extra:
        caps_x = item.extra
        caps_x = caps_x.replace(" Eps", "")
        capitulos = int(caps_x)
        paginas = capitulos / 10 + (capitulos % 10 > 0)
    else:
        paginas, capitulos = get_pages_and_episodes(data)

    logger.info("idserie=" + idserie)
    for num_pag in range(1, paginas + 1):

        numero_pagina = str(num_pag)
        headers = {"Referer": item.url}
        data2 = scrapertools.cache_page("http://jkanime.net/ajax/pagination_episodes/%s/%s/" % (idserie, numero_pagina),
                                        headers=headers)
        # logger.info("data2=" + data2)

        patron = '"number"\:"(\d+)","title"\:"([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data2)

        # http://jkanime.net/get-backers/1/
        for numero, scrapedtitle in matches:
            title = scrapedtitle.strip()
            url = urlparse.urljoin(item.url, numero)
            thumbnail = scrapedthumbnail
            plot = scrapedplot
            logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumbnail + "]")

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                                 fanart=thumbnail, plot=plot, fulltitle=title))

    if len(itemlist) == 0:
        try:
            # porestrenar = scrapertools.get_match(data,
            #                                      '<div[^<]+<span class="labl">Estad[^<]+</span[^<]+<span[^>]+>Por estrenar</span>')
            itemlist.append(Item(channel=item.channel, action="findvideos", title="Serie por estrenar", url="",
                                 thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot,
                                 server="directo", folder=False))
        except:
            pass

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", httptools.downloadpage(item.url).data)

    list_videos = scrapertools.find_multiple_matches(data, '<iframe class="player_conte" src="([^"]+)"')
    aux_url = []
    index = 1
    for e in list_videos:
        if e.startswith("https://jkanime.net/jk.php?"):
            headers = {"Referer": item.url}
            data = httptools.downloadpage(e, headers=headers).data

            url = scrapertools.find_single_match(data, '<embed class="player_conte".*?&file=([^\"]+)\"')
            if url:
                itemlist.append(item.clone(title="Enlace encontrado en server #%s" % index, url=url, action="play"))
                index += 1

        else:
            aux_url.append(e)

    itemlist.extend(servertools.find_video_items(data=",".join(aux_url)))
    for videoitem in itemlist:
        videoitem.fulltitle = item.fulltitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail

    return itemlist
