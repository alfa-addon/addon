# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per italiaserie
# https://alfa-addon.com/categories/kod-addon.50/
# ----------------------------------------------------------
import re
import urlparse

from core import httptools, scrapertools, servertools
from core.item import Item
from core import tmdb
from lib import unshortenit
from platformcode import config, logger

host = "https://italiaserie.org"


def mainlist(item):
    logger.info("kod.italiaserie mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Aggiornamenti Serie TV[/COLOR]",
                     action="peliculas",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Ultimi Episodi[/COLOR]",
                     action="latestep",
                     url="%s/aggiornamento-episodi/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]
    return itemlist


def newest(categoria):
    logger.info("[italiaserie.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = "%s/aggiornamento-episodi/" % host
            item.action = "latestep"
            itemlist = latestep(item)

            if itemlist[-1].action == "latestep":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def latestep(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data,
                                            r'<h1 class="entry-title">Aggiornamento Episodi</h1>\s*<div class="entry">(.*?)<p>&nbsp;</p>')
    patron = r'(?:<span[^>]+>|<strong>|)(<?[^<]*)<a href="([^"]+)"[^>]*>([^<]+)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedtitle, scrapedurl, scraped_number_and_title in matches:
        scrapedlang = scrapertools.find_single_match(scraped_number_and_title, r'(SUB-ITA)')
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace(scrapedlang, scrapedlang)
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        fulltitle = scrapedtitle.replace("–", "").replace(' ', '').strip()

        scraped_number_and_title = scrapertools.decodeHtmlentities(scraped_number_and_title.replace('&#215;', 'x'))
        seasonandep = scrapertools.find_single_match(scraped_number_and_title, r'(\d+x[0-9\-?]+)')
        extra = r'%s(.*?)(?:<br\s*/>|</p>)'

        # Multi Ep
        if re.compile(r'[,-]\s*\d+', re.DOTALL).findall(scraped_number_and_title):
            season = scrapertools.find_single_match(scraped_number_and_title, r'(\d+x)')
            scraped_number_and_title = scraped_number_and_title.split(',')
            for ep in scraped_number_and_title:
                ep = (season + ep if season not in ep else ep).strip()
                seasonandep = scrapertools.find_single_match(ep, r'(\d+x[0-9\-?]+)')
                completetitle = "%s %s" % (scrapedtitle, ep)

                itemlist.append(
                    Item(channel=item.channel,
                         action="findepvideos",
                         title=completetitle,
                         contentSerieName=completetitle,
                         fulltitle=fulltitle,
                         url=scrapedurl,
                         extra=extra % seasonandep.replace('x', '×'),
                         folder=True))
            continue

        # Ep singolo
        correct_scraped_number = seasonandep.replace('x', '×')
        extra = extra % (correct_scraped_number)
        completetitle = ("%s %s %s" % (
            scrapedtitle, scraped_number_and_title, "(%s)" % scrapedlang if scrapedlang else scrapedlang)).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findepvideos",
                 title=completetitle,
                 contentSerieName=completetitle,
                 fulltitle=fulltitle,
                 url=scrapedurl,
                 extra=extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def peliculas(item):
    logger.info("kod.italiaserie peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '<div class="post-thumb">\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedurl = scrapedurl.replace("-1/", "-links/")

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione
    patronvideos = '<a class="next page-numbers" href="(.*?)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def search(item, texto):
    logger.info("[italiaserie.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def episodios(item):
    def load_episodios(html, item, itemlist, lang_title):
        patron = '((?:.*?<a[^h]+href="[^"]+"[^>]+>[^<][^<]+<(?:b|\/)[^>]+>)+)'
        matches = re.compile(patron).findall(html)
        for data in matches:
            # Estrazione
            scrapedtitle = data.split('<a ')[0]
            scrapedtitle = re.sub(r'<[^>]*>', '', scrapedtitle).strip()
            if scrapedtitle != 'Categorie':
                scrapedtitle = scrapedtitle.replace('&#215;', 'x')
                scrapedtitle = scrapedtitle.replace('×', 'x')
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

    logger.info("[italiaserie.py] episodios")

    itemlist = []

    # Download pagina
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    if 'CLICCA QUI PER GUARDARE TUTTI GLI EPISODI' in data:
        item.url = re.sub('\-\d+[^\d]+$', '-links', item.url)
        data = httptools.downloadpage(item.url).data
        data = scrapertools.decodeHtmlentities(data)
    data = scrapertools.get_match(data, '<div class="entry-content">(.*?)<div class="clear"></div>')

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
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("kod.italiaserie findvideos")
    itemlist = []

    # Carica la pagina 
    data = item.url

    matches = re.findall(r'<a href="([^"]+)" target="_blank" rel="nofollow">', data, re.DOTALL)

    data = []
    for url in matches:
        url, c = unshortenit.unshorten(url)
        data.append(url)

    itemlist = servertools.find_video_items(data=str(data))

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist


def findepvideos(item):
    logger.info("kod.italiaserie findepvideos")

    itemlist = []

    # Carica la pagina 
    data = item.url

    matches = re.findall(r'<a href="([^"]+)"[^>]*>[^<]+</a>', data, re.DOTALL)

    data = []
    for url in matches:
        url, c = unshortenit.unshorten(url)
        data.append(url)

    itemlist = servertools.find_video_items(data=str(data))

    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist
