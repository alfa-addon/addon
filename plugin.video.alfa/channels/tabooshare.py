# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb

## italiafilm

'''
([^<]+) para extraer el texto entre dos tags “uno o más caracteres que no sean <" ^ cualquier caracter que no sea <
"([^"]+)" para extraer el valor de un atributo
\d+ para saltar números
\s+ para saltar espacios en blanco
(.*?) cuando la cosa se pone complicada

    ([^<]+)
  \'([^\']+)\'



    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist

'''

host = 'http://tabooshare.com'


def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

#    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h3>Categories</h3>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



    patron  = '<li class="cat-item cat-item-\d+"><a href="(.*?)" >(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')


    patron = '<div class="post" id="post-\d+">.*?<a href="([^"]+)" title="(.*?)"><img src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)

    scrapertools.printMatches(matches)


    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
        scrapedtitle = scrapedtitle.replace(" &#8211; Free Porn Download", "")
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = "https://hqcollect.tv" + scrapedurl
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )



# <span class="current">1</span><a href='http://tabooshare.com/page/2/'


# "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<span class="current">.*?<a href="(.*?)"')

    if next_page_url=="http://NaughtyPorn.net/":
        next_page_url = scrapertools.find_single_match(data,'<span class="current">.*?<a href=\'(.*?)\'')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data


# <strong>Download</strong><br />
# <a href="https://upstore.net/Bz2rW">https://upstore.net/Bz2rW</a></div>
# <div style="text-align: center;">&#8211;<br />
# <a href="http://ssh.tf/6pdcHZNhn">http://ssh.tf/6pdcHZNhn</a></div>
# <div style="text-align: center;">&#8211;</div>
# <div style="text-align: center;"><a href="https://openload.co/f/Cy6a6RXkBjA"><strong>Watch Online</strong></a><br />
# &#8211;</div>

    data = scrapertools.get_match(data,'<strong>Download</strong>(.*?)<div class="clear"></div>')
    patron = '<a href="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)


    for scrapedurl in matches:
        scrapedplot = ""
        itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl , url=scrapedurl , plot=scrapedplot , folder=True) )
    return itemlist
'''

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
