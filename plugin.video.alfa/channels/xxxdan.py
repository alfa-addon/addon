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

host = 'http://xxxdan.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular30"))
    itemlist.append( Item(channel=item.channel, title="Dururacion" , action="peliculas", url=host + "/longest"))
    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/channel30/hd"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?query=%s" % texto

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



    patron  = '<li><a href="([^"]+)" title="">.*?<span class="videos-count">([^"]+)</span><span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="dropdown-menu">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

     # <li><figure>
     #            <a href="http://xxxdan.com/channel/hardcore" rel="tag" class="img"
     #               title="hardcore">
     #                <img class="lazy" data-original="http://t0.cdn3x.com/xd/320x180/D90Zm/000.jpg" alt="hardcore" width="240" height="180" />
     #            </a>
     #        </figure><figcaption>
     #            <a href="http://xxxdan.com/channel/hardcore" rel="tag">hardcore<span class="score">51562</span></a>
     #        </figcaption></li>

    patron  = '<a href="([^"]+)" rel="tag".*?title="([^"]+)".*?data-original="([^"]+)".*?<span class="score">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = scrapedurl.replace("channel", "channel30")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="video-embed">(.*?)</div>')

# <li><figure>
#         <a href="http://xxxdan.com/PMYMO/sunbathing-mom-surprised.html" class="img  " title="sunbathing mom surprised"
#             data-animation="http://t1.cdn3x.com/xd/PMYMO/p_0001702581_240_25_10_1.mp4"             data-thumb="0" data-id="PMYMO">
#                             <img class="lazy" data-original="http://t0.cdn3x.com/xd/320x180/PMYMO/000.jpg" alt="sunbathing mom surprised" width="240" height="180" />
#                     </a>
#         <figcaption>
#                             <a href="http://xxxdan.com/PMYMO/sunbathing-mom-surprised.html" title="sunbathing mom surprised">sunbathing mom surprised</a>
#                         <ul class="properties">
#                 <li class="dur"><time datetime="PT11M44S">11:44</time>
#                 <li class="pubtime">2 days ago</li>
#                                             </ul>
#         </figcaption>
#     </figure></li>

    patron  = '<li><figure>\s*<a href="([^"]+)" class="img\s*" title="([^"]+)".*?data-original="([^"]+)".*?<time datetime="\w+">([^"]+)</time>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        url = scrapedurl
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a href="newest/2" rel="next">&rarr;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">&rarr;</a>')

    if next_page_url!="":
        next_page_url = next_page_url.replace("http://xxxdan.com/","")
        next_page_url = "/" + next_page_url
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
    data = scrapertools.cache_page(item.url)

#sources.push({type:'video/mp4',src:'http://c20.cdn3x.com/xd/LcUMouIXhQfFkSVzQ8DOEw/Be7xd77sPOHvMo4'});

    media_url = scrapertools.find_single_match(data, 'src:\'([^\']+)\'')

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist
'''
def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

 #sources.push({type:'video/mp4',src:'http://c20.cdn3x.com/xd/LcUMouIXhQfFkSVzQ8DOEw/Be7xd77sPOHvMo4'});

    patron  = 'src:\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
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
