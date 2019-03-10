# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per marapcana
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------
import re

from core import scrapertools, httptools, servertools
from core.item import Item
from core.tmdb import infoIca
from lib import unshortenit
from platformcode import logger, config

host = "http://marapcana.live"
# in caso di oscuramento verificare l'indirizzo http://marapcana.online/

headers = [['Referer', host]]

PERPAGE = 12


def mainlist(item):
    logger.info(" mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Film[/COLOR]",
                     url="%s/film-categoria/dvdrip-bdrip/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title="[COLOR azure]Categorie[/COLOR]",
                     url="%s/elenchi-film/" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peliculas_tv",
                     title="[COLOR azure]Serie TV[/COLOR]",
                     url="%s/lista-serie-tv/" % host,
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca SerieTV...[/COLOR]",
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png")]

    return itemlist


def peliculas(item):
    logger.info(" peliculas")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<a href="([^"]+)" title="([^"]+)" class="teaser-thumb">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedthumbnail = ""
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot",
                 Folder=True), tipo='movie'))

    nextpage_regex = '<a class="nextpostslink".*?href="([^"]+)".*?<\/a>'
    next_page = scrapertools.find_single_match(data, nextpage_regex)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url="%s" % next_page,
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))
    return itemlist


def categorie(item):
    itemlist = []

    if item.url == "":
        item.url = host

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.get_match(data, 'Genere(.*?)</select>')
    patron = '<option value="([^"]+)">(.*?)</option>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        if "adesso" in scrapedtitle:
            continue
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 fulltitle=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 viewmode="movie_with_plot",
                 Folder=True))
    return itemlist


def peliculas_tv(item):
    itemlist = []

    if item.url == "":
        item.url = host

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.get_match(data, 'Lista Serie Tv</h2>(.*?)</section>')
    patron = '<a href=\'(/serie/[^\']+)\'>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedurl, scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="episodios",
                 title=title,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True), tipo='tv'))

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def episodios(item):
    itemlist = []

    if item.url == "":
        item.url = host
    if host not in item.url:
        item.url = '%s%s' % (host, item.url)

    data = httptools.downloadpage(item.url, headers=headers).data

    bloque = scrapertools.find_single_match(data, '<table>(.*?)</table>')
    patron = '<tr><td>([^<]+)</td>.*?</tr>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    for scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="episodio",
                 fulltitle=scrapedtitle,
                 title=scrapedtitle,
                 url=item.url,
                 viewmode="movie_with_plot",
                 Folder=True))
    return itemlist


def episodio(item):
    if item.url == "":
        item.url = host

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<tr><td>' + item.title + '</td>.*?</tr>'
    data = scrapertools.find_single_match(data, patron)
    itemlist = servertools.find_video_items(data=data)
    for i in itemlist:
        tab = re.compile(
            '<div\s*id="(tab[^"]+)"[^>]+>[^>]+>[^>]+src="http[s]*:%s[^"]+"' % i.url.replace('http:', '').replace(
                'https:', ''), re.DOTALL).findall(data)
        qual = ''
        if tab:
            qual = re.compile('<a\s*href="#%s">([^<]+)<' % tab[0], re.DOTALL).findall(data)[0].replace("'", "")
            qual = "[COLOR orange]%s[/COLOR] - " % qual
        i.title = '%s[COLOR green][B]%s[/B][/COLOR] - %s' % (qual, i.title[2:], item.title)
        i.channel = item.channel
        i.fulltitle = item.title

    return itemlist


def search(item, texto):
    logger.info("[marapcana.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        if item.extra == "movie":
            return peliculas(item)
        if item.extra == "tvshow":
            return peliculas_tv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info(" findvideos")

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    urls = re.findall(r'href="([^"]+)" target="_blank" rel="noopener noreferrer">', data, re.DOTALL)

    if urls:
        for url in urls:
            url, c = unshortenit.unshorten(url)
            data += url + '\n'

    itemlist = servertools.find_video_items(data=data)
    for i in itemlist:
        tab = re.compile(
            '<div\s*id="(tab[^"]+)"[^>]+>[^>]+>[^>]+src="http[s]*:%s[^"]+"' % i.url.replace('http:', '').replace(
                'https:', ''), re.DOTALL).findall(data)
        qual = ''
        if tab:
            qual = re.compile('<a\s*href="#%s">([^<]+)<' % tab[0], re.DOTALL).findall(data)[0].replace("'", "")
            qual = "[COLOR orange]%s[/COLOR] - " % qual
        i.title = '%s[COLOR green][B]%s[/B][/COLOR] - %s' % (qual, i.title[1:], item.title)
        i.channel = item.channel
        i.fulltitle = item.title

    return itemlist
