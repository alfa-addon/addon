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
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist


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
        if "Calidad Alta" in quality:
            quality = quality.replace("Calidad Alta", "HQ")
        if " Calidad media - Carga mas rapido" in quality:
            quality = quality.replace(" Calidad media - Carga mas rapido", "360p")
        server = server.lower().strip()
        if "ok" == server:
            server = 'okru'
        itemlist.append(item.clone(url=url, action="play", server=server, contentQuality=quality,
                                   thumbnail=scrapedthumbnail, plot=scrapedplot,
                                   title="Enlace encontrado en %s: [%s]" % (server.capitalize(), quality)))
    for videoitem in itemlist:
        #Nos dice de donde viene si del addon o videolibrary
        if item.contentChannel=='videolibrary':
            videoitem.contentEpisodeNumber=item.contentEpisodeNumber
            videoitem.contentPlot=item.contentPlot
            videoitem.contentSeason=item.contentSeason
            videoitem.contentSerieName=item.contentSerieName
            videoitem.contentTitle=item.contentTitle
            videoitem.contentType=item.contentType
            videoitem.episode_id=item.episode_id
            videoitem.hasContentDetails=item.hasContentDetails
            videoitem.infoLabels=item.infoLabels
            videoitem.thumbnail=item.thumbnail
            #videoitem.title=item.title
    autoplay.start(itemlist, item)
    return itemlist
