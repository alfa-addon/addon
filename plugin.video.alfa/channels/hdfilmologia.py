# -*- coding: utf-8 -*-
# -*- Channel HDFilmologia -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import sys
import urllib
import urlparse
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "hdfilmologia"

host = "https://hdfilmologia.com/"

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


IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'openload', 'streamcherry']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(item.clone(title="Últimas Agregadas", action="movies", thumbnail=get_thumb('last', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'index.php?do=lastnews', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Estrenos", action="movies", thumbnail=get_thumb('premieres', auto=True),
                               text_blod=True, page=0, viewcontent='movies', url=host + 'estrenos',
                               viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Más Vistas", action="movies", thumbnail=get_thumb('more watched', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host + 'mas-vistas/', viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Películas Por País", action="countriesYears", thumbnail=get_thumb('country',
                                                                                                        auto=True), text_blod=True, page=0, viewcontent='movies',
                               url=host, viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Películas Por Año", action="countriesYears", thumbnail=get_thumb('year', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host, viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Géneros", action="genres", thumbnail=get_thumb('genres', auto=True),
                               text_blod=True, page=0, viewcontent='movies',
                               url=host, viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
                               text_blod=True, url=host, page=0))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?do=search&mode=advanced&subaction=search&story={0}".format(texto))
    # 'https://hdfilmologia.com/?do=search&mode=advanced&subaction=search&story=la+sombra'

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
    patron = '<a class="sres-wrap clearfix" href="([^"]+)">'  # url
    patron += '<div class="sres-img"><img src="/([^"]+)" alt="([^"]+)" />.*?'   # img, title
    patron += '<div class="sres-desc">(.*?)</div>'                              # plot

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, plot in matches:

        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, contentTitle=scrapedtitle,
                                   action="findvideos", text_color=color3, page=0, plot=plot,
                                   thumbnail=host + scrapedthumbnail))

    pagination = scrapertools.find_single_match(data, 'class="pnext"><a href="([^"]+)">')

    if pagination:
        itemlist.append(Item(channel=__channel__, action="sub_search",
                             title="» Siguiente »", url=pagination))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def movies(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    patron = '<div class="kino-item ignore-select">.*?<a href="([^"]+)" class="kino-h"><h2>([^<]+)</h2>.*?'  # url, title
    patron += '<img src="([^"]+)".*?'                           # img
    patron += '<div class="k-meta qual-mark">([^<]+)</div>.*?'  # quality
    patron += '<strong>Año:</strong></div>([^<]+)</li>'         # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle, scrapedthumbnail, quality, year in matches[item.page:item.page + 25]:
        scrapedthumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        title = "%s [COLOR yellow][%s][/COLOR]" % (scrapedtitle, quality)

        itemlist.append(Item(channel=__channel__, action="findvideos", text_color=color3,
                             url=scrapedurl, infoLabels={'year': year.strip()},
                             contentTitle=scrapedtitle, thumbnail=scrapedthumbnail,
                             title=title, context="buscar_trailer"))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 25 < len(matches):
        itemlist.append(item.clone(page=item.page + 25,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(
            data, 'class="pnext"><a href="([^"]+)">')

        if next_page:
            itemlist.append(item.clone(url=next_page, page=0,
                                       title="» Siguiente »", text_color=color3))

    return itemlist


def genres(item):
    logger.info()
    itemlist = []

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="myli"><a href="/([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        itemlist.append(item.clone(channel=__channel__, action="movies", title=scrapedtitle,
                                   url=host + scrapedurl, text_color=color3, viewmode="movie_with_plot"))

    return itemlist


def countriesYears(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)

    if item.title == "Películas Por País":
        patron_todas = 'Por País</option>(.*?)</option></select>'
    else:
        patron_todas = 'Por Año</option>(.*?)<option value="/">Peliculas'

    data = scrapertools.find_single_match(data, patron_todas)
    patron = '<option value="/([^"]+)">([^<]+)</option>'  # url, title
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle in matches:

        itemlist.append(item.clone(title=scrapedtitle, url=host + scrapedurl, action="movies"))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)

    patron = '(\w+)src\d+="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for lang, url in matches:

        server = servertools.get_server_from_url(url)
        if 'dropbox' in url:
            server = 'dropbox'
        if '/drive/' in url:
            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
            server = 'gdrive'

        if 'ultrapeliculashd' in url:
            data = httptools.downloadpage(url).data
            # logger.info(data)
            patron = "\|s\|(\w+)\|"
            matches = re.compile(patron, re.DOTALL).findall(data)
            for key in matches:
                url = 'https://www.dropbox.com/s/%s?dl=1' % (key)
                server = 'dropbox'
        languages = {'l': '[COLOR cornflowerblue](LAT)[/COLOR]',
                     'e': '[COLOR green](CAST)[/COLOR]',
                     's': '[COLOR red](VOS)[/COLOR]'}
        if lang in languages:
            lang = languages[lang]

        title = "Ver en: [COLOR yellow](%s)[/COLOR] [COLOR yellowgreen]%s[/COLOR]" % (server.title(), lang)
        if 'youtube' not in server:

            itemlist.append(item.clone(action='play', url=url, title=title, language=lang,
                                       text_color=color3))

    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist.sort(key=lambda it: it.language, reverse=False)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=thumbnail_host, contentTitle=item.contentTitle))

    return itemlist
