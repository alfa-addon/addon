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

host = 'http://www.elreyx.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/peliculasporno.html"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/peliculasporno.html"))
    itemlist.append( Item(channel=item.channel, title="Escenas" , action="escenas", url=host + "/index.html"))
    itemlist.append( Item(channel=item.channel, title="Productora" , action="productora", url=host + "/index.html"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://elreyx.com/search-%s" % texto + ".html"

    try:
        return escenas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def productora(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron  = '<a href="([^<]+)" title="View Category ([^<]+)">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="escenas", title=scrapedtitle , url="https:" + scrapedurl , thumbnail="https:" + scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <td><a href="//www.elreyx.com/categoria/1080p" title="View Category 1080p">1080p</a></td>
# <td><a href="//www.elreyx.com/peliculasporno/amateur" title="Movies Amateur">Amateur</a></td>
    patron  = '<td><a href="([^<]+)" title="Movies ([^<]+)">.*?</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url="https:" + scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    return itemlist




def escenas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


    patron  = '<div class="notice_image">.*?<a title="([^"]+)" href="([^"]+)">.*?<img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url="https:" + scrapedurl , thumbnail="https:" + scrapedthumbnail , plot=scrapedplot , folder=True) )

#                                                        <li><a href="#" class="current">1</a></li>
#    current_page = scrapertools.find_single_match(data,'<li><a href="#" class="current">(.*?)</a>')
#    <li><a href="#" class="current">1</a></li>
#    <li><a href='peliculasporno2.html' title='Pagina 2'>&raquo;</a></li>
#    next_page = int(current_page) + 1
#    next_page_url = "http://www.elreyx.com/index"+str(next_page)+".html"


#                                                        <a href='indice2.html' title='Pagina 2'><span class="visible-xs-inline">Siguiente</span> &raquo;</a></li>
    next_page_url = scrapertools.find_single_match(data,'<a href=\'([^\']+)\' title=\'Pagina \d+\'><span class="visible-xs-inline">Siguiente</span> &raquo;</a>')
    next_page_url = "http://www.elreyx.com/"+str(next_page_url)

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="escenas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


    patron  = '<div class="captura"><a title="([^"]+)" href="([^"]+)".*?><img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedtitle,scrapedurl,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url="https:" + scrapedurl , thumbnail="https:" + scrapedthumbnail , plot=scrapedplot , folder=True) )


#       <li><a href='peliculasporno2.html' title='Pagina 2'>&raquo;</a></li>

    next_page_url = scrapertools.find_single_match(data,'<li><a href=\'([^\']+)\' title=\'Pagina \d+\'>&raquo;</a>')
    next_page_url = "http://www.elreyx.com/"+str(next_page_url)

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)


    # <div id="tab4"><IFRAME SRC="http://2424rskfsdkgksdg435.com/?u=inTWk" FRAMEBORDER=0 MARGINWIDTH=0 MARGINHEIGHT=0 SCROLLING=NO WIDTH=640 HEIGHT=360 allowfullscreen></IFRAME> <div class="box box_red_videomega">
    #            <a href="https://myvideosfree.me/?le=WVVoU01HTkViM1pNTWxKb1pFYzVkMkl6U25WTWJVNTJZbE01YkdKWFNteGFRekY1WkcweGNtSXpVWGhPYldSM1QwaFJkV0ZJVW5SaVFTd3M," title="" target="_blank">
    #            <span style="padding-left: 40px;line-height:40px; color: #c83b3d;"><b>See video online in Full Screen from external page</b></span></a>
    #           </div>
    # </div>
    # <div id="tab3"><iframe src="http://2424rskfsdkgksdg435.com/?u=I0Cg" scrolling="no" frameborder="0" width="640" height="360" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>  <div class="box box_red_openload">
    #            <a href="http://2424rskfsdkgksdg435.com/?u=I0Cg" title="" target="_blank">
    #            <span style="padding-left: 40px;line-height:40px; color: #c83b3d;"><b>See video online in Full Screen from external page</span></b></a>
    #           </div>
    # </div>


#    data = scrapertools.get_match(data,'Streaming and Download Links:(.*?)</p>')
    patron = '<iframe src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

#    scrapedurl = scrapertools.find_single_match(data,'<iframe width=.*?src=\'(.*?)\'')
#    scrapedurl = str(scrapedurl)
    for scrapedurl in matches:
        scrapedplot = ""
#        scrapedtitle = str(scrapedtitle)
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )

    patron = '<IFRAME SRC="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

#    scrapedurl = scrapertools.find_single_match(data,'<iframe width=.*?src=\'(.*?)\'')
#    scrapedurl = str(scrapedurl)
    for scrapedurl in matches:
        scrapedplot = ""
#        scrapedtitle = str(scrapedtitle)
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot="" , folder=True) )



    return itemlist


def play(item):
    logger.info()
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
