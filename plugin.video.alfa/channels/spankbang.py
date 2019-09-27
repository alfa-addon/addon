# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://es.spankbang.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos", action="lista", url= host + "/new_videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas valorados", action="lista", url=host + "/trending_videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos", action="lista", url= host + "/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Mas largos", action="lista", url= host + "/longest_videos/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/s/%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<a href="([^"]+)/?order=trending"><img src="([^"]+)"><span>([^"]+)</span></a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl =  urlparse.urljoin(item.url,scrapedurl)
        scrapedthumbnail =  urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle , url=scrapedurl , 
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video-item" data-id="\d+">.*?'
    patron += '<a href="([^"]+)" class="thumb ">.*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '<i class="fa fa-clock-o"></i>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duration in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        duration = duration.strip()
        minutos = int(duration)
        horas=int(minutos/60)
        minutos-=horas*60
        if minutos < 10:
            minutos = "0%s" %minutos
        if horas == 0:
            duration = "%s:%s" % (horas,minutos)
        else:
            duration = "%s:%s" % (horas,minutos)

        title = "[COLOR yellow]" + duration + " min[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, 
                              fanart=thumbnail, plot=plot, contentTitle=title) )
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>" , text_color="blue",
                              url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    skey = scrapertools.find_single_match(data,'data-streamkey="([^"]+)"')
    session="523034c1c1fc14aabde7335e4f9d9006b0b1e4984bf919d1381316adef299d1e"
    post = {"id": skey, "data": 0, "sb_csrf_session": session}
    headers = {'Referer':item.url}
    url ="%s%s" % (host, "/api/videos/stream")
    data = httptools.downloadpage(url, post=post, headers=headers).data
    patron = '"stream_url_(\w+)":\["([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist

