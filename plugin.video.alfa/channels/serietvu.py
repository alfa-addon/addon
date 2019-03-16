# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per http://www.serietvu.com/
# ------------------------------------------------------------

import re

from core import httptools, scrapertools, servertools
from core.item import Item
from core import tmdb
from platformcode import logger, config



host = "https://www.serietvu.club"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()

headers = [['Referer', host]]


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info("[SerieTVU.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     action="lista_serie",
                     title=color("Nuove serie TV", "orange"),
                     url="%s/category/serie-tv" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="latestep",
                     title=color("Nuovi Episodi", "azure"),
                     url="%s/ultimi-episodi" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_serie",
                     title=color("Serie TV Aggiornate", "azure"),
                     url="%s/ultimi-episodi" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title=color("Cerca ...", "yellow"),
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info("[SerieTVU.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi"
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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info("[SerieTVU.py]==> search")
    item.url = host + "/?s=" + texto
    try:
        return lista_serie(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info("[SerieTVU.py]==> categorie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.get_match(data, r'<h2>Sfoglia</h2>\s*<ul>(.*?)</ul>\s*</section>')
    patron = r'<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title=scrapedtitle,
                 contentType="tv",
                 url="%s%s" % (host, scrapedurl),
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def latestep(item):
    logger.info("[SerieTVU.py]==> latestep")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<small>([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle, scrapedinfo in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
        episodio = re.compile(r'(\d+)x(\d+)', re.DOTALL).findall(scrapedinfo)
        title = "%s %s" % (scrapedtitle, scrapedinfo)
        itemlist.append(
            Item(channel=item.channel,
                 action="findepisodevideo",
                 title=title,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra=episodio,
                 thumbnail=scrapedimg,
                 show=title,
                 folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def lista_serie(item):
    logger.info("[SerieTVU.py]==> lista_serie")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedimg,
                 show=scrapedtitle,
                 folder=True))

    # Pagine
    patron = '<a href="([^"]+)"[^>]+>Pagina'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodios(item):
    logger.info("[SerieTVU.py]==> episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'<option value="(\d+)"[\sselected]*>.*?</option>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for value in matches:
        patron = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % value
        blocco = scrapertools.find_single_match(data, patron)

        patron = r'(<a data-id="\d+[^"]*" data-href="([^"]+)" data-original="([^"]+)" class="[^"]+">)[^>]+>[^>]+>([^<]+)</div>'
        matches = re.compile(patron, re.DOTALL).findall(blocco)
        for scrapedextra, scrapedurl, scrapedimg, scrapedtitle in matches:
            number = scrapertools.decodeHtmlentities(scrapedtitle.replace("Episodio", "")).strip()
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=value + "x" + number.zfill(2),
                     fulltitle=scrapedtitle,
                     contentType="episode",
                     url=scrapedurl,
                     thumbnail=scrapedimg,
                     extra=scrapedextra,
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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info("[SerieTVU.py]==> findvideos")
    itemlist = servertools.find_video_items(data=item.extra)

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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findepisodevideo(item):
    logger.info("[SerieTVU.py]==> findepisodevideo")

    # Download Pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # Prendo il blocco specifico per la stagione richiesta
    patron = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % item.extra[0][0]
    blocco = scrapertools.find_single_match(data, patron)

    # Estraggo l'episodio
    patron = r'<a data-id="%s[^"]*" data-href="([^"]+)" data-original="([^"]+)" class="[^"]+">' % item.extra[0][1].lstrip("0")
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    itemlist = servertools.find_video_items(data=matches[0][0])

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title).capitalize()
        videoitem.title = "".join(["[%s] " % color(server, 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
        videoitem.channel = item.channel

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def color(text, color):
    return "[COLOR %s]%s[/COLOR]" % (color, text)

# ================================================================================================================
