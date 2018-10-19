# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
#
#
#
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



host = 'http://porneq.com'


def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     /show/big+tits

    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/videos/browse/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistos" , action="peliculas", url=host + "/videos/most-viewed/"))
    itemlist.append( Item(channel=item.channel, title="Mas Votado" , action="peliculas", url=host + "/videos/most-liked/"))
    itemlist.append( Item(channel=item.channel, title="Big Tits" , action="peliculas", url=host + "/show/big+tits&sort=w"))
#    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/show/%s" % texto

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

#    data = httptools.downloadpage(item.url).data

    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')



# <div id="video-7485096" class="video">
# <div class="video-thumb">
# 		<a class="clip-link" data-id="7485096" title="CastingCouch HD 18 02 16 Keilani XXX MP4 KTR cchd 18 02 16 keilani" href="http://porneq.com/video/7485096/castingcouch-hd-18-02-16-keilani-xxx-mp4-ktr-cchd-18-02-16-keilani/">
# 			<span class="clip">
# 				<img src="http://porneq.com/media/porn12/thumbs/1434/CastingCouch-HD-18-02-16-Keilani-XXX-MP4-KTR-rarbg-cchd-18-02-16-keilani-360p-hdt6KhiE95x.jpg" alt="CastingCouch HD 18 02 16 Keilani XXX MP4 KTR cchd 18 02 16 keilani" /><span class="vertical-align"></span>
# 			</span>
#           	<span class="overlay"></span>
# 		</a><a class="heartit" title="Like this video" href="javascript:iLikeThis(7485096)"><i class="icon-heart"></i></a>   <span class="timer">1:00:35</span></div>
# <div class="video-data">
# 	<h4 class="video-title"><a href="http://porneq.com/video/7485096/castingcouch-hd-18-02-16-keilani-xxx-mp4-ktr-cchd-18-02-16-keilani/" title="CastingCouch HD 18 02 16 Keilani XXX MP4 KTR cchd 18 02 16 keilani">CastingCouch HD 18 02 16 Keilani XXX MP4 KTR cchd 18 02 16 keilani</a></h4>
# <ul class="stats">
# <li>		by <a href="http://porneq.com/profile/nutcracker302/948/" title="nutcracker302">nutcracker302</a></li>
#  <li>156,052 views</li><li></li></ul>
# </div>
# 	</div>

    patron = '<a class="clip-link" data-id="\d+" title="([^"]+)" href="([^"]+)">.*?<img src="([^"]+)".*?<span class="timer">(.*?)</span></div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    scrapertools.printMatches(matches)


    for scrapedtitle,scrapedurl,scrapedthumbnail,scrapedtime in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + scrapedtitle
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = "https://hqcollect.tv" + scrapedurl
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )



# <li><a class="next" href="http://porneq.com/channel/porn-videos/1/&p=2">»</a></li>
#   <nav id="page_nav"><a href="http://porneq.com/videos/browse/&ajax&p=2"></a></nav>

# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<nav id="page_nav"><a href="(.*?)"')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist


def play(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

# jwplayer("video-setup").setup({   file: "http://porneq.com/media/porn9/videos/626/mofoxxx-executsec-sd-tpb-360p-8ccRa8ONjNH.mp4"
# jwplayer("video-setup").setup({   file: "http://porneq.com/media/porn3/videos/682/GirlsDoPorn-Episode-170-E170-18-Years-Old-GirlsDoPorn-Episode-170-E170-18-Years-Old-360p-baN4IsDpjYl.mp4",

    patron = '"video-setup".*?file: "(.*?)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl in matches:

#        scrapedurl = scrapertools.find_single_match(data,'"video-setup".*?file: "(.*?)",')
        scrapedurl = str(scrapedurl)


    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                        thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist
    # itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
    # return itemlist


'''
def play(item):
    logger.info("pelisalacarta.porneq play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''
