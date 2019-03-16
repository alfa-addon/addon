# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per cinemasubito
# ------------------------------------------------------------
import binascii, re, urlparse

from channels import autoplay, filtertools
from core import httptools, scrapertools, servertools, tmdb
from core.item import Item
from lib import jscrypto
from platformcode import config, logger




host = "http://www.cinemasubito.org"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'youtube']
list_quality = ['HD', 'SD']


__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'cinemasubito')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'cinemasubito')

headers = [
    ['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0'],
    ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Accept-Language', 'en-US,en;q=0.5'],
    ['Host', host.replace("http://", "")],
    ['DNT', '1'],
    ['Upgrade-Insecure-Requests', '1'],
    ['Connection', 'keep-alive'],
    ['Referer', host],
    ['Cache-Control', 'max-age=0']
]


def mainlist(item):
    logger.info("kod.cinemasubito mainlist")

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]Film[/COLOR]",
                     action="peliculas",
                     url="%s/film/pagina/1" % host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Film Per Categoria[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     title="[COLOR azure]Serie TV[/COLOR]",
                     action="peliculas_tv",
                     url="%s/serie" % host,
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca Serie TV...[/COLOR]",
                     action="search",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info("kod.cinemasubito " + item.url + " search " + texto)
    item.url = host + "/cerca/" + texto
    try:
        if item.extra == "movie":
            return peliculas(item)
        if item.extra == "tvshow":
            return peliculas_tv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.get_match(data, '<h4>Genere</h4>(.*?)<li class="genre">')

    # Estrae i contenuti 
    patron = r'<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("Film genere ", "")
        itemlist.append(
            Item(
                channel=item.channel,
                action="peliculas",
                title=scrapedtitle,
                url=scrapedurl,
                thumbnail=
                "https://farm8.staticflickr.com/7562/15516589868_13689936d0_o.png",
                folder=True))

    return itemlist


def peliculas(item):
    logger.info("kod.cinemasubito peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<a href="([^"]+)" title="([^"]+)">\s*<div class="wrt">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        # qualità e linguaggio possono essere inseriti nell' item in modo che siano mostrati nei titoli intelligenti
        quality = ''
        scrapedplot = ""
        scrapedthumbnail = ""
        quality = scrapertools.find_single_match(scrapedtitle, r'\[(.*?)\]')
        year = scrapertools.find_single_match(scrapedtitle, r'\((.*?)\)')
        title = scrapertools.find_single_match(scrapedtitle, r'(.*?)(?:\(|\[)')
        title = '%s [%s] (%s)' % (title, quality, year)

        # Il contentTitle deve essere semplice senza nessun altro dettaglio come anno,qualità etc.
        # deve esserci solo un tipo di content, o contentTitle o contentSerieName

        contentTitle = scrapertools.find_single_match(scrapedtitle, r'(.*?)(?:\(|\[)')

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentTitle=contentTitle,
                 quality=quality,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR] ",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 extra=item.extra,
                 infoLabels={'year':year}))
                 

    # Con questo si ricavano le informazioni da tmdb per tutti elementi di itemlist
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='it')

    # Paginazione 
    patronvideos = r'<a href="[^"]+"[^d]+data-ci-pagination-page[^>]+>[^<]+<\/a><\/span>[^=]+="([^"]+)"'
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

    return itemlist


def peliculas_tv(item):
    logger.info("kod.cinemasubito peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # Estrae i contenuti 
    patron = r'<a href="([^"]+)" title="([^"]+)">\s*<div class="wrt">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        quality = ''
        scrapedplot = ''
        scrapedthumbnail = ''
        quality = scrapertools.find_single_match(scrapedtitle, r'\[(.*?)\]')
        year = scrapertools.find_single_match(scrapedtitle, r'\((.*?)\)')
        title = scrapertools.find_single_match(scrapedtitle, r'(.*?)(?:\(|\[)')
        title = '%s [%s] (%s)' % (title, quality, year)

        # Il contentTitle deve essere semplice senza nessun altro dettaglio come anno,qualità etc.
        # deve esserci solo un tipo di content, o contentTitle o contentSerieName

        contentSerieName = scrapedtitle
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentSerieName=contentSerieName,
                 quality=quality,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 show=scrapedtitle,
                 extra=item.extra))
        
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    # Paginazione 
    patronvideos = r'<a href="[^"]+"[^d]+data-ci-pagination-page[^>]+>[^<]+<\/a><\/span>[^=]+="([^"]+)"'
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

    return itemlist


def episodios(item):
    logger.info("kod.channels.cinemasubito episodios")

    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    patron = r'href="([^"]+)"><span class="glyphicon glyphicon-triangle-right"></span>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        if host not in scrapedurl:
            scrapedurl = host + scrapedurl
        else:
            scrapedurl = scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    # Comandi di servizio
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
    logger.info("kod.cinemasubito findvideos_tv")

    links = set()
    data = httptools.downloadpage(item.url, headers=headers).data
    p = scrapertools.find_single_match(data, r'var decrypted = CryptoJS\.AES\.decrypt\(vlinkCrypted, "([^"]+)",')
    urls = scrapertools.find_multiple_matches(data,
                                              r"<li><a rel=[^t]+target=[^c]+class=[^=]+=[^:]+:'(.*?)'[^:]+:'(.*?)'[^:]+:'(.*?)'")
    for url, iv, salt in urls:
        salt = binascii.unhexlify(salt)
        iv = binascii.unhexlify(iv)
        url = jscrypto.decode(url, p, iv=iv, salt=salt)
        url = url.replace(r'\/', '/')
        links.add(url)

    itemlist = servertools.find_video_items(data=str(links) + data)
    for videoitem in itemlist:
        videoitem.title = item.title + videoitem.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.show = item.show
        videoitem.plot = item.plot
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


