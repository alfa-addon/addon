# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale downloadme
# Version: 201804162230
# ------------------------------------------------------------
import re

from core import httptools, scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from lib.unshortenit import unshorten
from platformcode import logger, config
from lib import unshortenit




host = "https://www.downloadme.gratis"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("[downloadme.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Film[/COLOR]",
                     url="%s/category/film/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                #Item(channel=item.channel,
                #     action="peliculas",
                #     title="Serie TV",
                #     text_color="azure",
                #     url="%s/category/serie-tv/" % host,
                #     extra="tv",
                #     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                #Item(channel=item.channel,
                #     action="peliculas",
                #     title="Anime",
                #     text_color="azure",
                #     url="%s/category/anime/" % host,
                #     extra="tv",
                #     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title="[COLOR azure]Categorie[/COLOR]",
                     url="%s/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png")]

    return itemlist


def categorie(item):
    logger.info("[downloadme.py] peliculas")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, '<ul id="menu-categorie" class="menu">(.*?)</ul>')
    patron = '<a href="(.*?)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 text_color="azure",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url="%s/%s" % (host, scrapedurl),
                 extra=item.extra,
                 viewmode="movie_with_plot",
                 Folder=True))

    return itemlist

def peliculas(item):
    logger.info("[downloadme.py] peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    #blocco = scrapertools.find_single_match(data, '</p></div><div class="row">(.*?)<span class="sep">')
    patron = r'<a href="(.*?)" title="(.*?)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        #scrapedtitle = scrapedtitle.split("&#8211;")[0]
        #scrapedtitle = scrapedtitle.split(" Download")[0]
        scrapedthumbnail = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos" if 'movie' in item.extra else 'episodes',
                 text_color="azure",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url="%s/%s" % (host, scrapedurl),
                 viewmode="movie_with_plot",
                 thumbnail=scrapedthumbnail))

    nextpage_regex = '<a class="next page-numbers" href="([^"]+)">'
    next_page = scrapertools.find_single_match(data, nextpage_regex)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url="%s%s" % (host, next_page),
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))
    return itemlist

def episodes(item):
    logger.info("[downloadme.py] tv_series")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = r'<a href="([^"]+)"[^>]*>([^<]+)</a>(?:<br>|</p>)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if not scrapertools.find_single_match(scrapedtitle, r'\d+'): continue
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 text_color="azure",
                 contentType="episode",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 thumbnail=item.thumbnail,
                 url=scrapedurl,
                 viewmode="movie_with_plot"))

    return itemlist

def findvideos(item):
    logger.info("kod.downloadme findvideos")
    itemlist = []

    if 'movie' in item.extra:
        # Carica la pagina 
        data = httptools.downloadpage(item.url, headers=headers).data

        patron = r'<a\s*href="([^"]+)" target="_blank" rel="noopener">.*?link[^<]+</a>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl in matches:
            url, c = unshorten(scrapedurl)
            data += url + '\n'

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel

    return itemlist

