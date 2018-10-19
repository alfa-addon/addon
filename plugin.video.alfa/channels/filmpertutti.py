# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para piratestreaming
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
from core import jsontools




def mainlist(item):
    logger.info("pelisalacarta.filmpertutti mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimi film inseriti", action="peliculas", url="http://www.filmpertutti.black/category/film/"))
    itemlist.append( Item(channel=item.channel, title="Categorie film", action="categorias", url="http://www.filmpertutti.black/category/film/"))
    itemlist.append( Item(channel=item.channel, title="Serie TV" , action="peliculas", url="http://www.filmpertutti.black/category/serie-tv/"))
    itemlist.append( Item(channel=item.channel, title="Anime Cartoon Italiani", action="peliculas", url="http://www.filmpertutti.co/category/anime-cartoon-italiani/"))
    itemlist.append( Item(channel=item.channel, title="Anime Cartoon Sub-ITA", action="peliculas", url="http://www.filmpertutti.co/category/anime-cartoon-sub-ita/"))
    itemlist.append( Item(channel=item.channel, title="Cerca...", action="search"))
    return itemlist

def categorias(item):
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas) <option data-src="http://www.filmpertutti.black/category/film/animazione/">Animazione</option>
    patron  = '<option data-src="([^"]+)">([^"]+)</option>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def search(item,texto):
    logger.info("[filmpertutti.py] "+item.url+" search "+texto)
    item.url = "http://www.filmpertutti.eu/search/"+texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def peliculas(item):
    logger.info("pelisalacarta.filmpertutti peliculas")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)
    '''
    <li><a href="http://www.filmpertutti.black/in-the-shadow-of-iris-2016/" data-thumbnail="http://www.filmpertutti.black/wp-content/uploads/2017/05/iris00.jpg"><div>
                        <div class="title">In the Shadow of Iris [HD] (2016)</div>
                        <div class="episode" title="IMDb">5.8</div>                        <div class="hd" title="Filmato in alta definizione">HD</div>                    </div><a target="__blank" href="http://www.filmpertutti.black/fdh/wth.php?u=aW4tdGhlLXNoYWRvdy1vZi1pcmlzLTIwMTY="><p><i class="fa fa-play-circle-o" aria-hidden="true"></i> Guarda ora</p></a></a></li>
    '''
    '''
    div class="col-xs-6 col-sm-3 col-md-3 col-lg-2  box-container-single-image">
    <div class="general-box container-single-image">
    <a href="http://www.filmpertutti.co/barely-lethal-16-anni-e-spia-2015/" rel="bookmark" title="Link to Barely Lethal – 16 Anni e Spia (2015)" target="">
    <img width="330" height="488" src="http://www.filmpertutti.co/wp-content/uploads/2015/06/barelylethal.jpg" class="img-responsive center-block text-center wp-post-image" alt="barelylethal" />                    <h2>Barely Lethal – 16 Anni e Spia (2015)</h2>
    '''

    patron = '<li><a href="([^"]+)" data-thumbnail="([^"]+)">.*?<div class="title">([^"]+)</div>'

    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        plot = ""
        title=scrapedtitle
        url=urlparse.urljoin(item.url,scrapedurl)
        thumbnail=urlparse.urljoin(item.url,scrapedthumbnail)
        if title.startswith("Link to "):
            title = title[8:]
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title , url=url , thumbnail=thumbnail , plot=plot , folder=True) )

    # Extrae el paginador  <li><a href="http://www.filmpertutti.black/category/film/page/2/" >Pagina successiva &raquo;</a></li>
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" >Pagina successiva &raquo;</a>')
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next Page >>" , url=next_page_url , folder=True) )

    return itemlist
