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

host = 'https://www.youporn.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/browse/time/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/browse/views/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top_rated/"))
#    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))


    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/most_popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/alphabetical/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?query=%s" % texto

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
    data = scrapertools.get_match(data,'<a href="/pornstars/most_popular/" class="selected">All</a>(.*?)<i class=\'icon-menu-right\'></i></a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#   <a href="/pornstar/4186/brandi-love/">
# <img src="data:image/gif,GIF89a%01%00%01%00%80%00%00%00%00%00%FF%FF%FF%21%F9%04%01%00%00%00%00%2C%00%00%00%00%01%00%01%00%00%02%01D%00%3B" width="231" height="340" alt="Brandi Love" data-original="https://ci.phncdn.com/m=eNdvbgaaaa/pics/pornstars/000/004/440/thumb_198761.jpg" class="js_lazy" />
# <div class="pornstar-name-box">
# <span class="porn-star-name">Brandi Love</span>
# </div>
# </a>
# <div class="porn-star-info-box">
# <div class="porn-star-rank">
# <span>Rank: 1</span>
# </div>
# <div class="porn-star-videos-count">
# <span class="icon icon-camescope"></span>
# <span class="video-count">157</span>
# </div>

    patron  = '<a href="([^"]+)".*?data-original="([^"]+)".*?<span class="porn-star-name">([^"]+)</span>.*?<span class="video-count">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#                            <a href="/pornstars/?page=2" data-page-number='2'><i class='icon-menu-right'></i></a>
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" data-page-number=.*?>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<div class=\'row alphabetical\'.*?>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <div class='row alphabetical' id='categoryList' data-espnode="categories_list">
# <a href="/category/1/amateur/" class="four-column categoryBox" onclick="ga(['send', 'event', 'mainHeader', 'click', 'Click Categories Amateur_Amateur']);" data-espnode="category_amateur">
# <img src="data:image/gif,GIF89a%01%00%01%00%80%00%00%00%00%00%FF%FF%FF%21%F9%04%01%00%00%00%00%2C%00%00%00%00%01%00%01%00%00%02%01D%00%3B" alt="Amateur" class="js_lazy" data-original="https://fi1.ypncdn.com/static/cb/bundles/youpornwebfront/images/categories/amateur(m=ePZfLgaaaa).jpg">
# <div class='categoryTitle'>
# <p>Amateur
# <span>312,219 Videos</span>
# </p>
# </div>
# </a>

    patron  = '<a href="([^"]+)".*?data-original="([^"]+)".*?<p>([^"]+)<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle + " (" + cantidad +")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')


# <div class='video-box four-column video_block_wrapper' data-video-id="14329511" data-video-id-encrypted="ywDucv4DU1uVqPBgwz9UTw==">
# <div class="add-to-options-wrapper is-hidden">
# <div class="add-to-favorites js_addToFavorites" title="Add to favorites">
# <i class="icon-favorite"></i>
# </div>
# <div class="add-to-collection add-to-collection-button" title="Add to collection">
# <i class="icon-collections"></i>
# </div>
# <div class="recommended-option-dislike dislikeRecommended js_recommendationButton is-hidden" data-path="/change/videos/14329511/thumbsdown/" title="Remove Video">
# <i class="icon-not-interested"></i>
# </div>
# <div class="js_remove-undo-watchHistory remove-watch-history" title="Remove Video">
# <i class="icon-delete-collection"></i>
# </div>
# </div>
# <div class="fav-recommended-video-undo-wrapper js_fav-recommended-option-like is-hidden">
# <div class="undo-removed-title">
# Video Removed
# <span class=" js_recommendationButton likeRecommended" data-path="/change/videos/14329511/thumbsup/">Undo</span>
# </div>
# </div>
# <div class="js_remove-undo-watchHistory watch-history-undo-remove-wrapper is-hidden">
# <div class="undo-removed-title">
# Video Removed
# <span class="watch-history-undo-button js_watchHistoryUndo">Undo</span>
# </div>
# </div>
# <a href="/watch/14329511/natural-redhead-and-petite-blonde-teen-gina-gerson-in-a-threesome/" class='video-box-image' >
# <img src="data:image/gif,GIF89a%01%00%01%00%80%00%00%00%00%00%FF%FF%FF%21%F9%04%01%00%00%00%00%2C%00%00%00%00%01%00%01%00%00%02%01D%00%3B" class="js_lazy js-videoThumbFlip " alt='Natural Redhead and petite blonde teen Gina Gerson in a threesome'
# data-thumbnail="https://di1.ypncdn.com/m=e8KSKgaaaa/201801/30/14329511/original/9/natural-redhead-and-petite-blonde-teen-gina-gerson-in-a-threesome-9.jpg"
# data-original="https://di1.ypncdn.com/m=e8KSKgaaaa/201801/30/14329511/original/9/natural-redhead-and-petite-blonde-teen-gina-gerson-in-a-threesome-9.jpg"
# data-flipbook="{
# digitsPreffix: 'https://di1.ypncdn.com/m=e8KSKgaaaa/201801/30/14329511/original/',
# digitsSuffix: '/natural-redhead-and-petite-blonde-teen-gina-gerson-in-a-threesome-{index}.jpg',
# setLength: 16,
# firstThumbnail: 1,
# incrementer: 1
# }"
# >
# <div class="video-box-title">
# Natural Redhead and petite blonde teen Gina Gerson in a threesome
# </div>
# </a>
# <div class="video-box-infos">
# <div class='video-box-rating'>
# <span class='video-box-percentage up'>82%</span>
# <span class='video-box-views'>10,543 Views</span>
# </div>
# <div class="video-duration">05:40</div>
# <div class="video-hd-vr-icons">
# <i class="icon icon-hd-text"></i>
# </div>
# </div>
# <div class="js_add-to-option-wrapper">
# <span class="add-to-button js_add-to-button" title="Add to..." >
# <i class="icon-option-vertical option-vertical-button-background"></i>
# <i class="icon-option-vertical"></i>
# </span>
# <span class="close-add-to-button js_close-add-to-button is-hidden">
# <i class="icon-thin-x"></i>
# </span>
# </div>
# </div>

    patron  = '<a href="([^"]+)" class=\'video-box-image\'.*?data-original="([^"]+)".*?<div class="video-box-title">([^"]+)</div>.*?<div class="video-duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
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

#{"defaultQuality":false,"format":"","quality":"720","videoUrl":"https:\/\/ev.ypncdn.com\/201804\/20\/14522083\/720p_1500k_14522083\/YouPorn_-_scissoring-with-her-yoga-instructor.mp4?rate=137k&burst=1400k&validfrom=1524649700&validto=1524664100&hash=E84zJFu542PjUYBrqnhfng49p64%3D"},

#                                                  https://ev.ypncdn.com/201804/20/14522083/720p_1500k_14522083/YouPorn_-_scissoring-with-her-yoga-instructor.mp4?rate=137k&burst=1400k&validfrom=1524649700&validto=1524664100&hash=E84zJFu542PjUYBrqnhfng49p64%3D

    patron  = 'page_params.video.mediaDefinition =.*?"videoUrl":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        scrapedurl =  scrapedurl.replace("\/", "/")
    #    title = ""

    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))

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
