# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

#  https://es.chaturbate.com       https://www.queentits.com   https://www.sluts.xyz/
canonical = {
             'channel': 'chaturbate', 
             'host': config.get_setting("current_host", 'chaturbate', default=''), 
             'host_alt': ["https://chaturbate.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# https://chaturbate.com/api/ts/roomlist/room-list/?enable_recommendations=false&genders=f&limit=90&offset=90
# https://chaturbate.com/api/ts/hashtags/top_tags/?genders=s
# https://chaturbate.com/api/ts/hashtags/tag-table-data/?sort=&page=1&g=f&limit=100

def mainlist(item):
    logger.info()
    itemlist = []
    httptools.downloadpage(host, canonical=canonical).data
    url_api= "%sapi/ts/roomlist/room-list/?enable_recommendations=false&genders=%s&limit=90&offset=0"
    
    itemlist.append(Item(channel = item.channel, title="Mujeres" , action="lista", url=url_api %(host, "f")))
    itemlist.append(Item(channel = item.channel, title="Hombres" , action="lista", url=url_api %(host, "m")))
    itemlist.append(Item(channel = item.channel, title="Parejas" , action="lista", url=url_api %(host, "c")))
    itemlist.append(Item(channel = item.channel, title="Trans" , action="lista", url=url_api %(host, "t")))
    itemlist.append(Item(channel = item.channel, title="Categorias" , action="submenu"))
    return itemlist

def submenu(item):
    logger.info()
    itemlist = []
    url_tag = "%sapi/ts/hashtags/top_tags/?genders=%s"
    itemlist.append(Item(channel = item.channel, title="Mujeres" , action="categorias", url=url_tag %(host, "f"), type="f"))
    itemlist.append(Item(channel = item.channel, title="Hombres" , action="categorias", url=url_tag %(host, "m"), type="m"))
    itemlist.append(Item(channel = item.channel, title="Parejas" , action="categorias", url=url_tag %(host, "c"), type="c"))
    itemlist.append(Item(channel = item.channel, title="Trans" , action="categorias", url=url_tag %(host, "s"), type="t"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%ssearch/%s/" % (host,texto)
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
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for elem in data['all_tags']:
        title = elem
        url = "%sapi/ts/roomlist/room-list/?enable_recommendations=false&genders=%s&hashtags=%s&limit=90&offset=0" %(host, item.type, elem)
        thumbnail = ""
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    itemlist.sort(key=lambda x: x.title)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for elem in data['rooms']:
        title = elem['username']
        url = urlparse.urljoin(host,title)
        age = elem['display_age']
        thumbnail = elem['img']
        if age:
            title = "%s (%s)" % (title,age)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    total = data['total_count']
    page = int(scrapertools.find_single_match(item.url, '&offset=([0-9]+)'))
    next_page = (page+ 90)
    if next_page < int(total):
        next_page = re.sub(r"&offset=\d+", "&offset={0}".format(next_page), item.url)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace("\\u0022" , '"').replace("\\u002D", "-")
    url = scrapertools.find_single_match(data, '"hls_source"\: "([^"]+)"')
    itemlist.append(Item(channel = item.channel, action="play", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = data.replace("\\u0022" , '"').replace("\\u002D", "-")
    url = scrapertools.find_single_match(data, '"hls_source"\: "([^"]+)"')
    itemlist.append(Item(channel = item.channel, action="play", url=url, contentTitle=item.contentTitle))
    return itemlist