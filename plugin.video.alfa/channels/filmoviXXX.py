# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb
from core import jsontools


def mainlist(item):
    logger.info()
    itemlist = []
    if item.url=="":
        item.url = "http://www.filmovix.net/videoscategory/porno/"
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h1 class="cat_head">XXX</h1>(.*?)<h3> Novo dodato </h3>')
    patron  = '<li class="clearfix">.*?src="([^"]+)".*?<p class="title"><a href="([^"]+)" rel="bookmark" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        contentTitle = scrapedtitle
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="mainlist" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist
    
    
def play(item):
    logger.info()
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

