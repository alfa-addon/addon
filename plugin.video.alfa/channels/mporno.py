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

host = 'http://mporno.tv'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Top" , action="peliculas", url=host, plot=""))
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/most-recent/", plot="/most-recent/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/top-rated/", plot="/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas vistas" , action="peliculas", url=host + "/most-viewed/", plot="/most-viewed/"))
    itemlist.append( Item(channel=item.channel, title="Duracion" , action="peliculas", url=host + "/longest/", plot="/longest/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/videos/%s/page1.html" % texto

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
#    data = scrapertools.get_match(data,'<h2>Retro Categories:</h2>(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <div class="content content-channel ">
#     <div class="bg">
#         <div class="img">
#             <a href="http://mporno.unblckd.top/channels/14/18/page1.html">
#                             <img class="content_image" src="http://mporno.unblckd.top/core/images/catdefault.jpg" alt="18"   width="453">
# 				<div class="overlay"></div>
#                         </a>
# 		</div>
#         <div class="text">
#             <h3><a href="http://mporno.unblckd.top/channels/14/18/page1.html">18</a> <small>(903)</small></h3>
#         </div>
#     </div>
# </div>

    patron  = '<h3><a href="([^"]+)">(.*?)</a> <small>(.*?)</small></h3>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = scrapedurl.replace("http://mporno.unblckd.org/", "").replace("page1.html", "")
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + "  " + cantidad
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


# <div class="content ">
#     <div class="bg">
#         <div class="img">
#         <a href="http://mporno.unblckd.top/video/amazing-teen-getting-her-pussy-eaten-before-she-starts-to-suck-4678.html">
# 		            <script type='text/javascript'>stat['592ac84e5464a']=0; pic['592ac84e5464a']=new Array(); pics['592ac84e5464a']=new Array(1,1,1,1,1,1,1,1,1,1);</script>
#             <img class="content_image" src="http://mporno.unblckd.top/mediap/thumbs/5/5/1/1/9/5511990ebdd5a4270646.mp4/5511990ebdd5a4270646.mp4-3.jpg" alt="Amazing Teen Getting Her Pussy Eaten Before She Starts To Suck" id="592ac84e5464a" onmouseover='startm("592ac84e5464a","http://mporno.unblckd.top/mediap/thumbs/5/5/1/1/9/5511990ebdd5a4270646.mp4/5511990ebdd5a4270646.mp4-",".jpg");' onmouseout='endm("592ac84e5464a"); this.src="http://mporno.unblckd.top/mediap/thumbs/5/5/1/1/9/5511990ebdd5a4270646.mp4/5511990ebdd5a4270646.mp4-3.jpg";'  width="453"  height="315">
# 			<div class="overlay"></div>
#
# 		</a>
#         </div>
#         <div class="text">
#             <h3><a href="http://mporno.unblckd.top/video/amazing-teen-getting-her-pussy-eaten-before-she-starts-to-suck-4678.html">Amazing Teen Getting...</a></h3>
#             <span class="rating">
# 				<span class="star_off"><span class="star_on">44%</span></span>
# 			</span>
#         </div>
#     </div>
# </div>
# http://mporno.unblckd.top/mediap/thumbs/5/5/1/1/9/5511990ebdd5a4270646.mp4/5511990ebdd5a4270646.mp4-
# http://mporno.unblckd.top/mediap/videos/5/5/1/1/9/5511990ebdd5a4270646.mp4


    patron  = '<div class="content ">.*?<img class="content_image" src="([^"]+).mp4/.*?" alt="([^"]+)".*?this.src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        scrapedurl = scrapedurl.replace("/thumbs/", "/videos/") + ".mp4"

        thumbnail = scrapedthumbnail
        plot = item.plot
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))



#
#                    <a href='page2.html' class="next">Next &gt;&gt;</a>

# "Next page >>"
    else:
        patron  = '<a href=\'([^\']+)\' class="next">Next &gt;&gt;</a>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
#        next_page = scrapertools.find_single_match(data,'class="last" title=.*?<a href="([^"]+)">')
        plot = item.plot
        next_page =  next_page[0]
        next_page = host + plot + next_page
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page, plot=plot ) )
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    #       <iframe frameborder=0 scrolling="no"  src='http://www.playercdn.com/ec/embed.php?b64=PGlmcmFtZSBzcmM9Imh0dHA6Ly93d3cucGxheWVyY2RuLmNvbS9lYy9pMi5waHA_dXJsPWFIUjBjRG92TDNkM2R5NXdiM0p1YUhWaUxtTnZiUzkyYVdWM1gzWnBaR1Z2TG5Cb2NEOTJhV1YzYTJWNVBYQm9OVGN3T1RReFpEUmpNbVEyWWc9PSIgc2Nyb2xsaW5nPSJubyIgbWFyZ2lud2lkdGg9IjAiIG1hcmdpbmhlaWdodD0iMCIgZnJhbWVib3JkZXI9IjAiIGFsbG93ZnVsbHNjcmVlbj48L2lmcmFtZT4.'></iframe>

    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'(.*?)\'')

#      <iframe src="http://www.playercdn.com/ec/i2.php?url=aHR0cDovL3d3dy5wb3JuaHViLmNvbS92aWV3X3ZpZGVvLnBocD92aWV3a2V5PXBoNTcwOTQxZDRjMmQ2Yg==" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" allowfullscreen></iframe>

    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')

    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<source src="(.*?)"')


    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
#    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
