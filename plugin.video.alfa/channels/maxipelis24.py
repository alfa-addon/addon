# -*- coding: utf-8 -*-

import re
import urlparse
import urllib

from core import tmdb
from core import servertools
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = "https://maxipelis24.tv"


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel = item.channel, title = "peliculas", action = "movies", url = host, thumbnail = get_thumb('movies', auto = True)))
    itemlist.append(Item(channel = item.channel, action = "category", title = "Año de Estreno", url = host, cat = 'year', thumbnail = get_thumb('year', auto = True)))
    itemlist.append(Item(channel = item.channel, action = "category", title = "Géneros", url = host, cat = 'genre', thumbnail = get_thumb('genres', auto = True)))
    itemlist.append(Item(channel = item.channel, action = "category", title = "Calidad", url = host, cat = 'quality', thumbnail = get_thumb("quality", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "?s=", thumbnail = get_thumb("search", auto = True)))
    
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    if texto != '':
        return movies(item)

def category(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)

    if item.cat == 'genre':
        data = scrapertools.find_single_match(data, '<h3>Géneros <span class="icon-sort">.*?</ul>')
        patron = '<li class="cat-item cat-item.*?<a href="([^"]+)" >([^<]+)<'
    elif item.cat == 'year':
        data = scrapertools.find_single_match(data, '<h3>Año de estreno.*?</div>')
        patron = 'li><a href="([^"]+)">([^<]+).*?<'
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<h3>Calidad.*?</div>')
        patron = 'li><a href="([^"]+)">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel = item.channel, action = 'movies', title =scrapedtitle, url = scrapedurl, type = 'cat', first = 0))
    return itemlist

def movies(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)

    patron = '<div id="mt.+?href="([^"]+)".+?'
    patron += '<img src="([^"]+)" alt="([^"]+)".+?'
    patron += '<span class="ttx">([^<]+).*?'
    patron += 'class="year">([^<]+).+?class="calidad2">([^<]+)<'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, img, scrapedtitle, resto,  year, quality in matches:
        scrapedtitle = re.sub(r'\d{4}|[()]','', scrapedtitle)
        plot = scrapertools.htmlclean(resto).strip()
        title = ' %s [COLOR red][%s][/COLOR]' % (scrapedtitle, quality)
        itemlist.append(Item(channel = item.channel,
                             title = title, 
                             url = scrapedurl, 
                             action = "findvideos",
                             plot = plot,
                             thumbnail = img,
                             contentTitle = scrapedtitle,
                             contentType = "movie",
                             quality = quality,
                             infoLabels = {'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    #Paginacion
    matches = re.compile('class="respo_pag"><div class="pag.*?<a href="([^"]+)" >Siguiente</a><', re.DOTALL).findall(data)
    if matches:
        url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(Item(channel = item.channel, action = "movies", title = "Página siguiente >>", url = url))
    
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data) 
    patron = scrapertools.find_single_match(data, '<div id="player2">(.*?)</div>')
    patron = '<div id="div.*?<div class="movieplay">.+?[a-zA-Z]="([^&]+)&'
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    for  link in matches:
        if 'id=' in link:
            id_type = 'id'
            ir_type = 'ir'
        elif 'ud=' in link:
            id_type = 'ud'
            ir_type = 'ur'
        elif 'od=' in link:
            id_type = 'od'
            ir_type = 'or'
        elif 'ad=' in link:
            id_type = 'ad'
            ir_type = 'ar'
        elif 'ed=' in link:
            id_type = 'ed'
            ir_type = 'er'
        
        id = scrapertools.find_single_match(link, '%s=(.*)' % id_type)
        base_link = scrapertools.find_single_match(link, '(.*?)%s=' % id_type)

        ir = id[::-1]
        referer = base_link+'%s=%s&/' % (id_type, ir)
        video_data = httptools.downloadpage('%s%s=%s' % (base_link, ir_type, ir), headers={'Referer':referer},
                                            follow_redirects=False)
        url = video_data.headers['location']
        title = '%s'

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='play',
                             language='', infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())



    return itemlist