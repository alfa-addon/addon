# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
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


## italiafilm                                             \'([^\']+)\'

host = 'http://www.eroticage.net'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="+ Populares" , action="peliculas", url=host + "/en-cok-izlenenler/"))
#    itemlist.append( Item(channel=item.channel, title="+ Vistas" , action="peliculas", url=host + "/en-cok-yorumlananlar/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

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
    data = scrapertools.get_match(data,'<h2>TAGS</h2>(.*?)<div class="sideitem"')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#   <a href="http://www.eroticage.net/ero/70/" class="tag-cloud-link tag-link-71 tag-link-position-2" style="font-size: 8pt;" aria-label="70 (1 öge)">70</a>

    patron  = '<a href="(.*?)".*?>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)Son &raquo;</a>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <div class="film uclu">
#         			                     <div class="ayrinti">
#                    	 	><a href="http://www.eroticage.net/lyceennes-perverses-1979/">Lycéennes perverses (1979)</a></span><!--izleBtn bitiş-->
#                      	<div class="kats"><span>Kategori:</span> <a href="http://www.eroticage.net/Filmler/genel/" rel="category tag">Genel</a></div><!--kats bitiş-->
#                      	<div class="titleFilm"><a href="http://www.eroticage.net/lyceennes-perverses-1979/">Lycéennes perverses (1979)</a></div><!--titleFilm bitiş-->
#                		 </div><!--ayrinti bitiş-->
#                 	<a href="http://www.eroticage.net/lyceennes-perverses-1979/">
# 					<img width="160" height="235" src="http://www.eroticage.net/wp-content/uploads/2017/05/Lycéennes-perverses-1979-160x235.jpg" class="attachment-midi size-midi wp-post-image" alt="Lycéennes perverses (1979)" /></a>
# 		</div><!--film bitiş-->


    patron  = '<div class="titleFilm"><a href="([^"]+)">([^"]+)</a>.*?src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))


#        <a class="nextpostslink" rel="next" href="http://www.eroticage.net/page/2/">&gt;Next</a>
# "Next page >>"

    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page_url) )

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)<div class="butonlar">')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


#         <iframe src="https://openload.co/embed/C8J9saGbcwY/"
# <div id="wrapper" class="ortala">
# 		<div class="solBlok singleSol">
# 	        <div class="videoAlani">
# 		 	<div dir="ltr" style="text-align: left;">
# <div class="separator" style="clear: both; text-align: center;"><a style="margin-left: 1em; margin-right: 1em;" href="http://www.youtube.com/watch?v=ifxtZ4G_gnQ&amp;list=PLz6rHmdtQ6vACYCAqdo-E_7-71GoiLPHa"><img alt="" src="http://3.bp.blogspot.com/-FER7A6LlPVg/Ujn5wgSWGCI/AAAAAAAACEE/pFqRcnSLLMk/s640/thepigkeepersdaughterx.jpg" width="454" height="640" border="0" /></a></div>
# <p>&nbsp;</p>
# </div>
# <p><iframe scrolling="no" frameborder="0" width="440" height="330" webkitallowfullscreen mozallowfullscreen allowfullscreen src="http://video.meta.ua/iframe/7690755/"></iframe></p>
# <div dir="ltr" style="text-align: left;">
# <div class="separator" style="clear: both; text-align: center;"><a style="margin-left: 1em; margin-right: 1em;" href="http://www.youtube.com/watch?v=ifxtZ4G_gnQ&amp;list=PLz6rHmdtQ6vACYCAqdo-E_7-71GoiLPHa"><img alt="" src="http://1.bp.blogspot.com/-JDy7SPLHT7U/Ujn6yodIq1I/AAAAAAAACEQ/UqSFoxVeDfo/s1600/pig9825_ThPiKee_123_136lo.jpg" border="0" /></a></div>
# <p>&nbsp;</p>
# </div

    patron  = '<iframe.*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
#        scrapedtitle = ""
        itemlist.append( Item(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
