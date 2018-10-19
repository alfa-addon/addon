# -*- coding: utf-8 -*-
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

host = 'http://www.hdzog.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="peliculas", url=host + "/new/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular/"))
    itemlist.append( Item(channel=item.channel, title="Duracion" , action="peliculas", url=host + "/longest/"))
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
    # Se captura la excepciÃ³n, para no interrumpir al buscador global si un canal falla
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
    data = scrapertools.get_match(data,'<ul class="cf">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


        # <ul class="cf">
        #           <li>
        #       <a href="http://www.hdzog.com/category/amateur/" title="">
        #           <div class="thumb">
        #                                       <img class="thumb" src="http://www.hdzog.com/contents/categories/111.jpg" alt="Amateur"/>
        #                                       <span class="videos-count">5916</span>
        #               <span class="title">Amateur</span>
        #           </div>
        #           <p class="thumb-desc">
        #
        #           </p>
        #       </a>
        #   </li>

    patron  = '<li>.*?<a href="([^"]+)".*?<img class="thumb" src="([^"]+)" alt="([^"]+)".*?<span class="videos-count">(\d+)</span>'
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
    data = scrapertools.get_match(data,'<ul class="cf">(.*?)<h2>Advertisement</h2>')

   # <li>
   #      <a href="https://www.hdzog.com/videos/96221/fabulous-japanese-girl-sana-anzyu-in-incredible-jav-uncensored-teen-video/?pqr=1:e9619b4f74e1d6983b262f6d8ddacc48:0:96221:1" title="Fabulous Japanese girl Sana Anzyu in Incredible JAV uncensored Teen video">
   #        <div class="thumb " data-screen-main="1">
   #          <img class="EoCk7" data-sgid="1" data-video-id="96221" src="https://12111539.pix-cdn.org/contents/videos_screenshots//96000/96221/300x169/1.jpg" alt="Fabulous Japanese girl Sana Anzyu in Incredible JAV uncensored Teen video" />
   #
   #                                  <span class="rating ">74%</span>
   #          <span class="time">20:39</span>
   #
   #          <div class="buttons-overlay">
   #
   #            <button type="button" title="Watch later" class="watch-later jsThumbWatchLater" data-fav-video-id="96221" data-fav-type="1"><i></i></button>
   #            <button type="button" title="Add to favorites" class="add-to-fav jsThumbAddToFav" data-fav-video-id="96221" data-fav-type="0"><i></i></button>
   #
   #          </div>
   #
   #                          <div class="thumb-pagination">
   #                                          <span class="thumb-pagination-item"></span>
   #                                          <span class="thumb-pagination-item"></span>
   #                                          <span class="thumb-pagination-item"></span>
   #                                          <span class="thumb-pagination-item"></span>
   #                                          <span class="thumb-pagination-item"></span>
   #                                  </div>
   #
   #        </div>
   #        <div class="thumb-data">
   #          <span class="title">Fabulous Japanese girl Sana Anzyu ...</span>
   #          <span class="added">Added: 1 year ago</span>
   #        </div>
   #      </a>
   #    </li>



    patron  = '<li>.*?<a href="([^"]+)".*?src="([^"]+)" alt="([^"]+)" />.*?<span class="time">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,time  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#            <li class="next">
#                       <a href="/new/2/" title="Next Page" data-page-num="2">Next page &raquo;</a>

    else:
            patron  = '<a href="([^"]+)" title="Next Page" data-page-num="\d+">Next page &raquo;</a>'
            next_page = re.compile(patron,re.DOTALL).findall(data)
            next_page = host + next_page[0]
            itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = scrapertools.cachePage(item.url)

#                var video_url="aHR0cHМ6Ly93d3cuaGR6b2cuY29tL2dldF9maWxlLzМvY2МyZmY5NjIzOWU2NmJhNTМ0ZDNiNTViYzhjZGJhYTUvМzЕyМDАwLzМxМjc4Ny8zМTI3ODcubXА0Lz9kPTQ4МSZicj0xNTI4";
#                video_url+="||/get_file/3/cc2ff96239e66ba534d3b55bc8cdbaa550f62939c3/||193.111.52.130||1532253923";

    video_url = scrapertools.find_single_match(data, 'var video_url="([^"]*)"')
    video_url += scrapertools.find_single_match(data, 'video_url\+="([^"]*)"')

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
