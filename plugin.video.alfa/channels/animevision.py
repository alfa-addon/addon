# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per animevision
# ----------------------------------------------------------
import re

from core import httptools, scrapertools, tmdb
from platformcode import logger
from core.item import Item



host = "https://www.animevision.it"


def mainlist(item):
    logger.info("kod.animevision mainlist")

    itemlist = [Item(channel=item.channel,
                     action="lista_anime",
                     title="[COLOR azure]Anime [/COLOR]- [COLOR orange]Lista Completa[/COLOR]",
                     url=host + "/elenco.php",
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     url=host + "/?s=",
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart)]

    return itemlist



def search(item, texto):
    logger.info("kod.animevision search")
    item.url = host + "/?search=" + texto
    try:
        return lista_anime_src(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []




def lista_anime_src(item):
    logger.info("kod.animevision lista_anime_src")

    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r"<a class=\'false[Ll]ink\'\s*href=\'([^\']+)\'[^>]+>[^>]+>[^<]+<img\s*style=\'[^\']+\'\s*class=\'[^\']+\'\s*src=\'[^\']+\'\s*data-src=\'([^\']+)\'\s*alt=\'([^\']+)\'[^>]*>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedimg = host + "/" + scrapedimg
        scrapedurl = host + "/" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 thumbnail=scrapedimg,
                 fanart=scrapedimg,
                 viewmode="movie"))

    return itemlist



def lista_anime(item):
    logger.info("kod.animevision lista_anime")

    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = "<div class='epContainer' ><a class='falseLink' href='(.*?)'><div[^=]+=[^=]+=[^=]+=[^=]+='(.*?)'[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^=]+=[^>]+><b>(.*?)<"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedimg = host + "/" + scrapedimg
        scrapedurl = host + "/" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 contentType="tvshow",
                 title=scrapedtitle,
                 text_color="azure",
                 url=scrapedurl,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 thumbnail=scrapedimg,
                 fanart=scrapedimg,
                 viewmode="movie"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist



def episodi(item):
    logger.info("kod.animevision episodi")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = "<a class='nodecoration text-white' href='(.*?)'>(.+?)<"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.split(';')[1]
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedurl = host + "/" + scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=scrapedtitle,
                 url=scrapedurl,
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart))

    return itemlist



CategoriaThumbnail = "http://static.europosters.cz/image/750/poster/street-fighter-anime-i4817.jpg"
CategoriaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
