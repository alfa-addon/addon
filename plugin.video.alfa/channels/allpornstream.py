# -*- coding: utf-8 -*-
# -*- Channel allpornstream -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
#------------------------------------------------------------

import re

from core import urlparse
from platformcode import config, logger,unify
from core import scrapertools

from core.item import Item
from core import servertools, channeltools
from core import httptools
from bs4 import BeautifulSoup
from core.jsontools import json

UNIFY_PRESET = config.get_setting("preset_style", default="Inicial")
color = unify.colors_file[UNIFY_PRESET]

list_quality = ['default']
list_servers = ['']

### https://allpornstream.com/   https://dayporner.com/  https://pornstellar.com/   https://sex-scenes.com/
### https://scenesxxx.com/   https://freepornfun.com/   https://redtubevids.com/  https://pornapes.com/

##############    FALTA DIVIDIR EN PAG categorias

 
#                       https://diepornos.com/


canonical = {
             'channel': 'allpornstream', 
             'host': config.get_setting("current_host", 'allpornstream', default=''), 
             'host_alt': ["https://allpornstream.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "api/posts?page=1" ))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "api/posts?sort=views&page=1" ))
    itemlist.append(Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "api/posts?sort=rating&page=1" ))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "api/table-list?type=producers", extra="producer" ))
    itemlist.append(Item(channel=item.channel, title="Pornstar" , action="categorias", url=host + "api/table-list?type=actors", extra="actor" ))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "api/table-list?type=categories", extra="category" ))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%sapi/posts?search=%s&page=1" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    
    data_json = httptools.downloadpage(item.url).json
    
    
    for elem in data_json:
        # logger.debug(elem)
        cantidad = ""
        cantidad = elem['count']
        title = elem['%s' %item.extra] 
        slug = title.replace(" ", "-")
        if "producer" in item.extra:
            url = "%sapi/posts?studio=%s&page=1" %(host,slug)
        else:
            url = "%sapi/posts?%s=%s&page=1" %(host,item.extra,slug)
        if elem['thumbs_urls']:
            thumbnail = elem['thumbs_urls'][-1]
        else:
            thumbnail = ""
        if cantidad:
            title = "%s (%s)" %(title,cantidad)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             thumbnail=thumbnail , plot=plot) )
    if "category" in item.extra:
        itemlist.sort(key=lambda x: x.title)
        
    # cantidad = int(len(data_json))
    # lastpage = cantidad/30
    # if lastpage - int(lastpage) > 0:
        # lastpage = int(lastpage) + 1
    
    # logger.debug(lastpage)
    
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data_json = httptools.downloadpage(item.url).json
    for elem in data_json['posts']:
        id = elem['id']
        title = elem['video_title']
        slug = elem['slug']
        thumbnail = elem['image_details'][-1]
        canal = ""
        if elem['producers']:
            canal = elem['producers'][0]
            if canal in title: title = title.split("]")[-1]
            canal = "[COLOR %s][%s][/COLOR]" % (color.get('tvshow',''),canal)
        if elem['actors']:
            actors = elem['actors']
            pornstar = ' & '.join(actors)
            pornstar = "[COLOR %s] %s[/COLOR]" % (color.get('rating_3',''),pornstar)
            for elem in actors:
                title = title.replace(elem, "")
            title = title.replace(" ,,,, ", "").replace(" ,,, ", "").replace(" ,, ", "").replace(", ", "")
        title = "%s %s %s" %(canal,pornstar,title)
        url = "%spost/%s/a" %(host, id)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    
    postsNumber = data_json['count']
    lastpage = postsNumber/58
    if lastpage - int(lastpage) > 0:
        lastpage = int(lastpage) + 1
    page = int(scrapertools.find_single_match(item.url, 'page=(\d+)'))
    if page < lastpage:
        title="[COLOR blue]Página %s de %s[/COLOR]" %(page,lastpage)
        page += 1
        next_page = re.sub(r"page=\d+", "page={0}".format(page), item.url)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\\"', '"', data)
    url = scrapertools.find_single_match(data, '"embed_url":"([^"]+)"')
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\\"', '"', data)
    url = scrapertools.find_single_match(data, '"embed_url":"([^"]+)"')
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist