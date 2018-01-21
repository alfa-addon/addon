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

    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=host+"/lista-de-anime.php",
                         thumbnail=thumb_series))
    #itemlist.append(Item(channel=item.channel, action="lista", title="Series Animadas", url=host,
    #                     thumbnail=thumb_series))
    #itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host,
    #                     thumbnail=thumb_series))
    #itemlist.append(Item(channel=item.channel, action="lista", title="Pokemon", url=host,
    #                     thumbnail=thumb_series))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    #logger.info("Pagina para regex "+data)
    patron = '<div class="serie">' #Encabezado regex
    patron +="<a href='(.+?)'>" #scrapedurl
    patron +="<img src='(.+?)'.+?" #scrapedthumbnail
    patron +="<p class='.+?'>(.+?)<\/p>" #scrapedtitle
    patron +=".+?<span .+?>(.+?)<\/span>" #scrapedplot

    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail,scrapedtitle,scrapedplot in matches:
    	if ":" in scrapedtitle:
            cad = scrapedtitle.split(":")
            show = cad[0]
        else:
            if "(" in scrapedtitle:
                cad = scrapedtitle.split("(")
                if "Super" in scrapedtitle:
                    show = cad[1]
                    show = show.replace(")", "")
                else:
                    show = cad[0]
            else:
                show = scrapedtitle
                if "&" in show:
                    cad = scrapedtitle.split("xy")
                    show = cad[0]
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        scrapedurl=host+scrapedurl
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, plot=scrapedplot, 
        	thumbnail=scrapedthumbnail, action="episodios", show=show, context=context))
    #tmdb.set_infoLabels(itemlist)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="pagina">(.+?)<\/div><div id="fade".+?>'
    data = scrapertools.find_single_match(data, patron)
    patron_caps = "<li><a href='(.+?)'>Capitulo: (.+?) - (.+?)<\/a>"
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
                             action="add_serie_to_library", extra="episodios", show=item.title))

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
    data_vid = scrapertools.find_single_match(data1, 'var q = \[ \[(.+?)\] \]')
    # name = scrapertools.find_single_match(data,'<span>Titulo.+?<\/span>([^<]+)<br>')
    scrapedplot = scrapertools.find_single_match(data, '<br><span>Descrip.+?<\/span>([^<]+)<br>')
    scrapedthumbnail = scrapertools.find_single_match(data, '<div class="caracteristicas"><img src="([^<]+)">')
    itemla = scrapertools.find_multiple_matches(data_vid, '"(.+?)"')
    for url in itemla:
    	url=url.replace('\/', '/')
    	server1=url.split('/')
    	server=server1[2]
    	if "." in server:
    		server1=server.split('.')
    		if len(server1)==3:
    			server=server1[1]
    		else:
    			server=server1[0]
        if "goo" in url:
            url = googl(url)
            server='netutv'
        if "ok" in url:
            url = "https:"+url
            server='okru'
        quality="360p"
        itemlist.append(item.clone(url=url, action="play",
                                   thumbnail=scrapedthumbnail, server=server, plot=scrapedplot,
                                   title="Enlace encontrado en: %s [%s]" % (server.capitalize(), quality)))
    
    autoplay.start(itemlist, item)
    return itemlist
