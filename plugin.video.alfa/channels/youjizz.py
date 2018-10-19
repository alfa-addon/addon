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

host = 'https://www.youjizz.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest-clips/1.html"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/1.html"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated-week/1.html"))


#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s-1.html" % texto

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

# <a href="/pornstars/Ella+Knox">
# 		<img src='https://y1.pichunter.com/3633179_12_t.jpg'/>
# 	        <div class="caption"><span>Ella Knox</span></div>
# </a>

    patron  = '<a href="([^"]+)">\s*<img src=\'([^\']+)\'/>.*?<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""

#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class="footer-category">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#           <li><a href="/categories/Amateur-1.html" data-i18n="footer.category.amateur">Amateur</a></li>
    itemlist.append( Item(channel=item.channel, action="peliculas", title="Big Tits" , url="https://www.youjizz.com/search/big-tits-1.html?" , folder=True) )


    patron  = '<li><a href="([^"]+)" data-i18n=.*?>([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)


    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')


# <div class="video-thumb desktop-only ">
#     <div class="video-item">
#         <div class="frame-wrapper">
#             <ul class="rotator">
#                 <li data-rang="0"><span>&nbsp;</span></li>
#                 <li data-rang="1"><span>&nbsp;</span></li>
#                 <li data-rang="2"><span>&nbsp;</span></li>
#                 <li data-rang="3"><span>&nbsp;</span></li>
#                 <li data-rang="4"><span>&nbsp;</span></li>
#                 <li data-rang="5"><span>&nbsp;</span></li>
#                 <li data-rang="6"><span>&nbsp;</span></li>
#                 <li data-rang="7"><span>&nbsp;</span></li>
#             </ul>
#             <a data-video-id="44933461" class="frame image" href="/videos/brother-fuck-his-sister-and-sister%26%23039%3bs-friends-while-sleeping-after-the-party-44933461.html" target="_self">
#                 <img class="img-responsive"  src="//cdne-pics.youjizz.com/c/5/9/c592f537cd4e94711b956378513788e01512869532-1280-720-1141-h264.mp4-1.jpg"    alt="" data-original="//cdne-pics.youjizz.com/c/5/9/c592f537cd4e94711b956378513788e01512869532-1280-720-1141-h264.mp4-1.jpg" />
#                                     <span class="i-hd" data-i18n="video.videothumb.hd">HD</span>
#                             </a>
#                         <a data-video-id="44933461" class="frame video" href="/videos/brother-fuck-his-sister-and-sister%26%23039%3bs-friends-while-sleeping-after-the-party-44933461.html" target="_self" data-clip="//cdne-mobile.youjizz.com/videos/c/5/9/2/f/c592f537cd4e94711b956378513788e01512869532-clip.mp4?validfrom=1532079121&amp;validto=1532251921&amp;rate=36864&amp;hash=Z27T1%2F85GrUfl00UNJnkthxCsNQ%3D" style="display: none;">
#                 <div class="preload-line"></div>
#                 <img class="img-responsive" alt="" src="//cdne-pics.youjizz.com/c/5/9/c592f537cd4e94711b956378513788e01512869532-1280-720-1141-h264.mp4-1.jpg" />
#                                     <span class="i-hd" data-i18n="video.videothumb.hd">HD</span>
#                             </a>
#                     </div>
#         <div class="video-title"><a href='/videos/brother-fuck-his-sister-and-sister%26%23039%3bs-friends-while-sleeping-after-the-party-44933461.html'>Brother Fuck His Sister And Sister&amp;#039;s Friends While Sleeping After The Party</a>&nbsp;</div>
#         <div class="video-content-wrapper text-center">
#             <span class="time">39:47</span>
#             <select class="video-bar-rating-view" data-value="4.1" style="visibility: hidden;">
#                 <option value="1">1</option>
#                 <option value="2">2</option>
#                 <option value="3">3</option>
#                 <option value="4">4</option>
#                 <option value="5" selected>5</option>
#             </select>
#             <span class="views format-views">511876</span>
#         </div>
#     </div>
# </div>



    patron  = '<div class="video-thumb desktop-only ">.*?class="frame image" href="([^"]+)".*?data-original="([^"]+)" />.*?<div class="video-title">.*?>(.*?)</a>.*?<span class="time">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = "http:" + scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a class="pagination-next" href="/most-popular/2.html">Next &raquo;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a class="pagination-next" href="([^"]+)">Next &raquo;</a>')

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

    data = scrapertools.cache_page(item.url)

#  \'([^\']+)/\'    <meta itemprop="contentUrl" content="https://cdn-fck.tnaflix.com/tnamp4/922fec57511179b06c2f/Brazzers_Big_Tits_at_Work_Eva_Angelina_Ramon_Camera_Cums_In_Handy.mp4?key=c62fd67fe0ada667127298bcb9e40371?secure=EQdpT0ExwdSiP6btIwawQg==,1511524930" />

# var encodings = [{"quality":"540","filename":"\/\/cdn2e-videos2.yjcontentdelivery.com\/a\/e\/ae987f6405dcc92172ead4117095c7aa1512264362-960-540-1419-h264.mp4?validfrom=1512602105&validto=1512774905&rate=272448&hash=%2B2iTDm2lqJpJnNf1wv6YCAz%2BLHw%3D","is_old_origin":"1","name":"540p"},
#                  {"quality":"540","filename":"\/\/hls2e-vz-videos2.yjcontentdelivery.com\/_hls\/a\/e\/ae987f6405dcc92172ead4117095c7aa1512264362-960-540-1419-h264.mp4\/master.m3u8","is_old_origin":"1","name":"540p"}];

    media_url = scrapertools.find_single_match(data, '"filename"\:"(.*?)"')
    media_url = "https:" + media_url.replace("\\", "")

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#  \'([^\']+)/\'    <meta itemprop="contentUrl" content="https://cdn-fck.tnaflix.com/tnamp4/922fec57511179b06c2f/Brazzers_Big_Tits_at_Work_Eva_Angelina_Ramon_Camera_Cums_In_Handy.mp4?key=c62fd67fe0ada667127298bcb9e40371?secure=EQdpT0ExwdSiP6btIwawQg==,1511524930" />

# var encodings = [{"quality":"540","filename":"\/\/cdn2e-videos2.yjcontentdelivery.com\/a\/e\/ae987f6405dcc92172ead4117095c7aa1512264362-960-540-1419-h264.mp4?validfrom=1512602105&validto=1512774905&rate=272448&hash=%2B2iTDm2lqJpJnNf1wv6YCAz%2BLHw%3D","is_old_origin":"1","name":"540p"},
#                  {"quality":"540","filename":"\/\/hls2e-vz-videos2.yjcontentdelivery.com\/_hls\/a\/e\/ae987f6405dcc92172ead4117095c7aa1512264362-960-540-1419-h264.mp4\/master.m3u8","is_old_origin":"1","name":"540p"}];


    patron  = '"filename"\:"(.*?)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        scrapedurl = "http:" + scrapedurl.replace("\\", "")
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist
