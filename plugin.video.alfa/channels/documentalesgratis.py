# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para documentalesgratis.es
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os,sys
import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb


__channel__ = "documentalesgratis"
__category__ = "D"
__type__ = "generic"
__title__ = "documentalesgratis"
__language__ = "ES"
homepage = "http://www.documentalesgratis.es"


def isGeneric():
    return True

def mainlist(item):
    logger.info("[documentalesgratis.py] mainlist")

    itemlist = []
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="Novedades"      , url="http://www.documentalesgratis.es/video/"))
    itemlist.append( Item(channel=__channel__, action="novedades"  , title="+Vistos"      ,   url="http://www.documentalesgratis.es/video/?order_post=viewed"))
    itemlist.append( Item(channel=__channel__, action="novedades" ,  title="+Votados" ,       url="http://www.documentalesgratis.es/video/?order_post=linked"))
    itemlist.append( Item(channel=__channel__, action="novedades" ,  title="+Comentarios" ,   url="http://www.documentalesgratis.es/video/?order_post=comments"))
    itemlist.append( Item(channel=__channel__, action="categorias" , title="categorías" ,     url="http://www.documentalesgratis.es/"))
    itemlist.append( Item(channel=__channel__, action="tags" ,       title="Tag: +Buscados" , url="http://www.documentalesgratis.es"))

    itemlist.append( Item(channel=__channel__, action="search"     , title="Buscar"))
    return itemlist

def novedades(item):
    logger.info("[documentalesgratis.py] novedades")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    #logger.info(data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    data2 = re.compile('<div class="section-header">(.*?)</div></div></div>',re.DOTALL).findall(data)
    matches = re.compile('<div class="item-img">(.*?)</h3>',re.DOTALL).findall(data2[0])
    if not len(matches) == 0 :
        scrapertools.printMatches(matches)

        for match in matches:
            logger.info(str(match))
            try:

                scrapedurl = scrapertools.get_match(match,'<h3><a href="([^"]+)">(.*?)<')
                logger.info(scrapedurl[0])
                scrapedtitle = scrapedurl[1]
                scrapedurl = scrapedurl[0]
                logger.info("scrapedtitle")
                scrapedthumbnail = scrapertools.get_match(match,'src="(.*?)"')
                logger.info(scrapedthumbnail)
                scrapedplot = ''
                itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , fanart=scrapedthumbnail, folder=False) )

            except:
                logger.info("documentalesgratis.novedades Error al añadir entrada "+match)
                pass
    else:
        matches = re.compile('<div class="col-sm-4 col-xs-6 item responsive-height">(.*?)</h3>',re.DOTALL).findall(data2[0])
        scrapertools.printMatches(matches)
        #itemlist.append( Item(channel=__channel__, action="submenu", title="Submenu - "+item.title  , url=item.url , thumbnail="" , plot="" , folder=True) )
        for match in matches:
            logger.info(str(match))
            try:

                scrapedurl = scrapertools.get_match(match,'<h3><a title="[^"]+" href="([^"]+)">(.*?)<')
                logger.info(scrapedurl[0])
                scrapedtitle = scrapedurl[1]
                scrapedurl = scrapedurl[0]
                logger.info("scrapedtitle")
                scrapedthumbnail = scrapertools.get_match(match,'src="(.*?)"')
                logger.info(scrapedthumbnail)
                scrapedplot = ''
                #logger.info(scrapedplot)
                scrapedurl = urlparse.urljoin(item.url,scrapedurl)
                itemlist.append( Item(channel=__channel__, action="play", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , fanart=scrapedthumbnail, folder=False) )

            except:
                logger.info("documentalesgratis.busqueda Error al añadir entrada "+match)
                pass


    # Busca enlaces de paginas siguientes...
    try:
        next_page_url = scrapertools.get_match(data,'<a class="next page-numbers" href="([^"]+)"')

        if "Pagina siguiente" in item.title:
            item.plot = item.plot
        else:
            item.plot = item.title
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__, action="novedades", title=">> Pagina siguiente "  , url=next_page_url , thumbnail="" , plot=item.plot, folder=True) )
    except:
        logger.info("documentalesgratis.novedades Siguiente pagina no encontrada")

    return itemlist

def categorias(item):
    logger.info("[documentalesgratis.py] categorias")
    itemlist = []
    data = scrapertools.cache_page(item.url)

    # Saca el bloque con las categorias
    data = scrapertools.get_match(data,'<ul id="menu-header-menu"(.*?)</nav>')
    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url=match[0]))

    return itemlist


def tags(item):
    logger.info("[documentalesgratis.py] categorias")
    itemlist = []

    # Saca el bloque con los tag mas buscados
    data = scrapertools.cache_page(item.url)
    data = scrapertools.get_match(data,'<div class="widget mars-keycloud-widgets"><h2 class="widgettitle">Lo(.*?)</div>')
    patron = "<a href='([^']+)'[^>]+>([^<]+)</a>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        itemlist.append( Item(channel=__channel__ , action="novedades" , title=match[1],url=match[0]))

    return itemlist

def search(item,texto):
    #http://www.documentalesgratis.es/?s=marte
    logger.info("[documentalesgratis.py] search")
    if item.url=="":
        item.url="http://www.documentalesgratis.es/?s=%s"
    texto = texto.replace(" ","+")
    item.url = item.url % texto
    try:
        return novedades(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []

def play(item):
    logger.info("documentalesgratis.play")
    itemlist = []

    # Descarga la pagina
    data = scrapertools.cachePage(item.url)
    #logger.info(data)
    patron= '<div class="post-entry"><h2>(.*?)</p>'
    scrapedplot = re.compile(patron,re.DOTALL).findall(data)
    scrapedplot = re.compile("<.*?>",re.DOTALL).sub("",scrapedplot[0])
    scrapedplot = scrapertools.entityunescape(scrapedplot[0])
    logger.info(scrapedplot)

    # Busca los enlaces a los videos
    video_itemlist = servertools.find_video_items(data=data)
    for video_item in video_itemlist:
        itemlist.append( Item(channel=__channel__ , action="play" , server=video_item.server, title=item.title+video_item.title,url=video_item.url, thumbnail=video_item.thumbnail, plot=scrapedplot, folder=False))

    # Extrae los enlaces a los videos (Directo)
    patronvideos = "src= '([^']+)'"
    matches = re.compile(patronvideos,re.DOTALL).findall(data)
    if len(matches)>0:
        if not "www.youtube" in matches[0]:
            itemlist.append( Item(channel=__channel__ , action="play" , server="Directo", title=item.title+" [directo]",url=matches[0], thumbnail=item.thumbnail, plot=scrapedplot))

    return itemlist

# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    items = novedades(mainlist_items[0])
    bien = False
    for singleitem in items:
        mirrors = servertools.find_video_items( item=singleitem )
        if len(mirrors)>0:
            bien = True
            break

    return bien
