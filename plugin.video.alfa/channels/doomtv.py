# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()

CALIDADES = {'1080p': '1080p', '720p': '720p', '480p': '480p', '360p': '360p'}
list_quality = CALIDADES.values()
list_servers = ['directo', 'openload']

host = 'http://doomtv.net/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0 Chrome/58.0.3029.110',
    'Referer': host}

tgenero = {"Comedia": "https://s7.postimg.org/ne9g9zgwb/comedia.png",
           "Suspenso": "https://s13.postimg.org/wmw6vl1cn/suspenso.png",
           "Drama": "https://s16.postimg.org/94sia332d/drama.png",
           "Acción": "https://s3.postimg.org/y6o9puflv/accion.png",
           "Aventura": "https://s10.postimg.org/6su40czih/aventura.png",
           "Romance": "https://s15.postimg.org/fb5j8cl63/romance.png",
           "Animación": "https://s13.postimg.org/5on877l87/animacion.png",
           "Ciencia ficción": "https://s9.postimg.org/diu70s7j3/cienciaficcion.png",
           "Terror": "https://s7.postimg.org/yi0gij3gb/terror.png",
           "Documental": "https://s16.postimg.org/7xjj4bmol/documental.png",
           "Música": "https://s29.postimg.org/bbxmdh9c7/musical.png",
           "Fantasía": "https://s13.postimg.org/65ylohgvb/fantasia.png",
           "Bélico Guerra": "https://s23.postimg.org/71itp9hcr/belica.png",
           "Misterio": "https://s1.postimg.org/w7fdgf2vj/misterio.png",
           "Crimen": "https://s4.postimg.org/6z27zhirx/crimen.png",
           "Biográfia": "https://s15.postimg.org/5lrpbx323/biografia.png",
           "Familia": "https://s7.postimg.org/6s7vdhqrf/familiar.png",
           "Familiar": "https://s7.postimg.org/6s7vdhqrf/familiar.png",
           "Intriga": "https://s27.postimg.org/v9og43u2b/intriga.png",
           "Thriller": "https://s22.postimg.org/5y9g0jsu9/thriller.png",
           "Guerra": "https://s4.postimg.org/n1h2jp2jh/guerra.png",
           "Estrenos": "https://s21.postimg.org/fy69wzm93/estrenos.png",
           "Peleas": "https://s14.postimg.org/we1oyg05t/peleas.png",
           "Policiales": "https://s21.postimg.org/n9e0ci31z/policial.png",
           "Uncategorized": "https://s30.postimg.org/uj5tslenl/otros.png",
           "LGBT": "https://s30.postimg.org/uj5tslenl/otros.png"}


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        item.clone(title="Todas",
                   action="lista",
                   thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                   fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                   url='%s%s'%(host,'peliculas/page/1')
                   ))

    itemlist.append(
        item.clone(title="Generos",
                   action="seccion",
                   thumbnail='https://s3.postimg.org/5s9jg2wtf/generos.png',
                   fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                   url='%s%s' % (host, 'peliculas/page/1'),
                   ))

    itemlist.append(
        item.clone(title="Mas Vistas",
                   action="lista",
                   thumbnail='https://s9.postimg.org/wmhzu9d7z/vistas.png',
                   fanart='https://s9.postimg.org/wmhzu9d7z/vistas.png',
                   url='%s%s'%(host,'top-imdb/page/1'),
                   ))

    itemlist.append(
        item.clone(title="Buscar",
                   action="search",
                   url='http://doomtv.net/?s=',
                   thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
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
        if title in tgenero:
            thumbnail = tgenero[title]
        if url not in duplicado:
            itemlist.append(
                Item(channel=item.channel,
                     action='lista',
                     title=title,
                     url=url,
                     thumbnail = thumbnail
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
    #itemlist = get_url(item)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    url_m3u8 = scrapertools.find_single_match(data, '<source src=(.*?) type=application/x-mpegURL/>')
    itemlist.append(item.clone(url=url_m3u8, action='play'))
    patron = 'id=(tab\d+)><div class=movieplay><(?:iframe|script) src=(.*?)(?:scrolling|><\/script>)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, urls in matches:
        quality = scrapertools.find_single_match(data, '<div class=les-content><a href=#%s>(.*?)<\/a><\/div>'%option)
        title = '%s (%s)' % (item.title, quality)
        if 'content' in urls:
            urls = '%s%s'%('http:',urls)
            hidden_data = httptools.downloadpage(urls).data
            hidden_data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", hidden_data)
            patron = 'sources: \[{file: (.*?),'
            matches = re.compile(patron, re.DOTALL).findall(hidden_data)

            for videoitem in matches:

                new_item = Item(
                                channel = item.channel,
                                url = videoitem,
                                title = title,
                                contentTitle = item.title,
                                action = 'play',
                                quality = quality
                                )
                itemlist.append(new_item)
        else:
            new_item = Item(
                            channel=item.channel,
                            url=urls,
                            title=title,
                            contentTitle=item.title,
                            action='play',
                            quality = quality
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
