# -*- coding: utf-8 -*-
# -*- Channel CinemaHD -*-
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

host = 'http://www.cinemahd.co/'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Ultimas", action="list_all", url=host))
    itemlist.append(item.clone(title="Generos", action="section", section='genre'))
    itemlist.append(item.clone(title="Por Calidad", action="section", section='quality'))
    itemlist.append(item.clone(title="Por Año", action="section", section='year'))
    itemlist.append(item.clone(title="Alfabetico", action="section", section='alpha'))
    itemlist.append(item.clone(title="Buscar", action="search", url=host+'?s='))

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

    if item.section == 'alpha':
        patron = '<span class=Num>\d+.*?<a href=(.*?) class.*?<img src=(.*?) alt=.*?<strong>(.*?)</strong>.*?'
        patron += '<td>(\d{4})</td>.*?Qlty>(.*?)</span>'
    else:
        patron = '<article id=post-.*?<a href=(.*?)>.*?<img src=(.*?) alt=.*?'
        patron += '<h2 class=Title>(.*?)<\/h2>.*?<span class=Year>(.*?)<\/span>.*?Qlty>(.*?)<\/span>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, quality in matches:

        url = scrapedurl
        if "|" in scrapedtitle:
            scrapedtitle= scrapedtitle.split("|")
            contentTitle = scrapedtitle[0].strip()
        else:
            contentTitle = scrapedtitle

        contentTitle = re.sub('\(.*?\)','', contentTitle)

        title = '%s [%s] [%s]'%(contentTitle, year, quality)
        thumbnail = 'http:'+scrapedthumbnail
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentTitle=contentTitle,
                                   quality = quality,
                                   infoLabels={'year':year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'<a class=next.*?href=(.*?)>.*?»</a></div>')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    data = get_source(host)

    action = 'list_all'
    if item.section == 'quality':
        patron = 'menu-item-object-category.*?menu-item-\d+><a href=(.*?)>(.*?)<\/a>'
    elif item.section == 'genre':
        patron = '<a href=(http:.*?) class=Button STPb>(.*?)</a>'
    elif item.section == 'year':
        patron = 'menu-item-15\d+><a href=(.*?\?s.*?)>(\d{4})<\/a><\/li>'
    elif item.section == 'alpha':
        patron = '<li><a href=(.*?letters.*?)>(.*?)</a>'
        action = 'list_all'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        url = data_one
        title = data_two
        if title != 'Ver más':
            new_item = Item(channel=item.channel, title= title, url=url, action=action, section=item.section)
            itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    patron = 'id=(Opt\d+)>.*?src=(.*?) frameborder.*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, scrapedurl in matches:

        url= scrapedurl
        opt_data = scrapertools.find_single_match(data,'%s><span>.*?<strong>\d+<.*?</span>.*?<span>('
                                                       '.*?)</span>'%option).split('-')

        language = opt_data[0].strip()
        quality = opt_data[1].strip()

        if url != '':
            itemlist.append(item.clone(title='%s', url=url, language=language, quality=quality, action='play'))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return list_all(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host+'/animacion'
        elif categoria == 'terror':
            item.url = host+'/terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
