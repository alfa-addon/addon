# -*- coding: utf-8 -*-
# -*- Channel Cuevana 3 -*-
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


host = 'http://www.cuevana3.com/'

IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'Subtitulado':'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['fastplay', 'rapidvideo', 'streamplay', 'flashx', 'streamito', 'streamango', 'vidoza']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host,
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", section='genre',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all", url= host+'espanol',
                         thumbnail=get_thumb('audio', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all", url=host + 'latino',
                         thumbnail=get_thumb('audio', auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all", url=host + 'subtitulado',
                         thumbnail=get_thumb('audio', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", section='alpha',
                         thumbnail=get_thumb('alphabet', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+'?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []

    try:
        data = get_source(item.url)
        if item.section == 'alpha':
          patron = '<span class="Num">\d+.*?<a href="([^"]+)" class.*?'
          patron += 'src="([^"]+)" class.*?<strong>([^<]+)</strong>.*?<td>(\d{4})</td>'
        else:
            patron = '<article id="post-\d+".*?<a href="([^"]+)">.*?'
            patron += 'src="([^"]+)".*?<h2 class="Title">([^<]+)<\/h2>.*?<span class="Year">([^<]+)<\/span>'
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
            itemlist.append(Item(channel=item.channel, action='findvideos',
                                       title=title,
                                       url=url,
                                       thumbnail=thumbnail,
                                       contentTitle=contentTitle,
                                       infoLabels={'year':year}
                                       ))
        tmdb.set_infoLabels_itemlist(itemlist, True)

        #  Paginación

        url_next_page = scrapertools.find_single_match(data,'<a class="next.*?" rel="next" href="([^"]+)"')
        if url_next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                                 section=item.section))
    except:
        pass
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    data = get_source(host)
    action = 'list_all'

    if item.section == 'genre':
        data = scrapertools.find_single_match(data, '>Géneros</a>.*?</ul>')
    elif item.section == 'alpha':
        data = scrapertools.find_single_match(data, '<ul class="AZList"><li>.*?</ul>')
    patron = '<a href="([^"]+)">([^<]+)</a>'
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
    patron = 'TPlayerNv="Opt(\w\d+)".*?img src="(.*?)<span>\d+ - (.*?) - ([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, url_data, language, quality in matches:
        if 'domain' in url_data:
            url = scrapertools.find_single_match(url_data, 'domain=([^"]+)"')
        else:
            url = scrapertools.find_single_match(data, 'id="Opt%s">.*?file=([^"]+)"' % option)

        if url != '' and 'youtube' not in url:
                itemlist.append(Item(channel=item.channel, title='%s', url=url, language=IDIOMAS[language],
                                     quality=quality, action='play'))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    tmdb.set_infoLabels_itemlist(itemlist, True)
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
        if categoria == 'infantiles':
            item.url = host+'/category/animacion'
        elif categoria == 'terror':
            item.url = host+'/category/terror'
        elif categoria == 'documentales':
            item.url = host+'/category/documental'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
