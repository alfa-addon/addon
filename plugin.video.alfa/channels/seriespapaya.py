# -*- coding: utf-8 -*-

import re
import string
import urllib
import urlparse

from channels import filtertools
from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from channels import autoplay
from core.item import Item
from platformcode import config, logger

HOST = "http://www.seriespapaya.com"

IDIOMAS = {'es': 'Español', 'lat': 'Latino', 'in': 'Inglés', 'ca': 'Catalán', 'sub': 'VOSE', 'Español Latino':'lat',
           'Español Castellano':'es', 'Sub Español':'VOSE'}
list_idiomas = IDIOMAS.values()
list_quality = ['360p', '480p', '720p HD', '1080p HD', 'default']
list_servers = ['powvideo', 'streamplay', 'filebebo', 'flashx', 'gamovideo', 'nowvideo', 'openload', 'streamango',
                'streamcloud', 'vidzi', 'clipwatching', ]


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_buscar = get_thumb("search.png")
    itemlist = []
    itemlist.append(
        Item(action="listado_alfabetico", title="Listado Alfabetico", channel=item.channel, thumbnail=thumb_series_az))
    itemlist.append(
        Item(action="novedades", title="Capítulos de estreno", channel=item.channel, thumbnail=thumb_series))
    itemlist.append(Item(action="search", title="Buscar", channel=item.channel, thumbnail=thumb_buscar))
    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def listado_alfabetico(item):
    logger.info()
    itemlist = [item.clone(action="series_por_letra", title="0-9")]
    for letra in string.ascii_uppercase:
        itemlist.append(item.clone(action="series_por_letra", title=letra))
    return itemlist


def series_por_letra(item):
    logger.info("letra: %s" % item.title)
    item.letter = item.title.lower()
    item.extra = 0
    return series_por_letra_y_grupo(item)


def series_por_letra_y_grupo(item):
    logger.info("letra: %s - grupo: %s" % (item.letter, item.extra))
    itemlist = []
    url = urlparse.urljoin(HOST, "autoload_process.php")
    post_request = {
        "group_no": item.extra,
        "letra": item.letter.lower()
    }
    data = httptools.downloadpage(url, post=urllib.urlencode(post_request)).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = '<div class=list_imagen><img src=(.*?) \/>.*?<div class=list_titulo><a href=(.*?) style=.*?inherit;>(.*?)'
    patron +='<.*?justify>(.*?)<.*?Año:<\/b>.*?(\d{4})<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for img, url, name, plot, year in matches:
        new_item= Item(
            channel = item.channel,
            action="episodios",
            title=name,
            show=name,
            url=urlparse.urljoin(HOST, url),
            thumbnail=urlparse.urljoin(HOST, img),
            context=filtertools.context(item, list_idiomas, list_quality),
            plot = plot,
            infoLabels={'year':year}
        )
        if year:
           tmdb.set_infoLabels_item(new_item)
        itemlist.append(new_item)
    if len(matches) == 8:
        itemlist.append(item.clone(title="Siguiente >>", action="series_por_letra_y_grupo", extra=item.extra + 1))
    if item.extra > 0:
        itemlist.append(item.clone(title="<< Anterior", action="series_por_letra_y_grupo", extra=item.extra - 1))
    return itemlist


def novedades(item):
    logger.info()
    data = httptools.downloadpage(HOST).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'sidebarestdiv><a title=(.*?\d+X\d+) (.*?) href=(.*?)>.*?src=(.*?)>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for title, language,url, img in matches:
        language = IDIOMAS[language]
        itemlist.append(item.clone(action="findvideos", title=title, url=urlparse.urljoin(HOST, url), thumbnail=img,
                                   language=language))
    return itemlist


def newest(categoria):
    logger.info("categoria: %s" % categoria)
    if categoria != 'series':
        return []
    return novedades(Item())


def episodios(item):
    logger.info("url: %s" % item.url)
    infoLabels = {}
    data = httptools.downloadpage(item.url).data
    episodes = re.findall('visco.*?href="(?P<url>[^"]+).+?nbsp; (?P<title>.*?)</a>.+?ucapaudio.?>(?P<langs>.*?)</div>',
                          data, re.MULTILINE | re.DOTALL)
    itemlist = []
    for url, title, langs in episodes:
        s_e = scrapertools.get_season_and_episode(title)
        infoLabels = item.infoLabels
        infoLabels["season"] = s_e.split("x")[0]
        infoLabels["episode"] = s_e.split("x")[1]
        languages = " ".join(
            ["[%s]" % IDIOMAS.get(lang, lang) for lang in re.findall('images/s-([^\.]+)', langs)])
        filter_lang = languages.replace("[", "").replace("]", "").split(" ")
        itemlist.append(item.clone(action="findvideos",
                                   infoLabels = infoLabels,
                                   language=filter_lang,
                                   title="%s %s %s" % (item.title, title, languages),
                                   url=urlparse.urljoin(HOST, url)
                                   ))
    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    tmdb.set_infoLabels(itemlist, True)
    # Opción "Añadir esta serie a la videoteca de KODI"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios"))
    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    itemlist = []
    infoLabels = ()
    data = httptools.downloadpage(urlparse.urljoin(HOST, "/buscar.php?term=%s" % texto)).data
    data_dict = jsontools.load(data)
    try:
        tvshows = data_dict["myData"]
    except:
        return []
    for show in tvshows:
        itemlist.append(item.clone(action="episodios",
                       context=filtertools.context(item, list_idiomas, list_quality),
                       contentSerieName=show["titulo"],
                       thumbnail=urlparse.urljoin(HOST, show["img"]),
                       title=show["titulo"],
                       url=urlparse.urljoin(HOST, show["urla"])
                       ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def findvideos(item):
    logger.info("url: %s" % item.url)
    data = httptools.downloadpage(item.url).data
    expr = 'mtos' + '.+?' + \
           '<div.+?images/(?P<lang>[^\.]+)' + '.+?' + \
           '<div[^>]+>\s+(?P<date>[^\s<]+)' + '.+?' + \
           '<div.+?img.+?>\s*(?P<server>.+?)</div>' + '.+?' + \
           '<div.+?href="(?P<url>[^"]+).+?images/(?P<type>[^\.]+)' + '.+?' + \
           '<div[^>]+>\s*(?P<quality>.*?)</div>' + '.+?' + \
           '<div.+?<a.+?>(?P<uploader>.*?)</a>'
    links = re.findall(expr, data, re.MULTILINE | re.DOTALL)
    itemlist = []
    try:
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_enlaces = 2
    typeListStr = ["Descargar", "Ver"]
    for lang, date, server, url, linkType, quality, uploader in links:
        linkTypeNum = 0 if linkType == "descargar" else 1
        if filtro_enlaces != 2 and filtro_enlaces != linkTypeNum:
            continue
        if server ==  "Thevideo": server = "thevideome"
        if server ==  "1fichier": server = "onefichier"
        if server ==  "Uploaded": server = "uploadedto"
        itemlist.append(item.clone(
                action="play",
                title="{linkType} en {server} [{lang}] [{quality}] ({uploader}: {date})".format(
                    linkType=typeListStr[linkTypeNum],
                    lang=IDIOMAS.get(lang, lang),
                    date=date,
                    server=server.rstrip().capitalize(),
                    quality=quality,
                    uploader=uploader),
                server=server.lower().rstrip(),
                url=urlparse.urljoin(HOST, url),
                language=IDIOMAS.get(lang,lang),
                quality=quality
            )
        )
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


def play(item):
    logger.info("play: %s" % item.url)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    item.url = scrapertools.find_single_match(data, "location.href='([^']+)")
    item.server = ""
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist[0].thumbnail=item.contentThumbnail
    return itemlist
