# -*- coding: utf-8 -*-

import re
import urlparse
from os import path

from channels import renumbertools
from core import filetools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

CHANNEL_HOST = "http://animeflv.me/"
CHANNEL_DEFAULT_HEADERS = [
    ["User-Agent", "Mozilla/5.0"],
    ["Accept-Encoding", "gzip, deflate"],
    ["Referer", CHANNEL_HOST]
]

REGEX_NEXT_PAGE = r"class='current'>\d+?</li><li><a href=\"([^']+?)\""
REGEX_TITLE = r'(?:bigChar_a" href=.+?>)(.+?)(?:</a>)'
REGEX_THUMB = r'src="(http://media.animeflv\.co/uploads/thumbs/[^"]+?)"'
REGEX_PLOT = r'<span class="info">Línea de historia:</span><p><span>(.*?)</span>'
REGEX_URL = r'href="(http://animeflv\.co/Anime/[^"]+)">'
REGEX_SERIE = r'%s.+?%s([^<]+?)</a><p>(.+?)</p>' % (REGEX_THUMB, REGEX_URL)
REGEX_EPISODE = r'href="(http://animeflv\.co/Ver/[^"]+?)">(?:<span.+?</script>)?(.+?)</a></td><td>(\d+/\d+/\d+)</td></tr>'
REGEX_GENERO = r'<a href="(http://animeflv\.co/genero/[^\/]+/)">([^<]+)</a>'


def get_url_contents(url):
    html = httptools.downloadpage(url, headers=CHANNEL_DEFAULT_HEADERS).data
    # Elimina los espacios antes y despues de aperturas y cierres de etiquetas
    html = re.sub(r'>\s+<', '><', html)
    html = re.sub(r'>\s+', '>', html)
    html = re.sub(r'\s+<', '<', html)

    return html


def get_cookie_value():
    """
        Obtiene las cookies de cloudflare
    """

    cookie_file = path.join(config.get_data_path(), 'cookies.dat')
    cookie_data = filetools.read(cookie_file)

    cfduid = scrapertools.find_single_match(
        cookie_data, r"animeflv.*?__cfduid\s+([A-Za-z0-9\+\=]+)")
    cfduid = "__cfduid=" + cfduid + ";"
    cf_clearance = scrapertools.find_single_match(
        cookie_data, r"animeflv.*?cf_clearance\s+([A-Za-z0-9\+\=\-]+)")
    cf_clearance = " cf_clearance=" + cf_clearance
    cookies_value = cfduid + cf_clearance

    return cookies_value


header_string = "|User-Agent=Mozilla/5.0&Referer=http://animeflv.co&Cookie=" + \
                get_cookie_value()

def __find_next_page(html):
    """
        Busca el enlace a la pagina siguiente
    """

    return scrapertools.find_single_match(html, REGEX_NEXT_PAGE)


def __extract_info_from_serie(html):
    title = scrapertools.find_single_match(html, REGEX_TITLE)
    title = clean_title(title)
    url = scrapertools.find_single_match(html, REGEX_URL)
    thumbnail = scrapertools.find_single_match(
        html, REGEX_THUMB) + header_string
    plot = scrapertools.find_single_match(html, REGEX_PLOT)

    return [title, url, thumbnail, plot]


def __sort_by_quality(items):
    """
        Ordena los items por calidad en orden decreciente
    """

    def func(item):
        return int(scrapertools.find_single_match(item.title, r'\[(.+?)\]'))

    return sorted(items, key=func, reverse=True)


def clean_title(title):
    """
        Elimina el año del nombre de las series o peliculas
    """
    year_pattern = r'\([\d -]+?\)'

    return re.sub(year_pattern, '', title).strip()


def __find_series(html):
    """
        Busca series en un listado, ejemplo: resultados de busqueda, categorias, etc
    """
    series = []

    # Limitamos la busqueda al listado de series
    list_start = html.find('<table class="listing">')
    list_end = html.find('</table>', list_start)

    list_html = html[list_start:list_end]

    for serie in re.finditer(REGEX_SERIE, list_html, re.S):
        thumbnail, url, title, plot = serie.groups()
        title = clean_title(title)
        thumbnail = thumbnail + header_string
        plot = scrapertools.htmlclean(plot)

        series.append([title, url, thumbnail, plot])

    return series


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="letras",
                         title="Por orden alfabético"))
    itemlist.append(Item(channel=item.channel, action="generos", title="Por géneros",
                         url=urlparse.urljoin(CHANNEL_HOST, "ListadeAnime")))
    itemlist.append(Item(channel=item.channel, action="series", title="Por popularidad",
                         url=urlparse.urljoin(CHANNEL_HOST, "/ListadeAnime/MasVisto")))
    itemlist.append(Item(channel=item.channel, action="series", title="Novedades",
                         url=urlparse.urljoin(CHANNEL_HOST, "ListadeAnime/Nuevo")))
    itemlist.append(Item(channel=item.channel, action="series", title="Últimos",
                         url=urlparse.urljoin(CHANNEL_HOST, "ListadeAnime/LatestUpdate")))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         url=urlparse.urljoin(CHANNEL_HOST, "Buscar?s=")))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def letras(item):
    logger.info()

    base_url = 'http://animeflv.co/ListadeAnime?c='

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="series", title="#", url=base_url + "#"))

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        logger.debug("title=[%s], url=[%s], thumbnail=[]" % (letter, base_url + letter))

        itemlist.append(Item(channel=item.channel, action="series", title=letter, url=base_url + letter))

    return itemlist


def generos(item):
    logger.info()

    itemlist = []

    html = get_url_contents(item.url)

    list_genre = re.findall(REGEX_GENERO, html)

    for url, genero in list_genre:
        logger.debug("title=[%s], url=[%s], thumbnail=[]" % (genero, url))

        itemlist.append(Item(channel=item.channel, action="series", title=genero, url=url))

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "%20")
    item.url = "%s%s" % (item.url, texto)

    html = get_url_contents(item.url)

    try:
        # Se encontro un solo resultado y se redicciono a la página de la serie
        if html.find('<title>Ver') >= 0:
            show_list = [__extract_info_from_serie(html)]
        # Se obtuvo una lista de resultados
        else:
            show_list = __find_series(html)

        items = []
        for show in show_list:
            title, url, thumbnail, plot = show

            logger.debug("title=[%s], url=[%s], thumbnail=[%s]" % (title, url, thumbnail))

            items.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                              plot=plot, show=title, viewmode="movies_with_plot", context=renumbertools.context(item)))
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return items


def series(item):
    logger.info()

    page_html = get_url_contents(item.url)

    show_list = __find_series(page_html)

    items = []
    for show in show_list:
        title, url, thumbnail, plot = show

        logger.debug("title=[%s], url=[%s], thumbnail=[%s]" % (title, url, thumbnail))

        items.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                          plot=plot, show=title, viewmode="movies_with_plot", context=renumbertools.context(item)))

    url_next_page = __find_next_page(page_html)

    if url_next_page:
        items.append(Item(channel=item.channel, action="series", title=">> Página Siguiente", url=url_next_page))

    return items


def episodios(item):
    logger.info()

    itemlist = []

    html_serie = get_url_contents(item.url)

    info_serie = __extract_info_from_serie(html_serie)
    if info_serie[3]:
        plot = info_serie[3]
    else:
        plot = ''

    episodes = re.findall(REGEX_EPISODE, html_serie, re.DOTALL)

    es_pelicula = False
    for url, title, date in episodes:
        episode = scrapertools.find_single_match(title, r'Episodio (\d+)')

        # El enlace pertenece a un episodio
        if episode:
            season = 1
            episode = int(episode)
            season, episode = renumbertools.numbered_for_tratk(
                item.channel, item.show, season, episode)

            title = "%sx%s %s (%s)" % (season, str(episode).zfill(2), "Episodio %s" % episode, date)
        # El enlace pertenece a una pelicula
        else:
            title = "%s (%s)" % (title, date)
            item.url = url
            es_pelicula = True

        logger.debug("title=[%s], url=[%s], thumbnail=[%s]" % (title, url, item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=item.thumbnail,
                             plot=plot, show=item.show, fulltitle="%s %s" % (item.show, title)))

    # El sistema soporta la videoteca y se encontro por lo menos un episodio
    # o pelicula
    if config.get_videolibrary_support() and len(itemlist) > 0:
        if es_pelicula:
            item_title = "Añadir película a la videoteca"
            item_action = "add_pelicula_to_library"
            item_extra = ""
        else:
            item_title = "Añadir serie a la videoteca"
            item_action = "add_serie_to_library"
            item_extra = "episodios"

        itemlist.append(Item(channel=item.channel, title=item_title, url=item.url,
                             action=item_action, extra=item_extra, show=item.show))

        if not es_pelicula:
            itemlist.append(Item(channel=item.channel, title="Descargar todos los episodios",
                                 url=item.url, action="download_all_episodes", extra="episodios",
                                 show=item.show))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    encontrados = []
    page_html = get_url_contents(item.url)
    regex_api = r'http://player\.animeflv\.co/[^\"]+'
    iframe_url = scrapertools.find_single_match(page_html, regex_api)

    iframe_html = get_url_contents(iframe_url)
    itemlist.extend(servertools.find_video_items(data=iframe_html))
    
    qualities = ["360", "480", "720", "1080"]
    for videoitem in itemlist:
        if videoitem.url in encontrados:
            continue
        encontrados.append(videoitem.url)
        videoitem.fulltitle = item.fulltitle
        videoitem.title = "%s en calidad [%s]" % (videoitem.server, qualities[1])
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail

    regex_video_list = r'var part = \[([^\]]+)'

    videos_html = scrapertools.find_single_match(iframe_html, regex_video_list)
    videos = re.findall('"([^"]+)"', videos_html, re.DOTALL)
    for quality_id, video_url in enumerate(videos):
        if video_url in encontrados:
            continue
        encontrados.append(video_url)
        itemlist.append(Item(channel=item.channel, action="play", url=video_url, show=re.escape(item.show),
                             title="Ver en calidad [%s]" % (qualities[quality_id]), plot=item.plot,
                             fulltitle=item.title))
    return __sort_by_quality(itemlist)
