# -*- coding: utf-8 -*-

import re

from core import channeltools
from core import httptools
from core import scrapertoolsV2
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

HOST = 'http://www.yaske.ro'
parameters = channeltools.get_channel_parameters('yaske')
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
color1, color2, color3 = ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E']


def mainlist(item):
    logger.info()
    itemlist = []
    item.url = HOST
    item.text_color = color2
    item.fanart = fanart_host
    thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/4/verdes/%s.png"

    itemlist.append(item.clone(title="Novedades", action="peliculas", text_bold=True, viewcontent='movies',
                               url=HOST,
                               thumbnail=thumbnail % 'novedades', viewmode="movie_with_plot"))
    itemlist.append(item.clone(title="Estrenos", action="peliculas", text_bold=True,
                               url=HOST + "/premiere", thumbnail=thumbnail % 'estrenos'))
    itemlist.append(item.clone(title="Género", action="menu_buscar_contenido", text_bold=True,thumbnail=thumbnail % 'generos', viewmode="thumbnails",
                               url=HOST
                               ))

    itemlist.append(item.clone(title="", folder=False))
    itemlist.append(item.clone(title="Buscar por título", action="search", thumbnail=thumbnail % 'buscar'))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    try:
        item.url = HOST + "/search/?query=" + texto.replace(' ', '+')
        item.extra = ""
        itemlist.extend(peliculas(item))
        if itemlist[-1].title == ">> Página siguiente":
            item_pag = itemlist[-1]
            itemlist = sorted(itemlist[:-1], key=lambda Item: Item.contentTitle)
            itemlist.append(item_pag)
        else:
            itemlist = sorted(itemlist, key=lambda Item: Item.contentTitle)

        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = HOST
        elif categoria == 'infantiles':
            item.url = HOST + "/genre/16/"
        elif categoria == 'terror':
            item.url = HOST + "/genre/27/"
        else:
            return []

        itemlist = peliculas(item)
        if itemlist[-1].title == ">> Página siguiente":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = 'class="post-item-image btn-play-item".*?'
    patron += 'href="([^"]+)">.*?'
    patron += '<img data-original="([^"]+)".*?'
    patron += 'glyphicon-calendar"></i>([^<]+).*?'
    patron += 'post-item-flags"> (.*?)</div.*?'
    patron += 'text-muted f-14">(.*?)</h3'

    matches = scrapertools.find_multiple_matches(data, patron)

    patron_next_page = 'href="([^"]+)"> &raquo;'
    matches_next_page = scrapertools.find_single_match(data, patron_next_page)
    if len(matches_next_page) > 0:
        url_next_page = item.url + matches_next_page

    for scrapedurl, scrapedthumbnail, year, idiomas, scrapedtitle in matches:
        year = year.strip()
        patronidiomas = '<img src="([^"]+)"'
        matchesidiomas = scrapertools.find_multiple_matches(idiomas, patronidiomas)
        idiomas_disponibles = []
        for idioma in matchesidiomas:
            if idioma.endswith("/la.png"):
                idiomas_disponibles.append("LAT")
            elif idioma.endswith("/en.png"):
                idiomas_disponibles.append("VO")
            elif idioma.endswith("/en_es.png"):
                idiomas_disponibles.append("VOSE")
            elif idioma.endswith("/es.png"):
                idiomas_disponibles.append("ESP")

        if idiomas_disponibles:
            idiomas_disponibles = "[" + "/".join(idiomas_disponibles) + "]"
        contentTitle = scrapertoolsV2.htmlclean(scrapedtitle.strip())
        title = "%s %s" % (contentTitle, idiomas_disponibles)
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl,
                             thumbnail=scrapedthumbnail, contentTitle=contentTitle,
                             infoLabels={"year": year}, text_color=color1))
    # Obtenemos los datos basicos de todas las peliculas mediante multihilos
    tmdb.set_infoLabels(itemlist)

    # Si es necesario añadir paginacion
    if url_next_page:
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=">> Página siguiente", thumbnail=thumbnail_host,
                 url=url_next_page, folder=True, text_color=color3, text_bold=True))

    return itemlist


def menu_buscar_contenido(item):
    logger.info(item)
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = 'Generos.*?</ul>'
    data = scrapertools.find_single_match(data, patron)
    # Extrae las entradas
    patron = 'href="([^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        url = HOST + scrapedurl
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = scrapedtitle,
                             url = url,
                             text_color = color1,
                             contentType = 'movie',
                             folder = True,
                             viewmode = "movie_with_plot"
                             ))

    if item.extra in ['genre', 'audio', 'year']:
        return sorted(itemlist, key=lambda i: i.title.lower(), reverse=item.extra == 'year')
    else:
        return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    sublist = []

    # Descarga la página
    url = "http://widget.olimpo.link/playlist/?tmdb=" + scrapertools.find_single_match(item.url, 'yaske.ro/([0-9]+)')
    data = httptools.downloadpage(url).data
    if not item.plot:
        item.plot = scrapertoolsV2.find_single_match(data, '>Sinopsis</dt> <dd>([^<]+)</dd>')
        item.plot = scrapertoolsV2.decodeHtmlentities(item.plot)

    patron  = '(/embed/[^"]+).*?'
    patron += 'quality text-overflow ">([^<]+).*?'
    patron += 'title="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, calidad, idioma in matches:
        if 'embed' in url:
            url = "http://widget.olimpo.link" + url
            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, 'iframe src="([^"]+)')
            sublist.append(item.clone(channel=item.channel, action="play", url=url, folder=False, text_color=color1, quality=calidad.strip(),
                                  language=idioma.strip()))
    sublist = servertools.get_servers_itemlist(sublist, lambda i: "Ver en %s %s" % (i.server, i.quality), True)

    # Añadir servidores encontrados, agrupandolos por idioma
    for k in ["Español", "Latino", "Subtitulado", "Ingles"]:
        lista_idioma = filter(lambda i: i.language == k, sublist)
        if lista_idioma:
            itemlist.append(Item(channel=item.channel, title=k, fanart=item.fanart, folder=False,
                                 text_color=color2, text_bold=True, thumbnail=thumbnail_host))
            itemlist.extend(lista_idioma)

    # Insertar items "Buscar trailer" y "Añadir a la videoteca"
    if itemlist and item.extra != "library":
        title = "%s [Buscar trailer]" % (item.contentTitle)
        itemlist.insert(0, item.clone(channel="trailertools", action="buscartrailer",
                                      text_color=color3, title=title, viewmode="list"))

        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, text_color="green",
                                 contentTitle=item.contentTitle, extra="library", thumbnail=thumbnail_host))

    return itemlist
