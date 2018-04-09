# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()

CALIDADES = {'1080p': '1080p', '720p': '720p', '480p': '480p', '360p': '360p'}
list_quality = CALIDADES.values()
list_servers = ['directo', 'openload']

host = 'http://doomtv.net/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Todas",
                   action="lista",
                   thumbnail=get_thumb('all', auto=True),
                   fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                   url='%s%s'%(host,'peliculas/page/1')
                   ))

    itemlist.append(
        item.clone(title="Generos",
                   action="seccion",
                   thumbnail=get_thumb('genres', auto=True),
                   fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                   url='%s%s' % (host, 'peliculas/page/1'),
                   ))

    itemlist.append(
        item.clone(title="Mas Vistas",
                   action="lista",
                   thumbnail=get_thumb('more watched', auto=True),
                   fanart='https://s9.postimg.org/wmhzu9d7z/vistas.png',
                   url='%s%s'%(host,'top-imdb/page/1'),
                   ))

    itemlist.append(
        item.clone(title="Buscar",
                   action="search",
                   url='http://doomtv.net/?s=',
                   thumbnail=get_thumb('search', auto=True),
                   fanart='https://s30.postimg.org/pei7txpa9/buscar.png'
                   ))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    max_items = 20
    next_page_url = ''

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'movie-id=.*?href=(.*?) data-url.*?quality>(.*?)'
    patron += '<img data-original=(.*?) class.*?<h2>(.*?)<\/h2>.*?<p>(.*?)<\/p>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if item.next_page != 'b':
        if len(matches) > max_items:
            next_page_url = item.url
            matches = matches[:max_items]
            next_page = 'b'
    else:
        matches = matches[max_items:]
        next_page = 'a'
        next_page_str = scrapertools.find_single_match(data,"<li class='active'><a class=''>(\d+)</a>")
        next_page_num = int(next_page_str)+1
        page_base = re.sub(r'(page\/\d+)','', item.url)
        next_page_url = '%s%s%s'%(page_base,'page/',next_page_num)

        if next_page_url:
            next_page_url =  next_page_url

    for scrapedurl, quality, scrapedthumbnail, scrapedtitle, plot in matches:

        url = scrapedurl
        thumbnail = scrapedthumbnail
        filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w185", "")
        filtro_list = {"poster_path": filtro_thumb.strip()}
        filtro_list = filtro_list.items()
        title = scrapedtitle
        fanart = ''
        plot = plot
        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title=title,
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 infoLabels={'filtro': filtro_list},
                 fanart=fanart,
                 contentTitle=title
                 ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    # Paginacion
    if next_page_url != '':
        itemlist.append(
            Item(channel=item.channel,
                 action="lista",
                 title='Siguiente >>>',
                 url=next_page_url,
                 thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png',
                 extra=item.extra,
                 next_page=next_page
                 ))
    return itemlist


def seccion(item):
    logger.info()

    itemlist = []
    duplicado = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'menu-item-object-category menu-item-\d+><a href=(.*?)>(.*?)<\/a><\/li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = ''
        if url not in duplicado:
            itemlist.append(
                Item(channel=item.channel,
                     action='lista',
                     title=title,
                     url=url,
                     thumbnail=thumbnail
                     ))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return lista(item)


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # categoria='peliculas'
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host +'peliculas/page/1'
        elif categoria == 'infantiles':
            item.url = host + 'categoria/animacion/'
        elif categoria == 'terror':
            item.url = host + '/categoria/terror/'
        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'id=(tab\d+)><div class=movieplay><(?:iframe|script) src=(.*?)(?:scrolling|frameborder|><\/script>)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, urls in matches:

        new_item = Item(
                        channel=item.channel,
                        url=urls,
                        title=item.title,
                        contentTitle=item.title,
                        action='play',
                        )
        itemlist.append(new_item)
    itemlist = servertools.get_servers_itemlist(itemlist)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))

    return itemlist
