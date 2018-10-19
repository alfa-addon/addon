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

host = 'https://fapality.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/popular/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top/"))

    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/"))
#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
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
#    data = scrapertools.get_match(data,'<div class=\'row alphabetical\' id=\'categoryList\'>(.*?)<h2 class="heading4">Popular by Country</h2>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <div class="item"><a href="https://fapality.com/categories/anal/" title="Anal movies"><span class="title">Anal</span><span class="img_wrapper"><img src="https://i.fapality.com/videos_screenshots/22000/22085/240x180/55.jpg"></span><span class="img_thumbs"><span><img src="https://i4.fapality.com/videos_screenshots/22000/22088/150x113/53.jpg"></span><span><img src="https://i4.fapality.com/videos_screenshots/22000/22053/150x113/54.jpg"></span><span><img src="https://i2.fapality.com/videos_screenshots/22000/22033/150x113/10.jpg"></span></span></a><div class="meta"><div class="right">1487 movies</div><i class="fa fa-thumbs-up left-pull"></i> 99%</div></div>
# <div class="item"><a href="https://fapality.com/channels/evil-angel/" title="Evil Angel movies"><span class="title">Evil Angel</span><span class="img_wrapper"><img src="https://fapality.com/contents/content_sources/62/s2_evilangel.jpg" alt="Evil Angel"/></span><span class="img_thumbs"><span><img src="https://i4.fapality.com/videos_screenshots/9000/9472/150x113/16.jpg"></span><span><img src="https://i.fapality.com/videos_screenshots/5000/5613/150x113/39.jpg"></span><span><img src="https://i2.fapality.com/videos_screenshots/12000/12000/150x113/8.jpg"></span></span></a><div class="meta"><div class="right">1558 movies</div> <i class="fa fa-comments left-pull"></i> 3 <i class="fa fa-users  left-pull"></i> 236<i class="fa fa-thumbs-up left-pull"></i> 95%</div></div>

    patron  = '<div class="item"><a href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)">.*?<div class="right">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace("movies", "") + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div id="inner-content" class="row">(.*?)<h4 class="widgettitle">New</h4>')


# <li class="masonry-item item " data-id="22067" data-video="/get_file/1/f0f9eea637d2e22c7ac6db864fcf6125/22000/22067/22067_6s_trailer.mp4">
# <a href="https://fapality.com/22067/" class="kt_imgrc popfire" title="Little brunette Maddie Winters makes love with stepbrother" ><span class="img_wrapper"><img src="https://i.fapality.com/videos_screenshots/22000/22067/240x180/15.jpg" alt="Little brunette Maddie Winters makes love with stepbrother" onmouseover="KT_rotationStart(this, 'https://i.fapality.com/videos_screenshots/22000/22067/200x150/', 96)" onmouseout="KT_rotationStop(this)"/></span><span class="title" >Little brunette Maddie Winters makes love with stepbrother</span></a><div class="meta"><span class="rating good" title="Average Rating"><i class="fa fa-thumbs-up"></i> 80%</span><span class="views" title="Views"><i class="fa fa-eye"></i> 632</span></div><div class="description">Petite build angel Maddie Winters receives roses from his...</div></li>

    patron  = '<li class="masonry-item item ".*?<a href="([^"]+)" class="kt_imgrc popfire" title="([^"]+)" >.*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail  in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        title = scrapedtitle
#        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li itemprop="url" class="current"><a>02</a></li>
#								<li itemprop="url"><a href="/newest/3/" title="Page 03">03</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li itemprop="url" class="current">.*?<a href="([^"]+)"')

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

# </iframe>';return embedCode;}var video_id = 18284;var flashvars = {video_id: '18284', license_code: '$518594117109328', rnd: '1532157990',
# video_url: 'https://fapality.com/get_file/1/2ee66690f47f90750c24a23b5e9d8bb6/18000/18284/18284.mp4/?br=2371', postfix: '.mp4', video_url_text: '720p',
# video_alt_url: 'https://fapality.com/get_file/1/b6c266c2ac072f528f9168ae4ed6539a/18000/18284/18284_480p.mp4/?br=1477',  video_alt_url_text: '480p', default_slot: '2',
# video_alt_url2: 'https://fapality.com/get_file/1/c3003748f39f90d35a6595d1a9bd963d/18000/18284/18284_240p.mp4/?br=607',  video_alt_url2_text: '240p',

    patron  = 'video_url: \'([^\']+)\''
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
