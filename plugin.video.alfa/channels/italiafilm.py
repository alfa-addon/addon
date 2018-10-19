# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import httptools
from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger


DEBUG = config.get_setting("debug")
EVIDENCE = "   "


def mainlist(item):
    logger.info("[gnula.py] mainlist")
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Categorie" , action="categorias", url="http://www.italia-film.org/film-in-streaming/"))
    itemlist.append( Item(channel=item.channel, title="Cerca Film", action="search"))
    return itemlist

def categorias(item):
    logger.info("[italiafilm.py] categorias")
    itemlist = []
    logger.error("io")

    data = scrapertools.cache_page(item.url)

    '''
    <a href="#">Categorie</a>
    <ul class="sub-menu">
    <li id="menu-item-22311" class="menu-item menu-item-type-post_type menu-item-object-page menu-item-22311"><a href="http://www.italiafilms.tv/archivio-alfabetico-film-e-serie-tv/">Archivio alfabetico</a></li>
    <li id="menu-item-21089" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-21089"><a href="http://www.italiafilms.tv/category/now-on-cinema/">Adesso Nei Cinema</a></li>
    <li id="menu-item-21090" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-21090"><a href="http://www.italiafilms.tv/category/anime-e-cartoon/">Anime e Cartoon</a></li>
    <li id="menu-item-21091" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-21091"><a href="http://www.italiafilms.tv/category/archivio-film/">Archivio Film</a></li>
    <li id="menu-item-21092" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-21092"><a href="http://www.italiafilms.tv/category/film-animazione/">Film Animazione</a></li>
    '''

    data = scrapertools.find_single_match(data,'<a href=".">Categorie</a>(.*?)</div>')
    patron = '<li class="[^"]+"><a href="([^"]+)">([^<]+)</a></li>'

    patron = '<li[^>]+><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for url,title in matches:
        scrapedtitle = title
        scrapedurl = urlparse.urljoin(item.url,url)
        scrapedplot = ""
        scrapedthumbnail = ""
        if DEBUG: logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
        itemlist.append( Item(channel=item.channel, action='peliculas', title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True, viewmode="movie_with_plot") )

    return itemlist

# Al llamarse "search" la función, el launcher pide un texto a buscar y lo añade como parámetro
def search(item,texto):
    logger.info("[italiafilm.py] search "+texto)
    itemlist = []
    texto = texto.replace(" ","%20")
    item.url = "http://italiafilm.tv/?s="+texto
    #item.extra = "s="+texto

    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        return []


def peliculas(item):
    logger.info("[italiafilm.py] peliculas")
    itemlist = []

    data = scrapertools.cachePage(item.url)
    patron = '<article(.*?)</article>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:

        title = scrapertools.find_single_match(match,'<h3[^<]+<a href="[^"]+"[^<]+>([^<]+)</a>')
        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<h3[^<]+<a href="([^"]+)"')
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'data-echo="([^"]+)"')

        if (DEBUG): logger.info("title=["+title+"], url=["+url+"], thumbnail=["+thumbnail+"]")

        # Añade al listado de XBMC
        itemlist.append( Item(channel=item.channel, action='findvideos', title=title , url=url , thumbnail=thumbnail , fanart=thumbnail, plot=plot , viewmode="movie_with_plot", folder=True) )

    # Siguiente
    try:
        pagina_siguiente = scrapertools.get_match(data,'<a class="next page-numbers" href="([^"]+)"')
        itemlist.append( Item(channel=item.channel, action="peliculas", title=">> Pagina seguente" , url=pagina_siguiente , folder=True, viewmode="movie_with_plot") )
    except:
        pass

    return itemlist
