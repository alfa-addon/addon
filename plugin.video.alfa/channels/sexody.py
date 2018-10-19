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

host = 'http://sexodx.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="New" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Castellano" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-espanol/"))
#    itemlist.append( Item(channel=item.channel, title="Latino" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-latino/"))
#    itemlist.append( Item(channel=item.channel, title="VO" , action="peliculas", url="http://www.tupelicula.tv/filter?language=3"))
#    itemlist.append( Item(channel=item.channel, title="Portugues" , action="peliculas", url="http://www.tupelicula.tv/filter?language=5"))
#    itemlist.append( Item(channel=item.channel, title="VOS" , action="peliculas", url="http://peliculasm.tv/peliculas-idioma-sub-espanol/"))
#    itemlist.append( Item(channel=item.channel, title="Año" , action="anual", url="http://flvpeliculas.org/"))
#    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url="http://pornboss.org/category/movies/"))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto

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
    data = scrapertools.cachePage(item.url)

#             <li><a class="icob icoa pore brdr5px fx" title="Películas de Accion" href="http://peliculasm.tv/peliculas-accion/">Películas de Accion</a></li>

    patron  = '<li><a href="([^<]+)" title="([^<]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle.replace("Pelculas de ", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def anual(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#             <li><a href="http://www.flvpeliculas.org/category/estreno-2012">Estrenos 2012</a></li>
    patron  = '<li><a href="([^<]+)">Estrenos ([^<]+)</a>'
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
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

        # <li class="collection column small-12 medium-8">
        #     <div class="overflow"><a href="/video/cnvvsvs" title="Woodman Casting - Casey Calvert "><span class="responsive_border_md animated"><img src="http://img.sexodx.com/photo/8199393/7/3/woodman-casting-casey-calvert.png?checksum_id=3186525" style="height:150px;"><span class="badge_rating safe white" style="font-size:13px;; position:relative; float:right;;margin-top:-25px;margin-right:5px;z-index:10;"><i class="fa fa-clock-o"></i> 1:08:16</span></span><span class="txt_md">Woodman Casting - Casey Calvert </span></a>
        #     </div>
        # </li>


    patron  = '<div class="overflow"><a href="([^"]+)" title="(.*?)".*?<img src="([^"]+)".*?<i class="fa fa-clock-o"></i>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,time in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        http://sexody.com/embed/video/cnvvsvs http://stream.freedisc.pl/video/8770361/myfriendshotgirl-kimber-woods.mp4?checksum_id=3311924
        scrapedurl = host + scrapedurl

#        "embedUrl": "http://sexodx.com/static/player/v58/player.swf?file=https://stream.freedisc.pl/video/10061852/blacksonblondes-haley-reed.mp4?checksum_id=3705928&player=html5"


        data2 = scrapertools.cachePage(scrapedurl)
        scrapedurl = scrapertools.find_single_match(data2,'"embedUrl": "([^"]+)"')
        scrapedurl = scrapedurl.replace("http://sexodx.com/static/player/v58/player.swf?file=","")


        itemlist.append( Item(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl, thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

# <div class="pagination">
#     <div class="page-list"><span class="page page-current"><span class="page-current-mark"></span>1</span><a class="page page-link larger" href="/hot/month/2">2</a><a class="page page-link larger" href="/hot/month/3">3</a>
#     </div><a class="page page-direction page-next" href="/hot/month/2">Następna <span class="arrow-next arrow-text">→</span></a>

#  "Next Page >>"
    next_page_url = scrapertools.find_single_match(data,'<a class="page page-direction page-next" href="([^"]+)">')
    next_page_url = host + next_page_url
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist



'''
def findvideos(item):
    logger.info("pelisalacarta.a0 findvideos")
    itemlist = []
#    data = scrapertools.cachePage(item.url)


# url=[    <a href='http://streamcloud.eu/rhpjy8z5k621/Angel_Smalls.mp4.html' target='_blank'><img src='/player.jpg'/></a>
#                                             <a href='http://streamcloud.eu/r4o1lylniz4r/Eden_Sin.mp4.html' target='_blank'><img src='/player.jpg'/></a>
#                                             <a href='http://streamcloud.eu/7gfdk5pez34c/Marica_Hase.mp4.html' target='_blank'><img src='/player.jpg'/></a>
#                                             <a href='http://streamcloud.eu/rmxeeggzoj7g/Nicole_Clitman.mp4.html' target='_blank'><img src='/player.jpg'/></a>
#
#                                                 <br><br><br>
#                                             ]

#<button class="btn btn-hoster btn-sm" onclick="load_hoster('http://streamhive.tv/embed/528207733881', '', 1338);">Streamhive.tv</button>
#<button class="btn btn-hoster btn-sm" onclick="load_hoster('https://openload.co/embed/fUCAoHiXLAU/', '', 1329);">Openload.co</button>


#    patron  = '<a href=\'([^\']+)\' target'
#    matches = re.compile(patron,re.DOTALL).findall(url)

#    <strong>Calidad:</strong> HD Rip</p>
#    calidad = scrapertools.find_single_match(data,'<strong>Calidad:</strong>(.*?)</p>')

#      url = str(url)
#    for match in matches:
#        url = scrapertools.find_single_match(url,'<a href=\'([^\']+)\' target')
#        url = url.replace("'","").replace("load_hoster(","")
#        url = str(url)
#<li><a href="#ms1">VER LATINO</a></li> <li><a href="#ms2">VER CASTELLANO</a></li> <li><a href="#ms3">VER SUBTITULADO</a></li>
     #
    #  patron  = '<li><a href="#ms(.*?)</li>'
    #  matche2 = re.compile(patron,re.DOTALL).findall(data)
    #  for match in matche2:
    #      idioma = scrapertools.find_single_match(match,'">VER(.*?)</a>')

#        url = "http://www.tripledeseo.com/"+url
#        idioma = scrapertools.find_single_match(match,'<div class="calidad-txt">(.*?)</div>')

#       calidad = calidad.replace("Ahora en ", "")

    #    title = str(calidad)

        itemlist.append(item.clone(action="play", title=url, url=url))

# <div class="vid-play vid-loading" vid="2243" id="vid-play">
#         <iframe src="http://www.wankz.com/embed/1381768" scrolling="no" frameborder="0" width="100%" height="100%" data-id="1435" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true" id="iframe-play"></iframe>
# </div>

    # patron  = '<div class="vid-play(.*?)</div>'
    # matches = re.compile(patron,re.DOTALL).findall(data)
    # for match in matches:
    #     url = scrapertools.find_single_match(match,'<iframe src="([^"]+)" scrolling=')
    #     itemlist.append(item.clone(action="play", title=url, url=url))

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



# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    peliculas_items = peliculas(mainlist_items[0])
    bien = False
    for pelicula_item in peliculas_items:
        mirrors = servertools.find_video_items( item=pelicula_item )
        if len(mirrors)>0:
            bien = True
            break

    return bien
