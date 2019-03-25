# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per altadefinizioneclick
# ----------------------------------------------------------
import base64
import re
import urlparse

from channels import autoplay, filtertools, support
from core import scrapertools, servertools, httptools, tmdb
from core.item import Item
from platformcode import logger, config
from channelselector import thumb, get_thumb

host = "https://altadefinizione.center"   ### <- cambio Host da .fm a .center

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', "vidoza", "thevideo", "okru", 'youtube']
list_quality = ['1080p']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'altadefinizioneclick')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'altadefinizioneclick')

headers = [['Referer', host]]

def mainlist(item):
    logger.info("kod.altadefinizione.pink mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [
        Item(channel=item.channel,
             title="[B]Novità[/B]",
             action="fichas",
             url=host + "/nuove-uscite/",
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[B] > Film per Genere[/B]",
             action="genere",
             url=host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="[B] > Film per Anno[/B]",
             action="anno",
             url=host,
             thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
        Item(channel=item.channel,
             title="Film Sub-Ita",
             action="fichas",
             url=host + "/sub-ita/",
             thumbnail="http://i.imgur.com/qUENzxl.png"),
        Item(channel=item.channel,
             title="[COLOR blue]Cerca Film...[/COLOR]",
             action="search",
             extra="movie",
             thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    # auto thumb
    itemlist=thumb(itemlist) 

    return itemlist


def search(item, texto):
    logger.info("[altadefinizioneclick.py] " + item.url + " search " + texto)

    item.url = host + "/?s=" + texto

    try:
        return fichas_src(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def genere(item):
    logger.info("[altadefinizioneclick.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<ul class="listSubCat" id="Film">(.*?)</ul>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li><a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def anno(item):
    logger.info("[altadefinizioneclick.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<ul class="listSubCat" id="Anno">(.*?)</div>'
    data = scrapertools.find_single_match(data, patron)

    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl,
                 folder=True))

    return itemlist


def fichas(item):
    logger.info("[altadefinizioneclick.py] fichas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<img width[^s]+src="([^"]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="([^"]+)">([^<]+)<\/a>[^>]+>[^>]+>[^>]+>(?:[^>]+>|)[^I]+IMDB\:\s*([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, scrapedpuntuacion in matches:
        
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        clean_title = title
        title += " (" + scrapedpuntuacion + ")"

        # ------------------------------------------------
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        # ------------------------------------------------

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 contentTitle=clean_title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagination
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail=thumb()))

    return itemlist

def fichas_src(item):
    logger.info("[altadefinizioneclick.py] fichas")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    patron = '<a href="([^"]+)">\s*<div[^=]+=[^=]+=[^=]+=[^=]+=[^=]+="(.*?)"[^>]+>[^<]+<[^>]+>\s*<h[^=]+="titleFilm">(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        title = scrapertools.decodeHtmlentities(scrapedtitle)
        clean_title = re.sub(r'\(\d+\.?\d*\)', '', title).strip()

        # ------------------------------------------------
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        # ------------------------------------------------

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 contentTitle=clean_title,
                 title="[COLOR azure]" + title + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagination
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas_src",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnail=thumb(item)))

    return itemlist

def findvideos(item):
    logger.info("[altadefinizioneclick.py] findvideos")

    itemlist = []

    itemlist = support.hdpass_get_servers(item)

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
