# -*- coding: utf-8 -*-
# -*- Channel Pelisplus -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re, base64

from modules import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib import generictools
from bs4 import BeautifulSoup

IDIOMAS = {'latino': 'LAT', 'castellano': 'CAST', 'subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'directo',
    'vidlox',
    'fembed',
    'uqload',
    'gounlimited',
    'fastplay',
    'mixdrop',
    'mystream'
    ]
forced_proxy_opt = 'ProxySSL'  

canonical = {
             'channel': 'pelisplus', 
             'host': config.get_setting("current_host", 'pelisplus', default=''), 
             'host_alt': ["https://ww3.pelisplus.to/"], 
             'host_black_list': ["https://home.pelisplus.lat/", "https://pelisplus.lat/",
                                 "https://pelisplus.mov/", "https://pelisplus.ninja/", "https://www.pelisplus.lat/", 
                                 "https://www.pelisplus.me/", "https://pelisplushd.net/","https://pelisplushd.to/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 'forced_proxy_ifnot_assistant': forced_proxy_opt,
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
domain = scrapertools.find_single_match(host, patron_domain)


def mainlist(item):
    logger.info()
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="sub_menu", url=host + "peliculas",
                         type="movies",
                         thumbnail=get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu", url=host + "series", 
                         type="tv",
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Anime", action="sub_menu", url=host + "animes",
                         type="animes",
                         thumbnail=get_thumb('anime', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Doramas", action="list_all", url=host + "doramas",
                         content="serie", thumbnail=get_thumb('doramas', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",
                         thumbnail=get_thumb('search', auto=True)))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = list()
    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=item.url,
                         thumbnail=get_thumb('all', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         type=item.type,
                         thumbnail=get_thumb('genres', auto=True)))
    return itemlist


def create_soup(url, referer=None, post=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    if post:
        data = httptools.downloadpage(url, post=post, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url)
    matches = soup.find_all("article", class_="item") #re.compile(r"^pitem\d+")
    for elem in matches:
        url = elem.a['href']
        thumb = elem.img['src']
        if "placever.jpg" in thumb:
            thumb = elem.img['data-src']
        title = elem.img['alt']
        title2 = elem.h2.text.strip()
        
        year = scrapertools.find_single_match(title2, r"(\d{4})")
        if not year:
            year = "-"
        # if item.type and item.type.lower() not in url:
            # continue
        new_item = Item(channel=item.channel, title=title, url= url, thumbnail=thumb, infoLabels={"year": year})

        if "/pelicula/" in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = 'movie'
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.contentType = 'tvshow'

        itemlist.append(new_item)
    tmdb.set_infoLabels_itemlist(itemlist, True)
    #  Paginación

    try:
        next_page = soup.find('a', rel='next')['href']
        if next_page:
            if not next_page.startswith(host):
                next_page = host + next_page
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass

    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    soup = create_soup(item.url).find("ul", id="seasonAll")
    matches = soup.find_all("li")
    for elem in matches:
        title = elem.text.strip()
        infoLabels["season"] = scrapertools.find_single_match(title, "(\d+)")
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels, contentType='season'))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    
    soup = create_soup(item.url)
    patt = re.compile(r'const seasonsJson = \{')
    data = soup.find(text=patt)
    data = scrapertools.find_single_match(data,'"%s"(.*?)\]' %infoLabels["season"])
    patron = '"title": "([^"]+)".*?'
    patron += '"episode": (\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for name, cap in matches[::-1]:
        infoLabels['episode'] = cap
        url = "%s/season/%s/episode/%s" %(item.url,season,cap)
        title = '%sx%s - %s' % (season, cap, name)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels, contentType='episode'))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def section(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find('div', id='genresMenu')
    matches = soup.find_all("a", href=re.compile("/genres/[A-z0-9-]+"))
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        url += "?type=%s" %item.type
        itemlist.append(Item(channel=item.channel, url=url, title=title, action='list_all', type=item.type))

    return itemlist


def findvideos(item):
    import base64
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find('div', class_='bg-tabs')
    matches = soup.find_all("li", role="presentation") #re.compile(r"^pitem\d+")
    for elem in matches:
        url = elem['data-server']
        url = base64.b64encode(url.encode("utf-8")).decode('utf-8')
        data = httptools.downloadpage(host + "/player/" + url, canonical=canonical).data
        url = scrapertools.find_single_match(data,"(?i)Location.href = '([^']+)'")
        if "up.asdasd" in url:
            url = "https://netu.to/"
        idioma = soup.img['alt']
        itemlist.append(Item(channel=item.channel, title='%s [%s]', url=url, action='play', language=idioma,
                            infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % (i.server.capitalize(), i.language))
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle))
    return itemlist


def search(item, texto):
    logger.info()

    try:
        if texto != '':
            texto = urlparse.quote_plus(texto)
            item.url = urlparse.urljoin('search/', texto)
            item.url = urlparse.urljoin(host, item.url)
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

