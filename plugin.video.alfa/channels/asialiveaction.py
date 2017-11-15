# -*- coding: UTF-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://www.asialiveaction.com"


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="estrenos", title="Estrenos", url=host))
    itemlist.append(Item(channel=item.channel, action="lista", title="Peliculas",
                             url=urlparse.urljoin(host, "p/peliculas.html")))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series",
                         url=urlparse.urljoin(host, "p/series.html")))
    itemlist.append(Item(channel=item.channel, action="category", title="Orden Alfabético", url=host))
    itemlist.append(Item(channel=item.channel, action="category", title="Géneros", url=host))
    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno", url=host))
    #itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "/search?q=")))
    return itemlist


def category(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_generos = "<h2 class='title'>"+item.title+"<\/h2><div class='.+?'><ul class='.+?'><(.+?)><\/ul><\/div>"
    data_generos = scrapertools.find_single_match(data, patron_generos)
    patron = "<a href='(.+?)'>(.+?)<\/a>"
    matches = scrapertools.find_multiple_matches(data_generos, patron)
    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle != 'Próximas Películas':
            itemlist.append(item.clone(action='lista', title=scrapedtitle, url=host+scrapedurl))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return lista(item)

def estrenos(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_estre = "<div class='widget HTML' data-version='1' id='HTML9'><h2 class='title'>(.+?)<\/a><\/li><\/ul>"
    data_estre = scrapertools.find_single_match(data, patron_estre)
    patron = '<i class="([^"]+)"><\/i><div class="calidad">.+?' #serie o peli
    patron +='<img src="([^"]+)"\/>' #scrapedthumbnail
    patron +='<h4>([^"]+)<\/h4>.+?' #scrapedtitle
    patron +='<a href="([^"]+)">'   #scrapedurl
    matches = scrapertools.find_multiple_matches(data_estre, patron)
    for scrapedtype, scrapedthumbnail,scrapedtitle,scrapedurl in matches:
        title = "%s [%s]" % (scrapedtitle, scrapedtype)
        if scrapedtype == "pelicula":
            itemlist.append(item.clone(title=title, url=host+scrapedurl, action="findvideos", extra=scrapedtype,
                            show=scrapedtitle, thumbnail=scrapedthumbnail, contentType="movie",
                            context=["buscar_trailer"]))
        else:
            itemlist.append(item.clone(title=title, url=host+scrapedurl, show=scrapedtitle, 
                            thumbnail=scrapedthumbnail, action="capitulos"))
    return itemlist
def capitulos(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_datos='<div class="output">(.+?)><\/section>'
    data_caps = scrapertools.find_single_match(data, patron_datos)
    patron_caps='<img alt=".+?" src="(.+?)"\/><a href="http:\/\/bit.ly\/(.+?)"'
    matches = scrapertools.find_multiple_matches(data_caps, patron_caps)
    cap=0
    for scrapedthumbnail,scrapedurl in matches:
        link = scrapedurl
        cap=cap+1
        link="http://www.trueurl.net/?q=http%3A%2F%2Fbit.ly%2F"+link+"&lucky=on&Uncloak=Find+True+URL"
        data_other = httptools.downloadpage(link).data
        data_other = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_other)
        patron='<A title="http:\/\/privatelink.de\/\?(.+?)"'
        url = scrapertools.find_single_match(data_other, patron)
        title="%s%s - %s" % (title,str(cap).zfill(2),item.show)
        itemlist.append(item.clone(action='findvideos', title=title, 
                        url=url,show=item.show,thumbnail=scrapedthumbnail))
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                        action="add_serie_to_library", extra="episodios", show=item.show))
    return itemlist

def bitly(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="http:\/\/bit.ly\/(.+?)"'
    link = scrapertools.find_single_match(data, patron)
    link="http://www.trueurl.net/?q=http%3A%2F%2Fbit.ly%2F"+link+"&lucky=on&Uncloak=Find+True+URL"
    data_other = httptools.downloadpage(link).data
    data_other = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_other)
    patron='<A title="http:\/\/privatelink.de\/\?(.+?)"'
    url = scrapertools.find_single_match(data_other, patron)
    if item.contentType=="movie":
        contentType="movie"
    else:
        contentType="serie"
    item=(item.clone(action='findvideos',url=url,show=item.show, thumbnail=item.thumbnail, contentType=contentType))
    return item

def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
   
    patron = '<i class="(.+?)"><\/i>'  # scrapedtype
    patron +='<div class="calidad">(.+?)<\/div>'  # scrapedquality
    patron += '<img src="(.+?)"\/>'  # scrapedthumbnail
    patron += '<h4>(.+?)<\/h4>'  # scrapedtitle
    patron += "<h5>(.+?)<\/h5>"  # scrapedyear
    patron += '<a href="(.+?)"'  # scrapedurl
    #patron += "<\/a>.+?<div class='item-snippet'>(.+?)<"  # scrapedplot
    if item.title!="Prueba":
        pat='<div id="tab-1"><ul class="post-gallery">(.+?)<\/ul><\/div>'
        data=scrapertools.find_single_match(data, pat)
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtype,scrapedquality,scrapedthumbnail,scrapedtitle,scrapedyear,scrapedurl in matches:
        patron_quality="<span>(.+?)</span>"
        quality = scrapertools.find_multiple_matches(scrapedquality, patron_quality)
        qual=""
        for calidad in quality:
            qual=qual+"["+calidad+"] "
        title="%s [%s] %s" % (scrapedtitle,scrapedyear,qual)
        if item.title =="Series":
            itemlist.append(item.clone(title=title, url=host+scrapedurl, extra=scrapedtitle, plot=scrapedtitle,
                           show=scrapedtitle, thumbnail=scrapedthumbnail, contentType="serie", action="capitulos"))
        elif scrapedtype != 'serie':
            itemlist.append(
                item.clone(title=title, url=host+scrapedurl, action="findvideos", extra=scrapedtype, plot=scrapedtitle,
                           show=scrapedtitle, thumbnail=scrapedthumbnail, contentType="movie", context=["buscar_trailer"]))

    # Paginacion
    patron_genero = '<h1>([^"]+)<\/h1>'
    genero = scrapertools.find_single_match(data, patron_genero)
    if genero == "Romance" or genero == "Drama":
        patron = "<a rel='nofollow' class=previouspostslink' href='([^']+)'>Siguiente "
    else:
        patron = "<span class='current'>.+?href='(.+?)'>"

    next_page_url = scrapertools.find_single_match(data, patron)

    if next_page_url != "":
        item.url = next_page_url
        itemlist.append(Item(channel=item.channel, action="lista", title=">> Página siguiente", url=next_page_url,
                             thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []

    if item.extra == 'pelicula':
        item = bitly(item)

    data = httptools.downloadpage(item.url).data
    itemlist.extend(servertools.find_video_items(data=data))
    show = item.show
    for videoitem in itemlist:
        videoitem.channel = item.channel
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.contentType=="movie" and item.contentChannel!='videolibrary':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=show))

    return itemlist
