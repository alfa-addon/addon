# -*- coding: utf-8 -*-

import re
import urlparse

from channels import filtertools
from platformcode import config, logger
from platformcode import platformtools
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools

host = "http://mundiseries.com"

                
def mainlist(item):
    logger.info()
    itemlist = list()    

    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=urlparse.urljoin(host, "/lista-de-series")))

    return itemlist

def categorias(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_cat='<li id="menu-item-15068" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    categorias=scrapertools.find_single_match(data,patron_cat)
    patron = '<li id="menu-item-.+?" class=".+?"><a href="([^"]+)">([^"]+)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(categorias, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def alfabetico(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_alf1='<li id="menu-item-15069" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    patron_alf2='<li id="menu-item-15099" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    alfabeto1=scrapertools.find_single_match(data,patron_alf1)
    alfabeto2=scrapertools.find_single_match(data,patron_alf2)
    alfabeto=alfabeto1+alfabeto2
    patron = '<li id="menu-item-.+?" class=".+?"><a href="([^"]+)">([^"]+)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(alfabeto, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def top(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_top='<li id="menu-item-15087" class=".+?"><.+?>.+?<\/a>(.+?)<\/ul><\/li>'
    top=scrapertools.find_single_match(data,patron_top)
    patron = '<a href="([^"]+)">([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(top, patron)
    for link, name in matches:
        title=name
        url=link
        itemlist.append(item.clone(title=title, url=url, plot=title, action="lista_gen", show=title))
    return itemlist

def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)"><img src="([^"]+)" alt="ver ([^"]+) online'
    matches = scrapertools.find_multiple_matches(data, patron)
    for link, thumbnail, name in matches:
        title=name
        url=host+link
        thumbnail=host+thumbnail
        itemlist.append(item.clone(title=title, url=url, thumbnail=thumbnail, action="temporada"))
    return itemlist

def temporada(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger.info("preon,:"+data)
    patron = '<a href="([^"]+)"><div class="item-temporada"><img alt=".+?" src="([^"]+)"><div .+?>Ver ([^"]+)<\/div><\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for link,thumbnail,name in matches:
        title=name
        url=host+link
        thumbnail=host+thumbnail
        itemlist.append(item.clone(title=title, url=url, thumbnail=thumbnail,action="episodios"))
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_caps = 'href="http:.+?\/mundiseries.+?com([^"]+)" alt="([^"]+) Capitulo ([^"]+) Temporada ([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_show='<h1 class="h-responsive center">.+?'
    patron_show+='<font color=".+?>([^"]+)<\/font>'
    show = scrapertools.find_single_match(data,patron_show)
    for link, name,cap,temp in matches:
        if '|' in cap:
            cap = cap.replace('|','')
        if '|' in temp:
            temp = temp.replace('|','')
        if '|' in name:
            name = name.replace('|','')
        title = "%sx%s %s"%(temp, str(cap).zfill(2),name)
        url=host+link
        itemlist.append(Item(channel=item.channel, action="findvideos", 
                             title=title, url=url, show=show))
    if config.get_videolibrary_support() and len(itemlist) > 0:

        itemlist.append(Item(channel=item.channel, title="Añadir Temporada/Serie a la biblioteca de Kodi", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    id = ""
    type = ""

    data = httptools.downloadpage(item.url).data
    it2 = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    itemlist.extend(servertools.find_video_items(data=data))
    
    for item in it2:
        if "###" not in item.url:
            item.url += "###" + id + ";" + type
    for videoitem in itemlist:
        videoitem.channel=item.channel
    return itemlist
    
