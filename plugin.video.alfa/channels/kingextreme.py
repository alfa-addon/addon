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
from core import jsontools

## italiafilm                                             \'([^\']+)\'

host = 'https://kingextreme.unblocked.gdn/'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host))
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
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<ul id="primary-menu" class="menu">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#             <li id="menu-item-12003" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-12003"><a href="https://kingextreme.unblocked.gdn/category/porn-clips/porn-anal-videos-free-download/">Anal</a></li>

    patron  = '<li id="menu-item-\d+".*?><a href="([^"]+)".*?>([^"]+)</a>'
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
    data = scrapertools.cachePage(item.url)
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


   # <article id="post-69051" class="post-69051 post type-post status-publish format-standard has-post-thumbnail hentry category-hardcore-porn-videos">
   #                      <a href="https://kingextreme.unblocked.gdn/puremature-escort-to-a-virgin-with-brooke-paige/" class="entry-image-link">
   #                         <div class="entry-image" style="background-image: url('https://img200.imagetwist.com/th/25236/10rblcufw89c.jpg'); height:360px;"></div>
   #                      </a>
   #                      <div class="post-featured-trending"></div>
   #                      <div class="content-right-top ">
   #                         <span class="buzpress-post-format"> </span>
   #                         <div class="content-middle">
   #                            <span class="content-share-counter"> <span class="content-middle-open" data-toggle="dropdown" data-target=".content-m-69051" aria-expanded="false" role="button"> <i class="fa fa-retweet" aria-hidden="true"></i> </span> <span>0</span> </span>
   #                            <div class="content-m-69051 content-middle-content">
   #                               <div class="share-buttons"> <a class="post-share share-fb" title="Share on Facebook" href="#" target="_blank" rel="nofollow" onclick="window.open('https://www.facebook.com/sharer/sharer.php?u=http%3A%2F%2Fkingextreme.unblocked.gdn%2Fpuremature-escort-to-a-virgin-with-brooke-paige%2F','facebook-share-dialog','width=626,height=436');return false;"><i class="fa fa-facebook-official fa-2x"></i></a> <a class="social-icon share-tw" href="#" title="Share on Twitter" rel="nofollow" target="_blank" onclick="window.open('http://twitter.com/share?text=PureMature%20%E2%80%93%20Escort%20To%20A%20Virgin%20with%20Brooke%20Paige&amp;url=http%3A%2F%2Fkingextreme.unblocked.gdn%2Fpuremature-escort-to-a-virgin-with-brooke-paige%2F','twitter-share-dialog','width=626,height=436');return false;"><i class="fa fa-twitter fa-2x"></i></a> <a class="social-icon share-gg fa-2x" href="#" title="Share on Google Plus" rel="nofollow" target="_blank" onclick="window.open('https://plus.google.com/share?url=http%3A%2F%2Fkingextreme.unblocked.gdn%2Fpuremature-escort-to-a-virgin-with-brooke-paige%2F','googleplus-share-dialog','width=626,height=436');return false;"><i class="fa fa-google-plus fa-2x"></i></a> <a class="social-icon share-em" href="/cdn-cgi/l/email-protection#f1ce8284939b949285cca1848394bc9085848394d4c3c1d4b4c3d4c9c1d4c8c2d4c3c1b482929e8385d4c3c1a59ed4c3c1b0d4c3c1a7988396989fd4c3c186988599d4c3c1b3839e9e9a94d4c3c1a190989694d7909c81ca939e9588cc99858581d4c2b0d4c3b7d4c3b79a989f9694898583949c94df849f939d9e929a9495df96959fd4c3b7818483949c9085848394dc9482929e8385dc859edc90dc87988396989fdc86988599dc93839e9e9a94dc8190989694d4c3b7" title="Email this"><i class="fa fa-envelope fa-2x"></i></a></div>
   #                            </div>
   #                         </div>
   #                         <span class="content-avatar"> </span>
   #                      </div>
   #                      <div class="article-meta ">
   #                         <div class="article-meta-head">
   #                            <header class="entry-header">
   #                               <h2 class="entry-title"><a href="https://kingextreme.unblocked.gdn/puremature-escort-to-a-virgin-with-brooke-paige/" rel="bookmark">PureMature &#8211; Escort To A Virgin with Brooke Paige</a></h2>
   #                            </header>
   #                            <div class="entry-content"> PureMature - Escort To A Virgin with Brooke Paige&nbsp;https://turbobit.net/0g0i2ak1</div>
   #                            <span class="cat-links"><a href="https://kingextreme.unblocked.gdn/category/hardcore-porn-videos/" rel="category tag">Hardcore</a></span>
   #                         </div>
   #                         <div class="entry-meta"> <span class="post-likes"><i class="fa fa-thumbs-up" aria-hidden="true"></i> 0</span> <span class="post-views"><i class="fa fa-eye" aria-hidden="true"></i>802</span> <span class="post-comments"><i class="fa fa-comment" aria-hidden="true"></i> 0 </span> <span class="post-time"><i class="fa fa-clock-o" aria-hidden="true"></i>September 16, 2018</span></div>
   #                      </div>
   #                   </article>

    patron  = '<article id="post-\d+".*?<a href="([^"]+)".*?style="background-image: url\(\'([^"]+)\'\).*?rel="bookmark">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle
#        title = "[COLOR yellow]" + duracion + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))

#<link rel="next" href="https://kingextreme.unblocked.vc/page/2/" />
#        <a class="nextpostslink" rel="next" href="https://kingextreme.unblocked.bid/page/2/">»</a>
# "Next page >>"

    next_page_url = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)"')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #     patron  = '<a class="nextpostslink" rel="next" href="([^"]+)">'
    #     next_page = re.compile(patron,re.DOTALL).findall(data)
    #     itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )
    return itemlist

'''
def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#         <p>Online:</p>
#         <p><a href="https://vidlox.me/8xans5a6hgui" target="_blank" rel=

    patron  = '<p>Online:</p>.*?<a href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

#    sources: ["https://c23.vidlox.tv/hls/,oudvg3r6pjtk2yixv7i6axb7j6nqbwjlbbxly4ofvbb425qh5impqqq2p4ba,.urlset/master.m3u8","https://c23.vidlox.tv/oudvg3r6pjtk2yixv7i6axb7j6nqbwjlbbxly4ofvbb425qh5impqqq2p4ba/v.mp4"],

    for scrapedurl in matches:
        data = scrapertools.cachePage(scrapedurl)
        scrapedurl = scrapertools.find_single_match(data,'sources:.*?,"([^"]+)"]')

        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
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
