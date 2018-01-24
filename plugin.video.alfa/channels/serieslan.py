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
from channels import autoplay

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
        Item(channel=item.channel, action="lista", title="Series", url=host, thumbnail=thumb_series, page=0))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" '
    patron += 'class="link">.+?<img src="([^"]+)".*?'
    patron += 'title="([^"]+)">'
    if item.url==host:
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
        
        itemlist.append(item.clone(title=title, url=url, action="episodios", thumbnail=scrapedthumbnail, show=title,
                                   context=context))
    if b<29:
        a=a+1
        url="https://serieslan.com/pag-"+str(a)
        if b>10:
            itemlist.append(
                Item(channel=item.channel, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=url, action="lista", page=0))
    else:    
        itemlist.append(
             Item(channel=item.channel, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="lista", page=item.page + 1))

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
    # data_info = scrapertools.find_single_match(data, '<div class="info">.+?<\/div><\/div>')
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
                season, episode = renumbertools.numbered_for_tratk(item.channel, item.show, 1, total_episode)
                if len(name.split(pat)) == i:
                    title += "%sx%s " % (season, str(episode).zfill(2))
                else:
                    title += "%sx%s_" % (season, str(episode).zfill(2))
        else:
            total_episode += 1
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.show, 1, total_episode)

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
    logger.info()

    import base64

    itemlist = []

    url_server = "https://openload.co/embed/%s/"
    url_api_get_key = "https://serieslan.com/idx.php?i=%s&k=%s"

    def txc(key, _str):
        s = range(256)
        j = 0
        res = ''
        for i in range(256):
            j = (j + s[i] + ord(key[i % len(key)])) % 256
            x = s[i]
            s[i] = s[j]
            s[j] = x
        i = 0
        j = 0
        for y in range(len(_str)):
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            x = s[i]
            s[i] = s[j]
            s[j] = x
            res += chr(ord(_str[y]) ^ s[(s[i] + s[j]) % 256])
        return res

    data = httptools.downloadpage(item.url).data
    pattern = "<script type=.+?>.+?\['(.+?)','(.+?)','.+?'\]"
    idv, ide = scrapertools.find_single_match(data, pattern)
    thumbnail = scrapertools.find_single_match(data,
                                               '<div id="tab-1" class="tab-content current">.+?<img src="([^"]*)">')
    show = scrapertools.find_single_match(data, '<span>Episodio: <\/span>([^"]*)<\/p><p><span>Idioma')
    thumbnail = host + thumbnail
    data = httptools.downloadpage(url_api_get_key % (idv, ide), headers={'Referer': item.url}).data
    data = eval(data)

    if type(data) == list:
        video_url = url_server % (txc(ide, base64.decodestring(data[2])))
        server = "openload"
        if " SUB" in item.title:
            lang = "VOS"
        elif " Sub" in item:
            lang = "VOS"
        else:
            lang = "Latino"
        title = "Enlace encontrado en " + server + " [" + lang + "]"
        if item.contentChannel=='videolibrary':
            itemlist.append(item.clone(channel=item.channel, action="play", url=video_url,
                             thumbnail=thumbnail, server=server, folder=False))
        else:
            itemlist.append(Item(channel=item.channel, action="play", title=title, show=show, url=video_url, plot=item.plot,
                             thumbnail=thumbnail, server=server, folder=False))

        autoplay.start(itemlist, item)
        return itemlist
    else:
        return []

