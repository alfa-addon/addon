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
from channels import autoplay

host = "http://mundiseries.com"
list_servers = ['okru']
list_quality = ['default']
                
def mainlist(item):
    logger.info()
    itemlist = list()
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, action="lista", title="Series", url=urlparse.urljoin(host, "/lista-de-series")))
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)"><img src="([^"]+)" alt="ver ([^"]+) online'
    matches = scrapertools.find_multiple_matches(data, patron)
    for link, thumbnail, name in matches:
        itemlist.append(item.clone(title=name, url=host+link, thumbnail=host+thumbnail, action="temporada"))
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
        itemlist.append(item.clone(title=name, url=host+link, thumbnail=host+thumbnail,action="episodios",context=autoplay.context))
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron_caps = 'href="http:.+?\/mundiseries.+?com([^"]+)" alt="([^"]+) Capitulo ([^"]+) Temporada ([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_show='<h1 class="h-responsive center">.+?'
    patron_show+='<font color=".+?>([^"]+)<\/a><\/font>'
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
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir Temporada/Serie a la biblioteca de Kodi[/COLOR]", url=item.url,
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
        videoitem.channel= item.channel
    autoplay.start(itemlist, item)
    return itemlist
