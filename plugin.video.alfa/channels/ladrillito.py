# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canal (terrenoresidenziale)
# ------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import httptools
from core import jsontools as json
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb

#       http://laohu116.com
host = 'http://ladrillitopelis.net/'


def mainlist(item):
    logger.info()
    itemlist = []



    itemlist.append( Item(channel=item.channel, title="Recientes" , action="peliculas", url=host + "/movies/"))
    itemlist.append( Item(channel=item.channel, title="Castellano" , action="peliculas", url=host + "/genre/castellano/"))
    itemlist.append( Item(channel=item.channel, title="VO" , action="peliculas", url=host + "/genre/v-o/"))
    itemlist.append( Item(channel=item.channel, title="Latino" , action="peliculas", url=host + "/genre/latino/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Buscar" + "[/COLOR]" , action="search"))
    return itemlist


def search(item, texto):
    logger.info()
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


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h2>Géneros</h2>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <h2>Géneros</h2>
#        <ul class="genres scrolling">
#            <li class="cat-item cat-item-22371"><a href="http://ladrillitopelis.net/genre/4k-ultra-hd/">4K Ultra HD</a> <i>1</i>
#                                     </li>

    patron  = '<li class="cat-item cat-item-\d+"><a href="(.*?)">(.*?)</a> <i>(\d+)</i>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,cant in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + "  (" + cant + ")"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="cols-2">(.*?)<h2 class="section-heading">LO MAS NUEVO</h2>')

                        # <article id="post-5956" class="item movies">
                        #     <div class="poster">
                        #         <a href="http://ladrillitopelis.net/movies/la-torre-oscura/"><img src="http://ladrillitopelis.net/wp-content/uploads/2017/05/u2Mw9iR1sWEq3x2HPT40G4MHDRQ-185x278.jpg" alt="La torre oscura">
                        #         </a>
                        #         <div class="rating"><span class="icon-star2"></span> 7</div> <span class="quality">TS-Screener</span>
                        #     </div>
                        #     <div class="data">
                        #         <h3><div class="flag" style="background-image: url(http://ladrillitopelis.net/wp-content/themes/doploo2.01/assets/img/flags/mx.png)"></div> <a href="http://ladrillitopelis.net/movies/la-torre-oscura/">La torre oscura</a></h3> <span>2017</span>
                        #     </div>
                        # </article>

    patron  = '<article id="post-\d+".*?<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)">.*?<span class="quality">([^"]+)</span>.*?<span>(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,calidad,scrapedyear  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle+' ('+scrapedyear+') ' + "[COLOR red]" + calidad + "[/COLOR]"
        thumbnail = scrapedthumbnail
        plot = ""
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#                <a class='arrow_pag' href="http://laohu116.com/movies/page/2/"><i class='icon-caret-right'></i></a>
#       "Next page >>"
    try:
        patron  = '<a class=\'arrow_pag\' href="([^"]+)"><i class=\'icon-caret-right\'></i>'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page[0] ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
#    data = scrapertools.get_match(data,'Streaming and Download Links:(.*?)</p>')



    patron = '<td class="cal"><a class="link_a download" href="([^"]+)".*?ladrillitopelis.net</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,calidad,scrapedidioma in matches:
        ata = scrapertools.cachePage(scrapedurl)
        scrapedurl = scrapertools.find_single_match(ata, 'div class="boton reloading"><a href="([^"]+)"')

        scrapedplot = ""
        scrapedidioma = scrapedidioma.replace("Castellano", "CAS").replace("Latino", "LAT").replace("Subtitulada", "VOS")
        scrapedtitle = "Torrent "+ "[COLOR orange]" " (" + scrapedidioma + ") "+ "[/COLOR]" + "[COLOR red]" + calidad + "[/COLOR]"
        itemlist.append(item.clone(channel=item.channel, action="play", server="torrent", title=scrapedtitle , url=scrapedurl , plot="" , folder=True) )

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la biblioteca[/COLOR]', url=item.url,
                             action="add_pelicula_to_library", extra="findvideos", contentTitle = item.contentTitle))
    return itemlist
'''
def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.contentTitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
