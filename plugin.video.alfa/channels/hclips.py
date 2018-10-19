# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb
from core import jsontools

## italiafilm                                             \'([^\']+)\'

host = 'http://www.hclips.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/?"))
    itemlist.append( Item(channel=item.channel, title="Duracion" , action="peliculas", url=host + "/longest/?"))
#    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <a class="subhover" title="NEWS CLIPS" href="/category/clips/">All Clips</a> <BR>
#  - <a class=""  title="Clips 21Sextury"  href="/category/clips/?s=21Sextury">21Sextury</a> <BR>

    patron  = '<a class=""\s+title="([^"]+)"\s+href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedtitle,scrapedurl in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="cf">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



            # <div class="thumb_holder c-thumb_holder">
            #                                     <a href="http://www.hclips.com/categories/amateur/" class="thumb">
            #             <img width="220" height="165" class="img" src="http://www.hclips.com/contents/categories/18.jpg" alt="Amateur sex cam tube has a lot of amazing scenes with amateur mature ladies that really love to fuck and big collection of top-class anal amateur home clips." title="Amateur"/>
            #             <strong class="title">Amateur</strong>
            #             <span class="info videos_count_info">(<b>126 601</b> videos)</span>
            #             <span class="add">+35 videos today</span>                    </a>

    patron  = '<a href="([^"]+)" class="thumb">.*?src="([^"]+)".*?<strong class="title">([^"]+)</strong>.*?<b>(.*?)</b>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,vidnum in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
        title = scrapedtitle + " \(" + vidnum + "\)"
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = scrapertools.get_match(data,'<div class="thumb_holder">(.*?)<h3>Advertisement</h3>')


            # <div class="thumb_holder">
            #                         <a href="http://www.hclips.com/videos/afternoon-bj3/?pqr=1:ca02e299655209f5097abfd1528e3e5b:0:159691:1" class="thumb">
            #             <img src="http://static3.gfkey.com/contents/videos_screenshots/159000/159691/220x165/1.jpg" alt="Afternoon BJ !!!" width="220" height="165" onmouseover="KT_rotationStart(this, 'http://static3.gfkey.com/contents/videos_screenshots/159000/159691/220x165/', 12)" onmouseout="KT_rotationStop(this)"/>
            #             <span class="dur">11:25</span>
            #                                     <strong class="title">Afternoon BJ !!!</strong>
            #             <div class="info-small">
            #             <span class="info_l">
            #                                             <span class="info-small_views">Views: 2151</span>
            #             </span>
            #             <div class="info_r">
            #                 <span class="info-small_added-date">Added: 2 years ago</span>
            #             </div>
            #             </div>
            #         </a>



    patron  = '<a href="([^"]+)" class="thumb">.*?<img src="([^"]+)" alt="([^"]+)".*?<span class="dur">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,time  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)

        title = "[COLOR yellow]" + time + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#            li class="next">
#				<a href="/latest-updates/2/" title="Next Page">Next</a>

    else:
            patron  = '<a href="([^"]+)" title="Next Page">Next</a>'
            next_page = re.compile(patron,re.DOTALL).findall(data)
            next_page = host + next_page[0]
            itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#            var video_url = "aHR0cHМ6Ly93d3cuaGNsaXВzLmNvbS9nZXRfZmlsZS82L2RmNTcxODU1МDМ1ZGU0OTFhOGI0NGJlМjQ2МzVmYTА1LzЕxМTАwМС8xМTЕ0NDkvМTЕxNDQ5X2hxLm1wNС8,ZD0xNzY1JmJyPTQ2";
#            video_url += "||/get_file/6/df571855035de491a8b44be24635fa05aa1acbc8c5/||193.111.52.130||1532883397";


    video_url = scrapertools.find_single_match(data, 'var video_url = "([^"]*)"')
    video_url += scrapertools.find_single_match(data, 'video_url \+= "([^"]*)"')

    partes = video_url.split('||')
    video_url = decode_url(partes[0])
    video_url = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], video_url)
    video_url += '&' if '?' in video_url else '?'
    video_url += 'lip=' + partes[2] + '&lt=' + partes[3]

    itemlist.append(item.clone(action="play", title=item.title, url=video_url))

    return itemlist

def decode_url(txt):
    _0x52f6x15 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    reto = ''; n = 0
    # En las dos siguientes líneas, ABCEM ocupan 2 bytes cada letra! El replace lo deja en 1 byte. !!!!: АВСЕМ (10 bytes) ABCEM (5 bytes)
    txt = re.sub('[^АВСЕМA-Za-z0-9\.\,\~]', '', txt)
    txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M')

    while n < len(txt):
        a = _0x52f6x15.index(txt[n])
        n += 1
        b = _0x52f6x15.index(txt[n])
        n += 1
        c = _0x52f6x15.index(txt[n])
        n += 1
        d = _0x52f6x15.index(txt[n])
        n += 1

        a = a << 2 | b >> 4
        b = (b & 15) << 4 | c >> 2
        e = (c & 3) << 6 | d
        reto += chr(a)
        if c != 64: reto += chr(b)
        if d != 64: reto += chr(e)

    return urllib.unquote(reto)
