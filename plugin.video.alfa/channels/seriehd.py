# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per seriehd
# ------------------------------------------------------------
import base64
import re
import urlparse

from channels import autoplay, filtertools, support
from core import scrapertools, servertools, httptools, tmdb
from platformcode import logger, config
from core.item import Item
from channelselector import thumb

host = "https://www.seriehd.video"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'thevideome']
list_quality = ['1080p', '720p', '480p', '360']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'seriehd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'seriehd')

headers = [['Referer', host]]


def mainlist(item):
    logger.info("seriehd.py mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     action="fichas",
                     title="[B]Serie TV[/B]",
                     url=host + "/serie-tv-streaming/"),
                Item(channel=item.channel,
                     action="sottomenu",
                     title=" > Serie TV per Genere",
                     url=host),
                Item(channel=item.channel,
                     action="nation",
                     title=" > Serie TV per Nazione",
                     url=host),
                Item(channel=item.channel,
                     action="search",
                     extra="tvshow",
                     title="[COLOR blue]Cerca...[/COLOR]",
                     thumbnail="")]

    autoplay.show_option(item.channel, itemlist)

    # auto thumb
    itemlist=thumb(itemlist) 

    return itemlist


def search(item, texto):
    logger.info("[seriehd.py] search")

    item.url = host + "/?s=" + texto

    try:
        return fichas(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sottomenu(item):
    logger.info("[seriehd.py] sottomenu")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl))

    # Elimina 'voci dal menu' de la lista de 'sottomenu'
    itemlist.pop(0)
    itemlist.pop(0)
    itemlist.pop(0)
    itemlist.pop(28)

    return itemlist

def nation(item):
    itemlist = [Item(channel=item.channel,
                     action="fichas",
                     title="Serie TV Americane",
                     url=host+'/serie-tv-streaming/serie-tv-americane/'),
                Item(channel=item.channel,
                     action="fichas",
                     title="Serie TV Italiane",
                     url=host+'/serie-tv-streaming/serie-tv-italiane/')]
    # auto thumb
    itemlist=thumb(itemlist) 

    return itemlist

def fichas(item):
    logger.info("[seriehd.py] fichas")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<h2>(.*?)</h2>\s*'
    patron += r'<img src="([^"]+)" alt="[^"]*" />\s*'
    patron += '<A HREF="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedthumbnail, scrapedurl in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail))

    patron = r"<span class='current'>\d+</span><a rel='nofollow' class='page larger' href='([^']+)'>\d+</a>"
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="fichas",
                 title="[COLOR blue]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 thumbnali=thumb()))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    logger.info("[seriehd.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<iframe width=".+?" height=".+?" src="([^"]+)" allowfullscreen frameborder="0">'
    url = scrapertools.find_single_match(data, patron).replace("?seriehd", "")

    data = httptools.downloadpage(url).data.replace('\t', '').replace('\n', '').replace(' class="active"', '')


    section_stagione = scrapertools.find_single_match(data, '<h3>STAGIONE</h3><ul>(.*?)</ul>')
    patron = r'<li[^>]+><a href="([^"]+)">(\d+)<'
    seasons = re.compile(patron, re.DOTALL).findall(section_stagione)

    for scrapedseason_url, scrapedseason in seasons:

        season_url = urlparse.urljoin(url, scrapedseason_url)
        data = httptools.downloadpage(season_url).data.replace('\t', '').replace('\n', '').replace(' class="active"', '')

        section_episodio = scrapertools.find_single_match(data, '<h3>EPISODIO</h3><ul>(.*?)</ul>')
        patron = r'<a href="([^"]+)">(\d+)<'
        episodes = re.compile(patron, re.DOTALL).findall(section_episodio)

        for scrapedepisode_url, scrapedepisode in episodes:
            episode_url = urlparse.urljoin(url, scrapedepisode_url)

            title = scrapedseason + "x" + scrapedepisode.zfill(2)

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="episode",
                     title=title,
                     url=episode_url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[seriehd.py] findvideos")

    itemlist = []

    itemlist = support.hdpass_get_servers(item)

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    for item in itemlist:
        logger.info('ITEM= ' +str(item))

    return itemlist


def newest(categoria):
    logger.info("[seriehd] newest" + categoria)
    itemlist = []
    item = Item()
    try:

        ## cambiar los valores "peliculas, infantiles, series, anime, documentales por los que correspondan aqui en
        # el py y en l json ###
        if categoria == "series":
            item.url = host
            itemlist = fichas(item)

            if 'Successivo>>' in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
