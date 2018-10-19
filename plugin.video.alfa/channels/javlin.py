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

host = 'http://javl.in'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "MOVIES" + "[/COLOR]" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="Mas Votado" , action="catalogo", url=host + "/videos/most-liked/"))
    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Categorias" + "[/COLOR]" , action="categorias", url=host))
#    itemlist.append( Item(channel=item.channel, title="       Censored" , action="peliculas", url=host + "/category/censored/"))

#    itemlist.append( Item(channel=item.channel, title="       Uncensored" , action="peliculas", url=host + "/category/uncensored/"))
#    itemlist.append( Item(channel=item.channel, title="catalogo" , action="catalogo", url=host))

    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
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


def sub_search(item):
    logger.info()

    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    # <div class="row">
	# 		<a href="http://gnula.mobi/16160/pelicula/sicario-2015/" title="Sicario (2015)">
	# 			<img src="http://image.tmdb.org/t/p/w300/voDX6lrA37mtk1pVVluVn9KI0us.jpg" title="Sicario (2015)" alt="Sicario (2015)" />
	# 		</a>
	# </div>

    patron = '<div class="row">.*?<a href="([^"]+)" title="([^"]+)">.*?<img src="(.*?)" title'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url,name,img   in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", show=name, thumbnail=img))

# <a href="http://gnula.mobi/page/2/?s=la" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a></div>

    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion))

    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'>Scenes</a>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#           <li class="cat-item cat-item-114"><a href="http://justporn.to/category/genre/all-sex/" >All Sex</a>

    patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)" >(.*?)</a>'
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
#    data = scrapertools.get_match(data,'>Genre</a>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#          <option class="level-0" value="2288">Transsexual&nbsp;&nbsp;(76)</option>

    patron  = '<option class="level-0" value="([^"]+)">([^"]+)&nbsp;&nbsp;\((.*?)\)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,number in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle) + " ("+ str(number) + ")"
        scrapedurl = "http://javl.in/?cat=" + scrapedurl
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="ntitle1">Newest video:</div></td>(.*?)</table>')



    patron = '<div class="featured-wrap clearfix">.*?<a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"'
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

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#      <li><a rel='nofollow' href='http://kentet.net/category/asian/page/2/' class='inactive'>Next <i class='fa fa-angle-right'></i></a></li>

# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<li><a rel=\'nofollow\' href=\'([^\']+)\' class=\'inactive\'>Next')

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
    itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )
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
