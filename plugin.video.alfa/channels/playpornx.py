# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import urlparse
from bs4 import BeautifulSoup
from modules import autoplay

list_quality = ['default']
list_servers = []

# https://playpornfree.org/   https://streamporn.pw/  https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/
# pandamovie https://watchpornfree.info  https://xxxparodyhd.net  http://www.veporns.com  http://streamporno.eu
# https://www.netflixporno.net   https://xxxscenes.net   https://mangoporn.net   https://speedporn.net

canonical = {
             'channel': 'playpornx', 
             'host': config.get_setting("current_host", 'playpornx', default=''), 
             'host_alt': ["https://watchfreexxx.net/"], 
             'host_black_list': [], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*hreflang="?en"?'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Escenas" , action="submenu", url=host + "xxxporn/"))
    
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "?filter=latest"))
    itemlist.append(Item(channel=item.channel, title="Mas visto" , action="lista", url=host + "?filter=most-viewed"))
    itemlist.append(Item(channel=item.channel, title="Popular" , action="lista", url=host + "?filter=popular"))
    itemlist.append(Item(channel=item.channel, title="Mas Largo" , action="lista", url=host + "?filter=longest"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=host + "pornstars/"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="canal", url=host + "studios/"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "genres/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=item.url + "?filter=latest"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=item.url + "?filter=most-viewed"))
    itemlist.append(Item(channel=item.channel, title="Mas valorados" , action="lista", url=item.url + "?filter=popular"))
    itemlist.append(Item(channel=item.channel, title="Mas Largo" , action="lista", url=item.url + "?filter=longest"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="categorias", url=item.url + "pornstars/"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=item.url + "studios/"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "genres/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=item.url))
    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s?s=%s&filter=latest" % (item.url,texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def canal(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='tag-item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='video-block')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title'].replace("&nbsp;", "" )
        thumbnail = elem.img['src'].replace("amp;", "")
        if "svg" in thumbnail and elem.img.get('data-lazy-src', ''):
            thumbnail = elem.img['data-lazy-src'].replace("amp;", "")
        elif elem.img.get('data-src', ''):
            thumbnail = elem.img['data-src'].replace("amp;", "")
        cantidad = elem.find(class_='video-datas')
        if cantidad:
            title = "%s (%s)" %(title, cantidad.text.strip())
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
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
    matches = soup.find_all('div', class_='video-block')
    for elem in matches:
        thumbnail = ""
        url = elem.a['href']
        title = elem.find(class_='title').text.strip()
        thumbnail = elem.img['src'].replace("amp;", "")
        if "svg" in thumbnail and elem.img.get('data-lazy-src', ''):
            thumbnail = elem.img['data-lazy-src'].replace("amp;", "")
        elif elem.img.get('data-src', ''):
            thumbnail = elem.img['data-src'].replace("amp;", "")
        time = elem.find(class_='duration')
        if time:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text.strip(),title)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    video_urls = []
    soup = create_soup(item.url)
    pornstars = soup.find('div', id='video-actors').find_all('a', href=re.compile("/(:?pornstar|pornstars)/"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    if "N/A" not in pornstar:
        pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    else:
        pornstar = ""
    plot = pornstar
    
    matches = soup.find('div', id='pettabs').find_all('a')
    for elem in matches:
        url = elem['href']
        if url not in video_urls:
            video_urls += url
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play', language='VO',contentTitle = item.contentTitle, plot=plot))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

