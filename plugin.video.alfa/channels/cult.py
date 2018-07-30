# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Icarus - XBMC Plugin
# https://alfa-addon.com/categories/icarus-addon.50/
# By iSOD Crew
# ------------------------------------------------------------

import re, urlparse, urllib

from core import httptools, scrapertools
from core.item import Item
from platformcode import logger


__channel__ = "cult"

host = "https://www.imdb.com"


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info("[Cult.py]==> mainlist")
    return movies("".join([host, "/list/ls000571226/"]))

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def movies(url):
    logger.info("[Cult.py]==> movies")
    itemlist = []

    data = httptools.downloadpage(url).data
    groups = scrapertools.find_multiple_matches(data, r'<div class="lister-item-image ribbonize"(.*?)<div class="wtw-option-standalone"')

    for group in groups:
        infos = \
        { 
            'title': single_scrape(group, r'<a[^>]+>([^<]+)</a>'), 'year': single_scrape(group, r'unbold">\((\d+)\)</span>'), 
            'rating': single_scrape(group, r'star__rating">(\d+,?\d*)</span>'), 'plot': single_scrape(group, r'<p class="">\s*([^<]+)</p>'), 
            'genres': single_scrape(group, r'genre">\s*([^<]+)</span>'), 'age': single_scrape(group, r'certificate">([^<]+)</span>'), 
            'metascore': single_scrape(group, r'metascore[^>]*>\s*(\d+)[^>]+>'), 'image': single_scrape(group, r'loadlate="([^"]+)"[^>]+>')
        }

        infos['title'] = scrapertools.decodeHtmlentities(infos['title']).strip()
        infos['plot'] = scrapertools.decodeHtmlentities(infos['plot']).strip()

        title = "%s (%s)%s[%s]" % (infos['title'], color(infos['year'], "gray"), (" [%s]" % age_color("%s" % infos['age'])) if infos['age'] else "", color(infos['rating'], "orange"))

        plot = "Anno: %s%s\nVoto: %s\nGeneri: %s\nMetascore: %s\nDescrizione:\n%s" % \
            (infos['year'], "\nPubblico: %s" % age_color(infos['age']) if infos['age'] else "", infos['rating'], infos['genres'], infos['metascore'], infos['plot'])

        itemlist.append(
            Item(channel=__channel__,
                 text_color="azure",
                 action="do_search",
                 title=title,
                 plot=plot,
                 extra="%s{}%s" % (urllib.quote_plus(infos['title']), "movie"),
                 thumbnail=infos['image']))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def do_search(item):
    logger.info("[Cult.py]==> do_search")
    from channels import search
    return search.do_search(item)


# ===============================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def age_color(age):
    logger.info("[Cult.py]==> age_color")
    if age.lower() == "t":
        age = color(age, "green")
    elif age.lower() == "pg":
        age = color(age, "yellow")
    elif age.lower() == "vm14":
        age = color(age, "yellow")
    elif age.lower() == "vm18":
        age = color(age, "red")
    elif 'banned' in age.lower():
        age = color(age.replace('(', '').replace(')', '').strip(), "red")

    return age


# ================================================================================================================


# -------------------------------------
def single_scrape(text, patron):
    logger.info("[Cult.py]==> single_scrape")
    return scrapertools.find_single_match(text, patron)

# =====================================

# -------------------------------------
def color(text, color):
    logger.info("[Cult.py]==> color")
    return "[COLOR %s]%s[/COLOR]" % (color, text)

# =====================================
