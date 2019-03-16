# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale streaminghd
# ------------------------------------------------------------

from core import httptools, scrapertools, servertools, listtools
from core.item import Item
from platformcode import logger
from core import tmdb
import re

__channel__ = "streaminghd"
listtools.__channel__ = __channel__

host = "https://streaminghd.online"

headers = [['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0']] ## <-- user agent per poter accedere


def mainlist(item):
    logger.info("[streaminghd.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Film[/COLOR]",
                     url="%s/film/" % host,
                     extracheck="film",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Piu' Votati[/COLOR]",
                     url="%s/piu-votati/" % host,
                     extracheck="piuvotati",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Piu' Visti[/COLOR]",
                     url="%s/piu-visti//" % host,
                     extracheck="piuvisti",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Serie TV[/COLOR]",
                     url="%s/serietv/serie/" % host,
                     extracheck="serietv",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="by_anno_or_by_genere",
                     title="[COLOR azure]Genere[/COLOR]",
                     url=host,
                     extracheck="by_genere",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="by_anno_or_by_genere",
                     title="[COLOR azure]Elenco Per Anno[/COLOR]",
                     url=host,
                     extracheck="by_anno",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Film[/COLOR]",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Serie[/COLOR]",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def peliculas(item):
    logger.info("[streaminghd.py] peliculas")
    patron = ''

    if item.url == "":
        item.url = host
    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    logger.info("[streaminghd.py] peliculas")
    datat = data

    ## Setting generic parameters for moth of movies
    itemp = {'title': '\\2 (\\5) [Rate: [COLOR yellow]\\3[/COLOR]]',
             'url': '\\4',
             'thumbnail': '\\1',
             'extracheck': item.extracheck}

    tipos = 'movie'
    if 'serie' in item.extracheck:
        tipos = 'tv'
        itemp['content'] = 'tvshow'
        itemp['action'] = 'list_seasons'

    ## special condition for few movies
    if item.extracheck == "film":
        datat = scrapertools.find_single_match(data, '<div id="archive-content".*?<\/article><\/div>')
    elif "search" in item.extracheck:                                                                                              ## <-- NON FIXATO
        datat = scrapertools.find_single_match(data, '<div class="search-page">.*?<\/div><\/div><\/div>')
        itemp['title'] = '\\3 (\\4)'
        itemp['url'] = '\\2'
        patron = 'article.*?src="([^"\s]+)\s*".*?href="([^"\s]+)\s*"\s*>([^<]+).*?year">([^<]+).*?<\/article>'
    elif "piu" in item.extracheck:                                                                                              ## <-- Fix più visti / votati
        datat = scrapertools.find_single_match(data, '<article.*?class="item movies">.*?<\/div><\/div><\/div>')
        logger.info("[streaminghd.py] blocco"+datat)
        itemp['title'] = '\\2 (\\3)'
        itemp['url'] = '\\1'
        patron = '<article.*?href="([^"]+)".*?alt="([^"]+)".*?wdate">([^"]+)<\/span>'
    elif 'serie' in item.extracheck:                                                                                              ## <-- Fix più serie
        datat = scrapertools.find_single_match(data, '<article.*?class="item tvshows">.*?<\/article><\/div>')

    if not patron: patron = '<article.*?src="([^"\s]+)\s*"\s*alt="([^"]+)".*?\/span> s*([^<]*).*?href="([^"\s]+)\s*".*?span>([^<]+).*?<\/article>'

    itemlist = listtools.list_titles_info(regx=patron, data=datat, itemp=itemp, tipos=tipos)

    i = listtools.next_page(data, '<div.*?pagination.*?href="([^"\s]+)\s*"', 'peliculas')
    if i:
        i.extracheck = item.extracheck
        itemlist.append(i)

    return itemlist


def list_seasons(item):
    logger.info("[streaminghd.py] list_seasons")

    itemlist = listtools.list_seasons(item=item, sdel='<span class="title".*?Stagion.*?<\/span>',
                                      enddel='<\/div><\/div><\/div><\/div>',
                                      epdel={
                                          'regx': '<div\s*class="numerando".*?>([^<]+).*?episodiotitle.*?href="([^"\s]+)\s*">([^<]+)',
                                          'title': '\\1 \\3', 'url': '\\2'})

    return itemlist


def episodios(item):
    logger.info("[streaminghd.py] episodios")

    itemlist = listtools.list_episodes(item=item, data=item.url,
                                       epre={
                                           'regx': '<div\s*class="numerando".*?>([^<]+).*?episodiotitle.*?href="([^"\s]+)\s*">([^<]+)',
                                           'title': '\\1 \\3', 'url': '\\2'})

    return itemlist

def findvideos(item):
    logger.info("[streaminghd.py] findvideos")

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
        videoitem.channel = item.channel

    return itemlist

def search(item, texto):
    logger.info("[streaminghd.py] " + item.url + " search " + texto)
    try:
        if item.extra == "movie":
            item.url = host + "/?s=" + texto
            return peliculas_src(item)
        if item.extra == "tvshow":
            item.url = host + "/serietv/?s=" + texto
            return peliculas_tv_src(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def peliculas_src(item):
    logger.info("kod.streaminghd peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<article><div class="image"><div class="thumbnail animation-2"><a href="([^"]+)">[^=]+=[^=]+="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 extra="movie",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def peliculas_tv_src(item):
    logger.info("kod.streaminghd peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<article><div class="image"><div class="thumbnail animation-2"><a href="([^"]+)">[^=]+=[^=]+="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="episode",
                 extra="tvshow",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def by_anno_or_by_genere(item):
    logger.info("[streaminghd.py] genere")

    if item.url == "": item.url = host

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    if item.extracheck == "by_anno":
        patronvideos = '<li><a href="([^"]+)">([^"]+)<\/a><\/li>'
    elif item.extracheck == "by_genere":
        patronvideos = '<li class="cat-item\s*cat-item.*?href="([^"\s]+)\s*">([^<]+)<\/a>.*?<\/li>'

    itemlist = listtools.list_titles(regx=patronvideos, data=data,
                                     itemp={'title': '\\2', 'url': '\\1', 'action': 'peliculas', 'content': 'list'})

    return itemlist
