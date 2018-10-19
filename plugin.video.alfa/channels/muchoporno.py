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

host = 'https://www.muchoporno.xxx'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/más-visto/"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-raped/"))
#    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))


#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categorias/"))
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

  #<li id="menu-item-38568" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-38568"><a href="http://pornstreams.eu/tag/assparade/">AssParade</a></li>

    patron  = '<li id="menu-item-.*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="footer-category">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



            # <a class="muestra-escena muestra-categoria" href="/videos-porno/amateur/" title="Amateur">
            # <img class="thumb"
            #      src="https://pics.pornburst.xxx/misc/cat2-3.jpg?62"
            #      width="228" height="178"
            #      alt="Amateur"
            #      onerror="this.src='https://pics.pornburst.xxx/misc/cat3.jpg?62'" />
            # <h2> <span class="ico-h2 sprite"></span> Amateur </h2>
            #         </a>

    patron  = '<a class="muestra-escena muestra-categoria" href="([^"]+)" title="([^"]+)">.*?src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

# <div class="box-link-productora">
#
# 	<a class="muestra-escena"
# 	   href="/ver/un-polvo-rapido-para-una-asiatica-cachonda/"
# 	   title=""
# 	   data-stats-video-id="114343"
# 	   data-stats-video-name="Un polvo rápido para una asiática cachonda"
# 	   data-stats-video-category=""
# 	   data-stats-list-name="Index"
# 	   data-stats-list-pos = "1">
#
#
#
# 			<script type='text/javascript'>stat['753d089e2237072291546a90031cb9de6f67e055.mp4']=0; pic['753d089e2237072291546a90031cb9de6f67e055.mp4']=new Array(); pics['753d089e2237072291546a90031cb9de6f67e055.mp4']=new Array(1,1,1,1,1,1,1,1,1,1);</script>
# 			<img src="https://pics.pornburst.xxx/thumbs/7/5/3/d/0/753d089e2237072291546a90031cb9de6f67e055.mp4/753d089e2237072291546a90031cb9de6f67e055.mp4-3.jpg" data-src="https://pics.pornburst.xxx/thumbs/7/5/3/d/0/753d089e2237072291546a90031cb9de6f67e055.mp4/753d089e2237072291546a90031cb9de6f67e055.mp4-3.jpg" alt="Un polvo rápido para una asiática cachonda" id='753d089e2237072291546a90031cb9de6f67e055.mp4' class="thumbs-changer thumb" data-thumbs-prefix="https://pics.pornburst.xxx/thumbs/7/5/3/d/0/753d089e2237072291546a90031cb9de6f67e055.mp4/753d089e2237072291546a90031cb9de6f67e055.mp4-" height="150px" width="175px" />
#
#
# 		<h2> <span class="ico-h2 sprite"></span> Un polvo rápido para una asiática cachonda</h2>
#
# 		<span class="box-fecha-mins">
#
#
# 				<span class="fecha"> <span class="ico-views sprite" title="Views"></span> 18,143</span>
#
#
# 			<span class="minutos"> <span class="ico-minutos sprite" title="Length"></span> 05:00</span>
#
# 			<div class="clear"></div>
#
# 		</span>
#
# 	</a>
#
#
# </div>

    patron  = '<a class="muestra-escena"\s*href="([^"]+)".*?data-stats-video-name="([^"]+)".*?<img src="([^"]+)".*?<span class="ico-minutos sprite" title="Length"></span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a href="/page2.html">Siguiente</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)">Siguiente</a></li>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#<source src="https://cdnlw5.pornburst.xxx/videos/7/5/3/d/0/753d089e2237072291546a90031cb9de6f67e055.mp4?key=0TqmSr5xG63ZBLbJm5NRsWAKWFcnHbWv663nl3RIP5GH_ALlFwoJTV0NXFCEnQVCSb_XLTZGMThevQ1c7OZP1TODpETq3in6rp32R5NuTQUepGs66y2SYUrG5bx3kHG_43AkH931QLLMejVFmJEiKogotxG348K8omyGmokL0wDKivsJ_2qkMVhBZh5XdBKliRvsePUhA4Q3S5iRAYaBjBEcymIrqFq3sCephprilfM" type="video/mp4" />


    patron  = '<source src="([^"]+)" type="video/mp4"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
#        scrapedurl = "http:" + scrapedurl.replace("\\", "")
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist




'''
def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
