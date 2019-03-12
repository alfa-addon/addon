# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale filmontv
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------

import re
import urllib

from core import httptools
from platformcode import logger
from core import scrapertools
from core.item import Item
from core import tmdb



host = "https://www.comingsoon.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR red]IN ONDA ADESSO[/COLOR]",
                     action="tvoggi",
                     url="%s/filmtv/oggi/in-onda/" % host,
                     thumbnail="http://a2.mzstatic.com/eu/r30/Purple/v4/3d/63/6b/3d636b8d-0001-dc5c-a0b0-42bdf738b1b4/icon_256.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Mattina[/COLOR]",
                     action="tvoggi",
                     url="%s/filmtv/oggi/mattina/" % host,
                     thumbnail="http://icons.iconarchive.com/icons/icons-land/weather/256/Sunrise-icon.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Pomeriggio[/COLOR]",
                     action="tvoggi",
                     url="%s/filmtv/oggi/pomeriggio/" % host,
                     thumbnail="http://icons.iconarchive.com/icons/custom-icon-design/weather/256/Sunny-icon.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Sera[/COLOR]",
                     action="tvoggi",
                     url="%s/filmtv/oggi/sera/" % host,
                     thumbnail="http://icons.iconarchive.com/icons/icons-land/vista-people/256/Occupations-Pizza-Deliveryman-Male-Light-icon.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Notte[/COLOR]",
                     action="tvoggi",
                     url="%s/filmtv/oggi/notte/" % host,
                     thumbnail="http://icons.iconarchive.com/icons/oxygen-icons.org/oxygen/256/Status-weather-clear-night-icon.png")]

    return itemlist


def tvoggi(item):
    logger.info(" tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    # Estrae i contenuti 
    patron = '<div class="col-xs-12 col-sm-6 box-contenitore filmintv">.*?src="([^"]+)[^<]+<[^<]+<[^<]+<[^<]+<[^<]+<.*?titolo">([^<]+)<.*?ore <span>([^<]+)<\/span><br \/>([^<]+)<\/div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, time, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()

        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[COLOR red]" + time + "[/COLOR] - [COLOR azure]" + scrapedtitle + "[/COLOR] [COLOR yellow][" + scrapedtv + "][/COLOR]" ,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 folder=True), tipo="movie")

    return itemlist


# Esta es la función que realmente realiza la búsqueda

def do_search(item):
    from channels import search
    return search.do_search(item)