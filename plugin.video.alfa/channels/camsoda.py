# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import jsontools as json

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []

forced_proxy_opt = ''
timeout = 45

#### ImputStream FFmpeg

canonical = {
             'channel': 'camsoda', 
             'host': config.get_setting("current_host", 'camsoda', default=''), 
             'host_alt': ["https://www.camsoda.com/"], 
             'host_black_list': [], 
             'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'cf_assistant': False, 'CF_stat': True, 
             'CF': True, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# https://www.camsoda.com/api/v1/browse/react?p=2&gender-hide=m,t&perPage=98

def mainlist(item):
    logger.info()
    itemlist = []
    
    httptools.downloadpage(host, canonical=canonical, timeout=timeout).data
    
    itemlist.append(item.clone(title="Mujeres" , action="lista", url=host + "api/v1/browse/react/?gender-hide=c,m,t&p=1"))
    itemlist.append(item.clone(title="Hombres" , action="lista", url=host + "api/v1/browse/react/?gender-hide=c,f,t&p=1"))
    itemlist.append(item.clone(title="Couples" , action="lista", url=host + "api/v1/browse/react/?gender-hide=f,m,t&p=1"))
    itemlist.append(item.clone(title="Trans" , action="lista", url=host + "api/v1/browse/react/?gender-hide=c,m,F&p=1"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "api/v1/tags/index?page=1"))
    
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "%sapi/v1/browse/react/search/%s?p=1" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# https://www.camsoda.com/api/v1/browse/react/girls/tag/big-tits-cams?p=2&gender-hide=m,t&perPage=98

def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical, timeout=timeout).json
    for elem in data['tag_list']:
        name = elem['tag_slug']
        cantidad = elem['tag_count']
        title = "%s (%s)" %(name, cantidad)
        thumbnail = ""
        url = "%sapi/v1/browse/react/girls/tag/%s-cams?p=1" % (host,name)
        plot = "[COLOR yellow]%s[/COLOR]" %name
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot) )
    count= data['tag_count']
    current_page = scrapertools.find_single_match(item.url, ".*?page=(\d+)")
    current_page = int(current_page)
    if (current_page * 26) <= int(count) and (int(count) - (current_page*26)) > 26:
        current_page += 1
        next_page = re.sub(r"page=\d+", "page={0}".format(current_page), item.url)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical, timeout=timeout).json
    for elem in data['userList']:
        title = elem['username']
        is_on = elem['status']
        thumbnail = elem['thumbUrl']
        username = "guest_22596"
        url = "%sapi/v1/video/vtoken/%s?username=%s" % (host,title,username)
        if not "online" in is_on:
            title = "[COLOR red]%s[/COLOR]" % title
        if not thumbnail.startswith("https"):
            thumbnail = "https:%s" % thumbnail
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, contentTitle=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail))
    
    count= data['totalCount']
    current_page = scrapertools.find_single_match(item.url, ".*?p=(\d+)")
    current_page = int(current_page)
    if (current_page * 60) <= int(count) and (int(count) - (current_page*60)) > 60:
        current_page += 1
        next_page = re.sub(r"p=\d+", "p={0}".format(current_page), item.url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", contentTitle = item.contentTitle, url=item.url, server="camsoda" ))
    return itemlist