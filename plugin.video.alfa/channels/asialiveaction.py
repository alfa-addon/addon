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
    patron += '(href.*?)fa fa-download'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedepi, scrapedthumbnail, scrapedurls in matches:
        title="1x%s - %s" % (scrapedepi, item.contentSerieName)
        urls = scrapertools.find_multiple_matches(scrapedurls, 'href="([^"]+)')
        itemlist.append(item.clone(action='findvideos', title=title, url=item.url, thumbnail=scrapedthumbnail, type=item.type,
                                   urls = urls, infoLabels=item.infoLabels))
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
    if not item.urls:
        data = httptools.downloadpage(item.url).data
        matches = scrapertools.find_multiple_matches(data, 'http://www.sutorimu[^"]+')
    else:
        matches = item.urls
    for url in matches:
        if "spotify" in url:
            continue
        data = httptools.downloadpage(url).data
        bloque = scrapertools.find_single_match(data, "description articleBody(.*)/div")
        urls = scrapertools.find_multiple_matches(bloque, "iframe src='([^']+)")
        if urls:
            # cuando es streaming
            for url1 in urls:
                if "luis" in url1:
                    data = httptools.downloadpage(url1).data
                    url1 = scrapertools.find_single_match(data, 'file: "([^"]+)')
                itemlist.append(item.clone(action = "play", title = "Ver en %s", url = url1))
        else:
            # cuando es descarga
            bloque = bloque.replace('"',"'")
            urls = scrapertools.find_multiple_matches(bloque, "href='([^']+)")
            for url2 in urls:
                itemlist.append(item.clone(action = "play", title = "Ver en %s", url = url2))
        if "data-video" in bloque:
            urls = scrapertools.find_multiple_matches(bloque, 'data-video="([^"]+)')
            for url2 in urls:
                itemlist.append(item.clone(action = "play", title = "Ver en %s", url = "https://tinyurl.com/%s" %url2 ))
    for item1 in itemlist:
        if "tinyurl" in item1.url:
            item1.url = httptools.downloadpage(item1.url, follow_redirects=False, only_headers=True).headers.get("location", "")
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
