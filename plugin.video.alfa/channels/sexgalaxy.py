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


host = 'http://sexgalaxy.net/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Canales" , action="canales", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar" , action="search"))


    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
#               http://sexgalaxy.net/?s=boobs
    item.url = "http://sexgalaxy.net/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def canales (item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)

    data = scrapertools.cache_page(host)
    data = scrapertools.get_match(data,'Top Networks</a>(.*?)</ul>')

    patron  = '<li id=.*?<a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
#        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'More Categories</a>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = re.sub('<li id="menu-item-4889".*?>More Categories</a>', "", data)
#   <li id="menu-item-242460" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-242460"><a href="http://sexgalaxy.net/tag/amateur/">Amateur</a></li>
    patron  = '<li id=.*?<a href="(.*?)">(.*?)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
#        scrapedurl = host + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="ntitle1">Newest video:</div></td>(.*?)</table>')

			# 	<article id="post-709475" class="post-box small-post-box post-709475 post type-post status-publish format-standard hentry category-full-movies tag-adult tag-comedy tag-dvdrip tag-msw-productions tag-sci-fi">
			# 	<div class="post-img small-post-img">
			# 		<a href="http://sexgalaxy.net/rollerbabies-1976-dvdrip/" title="Rollerbabies (1976/DVDRip)">
			# 			<img src="https://imgcloud.pw/images/2018/07/17/9dea735df8b7dcb22a7191f81a8d.jpg" alt="">
			# 			<div class="post-format"><i class="fa fa-file-text"></i></div>
			# 		</a>
			# 		<span class="category-box"><a href="http://sexgalaxy.net/full-movies/" title="View all posts in Full Movies" >Full Movies</a></span>				</div>
			# 	<div class="post-data small-post-data">
			# 		<div class="post-data-container">
			# 			<header class="entry-header">
			# 				<div class="entry-meta post-info">
			# 					<h2 class="entry-title post-title"><a href="http://sexgalaxy.net/rollerbabies-1976-dvdrip/" rel="bookmark">Rollerbabies (1976/DVDRip)</a></h2>								<div class="entry-meta post-info"><span class="theauthor"><i class="fa fa-user"></i> <span class="author vcard"><span class="url fn"><a href="http://sexgalaxy.net/author/cwiylbb/">MovieSS</a></span></span></span><span class="posted"><i class="fa fa-clock-o"></i><time class="entry-date published updated" datetime="2018-07-17T17:17:48+00:00">July 17, 2018</time></span><span class="comments"><i class="fa fa-comments"></i>0</span>								</div><!-- .entry-meta -->
			# 												</div><!-- .entry-meta -->
			# 			</header><!-- .entry-header -->
			# 			<div class="entry-content post-excerpt">
			# 										</div><!-- .entry-content -->
			# 			<div class="readmore">
			# 				<a href="http://sexgalaxy.net/rollerbabies-1976-dvdrip/">Read More</a>
			# 			</div>
			# 		</div><!-- .post-data-container -->
			# 	</div><!-- .post-data -->
			# </article><!-- #post-## -->


    patron =  '<div class="post-img small-post-img">.*?<a href="(.*?)" title="(.*?)">.*?<img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle.replace("Ver Pel\ícula", "")
#        scrapedtitle = "[COLOR limegreen]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
#        scrapedtitle = str(scrapedtitle)
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = scrapedurl.replace("/xxx.php?tube=", "")
#        scrapedthumbnail = host + scrapedthumbnail
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , fulltitle=scrapedtitle , plot=scrapedplot , folder=True) )


#     <a class="next page-numbers" href="http://sexgalaxy.net/page/2/">Next &#8250;</a></div>

# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)"')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)


<p><em>Demolition Woman 2 -1994-</em><br />
<a href="https://openload.co/f/5tMqOaFRy9k/rtetert89789_10.mp4" rel="nofollow"  class="external" target="_blank">Download Openload.co</a><br />
<a href="http://yep.pm/x8o52Jjz6" rel="nofollow"  class="external" target="_blank">Download Depfile.com</a><br />
<a href="https://streamango.com/f/ekfbrsscefffkqtq/rtetert89789_10_mp4" rel="nofollow"  class="external" target="_blank">Streaming Streamango.com</a></p>
<p><a href="https://imgcloud.pw/image/GqvNfq" rel="nofollow"  class="external" target="_blank"><img src="https://imgcloud.pw/images/2018/01/09/1a4b5062338a6c36c6e8e8700da6a69587dd6.th.jpg" alt="Demolition Woman 2 -1994- Preview" /></a></p>
			</div><!-- .entry-content -->
# <a href="https://openload.co/f/ZQY7ZbwJ7TM/efsfesgoersg_4.mp4" class="external" rel="nofollow" target="_blank">Streaming Openload.co</a><br />
# <a href="https://www.rapidvideo.com/v/FG247LY1SX" class="external" rel="nofollow" target="_blank">Streaming Rapidvideo.com</a><br />
# <a href="http://yep.pm/4GAkLPC9Z" class="external" rel="nofollow" target="_blank">Download Depfile.com</a></p>


    data = scrapertools.get_match(data,'<p>Streaming and Download Links:<br />(.*?)</p>')

    patron = '<a href="([^"]+)" class="external" rel="nofollow" target="_blank">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
#        title = scrapedtitle

        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , plot="" , folder=True) )

    url = scrapertools.find_single_match(data,'<iframe src="([^"]+)" scrolling="no"')
    itemlist.append(item.clone(channel=item.channel, action="play", title="openload" , url=url , plot="" , folder=True) )

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
