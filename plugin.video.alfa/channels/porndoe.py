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

canonical = {
             'channel': 'porndoe', 
             'host': config.get_setting("current_host", 'porndoe', default=''), 
             'host_alt': ["https://porndoe.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host +"videos"))
    itemlist.append(Item(channel=item.channel, title="Exclusivos" , action="lista", url=host + "category/74/premium-hd"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "videos?sort=views-down"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "videos?sort=likes-down"))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="lista", url=host + "videos?sort=duration-down"))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="categorias", url=host + "pornstars"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "channels?sort=ranking"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories?sort=name"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch?keywords=%s" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def has_class_but_no_id(tag):
    return not tag.has_attr('class_')
    
def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "channels" in item.url:
        match1 = soup.find('div', class_='channels-list').find_all('div', class_='channels-item-thumb')
        matches =[]
        for elem in match1:
            matches.append(elem.parent)
    if "categories" in item.url:
        matches = soup.find_all(href=re.compile(r"/category/"))
    if "pornstars" in item.url:
        matches = soup.find_all('div', class_='actors-list-item')

    for elem in matches:
        cantidad = ""
        title = ""
        if "categories" in item.url:
            url = elem['href']
            title = elem['title']
            cantidad = elem.find('span')
        else:
            if elem.find(href=re.compile(r"/channel-profile/")):
                url = elem.find(href=re.compile(r"/channel-profile/"))['href']
            else:
                url = elem.a['href']
            cantidad = elem.find('span', class_='-grow')
            title = elem.a['title']
        thumbnail  = elem.svg['data-src']
        if cantidad:
            cantidad = cantidad.text.strip().replace(" Videos", "").replace(" videos", "")
            title = "%s (%s)" % (title, cantidad)
        url = url.replace("channel-profile", "channel-profile-videos")
        if "categories" in item.url:
            url += "?sort=release"
        else:
            url += "?sort=date-down"
        url = url.replace("https://letsdoeit.com", "")
        url = urlparse.urljoin(item.url,url)
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = soup.find('a', class_='pager-next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)

        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='video-item')
    for elem in matches:
        # logger.error(elem)
        if "redirect" in elem.a['href']:
            continue
        url = elem.a['href']
        # id = elem.a['ng-pop-under']
        # url = "%svideo/%s" %(host,id)
        title = elem.find('a', class_='video-item-link')['aria-label']
        thumbnail = elem.svg['data-src']
        time = elem['data-duration']
        hd = elem['data-hd']
        vr = elem['data-vr']
        quality = ""
        if "true" in vr: quality = "VR"
        if "true" in hd: quality = "HD"
        url = urlparse.urljoin(host,url)
        thumbnail = urlparse.urljoin(host,thumbnail)
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                                fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='pager-next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url).find('div', class_='vpp-section')
    pornstars = soup.find_all('a', href=re.compile("/pornstars-profile/[A-z0-9-]+"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    plot = ""
    if len(pornstars) <= 3:
        lista = item.contentTitle.split()
        if "HD" in item.title:
            lista.insert (4, pornstar)
        else:
            lista.insert (2, pornstar)
        item.contentTitle = ' '.join(lista)
    else:
        plot = pornstar
    
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
