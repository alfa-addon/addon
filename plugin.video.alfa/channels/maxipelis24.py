# -*- coding: utf-8 -*-

import re
import urlparse
import urllib

from core import servertools
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host="http://maxipelis24.com"


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="peliculas", action="movies", url=host, thumbnail=get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno", url=host, cat='year', thumbnail=get_thumb('year', auto=True)))
    itemlist.append(Item(channel=item.channel, action="category", title="Géneros", url=host, cat='genre', thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, action="category", title="Calidad", url=host, cat='quality', thumbnail=get_thumb("quality", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+"?s=", thumbnail=get_thumb("search", auto=True)))
    
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
        data = scrapertools.find_single_match(data, '<h3>Géneros.*?</div>')
        patron = '<a href="([^"]+)">([^<]+)<'
    elif item.cat == 'year':
        data = scrapertools.find_single_match(data, '<h3>Año de estreno.*?</div>')
        patron = 'li><a href="([^"]+)">([^<]+).*?<'
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<h3>Calidad.*?</div>')
        patron = 'li><a href="([^"]+)">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for  scrapedurl , scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel, action='movies', title=scrapedtitle, url=scrapedurl, type='cat', first=0))
    return itemlist

def movies(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)

    patron = '<div id="mt.+?href="([^"]+)".+?'
    patron += '<img src="([^"]+)" alt="([^"]+)".+?'
    patron += '<span class="imdb">.*?>([^<]+)<.*?'
    patron += '<span class="ttx">([^<]+).*?'
    patron += 'class="year">([^<]+).+?class="calidad2">([^<]+)<'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, img, scrapedtitle, ranking, resto,  year, quality in matches:
        plot = scrapertools.htmlclean(resto).strip()
        title = '%s [COLOR yellow](%s)[/COLOR] [COLOR red][%s][/COLOR]'% (scrapedtitle, ranking, quality)
        itemlist.append(Item(channel=item.channel,
                             title=title, 
                             url=scrapedurl, 
                             action="findvideos",
                             plot=plot,
                             thumbnail=img,
                             contentTitle = scrapedtitle,
                             contentType = "movie",
                             quality=quality))

    #Paginacion
    next_page = '<div class="pag_.*?href="([^"]+)">Siguiente<'
    matches = re.compile(next_page, re.DOTALL).findall(data)
    if matches:
        url = urlparse.urljoin(item.url, matches[0])
        itemlist.append(Item(channel=item.channel, action = "movies", title = "Página siguiente >>",url = url))
    
    return itemlist

def findvideos(item):
    logger.info()
    itemlist=[]

    data = httptools.downloadpage(item.url).data

    data = scrapertools.get_match(data, '<div id="contenedor">(.*?)</div></div></div>')

    # Busca los enlaces a los videos
    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = scrapertools.unescape(video[0])
        url = video[1]
        server = video[2]

        itemlist.append(Item(channel=item.channel, action="play", server=server, title=videotitle, url=url,
                             thumbnail=item.thumbnail, plot=item.plot, fulltitle=item.title, folder=False))

    # Opción "Añadir esta película a la biblioteca de KODI"
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 thumbnail=item.thumbnail
                 ))

    return itemlist
