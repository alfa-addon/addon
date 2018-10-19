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

host = 'https://hotmovs.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/most-popular/?sort_by=video_viewed_week"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/?sort_by=rating_week"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels/?sort_by=cs_viewed"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "/models/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/?sort_by=title"))
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
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <article class="item-channel">
#                     <a class="thumbnail" href="https://hotmovs.com/channels/assmasterpiece/">
#                         <img src="https://static1.hclips.net/contents/content_sources/1167/c3_ass_masterpiece_com_285-165_cvr.jpg" alt="assmasterpiece.com">
#
#                         <div class="thumbnail__info">
#                             <span class="thumbnail__info__right">
#                                 125 videos
#                             </span>
#                             <span class="thumbnail__info__left">
#                                 <h5>Ass Masterpiece</h5>
#                             </span>
#                         </div>
#
#                         <div class="thumbnail__info thumbnail__info--hover">
#                             <span class="thumbnail__info__right">
#                                 <i class="mdi mdi-eye"></i> 40,514
#                             </span>
#                             <span class="thumbnail__info__left">
#                                                                                                 <i class="mdi mdi-thumb-up"></i> 75%
#                             </span>
#                         </div>
#                     </a>
#                 </article>


    patron  = '<a class="thumbnail" href="([^"]+)">.*?<img src="([^"]+)".*?<span class="thumbnail__info__right">\s+([^"]+)</span>.*?<h5>([^"]+)</h5>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#  "Next page >>"       <li class="next"><a href="/channels/2/" data-action="ajax"

    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class=\'row alphabetical\' id=\'categoryList\'>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <article class="item">
#                     <a class="thumbnail" href="https://hotmovs.com/categories/3d-toons/" title="3D Toons">
#
#                                                     <img src="https://static1.hclips.net/contents/categories/343.jpg" alt="3D Toons">
#
#                         <div class="thumbnail__label">
#                             <i class="mdi mdi-video"></i> 138
#                         </div>
#
#                         <div class="thumbnail__info">
#                                 <span class="thumbnail__info__right">
#                                                                                                             <i class="mdi mdi-thumb-up"></i> 77%
#                                 </span>
#                                 <span class="thumbnail__info__left">
#                                     <h5>3D Toons</h5>
#                                 </span>
#                         </div>
#                     </a>
#                 </article>



    patron  = '<a class="thumbnail" href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)".*?<i class="mdi mdi-video"></i>([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#  "Next page >>"       <li class="next"><a href="/channels/2/" data-action="ajax"

    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div id="content">(.*?)<h4 class="widgettitle">New</h4>')

   # <article class="item" data-video-id="2979511">
   #    <a class="thumbnail thumbnail-pagination" href="/videos/2979511/girl-rimmed/" data-screen_main="1">
   #       <img class="EoCk7" src="https://static2.hclips.net/contents/videos_screenshots/2979000/2979511/268x200/1.jpg" alt="girl rimmed" data-custom3="tc:5836855:21">
   #       <div class="thumbnail__label thumbnail__label--watch-later"data-toggle="tooltip"data-placement="left"title="Add to Watch Later"data-fav-video-id="2979511"data-fav-type="1"data-fav-action="add_to_favourites"><span class="mdi mdi-timer"></span></div>
   #       <div class="thumbnail__info">
   #          <div class="thumbnail__info__right">21:38</div>
   #          <div class="thumbnail__info__left">
   #             <h5>girl rimmed</h5>
   #          </div>
   #       </div>
   #       <div class="thumbnail__info thumbnail__info--hover">
   #          <div class="thumbnail__info__right"><i class="mdi mdi-eye"></i> 0</div>
   #          <div class="thumbnail__info__left"><i class="mdi mdi-thumb-down"></i> 0%</div>
   #       </div>
   #    </a>
   # </article>


    patron  = '<article class="item" data-video-id="([^"]+)">.*?src="([^"]+)" alt="([^"]+)".*?<div class="thumbnail__info__right">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime  in matches:
        url = urlparse.urljoin(item.url,"/embed/" + scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle


        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))


#           "Next page >>"      <li class="next"><a href="/latest-updates/2/" data-action="ajax"

    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


#            var video_url="aHR0cHМ6Ly92aWRlby5ob3Rtb3ZzLmNvbS9obS9nZXRfZmlsZS8xOS8wМzJlZThhOTk3OGNjYmZmOGUxNGI3МWVlМ2Y3ZGUxNi8yМjU0МDАwLzIyNTQyNDUvМjI1NDI0NV9ocS5tcDQvP2Q9NjkyМyZicj0xOTА~";
#            video_url+='||/get_file/19/032ee8a9978ccbff8e14b71ee3f7de16fedb1b7d3d/||193.111.52.130||1538504449';

    video_url = scrapertools.find_single_match(data, 'var video_url="([^"]*)"')
    video_url += scrapertools.find_single_match(data, 'video_url\+=\'([^\']+)\'')

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
