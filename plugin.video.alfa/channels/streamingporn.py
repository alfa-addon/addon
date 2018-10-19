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

host = 'http://streamingporn.xyz'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/category/stream/"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated-week/1.html"))


    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))
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
    data = scrapertools.get_match(data,'PaySites(.*?)<li id="menu-item-28040"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#<li id="menu-item-15323" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-15323"><a href="http://streamingporn.xyz/tag/brazzers/">Brazzers</a></li>

    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<a href="#">Categories</a>(.*?)<li id="menu-item-30919')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<li id="menu-item-\d+".*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<!doctype html>(.*?)<h4 class="widgettitle">New</h4>')


# <article id="post-242378" class="anninamas post-242378 post type-post status-publish format-standard hentry category-stream tag-34098 tag-blowjob tag-fullhd tag-jeshbyjesh tag-summer-brooks">
#                            <div class="content-anninapro">
#                               <div class="entry-featuredImg"> <a href="http://streamingporn.xyz/summer-brooks-summer-brooks-bj-2018-jeshbyjesh-com-fullhd/"><span class="overlay-img"></span> <img src="https://imgcloud.pw/images/2018/07/19/838550d72b82065a69b68882c47b.jpg" alt="Summer Brooks &#8211; Summer Brooks BJ (2018/JeshByJesh.com/FullHD)"> </a></div>
#                               <header class="entry-header">
#                                  <h3 class="entry-title"><a href="http://streamingporn.xyz/summer-brooks-summer-brooks-bj-2018-jeshbyjesh-com-fullhd/" rel="bookmark">Summer Brooks &#8211; Summer Brooks BJ (2018/JeshByJesh.com/FullHD)</a></h3>
#                                  <div class="entry-meta smallPart"> <span class="posted-on"><i class="fa fa-calendar spaceLeftRight"></i><a href="http://streamingporn.xyz/summer-brooks-summer-brooks-bj-2018-jeshbyjesh-com-fullhd/" rel="bookmark"><time class="entry-date published updated" datetime="2018-07-19T07:53:16+00:00">July 19, 2018</time></a></span><span class="byline"> <i class="fa fa-user spaceLeftRight"></i><span class="author vcard"><a class="url fn n" href="http://streamingporn.xyz/author/83b2913dd73385a9/">Moon</a></span></span><span class="comments-link"><i class="fa fa-comments-o spaceLeftRight"></i><a href="http://streamingporn.xyz/summer-brooks-summer-brooks-bj-2018-jeshbyjesh-com-fullhd/#respond">No Comments</a></span></div>
#                               </header>
#                               <footer class="entry-footer smallPart annCenter"> <span class="read-more"><a href="http://streamingporn.xyz/summer-brooks-summer-brooks-bj-2018-jeshbyjesh-com-fullhd/">Read More</a><i class="fa spaceLeft fa-caret-right"></i></span> <span class="count-views floatLeft"><i class="fa fa-eye spaceRight"></i>1 views</span></footer>
#                            </div>
#                         </article>


    patron  = '<div class="entry-featuredImg">.*?<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        url = scrapedurl
#        year = " (%s)" % year
        title = scrapedtitle
#        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<div class="loadMoreInfinite"><a href="http://streamingporn.xyz/category/stream/page/2/" >Load More<i class="fa spaceLeft fa-angle-double-down"></i></a></div>

    next_page_url = scrapertools.find_single_match(data,'<div class="loadMoreInfinite"><a href="(.*?)" >Load More')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        next_page_url = next_page_url
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
#
#    data = scrapertools.get_match(data,'<span id="more-(.*?)<span class="tags-links">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br />", "", data)

    #<a href="https://openload.co/f/Zpi5b5JTM4s/grdhgthtfh_26.mp4" rel="nofollow"  class="external" target="_blank">Streaming Openload.co</a>


    patron  = '<a href="([^"]+)" rel="nofollow"  class="external" target="_blank">Streaming Openload.co</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl  in matches:
    #    scrapedurl = "http:" + scrapedurl
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist

'''

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
