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

canonical = {
             'channel': 'pornmz', 
             'host': config.get_setting("current_host", 'pornmz', default=''), 
             'host_alt': ["https://pornmz.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "?filter=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "?filter=most-viewed"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "?filter=popular"))
    itemlist.append(item.clone(title="Mas metraje" , action="lista", url=host + "?filter=longest"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "actors"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (host,texto)
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
    soup = create_soup(item.url).find('nav', id='site-navigation')
    matches = soup.find_all('a', href=re.compile(r"^%spmvideo/(?:s|c)/\w+" %host))
    for elem in matches:
        url = elem['href']
        title = elem.text
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url) 
    matches = soup.find_all('article',id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img
        if thumbnail:
            thumbnail = thumbnail['src']
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('article',id=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img
        if thumbnail:
            thumbnail = thumbnail['src']
        else:
            thumbnail = elem.video['poster']
        stime = elem.find('span', class_='duration')
        actors = elem['class']
        actriz = ""
        for x in actors:
            if "actors-" not in x:
                continue
            actor = x.replace("actors-", "").replace("-", " ")
            actriz += "%s, " %actor
        if actriz:
            title = "(%s) %s" %(actriz[:-2], title)
        if stime:
            stime = stime.text.strip()
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,title)
        if "px.gif" in thumbnail:
            thumbnail = elem.img['data-src']
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='current')
    if next_page:
        next_page = next_page.parent.find_next_sibling("li").a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.find('iframe')['src']
    url = urlparse.urljoin(item.url,url)
    soup = create_soup(url, referer=item.url)#.find('video', id='video')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        if elem.has_attr('title'):
            quality = elem['title']
        else:
            quality =  "mp4"
        url += "|Referer=%s" % item.url
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    if not matches:
        url = soup.find('div', class_='responsive-player').find(re.compile("(?:iframe|source)"))['src']
        if "php?q=" in url:
            import base64
            url = url.split('php?q=')
            url_decode = base64.b64decode(url[-1]).decode("utf8")
            url = AlfaChannel.do_unquote(url_decode)
            url = scrapertools.find_single_match(url, '<iframe src="([^"]+)"')
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist[::-1]


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='responsive-player')
    url = soup.find('iframe')['src']
    url = urlparse.urljoin(item.url,url)
    soup = create_soup(url)#.find('video', id='video')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        if elem.has_attr('title'):
            quality = elem['title']
        else:
            quality =  "mp4"
        url += "|Referer=%s" % item.url
        itemlist.append(['%s' %quality, url])
    if not matches:
        url = soup.find('div', class_='responsive-player').find(re.compile("(?:iframe|source)"))['src']
        if "php?q=" in url:
            import base64
            url = url.split('php?q=')
            url_decode = base64.b64decode(url[-1]).decode("utf8")
            url = AlfaChannel.do_unquote(url_decode)
            url = scrapertools.find_single_match(url, '<iframe src="([^"]+)"')
        itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist[::-1]
