# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from core import servertools

host = "http://www.pelisplus.tv/"

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

patrones = ['<img src="([^"]+)" alt=".*?" class="picture-movie">',
            '<span>Sinopsis:<\/span>.([^<]+)<span class="text-detail-hide"><\/span>.<\/p>']

IDIOMA = {'latino': 'Latino'}
list_language = IDIOMA.values()

list_quality = ['1080p',
                '720p',
                '480p',
                '360p',
                '240p',
                'default'
                ]
list_servers = [
    'gvideo',
    'openload',
    'thevideos'
]


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(
        item.clone(title="Peliculas",
                   action="menupeliculas",
                   thumbnail='https://s8.postimg.org/6wqwy2c2t/peliculas.png',
                   fanart='https://s8.postimg.org/6wqwy2c2t/peliculas.png',
                   extra='peliculas/'
                   ))

    itemlist.append(
        item.clone(title="Series",
                   action="menuseries",
                   thumbnail='https://s27.postimg.org/iahczwgrn/series.png',
                   fanart='https://s27.postimg.org/iahczwgrn/series.png',
                   extra='peliculas/'
                   ))

    itemlist.append(
        item.clone(title="Documentales",
                   action="lista",
                   url=host + 'documentales/pag-1',
                   thumbnail='https://s16.postimg.org/7xjj4bmol/documental.png',
                   fanart='https://s16.postimg.org/7xjj4bmol/documental.png',
                   extra='documentales/'
                   ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def menupeliculas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               url=host + 'peliculas/pag-1',
                               thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               extra='peliculas/'
                               ))

    itemlist.append(item.clone(title="Ultimas",
                               action="lista",
                               url=host + 'estrenos/pag-1',
                               thumbnail='https://s22.postimg.org/cb7nmhwv5/ultimas.png',
                               fanart='https://s22.postimg.org/cb7nmhwv5/ultimas.png',
                               extra='estrenos/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               url=host + 'peliculas/pag-1',
                               thumbnail='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               extra='documentales/'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + 'busqueda/?s=',
                               thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
                               fanart='https://s30.postimg.org/pei7txpa9/buscar.png',
                               extra='peliculas/'
                               ))

    return itemlist


def menuseries(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               url=host + "series/pag-1",
                               thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               extra='series/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               url=host + 'series/pag-1',
                               thumbnail='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               extra='series/'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + 'busqueda/?s=',
                               thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
                               fanart='https://s30.postimg.org/pei7txpa9/buscar.png',
                               extra='series/'
                               ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + 'busqueda/?s=' + texto

    try:
        if texto != '':
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()

    itemlist = []

    if 'series/' in item.extra:
        accion = 'temporadas'
        tipo = 'tvshow'
    else:
        accion = 'findvideos'
        tipo = 'movie'

    data = httptools.downloadpage(item.url).data

    if item.action != 'search':
        patron = '<img.*?width="147" heigh="197".*?src="([^"]+)".*?>.*?.<i class="icon online-play"><\/i>.*?.<h2 ' \
                 'class="title title-.*?">.*?.<a href="([^"]+)" title="([^"]+)">.*?>'
        actual = scrapertools.find_single_match(data,
                                                '<a href="https:\/\/www.pelisplus.tv\/.*?\/pag-([^p]+)pag-2" '
                                                'class="page bicon last"><<\/a>')
    else:
        patron = '<img data-original="([^"]+)".*?width="147" heigh="197".*?src=.*?>.*?\n<i class="icon ' \
                 'online-play"><\/i>.*?\n<h2 class="title title-.*?">.*?\n<a href="([^"]+)" title="([^"]+)">.*?>'
        actual = ''

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        thumbnail = scrapedthumbnail

        filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w154", "")
        filtro_list = {"poster_path": filtro_thumb}  # Nombre del campo a filtrar y valor en los resultados de la api
        #  de tmdb
        filtro_list = filtro_list.items()

        if item.action != 'search':

            new_item=(
                Item(channel=item.channel,
                     contentType=tipo,
                     action=accion,
                     title=title,
                     url=scrapedurl,
                     thumbnail=thumbnail,
                     fulltitle=scrapedtitle,
                     infoLabels={'filtro': filtro_list},
                     extra=item.extra,
                     context=autoplay.context
                     ))
            if 'serie' in scrapedurl:
                new_item.contentSerieName=scrapedtitle
            else:
                new_item.contentTitle = scrapedtitle
            itemlist.append(new_item)
        else:
            if item.extra=='':
                item.extra = scrapertools.find_single_match(url, 'serie|pelicula')+'s/'
                if 'series/' in item.extra:
                    accion = 'temporadas'
                    tipo = 'tvshow'
                else:
                    accion = 'findvideos'
                    tipo = 'movie'
            item.extra = item.extra.rstrip('s/')
            if item.extra in url:
                new_item=(
                    Item(channel=item.channel,
                         contentType=tipo,
                         action=accion,
                         title=scrapedtitle,
                         url=scrapedurl,
                         thumbnail=scrapedthumbnail,
                         fulltitle=scrapedtitle,
                         infoLabels={'filtro': filtro_list},
                         extra=item.extra,
                         context=autoplay.context
                         ))
                if 'serie' in scrapedurl:
                    new_item.contentSerieName=scrapedtitle
                else:
                    new_item.contentTitle = scrapedtitle
                itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if item.action != 'search' and actual != '':
        if itemlist != []:
            next_page = str(int(actual) + 1)
            next_page_url = item.extra + 'pag-' + next_page
            if not next_page_url.startswith("http"):
                next_page_url = host + next_page_url
            itemlist.append(
                Item(channel=item.channel,
                     action="lista",
                     title='Siguiente >>>',
                     url=next_page_url,
                     thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png',
                     extra=item.extra
                     ))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    templist = []
    data = httptools.downloadpage(item.url).data

    patron = '<span class="ico accordion_down"><\/span>Temporada([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle in matches:
        infoLabels = item.infoLabels
        url = item.url
        title = 'Temporada ' + scrapedtitle.strip(' \r\n')
        thumbnail = scrapertools.find_single_match(data, '<img src="([^"]+)" alt="" class="picture-movie">')
        plot = scrapertools.find_single_match(data,
                                              '<span>Sinopsis:<\/span>.([^<]+).<span class="text-detail-hide"><\/span>')
        fanart = scrapertools.find_single_match(data, '<img src="([^"]+)"/>.*?</a>')
        contentSeasonNumber = scrapedtitle.strip(' \r\n')
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=title,
                 fulltitle=item.title,
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 fanart=fanart,
                 extra=scrapedtitle.rstrip('\n'),
                 contentSerieName=item.contentSerieName,
                 contentSeasonNumber=contentSeasonNumber,
                 infoLabels={'season': contentSeasonNumber},
                 context=item.context
                 ))

    if item.extra == 'temporadas':
        for tempitem in itemlist:
            templist += episodios(tempitem)
    else:
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_serie_to_library",
                 extra="temporadas",
                 contentSerieName=item.contentSerieName,
                 contentSeasonNumber=contentSeasonNumber
                 ))
    if item.extra == 'temporadas':
        return templist
    else:
        return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<span class="ico season_play"><\/span>([^<]+)<\/a>.<a href="([^"]+)" class="season-online enabled">'
    temporada = 'temporada/' + item.extra.strip(' ')
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels

    for scrapedtitle, scrapedurl in matches:

        if temporada in scrapedurl:
            url = scrapedurl
            contentSeasonNumber = re.findall(r'temporada.*?(\d+)', url)
            capitulo = re.findall(r'Capitulo \d+', scrapedtitle)
            contentEpisodeNumber = re.findall(r'\d+', capitulo[0])
            contentEpisodeNumber = contentEpisodeNumber[0]
            infoLabels['episode'] = contentEpisodeNumber
            title = contentSeasonNumber[0] + 'x' + contentEpisodeNumber + ' - ' + scrapedtitle

            thumbnail = scrapertools.find_single_match(data, '<img src="([^"]+)" alt="" class="picture-movie">')
            plot = ''
            fanart = ''
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=title,
                     fulltitle=item.title,
                     url=url,
                     thumbnail=thumbnail,
                     plot=plot,
                     fanart=fanart,
                     extra=scrapedtitle,
                     contentSeasonNumber=item.contentSeasonNumber,
                     infoLabels=infoLabels,
                     context=item.context
                     ))
    if item.extra != 'temporadas':
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        itemlist = fail_tmdb(itemlist)
    return itemlist


def fail_tmdb(itemlist):
    logger.info()
    realplot = ''
    for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            if item.fanart == '':
                item.fanart = scrapertools.find_single_match(data, patrones[0])
            realplot = scrapertools.find_single_match(data, patrones[1])
            item.plot = scrapertools.remove_htmltags(realplot)
    return itemlist


def generos(item):
    tgenero = {"Comedia": "https://s7.postimg.org/ne9g9zgwb/comedia.png",
               "Suspense": "https://s13.postimg.org/wmw6vl1cn/suspenso.png",
               "Drama": "https://s16.postimg.org/94sia332d/drama.png",
               "Accion": "https://s3.postimg.org/y6o9puflv/accion.png",
               "Aventura": "https://s10.postimg.org/6su40czih/aventura.png",
               "Romance": "https://s15.postimg.org/fb5j8cl63/romance.png",
               "Animacion": "https://s13.postimg.org/5on877l87/animacion.png",
               "Ciencia Ficcion": "https://s9.postimg.org/diu70s7j3/cienciaficcion.png",
               "Terror": "https://s7.postimg.org/yi0gij3gb/terror.png",
               "Documental": "https://s16.postimg.org/7xjj4bmol/documental.png",
               "Musica": "https://s29.postimg.org/bbxmdh9c7/musical.png",
               "Western": "https://s23.postimg.org/lzyfbjzhn/western.png",
               "Fantasia": "https://s13.postimg.org/65ylohgvb/fantasia.png",
               "Guerra": "https://s23.postimg.org/71itp9hcr/belica.png",
               "Misterio": "https://s1.postimg.org/w7fdgf2vj/misterio.png",
               "Crimen": "https://s4.postimg.org/6z27zhirx/crimen.png",
               "Historia": "https://s15.postimg.org/fmc050h1n/historia.png",
               "Pelicula De La Television": "https://s9.postimg.org/t8xb14fb3/delatv.png",
               "Foreign": "https://s29.postimg.org/jdc2m158n/extranjera.png"}

    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<i class="s-upper" id="([^"]+)"><\/i>.<span>([^<]+)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        url = scrapedurl + 'pag-1'
        title = scrapedtitle
        if scrapedtitle in tgenero:
            thumbnail = tgenero[scrapedtitle]
            fanart = tgenero[scrapedtitle]
        else:
            thumbnail = ''
            fanart = ''
        extra = scrapedurl.replace('http://www.pelisplus.tv/', '')
        itemlist.append(
            Item(channel=item.channel,
                 action="lista",
                 title=title,
                 fulltitle=item.title,
                 url=url,
                 thumbnail=thumbnail,
                 fanart=fanart,
                 extra=extra
                 ))
    return itemlist

def get_vip(url):
    logger.info()
    itemlist =[]
    url= url.replace('reproductor','vip')
    data = httptools.downloadpage(url).data
    video_urls = scrapertools.find_multiple_matches(data,'<a href="(.*?)".*?>')
    for item in video_urls:
        if 'elreyxhd' in item:
            if 'plus'in item:
                id, tipo, lang= scrapertools.find_single_match(item,'plus\/(\d+)\/.*?=(\d+).*?=(.*)')
                new_url = 'https://www.elreyxhd.com/pelisplus.php?id=%s&tipo=%s&idioma=%s' % (id, tipo, lang)
                datax=httptools.downloadpage(new_url, follow_redirects=False).headers.get("location", "")
                itemlist.append(Item(url=datax))
            else:
                id = scrapertools.find_single_match(item,'episodes\/(\d+)')
                data_vip = httptools.downloadpage(item).data
                patron = '<a href="(.*?)">'
                matches = re.compile(patron, re.DOTALL).findall(data_vip)
                for urls in matches:
                    x = scrapertools.find_single_match(urls,r"&x=(\d)&")
                    if x != '':
                        new_url = 'https://www.elreyxhd.com/samir.php?id=%s&tipo=capitulo&idioma=latino&x=%s&sv=si' % (id, x)
                        datax = httptools.downloadpage(new_url, follow_redirects=False).headers.get("location", "")
                        itemlist.append(Item(url=datax))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    duplicados = []
    data = httptools.downloadpage(item.url).data
    video_page = scrapertools.find_single_match(data, "<iframe width='100%' height='500' src='(.*?)' frameborder='0'")

    itemlist.extend(get_vip(video_page))

    data = httptools.downloadpage(video_page).data
    patron = '<li data-id=".*?">\s+<a href="(.*?)" >'
    matches = re.compile(patron, re.DOTALL).findall(data)

    itemlist.extend(servertools.find_video_items(data=data))

    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.infoLabels = item.infoLabels
        if videoitem.quality == '' or videoitem.language == '':
           videoitem.quality = 'default'
           videoitem.language = 'Latino'
        videoitem.action = 'play'
        videoitem.fulltitle = item.title
        if videoitem.extra != 'directo' and 'youtube' not in videoitem.url:
           videoitem.title = item.contentTitle + ' (%s)'

    itemlist=servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    n = 0
    for videoitem in itemlist:
        if 'youtube' in videoitem.url:
            videoitem.title = '[COLOR orange]Trailer en' + ' (' + videoitem.server + ')[/COLOR]'
            itemlist[n], itemlist[-1] = itemlist[-1], itemlist[n]
        n = n + 1

    if item.extra == 'findvideos' and 'youtube' in itemlist[-1]:
        itemlist.pop(1)

        # Requerido para FilterTools
    tmdb.set_infoLabels_itemlist(itemlist, True)
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if 'serie' not in item.url:
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel,
                     title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url,
                     action="add_pelicula_to_library",
                     extra="findvideos",
                     contentTitle=item.contentTitle
                     ))

    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.extra = 'estrenos/'
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + 'estrenos/pag-1'

        elif categoria == 'infantiles':
            item.url = host + 'peliculas/animacion/pag-1'

        elif categoria == 'terror':
            item.url = host + 'peliculas/terror/pag-1'

        elif categoria == 'documentales':
            item.url = host + 'documentales/pag-1'
            item.extra = 'documentales/'

        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    #itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist
