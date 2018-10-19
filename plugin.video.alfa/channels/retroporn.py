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

## italiafilm                                             \'([^\']+)\'

host = 'http://www.retroporn.me'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Top" , action="peliculas", url=host, plot= "/group/All/"))
    itemlist.append( Item(channel=item.channel, title="Novedades" , action="peliculas", url=host + "/group/All/new-1.html", plot= "/group/All/"))
#    itemlist.append( Item(channel=item.channel, title="Duracion" , action="peliculas", url=host + "/all-longest/1/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/popular-1.html" % texto
    item.plot = "/search/%s/" % texto
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
    data = scrapertools.get_match(data,'<h2>Retro Categories:</h2>(.*?)</div>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#   <li><a href="/group/1960s/popular-1.html">1960s</a></li>

    patron  = '<li><a href="([^"]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = scrapedurl.replace("popular-1.html", "" )
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
#    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)Son &raquo;</a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


#                 <div class="prev">
#     <a href="/real.php?tube=/tube/dear-diary-i-wanked-out-again.html">
#         <img src="http://cdn.vintagetube.pro/content/37/333_Diary.jpg" >
#         <span class="prev-tit">Dear Diary, I Wanked Out Again</span>
#     </a>
#     <div class="prev-dur"><span>1:17:42</span></div>
# </div>


    patron  = '<div class="prev">.*?<a href="([^"]+)".*?<img src="([^"]+)".*?<span class="prev-tit">([^"]+)</span>.*?<div class="prev-dur"><span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
#        title = scrapedtitle
        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        scrapedurl = scrapedurl.replace("/real.php?tube=", "")
        scrapedurl = host + scrapedurl

        thumbnail = scrapedthumbnail
        plot = item.plot
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))



#
#                    <li><a href="/group/All/popular-2.html" target="_self"><span class="page">NEXT</span></a></li>

# "Next page >>"
    else:
        patron  = '<li><a href="([^"]+)" target="_self"><span class="page">NEXT</span></a></li>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        plot = item.plot
        next_page =  next_page[0]
        next_page = next_page.replace("/group/All/" , "")
        next_page = host + plot + next_page
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page, plot=plot ) )
    return itemlist


def play(item):
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

    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist
    # itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    # return itemlist
'''
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
