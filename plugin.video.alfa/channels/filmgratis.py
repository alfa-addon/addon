# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per filmgratis
# ------------------------------------------------------------
import re, urlparse

from platformcode import logger,config
from core import scrapertools, httptools, servertools, tmdb
from core.item import Item
from channels import autoplay
from channels import filtertools



IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'vidoza', 'youtube']
list_quality = ['HD', 'SD']


__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmgratis')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmgratis')

host = "https://www.filmgratis.one"

# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info("kod.filmgratis mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title=color("Home", "orange"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="annoattuale",
                     title=color("Film di quest'anno", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="categorie",
                     title=color("Categorie", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peranno",
                     title=color("Per anno", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="perpaese",
                     title=color("Per paese", "azure"),
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title=color("Cerca ...", "yellow"),
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def search(item, texto):
    logger.info("filmgratis.py Search ===> " + texto)
    item.url = "%s/index.php?story=%s&do=search&subaction=search" % (host, texto)
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    logger.info("filmgratis " + categoria)
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

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def annoattuale(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<div class="left-menu-main">(.*?)</div>')
    patron = r'<a href="([^"]+)">Film\s*\d{4}</a>'

    item.url = urlparse.urljoin(host, scrapertools.find_single_match(blocco, patron))
    return peliculas(item)

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def categorie(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<div class="menu-janr-content">(.*?)</div>')
    patron = r'<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        if 'film erotici' in scrapedtitle.lower(): continue
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 text_color="azure",
                 url=urlparse.urljoin(host, scrapedurl),
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def peranno(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<div class="sort-menu-title">\s*Anno di pubblicazione:\s*</div>(.*?)</div>')
    patron = r'<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 text_color="azure",
                 url=urlparse.urljoin(host, scrapedurl),
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def perpaese(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.get_match(data, r'<div class="sort-menu-title">\s*Paesi di produzione:\s*</div>(.*?)</div>')
    patron = r'<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=scrapedtitle,
                 text_color="azure",
                 url=urlparse.urljoin(host, scrapedurl),
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)".*?/></a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        year = scrapertools.find_single_match(scrapedtitle, r'\((\d{4})\)')

        html = httptools.downloadpage(scrapedurl).data

        patron = r'<div class="video-player-plugin">([\s\S]*)<div class="wrapper-plugin-video">'
        matches = re.compile(patron, re.DOTALL).findall(html)
        for url in matches:
            if "scrolling" in url:
                scrapedurl = scrapedurl

            cleantitle = scrapedtitle
            
            year = scrapertools.find_single_match(scrapedtitle, r'\((\d{4})\)')
            infolabels = {}
            if year:
                cleantitle = cleantitle.replace("(%s)" % year, '').strip()
                infolabels['year'] = year

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="movie",
                     title=scrapedtitle.replace(year, color("%s" % year, "red")),
                     fulltitle=cleantitle,
                     text_color="azure",
                     url=scrapedurl,
                     extra="movie",
                     show=cleantitle,
                     thumbnail=scrapedthumbnail,
                     infoLabels=infolabels,
                     folder=True))
                     
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagine
    patronvideos = r'<a href="([^"]+)">>'
    next_page = scrapertools.find_single_match(data, patronvideos)

    if next_page:
        scrapedurl = urlparse.urljoin(item.url, next_page)
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 extra=item.extra,
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[%s] " % color(server.capitalize(), 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        videoitem.language = IDIOMAS['Italiano']

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def color(text, color):
    return "[COLOR "+color+"]"+text+"[/COLOR]"

# ================================================================================================================
