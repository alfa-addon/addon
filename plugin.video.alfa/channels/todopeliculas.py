# -*- coding: utf-8 -*-
# -*- Channel TodoPeliculas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import httptools
from core import scrapertools
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'cast': 'Castellano'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['torrent']

host = 'http://www.todo-peliculas.com/'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(item.clone(title="Ultimas", action="list_all", url=host+'torrents'))
    itemlist.append(item.clone(title="Por Calidad", action="section", url=host))
    itemlist.append(item.clone(title="Buscar", action="search", url=host+'buscar?searchword='))

    autoplay.show_option(item.channel, itemlist)

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
    if item.type == 'buscar':
        patron = '<div class=moditemfdb><a title=(.*?)\s+href=(.*?)><img.*?class=thumbnailresult src=(.*?)/>'
    elif item.type == 'section':
        patron = '<div class=blogitem >.*?href=(.*?)>.*?src=(.*?) alt.*?title=(.*?)>'
    else:
        patron = '<div class=blogitem ><a title=(.*?)\s+href=(.*?)>.*?src=(.*?) onload'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for info_1, info_2, info_3 in matches:

        if item.type != 'section':
            url = host+info_2
            quality = scrapertools.find_single_match(info_1, '\[(.*?)\]')
            contentTitle = re.sub(r'\[.*?\]', '', info_1)
            title = '%s [%s]'%(contentTitle, quality)
            thumbnail = info_3

        else:
            url = host + info_1
            quality = scrapertools.find_single_match(info_3, '\[(.*?)\]')
            contentTitle = re.sub(r'\[.*?\]', '', info_3)
            title = '%s [%s]' % (contentTitle, quality)
            thumbnail = info_2
            quality = ''

        if quality == '':
            title = title.replace('[]', '')

        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentTitle=contentTitle,
                                   quality = quality
                                   ))

    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'Anterior.*?<a href=/(.*?) title=Siguiente>Siguiente</a>')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=host+url_next_page, action='list_all'))
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    data = get_source(host)
    patron = '<li><a href=(.*?) rel=tag class=>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        url = scrapedurl
        title = scrapedtitle
        new_item = Item(channel=item.channel, title= title, url=url, action='list_all', type='section')
        itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    second_url = scrapertools.find_single_match(data, '<p><a href=(.*?) rel')

    data = get_source(host+second_url)
    url = scrapertools.find_single_match(data, "open\('(.*?)'")

    if url != '':
        quality = item.quality
        title = 'Torrent [%s]' % quality
        itemlist.append(item.clone(title=title, url=url, quality=quality, action='play', server='torrent',
                                   language='cast'))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'buscar'

    if texto != '':
        return list_all(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['torrent', 'peliculas']:
            item.url = host+'torrents'
        elif categoria == '4k':
            item.url = 'http://www.todo-peliculas.com/tags/4k'
            item.type='section'
        itemlist = list_all(item)

        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
