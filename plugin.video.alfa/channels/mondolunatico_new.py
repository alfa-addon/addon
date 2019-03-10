# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale mondolunatico_new
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------
import re
import urlparse

from core import httptools, scrapertools, servertools
from core.item import Item
from core.tmdb import infoIca
from platformcode import logger, config

host = "http://mondolunatico.org"


def mainlist(item):
    logger.info("kod.istreaming mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Ultimi Film Inseriti[/COLOR]",
                     action="peliculas",
                     url="%s/stream/movies/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Film Per Categoria[/COLOR]",
                     action="categorias",
                     url="%s/stream/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def categorias(item):
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.get_match(data, '<h2>Film Per Genere</h2><ul class="genres scrolling">(.*?)</ul>')

    # Estrae i contenuti 
    patron = '<li[^>]+><a href="([^"]+)"[^>]+>([^<]+)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    return itemlist


def search(item, texto):
    logger.info("[mondolunatico.py] " + item.url + " search " + texto)
    item.url = host + "/stream?s=" + texto
    try:
        if item.extra == "movie":
            return pelis_movie_src(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def pelis_movie_src(item):
    logger.info("kod.mondolunatico_new peliculas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="thumbnail animation-2">\s*<a href="([^"]+)">\s*<img src="([^"]+)" alt="(.*?)" />'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedplot = ""
    for scrapedurl, scrapedthumbnail, scrapedtitle, in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True), tipo='movie'))

    return itemlist


def peliculas(item):
    logger.info("kod.mondolunatico_new peliculas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '</span><a href="([^"]+)">(.*?)</a></h3>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="findvideos",
                 contentType="movie",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True), tipo='movie'))

    # Paginazione 
    patronvideos = '<span class="current">[^<]+</span><a href=\'(.*?)\''
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def findvideos(item):
    logger.info("kod.mondolunatico findvideos")

    # Carica la pagina
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = 'src="([^"]+)" frameborder="0"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl in matches:
        if "dir?" in scrapedurl:
            data += httptools.downloadpage(scrapedurl).url + '\n'
        else:
            data += httptools.downloadpage(scrapedurl).data

    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title).capitalize()
        videoitem.title = "".join(["[%s] " % color(server, 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"
