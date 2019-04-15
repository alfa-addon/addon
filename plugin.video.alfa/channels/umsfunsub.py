# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per umsfunsub
# ----------------------------------------------------------

import re
import urllib

from core import httptools
from platformcode import logger
from core import scrapertools
from core.item import Item
from core import tmdb



host = "http://trackerums.altervista.org"

headers = [['Referer', host]]


def mainlist(item):
    logger.info("[UMSFunSub.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     title=support.color("Progetti", "azure"),
                     action="progetti",
                     plot="- In corso\n- Conclusi",
                     url=makeurl("progetti-fansub-anime-giapponesi-attivi-shoujo-shounen-manga.php"),
                     thumbnail="http://www.hiumi.it/public/forum/styles/art_deluxe/imageset/logo.png"),
                Item(channel=item.channel,
                     title=support.color("Lista Completa", "azure"),
                     action="lista_anime",
                     url=makeurl("streaming-fansub-gratuiti.php?categoria=In_corso&cat=Conclusi"),
                     thumbnail="http://www.hiumi.it/public/forum/styles/art_deluxe/imageset/logo.png"),
                Item(channel=item.channel,
                     title=support.color("Cerca ...", "yellow"),
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")
                ]

    return itemlist



def progetti(item):
    logger.info("[UMSFunSub.py]==> progetti")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, '<div id="pf_imageMenu1" class="imageMenu">(.*?)</div>')
    patron = '<a href="[^=]+=([\w]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedcategory, scrapedtitle in matches:
        scrapedurl = "streaming-fansub-gratuiti.php?categoria=" + scrapedcategory
        if len(itemlist) < 2:
            itemlist.append(
                Item(channel=item.channel,
                     action="lista_anime",
                     title=color(scrapedtitle, "azure"),
                     url=makeurl(scrapedurl),
                     thumbnail=item.thumbnail,
                     folder=True))

    return itemlist



def search(item, texto):
    logger.info("[UMSFunSub.py]==> search")
    item.url = makeurl("risultato_ricerca.php?ricerca=" + texto)
    try:
        return lista_anime(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def lista_anime(item):
    logger.info("[UMSFunSub.py]==> lista_anime")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<img src="([^"]+)"[^<]+<[^<]+<[^<]+>[^>]+<[^<]+<[^<]+<[^<]+<[^>]+>([^<]+)<[^<]+<[^<]+<[^<]+<a href="([^&]+)&amp;titolo=([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapeddetails, scrapedurl, scrapedtitle in matches:
        scrapedurl = item.url.replace(item.url.split("/")[-1], scrapedurl)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="episodi",
                 title="%s %s %s" % (
                 color(scrapedtitle, "azure"), support.color(" | ", "red"), color(scrapeddetails, "deepskyblue")),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=makeurl(scrapedthumbnail),
                 folder=True))

    return itemlist



def episodi(item):
    logger.info("[UMSFunSub.py]==> episodi")
    itemlist = []

    item.url = item.url.replace("dettagli_sub.php", "lista-ep-streaming.php") + "&titolo=" + urllib.quote(
        item.fulltitle)

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<div id="listaepvera">([\d+|\w+]+)\.?([^<]+)\s+?[^<]+<[^<]+<a href="[^\d]+(\d+)&'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapednumber, scrapedtitle, scrapedid in matches:
        animetitle = item.title.replace("[COLOR red] |" + item.title.split("|")[-1], "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title="%s | %s - %s" % (
                 color(scrapednumber, "gold"), color(animetitle, "azure"), color(scrapedtitle, "deepskyblue")),
                 fulltitle="%s | %s" % (color(animetitle, "red"), color(scrapedtitle, "deepskyblue")),
                 show=item.show,
                 url=makeurl("dettagli-stream.php?id=" + scrapedid, item.title),
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist



def findvideos(item):
    logger.info("[UMSFunSub.py]==> findvideos")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patronvideo = 'flashvars="file=([^&]+)&'
    urlvideo = scrapertools.find_single_match(data, patronvideo)

    estensionevideo = urlvideo.split(".")[-1]

    itemlist.append(Item(channel=item.channel,
                         action="play",
                         title="[%s] %s" % (support.color("." + estensionevideo, "orange"), item.title),
                         fulltitle=item.fulltitle,
                         show=item.show,
                         url=urlvideo,
                         thumbnail=item.thumbnail))
    return itemlist


def makeurl(text, title=""):
    if title == "":
        return host + "/" + text
    else:
        return host + "/" + text + "&titolo=" + urllib.quote(title)

