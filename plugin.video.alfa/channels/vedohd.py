# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vedohd
# ------------------------------------------------------------

import re
import urlparse

from channels import autoplay, filtertools, support
from core import scrapertoolsV2, httptools, servertools, tmdb
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from channelselector import thumb

#impostati dinamicamente da getUrl()
host = ""
headers = ""

permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
cb01Url = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
data = httptools.downloadpage(cb01Url).data
host = scrapertoolsV2.get_match(data, r'<a class=mega-menu-link href=(https://vedohd[^/]+)')+'/'
if host=="":  # in caso cb01 cambi, si spera di riuscire ad accedere da questo URL
    host = "https://vedohd.pw/"
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'wstream']
list_quality = ['HD', 'SD']

#esclusione degli articoli 'di servizio'
blacklist = ['CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ', 'AVVISO IMPORTANTE – CB01.UNO', 'GUIDA VEDOHD']


def mainlist(item):
    logger.info("[vedohd.py] mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title="Film",
                     url=host+"film-hd",
                     contentType="movie"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="I più votati",
                     url=host + "ratings/?get=movies",
                     contentType="movie"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="I più popolari",
                     url=host + "trending/?get=movies",
                     contentType="movie"),
                Item(channel=item.channel,
                     action="generos",
                     title="Generi",
                     url=host,
                     contentType="movie"),
                Item(channel=item.channel,
                     action="year",
                     title="Anno",
                     url=host,
                     contentType="movie"),
                Item(channel=item.channel,
                     action="search",
                     title="Cerca",
                     url=host,
                     contentType="movie")
                ]
    
    autoplay.show_option(item.channel, itemlist)

    # auto thumb
    itemlist=thumb(itemlist) 

    return itemlist


def search(item, text):
    logger.info("[vedohd.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    itemlist = []

    support.dooplay_search(item, itemlist, blacklist)


    return itemlist


def peliculas(item):
    logger.info("[vedohd.py] video")
    itemlist = []

    support.dooplay_films(item, itemlist, blacklist)

    return itemlist


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Trailer':
            logger.info(link['title'])
            server, quality = scrapertoolsV2.get_match(link['title'], '([^ ]+) ?(HD|3D)?')
            if quality:
                title = server + " [COLOR blue][" + quality + "][/COLOR]"
            else:
                title = server
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=title,
                     url=link['url'],
                     server=server,
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=quality,
                     contentType=item.contentType,
                     folder=False))

    autoplay.start(itemlist, item)

    return itemlist


def generos(item):
    itemlist = []
    patron = '<a href="([^"#]+)">([a-zA-Z]+)'
    support.scrape(item, itemlist, patron, ['url', 'title'], patron_block='<a href="#">Genere</a><ul class="sub-menu">.*?</ul>', action='peliculas', url_host=host)
    return itemlist


def year(item):
    itemlist = []
    patron = '<a href="([^"#]+)">([a-zA-Z]+)'
    support.scrape(item, itemlist, patron, ['url', 'title'], patron_block='<a href="#">Anno</a><ul class="sub-menu">.*?</ul>', action='peliculas', url_host=host)
    return itemlist


def play(item):
    logger.info("[vedohd.py] play")
    itemlist = []

    data = support.swzz_get_url(item)

    try:
        itemlist = servertools.find_video_items(data=data)

        for videoitem in itemlist:
            videoitem.title = item.show
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            videoitem.thumbnail = item.thumbnail
            videoitem.contentType = item.contentType
            videoitem.channel = item.channel
    except AttributeError:
        logger.error("vcrypt data doesn't contain expected URL")

    return itemlist
