# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay
from lib import gktools

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload'
                ]
list_quality = ['default']


host = "https://abtoon.net"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series", contentSerieName="Series", url=host, thumbnail=thumb_series, page=0))
    #itemlist.append(
    #    Item(channel=item.channel, action="lista", title="Live Action", contentSerieName="Live Action", url=host+"/liveaction", thumbnail=thumb_series, page=0))
    #itemlist.append(
    #    Item(channel=item.channel, action="peliculas", title="Películas", contentSerieName="Películas", url=host+"/peliculas", thumbnail=thumb_series, page=0))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" '
    if item.contentSerieName == "Series":
        patron += 'class="link">.+?<img src="([^"]+)".*?'
    else:
        patron += 'class="link-la">.+?<img src="([^"]+)".*?'
    patron += 'title="([^"]+)">'
    if item.url==host or item.url==host+"/liveaction":
        a=1
    else:
        num=(item.url).split('-')
        a=int(num[1])
    matches = scrapertools.find_multiple_matches(data, patron)

    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for link, img, name in matches[min:max]:
        b=b+1
        if " y " in name:
            title=name.replace(" y "," & ")
        else:
            title = name
        url = host + link
        scrapedthumbnail = host + img
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        
        itemlist.append(item.clone(title=title, url=url, action="episodios", thumbnail=scrapedthumbnail, show=title,contentSerieName=title,
                                   context=context))
    if b<29:
        a=a+1
        url=host+"/p/pag-"+str(a)
        if b>10:
            itemlist.append(
                Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=url, action="lista", page=0))
    else:    
        itemlist.append(
             Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="lista", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def peliculas(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="pel play" dt="(.+?)" .+?><img src="(.+?)" .+? title="(.*?)"><span class=".+?">(.+?)<\/span><a href="(.+?)" class.+?>'
    matches = scrapertools.find_multiple_matches(data, patron)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for scrapedplot,scrapedthumbnail, scrapedtitle, scrapedyear, scrapedurl in matches[min:max]:
        b=b+1
        url = host + scrapedurl
        thumbnail = host +scrapedthumbnail
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        itemlist.append(item.clone(title=scrapedtitle+"-"+scrapedyear, url=url, action="findvideos", thumbnail=thumbnail, plot=scrapedplot,
                show=scrapedtitle,contentSerieName=scrapedtitle,context=context))
    if b<29:
        pass
    else:    
        itemlist.append(
             Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="peliculas", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    # obtener el numero total de episodios
    total_episode = 0

    patron_caps = '<li><a href="(.*?)">(.*?) - (.*?)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_info = '<img src="([^"]+)" .+?>.+?<h1>([^"]+)<\/h1><p .+?>(.+?)<\/p>'
    scrapedthumbnail, show, scrapedplot = scrapertools.find_single_match(data, patron_info)
    scrapedthumbnail = host + scrapedthumbnail

    for link, cap, name in matches:

        title = ""
        pat = "$%&"
        # varios episodios en un enlace
        if len(name.split(pat)) > 1:
            i = 0
            for pos in name.split(pat):
                i = i + 1
                total_episode += 1
                season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, total_episode)
                if len(name.split(pat)) == i:
                    title += "%sx%s " % (season, str(episode).zfill(2))
                else:
                    title += "%sx%s_" % (season, str(episode).zfill(2))
        else:
            total_episode += 1
            season, episode = renumbertools.numbered_for_tratk(item.channel,item.contentSerieName, 1, total_episode)

            title += "%sx%s " % (season, str(episode).zfill(2))

        url = host + "/" + link
        if "DISPONIBLE" in name:
            title += "No Disponible aún"
        else:
            title += name
            itemlist.append(
                Item(channel=item.channel, action="findvideos", title=title, url=url, show=show, plot=scrapedplot,
                     thumbnail=scrapedthumbnail))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def findvideos(item):
    import base64
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    _sl = scrapertools.find_single_match(data, 'var abi = ([^;]+);')
    sl = eval(_sl)
    buttons = scrapertools.find_multiple_matches(data,'class="bsel" sl="(.+?)"')#[0,1,2,3,4]
    for ids in buttons:
        id = int(ids)
        url_end = golink(id,sl)
        new_url = "https://abtoon.net/" + "embed/" + sl[0] + "/" + sl[1] + "/" + str(id) + "/" + sl[2] + url_end
        data_new = httptools.downloadpage(new_url).data
        data_new = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_new)
        logger.info("asdasdasdcc"+data_new)
        valor1, valor2 = scrapertools.find_single_match(data_new, 'var x0x = \["[^"]*", "([^"]+)", "[^"]*", "[^"]*", "([^"]+)"\];') 
        try:
            url = base64.b64decode(gktools.transforma_gsv(valor2, base64.b64decode(valor1)))
            if 'download' in url:
                url = url.replace('download', 'preview')
            title = '%s'
            itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language='latino',
                         infoLabels=item.infoLabels))
        except Exception as e:
            logger.info(e)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist

def golink(ida,sl):
    a=ida
    b=[3,10,5,22,31]
    c=1
    d=""
    e=sl[2]
    for i in range(len(b)):
      d=d+substr(e,b[i]+a,c)
    return d

def substr(st,a,b):
    return st[a:a+b]