# -*- coding: utf-8 -*-
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


host = 'https://spankbang.xxx'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="peliculas", url= host + "/new_videos/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorados" , action="peliculas", url=host + "/wall-note-1.html"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="peliculas", url= host + "/wall-main-1.html"))
    itemlist.append( Item(channel=item.channel, title="Mas largos" , action="peliculas", url= host + "/wall-time-1.html"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search-%s-1.html" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '&nbsp;<a href="([^"]+)" class="link1">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = scrapedurl.replace(".html", "_date.html")
        scrapedurl = host +"/" + scrapedurl
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    # data = httptools.downloadpage(item.url).data
    data = scrapertools.cachePage(item.url)
    
    # <div class="video-item" data-id="4652797">
# <a href="/2rq4d/video/yenlomfc" class="thumb ">
# <img src="//static.spankbang.com/static_desktop/Images/blank.png" data-src="//cdnthumb3.spankbang.com/250/4/6/4652797-t6.jpg" alt="yenlomfc" class="cover lazyload has_mp4" />
# <span class="play fa fa-play-circle-o fa-3x"></span>
# <span class="i-len"><i class="fa fa-clock-o"></i> 73</span>
# </a>
# <span class="i-wl" onclick="add_wl(4652797, this)" title="Add to watch later"><i class="fa fa-clock-o"></i><strong>Watch later</strong></span>
# <span class="i-fav" onclick="add_fav(4652797, this)" title="Add to favorites"><i class="fa fa-heart"></i><strong>Favorite</strong></span>
# <span class="i-flag" onclick="show_flag(4652797)" title="Report"><i class="fa fa-flag"></i><strong>Report</strong></span>
# <div class="inf">yenlomfc</div>
# <ul>
# <li>Hace 11 minutos</li>
# <li><i class="fa fa-eye"></i> 60</li>
# <li><i class="fa fa-thumbs-o-up"></i> 100%</li>
# </ul>
# </div>
# <div class="video-item" data-id="4652795">
# <a href="/2rq4b/video/penny+underbust+playstation+modeling" class="thumb ">
# <img src="//static.spankbang.com/static_desktop/Images/blank.png" data-src="//cdnthumb1.spankbang.com/250/4/6/4652795-t6.jpg" alt="Penny Underbust Playstation Modeling" class="cover lazyload " />
# <span class="play fa fa-play-circle-o fa-3x"></span>
# <span class="i-hd">1080p</span>
# <span class="i-len"><i class="fa fa-clock-o"></i> 3</span>
# </a>
# <span class="i-wl" onclick="add_wl(4652795, this)" title="Add to watch later"><i class="fa fa-clock-o"></i><strong>Watch later</strong></span>
# <span class="i-fav" onclick="add_fav(4652795, this)" title="Add to favorites"><i class="fa fa-heart"></i><strong>Favorite</strong></span>
# <span class="i-flag" onclick="show_flag(4652795)" title="Report"><i class="fa fa-flag"></i><strong>Report</strong></span>
# <div class="inf">Penny Underbust Playstation Modeling</div>
# <ul>
# <li>Hace 12 minutos</li>
# <li><i class="fa fa-eye"></i> 99</li>
# <li><i class="fa fa-thumbs-o-up"></i> 100%</li>
# </ul>
# </div>
    
    
    
    patron = '<div class="video-item" data-id="\d+">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '<i class="fa fa-clock-o"></i>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        # http://cdnthumb1.spankbang.com/250/4/6/4652755-t6.jpg
        thumbnail = "http:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))
# <li class="next"><a href="/new_videos/2/">&raquo;</a></li>
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Página Siguiente >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'servervideo = \'([^\']+)\'.*?'
    patron += 'path = \'([^\']+)\'.*?'
    patron += 'filee = \'([^\']+)\'.*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for servervideo,path,filee  in matches:
        scrapedurl = servervideo + path + "56ea912c4df934c216c352fa8d623af3" + filee
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
    return itemlist

