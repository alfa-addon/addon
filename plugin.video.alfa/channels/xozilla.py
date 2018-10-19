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

host = 'https://www.xozilla.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/"))


    itemlist.append( Item(channel=item.channel, title="Chanel" , action="catalogo", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto

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
#    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<img class="thumb" src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        thumbnail = "http:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=thumbnail , plot=scrapedplot , folder=True) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#     <a class="item" href="https://www.xozilla.com/categories/fingering/" title="Fingering">
# 							<div class="img">
# 																	<img class="thumb" src="//i.xozilla.com/contents/categories/291.jpg" alt="Fingering"/>
# 																<div class="videos"><i class="fa fa-video-camera" aria-hidden="true"></i> 272 videos</div>
# 							</div>
# 							<strong class="title">Fingering</strong>
# <!-- 							<div class="wrap">
# 																								<div class="rating positive">
# 									83%
# 								</div>
# 							</div> -->
# 						</a>


    patron  = '<a class="item" href="([^"]+)" title="([^"]+)">.*?<img class="thumb" src="([^"]+)".*?</i> (\d+) videos</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
#        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')

# <a href="https://www.xozilla.com/videos/23962/rainbow-thigh-high-socks-clad-blonde-pours-milk-over-her-big-natural-tits/" class="item 						"
# 					    vthumb="//www.xozilla.com/get_file/5/4eb40f3f9eab536e0a8e322f8a8e7ffa/23000/23962/23962.webm"						data-title="Rainbow thigh high socks clad blonde pours milk over her big natural tits"
# 					   	data-navigate-to="item5a13fa406cbfc8.25382293"						 data-item-uuid="item5a13fa406cbfc8.25382293"
# 					     data-screen-url="//i.xozilla.com/contents/videos_screenshots/23000/23962"
# 						 data-video-id="23962"
# 						 data-video-page-url="https://www.xozilla.com/videos/23962/rainbow-thigh-high-socks-clad-blonde-pours-milk-over-her-big-natural-tits/"
# 						 data-server-group-id="5"
# 						 data-formats='{".mp4":{"postfix":".mp4","dimensions":["960","540"],"duration":"383","duration_string":"6:23","duration_array":{"minutes":6,"seconds":23,"text":"6:23"},"file_size":"100890709","file_size_string":"96.22 Mb","timeline_screen_amount":"77","timeline_screen_interval":"5","timeline_cuepoints":"0","file_name":"23962.mp4","file_path":"074ad5b0b0ab7f760499a3f4da1387db\/23000\/23962\/23962.mp4"},"hd.mp4":{"postfix":"hd.mp4","dimensions":["1280","720"],"duration":"383","duration_string":"6:23","duration_array":{"minutes":6,"seconds":23,"text":"6:23"},"file_size":"154009798","file_size_string":"146.88 Mb","timeline_screen_amount":"0","timeline_screen_interval":"0","timeline_cuepoints":"0","file_name":"23962hd.mp4","file_path":"e326aa9a9ec5571bb4ab737a98035075\/23000\/23962\/23962hd.mp4"},".webm":{"postfix":".webm","dimensions":["294","166"],"duration":"14","duration_string":"0:14","duration_array":{"minutes":0,"seconds":14,"text":"0:14"},"file_size":"352465","file_size_string":"344.2 Kb","timeline_screen_amount":"0","timeline_screen_interval":"0","timeline_cuepoints":"0","file_name":"23962.webm","file_path":"4eb40f3f9eab536e0a8e322f8a8e7ffa\/23000\/23962\/23962.webm"}}'>
#
# 						<div class="img ithumb">
# 															<img class="thumb lazy-load"
# 									 src="data:image/png;base64,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UmVhZHlxyWU8AAADKmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxMzIgNzkuMTU5Mjg0LCAyMDE2LzA0LzE5LTEzOjEzOjQwICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxNS41IChNYWNpbnRvc2gpIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjRCNUU2QTE1RkJDNTExRTZCMzQ1QkZFRjA4OTBEODg3IiB4bXBNTTpEb2N1bWVudElEPSJ4bXAuZGlkOjRCNUU2QTE2RkJDNTExRTZCMzQ1QkZFRjA4OTBEODg3Ij4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6NEI1RTZBMTNGQkM1MTFFNkIzNDVCRkVGMDg5MEQ4ODciIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6NEI1RTZBMTRGQkM1MTFFNkIzNDVCRkVGMDg5MEQ4ODciLz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz78tKAmAAAArUlEQVR42uzBMQEAAADCoPVPbQZ/oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOA0AQYAUusAAWKOe6AAAAAASUVORK5CYII=" data-original="//i.xozilla.com/contents/videos_screenshots/23000/23962/300x169/37.jpg"
# 									 alt="Rainbow thigh high socks clad blonde pours milk over her big natural tits"
# 									 									 thumb="//i.xozilla.com/contents/videos_screenshots/23000/23962/300x169/37.jpg"
# 									 width="300"
# 									 height="169"/>
# 																					<span class="hd-label">HD</span>
# 							<div class="duration">6m:23s</div>
# 						</div>
# 						<strong class="title">Rainbow thigh high socks clad blonde pours milk over...</strong>
# 											</a>

    patron  = '<a href="([^"]+)" class="item.*?data-original="([^"]+)".*?alt="([^"]+)".*?<div class="duration">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion in matches:
        url = scrapedurl
#        year = " (%s)" % year

        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li class="next"><a href="/latest-updates/2/" data-action="ajax" data-container-id="list_videos_latest_videos_list_pagination" data-block-id="list_videos_latest_videos_list" data-parameters="sort_by:post_date;from:2">Next</a></li>
#                                <li class="next"><a href="#videos" data-action="ajax" data-container-id="list_videos_common_videos_list_pagination" data-block-id="list_videos_common_videos_list" data-parameters="sort_by:post_date;from:2">Next</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li class="next"><a href="([^"]+)"')

    if next_page_url!="#videos":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )
    if next_page_url=="#videos":
        next_page_url = scrapertools.find_single_match(data,'from:(\d+)">Next</a>')
        next_page_url = urlparse.urljoin(item.url,next_page_url) + "/"
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
    data = scrapertools.cache_page(item.url)

    media_url = scrapertools.find_single_match(data, 'video_alt_url: \'([^\']+)/\'')
    if media_url == "":
        media_url = scrapertools.find_single_match(data, 'video_url: \'([^\']+)/\'')

    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#    \'([^\']+)\'    video_url: 'https://www.xozilla.com/get_file/5/4673982a6716f521237a06d403e8b06b/29000/29964/29964.mp4/', 																	postfix: '.mp4', 																	video_url_text: '540p',
# video_alt_url: 'https://www.xozilla.com/get_file/5/3179cd97b5b888eb84e7c57c2db3e8de/29000/29964/29964hd.mp4/', 																	video_alt_url_text: '720p', 																	video_alt_url_hd: '1', 																	preview_url: '//i.xozilla.com/contents/videos_screenshots/29000/29964/preview.mp4.jpg', 																	skin: 'youtube.css', 																	bt: '18', 																	volume: '1', 																	preload: 'metadata', 																	hide_controlbar: '1', 																	hide_style: 'fade', 																	autoplay: 'true', 																	adv_pause_html: 'https://www.xozilla.com/player/html.php?aid=pause_html&video_id=29964&cs_id=0', 																	float_replay: 'true', 																	embed: '1'															};


    patron  = 'video_url: \'([^\']+)/\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))

    next_page_url = scrapertools.find_single_match(data,'video_alt_url: \'([^\']+)/\'')
    itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))

    return itemlist
