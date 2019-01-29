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


host = "https://serieslan.com"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series", contentSerieName="Series", url=host, thumbnail=thumb_series, page=0))
    itemlist.append(
        Item(channel=item.channel, action="lista", title="Live Action", contentSerieName="Live Action", url=host+"/liveaction", thumbnail=thumb_series, page=0))
    #itemlist.append(
    #    Item(channel=item.channel, action="peliculas", title="Películas", contentSerieName="Películas", url=host+"/peliculas", thumbnail=thumb_series, page=0))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar",
                         thumbnail=thumb_series))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def search(item, texto):
    logger.info()
    #texto = texto.replace(" ", "+")
    item.url = host +"/buscar.php"
    item.texto = texto
    if texto != '':
        return sub_search(item)
    else:
        return []

def sub_search(item):
    logger.info()
    itemlist = []
    post = "k=" + item.texto
    results = httptools.downloadpage(item.url, post=post).data
    results = eval(results)
    logger.info(results)
    for result in results:
        scrapedthumbnail = host + "/tb/" + result[0] + ".jpg"
        scrapedtitle = result[1].decode('unicode_escape')
        logger.info(scrapedtitle)
        scrapedurl = host + "/" + result[2]
        #scrapedyear = result[3]
        itemlist.append(item.clone(action = "episodios",
                                   title = scrapedtitle,
                                   thumbnail = scrapedthumbnail,
                                   url = scrapedurl,
                                   contentSerieName = scrapedtitle
                        ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
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
        url=host+"/pag-"+str(a)
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

    patron_caps = '<li><span>Capitulo (\d+).*?</span><a href="(.*?)">(.*?)</a></li>'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_info = '<img src="([^"]+)">.+?</span>(.*?)</p>.*?<h2>Reseña:</h2><p>(.*?)</p>'
    scrapedthumbnail, show, scrapedplot = scrapertools.find_single_match(data, patron_info)
    scrapedthumbnail = host + scrapedthumbnail

    for cap, link, name in matches:

        title = ""
        pat = "/"
        if "Mike, Lu & Og"==item.title:
            pat="&/"
        if "KND" in item.title:
            pat="-"
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
        if "disponible" in link:
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
    _sa = scrapertools.find_single_match(data, 'var _sa = (true|false);')
    _sl = scrapertools.find_single_match(data, 'var _sl = ([^;]+);')
    sl = eval(_sl)
    #buttons = scrapertools.find_multiple_matches(data, '<button href="" class="selop" sl="([^"]+)">')
    buttons = [0,1,2]
    for id in buttons:
        new_url = golink(int(id), _sa, sl)
        data_new = httptools.downloadpage(new_url).data
        _x0x = scrapertools.find_single_match(data_new, 'var x0x = ([^;]+);')
        try:
            x0x = eval(_x0x)
            url = base64.b64decode(gktools.transforma_gsv(x0x[4], base64.b64decode(x0x[1])))
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

def golink (num, sa, sl):
    import urllib
    b = [3, 10, 5, 22, 31]
    d = ''
    for i in range(len(b)):
        d += sl[2][b[i]+num:b[i]+num+1]

    SVR = "https://viteca.stream" if sa == 'true' else "http://serieslan.com"
    TT = "/" + urllib.quote_plus(sl[3].replace("/", "><")) if num == 0 else ""

    return SVR + "/el/" + sl[0] + "/" + sl[1] + "/" + str(num) + "/" + sl[2] + d + TT