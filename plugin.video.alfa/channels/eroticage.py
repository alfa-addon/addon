# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re
from bs4 import BeautifulSoup

from platformcode import config, logger
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from channels import filtertools
from channels import autoplay


IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['pornhub']

host = 'https://www.erogarga.com'       # http://www.eroticage.net


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Novedades" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Mas Popular" , action="lista", url=host + "/?filter=popular"))
    itemlist.append(item.clone(title="Mas Visto" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mas Largo" , action="lista", url=host + "/?filter=longest"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host, texto)
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
    matches = soup.find('div', class_='tagcloud').find_all('a', class_='tag-cloud-link')
    for elem in matches:
        url = elem['href']
        title = elem.text
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail="", plot="") )
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
    soup = create_soup(item.url).find('main', id='main')
    matches = soup.find_all('article', class_='thumb-block')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['data-src']
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='responsive-player')
    for elem in matches:
        url = elem.iframe['src']
        if "spankbang" in url:
            data = httptools.downloadpage(url).data
            skey = scrapertools.find_single_match(data,'data-streamkey="([^"]+)"')
            session="523034c1c1fc14aabde7335e4f9d9006b0b1e4984bf919d1381316adef299d1e"
            post = {"id": skey, "data": 0}
            headers = {'Referer':item.url}
            url ="https://es.spankbang.com/api/videos/stream"
            data = httptools.downloadpage(url, post=post, headers=headers).data
            patron = '"(\d+(?:p|k))":\["([^"]+)"'
            matches = re.compile(patron,re.DOTALL).findall(data)
            for quality,url in matches:
                itemlist.append(['.mp4 %s' %quality, url])
            return itemlist
        if "cine-matik.com" in url:
            n = "yandex"
            m = url.replace("https://cine-matik.com/player/play.php?", "")
            post = "%s&alternative=%s" %(m,n)
            headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
            data1 = httptools.downloadpage("https://cine-matik.com/player/ajax_sources.php", post=post, headers=headers).data
            if data1=="":
                n = "blogger"
                m = url.replace("https://cine-matik.com/player/play.php?", "")
                post = "%s&alternative=%s" %(m,n)
                headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                data1 = httptools.downloadpage("https://cine-matik.com/player/ajax_sources.php", post=post, headers=headers).data
            url = scrapertools.find_single_match(data1,'"file":"([^"]+)"')
            if not url:
                n = scrapertools.find_single_match(data1,'"alternative":"([^"]+)"')
                post = "%s&alternative=%s" %(m,n)
                headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                data1 = httptools.downloadpage("https://cine-matik.com/player/ajax_sources.php", post=post, headers=headers).data
                url = scrapertools.find_single_match(data1,'"file":"([^"]+)"')
            url = url.replace("\/", "/")
        if not "meta" in url:
            itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
