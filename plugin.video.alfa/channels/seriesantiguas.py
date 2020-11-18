# -*- coding: utf-8 -*-
import sys
import re

from core import httptools, scrapertools, servertools, tmdb, jsontools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www.seriesantiguas.com'
base_url_start = '/feeds/posts/default'
base_url_end = '?alt=json-in-script&start-index=1&max-results=20&orderby=published'
IDIOMAS = {"Latino": "LAT"}
list_language = list(IDIOMAS.values())

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel =  item.channel,
                                    title = "Novedades",
                                    action = "newest",
                                    url = host + base_url_start + '/-/ESTRENO' + base_url_end,
                                    thumbnail = get_thumb("newest", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Destacadas",
                                    action = "list_all",
                                    url = host + base_url_start + '/-/POPULARES' + base_url_end,
                                    thumbnail = get_thumb("hot", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Series de los 80s",
                                    action = "list_all",
                                    url = host + base_url_start + '/-/80s' + base_url_end,
                                    thumbnail = get_thumb("year", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Series de los 90s",
                                    action = "list_all",
                                    url = host + base_url_start + '/-/90s' + base_url_end,
                                    thumbnail = get_thumb("year", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Series del 2000",
                                    action = "list_all",
                                    url = host + base_url_start + '/-/00s' + base_url_end,
                                    thumbnail = get_thumb("year", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Todas las series",
                                    action = "list_all",
                                    url = host + base_url_start + base_url_end,
                                    thumbnail = get_thumb("all", auto=True)
                                    ))
    itemlist.append(Item(channel =  item.channel,
                                    title = "Buscar...",
                                    action = "search",
                                    url = host+'/search/?q=',
                                    thumbnail = get_thumb("search", auto=True)
                                    ))
    return itemlist

def format_ascii(str):
    str = scrapertools.unescape(str)
    str = str.replace('á','a')
    str = str.replace('é','e')
    str = str.replace('í','i')
    str = str.replace('ó','o')
    str = str.replace('ú','u')
    str = str.replace('ü','u')
    str = str.replace('Á','A')
    str = str.replace('É','E')
    str = str.replace('Í','I')
    str = str.replace('Ó','O')
    str = str.replace('Ú','U')
    str = str.replace('Ü','U')
    return str

def check_item_for_exception(data):
    title_replace = ['¿Por qué a mí?']
    title_exception = ['(?s).por qu. a m..*']
    year_replace = ['1998']
    year_exception = ['(?s)las chicas superpoderosas.*']
    for x in range(len(title_replace)):
        data.contentSerieName = re.sub(title_exception[x], title_replace[x],
                                        data.contentSerieName.lower())
    for x in range(len(year_replace)):
        if scrapertools.find_single_match(data.contentSerieName.lower(),
                                            year_exception[x]):
            data.infoLabels['year'] = year_replace[x]
    return data

def newest(item):
    return list_all(item)

def list_all(item):
    # Puede que el código sea útil después
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    jsonptn = 'gdata.io.handleScriptLoaded\((.*?)\);'
    jsonmatch = scrapertools.find_single_match(data, jsonptn)
    json_list = jsontools.load(jsonmatch)
    items = json_list['feed']['entry']
    infoLabels = item.infoLabels
    for i in items:
        html = i['content']['$t']
        resultptn = '(?s)<img alt=".*?".*?src=.*?"([^"]+).*?a.*?href="([^"]+)">.*?<h3 style=.*?">.*?</h3>.*?<div class=.*?style=.*?"clear: both;.*?>([^<]+)'
        resultmatch = scrapertools.find_multiple_matches(html, resultptn)
        for scrapedthumbnail, scrapedurl, scrapedplot in resultmatch:
            infoLabels['plot'] = scrapertools.unescape(scrapedplot)
            infoLabels['fanart'] = scrapedthumbnail
            itemlist.append(
                check_item_for_exception(
                    Item(
                        action = "seasons",
                        channel = item.channel,
                        title = format_ascii(i['title']['$t']),
                        thumbnail = scrapedthumbnail,
                        url = scrapedurl,
                        contentSerieName = format_ascii(i['title']['$t']),
                        infoLabels = infoLabels
                    )
                )
            )
    # Si se encuentra otra página, se agrega un paginador
    nextpage = get_nextrow_url(item.url, int(json_list['feed']['openSearch$totalResults']['$t']))
    if nextpage != False:
        itemlist.append(
            Item(
                action = 'newest',
                channel =  item.channel,
                title =  '[COLOR orange]Siguiente página > [/COLOR]',
                url = nextpage
            )
        )
    logger.error(str(nextpage))
    tmdb.set_infoLabels(itemlist, seekTmdb = True, idioma_busqueda = 'es')
    return itemlist

def get_nextrow_url(current_url, total_results):
    logger.info()
    max_rslt_ptn = '(?s)max-results=([^&]+)'
    start_idx_ptn = '(?s)start-index=([^&]+)'
    cur_start_idx = scrapertools.find_single_match(current_url, start_idx_ptn)
    cur_max_rslt = scrapertools.find_single_match(current_url, max_rslt_ptn)
    cur_max_rslt = int(cur_max_rslt)
    cur_start_idx = int(cur_start_idx)
    start_idx = cur_max_rslt + cur_start_idx
    if not start_idx >= total_results:
        current_url = re.sub(start_idx_ptn, 'start-index=' + str(start_idx), current_url)
        return current_url
    else:
        return False
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        itemlist.append(
            check_item_for_exception(
                Item(
                    action =   "seasons",
                    channel = item.channel,
                    title = format_ascii(scrapedtitle),
                    thumbnail = scrapedthumbnail,
                    url = scrapedurl,
                    contentSerieName = format_ascii(scrapedtitle)
                )
            )
        )
    tmdb.set_infoLabels(itemlist, seekTmdb = True, idioma_busqueda = 'es')
    return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    listpattern = "(?s)class='topmenu1 megamenu' id='megamenuid'.*?class='megalist'.*?<a.*?(<ul.*?</ul>)"
    listmatch = scrapertools.find_single_match(data, listpattern)
    pattern = "(?s)<li><a href='([^']+)..T.*?[^ ]+.(.).*?</a>"
    matches = scrapertools.find_multiple_matches(listmatch, pattern)
    infoLabels = item.infoLabels
    for scpurl, scpseasonnum in matches:
        infoLabels['season'] = scpseasonnum
        itemlist.append(
            Item(
                action = "episodios",
                channel = item.channel,
                title = "Temporada %s" % infoLabels['season'],
                url = scpurl,
                infoLabels = infoLabels
            )
        )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True, idioma_busqueda = 'es')
    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        itemlist.append(
            Item(
                channel = item.channel,
                title = '[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                url = item.url,
                action = "add_serie_to_library",
                extra = "episodesxseason",
                contentSerieName = item.contentSerieName
            )
        )
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    eplist = seasons(item)

    for episode in eplist:
        itemlist.extend(episodios(episode))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    pattern = '(?s)class=\'post hentry.*?a href="([^"]+).*?img alt=\'([^\']+).*?src=\'([^\']+)'
    matches = scrapertools.find_multiple_matches(data, pattern)
    infoLabels = item.infoLabels
    for scpurl, scptitle, scpthumbnail in matches:
        title = ""
        episode = ""
        subpattern = '(?s)(.*?) \(T.*?[^ ]+.x.(.+?)\)'
        submatches = scrapertools.find_multiple_matches(scptitle, subpattern)
        for eptitle, epnum in submatches:
            title = eptitle
            episode = epnum
        infoLabels['episode'] = episode
        itemlist.append(
            Item(
                action =   "findvideos",
                channel = item.channel,
                title = str(infoLabels['season']) + 'x' + str(infoLabels['episode']) + ': ' + title,
                thumbnail = scpthumbnail,
                url = scpurl,
                infoLabels = infoLabels
            )
        )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True, idioma_busqueda = 'es')
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    itemlist.extend(servertools.find_video_items(item = item, data = data))
    itemlist = servertools.get_servers_itemlist(itemlist, None, True)
    for video in itemlist:
        video.channel = item.channel
        video.title = ('Ver por ' + video.title.replace(
                        (config.get_localized_string(70206) % ''), ''))
        video.thumbnail = item.thumbnail
        video.infoLabels = item.infoLabels
    itemlist = servertools.get_servers_itemlist(itemlist, None, True)
    return itemlist

def search(item, texto):
    logger.info()
    itemlist = []
    if texto != '':
        try:
            texto = texto.replace(" ", "+")
            texto = format_ascii(texto)
            item.url += texto
            return list_all(item)
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
            return itemlist