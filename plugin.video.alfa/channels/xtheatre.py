# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para PelisPlanet
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re
import sys
import urllib
import urlparse

from core import config
from core import httptools
from core import logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb

__channel__ = "xtheatre"

host = 'https://xtheatre.net/'
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFF6E2802', '0xFFFAA171', '0xFFE9D7940'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__-1]
else:
    color1 = color2 = color3 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'

def mainlist(item):
    logger.info()

    itemlist = []
    # thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'

    itemlist.append(Item(channel=__channel__, title="Últimas", url=host + '?filtre=date&cat=0',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail = thumbnail % '1'))

    itemlist.append(Item(channel=__channel__, title="Más Vistas", url=host + '?display=extract&filtre=views',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail = thumbnail % '2'))

    itemlist.append(Item(channel=__channel__, title="Mejor Valoradas", url=host + '?display=extract&filtre=rate',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail = thumbnail % '3'))

    itemlist.append(Item(channel=__channel__, title="Categorías", action="categorias",
                         url=host + 'categories/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail = thumbnail % '4'))

    itemlist.append(Item(channel=__channel__, title="Buscador", action="search", url=host, thumbnail = thumbnail % '5'))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|#038;", "", data)
    # logger.info(data)
    patron_todos = '<div id="content">(.*?)<div id="footer"'
    data = scrapertools.find_single_match(data, patron_todos)
    # logger.info(data)

    patron = 'data-lazy-src="([^"]+)".*?'  # img
    patron += 'title="([^"]+)"/>.*?'  # title
    patron += '</noscript><a href="([^"]+)"'  # url
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        title = "%s" % (scrapedtitle)

        itemlist.append(item.clone(channel=item.channel, action="findvideos", title=title,
                                   url=scrapedurl, thumbnail=scrapedthumbnail, plot='',
                                   viewmode="movie_with_plot", folder=True))
    # Extrae el paginador
    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)">Next &rsaquo;</a></li><li>')
    # paginacion = paginacion.replace('#038;', '')
    paginacion = urlparse.urljoin(item.url, paginacion)

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="peliculas",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
            patron = '<div id="video-synopsys" itemprop="description">(.*?)<div id="video-bottom">'
            data = scrapertools.find_single_match(data, patron)
            item.infoLabels['plot'] = scrapertools.find_single_match(data, '<p>(.*?)</p></div>')
            item.infoLabels['plot'] = scrapertools.htmlclean(item.plot)

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    logger.info(data)
    patron = 'data-lazy-src="([^"]+)".*?'  # img
    patron += '</noscript><a href="([^"]+)".*?'  # url
    patron += '<span>([^<]+)</span></a>.*?'  # title
    patron += '<span class="nb_cat border-radius-5">([^<]+)</span>'  # num_vids
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, vids in matches:
        title = "%s (%s)" % (scrapedtitle, vids.title())
        thumbnail = scrapedthumbnail
        url = scrapedurl
        itemlist.append(Item(channel=item.channel, action="peliculas", fanart=scrapedthumbnail,
                             title=title, url=url, thumbnail=thumbnail, plot='',
                             viewmode="movie_with_plot", folder=True))

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return sub_search(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron_todos = '<div id="content">(.*?)</li></ul></div></div>'
    data = scrapertools.find_single_match(data, patron_todos)

    patron = 'data-lazy-src="([^"]+)".*?'  # img
    patron += 'title="([^"]+)"/>.*?'  # title
    patron += '</noscript><a href="([^"]+)"'  # url
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        title = "%s" % (scrapedtitle)
        itemlist.append(item.clone(title=title, url=scrapedurl,
                                   action="findvideos", thumbnail=scrapedthumbnail))

    paginacion = scrapertools.find_single_match(
        data, "<a href='([^']+)' class=\"inactive\">\d+</a>")

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def findvideos(item):

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    logger.info(data)
    patron_todos = '<div class="video-embed">(.*?)</div>'
    data = scrapertools.find_single_match(data, patron_todos)
    patron = '<iframe src="[^"]+" data-lazy-src="([^"]+)".*?</iframe>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url in matches:
        title = item.title
        server = servertools.get_server_from_url(url)

        itemlist.append(item.clone(action='play', title=title, server=server, mediatype='movie', url=url))

    for videoitem in itemlist:
        videoitem.infoLabels = item.infoLabels
        videoitem.channel = item.channel
        videoitem.title = "%s [COLOR yellow](%s)[/COLOR]" % (item.title, videoitem.server)

    # if config.get_library_support() and len(itemlist) > 0:
    #     itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]',
    #                          url=item.url, action="add_pelicula_to_library",
    #                          thumbnail='https://s19.postimg.org/l5z8iy1zn/biblioteca.png',
    #                          extra="findvideos", contentTitle=item.contentTitle))

    return itemlist
