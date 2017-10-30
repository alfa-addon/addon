# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay

host = "http://www.danimados.com/"

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
    itemlist.append(Item(channel=item.channel, action="mainpage", title="Más Populares", url=host,
                         thumbnail=thumb_series))
    #itemlist.append(Item(channel=item.channel, action="movies", title="Peliculas Animadas", url=host,
    #                     thumbnail=thumb_series))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


"""
def search(item, texto):
    logger.info()
    texto = texto.replace(" ","+")
    item.url = item.url+texto
    if texto!='':
       return lista(item)
"""


def mainpage(item):
    logger.info()

    itemlist = []

    data1 = httptools.downloadpage(item.url).data
    data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data1)
    if item.title=="Más Populares":
        patron_sec='<a class="lglossary" data-type.+?>(.+?)<\/ul>'
        patron='<img .+? src="([^"]+)".+?<a href="([^"]+)".+?>([^"]+)<\/a>' #scrapedthumbnail, #scrapedurl, #scrapedtitle
    if item.title=="Categorías":
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
    data_lista = scrapertools.find_single_match(data, '<div class="items">(.+?)<\/div><\/div><div class=.+?>')
    patron = '<img src="([^"]+)" alt="([^"]+)">.+?<a href="([^"]+)">.+?<div class="texto">(.+?)<\/div>'
    #scrapedthumbnail,#scrapedtitle, #scrapedurl, #scrapedplot
    matches = scrapertools.find_multiple_matches(data_lista, patron)
    for scrapedthumbnail,scrapedtitle, scrapedurl, scrapedplot in matches:
        itemlist.append(
            item.clone(title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, 
                       context=autoplay.context,plot=scrapedplot, action="episodios", show=scrapedtitle))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
   
    data_lista = scrapertools.find_single_match(data,
                      '<ul class="episodios">(.+?)<\/ul><\/div><\/div><\/div>')
    show = item.title
    patron_caps = '<img src="([^"]+)"><\/a><\/div><div class=".+?">([^"]+)<\/div>.+?<a .+? href="([^"]+)">([^"]+)<\/a>'
    #scrapedthumbnail,#scrapedtempepi, #scrapedurl, #scrapedtitle
    matches = scrapertools.find_multiple_matches(data_lista, patron_caps)
    for scrapedthumbnail, scrapedtempepi, scrapedurl, scrapedtitle in matches:
        tempepi=scrapedtempepi.split(" - ")
        if tempepi[0]=='Pel':
            tempepi[0]=0
        title="{0}x{1} - ({2})".format(tempepi[0], tempepi[1].zfill(2), scrapedtitle)
        itemlist.append(Item(channel=item.channel, thumbnail=scrapedthumbnail,
                        action="findvideos", title=title, url=scrapedurl, show=show))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR blue]Añadir " + show + " a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))


    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data, 
                      '<div id="playex" .+?>(.+?)<\/nav><\/div><\/div>')
    patron='src="(.+?)"'
    itemla = scrapertools.find_multiple_matches(data,patron)
    for i in range(len(itemla)):
        #for url in itemla:
        url=itemla[i]
        #verificar existencia del video (testing)
        codigo=verificar_video(itemla[i])
        if codigo==200:
            if "ok.ru" in url:
                server='okru'
            else:
                server=''
            if "openload" in url:
                server='openload'
            if "google" in url:
                server='gvideo'
            if "rapidvideo" in url:
                server='rapidvideo'
            if "streamango" in url:
                server='streamango'
            if server!='':
                title="Enlace encontrado en %s " % (server.capitalize())
            else:
                title="NO DISPONIBLE"
            if title!="NO DISPONIBLE":
                itemlist.append(item.clone(title=title,url=url, action="play", server=server))
            
    autoplay.start(itemlist, item)
    return itemlist


def verificar_video(url):
    codigo=httptools.downloadpage(url).code
    if codigo==200:
        # Revise de otra forma
        data=httptools.downloadpage(url).data
        removed = scrapertools.find_single_match(data,'removed(.+)')
        if len(removed) != 0:
            codigo1=404
        else:
            codigo1=200
    else:
		codigo1=200
    return codigo1
