# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = 'https://yonkis.to'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="alfabetico", title="Listado alfabetico", url=host))
    itemlist.append(Item(channel=item.channel, action="mas_vistas", title="Series más vistas",
                         url=host + "/series-mas-vistas"))
    itemlist.append(Item(channel=item.channel, action="ultimos", title="Últimos episodios añadidos",
                         url=host))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host + "/buscar/serie"))

    return itemlist


def alfabetico(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="series", title="0-9", url=host + "/lista-de-series/0-9"))
    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        itemlist.append(Item(channel=item.channel, action="series", title=letra, url=host+"/lista-de-series/"+letra))

    return itemlist


def mas_vistas(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    matches = re.compile('<a title="([^"]+)" href="([^"]+)".*?src="([^"]+)".*?</a>', re.S).findall(data)

    itemlist = []
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        scrapedthumbnail = urlparse.urljoin(item.url, scrapedthumbnail.replace("/90/", "/150/"))

        itemlist.append(
            Item(channel=item.channel, action="episodios", title=scrapedtitle, fulltitle=scrapedtitle, url=scrapedurl,
                 thumbnail=scrapedthumbnail, show=scrapedtitle, fanart=item.fanart))

    return itemlist


def search(item, texto):
    logger.info()

    itemlist = []
    post = "keyword=%s&search_type=serie" % texto
    data = httptools.downloadpage(item.url, post=post).data

    try:
        patron = '<a href="([^"]+)" title="([^"]+)"><img.*?src="([^"]+)".*?class="content">([^<]+)</div>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl, scrapedtitle, scrapedthumb, scrapedplot in matches:
            title = scrapedtitle.strip()
            url = host + scrapedurl
            thumb = host + scrapedthumb.replace("/90/", "/150/")
            plot = re.sub(r"\n|\r|\t|\s{2,}", "", scrapedplot.strip())
            logger.debug("title=[" + title + "], url=[" + url + "], thumbnail=[" + thumb + "]")

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, fulltitle=title, url=url,
                                 thumbnail=thumb, plot=plot, show=title))

        return itemlist
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def ultimos(item):
    logger.info()

    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    logger.debug("data %s" % data)
    matches = re.compile('data-href="([^"]+)" data-src="([^"]+)" data-alt="([^"]+)".*?<a[^>]+>(.*?)</a>', re.S).findall(data)

    for url, thumb, show, title in matches:

        url = host + url

        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=thumb, show=show.strip(),
                             action="findvideos", fulltitle=title))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)

    matches = scrapertools.find_single_match(data, '<ul id="list-container" class="dictionary-list">(.*?)</ul>')
    matches = re.compile('title="([^"]+)" href="([^"]+)"', re.S).findall(matches)
    for title, url in matches:
        itemlist.append(Item(channel=item.channel, action="episodios", title=title, fulltitle=title,
                             url=urlparse.urljoin(item.url, url), thumbnail=item.thumbnail, show=title))

    # Paginador
    matches = re.compile('<a href="([^"]+)">></a>', re.S).findall(data)

    paginador = None
    if len(matches) > 0:
        paginador = Item(channel=item.channel, action="series", title="!Página siguiente",
                         url=urlparse.urljoin(item.url, matches[0]), thumbnail=item.thumbnail, show=item.show)

    if paginador and len(itemlist) > 0:
        itemlist.insert(0, paginador)
        itemlist.append(paginador)

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []

    # Descarga la pagina
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)

    pattern = '<meta property="og:description" content="([^/]+)" /><meta property="og:image" content="([^"]+)"'
    plot, thumb = scrapertools.find_single_match(data, pattern)

    matches = re.compile('<a class="episodeLink p1" href="([^"]+)"><strong>(.*?)</strong>(.*?)</a>', re.S).findall(data)

    for url, s_e, title in matches:
        url = host + url
        title = s_e.strip() + title
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=thumb, show=item.show, plot=plot,
                             action="findvideos", fulltitle=title))

    if config.get_videolibrary_support():
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show))
        itemlist.append(Item(channel=item.channel, title="Descargar todos los episodios de la serie", url=item.url,
                             action="download_all_episodes", extra="episodios", show=item.show))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)

    pattern = '<a href="([^"]+)"[^>]+><img[^>]+alt="([^"]+)" /></a></td><td class="episode-lang"><span ' \
              'class="flags[^"]+" title="([^"]+)"'

    matches = re.compile(pattern, re.S).findall(data)

    for url, server, lang in matches:
        title = "[%s] - [%s]" % (lang, server)
        url = host + url
        logger.debug("url %s" % url)
        itemlist.append(Item(channel=item.channel, action="play", title=title, fulltitle=item.fulltitle, url=url,
                        thumbnail=item.thumbnail, lang=lang))

    return itemlist


def play(item):
    logger.info()

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)

    itemlist = servertools.find_video_items(data=data)

    for video_item in itemlist:
        video_item.title = "%s [%s]" % (item.fulltitle, item.lang)
        video_item.thumbnail = item.thumbnail

    return itemlist
