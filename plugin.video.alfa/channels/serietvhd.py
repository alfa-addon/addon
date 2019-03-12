# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per serietvhd
# https://alfa-addon.com/categories/kod-addon.50/
# ----------------------------------------------------------
import re  
import urlparse

from core import httptools
from platformcode import logger, config
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb



host = "https://serietvhd.stream"

headers = [['Referer', host]]

def mainlist(item):
    logger.info("[serietvhd.py] mainlist")

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="lista_serie",
                     title="[COLOR azure]Serie Tv[/COLOR]",
                     url="%s/serietv/" % host,
                     extra="serietv",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_serie",
                     title="[COLOR azure]Piu Popolari[/COLOR]",
                     url="%s/piu-popolari/" % host,
                     extra="piu-popolari",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_serie",
                     title="[COLOR azure]Piu Votati[/COLOR]",
                     url="%s/piu-votati/" % host,
                     extra="piu-votati",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="by_anno_or_by_genere",
                     title="[COLOR azure]Genere[/COLOR]",
                     url="%s/serietv/" % host,
                     extra="by_genere",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="by_anno_or_by_genere",
                     title="[COLOR azure]Anno di Rilascio[/COLOR]",
                     url="%s/serietv/" % host,
                     extra="by_anno",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),					 
                #Item(channel=item.channel,
                #     action="topimdb",
                #     title="[COLOR azure]Top IMDB[/COLOR]",
                #     url="%s/top-imdb/" % host,
                #     extra="topimdb",
                #     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                 Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     url="%s/serietv/" % host,
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),					 ]

    return itemlist
    
def lista_serie(item):
    logger.info("[serietvhd.py] lista_serie ")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    #salvo il valore originale per eventuali usi futuri
    dataoriginale=data
    if item.extra=="serietv":
        data = scrapertools.find_single_match(data, '<div id="archive-content" class="animation-2 items">.*?</article></div>')

    patronvideos = '<article id.*?src="([^"]+)" alt="([^"]+)".*?href="([^"]+)">.*?</article>'

    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    
    for match in matches:

        scrapedthumbnail = urlparse.urljoin(item.url, match.group(1))
        scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
        scrapedtitle = scrapertools.unescape(match.group(2)).replace("[", "").replace("]", "")
        scrapedurl = urlparse.urljoin(item.url, match.group(3))
        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 contentType="serietv",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot"))

    next_page = scrapertools.find_single_match(dataoriginale, '<div class="pagination">.*?href="([^"]+)".*?</div>')
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url="%s" % next_page,
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def serietv(item):
    logger.info("[serietvhd.py] serietv")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    dataoriginale=data

    #estraggo i div contenenti le stagioni in un array
    matches = scrapertools.find_multiple_matches(data, '<div class="se-c">.*?</div></div>')

    for match in matches:
        """#per ogni stagione estraggo il numero di stagione
        stagione = scrapertools.find_single_match(match, '<div class="se-q">.*?"title">([^<]+).*?</div>')
        itemlist.append(
            Item(channel=item.channel,
                 action="",
                 contentType="serietv",
                 fulltitle=stagione,
                 show=stagione,
                 title="[COLOR yellow]%s[/COLOR]" % stagione,
                 viewmode="movie_with_plot"))"""

        #estraggo gli episodi della singola stagione
        patronvideos = '<li>.*?src="([^"]+)".*?"numerando">([^<]+).*?href="([^"]+)">([^<]+).*?"date">([^<]+).*?</li>'

        matches2 = re.compile(patronvideos, re.DOTALL).finditer(match)
        
        for match2 in matches2:
            scrapedthumbnail = urlparse.urljoin(item.url, match2.group(1))
            scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
            episodio = scrapertools.unescape(match2.group(2))
            scrapedurl = urlparse.urljoin(item.url, match2.group(3))
            scrapedtitle = scrapertools.unescape(match2.group(4))
            data = scrapertools.unescape(match2.group(5))
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="movie",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title="["+episodio +"] "+scrapedtitle + " ["+data+"]",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     extra=item.extra,
                     viewmode="movie_with_plot") )

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                url=item.url,
                action="add_serie_to_library",
                extra="serietv",
                show=item.show))

    return itemlist

def by_anno_or_by_genere(item):
    logger.info("[serietvhd.py] genere")
    itemlist = []

    if item.url == "":
        item.url = host

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    if item.extra=="by_anno":
        patronvideos = '<li><a href="([^"]+)">([^"]+)</a></li>'
    elif item.extra=="by_genere":
        patronvideos = '<li id="menu-item.*?genres.*?<a href="([^"]+)">([^<]+)</a></li>'

    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url, match.group(1))
        scrapedtitle = match.group(2)
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    return itemlist

def topimdb(item):
    logger.info("[serietvhd.py] topimdb")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    #salvo il valore originale per eventuali usi futuri
    dataoriginale=data

    patronvideos = '<div class="top-imdb-item".*?href="([^"]+)".*?src="([^"]+)".*?"puesto">([^<]+)<.*?"rating">([^<]+)<.*?>([^<]+)</a></div></div>'

    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url, match.group(1))
        scrapedthumbnail = urlparse.urljoin(item.url, match.group(2))
        scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
        posizione = scrapertools.unescape(match.group(3))
        voto = scrapertools.unescape(match.group(4))
        scrapedurl = scrapertools.unescape(match.group(5))
        scrapedtitle = scrapertools.unescape(match.group(6))

        itemlist.append(
            Item(channel=item.channel,
                 action="serietv",
                 contentType="serietv",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 viewmode="movie_with_plot"))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    try:
        item.url = host + "/?s=" + texto
        itemlist = []

        # Carica la pagina 
        data = httptools.downloadpage(item.url, headers=headers).data
        
        patronvideos = '<div class="result-item">.*?href="([^"]+)">.*?src="([^"]+)".*?alt="([^"]+)".*?</div>'

        matches = re.compile(patronvideos, re.DOTALL).finditer(data)
        
        for match in matches:
            scrapedurl = urlparse.urljoin(item.url, match.group(1))
            scrapedthumbnail = urlparse.urljoin(item.url, match.group(2))
            scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
            scrapedtitle = scrapertools.unescape(match.group(3))
            itemlist.append(
                Item(channel=item.channel,
                     action="serietv",
                     contentType="movie",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title=scrapedtitle.replace("[", "").replace("]", ""),
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     extra=item.extra,
                     viewmode="movie_with_plot"))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        return itemlist
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
		
def findvideos(item):
    logger.info("[serietvhd.py] findvideos")

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist
