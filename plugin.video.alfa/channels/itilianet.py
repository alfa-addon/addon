# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys


from core import tmdb
from core import httptools
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

## italiafilm

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

__channel__ = "itilianet"
__category__ = "F"
__type__ = "generic"
__title__ = "itilianet"
__language__ = "EN"

DEBUG = config.get_setting("debug")

host = 'http://itilia.net'

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.itilianet mainlist")
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.vintagetube.club/tube/last-1/" http://www.vintagetube.club/tube/popular-1/



    itemlist.append( Item(channel=__channel__, title="CLIPS" , action="peliculas", url=host))
#    itemlist.append( Item(channel=__channel__, title="Mas Votado" , action="catalogo", url=host + "/videos/most-liked/"))
#    itemlist.append( Item(channel=__channel__, title="[COLOR yellow]" + "Categorias" + "[/COLOR]" , action="categorias", url=host))

    itemlist.append( Item(channel=__channel__, title="JAV" , action="peliculas", url=host + "/category/jav/"))
#    itemlist.append( Item(channel=__channel__, title="catalogo" , action="catalogo", url=host))

    itemlist.append( Item(channel=__channel__, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = host+ "/?s=%s" % texto

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
    logger.info("pelisalacarta.itilianet peliculas")
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="ntitle1">Newest video:</div></td>(.*?)</table>')

# <div class="content_box_out ">
# <div class="content_box_in ">
# <div class="content_align">
# <div class="post excerpt">
# <div class="headerCategory">
# <span>XXX HD Movies</span> </div>
# <a href="http://itilia.net/montyspov-emma-louise-school-uniform/" title="MontysPOV – Emma Louise – School Uniform" rel="nofollow" id="featured-thumbnail">
# <div class="featured-thumbnail"><img width="300" height="165" src="http://itilia.net/wp-content/uploads/2017/03/hryjyj-300x165.jpg" class="attachment-featured size-featured wp-post-image" alt="" title=""/></div> </a>
# <header>
# <h2 class="title">
# <a href="http://itilia.net/montyspov-emma-louise-school-uniform/" title="MontysPOV – Emma Louise – School Uniform" rel="bookmark">MontysPOV – Emma Louise – School Uniform</a>
# </h2>
# </header>
# <div class="post-container">
# <div class="post-info">
# By <a rel="nofollow" href="http://itilia.net/author/admin/" title="Posts by admin" rel="author">admin</a> On March 27, 2017 In <a href="http://itilia.net/category/xxx-movies/">XXX HD Movies</a> </div>
# <div class="post-content image-caption-format-1">
# &nbsp; Stream 1 Stream 2 &nbsp; Download it now &nbsp; </div>
# <div class="readMore"><a href="http://itilia.net/montyspov-emma-louise-school-uniform/" title="MontysPOV – Emma Louise – School Uniform" rel="bookmark">More</a></div>
# </div>


    patron = '<div class="headerCategory">.*?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"'
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
        if (DEBUG):
            logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=__channel__, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#      <li><a rel='nofollow' href='http://itilia.net/page/2/' class='inactive'>Next &rsaquo;</a></li>

# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<li><a rel=\'nofollow\' href=\'([^\']+)\' class=\'inactive\'>Next &rsaquo;</a></li>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__ , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info("pelisalacarta.itilianet findvideos")
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

# <div class="entry-content">
# <p><a href="http://securely.link/AE5a4" target="_blank"><img src="http://securely.link/edgvN"/></a><span id="more-446801"></span></p>
# <p>  Streaming and Download Links:<br/>
# <a href="http://securely.link/NmwZ0" target="_blank">Streaming Openload.co</a><br/>
# <a href="http://securely.link/VCmPq" target="_blank">Download Depfile.com</a><br/>
# <a href="http://securely.link/nWRZH" target="_blank">Streaming Vidlox.tv</a>
# </p>
# <p>0:31:15 | 1920&#215;1080 | mp4 | 2185Mb</p>
# <p><a href="http://securely.link/3Wy4r" target="_blank"><img src="http://securely.link/96K5V"/></a> </p>
# </div>


#    data = scrapertools.get_match(data,'Streaming and Download Links:(.*?)</p>')
    patron = '<a href="([^"]+)" target="_blank">Streaming Openload.co</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

#    scrapedurl = scrapertools.find_single_match(data,'<iframe width=.*?src=\'(.*?)\'')
#    scrapedurl = str(scrapedurl)
    for scrapedurl in matches:
        scrapedplot = ""
#        scrapedtitle = str(scrapedtitle)

    data = httptools.downloadpage(scrapedurl).data
                                    #   <meta name="og:url" content="https://openload.co/f/g4jhL_GU8b0/yjh54u57_7.mp4">
                                    #   sources: ["https://c13.vidlox.tv/hls/,oudvgk2tljtk2yixv66oefz6dtry5erk43vu3q545arp5cmieycmnivdzmgq,.urlset/master.m3u8","https://c13.vidlox.tv/oudvgk2tljtk2yixv66oefz6dtry5erk43vu3q545arp5cmieycmnivdzmgq/v.mp4"],

    scrapedurl = scrapertools.find_single_match(data,'<meta name="og:url" content="(.*?)">')

    if (DEBUG):
        logger.info("title=["+scrapedurl+"], url=["+scrapedurl+"]")
    itemlist.append(item.clone(channel=__channel__, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
    return itemlist



def play(item):
    logger.info("pelisalacarta.itilianet play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''

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
