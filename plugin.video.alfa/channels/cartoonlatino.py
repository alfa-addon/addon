# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay

host = "http://www.cartoon-latino.com/"
from channels import autoplay

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload',
                'vimple',
                'gvideo',
                'rapidvideo'
                ]
list_quality = ['default']

def mainlist(item):
    logger.info()
    thumb_series = get_thumb('tvshows', auto=True)
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=host,
                         thumbnail=thumb_series))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista_gen(item):
    logger.info()

    itemlist = []

    data1 = httptools.downloadpage(item.url).data
    data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data1)
    patron_sec = '<section class="content">.+?<\/section>'
    data = scrapertools.find_single_match(data1, patron_sec)
    patron = '<article id=.+? class=.+?><div.+?>'
    patron += '<a href="([^"]+)" title="([^"]+)'  # scrapedurl, # scrapedtitle
    patron += ' Capítulos Completos ([^"]+)">'  # scrapedlang
    patron += '<img.+? data-src=.+? data-lazy-src="([^"]+)"'  # scrapedthumbnail
    matches = scrapertools.find_multiple_matches(data, patron)
    i = 0
    for scrapedurl, scrapedtitle, scrapedlang, scrapedthumbnail in matches:
        i = i + 1
        if 'HD' in scrapedlang:
            scrapedlang = scrapedlang.replace('HD', '')
        title = scrapedtitle + " [ " + scrapedlang + "]"
        itemlist.append(
            Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail, action="episodios",
                 show=scrapedtitle))
    tmdb.set_infoLabels(itemlist)
    # Paginacion
    patron_pag = '<a class="nextpostslink" rel="next" href="([^"]+)">'
    next_page_url = scrapertools.find_single_match(data, patron_pag)

    if next_page_url != "" and i != 1:
        item.url = next_page_url
        itemlist.append(Item(channel=item.channel, action="lista_gen", title=">> Página siguiente", url=next_page_url,
                             thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data_lista = scrapertools.find_single_match(data, '<div class="su-list su-list-style-"><ul>(.+?)<\/ul><\/div>')
    patron = "<a href='(.+?)'>(.+?)<\/a>"
    matches = scrapertools.find_multiple_matches(data_lista, patron)
    for link, name in matches:
        title = name + " [Latino]"
        url = link
        context1=[autoplay.context]
        itemlist.append(
            item.clone(title=title, url=url, plot=title, action="episodios", show=title,
                       context=context1))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data_lista = scrapertools.find_single_match(data,
                                                '<div class="su-list su-list-style-"><ulclass="lista-capitulos">.+?<\/div><\/p>')
    if '&#215;' in data_lista:
        data_lista = data_lista.replace('&#215;', 'x')

    show = item.title
    if "[Latino]" in show:
        show = show.replace("[Latino]", "")
    if "Ranma" in show:
        patron_caps = '<\/i> <strong>.+?Capitulo ([^"]+)\: <a .+? href="([^"]+)">([^"]+)<\/a>'
    else:
        patron_caps = '<\/i> <strong>Capitulo ([^"]+)x.+?\: <a .+? href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data_lista, patron_caps)
    scrapedplot = scrapertools.find_single_match(data, '<strong>Sinopsis<\/strong><strong>([^"]+)<\/strong><\/pre>')
    number = 0
    ncap = 0
    A = 1
    tempo=1
    for temp, link, name in matches:
        if A != temp and "Ranma" not in show:
            number = 0
        number = number + 1
        if "Ranma" in show:
            number,tempo=renumerar_ranma(number,tempo,18+1,1)
            number,tempo=renumerar_ranma(number,tempo,22+1,2)
            number,tempo=renumerar_ranma(number,tempo,24+1,3)
            number,tempo=renumerar_ranma(number,tempo,24+1,4)
            number,tempo=renumerar_ranma(number,tempo,24+1,5)
            number,tempo=renumerar_ranma(number,tempo,24+1,6)
        capi=str(number).zfill(2)
        if "Ranma" in show:
            title = "{0}x{1} - ({2})".format(str(tempo), capi, name)
        else:
            title = "{0}x{1} - ({2})".format(str(temp), capi, name)
        url = link
        A = temp
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, show=show))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir " + show + " a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def renumerar_ranma(number,tempo,final,actual):
    if number==final and tempo==actual:
        tempo=tempo+1
        number=1
    return number, tempo

def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data_function = scrapertools.find_single_match(data, '<!\[CDATA\[function (.+?)\]\]')
    data_id = scrapertools.find_single_match(data,
                                             "<script>\(adsbygoogle = window\.adsbygoogle \|\| \[\]\)\.push\({}\);<\/script><\/div><br \/>(.+?)<\/ins>")
    if data_id == "":
        data_id = scrapertools.find_single_match(data, "<p><center><br />.*?</center>")
    itemla = scrapertools.find_multiple_matches(data_function, "src='(.+?)'")
    serverid = scrapertools.find_multiple_matches(data_id, '<script>([^"]+)\("([^"]+)"\)')
    for server, id in serverid:
        for link in itemla:
            if server in link:
                url = link.replace('" + ID' + server + ' + "', str(id))
        itemlist.append(item.clone(url=url, action="play",
                                   title="Enlace encontrado en %s "
                                   ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    scrapertools.printMatches(itemlist)
    autoplay.start(itemlist, item)
    return itemlist
