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

# CAM    https://www.asianpornmovies.com https://www.asspoint.com https://www.mobilepornmovies.com https://movieshark.com https://www.sexoasis.com    https://www.porngash.com 
# OUT https://www.porntitan.com    https://www.teenieporn.com 
# https://www.porntv.com        https://www.lesbianpornvideos.com/
# https://www.ghettotube.com       https://www.pinflix.com     https://www.youngpornvideos.com
# https://www.ebonygalore.com/     https://www.gotporn.com/    https://www.fuq.com/ 

canonical = {
             'channel': 'ghettotube', 
             'host': config.get_setting("current_host", 'ghettotube', default=''), 
             'host_alt': ["https://www.ebonygalore.com/"], 
             'host_black_list': ["https://www.ghettotube.com"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "search?filter[order_by]=date&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mas popular" , action="lista", url=host + "search?filter[order_by]=popular&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "search?filter[order_by]=rating&page=1"))
    itemlist.append(Item(channel=item.channel, title="Mas metraje" , action="lista", url=host + "search?filter[order_by]=duration&page=1"))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="catalogo", url=host + "pornstar/"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch/%s?filter[order_by]=date&page=1" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='category-group-container').find_all('li', class_="category")
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail = ""
        cantidad = elem.find('span')
        title = title.replace(cantidad.text.strip(), "")
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        url += "?filter[order_by]=date&page=1"
        plot = ""
        if not "/galleries/" in url:
            itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_="card")
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='absolute')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        url += "?filter[order_by]=date&page=1"
        plot = ""
        if not "/galleries/" in url:
            itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    itemlist.sort(key=lambda x: x.title)
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_="cards").find_all('div', class_="card")
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        time = elem.find('span', class_='inline-grid')
        web = elem.find('a', href=re.compile(r"/source/[A-z0-9-]+")).text.strip()
        if "HD" in time.text.strip() or "4K" in time.text.strip():
            if "4K" in time.text.strip():
                quality = "4K"
            else:
                quality = "HD"
            time = time.text.replace("HD", "").replace("4K", "").strip()
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] [%s] %s" % (time,quality,web,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] [%s] %s" % (time.text.strip(),web,title)
        url = urlparse.urljoin(item.url,url)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                                   plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', attrs={"aria-label": "Next Page"})
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = httptools.downloadpage(item.url).url
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = httptools.downloadpage(item.url).url
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

