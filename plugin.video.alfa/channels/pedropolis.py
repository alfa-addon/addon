# -*- coding: utf-8 -*-
# -*- Channel PedroPolis -*-
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

__channel__ = "pedropolis"

host = "http://pedropolis.com/"

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
    itemlist = [item.clone(title="Peliculas", action="menumovies", text_blod=True,
                           viewcontent='movies', viewmode="movie_with_plot"),
                item.clone(title="Series", action="menuseries", text_blod=True, extra='serie', mediatype= "tvshow",
                           viewcontent='tvshows', url=host + 'tvshows/', viewmode="movie_with_plot")]

    return itemlist


def menumovies(item):
    logger.info()
    itemlist = [item.clone(title="Todas", action="peliculas", text_blod=True,
                           viewcontent='movies', url=host + 'movies/', viewmode="movie_with_plot"),
                item.clone(title="Más Vistas", action="peliculas", text_blod=True,
                           viewcontent='movies', url=host + 'tendencias/?get=movies', viewmode="movie_with_plot"),
                item.clone(title="Más Valoradas", action="peliculas", text_blod=True,
                           viewcontent='movies', url=host + 'calificaciones/?get=movies',
                           viewmode="movie_with_plot"), item.clone(title="Géneros", action="generos", text_blod=True,
                                                                   viewcontent='movies', url=host,
                                                                   viewmode="movie_with_plot")]

    return itemlist


def menuseries(item):
    logger.info()
    itemlist = [item.clone(title="Todas", action="series", text_blod=True, extra='serie', mediatype= "tvshow",
                           viewcontent='tvshows', url=host + 'tvshows/', viewmode="movie_with_plot"),
                item.clone(title="Más Vistas", action="series", text_blod=True, extra='serie', mediatype= "tvshow",
                           viewcontent='tvshows', url=host + 'tendencias/?get=tv', viewmode="movie_with_plot"),
                item.clone(title="Mejor Valoradas", action="series", text_blod=True, extra='serie', mediatype= "tvshow",
                           viewcontent='tvshows', url=host + 'calificaciones/?get=tv', viewmode="movie_with_plot")]

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    url_next_page = ''
    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = '<div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?'  # img, title
    patron += '<div class="rating"><span class="[^"]+"></span>([^<]+).*?'  # rating
    patron += '<span class="quality">([^<]+)</span><a href="([^"]+)">.*?'  # calidad, url
    patron += '<span>([^<]+)</span>'  # year

    matches = scrapertools.find_multiple_matches(datas, patron)

    # Paginación
    if item.next_page != 'b':
        if len(matches) > 19:
            url_next_page = item.url
        matches = matches[:19]
        next_page = 'b'
    else:
        matches = matches[19:]
        next_page = 'a'
        patron_next_page = "<span class=\"current\">\d+</span><a href='([^']+)'"
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])

    for scrapedthumbnail, scrapedtitle, rating, calidad, scrapedurl, year in matches:
        if 'Proximamente' not in calidad:
            scrapedtitle = scrapedtitle.replace('Ver ', '').partition(' /')[0].partition(':')[0].replace(
                'Español Latino', '').strip()
            item.infoLabels['year'] = year
            item.infoLabels['rating'] = rating
            title = "%s [COLOR green][%s][/COLOR] [COLOR yellow][%s][/COLOR]" % (scrapedtitle, year, calidad)

            new_item = Item(channel=__channel__, action="findvideos", contentTitle=scrapedtitle,
                            infoLabels={'year': year, 'rating': rating}, thumbnail=scrapedthumbnail,
                            url=scrapedurl, next_page=next_page, quality=calidad, title=title)
            if year:
                tmdb.set_infoLabels_item(new_item, __modo_grafico__)
                itemlist.append(new_item)

    if url_next_page:
        itemlist.append(Item(channel=__channel__, action="peliculas", title=">> Página siguiente",
                             url=url_next_page, next_page=next_page, folder=True, text_blod=True))

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
            # logger.info(data)
            item.fanart = scrapertools.find_single_match(data,
                                                         "<meta property='og:image' content='([^']+)' />").replace(
                'w780', 'original')
            item.plot = scrapertools.find_single_match(data, '<div itemprop="description" class="wp-content">.*?<p>(['
                                                             '^<]+)</p>')
            item.plot = scrapertools.htmlclean(item.plot)
            item.infoLabels['director'] = scrapertools.find_single_match(data,
                                                                         '<div class="name"><a href="[^"]+">([^<]+)</a>')
            item.infoLabels['rating'] = scrapertools.find_single_match(data, '<b id="repimdb"><strong>([^<]+)</strong>')
            item.infoLabels['votes'] = scrapertools.find_single_match(data, '<b id="repimdb"><strong>['
                                                                            '^<]+</strong>\s(.*?) votos</b>')

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
    data = scrapertools.find_single_match(data, 'Genero</a><ulclass="sub-menu">(.*?)</ul></li><li id')

    patron = '<li id="[^"]+" class="menu-item.*?<a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle != 'Proximamente':
            title = "%s" % scrapedtitle
            itemlist.append(item.clone(channel=item.channel, action="peliculas", title=title,
                                       url=scrapedurl, text_color=color3, viewmode="movie_with_plot"))

            itemlist.sort(key=lambda it: it.title)

    return itemlist


def series(item):
    logger.info()
    url_next_page = ''

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # logger.info(datas)

    patron = '<div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?<a href="([^"]+)">'

    matches = scrapertools.find_multiple_matches(data, patron)

    if item.next_page != 'b':
        if len(matches) > 19:
            url_next_page = item.url
        matches = matches[:19]
        next_page = 'b'
    else:
        matches = matches[19:]
        next_page = 'a'
        patron_next_page = '<link rel="next" href="([^"]+)" />'
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.replace('Ver ',
                                            '').replace(' Online HD',
                                                        '').replace('ver ', '').replace(' Online',
                                                                                        '').replace('&#8217;', "'")
        itemlist.append(Item(channel=__channel__, title=scrapedtitle,
                        url=scrapedurl, thumbnail=scrapedthumbnail,
                        contentSerieName=scrapedtitle, show=scrapedtitle,
                        next_page=next_page, action="temporadas", contentType='tvshow'))

    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    if url_next_page:
        itemlist.append(Item(channel=__channel__, action="series", title=">> Página Siguiente", url=url_next_page,
                             next_page=next_page))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    logger.info(datas)
    patron = '<span class="title">([^<]+)<i>.*?'  # numeros de temporadas
    patron += '<img src="([^"]+)"></a></div>'  # capítulos

    matches = scrapertools.find_multiple_matches(datas, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail)
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadírselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']

        itemlist.sort(key=lambda it: it.title)

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
        # Obtenemos los datos de todos los capítulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            if i.infoLabels['title']:
                # Si el capitulo tiene nombre propio añadírselo al titulo del item
                i.title = "%sx%s %s" % (i.infoLabels['season'], i.infoLabels['episode'], i.infoLabels['title'])
            if i.infoLabels.has_key('poster_path'):
                # Si el capitulo tiene imagen propia remplazar al poster
                i.thumbnail = i.infoLabels['poster_path']

    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))

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
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
    patron = '<div id="option-(\d+)" class="[^"]+"><iframe.*?src="([^"]+)".*?</iframe>'  #
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, url in matches:
        lang = scrapertools.find_single_match(data, '<li><a class="options" href="#option-%s">.*?<img '
                                                    'src="http://pedropolis.com/wp-content/themes/dooplay/assets/img'
                                                    '/flags/(\w+)' % option)

        if "bit.ly" in url:
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")

        itemlist.append(item.clone(channel=__channel__, url=url, title=item.contentTitle, action='play', language=lang))

    itemlist = servertools.get_servers_itemlist(itemlist)

    for x in itemlist:
        if x.extra != 'directo':
            x.thumbnail = item.thumbnail
            x.title = "%s %s [COLOR yellow](%s)[/COLOR] [COLOR yellow](%s)[/COLOR]" % (
                x.language, x.title, x.server.title(), x.quality)

    return itemlist
