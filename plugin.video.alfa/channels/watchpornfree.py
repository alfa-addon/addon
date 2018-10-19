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

# https://playpornfree.org/    https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/

host = 'https://watchpornfree.ws'

def mainlist(item):
    logger.info("")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/movies"))
    itemlist.append( Item(channel=item.channel, title="Parodia" , action="peliculas", url=host + "/category/parodies"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host + "/category/clips-scenes"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Año" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = "http://watchpornx.com/?s=%s" % texto

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
    logger.info("")
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data


    if item.title == "Canal":
        data = scrapertools.get_match(data,'>Studios</a>(.*?)</ul>')
    if item.title == "Año":
        data = scrapertools.get_match(data,'>Years</a>(.*?)</ul>')
    if item.title == "Categorias":
        data = scrapertools.get_match(data,'>XXX Genres</div>(.*?)</ul>')


    patron  = '<a href="(.*?)".*?>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle  in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " ("+cantidad+")"
#        scrapedtitle = scrapedtitle.replace("Pelculas de ", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
#        scrapedthumbnail ="http://www.porntrex.com" + scrapedthumbnail
#        scrapedurl ="http://www.porntrex.com" + scrapedurl

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def peliculas(item):
    logger.info("")
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

   # <article class="TPost B">
   #      <a href="https://watchpornfree.ws/teen-brazil-16-watch-online-free">
   #          <div class="Image">
   #              <figure class="Objf TpMvPlay AAIco-play_arrow"><img width="500" height="709" src="https://watchpornfree.ws/wp-content/uploads/2018/05/1527228150_1511258069_1510730200_1940674h.jpg" class="attachment-img-mov-md size-img-mov-md wp-post-image" alt="" srcset="https://watchpornfree.ws/wp-content/uploads/2018/05/1527228150_1511258069_1510730200_1940674h.jpg 500w, https://watchpornfree.ws/wp-content/uploads/2018/05/1527228150_1511258069_1510730200_1940674h-212x300.jpg 212w, https://watchpornfree.ws/wp-content/uploads/2018/05/1527228150_1511258069_1510730200_1940674h-71x100.jpg 71w, https://watchpornfree.ws/wp-content/uploads/2018/05/1527228150_1511258069_1510730200_1940674h-160x227.jpg 160w" sizes="(max-width: 500px) 100vw, 500px" /></figure>
   #                          </div>
   #          <div class="Title">Teen Brazil 16</div>        </a>
   #          </article>

    patron  = '<article class="TPost B">.*?<a href="([^"]+)">.*?src="([^"]+)".*?<div class="Title">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)



    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedtitle = scrapedtitle + str(duration)
        # scrapedurl = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", scrapedurl)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        scrapedthumbnail = "http://www.xxxparodyhd.com" + scrapedthumbnail

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl, thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

# <div id="paginador">
# <div class='paginado'><span class='current'>1</span>
# <a rel='nofollow' class='page larger' href='http://watchpornx.net/page/2'>2</a>
# <a rel='nofollow' class='page larger' href='http://watchpornx.net/page/3'>3</a>
# <a rel='nofollow' class=previouspostslink' href='http://watchpornx.net/page/2'>Next &rsaquo;</a>
# <a rel='nofollow' class=previouspostslink' href='http://watchpornx.net/page/553'>Last &raquo;</a></div></div>



#            "Next Page >>"   <a class="next page-numbers" href="https://watchpornfree.ws/page/2">Next &raquo;</a>

    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &raquo;</a>')
#    next_page_url = "http://sexody.com" + next_page_url
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist



'''
def findvideos(item):
    logger.info("")
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



def play(item):
    logger.info("")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''
