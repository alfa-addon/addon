# -*- coding: utf-8 -*-
# -*- Channel OH!Latino -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.ohpeliculas.com'

def mainlist(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(host).data
    patron = '<li class="cat-item cat-item-\d+"><a href="(.*?)" >(.*?)<\/a> <i>(\d+)<\/i>'
    matches = scrapertools.find_multiple_matches(data, patron)
    mcantidad = 0
    for scrapedurl, scrapedtitle, cantidad in matches:
        mcantidad += int(cantidad)

    itemlist.append(
        item.clone(title="Peliculas",
                   action='movies_menu'
                   ))

    itemlist.append(
        item.clone(title="Buscar",
                   action="search",
                   url=host+'?s=',
                   ))

    return itemlist


def movies_menu(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Todas",
                   action="list_all",
                   url=host
                   ))

    itemlist.append(
        item.clone(title="Generos",
                   action="section",
                   url=host, extra='genres'))

    itemlist.append(
        item.clone(title="Por año",
                   action="section",
                   url=host, extra='byyear'
                   ))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<div id=mt-.*? class=item>.*?<a href=(.*?)><div class=image>.*?'
    patron +='<img src=(.*?) alt=.*?span class=tt>(.*?)<.*?ttx>(.*?)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot in matches:
        url = scrapedurl
        action = 'findvideos'
        thumbnail = scrapedthumbnail
        contentTitle = scrapedtitle
        plot = scrapedplot
        title = contentTitle

        filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w185", "")
        filtro_list = {"poster_path": filtro_thumb}
        filtro_list = filtro_list.items()

        itemlist.append(Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=url,
                             plot=plot,
                             thumbnail=thumbnail,
                             contentTitle=contentTitle,
                             infoLabels={'filtro': filtro_list}
                             ))
    #tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data,
                                                   'alignleft><a href=(.*?) ><\/a><\/div><div class=nav-next alignright>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="list_all",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png'
                                 ))
    return itemlist


def section(item):
    logger.info()

    itemlist = []
    duplicated =[]
    data = httptools.downloadpage(item.url).data
    if item.extra == 'genres':
        patron = '<li class="cat-item cat-item-.*?><a href="(.*?)" >(.*?)<\/a>'
    elif item.extra == 'byyear':
        patron = '<a href="([^"]+)">(\d{4})<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = scrapedurl
        if url not in duplicated:
            itemlist.append(Item(channel=item.channel,
                                 action='list_all',
                                 title=title,
                                 url=url
                                 ))
            duplicated.append(url)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return list_all(item)


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.contentTitle = item.fulltitle
        videoitem.infoLabels = item.infoLabels
        if videoitem.server != 'youtube':
            videoitem.title = item.title + ' (%s)' % videoitem.server
        else:
            videoitem.title = 'Trailer en %s' % videoitem.server
        videoitem.action = 'play'
        videoitem.server = ""

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 ))
    tmdb.set_infoLabels(itemlist, True)
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/release/2017/'

        elif categoria == 'infantiles':
            item.url = host + '/genero/infantil/'

        itemlist = list_all(item)
        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist

def play(item):
    logger.info()
    item.thumbnail = item.contentThumbnail
    return [item]
