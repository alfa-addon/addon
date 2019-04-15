# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per filmperevolvere
# ----------------------------------------------------------
import re
import urlparse

import lib.pyaes as aes
from core import httptools
from platformcode import logger, config
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb



host = "https://filmperevolvere.it"

headers = [
    ['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'],
    ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Accept-Language', 'en-US,en;q=0.5'],
    ['Referer', host],
    ['DNT', '1'],
    ['Upgrade-Insecure-Requests', '1'],
    ['Cache-Control', 'max-age=0']
]


def mainlist(item):
    logger.info("kod.filmperevolvere mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Ultimi Film Inseriti[/COLOR]",
                     action="peliculas",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorie",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def newest(categoria):
    logger.info("[filmperevolvere.py] newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host
            item.action = "peliculas"
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


def search(item, texto):
    logger.info("[filmperevolvere.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return []


def categorie(item):
    itemlist = []

    c = get_test_cookie(item.url)
    if c: headers.append(['Cookie', c])

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data,
                                    'GENERI<span class="mega-indicator">(.*?)<\/ul>')

    # Estrae i contenuti 
    patron = '<a class="mega-menu-link" href="(.*?)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:

        if scrapedtitle.startswith(("HOME")):
            continue
        if scrapedtitle.startswith(("SERIE TV")):
            continue
        if scrapedtitle.startswith(("GENERI")):
            continue

        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 url='c|%s' % scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    for i in itemlist:
        logger.info(i) 

    return itemlist

def peliculas(item):
    logger.info("kod.filmperevolvere peliculas")
    itemlist = []

    c = get_test_cookie(item.url)
    if c: headers.append(['Cookie', c])

    if item.url[1]=="|":
        patron = 'class="ei-item-title"><a\s*href="([^"]*)">([^<]*)'
        item.url=item.url[2:]
    else:
        patron = '<div class="post-thumbnail">\s*<a href="([^"]+)" title="([^"]+)">\s*<img width="520"'

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle.title()
        txt = "Serie Tv"
        if txt in scrapedtitle: continue
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Paginazione
    patronvideos = '<span class=\'current\'>[^<]+</span><a class=[^=]+=[^=]+="(.*?)">'
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


def findvideos(item):
    logger.info("kod.filmperevolvere findvideos")

    c = get_test_cookie(item.url)
    if c: headers.append(['Cookie', c])

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, '[COLOR green][B]', videoitem.title, '[/B][/COLOR]'])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist

def get_test_cookie(url):
    data = httptools.downloadpage(url, headers=headers).data
    a = scrapertools.find_single_match(data, 'a=toNumbers\("([^"]+)"\)')
    if a:
        b = scrapertools.find_single_match(data, 'b=toNumbers\("([^"]+)"\)')
        if b:
            c = scrapertools.find_single_match(data, 'c=toNumbers\("([^"]+)"\)')
            if c:
                cookie = aes.AESModeOfOperationCBC(a.decode('hex'), iv=b.decode('hex')).decrypt(c.decode('hex'))
                return '__test=%s' % cookie.encode('hex')
    return ''
