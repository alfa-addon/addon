# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per toonitalia
# ----------------------------------------------------------

import re
import urlparse

from platformcode import logger, config
from core import servertools, httptools, scrapertools
from core.item import Item
from core import tmdb

host = "https://toonitalia.org"

def mainlist(item):
    logger.info("[toonitalia.py] Mainlist")

    # Menu Principale
    itemlist = [Item(channel=item.channel,
                     action="lista_anime",
                     title="Lista Anime",
                     text_color="azure",
                     url="%s/lista-anime-2/" % host,
                     extra="tv",
                     thumbnail="https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Anime Sub Ita",
                     text_color="azure",
                     url="%s/lista-anime-sub-ita/" % host,
                     extra="tv",
                     thumbnail="https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Film Animazione",
                     text_color="azure",
                     url="%s/lista-film-animazione/" % host,
                     extra="movie",
                     thumbnail="https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Serie TV",
                     text_color="azure",
                     url="%s/lista-serie-tv/" % host,
                     extra="tv",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="Cerca ...",
                     text_color="yellow",
                     action="search",
                     extra="anime",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist

def search(item, texto):
    logger.info("[toonitalia.py] Search")
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return src_list(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def src_list(item):
    logger.info("[toonitalia.py] src_list")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocchi = re.findall(r'<article id="post(.*?)</article>', data, re.DOTALL)
    for blocco in blocchi:
        url_title = re.findall(r'<h2 class="entry-title"><a href="([^"]+)"[^>]+>([^<]+)</a></h2>', blocco, re.DOTALL)

        scrapedtitle = scrapertools.decodeHtmlentities(url_title[0][1])
        scrapedurl = url_title[0][0]
        itemlist.append(
            Item(channel=item.channel,
                 action="links",
                 text_color="azure",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra=item.extra,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def lista_anime(item):
    logger.info("[toonitalia.py] Lista_anime")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    
    # Definisce il Blocco in cui cercare
    blocco = scrapertools.find_single_match(data, '<ul class="lcp_catlist"[^>]+>(.*?)</ul>')
    patron = '<a href="([^"]+)".*?>([^"]+)</a>'
    matches = re.compile(patron, re.DOTALL).finditer(blocco)


    for match in matches:
        scrapedtitle = scrapertools.unescape(match.group(2))
        scrapedurl = match.group(1)
        itemlist.append(
            Item(channel=item.channel,
                 action="links",
                 text_color="azure",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra=item.extra,
                 folder=True))

    return itemlist

def links(item):
    logger.info("[toonitalia.py] Links")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<span style="color:#[^;]+;">[Ll]inks?\s*'
    patron += r'([^<]+)<\/span>(?:<\/p>\s*|<br\s*\/>)(.*?)(?:<\/p>|\s*<a name)'
    blocchi = scrapertools.find_multiple_matches(data, patron)
    if not len(blocchi) > 0:
        patron = r'<a name="Links?\s*([^"]+)"><\/a>(.*?)<\/p>'
        blocchi = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, blocco in blocchi:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 text_color="orange",
                 title="Guarda con %s" % scrapedtitle,
                 url=blocco,
                 extra=scrapedtitle,
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist

def episodi(item):
    logger.info("[toonitalia.py] Episodi")
    itemlist = []
    patron = ''

    if 'openload' in item.extra.lower():
        patron = r'<a href="([^"]+)"[^>]+>(?:[^>]+>[^>]+>[^>]+>\s*<b>|)([^<]+)(?:</b>|</a>)'
    else:
        patron = r'<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.findall(patron, item.url, re.DOTALL)
    
    for scrapedurl, scrapedtitle in matches:
        if 'wikipedia' in scrapedurl: continue
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="tv",
                 title=scrapedtitle,
                 text_color="azure",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 extra="tv",
                 show=item.show,
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist

def findvideos(item):
    logger.info("[toonitalia.py] Findvideos")
    itemlist = servertools.find_video_items(data=item.url)
    
    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[%s] " % color(server.capitalize(), 'orange'), item.title])
        videoitem.text_color = "azure"
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

def color(text, color):
    return "[COLOR %s]%s[/COLOR]" % (color, text)
