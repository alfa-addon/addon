# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="peliculas", title="Novedades", fanart=item.fanart,
                         url="http://es.pornhub.com/video?o=cm"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorias", fanart=item.fanart,
                         url="http://es.pornhub.com/categories?o=al"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", fanart=item.fanart,
                         url="http://es.pornhub.com/video/search?search=%s&o=mr"))
    return itemlist


def search(item, texto):
    logger.info()

    item.url = item.url % texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<div id="categoriesStraightImages">(.*?)</ul>')

    # Extrae las categorias
    patron = '<li class="cat_pic" data-category=".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += 'alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        if "?" in scrapedurl:
            url = urlparse.urljoin(item.url, scrapedurl + "&o=cm")
        else:
            url = urlparse.urljoin(item.url, scrapedurl + "?o=cm")

        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=url, fanart=item.fanart,
                             thumbnail=scrapedthumbnail))

    itemlist.sort(key=lambda x: x.title)
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    videodata = scrapertools.find_single_match(data, 'videos search-video-thumbs">(.*?)<div class="reset"></div>')


# div class="img fade fadeUp videoPreviewBg">
#
# 									<a href="/view_video.php?viewkey=ph5ae8d823c6f33" title="Naughty Nylon Fuck Hole(Preview)" class="img " data-related-url="/video/ajax_related_video?vkey=ph5ae8d823c6f33"  >
#
# 																			            			<img
# 				src="https://ci.phncdn.com/www-static/images/blank.gif"
# 				alt="Naughty Nylon Fuck Hole(Preview)"
# 									data-mediumthumb="https://ci.phncdn.com/videos/201805/01/164359881/original/(m=ecuKGgaaaa)(mh=pQOXVsDVvEqL4bXl)1.jpg"
# 																	data-mediabook="https://dv.phncdn.com/videos/201805/01/164359881/180P_225K_164359881.webm?ttl=1525256535&ri=1024000&rs=1200&hash=3d7ad63955f80c30829b818272a9361a"
# 								class="js-preload js-videoThumb js-videoThumbFlip thumb js-videoPreview"
# 				width="150"
#
# 				 class="rotating" data-video-id="164359881" data-thumbs="16" data-path="https://ci.phncdn.com/videos/201805/01/164359881/original/(m=eWdTGgaaaa)(mh=fLcs-mQEewgAs_Dr){index}.jpg"			title="Naughty Nylon Fuck Hole(Preview)" />
# 										</a>
# 													<div class="marker-overlays js-noFade">
# 				<var class="duration">8:02</var>
# 									<span class="hd-thumbnail">HD</span>
# 															</div>
# 			</div>
# 		</div>
# 					<div class="add-to-playlist-icon display-none">
# 				<button type="button" data-title="Agregar a una lista de reproducci&oacute;n" class="tooltipTrig open-playlist-link playlist-trigger" onclick="return false;" data-rel="ph5ae8d823c6f33" >+</button>
# 			</div>
# 							<div class="thumbnail-info-wrapper clearfix">
# 				<span class="title">
# 																		<a href="/view_video.php?viewkey=ph5ae8d823c6f33" title="Naughty Nylon Fuck Hole(Preview)"class="" >Naughty Nylon Fuck Hole(Preview)</a>
# 															</span>
# 				<span class="views"><var>15</var> vistas</span>
# 				<div class="rating-container up">
# 					<div class="main-sprite icon"></div>
# 					<div class="value">100%</div>
# 				</div>

    # Extrae las peliculas
    patron = '<div class="phimage">.*?'
    patron += '<a href="([^"]+)" title="([^"]+).*?'
    patron += '<var class="duration">([^<]+)</var>(.*?)</div>.*?'
    patron += 'data-mediumthumb="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(videodata)

    for url, scrapedtitle, duration, scrapedhd, thumbnail in matches:
        title =  "(" + duration + ") " + scrapedtitle.replace("&amp;amp;", "&amp;")

        scrapedhd = scrapertools.find_single_match(scrapedhd, '<span class="hd-thumbnail">(.*?)</span>')
        if scrapedhd == 'HD':
            title += ' [HD]'

        url = urlparse.urljoin(item.url, url)
        itemlist.append(
            Item(channel=item.channel, action="play", title=title, url=url, fanart=item.fanart, thumbnail=thumbnail))

    if itemlist:
        # Paginador
        patron = '<li class="page_next"><a href="([^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if matches:
            url = urlparse.urljoin(item.url, matches[0].replace('&amp;', '&'))
            itemlist.append(
                Item(channel=item.channel, action="peliculas", title=">> Página siguiente", fanart=item.fanart,
                     url=url))

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#   {"defaultQuality":true,"format":"","quality":"720","videoUrl":"https:\/\/dv.phncdn.com\/videos\/201805\/01\/164360171\/720P_1500K_164360171.mp4?ttl=1525256716&ri=1024000&rs=1272&hash=a92304dcd283126303ce772d6e54f063"},


    patron  = '"defaultQuality":true,"format":"","quality":"\d+","videoUrl":"(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl  in matches:
        url = scrapedurl.replace("\/", "/")

    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist


'''
def play(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data

"video_title":"MilenaAngelClub - Morning Kiss , full video,\u00a0",
"defaultQuality":[720,480,240,1080],
"vcServerUrl":"/svvt/add?stype=svv&svalue=164360171&snonce=qyqova7wps8g56ou&skey=d458ac4cdcedb8103bda7f56d53d1b9d623bceb05e7a9b4c065c212aeeb51050&stime=1525253116","display_hd_upsell":true,"mediaDefinitions":
[{"defaultQuality":false,"format":"upsell","quality":"1080","videoUrl":""},
{"defaultQuality":true,"format":"","quality":"720","videoUrl":"https:\/\/dv.phncdn.com\/videos\/201805\/01\/164360171\/720P_1500K_164360171.mp4?ttl=1525256716&ri=1024000&rs=1272&hash=a92304dcd283126303ce772d6e54f063"},
{"defaultQuality":false,"format":"","quality":"480","videoUrl":"https:\/\/dv.phncdn.com\/videos\/201805\/01\/164360171\/480P_600K_164360171.mp4?ttl=1525256716&ri=1024000&rs=752&hash=cc1278d00aafd4480f148647afa7cdc9"},
{"defaultQuality":false,"format":"","quality":"240","videoUrl":"https:\/\/dv.phncdn.com\/videos\/201805\/01\/164360171\/240P_400K_164360171.mp4?ttl=1525256716&ri=1024000&rs=480&hash=de11cc332fe6f9f0d3f491ea9a8893cd"}],


    quality = scrapertools.find_multiple_matches(data, '"id":"quality([^"]+)"')
    for q in quality:
        match = scrapertools.find_single_match(data, 'var quality_%s=(.*?);' % q)
        match = re.sub(r'(/\*.*?\*/)', '', match).replace("+", "")
        url = ""
        for s in match.split():
            val = scrapertools.find_single_match(data, 'var %s=(.*?);' % s.strip())
            if "+" in val:
                values = scrapertools.find_multiple_matches(val, '"([^"]+)"')
                val = "".join(values)

            url += val.replace('"', "")
        itemlist.append([".mp4 %s [directo]" % q, url])

    return itemlist
'''
