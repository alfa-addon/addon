# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per cineblog01blog
# ------------------------------------------------------------

import re

from platformcode import logger, config
from core import httptools, scrapertools, servertools
from core.item import Item
from core.tmdb import infoIca

host = "https://www.cineblog01.cloud"



# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info()
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title=color("Nuovi film", "azure"),
                     url="%s/new-film-streaming/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="filmperanno",
                     title=color("Film per anno", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title=color("Cerca ..." , "yellow"),
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = "%s/new-film-streaming" % host
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info()
    item.url = host + "/xfsearch/" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<ul>\s*<li class="drop">(.*?)</ul>')
    patron = r'<li><a href="([^"]+)">([^"]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 url="".join([host, scrapedurl]),
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def filmperanno(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<li class="drop"><a.*?class="link1"><b>Film per anno</b></a>(.*?)</ul>')
    patron = r'<li><a href="([^"]+)">([^"]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def peliculas(item):
    logger.info()
    itemlist = []

    while True:
        data = httptools.downloadpage(item.url).data
        patron = r'<div class="short-story">\s*<a href="([^"]+)".*?>\s*'
        patron += r'<img.*?style="background:url\(([^\)]+)\).*?">'
        patron += r'\s*<div class="custom-title">([^<]+)</div>'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
            year = scrapertools.find_single_match(scrapedtitle, r'\((\d{4})\)')
            scrapedtitle = scrapedtitle.replace(year, color(year, "red"))

            # Bypass fake links
            html = httptools.downloadpage(scrapedurl).data

            patron = '<div class="video-player-plugin">([\s\S]*)<div class="wrapper-plugin-video">'
            matches = re.compile(patron, re.DOTALL).findall(html)
            for url in matches:
                if "scrolling" not in url: continue

                itemlist.append(infoIca(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="movie",
                         title=scrapedtitle,
                         fulltitle=scrapedtitle,
                         url=scrapedurl,
                         extra="movie",
                         thumbnail=scrapedthumbnail,
                         folder=True), tipo="movie"))

        # Pagine
        patronvideos = r'<a href="([^"]+)">Avanti</a>'
        next_page = scrapertools.find_single_match(data, patronvideos)

        if not next_page:
            break
        else:
            item.url = next_page
            if itemlist:
                itemlist.append(
                    Item(
                        channel=item.channel,
                        action="peliculas",
                        title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                        url=item.url,
                        thumbnail= "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                        folder=True))
                break

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info()
    data = httptools.downloadpage(item.url).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[%s] " % color(server, 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def color(text, color):
    return "[COLOR "+color+"]"+text+"[/COLOR]"

# ================================================================================================================
