# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para cineblog01
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
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

sito="https://www.cb01.uno"

DEBUG = config.get_setting("debug")


def mainlist(item):
    logger.info("[cineblog01.py] mainlist")
    itemlist = []


    # Main options
    itemlist.append( Item(channel=item.channel, action="peliculas"  , title="Film - Novita'" , url=sito, viewmode="movie_with_plot"))
    itemlist.append( Item(channel=item.channel, action="menugeneros", title="Film - Per genere" , url=sito))
    itemlist.append( Item(channel=item.channel, action="menuanyos"  , title="Film - Per anno" , url=sito))
    itemlist.append( Item(channel=item.channel, action="search"     , title="Film - Cerca" ))
    itemlist.append( Item(channel=item.channel, action="peliculas"  , title="Serie Tv" , url=sito+"/serietv/" , viewmode="movie_with_plot"))
    itemlist.append( Item(channel=item.channel, action="search", title="Serie Tv - Cerca" , extra="serie"))
    itemlist.append( Item(channel=item.channel, action="peliculas"  , title="Anime" , url="http://www.cineblog01.cc/anime/" , viewmode="movie_with_plot"))

    return itemlist

def menugeneros(item):
    logger.info("[cineblog01.py] menuvk")
    itemlist = []

    data = scrapertools.cache_page(item.url)
    logger.info(data)

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data,'<select name="select2"(.*?)</select')

    # The categories are the options for the combo
    patron = '<option value="([^"]+)">([^<]+)</option>'
    matches = re.compile(patron,re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for url,titulo in matches:
        scrapedtitle = titulo
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, viewmode="movie_with_plot"))

    return itemlist

def menuanyos(item):
    logger.info("[cineblog01.py] menuvk")
    itemlist = []

    data = scrapertools.cache_page(item.url)
    logger.info(data)

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data,'<select name="select3"(.*?)</select')

    # The categories are the options for the combo
    patron = '<option value="([^"]+)">([^<]+)</option>'
    matches = re.compile(patron,re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for url,titulo in matches:
        scrapedtitle = titulo
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, viewmode="movie_with_plot"))

    return itemlist

# Al llamarse "search" la funci�n, el launcher pide un texto a buscar y lo a�ade como par�metro
def search(item,texto):
    logger.info("[cineblog01.py] "+item.url+" search "+texto)

    try:

        if item.extra=="serie":
            item.url = "http://www.cb01.org/serietv/?s="+texto
            return listserie(item)
        else:
            item.url = "http://www.cb01.org/?s="+texto
            return peliculas(item)

    # Se captura la excepci�n, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def peliculas(item):
    logger.info("[cineblog01.py] mainlist")
    itemlist = []

    if item.url =="":
        item.url = sito

    # Descarga la p�gina
    data = scrapertools.cache_page(item.url)
    if DEBUG: logger.info(data)

    # Extrae las entradas (carpetas)
    '''

<div class="span12 filmbox">
<div class="span4"> <a href="https://www.cb01.uno/marjorie-prime-sub-ita-2017/"><p><img src="https://www.cb01.uno/imgk/marjorie_prime_2017.jpg?x30112"></p>
</a>

</div>
<div class="span8">

<a href="https://www.cb01.uno/marjorie-prime-sub-ita-2017/"> <h1>Marjorie Prime [Sub-ITA] (2017)</h1></a>

<p><strong>COMMEDIA &#8211; DURATA 98&#8242; &#8211; USA</strong> <br />
In un futuro prossimo, in un&#8217;epoca dominata dall&#8217;intelligenza artificiale, l&#8217;ottantaseienne Marjorie ha un nuovo e affascinante compagno che somiglia al defunto marito e che è stato programmato per farle rivivere la più grande storia d&#8217;amore della sua vita Sarà suo compito scegliere cosa ricordare e cosa dimenticare del <a href="https://www.cb01.uno/marjorie-prime-sub-ita-2017/"><br>+ info » ...</a>


<div class="rating">
<div class="pd-rating" id="pd_rating_holder_2105735_post_390218"></div>
<script language="javascript" charset="utf-8">
                                    PDRTJS_settings_2105735_post_390218 = {
                                        "id": "2105735",
                                        "popup": "off",
                                        "unique_id": "wp-post-390218",
                                        "title": "Marjorie Prime [Sub-ITA] (2017)",
                                        "permalink": "https://www.cb01.uno/marjorie-prime-sub-ita-2017/",
                                        "item_id": "_post_390218"
                                    };</script>
</div>
<span class="links"> | <a href="https://www.cb01.uno/marjorie-prime-sub-ita-2017/#respond"> <span class="dsq-postid" data-dsqidentifier="390218 https://www.cb01.uno/?p=390218">0</span> Commenti</a> </span> <span class="likes"> <div class="fblike_button" style="margin: 10px 0;"><iframe src="https://www.facebook.com/plugins/like.php?href=https%3A%2F%2Fwww.cb01.uno%2Fmarjorie-prime-sub-ita-2017%2F&amp;layout=button_count&amp;show_faces=false&amp;width=150&amp;action=like&amp;colorscheme=dark" scrolling="no" frameborder="0" allowTransparency="true" style="border:none; overflow:hidden; width:150px; height:20px"></iframe></div><g:plusone size="small" href="https://www.cb01.uno/marjorie-prime-sub-ita-2017/"></g:plusone></span> </div>

</div>

    '''
#    patronvideos  = '<div class="span4"[^<]+'
    patronvideos = '<div class="span4"> <a href="([^"]+)"><p><img src="([^"]+)\?x30112"></p>.*?'
#    patronvideos += '</a[^<]+'
#    patronvideos += '<!--<img[^>]+>--[^<]+'
#    patronvideos += '</div[^<]+'
#    patronvideos += '<div class="span8"[^<]+'
#    patronvideos += '<!--<div class="index_post_content">--[^<]+'
    patronvideos += '<h1>([^<]+)</h1></a>(.*?)<div class="rating">'

    #patronvideos += '<div id="description"><p>(.?*)</div>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedplot in matches:
        title = scrapedtitle
        url = urlparse.urljoin(item.url,scrapedurl)
#        thumbnail = scrapedthumbnail.replace("https", "http")
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        thumbnail = thumbnail.replace("https:", "http:")

        plot = scrapertools.htmlclean(scrapedplot).strip()
        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title, url=url, thumbnail=thumbnail, plot=plot, viewmode="movie_with_plot", fanart=thumbnail))

    # Next page mark
    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)">></a></li>')
    if next_page_url!="":
        itemlist.append( Item(channel=item.channel, action="peliculas" , title=">> Next page" , url=next_page_url, viewmode="movie_with_plot"))

    return itemlist

def listserie(item):
    logger.info("[cineblog01.py] mainlist")
    itemlist = []

    # Descarga la p�gina
    data = scrapertools.cache_page(item.url)
    if DEBUG: logger.info(data)

    # Extrae las entradas (carpetas)
    patronvideos  = '<div id="covershot"><a[^<]+<p[^<]+<img.*?src="([^"]+)".*?'
    patronvideos += '<div id="post-title"><a href="([^"]+)"><h3>([^<]+)</h3></a></div>[^<]+'
    patronvideos += '<div id="description"><p>(.*?)</p>'
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for match in matches:
        scrapedtitle = scrapertools.unescape(match[2])
        scrapedurl = urlparse.urljoin(item.url,match[1])
        scrapedthumbnail = urlparse.urljoin(item.url,match[0])
        scrapedplot = scrapertools.unescape(match[3])
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")

        # A�ade al listado de XBMC
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot))

    # Put the next page mark
    try:
        next_page = scrapertools.get_match(data,"<link rel='next' href='([^']+)'")
        itemlist.append( Item(channel=item.channel, action="listserie" , title=">> Next page" , url=next_page, thumbnail=scrapedthumbnail, plot=scrapedplot))
    except:
        pass

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

#    <a href="http://swzz.xyz/HR/go.php?id=56661" target="_blank" rel="noopener noreferrer">Backin</a></td>

    patron  = '<a href="([^"]+)" target="_blank" rel="noopener noreferrer">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl, scrapedtitle  in matches:
#        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
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
