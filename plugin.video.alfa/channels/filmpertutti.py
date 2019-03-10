# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per filmpertutti.co
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------
import re
import urlparse

from channels import autoplay
from core import scrapertools, servertools, httptools
from core.item import Item
from core.tmdb import infoIca
from lib import unshortenit
from platformcode import config, logger

host = "https://www.filmpertutti.uno"
list_servers = ['akvideo', 'openload', 'streamango', 'wstream']
list_quality = ['default']


def mainlist(item):
    logger.info("kod.filmpertutti mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Ultimi film inseriti[/COLOR]",
                     action="peliculas",
                     extra="movie",
                     url="%s/category/film/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie film[/COLOR]",
                     action="categorias",
                     url="%s/category/film/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     extra="tvshow",
                     action="peliculas_tv",
                     url="%s/category/serie-tv/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("kod.filmpertutti newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host + "/category/film/"
            item.action = "peliculas"
            item.extra = "movie"
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


def peliculas(item):
    logger.info("kod.filmpertutti peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)" data-thumbnail="([^"]+)"><div>\s*<div class="title">(.*?)<.*?IMDb">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scraprate in matches:
        scrapedplot = ""
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR] - IMDb: " + scraprate,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 extra=item.extra,
                 folder=True), tipo='movie'))

    # Paginazione 
    patronvideos = '<a href="([^"]+)"[^>]+>Pagina'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 extra=item.extra,
                 folder=True))

    return itemlist


def peliculas_tv(item):
    logger.info("kod.filmpertutti peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<li><a href="([^"]+)" data-thumbnail="([^"]+)"><div>\s*<div class="title">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedplot = ""
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="episodios",
                 fulltitle=title,
                 show=title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 extra=item.extra,
                 folder=True), tipo='tv'))

    # Paginazione 
    patronvideos = '<a href="([^"]+)"[^>]+>Pagina'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 extra=item.extra,
                 folder=True))

    return itemlist

def categorias(item):
    logger.info("kod.filmpertutti categorias")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # Narrow search by selecting only the combo
    patron = '<option>Scegli per Genere</option>(.*?)</select'
    bloque = scrapertools.get_match(data, patron)

    # The categories are the options for the combo  
    patron = '<option data-src="([^"]+)">([^<]+)</option>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 plot=scrapedplot))

    return itemlist


def search(item, texto):
    logger.info("kod.filmpertutti " + item.url + " search " + texto)
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


def episodios(item):
    def load_episodios(html, item, itemlist, lang_title):
        patron = '.*?<a[^h]+href="[^"]+"[^>]+>[^<]+<\/a>(?:<br \/>|<\/p>|-)'
        matches = re.compile(patron).findall(html)
        for data in matches:
            # Estrae i contenuti 
            scrapedtitle = data.split('<a ')[0]
            scrapedtitle = re.sub(r'<[^>]*>', '', scrapedtitle).strip()
            if scrapedtitle != 'Categorie':
                scrapedtitle = scrapedtitle.replace('&#215;', 'x')
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="episode",
                         title="[COLOR azure]%s[/COLOR]" % (scrapedtitle + " (" + lang_title + ")"),
                         url=data,
                         thumbnail=item.thumbnail,
                         extra=item.extra,
                         fulltitle=scrapedtitle + " (" + lang_title + ")" + ' - ' + item.show,
                         show=item.show))

    logger.info("[filmpertutti.py] episodios")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)

    lang_titles = []
    starts = []
    patron = r"Stagione.*?ITA"
    matches = re.compile(patron, re.IGNORECASE).finditer(data)
    for match in matches:
        season_title = match.group()
        if season_title != '':
            lang_titles.append('SUB ITA' if 'SUB' in season_title.upper() else 'ITA')
            starts.append(match.end())

    i = 1
    len_lang_titles = len(lang_titles)

    while i <= len_lang_titles:
        inizio = starts[i - 1]
        fine = starts[i] if i < len_lang_titles else -1

        html = data[inizio:fine]
        lang_title = lang_titles[i - 1]

        load_episodios(html, item, itemlist, lang_title)

        i += 1

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios" + "###" + item.extra,
                 show=item.show))

    return itemlist


def findvideos(item):
    def add_myitem(sitemlist, scontentType, server, stitle, surl):
        sitemlist.append(
            Item(channel=item.channel,
                 action="play",
                 contentType=scontentType,
                 title=stitle,
                 fulltitle=item.fulltitle,
                 server=server,
                 url=surl,
                 thumbnail=item.thumbnail,
                 extra=item.extra))

    logger.info("kod.filmpertutti findvideos")
    itemlist = []
    logger.debug(item)

    # Carica la pagina 
    if item.contentType == "episode":
        patron = '<a\s*href="(.*?)\s*".*?[^>]+>([^<]+)<\/a>'
        matches = re.compile(patron).findall(item.url)

        lsrvo = ''
        for lurl, lsrv in matches:

            if lsrv == 'HD': lsrv = lsrvo + ' HD'
            lsrvo = lsrv

            add_myitem(itemlist, "episode", lsrv, "[COLOR azure]%s[/COLOR]" % lsrv, lurl)
    else:
        # Carica la pagina 
        data = httptools.downloadpage(item.url).data
        patron = '<strong>\s*(Versione.*?)<p><strong>Download'
        data = re.compile(patron, re.DOTALL).findall(data)

        if data:
            vqual = re.compile('ersione.*?:\s*([^|,\s,&,<]+)').findall(data[0])
            sect = re.compile('Streaming', re.DOTALL).split(data[0])

            ## SD links
            links = re.compile('<a\s*href="([^",\s]+).*?>([^<]+)', re.DOTALL).findall(sect[1])

            for link, srv in links:
                add_myitem(itemlist, "movie", srv, "[COLOR azure]%s (SD)[/COLOR] - %s" % (srv, vqual[0]), link)

            ## HD Links
            if len(sect) > 2:
                links = re.compile('<a\s*href="([^",\s]+).*?>([^<]+)', re.DOTALL).findall(sect[2])

                for link, srv in links:
                    add_myitem(itemlist, "movie", srv, "[COLOR azure]%s (HD)[/COLOR] - %s" % (srv, vqual[0]), link)
        else:
            itemlist = servertools.find_video_items(item=item)

    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info("kod.filmpertutti play: %s" % item.url)

    data = item.url

    data, c = unshortenit.unshorten(data)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist
