# -*- coding: utf-8 -*-
# FilmONTV Channel
# By iSOD Crew | Para equipo SOD

import re, urllib

from core import httptools, scrapertools, tmdb
from core.item import Item
from platformcode import logger
from channelselector import get_thumb

__channel__ = "filmontv"

host = "http://www.elmundo.es"
second_host = "https://sincroguia-tv.expansion.com/ahora-en-tv"

def mainlist(item):
    logger.info()
    itemlist = [Item(channel=__channel__,
                     title=color("In Onda", "red"),
                     action="onairing",
                     extra="",
                     url=second_host,
                     thumbnail=get_thumb("channels_on_air.png")),
                Item(channel=__channel__,
                     title=color("Peliculas", "azure"),
                     action="day",
                     extra="peliculas",
                     thumbnail=get_thumb("channels_peliculas_en_aire.png")),
                Item(channel=__channel__,
                     title=color("TV Series", "azure"),
                     action="day",
                     extra="series",
                     thumbnail=get_thumb("channels_tv_en_aire.png"))]

    return itemlist


def day(item):
    logger.info()
    itemlist = [Item(channel=__channel__,
                     title=color("Madrugada", "azure"),
                     action="guidetv",
                     extra="madrugada",
                     url="%s/television/programacion-tv/%s.html" % (host, item.extra),
                     thumbnail="http://icons.iconarchive.com/icons/icons-land/weather/256/Sunrise-icon.png"),
                Item(channel=__channel__,
                     title=color("Mañana", "azure"),
                     action="guidetv",
                     extra="manana",
                     url="%s/television/programacion-tv/%s.html" % (host, item.extra),
                     thumbnail="http://icons.iconarchive.com/icons/custom-icon-design/weather/256/Sunny-icon.png"),
                Item(channel=__channel__,
                     title=color("Mediodia", "azure"),
                     action="guidetv",
                     extra="mediodia",
                     url="%s/television/programacion-tv/%s.html" % (host, item.extra),
                     thumbnail="http://icons.iconarchive.com/icons/custom-icon-design/weather/256/Sunny-icon.png"),
                Item(channel=__channel__,
                     title=color("Tarde", "azure"),
                     action="guidetv",
                     extra="tarde",
                     url="%s/television/programacion-tv/%s.html" % (host, item.extra),
                     thumbnail="https://s.evbuc.com/https_proxy?url=http%3A%2F%2Ftriumphbar.com%2Fimages%2Fhappyhour_icon.png&sig=ADR2i7_K2FSfbQ6b3dy12Xjgkq9NCEdkKg"),
                Item(channel=__channel__,
                     title=color("Noche", "azure"),
                     action="guidetv",
                     extra="noche",
                     url="%s/television/programacion-tv/%s.html" % (host, item.extra),
                     thumbnail="http://icons.iconarchive.com/icons/oxygen-icons.org/oxygen/256/Status-weather-clear-night-icon.png")]

    return itemlist

def onairing(item):
    logger.info()
    itemlist = []

    # Load the page
    data = httptools.downloadpage(item.url).data

    # Extract contents
    patron = r'alt="Programación\s*([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>\s*<div[^\(]+url\(([^\)]+)[^>]+>\s*'
    patron += r'<a.*?title="([^"]+)"[^>]*>[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtv, scrapedthumbnail, scrapedtitle, time in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()

        itemlist.append(
            Item(channel=__channel__,
                 action="do_search",
                 extra=scrapedtitle,
                 title=color("%s | %s [%s]" % (color(time, "gray"), scrapedtitle, color(scrapedtv, "yellow")), "azure"),
                 fulltitle=scrapedtitle,
                 url=['Películas', 'Series'],
                 thumbnail=scrapedthumbnail,
                 folder=True))

    return itemlist

def guidetv(item):
    logger.info()
    itemlist = []

    # Load the page
    data = httptools.downloadpage(item.url).data

    # Extract contents
    bloque = scrapertools.find_single_match(data, r'<div id="%s_\d+"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<ul class="rango-horario-programacion"[^>]*>(.*?)</ul>' % (item.extra))
    patron = r'<span class="hora-categoria">([^<]+)[^>]+>[^>]+>[^>]+>\s*<img.*?title="([^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<img alt="([^"]+)".*?src="([^"]+)"[^>]+>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for time, scrapedtv, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        scrapedthumbnail = "http:" + scrapedthumbnail

        itemlist.append(
            Item(channel=__channel__,
                 action="do_search",
                 extra=scrapedtitle,
                 title=color("%s | %s [%s]" % (color(time, "gray"), scrapedtitle, color(scrapedtv, "yellow")), "azure"),
                 fulltitle=scrapedtitle,
                 url=['Películas'] if 'peliculas' in item.extra else ['Series'],
                 thumbnail=scrapedthumbnail,
                 folder=True))

    tmdb.set_infoLabels(itemlist)
    return itemlist


# Esta es la función que realmente realiza la búsqueda

def do_search(item):
    from channels import search
    return search.do_search(item, item.url)

def color(text, color):
    return "[COLOR %s]%s[/COLOR]" % (color, text)
