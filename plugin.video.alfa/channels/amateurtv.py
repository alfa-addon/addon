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
from core import jsontools as json

host = 'https://www.amateur.tv'
hosta = 'https://www.amateur.tv/v3/readmodel/cache/cams/%s/0/50/es'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=hosta %"a"))
    itemlist.append(item.clone(title="Mujer" , action="lista", url=hosta %"w"))
    itemlist.append(item.clone(title="Parejas" , action="lista", url=hosta %"c"))
    itemlist.append(item.clone(title="Hombres" , action="lista", url=hosta %"m"))
    itemlist.append(item.clone(title="Trans" , action="lista", url=hosta %"t"))
    itemlist.append(item.clone(title="Privado" , action="lista", url=hosta %"p"))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    data = data['cams']
    for elem in data['nodes']:
        # logger.debug(elem)
        id = elem['id']
        is_on = elem['online']
        thumbnail = elem['imageURL']
        country  = elem['country']
        name = elem['user']['username']
        age = elem['user']['age']
        quality = elem['hd']
        title = "%s %s %s" %(name, age, country)
        if not is_on:
            title= "[COLOR red] %s[/COLOR]" % title
        # if quality:
            # title = "[COLOR red]HD[/COLOR] %s" % title
        url = "https://www.amateur.tv/v3/readmodel/show/%s/es" %name
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                                   plot=plot, fanart=thumbnail, contentTitle=title ))
    count= data['totalCount']
    current_page = scrapertools.find_single_match(item.url, ".*?/(\d+)/50/")
    current_page = int(current_page)
    if current_page <= int(count) and (int(count) - current_page) > 50:
        current_page += 50
        next_page = re.sub(r"\d+/50/", "{0}/50/".format(current_page), item.url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    url = data['videoTechnologies']['fmp4']
    url += "|verifypeer=false"
    itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    url = data['videoTechnologies']['fmp4']
    url += "|verifypeer=false"
    itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    return itemlist

