# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# *AddonNamer* - XBMC Plugin
# Canale per altadefinizione01
# ------------------------------------------------------------
import re
import urlparse

from channels import autoplay
from channels import filtertools
from core import scrapertools, servertools, httptools, tmdb, scrapertoolsV2
from core.item import Item
from platformcode import logger, config

#URL che reindirizza sempre al dominio corrente
host = "https://altadefinizione01.to"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'rapidvideo', 'streamcherry', 'megadrive']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'altadefinizione01')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'altadefinizione01')

headers = None
blacklist_categorie = ['Altadefinizione01', 'Altadefinizione.to']


def mainlist(item):
    logger.info("kod.altadefinizione01 mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     title="[COLOR azure]In sala[/COLOR]",
                     action="sala",
                     url="%s/page/1/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Ultimi film inseriti[/COLOR]",
                     action="peliculas",
                     url="%s/page/1/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Sub ITA[/COLOR]",
                     action="subIta",
                     url="%s/sub-ita/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR azure]Categorie film[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("kod.altadefinizione01 newest" + categoria)
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


def createItem(data, item, itemlist, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedquality, subDiv, subText):
    info = scrapertoolsV2.find_multiple_matches(data, '<span class="ml-label">([0-9]+)+<\/span>.*?<span class="ml-label">(.*?)<\/span>.*?<p class="ml-cat".*?<p>(.*?)<\/p>.*?<a href="(.*?)" class="ml-watch">')
    infoLabels = {}
    for infoLabels['year'], duration, scrapedplot, checkUrl in info:
        if checkUrl == scrapedurl:
            break

    infoLabels['duration'] = int(duration.replace(' min', '')) * 60  # calcolo la durata in secondi
    scrapedthumbnail = host + scrapedthumbnail
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
    fulltitle = scrapedtitle
    if subDiv:
        fulltitle += ' (' + subText + ')'
    fulltitle += ' [' + scrapedquality.strip() + ']'

    itemlist.append(
        Item(channel=item.channel,
             action="findvideos",
             text_color="azure",
             contentType="movie",
             contentTitle=scrapedtitle,
             contentQuality=scrapedquality.strip(),
             plot=scrapedplot,
             title=fulltitle,
             url=scrapedurl,
             infoLabels=infoLabels,
             thumbnail=scrapedthumbnail))


def sala(item):
    logger.info("kod.altadefinizione01 peliculas")
    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # The categories are the options for the combo
    patron = '<div class="ml-mask">.*?<div class="cover_kapsul".*?<a href="(.*?)">.*?<img .*?src="(.*?)".*?alt="(.*?)".*?<div class="trdublaj">(.*?)<\/div>.(<div class="sub_ita">(.*?)<\/div>|())'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedquality, subDiv, subText, empty in matches:
        createItem(data, item, itemlist, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedquality, subDiv, subText)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def subIta(item):
    logger.info("kod.altadefinizione01 subita")
    return peliculas(item, sub=True)


def peliculas(item, sub=False):
    logger.info("kod.altadefinizione01 peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data

    # The categories are the options for the combo
    patron = '<div class="cover_kapsul ml-mask".*?<a href="(.*?)">(.*?)<\/a>.*?<img .*?src="(.*?)".*?<div class="trdublaj">(.*?)<\/div>.(<div class="sub_ita">(.*?)<\/div>|())'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedquality, subDiv, subText, empty in matches:
        if sub or not subDiv:
            createItem(data, item, itemlist, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedquality, subDiv, subText)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginazione 
    patronvideos = '<span>[^<]+</span>[^<]+<a href="(.*?)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        action = "peliculas" if not sub else "subIta"
        itemlist.append(
            Item(channel=item.channel,
                 action=action,
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def categorias(item):
    logger.info("kod.altadefinizione01 categorias")
    itemlist = []

    # data = scrapertools.cache_page(item.url)
    data = httptools.downloadpage(item.url, headers=headers).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data, '<ul class="kategori_list">(.*?)</ul>')

    # The categories are the options for the combo
    patron = '<li><a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        if not scrapedtitle in blacklist_categorie:
            scrapedurl = host + scrapedurl
            itemlist.append(
                Item(channel=item.channel,
                     action="subIta",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png",
                     folder=True))

    return itemlist


def search(item, texto):
    logger.info("[altadefinizione01.py] " + item.url + " search " + texto)
    item.url = "%s/index.php?do=search&story=%s&subaction=search" % (
        host, texto)
    try:
        if item.extra == "movie":
            return subIta(item)
        if item.extra == "tvshow":
            return peliculas_tv(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info("[altadefinizione01.py] findvideos")

    # Carica la pagina
    if item.contentType == "episode":
        data = item.url
    else:
        data = httptools.downloadpage(item.url, headers=headers).data

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


""" def peliculas_tv(item):
    logger.info("kod.altadefinizionezone peliculas")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<section class="main">(.*?)</section>'
    data = scrapertools.find_single_match(data, patron)

    # Estrae i contenuti 
    patron = '<h2 class="titleFilm"><a href="([^"]+)">(.*?)</a></h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="seasons",
                 fulltitle=scrapedtitle,
                 contentType='tv',
                 contentTitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 folder=True))

    tmdb.set_infoLabels(itemlist)

    # Paginazione 
    patronvideos = '<span>.*?</span>.*?href="(.*?)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if matches:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas_tv",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def seasons(item):
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = '<li><a href="([^"]+)" data-toggle="tab">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedseason in matches:
        scrapedurl = item.url + scrapedurl
        scrapedtitle = item.title

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]" + " " + "Stagione " + scrapedseason,
                 url=scrapedurl,
                 thumbnail=item.scrapedthumbnail,
                 plot=item.scrapedplot,
                 folder=True))

    return itemlist


def episodios(item):
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    patron = 'class="tab-pane fade" id="%s">(.*?)class="tab-pane fade"' % item.url.split('#')[1]
    bloque = scrapertools.find_single_match(data, patron)
    patron = 'class="text-muted">.*?<[^>]+>(.*?)<[^>]+>[^>]+>[^>][^>]+>[^<]+<a href="#" class="slink" id="megadrive-(.*?)" data-link="(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedtitle, scrapedepi, scrapedurl in matches:
        scrapedthumbnail = ""
        scrapedplot = ""
        scrapedepi = scrapedepi.split('_')[0] + "x" + scrapedepi.split('_')[1].zfill(2)
        scrapedtitle = scrapedepi + scrapertools.decodeHtmlentities(scrapedtitle)

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

    return itemlist """
