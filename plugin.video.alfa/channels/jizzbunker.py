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

host = 'http://jizzbunker.com/es'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular1"))
    itemlist.append( Item(channel=item.channel, title="Tendencia" , action="peliculas", url=host + "/trending"))
    itemlist.append( Item(channel=item.channel, title="Dururacion" , action="peliculas", url=host + "/longest"))
#    itemlist.append( Item(channel=item.channel, title="HD" , action="peliculas", url=host + "/high-definition/date-last-week/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?query=%s/" % texto

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
    data = scrapertools.get_match(data,'<h3>CLIPS</h3>(.*?)<h3>FILM</h3>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)



    patron  = '<li><a href="([^"]+)" title="">.*?<span class="videos-count">([^"]+)</span><span class="title">([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

     # <li><figure>
     #            <a href="http://jizzbunker.com/es/channel/sexo-duro" rel="tag" class="img"
     #               title="sexo duro">
     #                <img class="lazy" data-original="http://t8.cdn3x.com/t/240/0000158723/008.jpg" alt="sexo duro" width="240" height="180" />
     #            </a>
     #        </figure><figcaption>
     #            <a href="http://jizzbunker.com/es/channel/sexo-duro" rel="tag">sexo duro<span class="score">211982</span></a>
     #        </figcaption></li>

    patron  = '<li><figure>.*?<a href="([^"]+)".*?<img class="lazy" data-original="([^"]+)" alt="([^"]+)".*?<span class="score">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedurl = scrapedurl.replace("channel", "channel30")
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

# <li><figure>
#         <a href="http://jizzbunker.com/es/1548542/please-no-names.html" class="img " title="gorditas guapas, big butt, sexo duro, mulatas, madres para coger, tetas masivas, black and ebony, peeing, sexy"
#                         data-thumb="0"
#             data-id="1548542">
#                             <img class="lazy" data-original="http://t0.cdn3x.com/t/240/0001548542/000.jpg" alt="gorditas guapas, big butt, sexo duro, mulatas, madres para coger, tetas masivas, black and ebony, peeing, sexy" width="240" height="180" />
#                     </a>
#         <figcaption>
#                             <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/gorditas-guapas">gorditas guapas</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/big-butt">big butt</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/sexo-duro">sexo duro</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/mulatas">mulatas</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/madres-para-coger">madres para coger</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/tetas-masivas">tetas masivas</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/black-and-ebony">black and ebony</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/peeing">peeing</a>
#                 <a class="tag" rel="tag" href="http://jizzbunker.com/es/channel/sexy">sexy</a>
#                                         <ul class="properties">
#                 <li class="dur"><time datetime="PT32M2S">32:02</time>
#                 <li class="pubtime">4 days ago</li>
#                                             </ul>
#         </figcaption>
#     </figure></li>
#         <li><figure>

    patron  = '<li><figure>.*?<a href="([^"]+)/([^"]+).html".*?<img class="lazy" data-original="([^"]+)".*?<time datetime=".*?">([^"]+)</time>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedtitle,scrapedthumbnail,duracion in matches:
        url = scrapedurl + "/" + scrapedtitle + ".html"
#        year = " (%s)" % year

        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        contentTitle = title
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#			"Next page >>"		<li><a href="trending/2" rel="next">&rarr;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">&rarr;</a>')

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

#            {type:'video/mp4',src:'http://c26.cdn3x.com/v/yzvKajhi2MeAoLMYEcxFkA/1511265166/02/21/69/0000022169.480'}

    patron  = 'type:\'video/mp4\',src:\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                            thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

#        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist
