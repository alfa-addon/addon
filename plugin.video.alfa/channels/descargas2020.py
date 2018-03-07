# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from core import servertools
from core import scrapertools
from core.item import Item
from platformcode import logger
from core import httptools
from channelselector import get_thumb

Host='http://descargas2020.com'


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas",url=Host+"/peliculas/",
                         thumbnail=get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series",url=Host+"/series/",
                         thumbnail=get_thumb('tvshows', auto=True)))
    #itemlist.append(Item(channel=item.channel, action="listado", title="Anime", url=Host+"/anime/",
    #                     viewmode="movie_with_plot"))
    #itemlist.append(
    #    Item(channel=item.channel, action="listado", title="Documentales", url=Host+"/documentales/",
    #         viewmode="movie_with_plot"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url= Host+'/buscar',
                         thumbnail=get_thumb('search', auto=True)))
    return itemlist

def submenu(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li><a href="'+item.url+'"><i.+?<ul>(.+?)<\/ul>' #Filtrado por url
    data_cat = scrapertools.find_single_match(data, patron)
    patron_cat='<li><a href="(.+?)" title="(.+?)".+?<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_cat, patron_cat)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl,action="listado"))
    if 'peliculas' in item.url:
        new_item = item.clone(title='Peliculas 4K', url=Host+'/buscar', post='q=4k', action='listado2',
                              pattern='buscar-list')
        itemlist.append(new_item)
    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_data='<ul class="pelilist">(.+?)</ul>'
    data_listado = scrapertools.find_single_match(data, patron_data)
    patron_listado='<li><a href="(.+?)" title=".+?"><img src="(.+?)".+?><h2'
    if 'Serie' in item.title:
        patron_listado+='.+?>'
    else:
        patron_listado+='>'
    patron_listado+='(.+?)<\/h2><span>(.+?)<\/span><\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_listado, patron_listado)

    for scrapedurl, scrapedthumbnail,scrapedtitle,scrapedquality in matches:

        new_item = item.clone(title=scrapedtitle, url=scrapedurl,thumbnail=scrapedthumbnail, quality=scrapedquality)

        if 'Serie' in item.title:
            new_item.action="episodios"
            new_item.contentSerieName = scrapedtitle
            new_item.contentType = 'tvshow'
        else:
            new_item.action="findvideos"
            new_item.contentTitle = scrapedtitle
            new_item.contentType = 'movie'
        itemlist.append(new_item)
    # Página siguiente
    patron_pag='<ul class="pagination"><li><a class="current" href=".+?">.+?<\/a>.+?<a href="(.+?)">'
    siguiente = scrapertools.find_single_match(data, patron_pag)
    itemlist.append(
             Item(channel=item.channel, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=siguiente, action="listado"))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_data='<ul class="buscar-list">(.+?)</ul>'
    data_listado = scrapertools.find_single_match(data, patron_data)
    patron = '<img src="(.+?)" alt=".+?">.+?<div class=".+?">.+?<a href=(.+?)" title=".+?">.+?>Serie.+?>(.+?)<'
    matches = scrapertools.find_multiple_matches(data_listado, patron)
    for scrapedthumbnail,scrapedurl, scrapedtitle in matches:
        if " al " in scrapedtitle:
            #action="episodios"
            titulo=scrapedurl.split('http')
            scrapedurl="http"+titulo[1]
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl,thumbnail=scrapedthumbnail,
                                   action="findvideos", show=scrapedtitle))
    return itemlist


def listado2(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    list_chars = [["Ã±", "ñ"]]
    for el in list_chars:
        data = re.sub(r"%s" % el[0], el[1], data)
    try:
        get, post = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a class="current" href.*?'
                                                         '<a\s*href="([^"]+)"(?:\s*onClick=".*?\'([^"]+)\'.*?")')
    except:
        post = False

    if post:
        if "pg" in item.post:
            item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
        else:
            item.post += "&pg=%s" % post

    pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
    data = scrapertools.get_match(data, pattern)


    pattern = '<li><a href="(?P<url>[^"]+)".*?<img src="(?P<img>[^"]+)"[^>]+>.*?<h2.*?>\s*(?P<title>.*?)\s*</h2>'
    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url, thumb, title in matches:
        title = scrapertools.htmlclean(title)
        title = title.replace("ï¿½", "ñ")

        # no mostramos lo que no sean videos
        if "descargar-juego/" in url or "/varios/" in url:
            continue

        if ".com/series" in url:

            show = title

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumb,
                                 context=["buscar_trailer"], show=show))

        else:
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                     context=["buscar_trailer"]))

    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado2", title="[COLOR cyan]Página Siguiente >>[/COLOR]",
                                   thumbnail=''))

    return itemlist


def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.post = "q=%s" % texto
        item.pattern = "buscar-list"
        itemlist = listado2(item)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def findvideos(item):
    logger.info()
    itemlist = []
    new_item = []
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data = data)
    url = scrapertools.find_single_match(data, 'location.href = "([^"]+)"')
    new_item.append(Item(url = url, title = "Torrent", server = "torrent", action = "play"))
    if url != '':
        itemlist.extend(new_item)
    for it in itemlist:
        it.channel = item.channel
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = Host+'/peliculas-hd/'
            action = listado(item)
        if categoria == '4k':
            item.url = Host + '/buscar'
            item.post = 'q=4k'
            item.pattern = 'buscar-list'
            action = listado2(item)

        itemlist = action
        if itemlist[-1].title == "[COLOR cyan]Página Siguiente >>[/COLOR]":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist