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

forced_proxy_opt = 'ProxySSL'
timeout = 45

canonical = {
             'channel': 'spankbang', 
             'host': config.get_setting("current_host", 'spankbang', default=''), 
             'host_alt': ["https://es.spankbang.com/"], 
             'host_black_list': [], 
             'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 4, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             # 'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos", action="lista", url= host + "new_videos/1/"))
    itemlist.append(Item(channel=item.channel, title="Mas valorados", action="lista", url=host + "trending_videos/"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos", action="lista", url= host + "most_popular/"))
    itemlist.append(Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "pornstars"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "channels/1?o=top"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "tags"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ss/%s/?o=new" % (host, texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('main', id='container')
    matches = soup.find_all('a', class_='image')
    for elem in matches:
        url = elem['href']
        title = elem.img['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='videos')
        if cantidad:
            title = "%s (%s)" %(title, cantidad.text)
        url =  urlparse.urljoin(host,url)
        url += "?o=new"
        thumbnail =  urlparse.urljoin(host,thumbnail)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title , url=url , 
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('ul', class_='list')
    matches = soup.find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text
        thumbnail = ""
        url =  urlparse.urljoin(item.url,url)
        url += "?o=new"
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title , url=url , 
                             fanart=thumbnail, thumbnail=thumbnail, plot=plot) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, timeout=timeout, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=timeout, canonical=canonical).data
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='results')
    matches = soup.find_all('div', id=re.compile(r"^v_id_\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='l')
        quality = elem.find('span', class_='h')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time.text,quality.text,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text,title)
        url =  urlparse.urljoin(item.url,url)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

