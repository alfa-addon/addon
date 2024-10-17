# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from bs4 import BeautifulSoup

host = ''
canonical = {
             'channel': 'netfapx', 
             'host': config.get_setting("current_host", 'netfapx', default=''), 
             'host_alt': ["https://netfapx.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# Timming 

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "?orderby=newest"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "?orderby=popular"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "?orderby="))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="catalogo", url=host + "pornstar/?orderby=popular"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories/"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (host, texto)
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
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='pinbox')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['src']
        cantidad = elem.find_all("div")[-2]#.text.split("\n")[2]
        cantidad = scrapertools.find_single_match(str(cantidad), '"Videos"/>([^<]+)<').strip()
        title = "%s (%s)" %(stitle,cantidad)
        url = url.replace("pornstar", "videos")
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    try:
        next_page = soup.find('a', class_='next')['href']
    except Exception:
        next_page = None
    if next_page:
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page.strip()))
    return itemlist
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    soup = soup.find('div', class_='cat-thumb')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        thumbnail = elem.img['src']
        title = scrapertools.find_single_match(thumbnail, '.*?/02/(.*?)-Porn-Videos.jpg')
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
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
    matches = soup.find_all('article', class_='pinbox')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['src']
        stime = elem.find_all("div")[-2].text.split("\n")[3]
        title = "[COLOR yellow]%s[/COLOR] %s" % (stime.strip(),stitle)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    try:
        next_page = soup.find('a', class_='next')['href']
    except Exception:
        next_page = None
    if next_page:
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page.strip()))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    url = scrapertools.find_single_match(data, 'source: "([^"]+)"')
    url += "|ignore_response_code=True"
    itemlist.append(Item(channel=item.channel, action="play", title = "Direto", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    pornstars = scrapertools.find_single_match(data, '>Pornstars:</h2>(.*?)<h2')
    pornstars = scrapertools.find_multiple_matches(pornstars, '>([^<]+)</a>')
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    lista = item.contentTitle.split()
    lista.insert (2, pornstar)
    item.contentTitle = ' '.join(lista)    
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    url = scrapertools.find_single_match(data, 'source: "([^"]+)"')
    if not url:
        url = scrapertools.find_single_match(data, '<source src="([^"]+)" type="video/mp4"')
    url += "|ignore_response_code=True"
    itemlist.append(Item(channel=item.channel, action="play", timeout=30, url=url, contentTitle=item.contentTitle))
    return itemlist