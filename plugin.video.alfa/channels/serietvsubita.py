# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per http://serietvsubita.net/
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------
import re, urlparse

from platformcode import logger, config
from core import scrapertools, httptools
from core.item import Item
from core.tmdb import infoIca



host = "http://serietvsubita.net"


def mainlist(item):
    logger.info("kod.channels.serietvsubita mainlist")

    itemlist = [Item(channel=item.channel,
                     action="episodios",
                     title="[COLOR azure]Novità[/COLOR]",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     folder=True),
                Item(channel=item.channel,
                     action="series",
                     title="[COLOR azure]Indice A-Z[/COLOR]",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     folder=True),
                Item(channel=item.channel,
                     action="search",
                     extra="tvshow",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search",
                     folder=True)]
    return itemlist


def search(item, texto):
    logger.info("kod.channels.serietvsubita search")
    item.url = host + "/?s=" + texto + "&op.x=0&op.y=0"

    try:
        return episodios(item)
    # Se captura la excepci?n, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def episodios(item):
    logger.info("kod.channels.serietvsubita episodios")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # patron  = '</div><div class="clear"></div>.*?'
    patron = '<h2><a href="([^"]+)".*?title="([^"]+)".*?<p><a href.*?<img.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if scrapedtitle.startswith(("NUOVA PAGINA FACEBOOK")):
            continue
        if scrapedtitle.startswith("Link to "):
            scrapedtitle = scrapedtitle[8:]
        scraped_1 = scrapedtitle.split("S0")[0][:-1]
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace(scraped_1, "")

        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scraped_1,
                 show=scraped_1,
                 title="[COLOR azure]" + scraped_1 + "[/COLOR]" + " " + scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True), tipo='tv'))

    # paginación
    patron = '<div id="navigation">.*?\d+</a> <a href="([^"]+)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR orange]Post più vecchi...[/COLOR]",
                 url=next_page,
                 action="episodios",
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


def series(item):
    logger.info("kod.channels.serietvsubita series")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<li id="widget_categories" class="widget png_scale"><h2 class="blocktitle"><span>ELENCO SERIE</span>(.*?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li class="cat-item[^<]+<a href="([^"]+)[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        thumbnail = ""
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)

        itemlist.append(
            Item(channel=item.channel,
                 action="episodiosearch",
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=url,
                 thumbnail="http://xbmc-repo-ackbarr.googlecode.com/svn/trunk/dev/skin.cirrus%20extended%20v2/extras/moviegenres/New%20TV%20Shows.png",
                 folder=True))

    # paginación
    patron = '<div id="navigation">.*?\d+</a> <a href="([^"]+)"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR orange]Episodi precedenti...[/COLOR]",
                 url=next_page,
                 action="series",
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


def episodiosearch(item):
    logger.info("kod.channels.serietvsubita episodios")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="post-meta">.*?<a href="([^"]+)" title="([^"]+)".*?<img.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=item.show,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist
