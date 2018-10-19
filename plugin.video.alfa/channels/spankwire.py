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

host = 'https://www.spankwire.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/recentvideos/straight"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/home1/Straight/Month/Views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/home1/Straight/Month/Rating"))
#    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))


#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/Straight"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto

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

  #<li id="menu-item-38568" class="menu-item menu-item-type-taxonomy menu-item-object-post_tag menu-item-38568"><a href="http://pornstreams.eu/tag/assparade/">AssParade</a></li>

    patron  = '<li id="menu-item-.*?<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

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
#    data = scrapertools.get_match(data,'<div class="footer-category">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


		# <div class="category-thumb">
		# 			<a href="/categories/Straight/Amateur/Submitted/16" onClick="googleAnalytics('Straight Categories','Click Amateur');">
		# 				 <img src="//cdn1-static-spankwire.spankcdn.net/images/category/Straight/Amateur.jpg" alt="Amateur" />
		# 			</a>
		# 			<h2>
		# 				<a href="/categories/Straight/Amateur/Submitted/16" onClick="googleAnalytics('Straight Categories','Click Amateur');">Amateur</a>
		# 			</h2>
		# 			<span>10,436 Videos</span>
		# 		</div>

    patron  = '<div class="category-thumb"><a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)" />.*?<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/Submitted/59"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

# <li class="js-li-thumbs"><div class="video_thumb_wrapper"><div class="video_thumb_wrapper__thumb-wrapper js-thumb-wrapper">
# <a href="/Amateur-first-woman-time-Horny-Step-Mom-Gets-Slammed/video18615372/">
# <img id="thumbnail_18615372_1"
# data-original="//cdn4-image-spankwire.spankcdn.net/m=eaCaaBFnGw/201804/22/18615372/originals/1.jpg"
# data-video-id="18615372"
# data-srcdata="//cdn4-image-spankwire.spankcdn.net/m=eaCaaBFnGw/201804/22/18615372/originals/1.jpg"
# data-srcsmall="//cdn4-image-spankwire.spankcdn.net/m=eayaasFnGw/201804/22/18615372/originals/1.jpg"
# data-srcmedium="//cdn4-image-spankwire.spankcdn.net/m=eaCaaBFnGw/201804/22/18615372/originals/1.jpg"
# data-flipbook="//cdn4-image-spankwire.spankcdn.net/m=eaCaaBFnGw/201804/22/18615372/originals/{index}.jpg"
# data-flipbook-values="dflt"
# alt="Amateur first woman time Horny Step Mom Gets Slammed"
# class="flipBookRotation rotating lazy"
# title="Amateur first woman time Horny Step Mom Gets Slammed"
# onerror="thumbLoadError(this)" /><div class="video_thumb_wrapper__thumb-wrapper__isHD"><span>HD</span></div>
#
# div class="video_thumb_wrapper__thumb-wrapper__title_video">
# <a href="/Amateur-first-woman-time-Horny-Step-Mom-Gets-Slammed/video18615372/">Amateur first woman time Horny Step Mom Gets Slammed</a></div><div class="video_thumb_wrapper__thumb-wrapper__video_info"><div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__rating_box">90%							<span>rating</span></div><div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__views_box">
# 2,924							<span>views</span></div></div><div class="video_thumb_wrapper__thumb-wrapper__video_info"><div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__duration">
# 5:00</div><div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__categories">
# <span>teen-katie,&nbspmorgan-hardcore-mom-amateur-teen-porn-taboo-p</span></div></div></div></li>


    patron  = '<div class="video_thumb_wrapper">.*?<a href="([^"]+)".*?data-original="([^"]+)".*?title="([^"]+)".*?<div class="video_thumb_wrapper__thumb_info video_thumb_wrapper__duration">(.*?)</div>'
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


#			"Next page >>"		<link rel="next" href="straight?Page=2" />

    next_page_url = scrapertools.find_single_match(data,'<link rel="next" href="([^"]+)" />')

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

    # playerData.cdnPath180         = '//cdn1-public-spankwire.spankcdn.net/201804/08/18248622/mp4_normal_18248622.mp4?validfrom=1527159178&validto=1527166378&rate=40k&burst=800k&hash=j1QeyQFzJI9TNP%2FffRIHzEPd3v0%3D';
	# playerData.cdnPath240         = '//cdn1-public-spankwire.spankcdn.net/201804/08/18248622/mp4_high_18248622.mp4?validfrom=1527159178&validto=1527166378&rate=48k&burst=800k&hash=TW%2FkjWzyPf%2Fi7vF0rtG3Hp7sVq0%3D';
	# playerData.cdnPath480         = '//cdn1-public-spankwire.spankcdn.net/201804/08/18248622/mp4_ultra_18248622.mp4?validfrom=1527159178&validto=1527166378&rate=78k&burst=800k&hash=d6qWgLmkbZXYueqHk58uWsy%2BLfs%3D';
	# playerData.cdnPath720         = '//cdn1-public-spankwire.spankcdn.net/201804/08/18248622/mp4_720p_18248622.mp4?validfrom=1527159178&validto=1527166378&rate=133k&burst=800k&hash=Ev8mmXGtFHKt2nZkEwe10LuDXvg%3D';

    patron  = 'playerData.cdnPath480         = \'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        url = scrapedurl
        if url=="":
            scrapedurl = scrapertools.find_single_match(data,'playerData.cdnPath480         = \'([^\']+)\'')
        scrapedurl = "http:" + scrapedurl
    #    title = ""

        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = scrapedurl, url=scrapedurl))

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
