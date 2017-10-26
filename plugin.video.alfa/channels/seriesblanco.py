# -*- coding: utf-8 -*-

import re
import urlparse

from channels import filtertools
from channelselector import get_thumb
from core import httptools
from core import scrapertoolsV2
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import autoplay



HOST = "https://seriesblanco.com/"
IDIOMAS = {'es': 'Español', 'en': 'Inglés', 'la': 'Latino', 'vo': 'VO', 'vos': 'VOS', 'vosi': 'VOSI', 'otro': 'OVOS'}
list_idiomas = IDIOMAS.values()
list_language = ['default']
CALIDADES = ['SD', 'HDiTunes', 'Micro-HD-720p', 'Micro-HD-1080p', '1080p', '720p']
list_quality = CALIDADES

list_servers = ['streamix',
                'powvideo',
                'streamcloud',
                'openload',
                'flashx',
                'streamplay',
                'nowvideo',
                'gamovideo',
                'kingvid',
                'vidabc'
                ]


def mainlist(item):
    logger.info()

    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_buscar = get_thumb("search.png")

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(Item(channel=item.channel, title="Listado alfabético", action="series_listado_alfabetico",
                         thumbnail=thumb_series_az))
    itemlist.append(Item(channel=item.channel, title="Todas las series", action="series",
                         url=urlparse.urljoin(HOST, "listado/"), thumbnail=thumb_series))
    itemlist.append(
        Item(channel=item.channel, title="Capítulos estrenados recientemente", action="home_section",
             extra="Series Online : Capítulos estrenados recientemente",
             url=HOST, thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Series más vistas", action="series", extra="Series Más vistas",
                         url=urlparse.urljoin(HOST, "listado-visto/"), thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Últimas fichas creadas", action="series",
                         url=urlparse.urljoin(HOST, "fichas_creadas/"), thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Series por género", action="generos",
                         url=HOST, thumbnail=thumb_series))
    itemlist.append(
        Item(channel=item.channel, title="Buscar...", action="search", url=urlparse.urljoin(HOST, "finder.php"),
             thumbnail=thumb_buscar))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, CALIDADES)

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def home_section(item):
    logger.info("section = %s" % item.extra)

    pattern = "['\"]panel-title['\"]>[^/]*%s(.*?)(?:panel-title|\Z)" % item.extra
    # logger.debug("pattern = %s" % pattern)

    data = httptools.downloadpage(item.url).data
    result = re.search(pattern, data, re.MULTILINE | re.DOTALL)

    if result:
        # logger.debug("found section: {0}".format(result.group(1)))
        item.extra = 1
        return extract_series_from_data(item, result.group(1))

    logger.debug("No match")
    return []


def extract_series_from_data(item, data):
    itemlist = []
    episode_pattern = re.compile('/capitulo-([0-9]+)/')
    shows = re.findall("<a.+?href=['\"](?P<url>/serie[^'\"]+)[^<]*<img[^>]*src=['\"](?P<img>http[^'\"]+).*?"
                       "(?:alt|title)=['\"](?P<name>[^'\"]+)", data)
    for url, img, name in shows:
        try:
            name.decode('utf-8')
        except UnicodeError:
            name = unicode(name, "iso-8859-1", errors="replace").encode("utf-8")

        # logger.debug("Show found: %s -> %s (%s)" % (name, url, img))
        if not episode_pattern.search(url):
            action = "episodios"
        else:
            action = "findvideos"

        context1=[filtertools.context(item, list_idiomas, CALIDADES), autoplay.context]
        itemlist.append(item.clone(title=name, url=urlparse.urljoin(HOST, url),
                                   action=action, show=name,
                                   thumbnail=img,
                                   context=context1))

    more_pages = re.search('pagina=([0-9]+)">>>', data)
    if more_pages:
        # logger.debug("Adding next page item")
        itemlist.append(item.clone(title="Siguiente >>", extra=item.extra + 1))

    if item.extra > 1:
        # logger.debug("Adding previous page item")
        itemlist.append(item.clone(title="<< Anterior", extra=item.extra - 1))

    return itemlist


def series(item):
    logger.info()
    if not hasattr(item, 'extra') or not isinstance(item.extra, int):
        item.extra = 1

    if '?' in item.url:
        merger = '&'
    else:
        merger = '?'

    page_url = "%s%spagina=%s" % (item.url, merger, item.extra)
    logger.info("url = %s" % page_url)

    data = scrapertoolsV2.decodeHtmlentities(httptools.downloadpage(page_url).data)
    return extract_series_from_data(item, data)


def series_listado_alfabetico(item):
    logger.info()

    return [item.clone(action="series", title=letra, url=urlparse.urljoin(HOST, "listado-%s/" % letra))
            for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


def generos(item):
    logger.info()
    data = httptools.downloadpage(item.url).data

    result = re.findall("href=['\"](?P<url>/listado/[^'\"]+)['\"][^/]+/i>\s*(?P<genero>[^<]+)", data)
    return [item.clone(action="series", title=genero, url=urlparse.urljoin(item.url, url)) for url, genero in result]


def newest(categoria):
    logger.info("categoria: %s" % categoria)
    itemlist = []
    try:
        if categoria == 'series':
            itemlist = home_section(Item(extra=CAPITULOS_DE_ESTRENO_STR, url=HOST))

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist


def search(item, texto):
    logger.info("%s" % texto)
    texto = texto.replace(" ", "+")

    itemlist = []

    try:
        post = "query=%s" % texto
        data = httptools.downloadpage(item.url, post=post).data
        data = re.sub(r"\n|\r|\t|\s{2}", "", data)
        shows = re.findall("<a href=['\"](?P<url>/serie[^'\"]+)['\"].*?<img src=['\"](?P<img>[^'\"]+)['\"].*?"
                           "id=['\"]q2[1\"] name=['\"]q2['\"] value=['\"](?P<title>.*?)['\"]", data)

        for url, img, title in shows:
            itemlist.append(item.clone(title=title, url=urlparse.urljoin(HOST, url), action="episodios", show=title,
                                       thumbnail=img, context=filtertools.context(item, list_idiomas, CALIDADES)))

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return itemlist


def episodios(item):
    logger.info("%s - %s" % (item.title, item.url))

    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    fanart = scrapertoolsV2.find_single_match(data, "background-image[^'\"]+['\"]([^'\"]+)")
    plot = scrapertoolsV2.find_single_match(data, "id=['\"]profile2['\"]>\s*(.*?)\s*</div>")

    # logger.debug("fanart: %s" % fanart)
    # logger.debug("plot: %s" % plot)

    episodes = re.findall("<tr.*?href=['\"](?P<url>[^'\"]+).+?>(?P<title>.+?)</a>.*?<td>(?P<flags>.*?)</td>", data,
                          re.MULTILINE | re.DOTALL)
    for url, title, flags in episodes:
        title = re.sub("<span[^>]+>", "", title).replace("</span>", "")
        idiomas = " ".join(["[%s]" % IDIOMAS.get(language, "OVOS") for language in
                            re.findall("banderas/([^\.]+)", flags, re.MULTILINE)])
        filter_lang = idiomas.replace("[", "").replace("]", "").split(" ")
        display_title = "%s - %s %s" % (item.show, title, idiomas)
        # logger.debug("Episode found %s: %s" % (display_title, urlparse.urljoin(HOST, url)))
        itemlist.append(item.clone(title=display_title, url=urlparse.urljoin(HOST, url),
                                   action="findvideos", plot=plot, fanart=fanart, language=filter_lang))

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, CALIDADES)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios"))

    return itemlist


def parse_videos(item, type_str, data):
    video_patterns_str = [
        '<tr.+?<span>(?P<date>.+?)</span>.*?banderas/(?P<language>[^\.]+).+?href="(?P<link>[^"]+).+?servidores/'
        '(?P<server>[^\.]+).*?</td>.*?<td>.*?<span>(?P<uploader>.+?)</span>.*?<span>(?P<quality>.*?)</span>',
        '<tr.+?banderas/(?P<language>[^\.]+).+?<td[^>]*>(?P<date>.+?)</td>.+?href=[\'"](?P<link>[^\'"]+)'
        '.+?servidores/(?P<server>[^\.]+).*?</td>.*?<td[^>]*>.*?<a[^>]+>(?P<uploader>.+?)</a>.*?</td>.*?<td[^>]*>'
        '(?P<quality>.*?)</td>.*?</tr>'
    ]

    for v_pat_str in video_patterns_str:
        v_patt_iter = re.compile(v_pat_str, re.MULTILINE | re.DOTALL).finditer(data)

        itemlist = []

        for vMatch in v_patt_iter:
            v_fields = vMatch.groupdict()
            quality = v_fields.get("quality")

            # FIX para veces que añaden el idioma en los comentarios
            regex = re.compile('sub-inglés-?', re.I)
            quality = regex.sub("", quality)
            # quality = re.sub(r"sub-inglés-?", "", quality, flags=re.IGNORECASE)

            if not quality:
                quality = "SD"

            # FIX para los guiones en la calidad y no tener que añadir otra opción en la lista de calidades
            if quality.startswith("MicroHD"):
                regex = re.compile('microhd', re.I)
                quality = regex.sub("Micro-HD-", quality)
                # quality = re.sub(r"microhd", "Micro-HD-", quality, flags=re.IGNORECASE)
            server = v_fields.get("server")
            title = "%s en %s [%s] [%s] (%s: %s)" % (type_str, v_fields.get("server"),
                                                     IDIOMAS.get(v_fields.get("language"), "OVOS"), quality,
                                                     v_fields.get("uploader"), v_fields.get("date"))
            itemlist.append(
                item.clone(title=title, fulltitle=item.title, url=urlparse.urljoin(HOST, v_fields.get("link")),
                           action="play", language=IDIOMAS.get(v_fields.get("language"), "OVOS"),
                           quality=quality, server= server))

        if len(itemlist) > 0:
            return itemlist

    return []


def extract_videos_section(data):
    return re.findall("panel-title[^>]*>\s*([VvDd].+?)</div>[^<]*</div>[^<]*</div>", data, re.MULTILINE | re.DOTALL)


def findvideos(item):
    logger.info("%s = %s" % (item.show, item.url))

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    # logger.info(data)

    online = extract_videos_section(data)
    try:
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_enlaces = 2

    list_links = []

    if filtro_enlaces != 0:
        list_links.extend(parse_videos(item, "Ver", online[-2]))

    if filtro_enlaces != 1:
        list_links.extend(parse_videos(item, "Descargar", online[-1]))

    list_links = filtertools.get_links(list_links, item, list_idiomas, CALIDADES)

    for i in range(len(list_links)):
        a=list_links[i].title
        b=a.lstrip('Ver en')
        c=b.split('[')
        d=c[0].rstrip( )
        d=d.lstrip( )
        list_links[i].server=d
        if item.contentChannel=='videolibrary':
            list_links[i].contentEpisodeNumber=item.contentEpisodeNumber
            list_links[i].contentPlot=item.contentPlot
            list_links[i].contentSeason=item.contentSeason
            list_links[i].contentSerieName=item.contentSerieName
            list_links[i].contentTitle=item.contentTitle
            list_links[i].contentType=item.contentType
            list_links[i].episode_id=item.episode_id
            list_links[i].hasContentDetails=item.hasContentDetails
            list_links[i].infoLabels=item.infoLabels
            list_links[i].thumbnail=item.thumbnail

    autoplay.start(list_links, item)

    return list_links


def play(item):
    logger.info("%s - %s = %s" % (item.show, item.title, item.url))
    if item.url.startswith(HOST):
        data = httptools.downloadpage(item.url).data

        ajax_link = re.findall("loadEnlace\((\d+),(\d+),(\d+),(\d+)\)", data)
        ajax_data = ""
        for serie, temp, cap, linkID in ajax_link:
            # logger.debug(
            #     "Ajax link request: Serie = %s - Temp = %s - Cap = %s - Link = %s" % (serie, temp, cap, linkID))
            ajax_data += httptools.downloadpage(
                HOST + '/ajax/load_enlace.php?serie=' + serie + '&temp=' + temp + '&cap=' + cap + '&id=' + linkID).data

        if ajax_data:
            data = ajax_data

        patron = "window.location.href\s*=\s*[\"']([^\"']+)'"
        url = scrapertoolsV2.find_single_match(data, patron)

    else:
        url = item.url

    itemlist = servertools.find_video_items(data=url)

    titulo = scrapertoolsV2.find_single_match(item.fulltitle, "^(.*?)\s\[.+?$")
    if titulo:
        titulo += " [%s]" % item.language

    for videoitem in itemlist:
        if item.contentChannel=='videolibrary':
            videoitem.contentEpisodeNumber=item.contentEpisodeNumber
            videoitem.contentPlot=item.contentPlot
            videoitem.contentSeason=item.contentSeason
            videoitem.contentSerieName=item.contentSerieName
            videoitem.contentTitle=item.contentTitle
            videoitem.contentType=item.contentType
            videoitem.episode_id=item.episode_id
            videoitem.hasContentDetails=item.hasContentDetails
            videoitem.infoLabels=item.infoLabels
            videoitem.thumbnail=item.thumbnail
        if titulo:
            videoitem.title = titulo
        else:
            videoitem.title = item.title
        videoitem.channel = item.channel

    return itemlist
