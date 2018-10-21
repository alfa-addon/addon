# -*- coding: UTF-8 -*-

import re
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = "http://www.asialiveaction.com"

IDIOMAS = {'Japones': 'Japones'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gvideo', 'openload','streamango']

def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
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
    autoplay.show_option(item.channel, itemlist)
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
    patron = "<li.*?>([^<]+)<a href='([^']+)'>"
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
    data = data.replace('"ep0','"epp"')
    patron  = '(?is)<div id="ep(\d+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'href="([^"]+)" target="_blank"'
    matches = scrapertools.find_multiple_matches(data, patron)
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

    css_data = scrapertools.find_single_match(data, "<style id='page-skin-1' type='text/css'>(.*?)</style>")

    data = scrapertools.find_single_match(data, "itemprop='headline'>.*?</h2>.*?</ul>")

    patron = '<span class="([^"]+)">.*?<figure class="poster-bg">(.*?)<img src="([^"]+)" />'
    patron += '(.*?)</figure><h6>([^<]+)</h6><a href="([^"]+)"></a>'
    matches = scrapertools.find_multiple_matches(data, patron)

    first = int(item.first)
    last = first + 19
    if last > len(matches):
        last = len(matches)
        next = False

    for scrapedtype, scrapedyear, scrapedthumbnail, scrapedquality, scrapedtitle, scrapedurl in matches[first:last]:
        year = scrapertools.find_single_match(scrapedyear, '<span>(\d{4})</span>')

        if not year:
            class_year = scrapertools.find_single_match(scrapedyear, 'class="([^\"]+)"')
            year = scrapertools.find_single_match(css_data, "\." + class_year + ":after {content:'(\d{4})';}")
            if not year:
                year = scrapertools.find_single_match(data, "headline'>(\d{4})</h2>")

        qual = ""
        if scrapedquality:
            patron_qualities='<i class="([^"]+)"></i>'
            qualities = scrapertools.find_multiple_matches(scrapedquality, patron_qualities)

            for quality in qualities:
                patron_desc = "\." + quality + ":after {content:'([^\']+)';}"
                quality_desc = scrapertools.find_single_match(css_data, patron_desc)

                qual = qual+ "[" + quality_desc + "] "

        title="%s [%s] %s" % (scrapedtitle,year,qual)

        new_item = Item(channel=item.channel, title=title, url=host+scrapedurl, thumbnail=scrapedthumbnail,
                       type=scrapedtype, infoLabels={'year':year})

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
    matches = scrapertools.find_multiple_matches(data, patron)
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
    matches = scrapertools.find_multiple_matches(data, patron)
    for video_id in matches:
        url_data = httptools.downloadpage('https://tinyurl.com/%s' % video_id, follow_redirects=False)
        url = url_data.headers['location']
        itemlist.append(Item(channel=item.channel, title = '%s', url=url, action='play', infoLabels=item.infoLabels))
    patron = '<iframe src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        itemlist.append(item.clone(title = '%s', url=url, action='play'))
    itemlist.extend(dl_links)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
