# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="videos", title="Útimos vídeos", url="http://es.xhamster.com/",
                         viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="lista", title="Categorías", url="http://es.xhamster.com/categories"))
    itemlist.append(Item(channel=item.channel, action="votados", title="Más votados"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar",
                         url="http://xhamster.com/search.php?q=%s&qcat=video"))
    return itemlist


# REALMENTE PASA LA DIRECCION DE BUSQUEDA

def search(item, texto):
    logger.info()
    tecleado = texto.replace(" ", "+")
    item.url = item.url % tecleado
    item.extra = "buscar"
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# SECCION ENCARGADA DE BUSCAR

def videos(item):
    logger.info()
    data = scrapertools.cache_page(item.url)
    itemlist = []

    data = scrapertools.get_match(data, '>Duración(.*?)</article>')


#                                             <div class="thumb-list thumb-list--sidebar thumb-list--recent">
#                             <div class="thumb-list__item video-thumb video-thumb--dated video-thumb--with-date">
#         <div class="video-thumb__date-added">
#             11 de septiembre de 2018<i class="video-thumb__arrow xh-icon arrow-right"></i><i class="video-thumb__arrow xh-icon arrow-right"></i>
#         </div>
#     <a class="video-thumb__image-container thumb-image-container" href="https://es.xhamster.com/videos/mature-busty-natural-mom-fucks-strong-boy-10102610" data-sprite="https://thumb-v0.xhcdn.com/a/L0HT9h6iU9_nKBEEutxW_A/010/102/610/240x135.s.jpg" data-previewvideo="https://thumb-v0.xhcdn.com/a/d_DRiRaMvU2_sSbYjbNg7w/010/102/610/240x135.t.mp4">
#         <i class="thumb-image-container__icon thumb-image-container__icon--hd"></i>
#
#         <img class="thumb-image-container__image" src="https://thumb-v-cl2.xhcdn.com/a/tzuERGDMVPrAlP8syolBYw/010/102/610/240x135.1.jpg" onerror="window.Thumb && window.Thumb.onerror(this)" alt="Mature busty natural mom fucks strong boy">
#
#     <div class="thumb-image-container__duration">06:15</div>
# </a>
#
# <div class="video-thumb-info">
#     <a class="video-thumb-info__name" href="https://es.xhamster.com/videos/mature-busty-natural-mom-fucks-strong-boy-10102610">Mature busty natural mom fucks strong boy</a>
#             <i class="video-thumb-info__views xh-icon beta-eye cobalt">24,811</i>
#
#             <i class="video-thumb-info__rating video-thumb-info__rating--like xh-icon beta-like">95%</i>
# </div>
# </div>

    # Patron #1
    patron = '<a class="video-thumb__image-container thumb-image-container" href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)">.*?<div class="thumb-image-container__duration">([^"]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle,scrapedtime in matches:
        logger.debug("title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        scrapedtitle = "[COLOR yellow](" + scrapedtime + ")[/COLOR] " + scrapedtitle
        itemlist.append(
            Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 folder=True))

    # Patron #2
    patron = '<a href="([^"]+)"  data-click="[^"]+" class="hRotator"><img src=\'([^\']+)\' class=\'thumb\' alt="([^"]+)"/>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        logger.debug("title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        itemlist.append(
            Item(channel=item.channel, action="play", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 folder=True))

    # Paginador
         # <li class="next">
         #        <a
         #           data-page="next" href="https://es.xhamster.com/2">
         #            Siguiente
         #            <i class="xh-icon arrow-right white"></i>
         #        </a>
         #    </li>

    patron = 'data-page="next" href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) > 0:
        itemlist.append(
            Item(channel=item.channel, action="videos", title="Página Siguiente", url=matches[0], thumbnail="",
                 folder=True, viewmode="movie"))

    return itemlist


# SECCION ENCARGADA DE VOLCAR EL LISTADO DE CATEGORIAS CON EL LINK CORRESPONDIENTE A CADA PAGINA

def categorias(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, action="lista", title="Heterosexual", url="http://es.xhamster.com/categories"))
    itemlist.append( Item(channel=item.channel, action="lista", title="Transexuales", url="http://es.xhamster.com/shemale/categories"))
    itemlist.append( Item(channel=item.channel, action="lista", title="Gays", url="http://es.xhamster.com/gay/categories"))
    return itemlist


def votados(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel, action="videos", title="Día",
                         url="http://es.xhamster.com/rankings/daily-top-videos.html", viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Semana",
                         url="http://es.xhamster.com/rankings/weekly-top-videos.html", viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="videos", title="Mes",
                         url="http://es.xhamster.com/rankings/monthly-top-videos.html", viewmode="movie"))
    itemlist.append(Item(channel=item.channel, action="videos", title="De siempre",
                         url="http://es.xhamster.com/rankings/alltime-top-videos.html", viewmode="movie"))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<div class="letter-blocks page">(.*?)<div class="letter">')

    patron = '<a href="(.*?)" >(.*?) '
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append( Item(channel=item.channel, action="videos", title=scrapedtitle, url=scrapedurl, folder=True,
                             viewmode="movie"))

#    sorted_itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return itemlist


# OBTIENE LOS ENLACES SEGUN LOS PATRONES DEL VIDEO Y LOS UNE CON EL SERVIDOR
def play(item):
    logger.info()
    itemlist = []

    data = scrapertools.cachePage(item.url)
    logger.debug(data)

    patron = '"([0-9]+p)":"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for res, url in matches:
        url = url.replace("\\", "")
        logger.debug("url=" + url)
        itemlist.append(["%s %s [directo]" % (res, scrapertools.get_filename_from_url(url)[-4:]), url])

    return itemlist
