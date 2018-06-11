# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from platformcode import logger
from platformcode import config
from core import tmdb
from channelselector import get_thumb

from channels import filtertools
from channels import autoplay


__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'peliculasdk')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'peliculasdk')
__adult_mode__ = config.get_setting("adult_mode")

host = "http://www.peliculasdk.com"


IDIOMAS = {'es': 'Español', 'la': 'Latino', 'su': 'Subtitulado', 'in': 'Inglés'}
list_language = IDIOMAS.values()
list_quality = ['HD-1080', 'HD-720', 'HD-320', 'BR-R', 'BR-S', 'DVD-R', 'DVD-S', 'TS-HQ', 'TS', 'CAM']  # -R:Rip, -S:Screener
list_servers = ['directo', 'streamango', 'powvideo', 'datoporn', 'gamovideo', 'streamplay', 'okru', 'rapidvideo', 'openload']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Estrenos', action='peliculas', url= host + "/ver/estrenos/",
                         thumbnail=get_thumb('newest', auto=True), type='movies'))

    itemlist.append(Item(channel=item.channel, title='Por géneros', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))

    itemlist.append(Item(channel=item.channel, title='Por calidades', action='section',
                         thumbnail=get_thumb('quality', auto=True), type='movies'))

    itemlist.append(Item(channel=item.channel, title='Por idiomas', action='section',
                         thumbnail=get_thumb('language', auto=True), type='movies'))

    if __adult_mode__ != 0:
        itemlist.append(Item(channel=item.channel, title='Adultos +18', action='peliculas', url= host + "/genero/adultos/",
                             thumbnail=get_thumb('adults', auto=True), type='movies'))

    itemlist.append(Item(channel=item.channel, title='Buscar...', action='search',
                         thumbnail=get_thumb('search', auto=True), type='movies'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def section(item):
    logger.info()
    itemlist=[]
    duplicados=[]
    data = httptools.downloadpage(host).data

    if 'Por géneros' in item.title:
        patron = '<li><a href="(\/genero\/[^"]*)">([^<]*)<\/a><\/li>'  #<li><a href="/genero/accion">Acción</a></li>
    elif 'Por calidades' in item.title:
        patron = "<li><a href='(\/calidad\/[^']*)'>([^<]*)<\/a><\/li>" #<li><a href='/calidad/HD-1080/'>HD 1080</a></li>
    elif 'Por idiomas' in item.title:
        patron = "<li><a href='(\/idioma\/[^']*)'>([^<]*)<\/a><\/li>"  #<li><a href='/idioma/Espanol/'>Español</a></li>

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle not in duplicados:
            itemlist.append(Item(channel=item.channel, url=host + scrapedurl, title=scrapedtitle, action='peliculas',
                                 type=item.type))
            duplicados.append(scrapedtitle)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")

    item.url = host + "/index.php?s=%s&x=0&y=0" % (texto)

    try:
        return buscador(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def buscador(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|&#.*?;", "", data)

    patron = 'style="position:relative"> '
    patron += '<a href="([^"]+)">'
    patron += '<img src="([^"]+)" alt="([^"]+)"></a><br>'
    patron += '<div class="titulope">([^<]+)</div>.*?'
    patron += 'Audio: (.+?)</div>.*?'
    patron += 'Calidad: (.+?)</div>.*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtitleorig, scrapedlenguaje, scrapedcalidad in matches:
        
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        scrapedtitle = re.sub(r"\(\d+\)", "", scrapedtitle).strip()

        audios = scrapertools.find_multiple_matches(scrapedlenguaje, '<a href="[^"]*" rel="[^"]*">([^<]*)</a>')
        calidad = scrapertools.find_single_match(scrapedcalidad, '<a href="[^"]*" rel="[^"]*">([^<]*)</a>')

        titulo = '%s [%s][%s]' % (scrapedtitle, ','.join([a[:3] for a in audios]), calidad)

        # Parece que las pelis de adultos se mezclan en la búsqueda y lo único que las diferencia es que no tienen Calidad
        if calidades or __adult_mode__ != 0:
            itemlist.append(Item(channel=item.channel,
                                 action="findvideos", url=scrapedurl,
                                 title=titulo, contentTitle=scrapedtitle,
                                 thumbnail=scrapedthumbnail,
                                 language=audios,
                                 quality=calidad,
                                 infoLabels={'year':year}
                                 ))

    tmdb.set_infoLabels(itemlist)

    # Paginación
    url_next_page = scrapertools.find_single_match(data,'<a href="([^"]*)">Siguiente &raquo;</a>')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|&#.*?;", "", data)

    patron = 'style="position:relative"> '
    patron += '<a href="([^"]+)">'
    patron += '<img src="([^"]+)" alt="([^"]+)"></a><br>'
    patron += '<div class="titulope">([^<]+)</div>.*?'
    patron += 'Audio: (.+?)</div>.*?'
    patron += 'Calidad: (.+?)</div>.*?'
    patron += 'Género: (.+?)</div>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtitleorig, scrapedlenguaje, scrapedcalidad, scrapedgenero in matches:
        
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        scrapedtitle = re.sub(r"\(\d+\)", "", scrapedtitle).strip()

        audios = scrapertools.find_multiple_matches(scrapedlenguaje, '<a href="[^"]*" rel="[^"]*">([^<]*)</a>')
        calidad = scrapertools.find_single_match(scrapedcalidad, '<a href="[^"]*" rel="[^"]*">([^<]*)</a>')
        generos = scrapertools.find_multiple_matches(scrapedgenero, '<a href="[^"]*" rel="[^"]*">([^<]*)</a>')

        titulo = '%s [%s][%s]' % (scrapedtitle, ','.join([a[:3] for a in audios]), calidad)

        if 'Adultos' not in generos or __adult_mode__ != 0:
            itemlist.append(Item(channel=item.channel,
                                 action="findvideos", url=scrapedurl,
                                 title=titulo, contentTitle=scrapedtitle,
                                 thumbnail=scrapedthumbnail,
                                 language=audios,
                                 quality=calidad,
                                 infoLabels={'year':year}
                                 ))

    tmdb.set_infoLabels(itemlist)

    # Paginación
    url_next_page = scrapertools.find_single_match(data,'<a href="([^"]*)">Siguiente &raquo;</a>')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<li><a href="#(tab\d+)"><span class="re">\d<\/span><span class="([^"]+)"><\/span><span class=.*?>([^<]+)<\/span>'
    check = re.compile(patron, re.DOTALL).findall(data)
    if not check:
        patron = '<li><a href="#(tab\d+)">'
        check = re.compile(patron, re.DOTALL).findall(data)
        for i, valor in enumerate(check):
            check[i] = [valor, '', '']

    patron = '<div id="(tab\d+)" class="tab_content">(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    servers_data_list = []
    for i, match in enumerate(matches):
        if match[0] == check[i][0]:
            if '<iframe' in match[1]:
                src = scrapertools.find_single_match(match[1], ' src="([^"]*)"')
                servers_data_list.append([check[i][1], check[i][2], 'iframe', src])  # idioma, calidad, 'iframe', src 

            elif '<script' in match[1]:
                src = scrapertools.find_single_match(match[1], '<script>(.*?)<\/script>')
                if src:
                    func, parm  = scrapertools.find_single_match(src, '(.*?)\("([^"]*)"\)')
                    servers_data_list.append([check[i][1], check[i][2], func, parm ])  # idioma, calidad, func, parm 

    data = httptools.downloadpage(host + '/Js/videod.js').data
    patron = 'function (\w+)\(id\){(.*?)}'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for idioma, calidad, func, parm in servers_data_list:
        if func == 'iframe':
            title = "Ver en: %s [" + idioma + "][" + calidad + "]"
            itemlist.append(
                item.clone(title=title, url=parm, action="play",
                     thumbnail=item.category,
                     language=idioma, quality=calidad))

        else:
            for funcion, contenido in matches:
                if funcion == func:
                    if '<script' in contenido: continue
                    if '<iframe' in contenido:
                        src = scrapertools.find_single_match(contenido, 'src="([^"]*)"')
                    else:
                        src = scrapertools.find_single_match(contenido, 'href="([^"]*)"')
                    if "'+codigo+'" not in src: continue
                    src = src.replace("'+codigo+'", parm)

                    title = "Ver en: %s [" + idioma + "][" + calidad + "]"
                    itemlist.append(
                        item.clone(title=title, url=src, action="play",
                             thumbnail=item.category,
                             language=idioma, quality=calidad))
                    break

    tmdb.set_infoLabels(itemlist)

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
        infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                      'title': item.fulltitle}
        itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                             action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                             text_color="0xFFff6666",
                             thumbnail='http://imgur.com/0gyYvuC.png'))

    itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'castellano':
            item.url = host + "idioma/Espanol/"
            item.action = "peliculas"
        itemlist = peliculas(item)
        if itemlist[-1].action == "peliculas":
            itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist
