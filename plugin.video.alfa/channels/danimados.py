# -*- coding: utf-8 -*-
# -*- Channel Danimados -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
import base64
import re
PY3 = False

if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int

from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger
from channelselector import get_thumb
from lib.AlfaChannelHelper import CustomChannel

IDIOMAS = {'la': 'LAT', 'sub': 'VOSE'}
list_idiomas = list(IDIOMAS.values())
list_servers = ['fembed', 'mega', 'yourupload', 'streamsb', 'mp4upload', 'mixdrop', 'uqload']
list_quality = []

canonical = {
             'channel': 'danimados', 
             'host': config.get_setting("current_host", 'danimados', default=''), 
             'host_alt': ["https://www.d-animados.com/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = CustomChannel(host, tv_path="/series", canonical=canonical)



def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Últimos capítulos", action="last_tvshows", url=host,
                         thumbnail=get_thumb("last", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", url=host, xtaxonomy="none", xterm="none", xsearch="none", xtype="series", xpage=1,
                         thumbnail=get_thumb("tvshows", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Anime", action="list_all", url=host, xtaxonomy="post_tag", xterm="180", xsearch="none", xtype="mixed", xpage=1,
                         thumbnail=get_thumb("anime", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all", url=host, xtaxonomy="none", xterm="none", xsearch="none", xtype="movies", xpage=1,
                         thumbnail=get_thumb("movies", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="generos", url = host,
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=", xtaxonomy="none", xterm="none", xtype="mixed", xpage=1, 
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def last_tvshows(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    patron  = 'item-pelicula pull-left.*?href="([^"]+).*?'
    patron += 'title="([^"]+).*?'
    patron += '<img src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, action="findvideos",
                        infoLabels={"year": "-"}))
    return itemlist


def list_all(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    nonce = scrapertools.find_single_match(data, '"nonce":"(\w+)')
    if item.extra == "generos":
        item.xgenres = scrapertools.find_single_match(data, 'data-term="(\w+)')
        item.xterm = item.xgenres
        item.xgenres = "\"" + item.xgenres + "\""
        item.xtaxonomy = "category"
        item.xtype = "mixed"
        if not item.xpage: item.xpage = 1
    post ={
	"action": "action_search",
	"vars": "{\"_wpsearch\":\"%s\",\"taxonomy\":\"%s\",\"search\":\"%s\",\"term\":\"%s\",\"type\":\"%s\",\"genres\":[%s],\"years\":[],\"sort\":\"1\",\"page\":%s}" %(nonce, item.xtaxonomy, item.search, item.xterm, item.xtype, item.xgenres, item.xpage)
    }
    data = httptools.downloadpage(url=host + "/wp-admin/admin-ajax.php", post=post).json["html"]
    
    patron  = 'post dfx fcl movies.*?title">([^<]+).*?'
    patron += 'year">([^<]+).*?'
    patron += 'src="([^"]+).*?'
    patron += 'href="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    infoLabels = {}
    for scrapedtitle, scrapedyear, scrapedthumbnail, scrapedurl in matches:
        infoLabels["year"] = scrapedyear
        actionx = "findvideos"
        if "series" in scrapedurl: actionx = "seasons"
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, action=actionx,
                        infoLabels=infoLabels, contentSerieName=scrapedtitle
                        ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if itemlist:
        pagina = "Pagina: %s" %str(item.xpage+1)
        itemlist.append(Item(channel=item.channel, title=pagina, url=scrapedurl, action="list_all",
                        infoLabels=infoLabels, contentSerieName=scrapedtitle,
                        xtaxonomy=item.xtaxonomy, xterm=item.xterm, xtype=item.xtype, xpage=item.xpage + 1,
                        ))

    return itemlist


def generos(item):
    logger.info()

    itemlist = list()
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?is)Categorias.*?</ul')
    patron  = 'href="([^"]+).*?'
    patron += '>([^"<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, action="list_all", extra="generos"))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    if item.c_type == "Movie":
        return episodesxseason(item)
    data = httptools.downloadpage(item.url).data
    patron  = 'Temporada <span>(\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    season_list = list()
    infoLabels = item.infoLabels

    for season_number in matches:
        title = "Temporada %s" % season_number
        infoLabels["season"] = season_number
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseasons",
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    itemlist = itemlist[::-1]

    itemlist = AlfaChannel.add_serie_to_videolibrary(item, itemlist)
    

    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    bloque = scrapertools.find_single_match(data, 'Temporada <span>%s<\/span>.*?</li></ul>' %season)
    patron  = 'src="([^"]+).*?'
    patron += 'alt="([^"]+).*?'
    patron += '<span>S(\d+)-'
    patron += 'E(\d+).*?'
    patron += 'href="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedthumbnail, scrapedtitle, scrapedseason, scrapedepisode, scrapedurl in matches:
        lang = "VOSE"
        infoLabels["episode"] = scrapedepisode
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, action="findvideos",
                             language=IDIOMAS.get(lang, "VOSE"), infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    patron  = '(?is)data-player.*?src="([^"]+)'
    patron += ''
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        data1 = httptools.downloadpage(url).data
        patron1  = 'src="([^"]+)'
        url1 = scrapertools.find_single_match(data1, patron1)
        data2 = httptools.downloadpage(url1).data
        patron2 = "go_to_player\('([^']+)"
        matches2 = scrapertools.find_multiple_matches(data2, patron2)
        for url2 in matches2:
            urlx = url2
            itemlist.append(Item(channel=item.channel, title="%s", url=urlx, action="play", language=item.language,
                                infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_idiomas)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    if "player" in item.url:
        data3 = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(data3, 'function runPlayer.*?url: "([^"]+)')
        if not url.startswith("https"): url = "https:" + url
        data = httptools.downloadpage(url).data
        item.url = "https:" + scrapertools.find_single_match(data, '"file":"([^"]+)').replace("\\","")
        item.server = ""

    return [item]


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.search = texto
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
