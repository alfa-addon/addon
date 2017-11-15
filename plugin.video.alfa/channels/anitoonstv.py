# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload',
                'okru',
                'netutv',
                'rapidvideo'
                ]
list_quality = ['default']


host = "http://www.anitoonstv.com"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, action="lista", title="Anime", url=host,
                         thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series Animadas", url=host,
                         thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host,
                         thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, action="lista", title="Pokemon", url=host,
                         thumbnail=thumb_series))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if 'Novedades' in item.title:
        patron_cat = '<div class="activos"><h3>(.+?)<\/h2><\/a><\/div>'
        patron = '<a href="(.+?)"><h2><span>(.+?)<\/span>'
    else:
        patron_cat = '<li><a href=.+?>'
        patron_cat += str(item.title)
        patron_cat += '<\/a><div>(.+?)<\/div><\/li>'
        patron = "<a href='(.+?)'>(.+?)<\/a>"
    data = scrapertools.find_single_match(data, patron_cat)

    matches = scrapertools.find_multiple_matches(data, patron)
    for link, name in matches:
        if "Novedades" in item.title:
            url = link
            title = name.capitalize()
        else:
            url = host + link
            title = name
        if ":" in title:
            cad = title.split(":")
            show = cad[0]
        else:
            if "(" in title:
                cad = title.split("(")
                if "Super" in title:
                    show = cad[1]
                    show = show.replace(")", "")
                else:
                    show = cad[0]
            else:
                show = title
                if "&" in show:
                    cad = title.split("xy")
                    show = cad[0]
        context1=[renumbertools.context(item), autoplay.context]
        itemlist.append(
            item.clone(title=title, url=url, plot=show, action="episodios", show=show,
                       context=context1))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="pagina">(.+?)<\/div><div id="fade".+?>'
    data = scrapertools.find_single_match(data, patron)
    patron_caps = "<a href='(.+?)'>Capitulo: (.+?) - (.+?)<\/a>"
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    show = scrapertools.find_single_match(data, '<span>Titulo.+?<\/span>(.+?)<br><span>')
    scrapedthumbnail = scrapertools.find_single_match(data, "<img src='(.+?)'.+?>")
    scrapedplot = scrapertools.find_single_match(data, '<span>Descripcion.+?<\/span>(.+?)<br>')
    i = 0
    temp = 0
    for link, cap, name in matches:
        if int(cap) == 1:
            temp = temp + 1
        if int(cap) < 10:
            cap = "0" + cap
        season = temp
        episode = int(cap)
        season, episode = renumbertools.numbered_for_tratk(
            item.channel, item.show, season, episode)
        date = name
        title = "%sx%s %s (%s)" % (season, str(episode).zfill(2), "Episodio %s" % episode, date)
        # title = str(temp)+"x"+cap+"  "+name
        url = host + "/" + link
        if "NO DISPONIBLE" not in name:
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, thumbnail=scrapedthumbnail,
                                 plot=scrapedplot, url=url, show=show))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def googl(url):
    logger.info()
    a=url.split("/")
    link=a[3]
    link="http://www.trueurl.net/?q=http%3A%2F%2Fgoo.gl%2F"+link+"&lucky=on&Uncloak=Find+True+URL"
    data_other = httptools.downloadpage(link).data
    data_other = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data_other)
    patron='<td class="withbg">Destination URL<\/td><td><A title="(.+?)"'
    trueurl = scrapertools.find_single_match(data_other, patron)
    return trueurl

def findvideos(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data1 = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data_vid = scrapertools.find_single_match(data1, '<div class="videos">(.+?)<\/div><div .+?>')

    # name = scrapertools.find_single_match(data,'<span>Titulo.+?<\/span>([^<]+)<br>')
    scrapedplot = scrapertools.find_single_match(data, '<br><span>Descrip.+?<\/span>([^<]+)<br>')
    scrapedthumbnail = scrapertools.find_single_match(data, '<div class="caracteristicas"><img src="([^<]+)">')
    itemla = scrapertools.find_multiple_matches(data_vid, '<div class="serv">.+?-(.+?)-(.+?)<\/div><.+? src="(.+?)"')
    for server, quality, url in itemla:
        if "HQ" in quality:
            quality = "HD"
        if "Calidad Alta" in quality:
            quality = "HQ"
        if " Calidad media - Carga mas rapido" in quality:
            quality = "360p"
        server = server.lower().strip()
        if "ok" in server:
            server = 'okru'
        if "rapid" in server:
            server = 'rapidvideo'
        if "netu" in server:
            server = 'netutv'
            url = googl(url)
        itemlist.append(item.clone(url=url, action="play", server=server, contentQuality=quality,
                                   thumbnail=scrapedthumbnail, plot=scrapedplot,
                                   title="Enlace encontrado en: %s [%s]" % (server.capitalize(), quality)))
    
    autoplay.start(itemlist, item)
    return itemlist
