# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
from platformcode import config, logger
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb

host = "http://www.pelisplanet.com/"

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

__channel__ = "pelisplanet"
parameters = channeltools.get_channel_parameters('pelisplanet')
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
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

def mainlist(item):
    logger.info()
    itemlist = []
    item.url = host
    item.text_color = color1
    item.fanart = fanart_host
    thumbnail = "https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/%s.png"

    itemlist.append(item.clone(title="Novedades", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'novedades',
                               viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Estrenos", action="peliculas", text_blod=True,
                               url=host + 'genero/estrenos/', thumbnail=thumbnail % 'estrenos'))

    itemlist.append(item.clone(title="Géneros", action="generos", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'generos',
                               viewmode="movie_with_plot", url=host + 'generos/'))

    itemlist.append(Item(channel=item.channel, title="Filtrar por Idiomas",
                         fanart=fanart_host, folder=False, text_color=color3,
                         text_blod=True, thumbnail=thumbnail % 'idiomas'))

    itemlist.append(item.clone(title="Castellano", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'castellano',
                               viewmode="movie_with_plot", url=host + 'idioma/castellano/'))

    itemlist.append(item.clone(title="Latino", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'latino',
                               viewmode="movie_with_plot", url=host + 'idioma/latino/'))

    itemlist.append(item.clone(title="Buscar por Título o Actor", action="search", text_blod=True,
                               thumbnail=thumbnail % 'busqueda', url=host))
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
    patron = '<div class="img">.*?<a href="(?P<url>[^"]+)" title="(?P<name>[^"]+)".*?'
    patron += '<img.+?src="(?P<img>[^"]+)".*?\(([^\)]+)\)"> </a></div>.*?'
    patron += 'Ver\s(.*?)\sOnline'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, name, img, year, scrapedinfo in matches:
        contentTitle = scrapertools.decodeHtmlentities(scrapedinfo.strip())
        plot = item.plot
        itemlist.append(item.clone(title=name, url=url, contentTitle=contentTitle,
                                   plot=plot, action="findvideos", infoLabels={"year": year},
                                   thumbnail=img, text_color=color3))

    paginacion = scrapertools.find_single_match(
        data, '<a class="page larger" href="([^"]+)">\d+</a>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=paginacion,
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    tmdb.set_infoLabels(itemlist)

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            item.fanart = scrapertools.find_single_match(
                data, 'meta property="og:image" content="([^"]+)" \/>')
            item.plot = scrapertools.find_single_match(data,
                                                       'Castellano</h3>\s*<p>(.+?)<strong>')
            item.plot = scrapertools.htmlclean(item.plot)

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + "genero/animacion-e-infantil/"
        else:
            return []

        itemlist = peliculas(item)
        if itemlist[-1].title == "» Siguiente »":
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
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    patron_todas = '<div class="home-movies">(.*?)<footer>'
    data = scrapertools.find_single_match(data, patron_todas)
    patron = 'col-sm-5"><a href="(?P<scrapedurl>[^"]+)".+?'
    patron += 'browse-movie-link-qd.*?>(?P<calidad>[^>]+)</.+?'
    patron += '<p>(?P<year>[^>]+)</p>.+?'
    patron += 'title one-line">(?P<scrapedtitle>[^>]+)</h2>.+?'
    patron += 'img-responsive" src="(?P<scrapedthumbnail>[^"]+)".*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, calidad, year, scrapedtitle, scrapedthumbnail in matches:
        datas = httptools.downloadpage(scrapedurl).data
        datas = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", datas)
        #logger.info(datas)
        if '/ ' in scrapedtitle:
            scrapedtitle = scrapedtitle.partition('/ ')[2]
        contentTitle = scrapertools.find_single_match(datas, '<em class="pull-left">Titulo original: </em>([^<]+)</p>')
        contentTitle = scrapertools.decodeHtmlentities(contentTitle.strip())
        rating = scrapertools.find_single_match(datas, 'alt="Puntaje MPA IMDb" /></a><span>([^<]+)</span>')
        director = scrapertools.find_single_match(datas, '<div class="list-cast-info tableCell"><a href="[^"]+" rel="tag">([^<]+)</a></div>')
        title = "%s [COLOR yellow][%s][/COLOR]" % (scrapedtitle.strip(), calidad.upper())

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, plot='',
                             url=scrapedurl, contentQuality=calidad, thumbnail=scrapedthumbnail,
                             contentTitle=contentTitle, infoLabels={"year": year, 'rating': rating, 'director': director},
                             text_color=color3))

    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    paginacion = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')
    if paginacion:

        itemlist.append(Item(channel=item.channel, action="peliculas",
                                   title="» Siguiente »", url=paginacion, plot="Página Siguiente",
                                   thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            item.fanart = scrapertools.find_single_match(data, 'meta property="og:image" content="([^"]+)" \/>')
            item.plot = scrapertools.find_single_match(data, 'Castellano</h3>\s*<p>(.+?)<strong>')
            item.plot = scrapertools.htmlclean(item.plot)

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
    patron = '<div class="todos">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle,
                             url=scrapedurl, text_color=color3, thumbnail=scrapedthumbnail,
                             plot="", viewmode="movie_with_plot", folder=True))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    datas = httptools.downloadpage(item.url).data
    datas = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", datas)
    # logger.info(data)
    patron = '<a style="cursor:pointer; cursor: hand;" rel="([^"]+)".*?'
    patron += 'clearfix colores title_calidad">.*?<span>([^<]+)</span></a>'

    matches = re.compile(patron, re.DOTALL).findall(datas)

    for scrapedurl, servidores, in matches:
        if 'youtube' in scrapedurl:
            video_urls = []
            doc_id = scrapertools.find_single_match(scrapedurl, "docid=(\w+)")
            doc_url = "http://docs.google.com/get_video_info?docid=%s" % doc_id
            response = httptools.downloadpage(doc_url, cookies=False)
            cookies = ""
            cookie = response.headers["set-cookie"].split("HttpOnly, ")
            for c in cookie:
                cookies += c.split(";", 1)[0] + "; "
            data = response.data.decode('unicode-escape')
            data = urllib.unquote_plus(urllib.unquote_plus(data))
            headers_string = "|Cookie=" + cookies
            url_streams = scrapertools.find_single_match(data, 'url_encoded_fmt_stream_map=(.*)')
            streams = scrapertools.find_multiple_matches(url_streams,
                                             'itag=(\d+)&url=(.*?)(?:;.*?quality=.*?(?:,|&)|&quality=.*?(?:,|&))')
            itags = {'18':'360p', '22':'720p', '34':'360p', '35':'480p', '37':'1080p', '43':'360p', '59':'480p'}
            for itag, video_url in streams:
                video_url += headers_string
                video_urls.append([video_url, itags[itag]])

            for video_item in video_urls:
                calidad = video_item[1]
                title = '%s [COLOR green](%s)[/COLOR] [COLOR green]([/COLOR][COLOR black]You[/COLOR][COLOR red]tube[/COLOR][COLOR green])[/COLOR]'%(item.contentTitle, calidad)
                url = video_item[0]

                itemlist.append(
                    item.clone(channel=item.channel,
                         action='play',
                         title=title,
                         url= url,
                         thumbnail=item.thumbnail,
                         plot=item.plot,
                         fanart=item.fanart,
                         contentTitle=item.contentTitle,
                         server='directo',
                         context = item.context
                         ))
                itemlist.sort(key=lambda it: it.title, reverse=True)
        if 'pelispp.com' or 'ultrapelis' in scrapedurl:
            data = httptools.downloadpage(scrapedurl, headers=headers).data
            patronr = 'file: "([^"]+)",label:"([^"]+)",type'
            matchesr = re.compile(patronr, re.DOTALL).findall(data)
            for scrapedurl, label in matchesr:
                url = scrapedurl.replace('\\', '')
                language = 'latino'
                quality = label.decode('cp1252').encode('utf8')
                title = item.contentTitle + ' (' + str(label) + ') ([COLOR blue]G[/COLOR][COLOR red]o[/COLOR][COLOR yellow]o[/COLOR][COLOR blue]g[/COLOR][COLOR green]l[/COLOR][COLOR red]e[/COLOR])'
                thumbnail = item.thumbnail
                fanart = item.fanart
                itemlist.append(item.clone(action="play", title=title, url=url, server='directo',
                                           thumbnail=thumbnail, fanart=fanart, extra='directo',
                                           quality=quality, language=language,))
                itemlist.sort(key=lambda it: it.title, reverse=True)

        # if 'youtube' not in scrapedurl:
        servidores.lower()
        if 'youtube' not in scrapedurl and 'pelispp.com' not in scrapedurl and 'streamplus' not in servidores:
            quality = scrapertools.find_single_match(
                datas, '<p class="hidden-xs hidden-sm">.*?class="magnet-download">([^<]+)p</a>')
            title = "[COLOR green]%s[/COLOR] [COLOR yellow][%s][/COLOR] [COLOR yellow][%s][/COLOR]" % (
                item.contentTitle, quality.upper(), servidores.capitalize())
            url = scrapedurl.replace('\\', '')
            thumbnail = item.thumbnail
            server = servertools.get_server_from_url(url)

            itemlist.append(item.clone(action='play', title=title, url=url, quality=quality,
                                       server=server, text_color=color3, thumbnail=thumbnail))

    for videoitem in itemlist:
        videoitem.infoLabels = item.infoLabels
        videoitem.channel = item.channel
        videoitem.action = 'play'
        videoitem.fulltitle = item.title

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library",
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/libreria.png',
                             extra="findvideos", contentTitle=item.contentTitle))

    return itemlist
