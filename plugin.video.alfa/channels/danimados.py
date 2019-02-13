# -*- coding: utf-8 -*-

import re
import base64

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay

host = "https://www.danimados.com/"

list_servers = ['openload',
                'okru',
                'rapidvideo'
                ]
list_quality = ['default']


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="mainpage", title="Categorías", url=host,
                         thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, action="lista", title="Peliculas Animadas", url=host+"peliculas/",
                         thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host + "?s=",
                         thumbnail=thumb_series))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ","+")
    item.url = host + "?s=" + texto
    if texto!='':
       return sub_search(item)


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)class="thumbnail animation-.*?href="([^"]+).*?'
    patron += 'img src="([^"]+).*?'
    patron += 'alt="([^"]+).*?'
    patron += 'class="meta"(.*?)class="contenido"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        scrapedyear = scrapertools.find_single_match(scrapedyear, 'class="year">(\d{4})')
        item.action = "findvideos"
        item.contentTitle = scrapedtitle
        item.contentSerieName = ""
        if "serie" in scrapedurl:
           item.action = "episodios"
           item.contentTitle = ""
           item.contentSerieName = scrapedtitle
        title = scrapedtitle
        if scrapedyear:
            item.infoLabels['year'] = int(scrapedyear)
            title += " (%s)" %item.infoLabels['year']
        itemlist.append(item.clone(thumbnail = scrapedthumbnail,
                                   title = title,
                                   url = scrapedurl
                                  ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def mainpage(item):
    logger.info()
    itemlist = []
    data1 = httptools.downloadpage(item.url).data
    data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data1)
    patron_sec='<ul id="main_header".+?>(.+?)<\/ul><\/div>'
    patron='<a href="([^"]+)">([^"]+)<\/a>'#scrapedurl, #scrapedtitle
    data = scrapertools.find_single_match(data1, patron_sec)
    matches = scrapertools.find_multiple_matches(data, patron)
    if item.title=="Géneros" or item.title=="Categorías":
        for scrapedurl, scrapedtitle in matches:
            if "Películas Animadas"!=scrapedtitle:
                itemlist.append(
                    Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, action="lista"))
        return itemlist
    else:
        for scraped1, scraped2, scrapedtitle in matches:
            scrapedthumbnail=scraped1
            scrapedurl=scraped2
            itemlist.append(
                    Item(channel=item.channel, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, action="episodios",
                         show=scrapedtitle))
        tmdb.set_infoLabels(itemlist)
        return itemlist
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.title=="Peliculas Animadas":
        data_lista = scrapertools.find_single_match(data, 
             '<div id="archive-content" class="animation-2 items">(.*)<a href=\'')
    else:
        data_lista = scrapertools.find_single_match(data, 
             '<div class="items">(.+?)<\/div><\/div><div class=.+?>')
    patron = '<img src="([^"]+)" alt="([^"]+)">.+?<a href="([^"]+)">.+?<div class="texto">(.+?)<\/div>'
    matches = scrapertools.find_multiple_matches(data_lista, patron)
    for scrapedthumbnail,scrapedtitle, scrapedurl, scrapedplot in matches:
        if item.title=="Peliculas Animadas":
            itemlist.append(
                item.clone(title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, contentType="movie", 
                       plot=scrapedplot, action="findvideos", show=scrapedtitle))            
        else:    
            itemlist.append(
                item.clone(title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, 
                       context=autoplay.context,plot=scrapedplot, action="episodios", show=scrapedtitle))
    if item.title!="Peliculas Animadas":
        tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = {}
    data = httptools.downloadpage(item.url).data
    patron = '(?s)<ul class="episodios">(.+?)<span>Compartido'
    data_lista = scrapertools.find_single_match(data,patron)
    contentSerieName = item.title
    patron_caps  = 'href="([^"]+)".*?'
    patron_caps += 'src="([^"]+)".*?'
    patron_caps += 'numerando">([^<]+).*?'
    patron_caps += 'episodiotitle">.*?>([^<]+)'
    matches = scrapertools.find_multiple_matches(data_lista, patron_caps)
    for scrapedurl, scrapedthumbnail, scrapedtempepi, scrapedtitle in matches:
        tempepi=scrapedtempepi.split(" - ")
        if tempepi[0]=='Pel':
            tempepi[0]=0
        title="{0}x{1} - ({2})".format(tempepi[0], tempepi[1].zfill(2), scrapedtitle)
        item.infoLabels["season"] = tempepi[0]
        item.infoLabels["episode"] = tempepi[1]
        itemlist.append(item.clone(thumbnail=scrapedthumbnail,
                        action="findvideos", title=title, url=scrapedurl))
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir " + contentSerieName + " a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", contentSerieName=contentSerieName))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'player-option-\d+.*?'
    patron += 'data-sv="([^"]+).*?'
    patron += 'data-user="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    headers = {"X-Requested-With":"XMLHttpRequest"}
    for scrapedserver, scrapeduser in matches:
        data1 = httptools.downloadpage("https://space.danimados.space/gilberto.php?id=%s&sv=mp4" %scrapeduser).data
        data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data1)
        url = base64.b64decode(scrapertools.find_single_match(data1, '<iframe data-source="([^"]+)"'))
        url1 = devuelve_enlace(url)
        if "drive.google" in url1:
            url1 = url1.replace("view","preview")
        if url1:
            itemlist.append(item.clone(title="Ver en %s",url=url1, action="play"))
    tmdb.set_infoLabels(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.contentType=="movie" and item.contentChannel!='videolibrary':
        itemlist.append(
            item.clone(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                action="add_pelicula_to_library"))
    autoplay.start(itemlist, item)
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]


def devuelve_enlace(url1):
    if 'danimados' in url1:
        url = 'https:' + url1
        new_data = httptools.downloadpage(url).data
        new_data = new_data.replace('"',"'")
        url1 = scrapertools.find_single_match(new_data, "iframe src='([^']+)")
        new_data = httptools.downloadpage(url1).data
        url = scrapertools.find_single_match(new_data, "sources:\s*\[\{file:\s*'([^']+)")
        if "zkstream" in url or "cloudup" in url:
            url1 = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
        else:
            url1 = url
    return url1
