# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from platformcode import config, logger

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload',
                'okru',
                'myvideo',
                'sendvid'
                ]
list_quality = ['default']

host = 'http://www.seodiv.com'
language = 'latino'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(
        Item(channel=item.channel,
             title="Todos",
             action="todas",
             url=host,
             thumbnail='https://s27.postimg.cc/iahczwgrn/series.png',
             fanart='https://s27.postimg.cc/iahczwgrn/series.png',
             page=0
             ))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def todas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = '<div class=shortf><div><div class=shortf-img><a href=(.*?)><img src=(.*?) alt=.*?quality>(.*?)<.*?Ver ' \
             'Serie><span>(.*?)<\/span>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=int(min)-int(item.page)
    max = min + num_items_x_pagina - 1
    
    for scrapedurl, scrapedthumbnail, scrapedcalidad, scrapedtitle in matches[min:max]:
        url = host + scrapedurl
        calidad = scrapedcalidad
        title = scrapedtitle.decode('utf-8')
        thumbnail = scrapedthumbnail
        fanart = 'https://s32.postimg.cc/gh8lhbkb9/seodiv.png'
        if not 'xxxxxx' in scrapedtitle:
            itemlist.append(
                Item(channel=item.channel,
                 action="temporadas",
                 title=title, url=url,
                 thumbnail=thumbnail,
                 fanart=fanart,
                 contentSerieName=title,
                 extra='',
                 language=language,
                 context=autoplay.context
                 ))
    tmdb.set_infoLabels(itemlist)
    if len(itemlist)>28:
        itemlist.append(
             Item(channel=item.channel, 
                title="[COLOR cyan]Página Siguiente >>[/COLOR]", 
                url=item.url, action="todas", 
                page=item.page + 1))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    url_base = item.url
    patron = '<li class=item\d+><a href=#>(.*?) <\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    temp = 1
    if matches:
        for scrapedtitle in matches:
            url = url_base
            tempo = re.findall(r'\d+', scrapedtitle)
            # if tempo:
            #    title = 'Temporada' + ' ' + tempo[0]
            # else:
            title = scrapedtitle
            thumbnail = item.thumbnail
            plot = item.plot
            fanart = scrapertools.find_single_match(data, '<img src="([^"]+)"/>.*?</a>')
            itemlist.append(
                Item(channel=item.channel,
                     action="episodiosxtemp",
                     title=title,
                     fulltitle=item.title,
                     url=url,
                     thumbnail=thumbnail,
                     plot=plot, fanart=fanart,
                     temp=str(temp),
                     contentSerieName=item.contentSerieName,
                     context=item.context
                     ))
            temp = temp + 1

        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                Item(channel=item.channel,
                     title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                     url=item.url,
                     action="add_serie_to_library",
                     extra="episodios",
                     contentSerieName=item.contentSerieName,
                     extra1=item.extra1,
                     temp=str(temp)
                     ))
        return itemlist
    else:
        itemlist = episodiosxtemp(item)
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                Item(channel=item.channel,
                     title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                     url=item.url,
                     action="add_serie_to_library",
                     extra="episodios",
                     contentSerieName=item.contentSerieName,
                     extra1=item.extra1,
                     temp=str(temp)
                     ))
        return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    for tempitem in templist:
        itemlist += episodiosxtemp(tempitem)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url, add_referer=True).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def episodiosxtemp(item):
    logger.info()

    logger.info()
    itemlist = []
    item.title = 'Temporada %s' % item.temp.zfill(2)
    patron_temp = '<li class=item\d+><a href=#>%s <\/a><ul><!--initiate accordion-->.*?<!--initiate ' \
                  'accordion-->' % item.title
    all_data = get_source(item.url)
    data = scrapertools.find_single_match(all_data, patron_temp)
    tempo = item.title
    if 'Temporada' in item.title:
        item.title = 'temporada-%s'%item.temp.zfill(2)
    patron = '<li><a href=(.*?)>.*?(Capitulo|Pelicula).*?(\d+).*?<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtipo, scrapedtitle in matches:
        url = host + scrapedurl
        plot = item.plot
        if scrapedtipo == 'Capitulo' and item.temp != '':
            title = item.contentSerieName + ' ' + item.temp + 'x' + scrapedtitle
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=title,
                     fulltitle=item.fulltitle,
                     url=url,
                     thumbnail=item.thumbnail,
                     plot=plot,
                     language=language,
                     contentSerieName=item.contentSerieName,
                     context=item.context
                     ))

        if item.title not in scrapedurl and scrapedtipo == 'Capitulo' and item.temp \
                == '':
            if item.temp == '': temp = '1'
            title = item.contentSerieName + ' ' + temp + 'x' + scrapedtitle
            if '#' not in scrapedurl:
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         title=title,
                         fulltitle=item.fulltitle,
                         url=url,
                         thumbnail=item.thumbnail,
                         plot=plot,
                         contentSerieName=item.contentSerieName,
                         context=item.context
                         ))

        if 'temporada' not in item.title and item.title not in scrapedurl and scrapedtipo == 'Pelicula':
            title = scrapedtipo + ' ' + scrapedtitle
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=title,
                     fulltitle=item.fulltitle,
                     url=url,
                     thumbnail=item.thumbnail,
                     plot=plot,
                     language=language,
                     contentSerieName=item.contentSerieName,
                     context=item.context
                     ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    lang=[]
    data = httptools.downloadpage(item.url).data
    video_items = servertools.find_video_items(item)
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    language_items=scrapertools.find_single_match(data,
                 '<ul class=tabs-sidebar-ul>(.+?)<\/ul>')
    matches=scrapertools.find_multiple_matches(language_items,
                 '<li><a href=#ts(.+?)><span>(.+?)<\/span><\/a><\/li>')
    for idl,scrapedlang in matches:
        if int(idl)<5 and int(idl)!=1:
            lang.append(scrapedlang)
    i=0
    if len(lang)!=0:
        lang.reverse()
    for videoitem in video_items:
        videoitem.thumbnail = servertools.guess_server_thumbnail(videoitem.server)
        if i<len(lang) and len(lang)!=0:
            videoitem.language=lang[i]
        else:
            videoitem.language = scrapertools.find_single_match(data, '<span class=f-info-title>Idioma:<\/span>\s*<span '
                                                                'class=f-info-text>(.*?)<\/span>')
        videoitem.title = item.contentSerieName + ' (' + videoitem.server + ') (' + videoitem.language + ')'
        videoitem.quality = 'default'
        videoitem.context = item.context
        i=i+1
        itemlist.append(videoitem)

    # Requerido para FilterTools

    if len(itemlist) > 0 and filtertools.context:
        itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
