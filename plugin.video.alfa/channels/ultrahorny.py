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
import requests

host = 'https://ultrahorny.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    # itemlist.append(item.clone(title="Pornstars" , action="categorias", url=host + "/pornstar/?filter=popular"))  #no tiene contenido
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s//?s=%s" % (host,texto)
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
    soup = create_soup(item.url).find('ul', class_='lst_categorias') 
    matches = soup.find_all('li')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.img['src']
        title = elem.find('h5')
        if title:
            title = title.text.strip()
        else:
            title = elem.find('h3').text.strip() #para pornstars
        cantidad = elem.find('div', class_='float-right')
        if cantidad:
            cantidad = cantidad.text.strip()
            title = "%s (%s)" % (title,cantidad)
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
    if "/?s=" in item.url or "/channel/" in item.url:
        soup = create_soup(item.url)
    else:
        soup = create_soup(item.url)  #.find("div", id="widget_post-2")
    matches = soup.find_all('div', class_='item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-original']
        time = elem.find('div', class_='duration')
        quality = elem.find('span', class_='is-hd')
        title 
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time.text, title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text, title)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a
        if next_page:
            next_page = next_page['href']
            next_page = urlparse.urljoin(item.url,next_page)
            itemlist.append(item.clone(action="lista", title=next_page, url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
    directo_result = httptools.downloadpage(url)
    directo_result = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", directo_result.data)
    metadata_url = scrapertools.find_single_match(directo_result, '"videoUrl":\"([^"]+)\"')
    metadata_server = scrapertools.find_single_match(directo_result, '"videoServer":\"([^"]+)\"')
    metadata_url = re.sub(r'\\', "", metadata_url)
    metadata_url = "https://htstreaming.com%s?s=%s&d=" %(metadata_url, metadata_server)
    metadata = requests.get(metadata_url, headers={"Referer": url}).content
    # metadata = httptools.downloadpage(metadata_url, headers={"referer": url}).data
    patron = "RESOLUTION=(.*?)http([^#]+)"
    video_matches = re.compile(patron, re.DOTALL).findall(metadata)
    for video_resolution, video_url in video_matches:
        final_url = "http" + video_url.strip()
        url_video = final_url + "|referer=%s" % url
        logger.info(final_url)
        itemlist.append(Item(channel=item.channel, title='%s (' + video_resolution.strip() + ')', url=url_video, action='play'))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    return itemlist


# def play(item):
    # logger.info()
    # itemlist = []
    # soup = create_soup(item.url)
    # matches = soup.find_all('div', class_='cnt_post video_cnt')
    # for elem in matches:
        # url = elem.iframe['src']
        # if "pornoflix" in url:
            # url = create_soup(url).find('source')['src']
        # itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    # itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # return itemlist

