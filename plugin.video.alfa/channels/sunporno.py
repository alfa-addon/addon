# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

# https://sextubefun.com/  https://iporntoo.com/  https://wanktv.com/  https://www.sunporno.com/   https://freehdporn.xxx/


##############   Response code: 404    a la segunda entra

canonical = {
             'channel': 'sunporno', 
             'host': config.get_setting("current_host", 'sunporno', default=''), 
             'host_alt': ["https://www.sunporno.com/"], 
             'host_black_list': [], 
             'pattern': ['toplogo" href="?([^"|\s*]+)["|\s*]'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 4, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevas" , action="lista", url=host +"s/?q=&sort_by=post_date&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Popular" , action="lista", url=host + "s/?q=&sort_by=video_viewed&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "s/?q=&sort_by=rating&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Mas favoritas" , action="lista", url=host + "s/?q=&sort_by=most_favourited&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Mas comentada" , action="lista", url=host + "s/?q=&sort_by=most_commented&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="Mas largas" , action="lista", url=host + "s/?q=&sort_by=duration&from_videos=1"))
    itemlist.append(Item(channel=item.channel, title="PornStars" , action="categorias", url=host + "pornstars/?sort_by=model_viewed&from=1"))
    # itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "tags/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ss/?q=%s&sort_by=post_date&from_videos=1" % (host, texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='item')
    for elem in matches:
        if not elem.find('img'):
            continue
        url = elem.a['href']
        title = elem.a['title']
        if elem.img.get("src", ""):
            thumbnail = elem.img['src']
        if "px_4_3.png" in thumbnail:
            thumbnail = elem.img['data-src']
        cantidad = elem.find('div', class_='model-info-videos')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url += "?sort_by=post_date&from=1"
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page.find('a'):
        next_page = next_page.a['data-parameters'].split(":")[-1]
        if "from_videos" in item.url:
            next_page = re.sub(r"&from_videos=\d+", "&from_videos={0}".format(next_page), item.url)
        else:
            next_page = re.sub(r"&from=\d+", "&from={0}".format(next_page), item.url)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, timeout=timeout, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=timeout, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('a', class_='item')
    for elem in matches:
        url = elem['href']
        title = elem['title']
        if elem.img.get("src", ""):
            thumbnail = elem.img['src']
        if "px_4_3.png" in thumbnail:
            thumbnail = elem.img['data-src']
        time = elem.find('div', class_='duration').text.strip()
        quality = elem.find('i', class_='icon-hd')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page and next_page.find('a'):
        next_page = next_page.a['data-parameters'].split(":")[-1]
        if "from_videos" in item.url:
            next_page = re.sub(r"&from_videos=\d+", "&from_videos={0}".format(next_page), item.url)
        else:
            next_page = re.sub(r"&from=\d+", "&from={0}".format(next_page), item.url)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    pornstars = soup.find_all('a', class_='tag-pornstar')
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR orange]%s[/COLOR]" % (pornstar)
    lista = item.title.split()
    if "HD" in item.title:
        lista.insert (4, pornstar)
    else:
        lista.insert (2, pornstar)
    item.contentTitle = ' '.join(lista)
    itemlist.append(Item(channel=item.channel, action="play", title= "%s" , contentTitle=item.contentTitle, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist
