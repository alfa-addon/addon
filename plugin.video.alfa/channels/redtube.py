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

host = 'https://es.redtube.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/mostviewed"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top"))

#    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstar"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?search=%s" % texto

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

# <li id="recommended_pornstars_block_ps_288742" class="ps_info">
#     <div class="ps_info_wrapper">
#         <a class="pornstar_link js_mpop js-pop" href="/pornstar/jasmine+grey"
#            onclick="ga('send', 'event', 'homepage', 'pornstar');">
#             <img id="recommended_pornstars_block_ps_image_288742"
#                  class="ps_info_image"
#                  src="https://ci.phncdn.com/m=eWrP8f/pics/pornstars/000/288/742/thumb_1189051.jpg"
#                                   title="Jasmine Grey"
#                  alt="Jasmine Grey">
#                             <div class="ps_info_rank">
#                     Puntaje: 1                </div>
#                     </a>
#         <a class="ps_info_name js_mpop js-pop" href="/pornstar/jasmine+grey">
#             Jasmine Grey        </a>
#         <div class="ps_info_count">
#             2            Videos        </div>
#     </div>
#             </li>

    patron  = '<a class="pornstar_link js_mpop js-pop" href="([^"]+)".*?"([^"]+)"\s+title="([^"]+)".*?<div class="ps_info_count">\s+([^"]+)\s+Videos'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle +  " [COLOR yellow]" + cantidad + "[/COLOR] "
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<a id="wp_navNext" class="js_pop_page" href="([^"]+)">')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class=\'row alphabetical\' id=\'categoryList\'>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


 # <li id="category_46" class="category_item" data-category_id="46">
 #                <div class="category_item_wrapper">
 #                    <a href="/redtube/verifiedamateurs" class="category_thumb_link js_mpop">
 #                       <img class="category_item_image"
 #                            data-thumb_url="https://ci.rdtcdn.com/www-static/cdn_files/redtube/images/pc/category/verifiedamateurs_001.jpg"
 #                            src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
 #                            alt="Aficionadas Verificadas"
 #                            />
 #                    </a>
 #                    <div class="category_item_info">
 #                        <a class="category_item_link js_mpop" href="/redtube/verifiedamateurs">
 #                            <strong>
 #                                Aficionadas Verificadas                            </strong>
 #                        </a>
 #                        <span class="category_count">
 #                            6,950 Videos                        </span>
 #                    </div>
 #                </div>            </li>


    patron  = '<div class="category_item_wrapper">.*?<a href="([^"]+)".*?data-thumb_url="([^"]+)".*?alt="([^"]+)".*?<span class="category_count">\s+([^"]+) Videos'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div id="inner-content" class="row">(.*?)<h4 class="widgettitle">New</h4>')



    #        <li class="videoblock_list" id="browse_10810311">
    #     <div class="video_block_wrapper">
    #         <div class="preloadLine"></div>
    #         <span class="video_thumb_wrap">
    #             <a class="video_link js_mpop js-pop" href="/10810311">
    #                 <img id="img_browse_10810311"
    #                      src="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201810/02/10810311/original/12.jpg"
    #                      alt="SEXYMOMMA - Lesbian threeway with an alluring mature dyke"
    #                      data-thumb_url="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201810/02/10810311/original/12.jpg"
    #                      data-thumbs="16"
    #                      data-path="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201810/02/10810311/original/{index}.jpg"
    #                                                 data-mediabook="https://cw.rdtcdn.com/media/videos/201810/02/10810311/180P_225K_10810311.webm"
    #                                              class="thumb img_video_list js-videoThumb js-videoThumbFlip js-videoPreview"/>
    #                                 <span class="hd-video-icon site_sprite"></span>
    #                                                 <span class="duration">
    #                                         <span class="hd-video-text">HD</span>
    #                                                             12:00                    </span>
    #             </a>
    #         </span>            <div class="video_title">
    #             <a title="SEXYMOMMA - Lesbian threeway with an alluring mature dyke" href="/10810311">SEXYMOMMA - Lesbian threeway with an alluring mature dyke</a>
    #         </div>
    #         <span class="video_count">31 vistas</span>
    #         <span class="video_percentage">0%</span>
    #     </div>
    # </li>
    #    <li class="videoblock_list" id="result_video_9801551">
    #     <div class="video_block_wrapper">
    #         <div class="preloadLine"></div>
    #         <span class="video_thumb_wrap">
    #             <a class="video_link js_mpop js-pop" href="/9801551">
    #                 <img id="img_result_video_9801551"
    #                      src="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201808/25/9801551/original/15.jpg"
    #                      alt="SUPER HOT BUSTY MILF FUCKED HARD AND DEEP AT HOME"
    #                      data-thumb_url="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201808/25/9801551/original/15.jpg"
    #                      data-thumbs="16"
    #                      data-path="https://thumbs-cdn.redtube.com/m=eGJF8f/media/videos/201808/25/9801551/original/{index}.jpg"
    #                                                 data-mediabook="https://ew.rdtcdn.com/media/videos/201808/25/9801551/180P_225K_9801551.webm"
    #                                              class="thumb img_video_list js-videoThumb js-videoThumbFlip js-videoPreview"/>
    #                                 <span class="hd-video-icon site_sprite"></span>
    #                                                 <span class="duration">
    #                                         <span class="hd-video-text">HD</span>
    #                                                             44:15                    </span>
    #             </a>
    #         </span>            <div class="video_title">
    #             <a title="SUPER HOT BUSTY MILF FUCKED HARD AND DEEP AT HOME" href="/9801551">SUPER HOT BUSTY MILF FUCKED HARD AND DEEP AT HOME</a>
    #         </div>
    #         <span class="video_count">430.562 vistas</span>
    #         <span class="video_percentage">87%</span>
    #     </div>
    # </li>

    patron  = '<img id="img_.*?data-path="([^"]+)".*?<span class="duration">(.*?)</a>.*?<a title="([^"]+)" href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail,duracion,scrapedtitle,scrapedurl in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year

        duracion = duracion.replace("<span class=\"hd-video-text\">HD</span>", "").replace("                    </span>", " ").replace("           ", "").replace("         ", "").replace("   ", "")
        scrapedthumbnail = scrapedthumbnail.replace("{index}.", "1.")

        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		  <a id="wp_navNext" class="js_pop_page" href="/newest?page=2">

    next_page_url = scrapertools.find_single_match(data,'<a id="wp_navNext" class="js_pop_page" href="([^"]+)">')

    if next_page_url!="":
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
    itemlist = []
    data = scrapertools.cachePage(item.url)

# "defaultQuality":true,"format":"",
# "quality":"480","videoUrl":"https:\/\/ev.rdtcdn.com\/media\/videos\/201807\/22\/8789841\/480P_600K_8789841.mp4?validfrom=1532242448&validto=1532249648&rate=100k&burst=2000k&hash=wVSzFnAhFLMBJGIUZkeWNzIjrss%3D"},
# {"defaultQuality":false,"format":"","quality":"240","videoUrl":"https:\/\/ev.rdtcdn.com\/media\/videos\/201807\/22\/8789841\/240P_400K_8789841.mp4?validfrom=1532242448&validto=1532249648&rate=60k&burst=2000k&hash=1sp83gvEWgpfkCyAKP7RYrD7iPk%3D"}],

    patron  = '"defaultQuality":true,"format":"",.*?"videoUrl"\:"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl  in matches:
        url =  scrapedurl.replace("\/", "/")

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
