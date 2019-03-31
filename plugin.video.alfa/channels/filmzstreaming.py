# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per filmzstreaming
# ----------------------------------------------------------
import re, urlparse, urllib

from platformcode import logger, config
from channels import autoplay
from channels import filtertools
from core import scrapertools, servertools, httptools
from core.item import Item
from core import tmdb



host = "https://filmzstreaming.blue"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'youtube']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmzstreaming')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmzstreaming')

headers = [['Referer', host]]

def mainlist(item):
    logger.info("kod.filmzstreaming mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Ultimi film inseriti[/COLOR]",
                     action="peliculas",
                     extra="movie",
                     url="%s/film/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie film[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     action="peliculas_tv",
                     extra="tvshow",
                     url="%s/serietv/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def peliculas(item):
    logger.info("kod.filmzstreaming peliculas")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, '</h1>(.*?)<div class="sidebar scrolling">')

    # Estrae i contenuti
    patron = r'<h3><a href="([^"]+)">(.*?)</a></h3>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace("Streaming ", "")

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    # Paginazione
    patronvideos = '<span class="current">[^>]+</span><a href=\'(.*?)\' class="inactive">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def peliculas_tv(item):
    logger.info("kod.filmzstreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    blocco = scrapertools.find_single_match(data, '</h1>(.*?)<div class="sidebar scrolling">')

    # Estrae i contenuti 
    patron = r'<h3><a href="([^"]+)">(.*?)</a></h3>'
    matches = re.compile(patron, re.DOTALL).findall(blocco)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace(" Streaming", "")
        scrapedtitle = scrapedtitle.title()

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    # Paginazione
    patronvideos = '<span class="current">[^>]+</span><a href=\'(.*?)\' class="inactive">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    logger.info("kod.filmzstreaming peliculas_tv")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<div class="numerando">(.*?)</div><div class="episodiotitle"> <a href="([^"]+)">(.*?)</a> '
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scraped_1, scrapedurl, scraped_2 in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scraped_1 + " " + scraped_2

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 extra=item.extra,
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    # Comandi di servizio
    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def peliculas_src_tv(item):
    logger.info("kod.filmzstreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<div class="title">\s*<a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace("Streaming ", "")

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="tv",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    # Paginazione
    patronvideos = '<span class="current">[^>]+</span><a href=\'(.*?)\' class="inactive">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_src_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def peliculas_src(item):
    logger.info("kod.filmzstreaming peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = '<div class="title">\s*<a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedtitle = scrapedtitle.replace("Streaming ", "")

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail))

    # Paginazione
    patronvideos = '<span class="current">[^>]+</span><a href=\'(.*?)\' class="inactive">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_src",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def categorias(item):
    logger.info("kod.filmzstreaming categorias")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data, '<ul class="sub-menu">(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                 folder=True))

    return itemlist

def search(item, texto):
    logger.info("[filmzstreaming.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        if item.extra == "movie":
            return peliculas_src(item)
        if item.extra == "tvshow":
            return peliculas_src_tv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def findvideos(item):
    logger.info("[filmzstreaming.py] findvideos")

    # Carica la pagina 

    if item.contentType == 'episode':
        data = httptools.downloadpage(item.url).data
        patron = '<li id=[^=]+="dooplay_player_option[^=]+="([^"]+)" data-nume="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for posts, numes in matches:
            uri = "%s/wp-admin/admin-ajax.php" % host
            payload = urllib.urlencode({'action': 'doo_player_ajax', 'post': posts, 'nume': numes})
            data += httptools.downloadpage(uri, post=payload).data
    else:
        data = httptools.downloadpage(item.url).data
        patron = '<span class="loader"></span></li><li id=[^=]+="dooplay_player_[^=]+="([^"]+)" data-nume="([^"]+)">'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for posts, numes in matches:
            uri = "%s/wp-admin/admin-ajax.php" % host
            payload = urllib.urlencode({'action': 'doo_player_ajax', 'post': posts, 'nume': numes})
            data += httptools.downloadpage(uri, post=payload).data
        
            #import requests
            #payload = {'action': 'doo_player_ajax', 'post': posts, 'nume': numes}
            #req = requests.post(uri, data=payload)
            #data += str(req.text)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
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

