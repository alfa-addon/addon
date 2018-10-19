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

host = 'http://freepornstreams.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="MOVIES" , action="peliculas", url=host + "/free-full-porn-movies/"))
    itemlist.append( Item(channel=item.channel, title="CLIPS" , action="peliculas", url=host + "/free-stream-porn/"))
    itemlist.append( Item(channel=item.channel, title="CATALOGO" , action="catalogo", url=host))

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
    data = scrapertools.get_match(data,'<a href="http://freepornstreams.org/freepornst/stout.php">Top Sites</a>(.*?)</aside>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#<li id="menu-item-258041" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-258041"><a href="http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=http://freepornstreams.org/tag/throated">Throated</a></li>

    patron  = '<li id="menu-item-\d+".*?u=([^"]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul id="taxonomy_list_widget_list_2" class="tlw-list">.*?)</aside>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#   <li><a href="http://freepornstreams.org/tag/high-def-porn-video/" rel="nofollow">HD</a></li>

    patron  = '<li><a href="([^"]+)" rel="nofollow">(.*?)</a>'
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

 # <article id="post-323025" class="post-323025 post type-post status-publish format-standard hentry category-free-full-porn-movies tag-free-anal-sex-videos tag-ass-to-mouth tag-atm tag-evil-angel tag-gaping tag-gonzo-pornography tag-point-of-view tag-best-pov-porn">
	# 			<header class="entry-header">
 #
	# 					<h1 class="entry-title">
	# 			<a href="http://freepornstreams.org/watch-bitch-3/" rel="bookmark">Watch Me Bitch 3</a>
	# 		</h1>
	# 									<div class="comments-link">
	# 				<a href="http://freepornstreams.org/watch-bitch-3/#respond"><span class="leave-reply">Leave a reply</span></a>				</div><!-- .comments-link -->
	# 				</header><!-- .entry-header -->
 #
	# 	<div class="entry-content">
 #            <p><a href="http://freepornstreams.org/watch-bitch-3/"><img src="https://imgcloud.pw/images/2018/07/15/2951031f0e635c33af3cd0.jpg" alt="2951031f0e635c33af3cd0.jpg" border="0" /></a><br />
 # <a href="http://freepornstreams.org/watch-bitch-3/#more-323025" class="more-link">Continue reading <span class="meta-nav">&rarr;</span></a></p>
 #                    </div><!-- .entry-content -->
 # 
	# 	<footer class="entry-meta">
	# 		This entry was posted in <a href="http://freepornstreams.org/free-full-porn-movies/" rel="category tag">Movies</a> and tagged <a href="http://freepornstreams.org/tag/free-anal-sex-videos/" rel="tag">Anal</a>, <a href="http://freepornstreams.org/tag/ass-to-mouth/" rel="tag">Ass to mouth</a>, <a href="http://freepornstreams.org/tag/atm/" rel="tag">ATM</a>, <a href="http://freepornstreams.org/tag/evil-angel/" rel="tag">Evil Angel</a>, <a href="http://freepornstreams.org/tag/gaping/" rel="tag">Gaping</a>, <a href="http://freepornstreams.org/tag/gonzo-pornography/" rel="tag">Gonzo</a>, <a href="http://freepornstreams.org/tag/point-of-view/" rel="tag">Point Of View</a>, <a href="http://freepornstreams.org/tag/best-pov-porn/" rel="tag">POV</a> on <a href="http://freepornstreams.org/watch-bitch-3/" title="5:32 pm" rel="bookmark"><time class="entry-date" datetime="2018-07-15T17:32:10+00:00">July 15, 2018</time></a><span class="by-author"> by <span class="author vcard"><a class="url fn n" href="http://freepornstreams.org/author/96jnrtgfv/" title="View all posts by Pi" rel="author">Pi</a></span></span>.								</footer><!-- .entry-meta -->
	# </article><!-- #post -->

#    patron  = '<div class="content ">.*?<img class="content_image" src="([^"]+).mp4/\d+.mp4-\d.jpg" alt="([^"]+)".*?this.src="([^"]+)"'
    patron  = '<article id="post-\d+".*?<a href="([^"]+)" rel="bookmark">(.*?)</a>.*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
#        scrapedurl = scrapedurl.replace("/thumbs/", "/videos/") + ".mp4"

        thumbnail = scrapedthumbnail.replace("jpg#", "jpg")
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))

#
#                   <div class="nav-previous"><a href="http://freepornstreams.org/free-full-porn-movies/page/2/"><span class="meta-nav">&larr;</span> Older posts</a>
# "Next page >>"
    else:
        patron  = '<div class="nav-previous"><a href="(.*?)"'
        next_page = re.compile(patron,re.DOTALL).findall(data)
#        next_page = scrapertools.find_single_match(data,'class="last" title=.*?<a href="([^"]+)">')
        next_page =  next_page[0]
#        next_page = host + next_page
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page ) )
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<p> Streaming and Download Links:(.*?)</p>')


    # <p><em>cic-screw68a</em>
    # <br /> <a href="http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=https://openload.co/f/PETFxTzrZX8/retgdfgdfg8794545_25.avi" rel="nofollow" >Streaming Openload.co</a>
    # <br /> <a href="http://yep.pm/Mbn92NBUt" rel="nofollow"  target="_blank" class="external">Download Depfile.com</a>
    # <br /> <a href="https://streamango.com/f/ldammsoomdrfqkkq/retgdfgdfg8794545_25_avi" rel="nofollow"  target="_blank" class="external">Streaming Streamango.com</a>
    # </p>


    patron  = '<br /> <a href="([^"]+)" target="_blank".*?>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle in matches:
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
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
'''
