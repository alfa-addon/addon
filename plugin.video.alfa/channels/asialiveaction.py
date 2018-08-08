# -*- coding: UTF-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = "http://www.asialiveaction.com"


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="lista", title="Peliculas",
                             url=urlparse.urljoin(host, "p/peliculas.html"), type='pl', first=0))

    itemlist.append(Item(channel=item.channel, action="lista", title="Series",
                         url=urlparse.urljoin(host, "p/series.html"), type='sr', first=0))

    itemlist.append(Item(channel=item.channel, action="category", title="Géneros", url=host, cat='genre'))

    itemlist.append(Item(channel=item.channel, action="category", title="Calidad", url=host, cat='quality'))

    itemlist.append(Item(channel=item.channel, action="category", title="Orden Alfabético", url=host, cat='abc'))

    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno", url=host, cat='year'))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+"/search?q="))
    return itemlist


def category(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    if item.cat == 'abc':
        data = scrapertools.find_single_match(data, '<span>Orden Alfabético</span>.*?</ul>')
    elif item.cat == 'genre':
        data = scrapertools.find_single_match(data, '<span>Géneros</span>.*?</ul>')
    elif item.cat == 'year':
        data = scrapertools.find_single_match(data, '<span>Año</span>.*?</ul>')
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<span>Calidad</span>.*?</ul>')

    patron = "<li>([^<]+)<a href='([^']+)'>"

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedtitle, scrapedurl  in matches:
        if scrapedtitle != 'Próximas Películas':
            itemlist.append(item.clone(action='lista', title=scrapedtitle, url=host+scrapedurl, type='cat', first=0))

    return itemlist


def search_results(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<span class=.post-labels.>([^<]+)</span>.*?class="poster-bg" src="([^"]+)"/>.*?<h4>.*?'
    patron +=">(\d{4})</a>.*?<h6>([^<]+)<a href='([^']+)"

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedtype, scrapedthumbnail, scrapedyear, scrapedtitle ,scrapedurl in matches:

        title="%s [%s]" % (scrapedtitle,scrapedyear)
        new_item= Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail)
        if scrapedtype.strip() == 'Serie':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episodios'
            new_item.type = 'sr'
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
            new_item.type = 'pl'


        itemlist.append(new_item)

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return search_results(item)

def episodios(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron ='<div id="ep(\d+)" class="eps"> <section class="section-post online"><div class="player">.*?'
    patron += 'src="([^"]+)"/><a href="([^"]+)" target='

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedepi, scrapedthumbnail, scrapedurl in matches:
        url = scrapedurl
        title="1x%s - %s" % (scrapedepi, item.contentSerieName)
        itemlist.append(item.clone(action='findvideos', title=title, url=url, thumbnail=scrapedthumbnail, type=item.type,
                                   infoLabels=item.infoLabels))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                             url=item.url, action="add_serie_to_library", extra="episodios",
                             contentSerieName=item.contentSerieName))
    return itemlist

def lista(item):
    logger.info()
    next = True
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data, "itemprop='headline'>.*?</h2>.*?</ul>")

    patron = '<span class="([^"]+)">.*?<figure class="poster-bg"><header><span>(\d{4})</span></header><img src="([^"]+)" />'
    patron += '<footer>(.*?)</footer></figure><h6>([^<]+)</h6><a href="([^"]+)"></a>'

    matches = scrapertools.find_multiple_matches(data, patron)

    first = int(item.first)
    last = first + 19
    if last > len(matches):
        last = len(matches)
        next = False


    for scrapedtype, scrapedyear, scrapedthumbnail, scrapedquality, scrapedtitle ,scrapedurl in matches[first:last]:
        patron_quality="<span>(.+?)</span>"
        quality = scrapertools.find_multiple_matches(scrapedquality, patron_quality)
        qual=""

        for calidad in quality:
            qual=qual+"["+calidad+"] "

        title="%s [%s] %s" % (scrapedtitle,scrapedyear,qual)
        new_item= Item(channel=item.channel, title=title, url=host+scrapedurl, thumbnail=scrapedthumbnail,
                       type=scrapedtype, infoLabels={'year':scrapedyear})
        if scrapedtype.strip() == 'sr':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episodios'
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'

        if scrapedtype == item.type or item.type == 'cat':
            itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    #pagination

    url_next_page = item.url
    first = last

    if next:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista', first=first))

    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    dl_links = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    ### obtiene los gvideo
    patron = 'class="Button Sm fa fa-download mg"></a><a target="_blank" rel="nofollow" href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for dl_url in matches:
        g_data = httptools.downloadpage(dl_url).data
        video_id = scrapertools.find_single_match(g_data, 'jfk-button jfk-button-action" href="([^"]+)">')
        g_url = '%s%s' % ('https://drive.google.com', video_id)
        g_url = g_url.replace('&amp;', '&')
        g_data = httptools.downloadpage(g_url, follow_redirects=False, only_headers=True).headers
        url = g_data['location']
        dl_links.append(Item(channel=item.channel, title='%s', url=url, action='play', infoLabels=item.infoLabels))

    if item.type == 'pl':
        new_url = scrapertools.find_single_match(data, '<div class="player">.*?<a href="([^"]+)" target')

        data = httptools.downloadpage(new_url).data
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="btn.*?" data-video="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for video_id in matches:
        url_data = httptools.downloadpage('https://tinyurl.com/%s' % video_id, follow_redirects=False)
        url = url_data.headers['location']
        itemlist.append(Item(channel=item.channel, title = '%s', url=url, action='play', infoLabels=item.infoLabels))

    itemlist.extend(dl_links)

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    return itemlist