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
from core import jsontools as json

canonical = {
             'channel': 'fantasticc', 
             'host': config.get_setting("current_host", 'fantasticc', default=''), 
             'host_alt': ["https://fantasti.cc"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []

    # itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/videos/upcoming/")) #pagina no carga
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/videos/popular/today/"))

    itemlist.append(Item(channel=item.channel, title="Upload" , action="lista", url=host + "/category/upload/tube/date/"))
    itemlist.append(Item(channel=item.channel, title="Upload popular" , action="lista", url=host + "/category/upload/tube/popular/"))
    itemlist.append(Item(channel=item.channel, title="Upload mas visto" , action="lista", url=host + "/category/upload/tube/views/"))
    itemlist.append(Item(channel=item.channel, title="Upload mas largo" , action="lista", url=host + "/category/upload/tube/length/"))

    itemlist.append(Item(channel=item.channel, title="Comunity" , action="lista", url=host + "/category/community/community/date/"))
    itemlist.append(Item(channel=item.channel, title="Comunity tube" , action="lista", url=host + "/category/community/tube/date/"))
    itemlist.append(Item(channel=item.channel, title="Comunity tube popular" , action="lista", url=host + "/category/community/tube/popular/"))
    itemlist.append(Item(channel=item.channel, title="Comunity tube mas visto" , action="lista", url=host + "/category/community/tube/views/"))
    itemlist.append(Item(channel=item.channel, title="Comunity tube mas largo" , action="lista", url=host + "/category/community/tube/length/"))
    itemlist.append(Item(channel=item.channel, title="Comunity pro" , action="lista", url=host + "/category/community/pro/date/"))

    itemlist.append(Item(channel=item.channel, title="Collections trending" , action="collections", url=host + "/videos/collections/trending/31days/page_1"))
    itemlist.append(Item(channel=item.channel, title="Collections popular" , action="collections", url=host + "/videos/collections/popular/31days/page_1"))
    itemlist.append(Item(channel=item.channel, title="Collections mas visto" , action="collections", url=host + "/videos/collections/most-viewed/all_time/page_1"))
    itemlist.append(Item(channel=item.channel, title="Collections Categorias" , action="categorias", url=host + "/category/"))

    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/category/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
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
    matches = soup.find_all('div', class_='content-block-category')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('span', class_='category-name').text.strip()
        thumbnail = elem.div['data-src']
        url = urlparse.urljoin(item.url,url)
        if "Collections" in item.title:
            url = "%scollections/" %url
            action="collections"
        else:
            url = "%stube/" %url
            action="lista"
        plot = ""
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    return itemlist


def collections(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='submitted-videos')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        cantidad = elem.find('span', class_='videosListNumber')
        yesPopunder = elem.find('a', class_='yesPopunder')
        thumbnail = ""
        if yesPopunder:
            thumbnail= yesPopunder['style']
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        thumbnail = scrapertools.find_single_match(thumbnail, "(http.*?.jpg)")
        if not yesPopunder:
            title = "[COLOR red]%s[/COLOR]" % title
            thumbnail = ""
        plot = ""
        itemlist.append(Item(channel=item.channel, action="listaco", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('span', class_="this_page").find_next_sibling('a')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def listaco(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    djson = scrapertools.find_single_match(data,'videosJSON = (\[.*?\]);')
    JSONData = json.load(djson)
    for Video in  JSONData:
        title = Video["title"]
        thumbnail = Video["rawThumb"]
        url = Video["url"]
        url = urlparse.urljoin(item.url,url)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url,
                          thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url, timeout=30).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "category" in item.url or "search" in item.url:
        matches = soup.find_all('div', class_='searchVideo')
    else:
        matches = soup.find_all('div', id=re.compile(r"^post_\d+"))
    for elem in matches:
        url = elem.a['href']
        if elem.img.get("alt", ""):
            title = elem.img['alt']
        else:
            title = elem.text.strip()
        thumbnail = elem.img['src']
        url = urlparse.urljoin(item.url,url)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('span', class_="this_page").find_next_sibling('a')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find('iframe')['src']
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find('iframe')['src']
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
