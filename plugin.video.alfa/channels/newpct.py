# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from core import servertools
from core import scrapertools
from core.item import Item
from platformcode import logger
from core import httptools

from platformcode import config
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'newpct')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'newpct')

Host='http://www.tvsinpagar.com'


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas",url=Host+"/peliculas/"))
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series",url=Host+"/series/"))
    #itemlist.append(Item(channel=item.channel, action="listado", title="Anime", url=Host+"/anime/",
    #                     viewmode="movie_with_plot"))
    #itemlist.append(
    #    Item(channel=item.channel, action="listado", title="Documentales", url=Host+"/documentales/",
    #         viewmode="movie_with_plot"))
    #itemlist.append(Item(channel=item.channel, action="search", title="Buscar"))
    return itemlist

def submenu(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li><a href="'+item.url+'"><i.+?<ul>(.+?)<\/ul>' #Filtrado por url
    data_cat = scrapertools.find_single_match(data, patron)
    patron_cat='<li><a href="(.+?)" title="(.+?)".+?<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_cat, patron_cat)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl,action="listado"))
    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_data='<ul class="pelilist">(.+?)</ul>'
    data_listado = scrapertools.find_single_match(data, patron_data)
    patron_listado='<li><a href="(.+?)" title=".+?"><img src="(.+?)".+?><h2'
    if 'Serie' in item.title:
    	patron_listado+='.+?>'
    else:
    	patron_listado+='>'
    patron_listado+='(.+?)<\/h2><span>(.+?)<\/span><\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_listado, patron_listado)
    for scrapedurl, scrapedthumbnail,scrapedtitle,scrapedquality in matches:
    	if 'Serie' in item.title:
    		action="episodios"
    	else:
    		action="findvideos"    	
    	itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl,thumbnail=scrapedthumbnail, action=action, quality=scrapedquality,show=scrapedtitle))
    # Página siguiente
    patron_pag='<ul class="pagination"><li><a class="current" href=".+?">.+?<\/a>.+?<a href="(.+?)">'
    siguiente = scrapertools.find_single_match(data, patron_pag)
    itemlist.append(
             Item(channel=item.channel, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=siguiente, action="listado"))
    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_data='<ul class="buscar-list">(.+?)</ul>'
    data_listado = scrapertools.find_single_match(data, patron_data)
    patron = '<img src="(.+?)" alt=".+?">.+?<div class=".+?">.+?<a href=(.+?)" title=".+?">.+?>Serie.+?>(.+?)<'
    matches = scrapertools.find_multiple_matches(data_listado, patron)
    for scrapedthumbnail,scrapedurl, scrapedtitle in matches:
    	if " al " in scrapedtitle:
    		#action="episodios"
    		titulo=scrapedurl.split('http')
    		scrapedurl="http"+titulo[1]
    	itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl,thumbnail=scrapedthumbnail, action="findvideos", show=scrapedtitle))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    new_item = []
    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data = data)
    url = scrapertools.find_single_match( data, 'location.href = "([^"]+)"')
    new_item.append(Item(url = url, title = "Torrent", server = "torrent", action = "play"))
    itemlist.extend(new_item)
    for it in itemlist:
        it.channel = item.channel
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    return itemlist
