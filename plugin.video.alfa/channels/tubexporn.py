# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.tubxxporn.com'  #  https://www.pornktube.porn


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto
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
    data= scrapertools.find_single_match(data, '>Back</a>(.*?)</div>')
    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = ""
        plot = ""
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=thumbnail , plot=plot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)" alt="([^"]+)".*?'
    patron += '<div class="length">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        title = '[COLOR yellow] %s [/COLOR] %s' % (scrapedtime , scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="mobnav">Next')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


# <div class="plwidth" id="playernew">
# <div id="player" data-id="16098" 
                 # data-s="146" 
                 # data-q="240p;ad653824122280e8c0a2e57eb76e99ea;LQ&nbsp;240p;89000;1575977728;LFwyX8GL-jAy-k2NmNrqeg,360p;ff53c1a9e21c243f2b510b0d521b4a6b;SD&nbsp;360p;137000;1575977728;YiAqpAy5iTfe0Zp8GeaCnQ,480p;3b5430db5a6defea95b752421d059261;SD&nbsp;480p;197250;1575977728;14YBH_UvUqbKaLDqSMl3VQ,720p;d4f959bf48c8ed137801d92ec3859a1c;HD&nbsp;720p;335750;1575977728;wW6N9c0V3osfSI1S7wCnmQ,1080p;b49af371e1392da05a455226bbac42ab;FULL&nbsp;HD&nbsp;1080p;1141750;1575977728;9Yi74xf_TtMP7eHr9AnOKA" 
                 # data-t="244" 
                 # data-n="129">

# http://s129.cdna.tv/wqpvid/1575977817/bVE5kVYenKZjw2c9mN5WIw/16000/16098/16098_1080p.mp4

def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    id,data,server = scrapertools.find_single_match(data, '<div id="player" data-id="(\d+)".*?data-q="([^"]+)".*?data-n="(\d+)"')
    patron = '&nbsp;([A-z0-9]+);\d+;(\d+);([^,"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,number,key in matches:
        nt = int(int(id)/1000)
        n = str(nt*1000)
        url = "http://s%s.cdna.tv/wqpvid/%s/%s/%s/%s/%s_%s.mp4" % (server,number,key,n,id,id,quality)
        url= url.replace("_720p", "")
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist

