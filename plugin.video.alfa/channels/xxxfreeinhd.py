# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
import base64
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://watchxxxfreeinhd.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/?filtre=date&cat=0"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/?display=tube&filtre=views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/?display=tube&filtre=rate"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "search.php?q=%s&language=en&search=Search" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<noscript>.*?src="([^"]+)".*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += '<span class="nb_cat border-radius-5">(\d+) videos</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        title = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li class="border-radius-5 box-shadow">.*?'
    patron += '<img width="\d+" height="\d+" src="([^"]+)" class=.*?'
    patron += '<a href="([^"]+)" title="([^"]+)">.*?'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail + "|https://watchxxxfreeinhd.com/" 
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=scrapedurl,
                              thumbnail=thumbnail, plot=plot, fanart=scrapedthumbnail ))
    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if next_page:
        next_page =  urlparse.urljoin(item.url,next_page)
        if "?filtre=date&cat=0" in item.url: next_page += "?filtre=date&cat=0"
        elif "?display=tube&filtre=views" in item.url: next_page += "?display=tube&filtre=views"
        elif "?display=tube&filtre=rate" in item.url: next_page += "?display=tube&filtre=rate"
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data,'<div class="video-embed">(.*?)<div class="views-infos">')
    patron = 'data-lazy-src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for title in matches:
        if "strdef" in title: 
        #Aparece directo y es https://strdef.world/vplayer.php?id=351ec419-8f56-4f93-8f5e-8e945c6ad399 = verystream 
                             # https://strdef.world/player.php?id=609f6664-e500-4377-96cd-9737b0a3d21c = oload
            url = decode_url(title)
            if "strdef" in url:
                url = httptools.downloadpage(url).data
        if "hqq" in title:
            url = title
        itemlist.append( Item(channel=item.channel, action="play", title = "%s", url=url, fulltitle=item.fulltitle ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


#Play el titulo es enlace encontrado en "XXXXXX" y  no el titulo
def play(item):
    itemlist = []
    itemlist = servertools.find_video_items(data=item.url)
    for item in itemlist:
        item.channel = "url"
        item.action = "play"
    return itemlist


#ESTO habria que simplificar
def decode_url(txt):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(txt).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    b64_url = scrapertools.find_single_match(data, '\(dhYas638H\("([^"]+)"\)')
    b64_url = base64.b64decode(b64_url + "=")
    b64_url = base64.b64decode(b64_url + "==")
    b64_url = scrapertools.find_single_match(b64_url, '\(dhYas638H\("([^"]+)"\)')
    b64_url = base64.b64decode(b64_url + "=")
    b64_url = base64.b64decode(b64_url + "==")
    url = scrapertools.find_single_match(b64_url, '<iframe src="([^"]+)"')
    logger.debug (url)
    return url


