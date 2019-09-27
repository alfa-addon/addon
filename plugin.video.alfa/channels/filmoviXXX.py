# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

# BLOQUEO ESET INTERNET SECURITY
def mainlist(item):
    logger.info()
    itemlist = []
    if item.url=="":
        item.url = "http://www.filmovix.net/videoscategory/porno/"
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<h1 class="cat_head">XXX</h1>(.*?)<h3> Novo dodato </h3>')
    patron  = '<li class="clearfix">.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<p class="title"><a href="([^"]+)" rel="bookmark" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        contentTitle = scrapedtitle
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                               thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle=contentTitle))
    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="mainlist", title="Página Siguiente >>", text_color="blue", url=next_page_url) )
    return itemlist
    

def play(item):
    itemlist = []
    itemlist = servertools.find_video_items(item)
    a = len (itemlist)
    for i in itemlist:
        
        if a < 1:
            return []
        res = servertools.check_video_link(i.url, i.server, timeout=5)
        a -= 1
        if 'green' in res:
            return [i]
        else:
            continue

