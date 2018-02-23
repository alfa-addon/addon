# -*- coding: utf-8 -*-
# -*- Channel CanalPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urllib
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "canalpelis"

host = "http://www.canalpelis.com/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]


parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

thumbnail = "https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/%s.png"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Peliculas", action="peliculas",thumbnail=get_thumb('movies', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'movies/', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Géneros", action="generos",thumbnail=get_thumb('genres', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'genre/', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Año de Estreno", action="year_release", thumbnail=get_thumb('year', auto=True),
                               text_blod=True, page=0, viewcontent='movies', url=host + 'release/',
                               viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Buscar", action="search",thumbnail=get_thumb('search', auto=True),
                               text_blod=True, url=host, page=0))

    itemlist.append(item.clone(title="Series", action="series", extra='serie', url=host + 'tvshows/',
                               viewmode="movie_with_plot", text_blod=True, viewcontent='movies',
                               thumbnail=get_thumb('tvshows', auto=True), page=0))

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
    # logger.info(data)
    patron = '<div class="thumbnail animation-2"><a href="([^"]+)">.*?'  # url
    patron += '<img src="([^"]+)" alt="([^"]+)" />.*?'  # img and title
    patron += '<span class="([^"]+)".*?'  # tipo
    patron += '<span class="year">([^<]+)</span>'  # year
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, tipo, year in matches:

        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, contentTitle=scrapedtitle,
                                   action="findvideos", infoLabels={"year": year},
                                   thumbnail=scrapedthumbnail, text_color=color3, page=0))

    paginacion = scrapertools.find_single_match(
        data, '<a class="page larger" href="([^"]+)">\d+</a>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=paginacion))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = '<div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?'  # img, title.strip()
    patron += '<span class="icon-star2"></span>(.*?)/div>.*?'  # rating
    patron += '<span class="quality">([^<]+)</span>.*?'  # calidad
    patron += '<a href="([^"]+)"><div class="see"></div>.*?'  # url
    patron += '<span>(\d+)</span>'  # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, rating, quality, scrapedurl, year in matches[item.page:item.page + 20]:
        if 'Próximamente' not in quality and '-XXX.jpg' not in scrapedthumbnail:

            scrapedtitle = scrapedtitle.replace('Ver ', '').strip()
            contentTitle = scrapedtitle.partition(':')[0].partition(',')[0]
            title = "%s [COLOR green][%s][/COLOR] [COLOR yellow][%s][/COLOR]" % (
                scrapedtitle, year, quality)

            itemlist.append(item.clone(channel=__channel__, action="findvideos", text_color=color3,
                                       url=scrapedurl, infoLabels={'year': year},
                                       contentTitle=contentTitle, thumbnail=scrapedthumbnail,
                                       title=title, context="buscar_trailer", quality = quality))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 20 < len(matches):
        itemlist.append(item.clone(page=item.page + 20,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(
            data, "<span class=\"current\">\d+</span><a href='([^']+)'")

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »", text_color=color3))

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            datas = httptools.downloadpage(item.url).data
            datas = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", datas)
            item.fanart = scrapertools.find_single_match(
                datas, "<meta property='og:image' content='([^']+)' />")
            item.fanart = item.fanart.replace('w780', 'original')
            item.plot = scrapertools.find_single_match(datas, '</h4><p>(.*?)</p>')
            item.plot = scrapertools.htmlclean(item.plot)
            item.infoLabels['director'] = scrapertools.find_single_match(
                datas, '<div class="name"><a href="[^"]+">([^<]+)</a>')
            item.infoLabels['genre'] = scrapertools.find_single_match(
                datas, 'rel="tag">[^<]+</a><a href="[^"]+" rel="tag">([^<]+)</a>')

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="cat-item cat-item-[^"]+"><a href="([^"]+)" title="[^"]+">([^<]+)</a> <i>([^<]+)</i></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, cantidad in matches:
        if cantidad != '0' and scrapedtitle != '# Próximamente':
            title = "%s (%s)" % (scrapedtitle, cantidad)
            itemlist.append(item.clone(channel=item.channel, action="peliculas", title=title, page=0,
                                       url=scrapedurl, text_color=color3, viewmode="movie_with_plot"))

    return itemlist


def year_release(item):
    logger.info()
    itemlist = []

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'  # url, title
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        itemlist.append(item.clone(channel=item.channel, action="peliculas", title=scrapedtitle, page=0,
                                   url=scrapedurl, text_color=color3, viewmode="movie_with_plot", extra='next'))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)

    patron = '<div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?<a href="([^"]+)">.*?'
    patron += '<div class="texto">([^<]+)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, scrapedurl, plot in matches:
        if plot == '':
            plot = scrapertools.find_single_match(data, '<div class="texto">([^<]+)</div>')
        scrapedtitle = scrapedtitle.replace('Ver ', '').replace(
            ' Online HD', '').replace('ver ', '').replace(' Online', '').replace(' (Serie TV)', '').strip()
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, action="temporadas",
                                   contentSerieName=scrapedtitle, show=scrapedtitle, plot=plot,
                                   thumbnail=scrapedthumbnail, contentType='tvshow'))

    url_next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')

    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    if url_next_page:
        itemlist.append(Item(channel=__channel__, action="series",
                             title="» Siguiente »", url=url_next_page))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<span class="title">([^<]+)<i>.*?'  # numeros de temporadas
    patron += '<img src="([^"]+)"></a></div>'  # capitulos

    matches = scrapertools.find_multiple_matches(datas, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail, extra='temporadas')
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, __modo_grafico__)

        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadirselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.title)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=thumbnail_host, fanart=fanart_host))

        return itemlist
    else:
        return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # logger.info(datas)
    patron = '<div class="imagen"><a href="([^"]+)">.*?'  # url cap, img
    patron += '<div class="numerando">(.*?)</div>.*?'  # numerando cap
    patron += '<a href="[^"]+">([^<]+)</a>'  # title de episodios

    matches = scrapertools.find_multiple_matches(datas, patron)

    for scrapedurl, scrapedtitle, scrapedname in matches:
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+) - (\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        season, episode = match[0]

        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue

        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", text_color=color3, fulltitle=title,
                              contentType="episode")
        if 'infoLabels' not in new_item:
            new_item.infoLabels = {}

        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)

        itemlist.append(new_item)

    # TODO no hacer esto si estamos añadiendo a la videoteca
    if not item.extra:
        # Obtenemos los datos de todos los capitulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            if i.infoLabels['title']:
                # Si el capitulo tiene nombre propio añadirselo al titulo del item
                i.title = "%sx%s %s" % (i.infoLabels['season'], i.infoLabels[
                                        'episode'], i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si el capitulo tiene imagen propia remplazar al poster
                i.thumbnail = i.infoLabels['poster_path']

    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    # Opción "Añadir esta serie a la videoteca"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=thumbnail_host, fanart=fanart_host))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = '<div id="option-(\d+)" class="play-box-iframe.*?src="([^"]+)" frameborder="0" scrolling="no" allowfullscreen></iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, url in matches:
        datas = httptools.downloadpage(urlparse.urljoin(host, url),
                                                  headers={'Referer': item.url}).data

        patron = '<iframe[^>]+src="([^"]+)"'
        url = scrapertools.find_single_match(datas, patron)
        lang = scrapertools.find_single_match(
            data, '<li><a class="options" href="#option-%s"><b class="icon-play_arrow"><\/b> (.*?)<span class="dt_flag">' % option)
        lang = lang.replace('Español ', '').replace('B.S.O. ', '')

        server = servertools.get_server_from_url(url)
        title = "%s [COLOR yellow](%s) (%s)[/COLOR]" % (item.contentTitle, server.title(), lang)
        itemlist.append(item.clone(action='play', url=url, title=title, extra1=title,
                                   server=server, language = lang, text_color=color3))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=thumbnail_host, contentTitle=item.contentTitle))

    return itemlist
