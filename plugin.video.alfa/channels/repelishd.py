# -*- coding: utf-8 -*-
# -*- Channel RepelisHD -*-
# -*- Created for Rebel-addon -*-
# -*- By the Rebel Developer -*-

import sys
import re

from core import urlparse
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools, channeltools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from modules import filtertools
from modules import autoplay


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'sub': 'VOSE'}
CUSTOM_FILTER = {'castellano': 'Castellano', 'latino': 'Latino', 'subtitulado': 'sub'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = []


thumbmx = 'http://flags.fmcdn.net/data/flags/normal/mx.png'
thumbes = 'http://flags.fmcdn.net/data/flags/normal/es.png'
thumbus = 'http://flags.fmcdn.net/data/flags/normal/us.png'


forced_proxy_opt = 'ProxySSL'

#  "https://repelishd.cam/"
#  "https://cinehdplus.gratis/"  "https://cinehdplus.cam/" 

#  "https://cinehdplus.org/"  "https://cinehdplus.net/"(OUT)

canonical = {
             'channel': 'repelishd', 
             'host': config.get_setting("current_host", 'repelishd', default=''), 
             'host_alt': ["https://cinehdplus.gratis/"], 
             'host_black_list': ["https://cinehdplus.cam/"], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*title='], 
             # 'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'cf_assistant': False, 'CF_stat': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="RepelisHD Castellano", action="submenu", url=host, thumbnail=thumbes, extra="Castellano"))
    itemlist.append(Item(channel=item.channel, title="RepelisHD Latino", action="submenu", url=host, thumbnail=thumbmx, extra="Latino"))
    itemlist.append(Item(channel=item.channel, title="RepelisHD Vose", action="submenu", url=host, thumbnail=thumbus, extra="sub"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def submenu(item):
    logger.info()
    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all", url="%s%s/page/1/?language=%s" % (host, "cine", item.extra), thumbnail=get_thumb("movies", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", url="%s%s/page/1/?language=%s" % (host, "series", item.extra), thumbnail=get_thumb("tvshows", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url="%s%s/page/1/?language=%s" % (host, "peliculas", item.extra), thumbnail=get_thumb("genres", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Años", action="anno", url=host, thumbnail=get_thumb("year", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host, thumbnail=get_thumb("search", auto=True), extra=item.extra))
    
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
    
    soup = create_soup(item.url, referer=host)
    matches = soup.find_all("div", class_="card")
    for elem in matches:
        lang = list()
        url = elem.a["href"]
        title = elem.img["alt"]
        quality = elem.find(class_='quality').text.strip()
        try:
            thumb = elem.img["data-src"]
        except:
            thumb = elem.img["src"]
        
        languages = elem.find_all("img", class_="idioma")
        for l in languages:
            if not l["alt"] in lang:
                lang.append(l["alt"])
        year = elem.find("span", class_="year").text
        
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, 
                        language=lang, infoLabels={"year": year})
        
        if re.match(r"s\d+-e\d+", quality):
            new_item.contentSerieName = title
            new_item.action = "seasons"
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    for itm in itemlist:
        itm.extra = item.extra
    
    try:
        next_page = soup.find(class_="catalog__paginator").find_all("a")[-1]
        if not "index.php" in item.url:
            next_page = next_page["href"]
            next_page = scrapertools.find_single_match(next_page, 'page/(\d+)')
            next_page = re.sub(r"page/\d+", "page/{0}".format(next_page), item.url)
        else:
            next_page = next_page["onclick"]
            next_page = scrapertools.find_single_match(next_page, '(\d+)')
            next_page = re.sub(r"&search_start=\d+", "&search_start={0}".format(next_page), item.url)
            
        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except:
        pass
    
    return itemlist


def section(item):
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="genres").find_all("li")
    for elem in matches:
        url = elem.a['href']
        title = url.replace(host, '').replace("/", "")
        if "series" in title or "cine" in title or "proximas" in title: continue
        url = item.url.replace("peliculas", title)
        title = title.capitalize()
        itemlist.append(item.clone(title=title, url=url, action="list_all"))
    
    return itemlist


def anno(item):
    logger.info()
    from datetime import datetime
    
    itemlist = []
    
    now = datetime.now()
    year = int(now.year)
    while year >= 1980:
        itemlist.append(item.clone(title="%s" %year, action="list_all", url= "%s%s/page/1/?language=%s&years=%s;%s" % (host, "peliculas", item.extra, year, year)))
        year -= 1
    itemlist.append(item.clone(title="70s", action="list_all", url= "%s%s/page/1/?language=%s&years=1970;1979" % (host, "peliculas", item.extra)))
    itemlist.append(item.clone(title="60s", action="list_all", url= "%s%s/page/1/?language=%s&years=1960;1969" % (host, "peliculas", item.extra)))
    itemlist.append(item.clone(title="50s", action="list_all", url= "%s%s/page/1/?language=%s&years=1950;1959" % (host, "peliculas", item.extra)))
    itemlist.append(item.clone(title="<40s", action="list_all", url= "%s%s/page/1/?language=%s&years=1930;1949" % (host, "peliculas", item.extra)))
    
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='tt_season').find_all("a")
    for elem in matches:
        season = elem.text.strip()
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    for itm in itemlist:
        itm.extra = item.extra
    
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
    
    try:
        matches = create_soup(item.url).find("div", id="season-%s" % season).find("ul").find_all("li")
    except:
        return itemlist
    for elem in matches:
        cap = elem.a.text.strip()
        # if int(cap) < 10:
            # cap = "0%s" % cap
        title = "%sx%s" % (season, cap)
        infoLabels['episode'] = cap
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='findvideos', infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    for itm in itemlist:
        itm.extra = item.extra
    
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url)
    if infoLabels.get('season', ''):
        patron = "serie-%s_%s" %(infoLabels['season'], infoLabels['episode'])
        matches = soup.find('a', id=patron).parent
        matches = soup.find('div', class_='mirrors')
    
    else:
        url = soup.find('div', class_='player_contenedor').find("iframe")['src']
        data = create_soup(url)
        matches = data.find_all('ul', class_='_player-mirrors')
    if infoLabels.get('season', ''):
        for elem in matches.find_all('a'):
            url = elem['data-link']
            server = elem.text.strip()
            itemlist.append(Item(
                                    channel=item.channel,
                                    contentTitle=item.contentTitle,
                                    contentThumbnail=item.thumbnail,
                                    infoLabels=item.infoLabels,
                                    # language="Latino",
                                    title='%s', action="play",
                                    url=url
                                   ))
    else:
        for elem in matches:
            lang = elem['class'][1]
            lang = CUSTOM_FILTER.get(lang, 'unknown')
            if lang != item.extra:
                logger.error("{} ({}) != {}".format(lang, IDIOMAS.get(lang, ''), item.extra))
                continue
            else:
                logger.error("{} ({}) == {}".format(lang, IDIOMAS.get(lang, ''), item.extra))
            matches = elem.find_all('li')
            for url in matches:
                server = url.text.strip()
                url = url['data-link']
                if "verhdlink" in url: continue
                if url.startswith("//"):
                    url = "https:%s" %url
                itemlist.append(Item(
                                        channel=item.channel,
                                        contentTitle=item.contentTitle,
                                        contentThumbnail=item.thumbnail,
                                        infoLabels=item.infoLabels,
                                        language=IDIOMAS.get(lang, ''),
                                        title='%s', action="play",
                                        url=url
                                       ))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
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
    texto = texto.replace(" ", "%20")
    item.url = host + "index.php?do=search&subaction=search&search_start=1&story=" + texto
    if texto != '':
        return list_all(item)
    else:
        return []

