# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'http://www.veporns.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/month"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "/top-videos"))
    itemlist.append( Item(channel=item.channel, title="PornStar" , action="catalogo", url=host + "/pornstars"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = host + "/porn/%s/" % texto
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li><a href="([^"]+)" class="thumb" title="([^"]+)".*?'
    patron += 'image:url\(([^\)]+)\).*?'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title=scrapedtitle
        thumbnail = scrapedthumbnail
        url = scrapedurl
        itemlist.append( Item(channel=item.channel, action="lista2", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="catalogo", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<ul style="margin-top:-10px;"><li><a href="([^"]+)" title="([^"]+) Porn Videos"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = ""
        url = urlparse.urljoin(host,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return sorted(itemlist, key=lambda i: i.title)

def lista2(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li><img class="small_video_img" src="([^"]+)".*?'
    patron += '<a href="([^"]+)" class="thumb" title="([^"]+)">.*?'
    patron += '>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle,time in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li class="dvd-new".*?<a href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?image:url\(([^")]+)\)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    url = scrapertools.find_single_match(data, 'onClick="toplay\((.*?)\)')
    url = url.replace("'", "").split(",")
    url = "http://www.veporns.com/ajax.php?page=video_play&thumb=%s&theme=%s&video=%s&id=%s&catid=%s&tip=%s&server=%s" %(url[0],url[1],url[2],url[3],url[4],url[5],str(url[6]))
    headers = {"X-Requested-With":"XMLHttpRequest"}
    data = httptools.downloadpage(url, headers=headers).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

