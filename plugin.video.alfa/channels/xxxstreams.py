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

host = 'http://xxxstreams.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url= host + "/category/full-porn-movie-stream/"))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Clips" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/category/full-porn-movie-stream/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

    try:
        return peliculas(item)
#        return sub_search(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    # <div class="row">
	# 		<a href="http://gnula.mobi/16160/pelicula/sicario-2015/" title="Sicario (2015)">
	# 			<img src="http://image.tmdb.org/t/p/w300/voDX6lrA37mtk1pVVluVn9KI0us.jpg" title="Sicario (2015)" alt="Sicario (2015)" />
	# 		</a>
	# </div>

    patron = '<h1 class="entry-title"><a href="([^"]+)" rel="bookmark">([^"]+)</a>.*?<img src="(.*?)"/>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url,name,img   in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", show=name, thumbnail=img))

# <a href="http://gnula.mobi/page/2/?s=la" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a></div>

    paginacion = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Next &rarr;</a>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion))

    return itemlist




def categorias(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

# <li id="menu-item-310254" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-310254"><a href="http://xxxstreams.org/tag/legalporno-com/">LegalPorno</a></li>
#        <li id="menu-item-412140" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-412140"><a href="http://xxxstreams.org/tag/hd/">HD</a></li>


    patron  = '<li id="menu-item.*?class="menu-item menu-item-type-taxonomy.*?<a href="([^<]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


# 	<div class="entry-content">
# 		<p><a href="https://imgcloud.pw/image/G06dBX" target="_blank" class="external" rel="nofollow"><a href="http://xxxstreams.org/seventeens-playground-8-2010-dvdrip/"><img src="https://imgcloud.pw/images/2018/01/21/c194251336edddace0273aa69635.jpg" alt="c194251336edddace0273aa69635.jpg" border="0" /></a></a><br />
#  <a href="http://xxxstreams.org/seventeens-playground-8-2010-dvdrip/#more-464299" class="more-link">Continue reading <span class="screen-reader-text">Seventeens Playground 8 (2010/DVDRip)</span> <span class="meta-nav">&rarr;</span></a></p>
# 	</div><!-- .entry-content -->
#
#
# 	<footer class="entry-meta"><span class="tag-links"><a href="http://xxxstreams.org/tag/all-sex/" rel="tag">All Sex</a><a href="http://xxxstreams.org/tag/amateur/" rel="tag">Amateur</a><a href="http://xxxstreams.org/tag/dvdrip/" rel="tag">Dvdrip</a><a href="http://xxxstreams.org/tag/legal-teens/" rel="tag">Legal teens</a><a href="http://xxxstreams.org/tag/lesbians/" rel="tag">Lesbians</a><a href="http://xxxstreams.org/tag/masturbation/" rel="tag">Masturbation</a><a href="http://xxxstreams.org/tag/seventeen-video-art-holland/" rel="tag">Seventeen Video Art Holland</a><a href="http://xxxstreams.org/tag/sex-toys/" rel="tag">Sex Toys</a></span></footer></article><!-- #post-## -->
#
# <article id="post-464298" class="post-464298 post type-post status-publish format-standard hentry category-full-porn-movie-stream tag-all-sex tag-hd tag-mia-smiles tag-nurses tag-sasha-grey tag-straight tag-teravision tag-webrip">
#
# 	<header class="entry-header">
# 				<div class="entry-meta">
# 			<span class="cat-links"><a href="http://xxxstreams.org/category/full-porn-movie-stream/" rel="category tag">Full Movies</a></span>
# 		</div>
# 		<h1 class="entry-title"><a href="http://xxxstreams.org/sasha-greys-anatomy-2007-webrip-hd/" rel="bookmark">Sasha Greys Anatomy (2007/WEBRip/HD)</a></h1>
# 		<div class="entry-meta">
# 			<span class="entry-date"><a href="http://xxxstreams.org/sasha-greys-anatomy-2007-webrip-hd/" rel="bookmark"><time class="entry-date" datetime="2018-01-21T14:15:23+00:00">January 21, 2018</time></a></span> <span class="byline"><span class="author vcard"><a class="url fn n" href="http://xxxstreams.org/author/c3e75399f5d66869/" rel="author">Pi</a></span></span>			<span class="comments-link"><a href="http://xxxstreams.org/sasha-greys-anatomy-2007-webrip-hd/#respond">Leave a comment</a></span>
# 					</div><!-- .entry-meta -->
# 	</header><!-- .entry-header -->




    patron  = '<div class="entry-content">.*?<img src="([^"]+)".*?<a href="([^<]+)".*?<span class="screen-reader-text">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# <a class="next page-numbers" href="http://xxxstreams.org/full-porn-movie-stream/page/2/">Next &rarr;</a> </div>

    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &rarr;</a>')
#    next_page_url = "http://www.elreyx.com/"+str(next_page_url)

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = scrapertools.get_match(data,'<p><em>(.*?)</p>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <p>1:56:29 | 512&#215;384 | avi | 1493Mb</p>
# <p><em>Seventeens Playground 8 (2010DVDRip)</em><br />
# <a href="https://openload.co/f/9xwBAC0P11c/rtyrty7987978_15.avi" rel="nofollow"  target="_blank" class="external">Streaming Openload.co</a><br />
# <a href="http://yep.pm/k5gR4TrDj" rel="nofollow"  target="_blank" class="external">Download Depfile.com</a><br />
# <a href="https://streamango.com/f/mrmcsaoreqccqasr/rtyrty7987978_15_avi" rel="nofollow"  target="_blank" class="external">Streaming Streamango.com</a></p>
# <p><a href="https://imgcloud.pw/image/G0lwlC" rel="nofollow"  target="_blank" class="external"><img src="https://imgcloud.pw/images/2018/01/20/ba2ddaea24e9553d4d411f302e6951478def86da092fe8d2.th.jpg" alt="Seventeens Playground 8 (2010DVDRip) Preview" /></a></p>
# 	</div><!-- .entry-content -->

# <p><em>Sexxy Bunny &#8211; 3 girl outfoor wet tshirt play</em><br />
# <a href="https://openload.co/f/ms-y5kB3uz4/zsrtghbhzftf_16.mp4" rel="nofollow" target="_blank" class="external">Streaming Openload.co</a><br />
# <a href="http://yep.pm/Et824rd72" rel="nofollow" target="_blank" class="external">Download Depfile.com</a><br />
# <a href="https://streamango.com/f/tsmfstmnftfpkldo/zsrtghbhzftf_16_mp4" rel="nofollow" target="_blank" class="external">Streaming Streamango.com</a></p>
# <p><a href="https://imgcloud.pw/image/G0pEhF" rel="nofollow" target="_blank" class="external"><img src="https://imgcloud.pw/images/2018/01/21/b1d0f3a1a26756fc379e43b0f890a1fbfc54e851e9d17c22.th.jpg" alt="Sexxy Bunny - 3 girl outfoor wet tshirt play Preview" /></a></p>
# 	</div><!-- .entry-content -->

    patron  = '<a href="([^"]+)".*?class="external">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, fulltitle=item.title, url=scrapedurl, thumbnail=scrapedthumbnail, plot=scrapedplot, folder=True) )
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
