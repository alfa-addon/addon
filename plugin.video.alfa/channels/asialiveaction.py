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
                             url=urlparse.urljoin(host, "/category/pelicula"), type='pl', pag=1))
    #itemlist.append(Item(channel=item.channel, action="lista", title="Series",
    #                     url=urlparse.urljoin(host, "/category/serie"), type='sr', pag=1))
    itemlist.append(Item(channel=item.channel, action="category", title="Géneros", url=host, cat='genre'))
    itemlist.append(Item(channel=item.channel, action="category", title="Calidad", url=host, cat='quality'))
    itemlist.append(Item(channel=item.channel, action="category", title="Orden Alfabético", url=host, cat='abc'))
    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno", url=host, cat='year'))
    #itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+"/search?q="))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def category(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.cat == 'abc':
        data = scrapertools.find_single_match(data, '<div class="Body Container">(.+?)<main>')
    elif item.cat == 'genre':
        data = scrapertools.find_single_match(data, '<a>Géneros<\/a><ul class="sub.menu">(.+?)<a>Año<\/a>')
    elif item.cat == 'year':
        data = scrapertools.find_single_match(data, '<a>Año<\/a><ul class="sub.menu">(.+?)<a>Idioma<\/a>')
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<a>Calidad<\/a><ul class="sub-menu">(.+?)<a>Géneros<\/a>')
    patron = '<li.*?><a href="(.*?)">(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        if scrapedtitle != 'Próximas Películas':
            itemlist.append(item.clone(action='lista', title=scrapedtitle, url=host+scrapedurl, type='cat', pag=0))
    return itemlist


def search_results(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger.info(data)
    patron = '<span class=.post-labels.>([^<]+)</span>.*?class="poster-bg" src="([^"]+)"/>.*?<h4>.*?'
    patron +=">(\d{4})</a>.*?<h6>([^<]+)<a href='([^']+)"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtype, scrapedthumbnail, scrapedyear, scrapedtitle ,scrapedurl in matches:
        title="%s [%s]" % (scrapedtitle, scrapedyear)
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

def lista(item):
    logger.info()
    next = True
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
        
    patron = '<article .*?">'
    patron += '<a href="([^"]+)"><.*?><figure.*?>' #scrapedurl
    patron += '<img.*?src="([^"]+)".*?>.*?' #scrapedthumbnail
    patron += '<h3 class=".*?">([^"]+)<\/h3>' #scrapedtitle
    patron += '<span.*?>([^"]+)<\/span>.+?' #scrapedyear
    patron += '<a.+?>([^"]+)<\/a>' #scrapedtype
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
        title="%s - %s" % (scrapedtitle,scrapedyear)

        new_item = Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                       type=scrapedtype, infoLabels={'year':scrapedyear})

        if scrapedtype == 'sr':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episodios'
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
            
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    #pagination
    pag = item.pag + 1
    url_next_page = item.url+"/page/"+str(pag)+"/"
    if len(itemlist)>19:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista', pag=pag))
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
        language = scrapertools.find_single_match(data, '(?:ɥɔɐәlq|lɐʇәɯllnɟ) (\w+)')
        if not language: language = "VOS"
        bloque = scrapertools.find_single_match(data, "description articleBody(.*)/div")
        urls = scrapertools.find_multiple_matches(bloque, "iframe src='([^']+)")
        if urls:
            # cuando es streaming
            for url1 in urls:
                if "luis" in url1:
                    data = httptools.downloadpage(url1).data
                    url1 = scrapertools.find_single_match(data, 'file: "([^"]+)')
                itemlist.append(item.clone(action = "play", title = "Ver en %s (" + language + ")", language = language, url = url1))
        else:
            # cuando es descarga
            bloque = bloque.replace('"',"'")
            urls = scrapertools.find_multiple_matches(bloque, "href='([^']+)")
            for url2 in urls:
                itemlist.append(item.clone(action = "play", title = "Ver en %s (" + language + ")", language = language, url = url2))
        if "data-video" in bloque:
            urls = scrapertools.find_multiple_matches(bloque, "data-video='([^']+)")
            for url2 in urls:
                itemlist.append(item.clone(action = "play", title = "Ver en %s (" + language + ")", language = language, url = "https://tinyurl.com/%s" %url2 ))
    for item1 in itemlist:
        if "tinyurl" in item1.url:
            item1.url = httptools.downloadpage(item1.url, follow_redirects=False, only_headers=True).headers.get("location", "")
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
