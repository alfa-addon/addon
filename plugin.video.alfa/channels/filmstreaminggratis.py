# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per filmstreaminggratis
# https://alfa-addon.com/categories/kod-addon.50/
# ----------------------------------------------------------

import re

from channels import autoplay
from channels import filtertools
from core import scrapertools, servertools, httptools
from core.item import Item
from core.tmdb import infoIca
from platformcode import logger, config

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'thevideome', 'okru', 'mailru']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmstreaminggratis')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmstreaminggratis')

host = "https://www.filmstreaminggratis.org"


def mainlist(item):
    logger.info("kod.filmstreaminggratis mainlist")
    logger.info("[FilmStreamingGratis.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     action="ultimifilm",
                     title=color("Ultimi Film", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title=color("Cerca film ...", "yellow"),
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist



def newest(categoria):
    logger.info("[FilmStreamingGratis.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host
            item.action = "ultimifilm"
            itemlist = ultimifilm(item)

            if itemlist[-1].action == "ultimifilm":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist



def search(item, texto):
    logger.info("[FilmStreamingGratis.py]==> search")
    item.url = host + "/?s=" + texto
    try:
        return loadfilms(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def ultimifilm(item):
    logger.info("[FilmStreamingGratis.py]==> ultimifilm")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, '<div class="es-carousel">(.*?)</div></li></ul>')
    patron = '<h5><a href="([^"]+)"[^>]+>([^<]+)</a></h5>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra="movie",
                 thumbnail=item.thumbnail,
                 folder=True), tipo="movie"))

    return itemlist



def categorie(item):
    logger.info("[FilmStreamingGratis.py]==> categorie")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, '<div class="list styled custom-list"><ul>(.*?)</ul></div>')
    patron = '<li><a href="([^"]+)" title="[^"]+" >([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        if "Serie TV" not in scrapedtitle:  # Il sito non ha una buona gestione per le Serie TV
            itemlist.append(
                Item(channel=item.channel,
                     action="loadfilms",
                     title=scrapedtitle,
                     url=scrapedurl,
                     extra="movie",
                     thumbnail=item.thumbnail,
                     folder=True))

    return itemlist



def loadfilms(item):
    logger.info("[FilmStreamingGratis.py]==> loadfilms")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<h2 class="post-title"><a href="([^"]+)" title="[^"]+">'
    patron += '([^<]+)</a></h2>[^>]+>[^>]+>[^>]+><.*?data-src="([^"]+)"'
    patron += '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s+?([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot.strip())
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 plot=scrapedplot,
                 thumbnail=scrapedthumbnail,
                 folder=True), tipo=item.extra))

    patronvideos = '<link rel="next" href="([^"]+)"\s*/>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = matches[0]
        itemlist.append(
            Item(channel=item.channel,
                 action="loadfilms",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist



def findvideos(item):
    logger.info("[FilmStreamingGratis.py]==> findvideos")

    data = httptools.downloadpage(item.url).data

    if '%s/go/' % host in data:
        urls = scrapertools.find_multiple_matches(data, r'%s/go/[0-9\-]{6}' % host) # Multiple matches con go/9575-2/
        data = ""
        for url in urls:
            data += httptools.downloadpage(url).url + '\n'

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[%s] " % color(server.capitalize(), 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        videoitem.language = IDIOMAS['Italiano']

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist



def color(text, color):
    return "[COLOR %s]%s[/COLOR]" % (color, text)

