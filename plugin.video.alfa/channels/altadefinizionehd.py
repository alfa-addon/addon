# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per filmissimi
# https://alfa-addon.com/categories/kod-addon.50/
# ----------------------------------------------------------
import re

from core import httptools, scrapertools, servertools
from platformcode import logger, config
from core.item import Item
from core.tmdb import infoIca



host = "https://altadefinizione.wiki"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("[filmissimi.py] mainlist")
    itemlist = [Item(channel=item.channel,
                     action="elenco",
                     title="[COLOR yellow]Novita'[/COLOR]",
                     url=host,
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="elenco",
                     title="[COLOR azure]Film Sub-Ita[/COLOR]",
                     url=host + "/genere/sub-ita",
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="elenco",
                     title="[COLOR azure]Film HD[/COLOR]",
                     url=host + "/genere/film-in-hd",
                     thumbnail=NovitaThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="genere",
                     title="[COLOR azure]Genere[/COLOR]",
                     url=host,
                     thumbnail=GenereThumbnail,
                     fanart=FilmFanart),
                Item(channel=item.channel,
                     action="search",
                     extra="movie",
                     title="[COLOR orange]Cerca..[/COLOR]",
                     thumbnail=CercaThumbnail,
                     fanart=FilmFanart)]

    return itemlist



def newest(categoria):
    logger.info("[filmissimi.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = "http://www.filmissimi.net"
            item.action = "elenco"
            itemlist = elenco(item)

            if itemlist[-1].action == "elenco":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist



def genere(item):
    logger.info("[filmissimi.py] genere")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.get_match(data, '<ul id="menu-categorie-1" class="ge">(.*?)</div>')

    patron = '<li id=[^>]+><a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=item.channel,
                 action="elenco",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    return itemlist



def elenco(item):
    logger.info("[filmissimi.py] elenco")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    elemento = scrapertools.find_single_match(data, r'<div class="estre">(.*?)<div class="paginacion">')

    patron = r'<a href="([^"]+)" title="([^"]+)"[^>]*>[^>]+>\s*.*?img src="([^"]+)"[^>]*>'
    matches = re.compile(patron, re.DOTALL).findall(elemento)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        logger.info("title=[" + scrapedtitle + "] url=[" + scrapedurl + "] thumbnail=[" + scrapedthumbnail + "]")
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail), tipo="movie"))

    # Paginazione
    # ===========================================================================================================================
    matches = scrapedSingle(item.url, '<div class="paginacion">(.*?)</div>',
                            "current'>.*?<\/span><.*?href='(.*?)'>.*?</a>")
    if len(matches) > 0:
        paginaurl = matches[0]
        itemlist.append(
            Item(channel=item.channel, action="elenco", title=AvantiTxt, url=paginaurl, thumbnail=AvantiImg))
    else:
        itemlist.append(Item(channel=item.channel, action="mainlist", title=ListTxt, folder=True))
    # ===========================================================================================================================

    
    return itemlist




def search(item, texto):
    logger.info("[filmissimi.py] init texto=[" + texto + "]")
    itemlist = []
    url = host + "/?s=" + texto

    data = httptools.downloadpage(url, headers=headers).data

    patron = 'src="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="([^"]+)"[^>]*>([^<]+)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="findvideos",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail), tipo="movie"))

    # Paginazione
    # ===========================================================================================================================
    matches = scrapedSingle(url, '<div class="paginacion">(.*?)</div>', "current'>.*?<\/span><.*?href='(.*?)'>.*?</a>")

    if len(matches) > 0:
        paginaurl = matches[0]
        itemlist.append(Item(channel=item.channel, action="elenco", title=AvantiTxt, url=paginaurl, thumbnail=AvantiImg))
    else:
        itemlist.append(Item(channel=item.channel, action="mainlist", title=ListTxt, folder=True))
    # ===========================================================================================================================
    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[COLOR azure][[COLOR orange]%s[/COLOR]][/COLOR] " % server.capitalize(), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        
    return itemlist



def scrapedAll(url="", patron=""):
    matches = []
    data = httptools.downloadpage(url, headers=headers).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches



def scrapedSingle(url="", single="", patron=""):
    data = httptools.downloadpage(url, headers=headers).data
    elemento = scrapertools.find_single_match(data, single)
    matches = re.compile(patron, re.DOTALL).findall(elemento)
    scrapertools.printMatches(matches)

    return matches



NovitaThumbnail = "https://superrepo.org/static/images/icons/original/xplugin.video.moviereleases.png.pagespeed.ic.j4bhi0Vp3d.png"
GenereThumbnail = "https://farm8.staticflickr.com/7562/15516589868_13689936d0_o.png"
FilmFanart = "https://superrepo.org/static/images/fanart/original/script.artwork.downloader.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
ListTxt = "[COLOR orange]Torna a elenco principale [/COLOR]"
AvantiTxt = config.get_localized_string(30992)
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"
thumbnail = "http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"
