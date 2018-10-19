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

## italiafilm

'''
([^<]+) para extraer el texto entre dos tags “uno o más caracteres que no sean <" ^ cualquier caracter que no sea <
"([^"]+)" para extraer el valor de un atributo
\d+ para saltar números
\s+ para saltar espacios en blanco
(.*?) cuando la cosa se pone complicada

    ([^<]+)
  \'([^\']+)\'



    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist

'''

host = 'http://free-porn-videos.xyz'


def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/Category/porn-videos/"))
    itemlist.append( Item(channel=item.channel, title="Parody" , action="peliculas", url=host + "/Category/free-porn-parodies/"))

    itemlist.append( Item(channel=item.channel, title="BigTits" , action="peliculas", url=host + "/?s=big+tit"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search", text_color="yellow"))
    return itemlist


#http://free-porn-videos.xyz/?s=anal

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

def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')


# <article id="post-31081" class="group post-standard grid-item post-31081 post type-post status-publish format-standard has-post-thumbnail hentry category-adult-movie tag-13777 tag-adult-dvd-free-download tag-adult-movies-download tag-asian tag-download-porn-dvd tag-erotic-movies-online tag-free-full-porn-dvds tag-free-porn-dvd-download tag-free-stream-porn tag-free-streaming-xxx tag-full-porn-stream tag-hd-dvd-free-download tag-japan tag-japanese tag-mature tag-milf tag-porn tag-porn-dvd tag-porn-movies-online tag-show-more tag-takara-eizou tag-tsuno-miho tag-watch-adult-dvd tag-watch-erotic-movies tag-watch-free-porn-dvd tag-watch-porn-dvd tag-wives">
# <div class="post-inner post-hover">
# <div class="post-thumbnail">
# <a href="http://free-porn-videos.xyz/adult-movie/mond-065-booty-and-crotch-feel-other-than-her-husband-is-out-open-tsuno-miho-porn-dvd/" title="MOND-065 Booty And Crotch Feel Other Than Her Husband Is Out Open Tsuno Miho Porn DVD">
# <img  width="230" height="320"  src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" data-src="http://free-porn-videos.xyz/wp-content/uploads/2018/09/MOND-065-Booty-And-Crotch-Feel-Other-Than-Her-Husband-Is-Out-Open-Tsuno-Miho-Porn-DVD.jpg"  class="attachment-thumb-standard size-thumb-standard wp-post-image" alt="MOND-065 Booty And Crotch Feel Other Than Her Husband Is Out Open Tsuno Miho" data-srcset="http://free-porn-videos.xyz/wp-content/uploads/2018/09/MOND-065-Booty-And-Crotch-Feel-Other-Than-Her-Husband-Is-Out-Open-Tsuno-Miho-Porn-DVD.jpg 514w, http://free-porn-videos.xyz/wp-content/uploads/2018/09/MOND-065-Booty-And-Crotch-Feel-Other-Than-Her-Husband-Is-Out-Open-Tsuno-Miho-Porn-DVD-250x348.jpg 250w, http://free-porn-videos.xyz/wp-content/uploads/2018/09/MOND-065-Booty-And-Crotch-Feel-Other-Than-Her-Husband-Is-Out-Open-Tsuno-Miho-Porn-DVD-500x696.jpg 500w" data-sizes="(max-width: 230px) 100vw, 230px" />															</a>
# </div><!--/.post-thumbnail-->
# <div class="post-content">
# <div class="post-meta group">
# <p class="post-category"><a href="http://free-porn-videos.xyz/Category/adult-movie/" rel="category tag">Adult Movie</a></p>
# <p class="post-date">
# <time class="published updated" datetime="2018-09-01 00:14:19">September 1, 2018</time>
# </p>
# <p class="post-byline" style="display:none">&nbsp;by    <span class="vcard author">
# <span class="fn"><a href="http://free-porn-videos.xyz/author/samantha/" title="Posts by Ebony Samantha" rel="author">Ebony Samantha</a></span>
# </span> &middot; Published <span class="published">September 1, 2018</span>
# </p>
# </div><!--/.post-meta-->
# <h2 class="post-title entry-title">
# <a href="http://free-porn-videos.xyz/adult-movie/mond-065-booty-and-crotch-feel-other-than-her-husband-is-out-open-tsuno-miho-porn-dvd/" rel="bookmark" title="MOND-065 Booty And Crotch Feel Other Than Her Husband Is Out Open Tsuno Miho Porn DVD">MOND-065 Booty And Crotch Feel Other Than Her Husband Is Out Open Tsuno Miho Porn DVD</a>
# </h2><!--/.post-title-->
# <div class="entry excerpt entry-summary">
# <p>&nbsp; Genre: Asian, Japanese, Mature, MILF, Porn DVD, Wives Director: Takara Eizou Actors: Tsuno Miho Country: Japan Duration: 2 hrs. 05 mins Quality: DVD Release: 2015 MOND-065 Booty And Crotch Feel Other Than Her Husband Is Out Open Tsuno Miho Watch HD XXX Movies Online For Free and Download the latest porn dvds. For every-body, every-where, every-device, and every-thing for Adult 😉 Watch MOND-065 Booty&#46;&#46;&#46;</p>
# </div><!--/.entry-->
# </div><!--/.post-content-->
# </div><!--/.post-inner-->
# </article><!--/.post-->


    patron = '<article id="post-\d+".*?<a href="([^"]+)" title="([^"]+)">.*?data-src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle.replace("&#8211; Full Free HD XXX DVD", "")
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = "https://hqcollect.tv" + scrapedurl
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )



#                                               <a class="nextpostslink" rel="next" href="http://free-porn-videos.xyz/page/2/">&raquo;</a>

# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<a class="nextpostslink" rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

#       <iframe src="https://openload.co/embed/sPNKn2DSafo/Teeny_Titten_XXL_2_%282017%29.mp4" width="100%" height="360" frameborder="0" scrolling="no" allowfullscreen="allowfullscreen"><span data-mce-type="bookmark" style="display: inline-block; width: 0px; overflow: hidden; line-height: 0;" class="mce_SELRES_start">﻿</span></iframe></p>
#    <img title="Cover Kim Kardashian And Rapper Ray J Leaked Sex Tape (2014)" src="http://i.imgur.com/kpN1fJB.jpg"
    scrapedurl = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
    scrapedurl = scrapedurl.replace("%28", "(").replace("%29", ")")

    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)


    #
    # patron = '<iframe src="([^"]+)" width="100%".*?src="([^"]+)"'
    # matches = re.compile(patron,re.DOTALL).findall(data)
    #
    #
    # for scrapedurl,scrapedthumbnail  in matches:
    #     scrapedurl = scrapedurl.replace("%28", "(").replace("%29", ")")
    #
    #
    #     itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , folder=True) )
    return itemlist
'''
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
'''
