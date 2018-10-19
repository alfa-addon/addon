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

host = 'http://es.foxtube.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/buscador/%s" % texto

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


#   <li class="bgco1"><a class="tco2" href="/videos/actrices-porno/">Actrices porno</a></li>
    patron  = '<li class="bgco1"><a class="tco2" href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


# <a class="thumb tco1" href="/videos/anissa-kate-seduce-jefe-folla-aparcamiento-12885.shtml">
# <figure>
# <img id="v_12885" src="http://v.fxtimg.com/12885/x12885.jpg.pagespeed.ic.-_WyiNYRaH.jpg" data-origen="http://v.fxtimg.com/12885/12885.jpg" class="" alt="Anissa Kate seduce a su jefe y folla con él en el aparcamiento">
# <figcaption class="titulo">
# Anissa Kate seduce a su jefe y folla con él en el aparcamiento
# </figcaption>
# </figure>
# <span class="t">
# <i class="m tc2">24:12</i>
# <i class="tc2">7.7</i> </span> </a>

# <a class="thumb tco1" href="/videos/una-explosiva-rubia-con-gargantilla-goza-follando-con-sus-amantes-negros-16088.shtml">
# <figure>
# <img id="v_16088" src="http://v.fxtimg.com/16088/16088.jpg.pagespeed.ce.bJnaUCnSOF.jpg" data-origen="http://v.fxtimg.com/16088/16088.jpg" class="r" alt="Una explosiva rubia con gargantilla goza follando con sus amantes negros">
# <figcaption class="titulo">
# Una explosiva rubia con gargantilla goza follando con sus amantes negros
# </figcaption>
# </figure>
# <span class="t">
# <i class="m tc2">24:00</i>
# <i class="tc2">9.5</i>
# </span>
# </a>                     http://es.foxtube.com/videos/una-explosiva-rubia-con-gargantilla-goza-follando-con-sus-amantes-negros-16088.shtml



    patron  = '<a class="thumb tco1" href="([^"]+)">.*?src="([^"]+)".*?alt="([^"]+)">.*?<i class="m tc2">(.*?)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        url = host + scrapedurl

        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))





#            <a class="bgco2 tco3" rel="next" href="/videos/4/">&gt</a>
    else:
            patron  = '<a class="bgco2 tco3" rel="next" href="([^"]+)">&gt</a>'
            next_page = re.compile(patron,re.DOTALL).findall(data)
            next_page = item.url +next_page[0]
            itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)

    url = scrapertools.find_single_match(scrapertools.cachePage(item.url),'<iframe src="([^"]+)"')
    data = httptools.downloadpage(url).data

        # html5player.setVideoUrlLow('https://video-hw.xvideos-cdn.com/videos/3gp/c/4/f/xvideos.com_c4f7b07451429bbadb7c6c89f559de23.mp4?e=1531685223&ri=1024&rs=85&h=de48cf4eddd8bd3cd666160332609271');
	    # html5player.setVideoUrlHigh('https://video-hw.xvideos-cdn.com/videos/mp4/c/4/f/xvideos.com_c4f7b07451429bbadb7c6c89f559de23.mp4?e=1531685223&ri=1024&rs=85&h=bb66dbd7fae92e317008d7132b0f15ae');
	    # html5player.setVideoHLS('https://xvideos-im-c16f3400-23673092-hls.s.loris.llnwd.net/1531685223/111/d77c4e6a5170d2bb4fa1dae2e23a686c/videos/hls/c4/f7/b0/c4f7b07451429bbadb7c6c89f559de23/hls.m3u8');

#    patron  = 'sources\":\["(.*?)"'

#<div class="aspect"><iframe src="https://flashservice.xvideos.com/embedframe/23673092" frameborder=0 width="100%" height="100%" scrolling=no allowfullscreen></iframe></div>


    patron  = 'html5player.setVideoUrlHigh\\(\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("\/", "/")
        itemlist.append(Item(channel=item.channel, action="play", title=scrapedurl, fulltitle=scrapedurl, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

#        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
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
'''
