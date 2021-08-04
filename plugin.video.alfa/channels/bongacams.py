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

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []

host = 'https://en.bongacams.com'
hosta = "https://es.bongacams.com/tools/listing_v3.php?livetab=%s&online_only=true&offset=0&can_pin_models=true&limit=40"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Female" , action="lista", url=hosta %"female"))
    itemlist.append(item.clone(title="Couples" , action="lista", url=hosta % "couples"))
    itemlist.append(item.clone(title="Male" , action="lista", url=hosta % "male"))
    itemlist.append(item.clone(title="Transexual" , action="lista", url=hosta % "/transsexual"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host,texto)
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
    soup = create_soup(item.url)
    matches = soup.find_all('li', class_='hbd_item')
    for elem in matches:
        cat = elem.a['href'].replace("/", "")
        cantidad = elem.find('span', class_='hbd_s_live')
        if cantidad:
            title = "%s %s" % (cat,cantidad.text.strip())
        url = "https://es.bongacams.com/tools/listing_v3.php?livetab=%s&online_only=true&offset=0&can_pin_models=true&category=%s&limit=40" %("female", cat)
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    headers={'X-Requested-With' : 'XMLHttpRequest'}
    data = httptools.downloadpage(item.url, headers=headers).json
    for elem in data['models']:
        thumbnail = elem['thumb_image'].replace("{ext}", "webp")
        title = elem['username']
        name = elem['display_name']
        thumbnail = "https:%s" % thumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
                               
    count= data['online_count']
    current_page = scrapertools.find_single_match(item.url, ".*?&offset=(\d+)")
    current_page = int(current_page)
    if current_page <= int(count) and (int(count) - current_page) > 40:
        current_page += 40
        next_page = re.sub(r"&offset=\d+", "&offset={0}".format(current_page), item.url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url="http://bongacams.com/tools/amf.php"
    post = {'method' : 'getRoomData', 'args[]' : 'false', 'args[]' : item.title}
    headers={'X-Requested-With' : 'XMLHttpRequest'}
    data = httptools.downloadpage(url, post=post, headers=headers).json
    url = data['localData']['videoServerUrl']
    if url.startswith("//mobile"):
       videourl = 'https:' + url + '/hls/stream_' + item.title + '.m3u8'
    else:
       videourl = 'https:' + url + '/hls/stream_' + item.title + '/playlist.m3u8'
    itemlist.append(item.clone(action="play", title=videourl, contentTitle = item.title, url=videourl, server="Directo" ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url="http://bongacams.com/tools/amf.php"
    post = {'method' : 'getRoomData', 'args[]' : 'false', 'args[]' : item.title}
    headers={'X-Requested-With' : 'XMLHttpRequest'}
    data = httptools.downloadpage(url, post=post, headers=headers).json
    url = data['localData']['videoServerUrl']
    if url.startswith("//mobile"):
       videourl = 'https:' + url + '/hls/stream_' + item.title + '.m3u8'
    else:
       videourl = 'https:' + url + '/hls/stream_' + item.title + '/playlist.m3u8'
    itemlist.append(item.clone(action="play", title=videourl, contentTitle = item.title, url=videourl, server="Directo" ))
    return itemlist