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

host = 'http://hd.xtapes.to'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "Peliculas" + "[/COLOR]" , action="peliculas", url=host + "/full-porn-movies/?display=tube&filtre=date"))
    itemlist.append( Item(channel=item.channel, title="[COLOR yellow]" + "       Studio" + "[/COLOR]" , action="catalogo", url=host))

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/?filtre=date&cat=0"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/?display=tube&filtre=views"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/?display=tube&filtre=rate"))
    itemlist.append( Item(channel=item.channel, title="Mas larga" , action="peliculas", url=host + "/?display=tube&filtre=duree"))





    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host))
#    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))



    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

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

    if item.title=="Canal":
        data = scrapertools.get_match(data,'<div class="footer-banner">(.*?)<div id="footer-copyright">')
    else:
       data = scrapertools.get_match(data,'<li id="menu-item-16"(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#           <li id="menu-item-123" class="menu-item menu-item-type-taxonomy menu-item-object-category current-menu-item menu-item-123"><a href="http://hd.xtapes.to/free-bangbros-porn/">BangBros</a></li>

    patron  = '<a href="([^"]+)">([^"]+)</a></li>'
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
    data = scrapertools.get_match(data,'<a>Categories</a>(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#          <li id="menu-item-34" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-34"><a href="http://hd.xtapes.to/anal-porn/">Anal</a></li>



    patron  = '<a href="([^"]+)">([^"]+)</a>'
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


# <li class="border-radius-5 box-shadow">
# <img src="https://www.xtapes.tv/pic/008iuz5g5d.jpg" alt="Mommy Needs A MANicure | Reagan Foxx, Jordi El Nino Polla | 2018" title="Mommy Needs A MANicure | Reagan Foxx, Jordi El Nino Polla | 2018" />
# <a href="http://hd.xtapes.to/mommy-needs-a-manicure-reagan-foxx-jordi-el-nino-polla-2018/" title="Mommy Needs A MANicure | Reagan Foxx, Jordi El Nino Polla | 2018"><span>Mommy Needs A MANicure | Reagan Foxx, Jordi El Nino Polla | 2018</span></a>
# <div class="listing-infos">
#
# <div class="views-infos">2503 <span class="views-img"></span></div>
#
# <div class="time-infos">00:33:09<span class="time-img"></span></div>
#
# <div class="rating-infos">66%<span class="rating-img"></span></div>
# </div>
# </li>


    patron  = '<li class="border-radius-5 box-shadow">.*?src="([^"]+)".*?<a href="([^"]+)" title="([^"]+)">.*?<div class="time-infos".*?>([^"]+)<span class="time-img">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail,scrapedurl,scrapedtitle,duracion  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
        title = scrapedtitle
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle = title,  contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"	<li><a class="next page-numbers" href="http://hd.xtapes.to/page/2/?filtre=date&#038;cat=0#038;cat=0">Next videos &raquo;</a></li>
#                            <li><a class="next page-numbers" href="http://hd.xtapes.to/big-tits-free-porn/page/2/">Next videos &raquo;</a></li>
#                            <li><a class="next page-numbers" href="http://hd.xtapes.to/page/3/?display=tube&#038;filtre=views#038;filtre=views">Next videos &raquo;</a></li>
#                            <li><a class="next page-numbers" href="http://hd.xtapes.to/page/3/?display=tube&#038;filtre=rate#038;filtre=rate">Next videos &raquo;</a></li>

    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next video')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        next_page_url = next_page_url.replace("#038;cat=0#038;", "").replace("#038;filtre=views#038;", "").replace("#038;filtre=rate#038;", "").replace("#038;filtre=duree#038;", "")
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist

'''
def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

# <video id="html5-player" autobuffer controls class="video-js vjs-default-skin vjs-big-play-centered" width="100%" height="100%" src="https://www.gotporn.com/gvf/lmqtthjmz8bbyj7dyAymb8x5hx9fytcp5z0q8rAnlr45jy0kq75v5fly890mm9nt1n684yjknxj1fp1mt6ftqf5k8zAt7sxnqh5p865k0pqbxzzqrhfb0m9jmdbdt543jy0gst3b4gbw5mrlrAsAp39h10lv4364vd16Aq546wsgqv962nksxxcy374s1vw0rAch2qymxlpw55mlgAcf2cddvwv91p5qspwrp66dr94kApfp07hxbltwnpz67A264wbd35yrgls4gnbdc9Aypc1mjf8gsjvyf00bqsx5wsvb2jwrty44w6wgpgbylfk1gqgkpnw4ylfjw">
# <source src="https://www.gotporn.com/gvf/lmqtthjmz8bbyj7dyAymb8x5hx9fytcp5z0q8rAnlr45jy0kq75v5fly890mm9nt1n684yjknxj1fp1mt6ftqf5k8zAt7sxnqh5p865k0pqbxzzqrhfb0m9jmdbdt543jy0gst3b4gbw5mrlrAsAp39h10lv4364vd16Aq546wsgqv962nksxxcy374s1vw0rAch2qymxlpw55mlgAcf2cddvwv91p5qspwrp66dr94kApfp07hxbltwnpz67A264wbd35yrgls4gnbdc9Aypc1mjf8gsjvyf00bqsx5wsvb2jwrty44w6wgpgbylfk1gqgkpnw4ylfjw" type='video/mp4'>
# </video>
# https://www.gotporn.com/gvf/hd613pdg386qhf9zcyqg71kdtdym3AkAgs7xrtAg9rp16nq0sA30fqsfycA91z072p7fdvynlrk3lvx00lAc7s2qfb5pwm32pz2jckdrnj0AA8lwy9l5hky6td8ld5qqz4y7nht2qtzvhsyq7k7ktt7v5j025bwtxy4qc9cmmy0hb8jpfjlf2syt8l43zkm83br7sm90c679bxjv9wmb5vgpj5d6n2zttjgslgj8cbdr93p4tk8yfrk2bx3bx9pfn7t2znj708Apr71jk2ssc99srxz3fp2h9z87yd10fxjfc6hh0tdhsc0nxg99zgd76np2myy1z1shxhy2pv9hpfkgwxzq7hptdph088q
# https://vs31.gotporn.com/fcontent/ffab47945dcdbe9eeb0566609130366f/5a54b166/2018/01/08/2018-01-08-8094512/GotPorn-gorgeous-teen-assistant-micah-moore-taught
# https://www.gotporn.com/gvf/7g3Agxy4bjrl5g5rAAAbmgxlbt2sfzAlkpAc8hq24zrsrzr2ct50hc8nvhmr4vb5jht4q4tl4bxyt9dyfAd5m9xv10nz1dw2d0y5x3cwv64x9p3fss8rt6wsr5rm25Az7crjg361xbtqzms0tdbbk8fw8hdtql8k9gb12z4hxydkc436ryc2kqhsbb22qs4r5mz109qccz2ntn52wljAp8hs4Aw0qmyjyszdclbl8qwgq7vbvt70lld628dq0gcthqr6zpjy8x6k97A3pjf209b2d7t00fx208w4c11v59bn0bblA57wl0pl9d2mgv75r1p0t118j9jkplkryx95x6rh947z3krggnk7lxq
# https://vs29.gotporn.com/fcontent/605b7cf8ff7626cde3072fef8f081688/5a54b246/2018/01/09/2018-01-09-8095470/GotPorn-banging-this-nerd-snatch-in-doggie-and-cowgirl-position.mp4

    patron  = '<source src="([^"]+)" type=\'video/mp4\'>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
#        scrapedurl = "http:" + scrapedurl.replace("\\", "")
        title = scrapedurl

    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist

'''
def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
