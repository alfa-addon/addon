# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools

host = 'http://freepornstreams.org'    #es http://xxxstreams.org 


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/free-full-porn-movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="lista", url=host + "/free-stream-porn/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))
    itemlist.append( Item(channel=item.channel, title="Categoria" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'>Top Sites</a>(.*?)</aside>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">([^"]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'Top Tags(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = scrapedurl.replace ("http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=" , "")
        itemlist.append( Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                               thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" rel="bookmark">(.*?)</a>.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        if '/HD' in scrapedtitle : title= "[COLOR red]" + "HD" + "[/COLOR] " + scrapedtitle
        elif 'SD' in scrapedtitle : title= "[COLOR red]" + "SD" + "[/COLOR] " + scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]" + "FullHD" + "[/COLOR] " + scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]" + "1080p" + "[/COLOR] " + scrapedtitle
        else: title = scrapedtitle
        thumbnail = scrapedthumbnail.replace("jpg#", "jpg")
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, fulltitle=title) )
    next_page = scrapertools.find_single_match(data, '<div class="nav-previous"><a href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="Página Siguiente >>", text_color="blue", url=next_page) )
    return itemlist


# <p>0:39:44 | 768&#215;432 | mp4 | 359Mb<br />
# We recommend to visit <a href="https://severeporn.com/" target="_blank" class="external" rel="nofollow">severeporn.com</a><br />
# <a href="https://gounlimited.to/6bcsm0borw4w/esthw46su_8.mp4" rel="nofollow" target="_blank" class="external">Streaming Gounlimited.to</a><br />
# <a href="https://openload.co/f/iXK7muRlBGo/esthw46su_8.mp4" rel="nofollow" target="_blank" class="external">Streaming Openload.co</a><br />
# <a href="https://vidoza.net/nm5jq9rfalbr.html" rel="nofollow" target="_blank" class="external">Streaming Vidoza.net</a><br />
# <a href="https://ubiqfile.com/w00dixda1h2l/esthw46su_8.mp4.html" rel="nofollow" target="_blank" class="external">Download Ubiqfile.com</a></p>



#gounlimited y download aparecen como directo
def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" rel="nofollow".*?>(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        url= url.replace("https:", "http:") #necesario para gounlimited, y funciona conresto server
        itemlist.append(item.clone(action='play',title="%s", url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

# titulo aparece servidor y vidoza no funciona y si lo encuentra el buscador en servidor
def play(item):
    logger.info(item)
    itemlist = servertools.find_video_items(item.clone(url = item.url))
    return itemlist