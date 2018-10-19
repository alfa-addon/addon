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

host = 'https://www.porn300.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/es/videos/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/es/mas-vistos/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/es/mas-votados/"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/es/canales/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/es/pornostars/?sort=views"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/es/categorias/?sort=videos"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/es/buscar/?q=%s" % texto

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
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

      #                               <li class="grid__item grid__item--pornstar-thumb invisible" itemscope itemtype="http://schema.org/Person">
      # <a itemprop="url" href="/es/pornostar/esperanza-gomez/" title="Esperanza Gomez">
      #     <figure class="grid__item__img">
      #         <img itemprop="image" src=https://pics.porn300.com/misc/model48.jpg alt="Esperanza Gomez" width="411" height="320">
      #         <small class="grid__item__hover-btn">navegar</small>
      #         <figcaption>
      #             <h3 class="grid__item__title grid__item__title--pornstars" itemprop="name">Esperanza Gomez</h3>
      #         </figcaption>
      #     </figure>
      #     <ul class="grid__item__data grid__item__data--pornstar">
      #         <li>
      #             <svg class="icon icon--thumb-data" aria-label="Vídeo">
      #                 <use xlink:href="/assets/icons/sprite/icons.939230ed6835c669.svg#video"></use>
      #             </svg>
      #             36 vídeos
      #         </li>
      #         <li>

    patron  = '<a itemprop="url" href="([^"]+)".*?title="([^"]+)">.*?<img itemprop="image" src=([^"]+) alt=.*?</svg>          ([^"]+)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#  "Next page >>"		<li class="pagination_item" itemprop="url"><a class="btn btn-primary--light btn-pagination" itemprop="name" href="/es/mas-votados/?page=2" title="Siguiente"><span class="hidden-xs">Siguiente</span> <svg class="icon icon--thumb-data" aria-label="Clock"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/assets/icons/sprite/icons.svg#chevron-right"></use></svg></a></li> </ul></nav>

    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class=\'row alphabetical\' id=\'categoryList\'>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <li class="grid__item grid__item--category" itemprop="itemListElement" itemscope="" itemtype="http://schema.org/ListItem">
#     <a itemprop="url" href="/es/categoria/espanolas-porno/" data-category-gtmname="Spanish" data-category-permalink="espanolas-porno" title="Españolas">
#         <figure class="grid__item__img">
#             <span class="grid__item__img--container">
#                 <img itemprop="image" src="https://pics.porn300.com/misc/cat105.jpg" alt="Españolas" width="185" height="249">
#                 <small class="grid__item__hover-btn">navegar</small>
#             </span>
#             <figcaption class="caption-category">
#                 <h3 class="grid__item__title grid__item__title--category" itemprop="name">Españolas</h3>
#                 <small class="grid__item__count">
#                     <svg class="icon icon--count" aria-label="Vídeos">
#                         <use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/assets/icons/sprite/icons.939230ed6835c669.svg#video"></use>
#                     </svg> 295
#                 </small>
#             </figcaption>
#         </figure>
#         <meta itemprop="position" content="1">
#     </a>
# </li>



    patron  = '<a itemprop="url" href="([^"]+)".*?title="([^"]+)">.*?<img itemprop="image" src="([^"]+)".*?</svg>([^"]+)               </small>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#  "Next page >>"		<li class="pagination_item" itemprop="url"><a class="btn btn-primary--light btn-pagination" itemprop="name" href="/es/mas-votados/?page=2" title="Siguiente"><span class="hidden-xs">Siguiente</span> <svg class="icon icon--thumb-data" aria-label="Clock"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/assets/icons/sprite/icons.svg#chevron-right"></use></svg></a></li> </ul></nav>

    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div id="inner-content" class="row">(.*?)<h4 class="widgettitle">New</h4>')

#                                                 <li class="grid__item grid__item--video-thumb" itemscope itemtype="http://schema.org/VideoObject">
#     <a itemprop="url" href="/es/video/mami-salida-satisfecha-por-joven-cachas/" data-video-id="756669" title="Mami salida satisfecha por joven cachas">
#         <figure class="grid__item__img">
#             <img itemprop="thumbnailUrl" src="https://pics.porn300.com/thumbs/9/a/3/b/e/9a3be9b30e992878f08e1306b54ba9f76e7fcc6d.mp4/9a3be9b30e992878f08e1306b54ba9f76e7fcc6d.mp4-7.jpg" alt="Mami salida satisfecha por joven cachas" width="175" height="150">
#             <small class="grid__item__hover-btn">ver</small>
#             <figcaption>
#                 <h3 class="grid__item__title grid__item__title--videos" itemprop="name">Mami salida satisfecha por joven cachas</h3>
#             </figcaption>
#         </figure>
#         <meta itemprop="description" content="Esta madura se masturba en la oficina antes de llamar a su asistente para que le taladre el coño como solo él puede hacerlo. ¡En una oficina pasan muchas cosas!">
#         <ul class="grid__item__data grid__item__data--video">
#             <li class="duration-video" itemprop="duration">
#                 <svg class="icon icon--thumb-data" aria-label="Reloj">
#                     <use xlink:href="/assets/icons/sprite/icons.939230ed6835c669.svg#clock"></use>
#                 </svg>
#                 18:36
#             </li>
#             <li itemprop="interactionCount">
#                 <svg class="icon icon--thumb-data" aria-label="Ojo">
#                     <use xlink:href="/assets/icons/sprite/icons.939230ed6835c669.svg#eye"></use>
#                 </svg>
#                 6,93K
#             </li>
#             <li class="data__vote">
#                 <svg class="icon icon--thumb-data" aria-label="Me gusta">
#                     <use xlink:href="/assets/icons/sprite/icons.939230ed6835c669.svg#thumbs-up"></use>
#                 </svg>
#                 76,32%
#             </li>
#             <li class="hidden"><meta itemprop="uploadDate" content="2018-07-04 21:00:01"></li>
#         </ul>
#     </a>
# </li>

    patron  = '<a itemprop="url" href="([^"]+)" data-video-id="\d+" title="([^"]+)">.*?<img itemprop="thumbnailUrl" src="([^"]+)".*?</svg>\s+(.*?)         </li>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li class="pagination_item" itemprop="url"><a class="btn btn-primary--light btn-pagination" itemprop="name" href="/es/mas-votados/?page=2" title="Siguiente"><span class="hidden-xs">Siguiente</span> <svg class="icon icon--thumb-data" aria-label="Clock"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/assets/icons/sprite/icons.svg#chevron-right"></use></svg></a></li> </ul></nav>


    next_page_url = scrapertools.find_single_match(data,'<a class="btn btn-primary--light btn-pagination" itemprop="name" href="([^"]+)" title="Siguiente">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

  #<source src="https://cdnlw8.porn300.com/videos/c/7/3/5/5/c735523225eeef2085f0194666dab97b275cc612.mp4?key=LiZbdUPNeXcbdsvAsYOFnJ1OeyqAm2oqVwiiw9gfx-Ap9_p8kzkd4Emce8lTopVISeGShuvNrzq_2x4P2vx3Y5qP_2FLi1tc4jrNITZrSBvB5yaDk6ePaIfBmcbzko2tmxCyEPTpIZvyTBW4wx4C4rhoIyr3Wm5R5KJUXXAGW3yUNkIvdEba0LFPizNWZ4akJ0FjDJ-2-S97tiiSL7QMLptMHJpUc6Q4arHPLWubec6BJM8TCbnDz1F2XAF4kj_U" type="video/mp4">

    patron  = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl  in matches:
        url =  scrapedurl

    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist



'''

def play(item):
    logger.info()
    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
#    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
'''
