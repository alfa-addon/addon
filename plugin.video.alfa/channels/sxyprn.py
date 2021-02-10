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

from channels import autoplay
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup
from lib import alfa_assistant

host = 'https://www.sxyprn.com'


list_language = []
list_servers = ['streamtape', 'Directo']
list_quality = []


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    check = ""
    if not alfa_assistant.open_alfa_assistant():
        check = "orange"

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/0.html?page=0&op", check=check))
    itemlist.append(item.clone(title="Mas vistos" , action="findvideos", url=host + "/0.html?sm=views&page=0&op", check=check))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/0.html?sm=trending&page=0&op", check=check))
    itemlist.append(item.clone(title="Sitios" , action="catalogo", url=host + "?op", check=check))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "?op", check=check))
    itemlist.append(item.clone(title="Buscar...", action="search", op=True, check=check))

    itemlist.append(item.clone(title="", folder=0))
    itemlist.append(item.clone(title="[COLOR %s]Con Assistant[/COLOR]" %check , action="submenu", check=check))
    
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="[COLOR %s]Nuevos[/COLOR]" %item.check, action="lista", url=host + "/0.html?page=0"))
    itemlist.append(item.clone(title="[COLOR %s]Mas vistos[/COLOR]" %item.check, action="findvideos", url=host + "/0.html?page=0&sm=views"))
    itemlist.append(item.clone(title="[COLOR %s]Mejor valorada[/COLOR]" %item.check, action="lista", url=host + "/0.html?page=0&sm=trending"))
    itemlist.append(item.clone(title="[COLOR %s]Sitios[/COLOR]" %item.check, action="catalogo", url=host))
    itemlist.append(item.clone(title="[COLOR %s]Categorias[/COLOR]" %item.check, action="categorias", url=host))
    itemlist.append(item.clone(title="[COLOR %s]Buscar[/COLOR]" %item.check, action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = host + "/%s.html?page=0" % texto
    if item.op:
        item.url += "&op"

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
    matches = soup.find_all('div', class_='htag_el')
    for elem in matches:
        url = elem.parent['href'].replace("trending", "latest")
        title = elem.find('span', class_='htag_el_tag').text.strip().replace("#", "")
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='htag_el_count').text.strip()
        title = "%s (%s)" %(title, cantidad)
        thumbnail = "https:" + thumbnail
        url = urlparse.urljoin(item.url,url)
        if "op" in item.url:
            url += "?page=0&op"
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail ) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='top_sub_el_sc')
    for elem in matches:
        url = elem.parent['href'].replace("trending", "latest")
        title = elem.find('span', class_='top_sub_el_key_sc').text.strip()
        cantidad = elem.find('span', class_='top_sub_el_count').text.strip()
        title = "%s (%s)" %(title, cantidad)
        thumbnail = ""
        url = urlparse.urljoin(item.url,url)
        if "op" in item.url:
            url += "?page=0&op"
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail ) )
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
    matches = soup.find_all('div', class_='post_el_small')
    for elem in matches:
        ext = ""
        time = ""
        quality = ""
        serv = ['jetload','evoload', 'waaw', 'aparat.cam/reg']
        url = elem.find('a', class_='post_time')['href']
        titulo = elem.find('a', class_='post_time')['title']
        thumbnail = elem.img
        if thumbnail: 
            thumbnail = thumbnail['src']
            if "removed.png" in thumbnail: thumbnail = urlparse.urljoin(item.url,thumbnail)
        titulo = re.sub("#\w+", "", titulo).strip()
        title = scrapertools.find_single_match(titulo, '(.*?)https')
        if not title:
            title = titulo.replace("Visit Hornyfanz.com ", "")
        if thumbnail and not "removed.png" in thumbnail:
            time = elem.find('span', class_='duration_small').text.strip()
            quality = elem.find('span', class_='shd_small')
            if not thumbnail.startswith("https"):
                thumbnail = "https:%s" % thumbnail
        if not "EXTERNAL LINK" in time and item.check:
            title = "[COLOR %s]%s[/COLOR]" % (item.check, title)
        if "EXTERNAL LINK" in time:
            time = ""
            ext = True
            ext1 = elem.find_all('a', class_='extlink')
            ext2 =[elem['href'] for elem in ext1]
            col = [a for a in serv for b in ext2 if a in b]
            if len(col) and len(ext1) <= 1:
                title = " [COLOR red]%s[/COLOR]" % title
        if quality:
            quality = quality.text.strip()
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time, quality, title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time, title)
        url = urlparse.urljoin(item.url,url)
        itemlist.append(item.clone(action="findvideos", title=title, url=url, contentTitle = title,
                          thumbnail=thumbnail, fanart=thumbnail, ext=ext))
    next_page = soup.find('div', class_='next_page')
    if next_page:
        next_page = next_page.parent['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def asist(url):
    logger.info()
    # itemlist = []
    alfa_assistant.open_alfa_assistant()
    data = alfa_assistant.get_source_by_page_finished(url, 4, closeAfter=True)
    for visited in  data["urlsVisited"]:
        if "/cdn8/" in visited["url"]:
            url = visited["url"]
            url = httptools.downloadpage(url, follow_redirects=False).headers["location"]
            if not url.startswith("https"):
                url = "https:%s" % url
            # itemlist.append(item.clone(action="play",title="%s", url=url))
    # itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return url


def findvideos(item):
    logger.info()
    itemlist = []
    logger.debug("ITEM: %s" % item)
    video_urls = []
    soup = create_soup(item.url)
    if item.ext:
        matches = soup.find_all('a', class_='extlink')
        for elem in matches:
            url = elem['href']
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    else:
        url = soup.find(class_='vidsnfo')['data-vnfo'].split(':')[1]
        url= url.replace("\\", "").replace("/cdn/", "https://www.sxyprn.com/cdn8/").replace("}", "")
        if alfa_assistant.open_alfa_assistant():
            itemlist.append(item.clone(action="play", title="Directo", server="Directo", contentTitle = item.title, url= asist(item.url) ))
        else:
            itemlist.append(item.clone(action="play", title="[COLOR red]Directo[/COLOR]", contentTitle = item.title, url=url ))
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

