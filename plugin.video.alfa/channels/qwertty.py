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

host = 'http://qwertty.net'

def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Recientes" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/?filter=most-viewed"))
    itemlist.append( Item(channel=item.channel, title="Mas popular" , action="peliculas", url=host + "/?filter=popular"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/?filter=random"))

#    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
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

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


#       <li><a href="/anal/">Anal</a></li>   http://qwertty.net/big-tits/
    patron  = '<li><a href="([^<]+)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>(.*?)</div>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <article id="post-10298" class="thumb-block post-10298 post type-post status-publish format-video has-post-thumbnail hentry category-video-online tag-ass-fuck tag-choked-while-fucked tag-choking tag-deeptroath tag-euro-teen tag-european tag-hardcode tag-rough-anal tag-rough-sex tag-stockings tag-submissive-slut tag-teenager tag-young tag-young-couple post_format-post-format-video">
#                         <a href="http://qwertty.net/10298/young-teen-fucked-really-hard-and-rough/" title="Young teen fucked really hard and rough">
#                            <div class="post-thumbnail thumbs-rotation" data-thumbs='https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)1.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)2.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)3.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)4.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)5.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)6.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)7.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)8.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)9.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)10.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)11.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)12.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)13.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)14.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)15.jpg,https://ci.phncdn.com/videos/201511/28/62647721/original/(m=eaf8Ggaaaa)(mh=ppiGe5qz5B2L0rYa)16.jpg'>
#                               <img data-src="http://qwertty.net/wp-content/uploads/2018/07/young-teen-fucked-really-hard-and-rough-320x180.jpg" alt="Young teen fucked really hard and rough" src="http://qwertty.net/wp-content/themes/retrotube/assets/img/px.gif">
#                               <div class="play-icon-hover"><i class="fa fa-play-circle"></i></div>
#                               <span class="views"><i class="fa fa-eye"></i> 0</span> <span class="duration"><i class="fa fa-clock-o"></i> 24:34</span>
#                            </div>
#                            <div class="rating-bar no-rate">
#                               <div class="rating-bar-meter" style="width: 0%;"></div>
#                               <i class="fa fa-thumbs-up" aria-hidden="true"></i> <span>0%</span>
#                            </div>
#                            <header class="entry-header"> <span>Young teen fucked really hard and rough</span></header>
#                         </a>
#                      </article>


    patron  = '<article id="post-\d+".*?<a href="([^"]+)" title="([^"]+)">.*?<img data-src="(.*?)".*?<span class="duration"><i class="fa fa-clock-o"></i>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion in matches:
        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# <li><a href="http://qwertty.net/page/2/">Next</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)">Next</a>')
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = httptools.downloadpage(item.url).data

#           <source src="https://thumb-v7.xhcdn.com/a/ShCaeRmrCYVIPEiq5kWiTg/000/785/247/240x135.t.mp4" type='video/mp4;' /></video>

    url = scrapertools.find_single_match(data,'<source src="([^"]+)"')
    scrapedthumbnail = ""

    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url, thumbnail=scrapedthumbnail))

    return itemlist

'''
def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''
