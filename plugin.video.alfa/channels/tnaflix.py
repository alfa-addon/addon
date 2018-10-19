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

host = 'https://www.tnaflix.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/new/1"))
#    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/most-popular/"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/"))


#    itemlist.append( Item(channel=item.channel, title="Chanel" , action="catalogo", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search.php?what=%s&tab=" % texto

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

# <a class="thumb" href="/amateur-porn">
#                           <img src="//img.tnastatic.com//q80w233/category_avatars/amateur-porn.jpg" alt="Best Amateur Porn Videos, XXX Movies, Pornstars &amp; Pics">
#
#                         <div class="vidcountSp">664,324</div>
#           </a>
#           <a class="categoryTitle" href="/amateur-porn" title="Amateur Porn">Amateur Porn</a>
#           <div class="clear catsItemInfo">
#             <div class="inInBtnBlock clear">
#                     				<button class="simpleBtn simpleBtnSG catSubscribeBtns dyn_SUID_visible subcat_6" data-id="6" style="display:none"><i>Subscribe</i></button>
#       				<button class="simpleBtn simpleBtnSG act catUnsubscribeBtns dyn_SUID_visible unsubcat_6" data-id="6" style="display:none"><i>Unsubscribe</i></button>
#       				<button class="simpleBtn simpleBtnSG no_ajax loginLink dyn_SUID_invisible" data-id="6" style="display:block"><i>Subscribe</i></button>
#       				<span id="subcatcount_6">868</span>
#             </div>
#           </div>
#         </li>


    patron  = '<a class="thumb" href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+) Videos, XXX Movies, Pornstars &amp; Pics">.*?<div class="vidcountSp">(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = "http:" + scrapedthumbnail
        scrapedtitle = scrapedtitle.replace("Best", "") + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')




              #         <li      data-vid='2829045' data-nk='5bd2d52f9be960cc79ebe7d9c61d301a' data-vk='922fec57511179b06c2f' data-vn='18' data-date='1511516881' data-th='25' data-hd='1' data-time='480' data-name='Brazzers - Big Tits at Work - Eva Angelina Ramon - Camera Cums In Handy' >
          		# 	<a class='thumb no_ajax' href='/blowjob-videos/Brazzers-Big-Tits-at-Work-Eva-Angelina-Ramon-Camera-Cums-In-Handy/video2829045' data-width='0'>
          		# 		<img class='lazy' src='/images/loader.jpg' data-original='https://img1.tnastatic.com/a16:8q80w300/thumbs/92/25_2829045l.jpg' alt="Brazzers - Big Tits at Work - Eva Angelina Ramon - Camera Cums In Handy"><div class='videoDuration'>8:00</div><div class="hdIcon">720p</div>
          		# 		<div class='watchedInfo' style='display:none'>Watched</div>
          		# 	</a>
          		# 	<a href='/blowjob-videos/Brazzers-Big-Tits-at-Work-Eva-Angelina-Ramon-Camera-Cums-In-Handy/video2829045' class='newVideoTitle nvtHide'>Brazzers - Big Tits at Work - Eva Angelina Ramon - Camera Cums In Handy</a>
          		# 	<div class='thumbHidenBlock'>
              #     <div class='thumbAdditionalInfo'>
              #       <div class='tai clear'>
              #         <div class='floatLeft'>14 minutes ago</div>
              #         <div class='floatRight'><i class='icon-remove-red-eye'></i>18</div>
              #       </div>
              #       <div class='ntlTagsCats'>
              #         <span class='simpleTag' data-href=''>#blowjobs</span> <span class='simpleTag' data-href='/hardcore-porn'>#hardcore</span> <span class='simpleTag' data-href='/teen-porn'>#teens</span> <span class='simpleTag' data-href=''>#hardcore</span> <span class='simpleTag' data-href=''>#cocks</span>
              #       </div>
              #
              #     </div>
              #   </div>
              #   <div data-tooltip="Watch later" class="mdtOutOther tooltip-left"><button class="wlWatch"></button></div>
              # <div data-tooltip="Open in new window" class="mdtOutOther mdtOutOtherSec tooltip-left"><button class="wlNewWind"></button></div>
              #
              #
              #   <div class='curatorUser' style='display: none'>
              #     <div data-chid='76923'>
              #       <a href='/channel/brazzers'><img src='/images/loader.jpg' alt='' data-original='https://img.tnastatic.com/q90w44s/pics/alpha/3104360/96559056/2126995317.gif'></a>
              #     </div>
              #   </div>
      			# </li>    ,duracion,calidad    <div class=\'videoDuration\'>(.*?)</div><div class="hdIcon">(.*?)</div>


    patron  = '<a class=\'thumb no_ajax\' href=\'(.*?)\'.*?data-original=\'(.*?)\' alt="([^"]+)"><div class=\'videoDuration\'>([^<]+)</div>'
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


#			"Next page >>"		<a class="llNav" href="/new/2"></a>


    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')

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

#  \'([^\']+)/\'    <meta itemprop="contentUrl" content="https://cdn-fck.tnaflix.com/tnamp4/922fec57511179b06c2f/Brazzers_Big_Tits_at_Work_Eva_Angelina_Ramon_Camera_Cums_In_Handy.mp4?key=c62fd67fe0ada667127298bcb9e40371?secure=EQdpT0ExwdSiP6btIwawQg==,1511524930" />



    patron  = '<meta itemprop="contentUrl" content="([^"]+)" />'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist

    #     itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=url))
    # return itemlist
