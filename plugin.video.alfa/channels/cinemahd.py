# -*- coding: utf-8 -*-
# -*- Channel CinemaHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


host = 'http://www.cinemahd.co/'

IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['fastplay', 'rapidvideo', 'streamplay', 'flashx', 'streamito', 'streamango', 'vidoza']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(item.clone(title="Ultimas", action="list_all", url=host, thumbnail=get_thumb('last', auto=True)))
    itemlist.append(item.clone(title="Generos", action="section", section='genre',
                               thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Por Calidad", action="section", section='quality',
                               thumbnail=get_thumb('quality', auto=True)))
    itemlist.append(item.clone(title="Por Año", action="section", section='year',
                               thumbnail=get_thumb('year', auto=True)))
    itemlist.append(item.clone(title="Alfabetico", action="section", section='alpha',
                               thumbnail=get_thumb('alphabet', auto=True)))
    itemlist.append(item.clone(title="Buscar", action="search", url=host+'?s=',
                               thumbnail=get_thumb('search', auto=True)))

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
    if item.section == 'alpha':
        patron = '<span class=Num>\d+.*?<a href=(.*?) class.*?<img src=(.*?) alt=.*?<strong>(.*?)</strong>.*?'
        patron += '<td>(\d{4})</td>'
    else:
        patron = '<article id=post-.*?<a href=(.*?)>.*?<img src=(.*?) alt=.*?'
        patron += '<h3 class=Title>(.*?)<\/h3>.*?<span class=Year>(.*?)<\/span>'
    data = get_source(item.url)
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:

        url = scrapedurl
        if "|" in scrapedtitle:
            scrapedtitle= scrapedtitle.split("|")
            contentTitle = scrapedtitle[0].strip()
        else:
            contentTitle = scrapedtitle

        contentTitle = re.sub('\(.*?\)','', contentTitle)

        title = '%s [%s]'%(contentTitle, year)
        thumbnail = 'http:'+scrapedthumbnail
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentTitle=contentTitle,
                                   infoLabels={'year':year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'<a class=next.*?href=(.*?)>')
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
        patron = 'custom menu-item-15\d+><a href=(.*?\?s.*?)>(\d{4})<\/a><\/li>'
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
    data = scrapertools.decodeHtmlentities(data)

    patron = 'id=(Opt\d+)>.*?src=(.*?) frameborder.*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, scrapedurl in matches:
        scrapedurl = scrapedurl.replace('"','').replace('&#038;','&')
        data_video = get_source(scrapedurl)
        url = scrapertools.find_single_match(data_video, '<div class=Video>.*?src=(.*?) frameborder')
        opt_data = scrapertools.find_single_match(data,'%s><span>.*?</span>.*?<span>(.*?)</span>'%option).split('-')
        language = opt_data[0].strip()
        quality = opt_data[1].strip()
        if url != '' and 'youtube' not in url:
            itemlist.append(item.clone(title='%s', url=url, language=IDIOMAS[language], quality=quality, action='play'))
        elif 'youtube' in url:
            trailer = item.clone(title='Trailer', url=url, action='play', server='youtube')

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    try:
        itemlist.append(trailer)
    except:
        pass

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
