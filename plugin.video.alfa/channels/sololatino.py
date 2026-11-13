# -*- coding: utf-8 -*-
# -*- Channel SoloLatino -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-
from core import urlparse as alfa_urlparse
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from lib import planbtools, jsunpack
from channelselector import get_thumb
from platformcode import config, logger
from modules import filtertools
from modules import autoplay
from lib.alfa_assistant import is_alfa_installed
from core.jsontools import json


IDIOMAS = {'2': 'VOSE', "0": "LAT", "1": "CAST", "LAT": "LAT"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'gvideo',
    'fembed',
    'directo'
    ]

# cf_assistant = True if is_alfa_installed() else False
# cf_assistant = "force" if is_alfa_installed() else False
# forced_proxy_opt = None if cf_assistant else 'ProxyCF'
# cf_debug = True
forced_proxy_opt = '' # ProxyCF  ProxySSL          https://sololatino.net/peliculas
headers = httptools.default_headers.copy()

canonical = {
             'channel': 'sololatino', 
             'host': config.get_setting("current_host", 'sololatino', default=''), 
             'host_alt': ["https://sololatino.net/"], 
             'host_black_list': [], 
             'pattern': ['<meta\s*property="og:url"\s*content="([^"]+)"'], 
             
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'host_alt_findb': [1]
             
             # 'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'cf_assistant': False, 'CF_stat': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             
             
             # 'set_tls': True, 'set_tls_min': True, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': cf_assistant, 
             # 'cf_assistant_ua': True, 'cf_assistant_get_source': True if cf_assistant == 'force' else False, 
             # 'cf_no_blacklist': True, 'cf_removeAllCookies': False if cf_assistant == 'force' else True,
             # 'cf_challenge': True, 'cf_returnkey': 'url', 'cf_partial': True, 'cf_debug': cf_debug, 
             # 'cf_cookies_names': {'cf_clearance': False},
             # 'CF_if_assistant': True if cf_assistant is True else False, 'retries_cloudflare': -1, 
             # 'CF_stat': True if cf_assistant is True else False, 'session_verify': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True, 'renumbertools': False
            }

host = canonical['host'] or canonical['host_alt'][0]

TIMEOUT = 30


def mainlist(item):
    logger.info()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=alfa_urlparse.build_url(host, 'peliculas'),
                         thumbnail=get_thumb('movies', auto=True), type="pelicula"))
    itemlist.append(Item(channel=item.channel, title='Series', url=alfa_urlparse.build_url(host, 'series'), action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Anime', url=alfa_urlparse.build_url(host, 'animes'), action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Doramas', url=alfa_urlparse.build_url(host, 'doramas'), action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Plataformas', url=host, action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=alfa_urlparse.build_url(host, 'buscar', query='q='),
                         thumbnail=get_thumb("search", auto=True)))
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def sub_menu(item):
    logger.info()
    
    itemlist = list()
    # url = item.url.replace('peliculas', 'pelicula')
    
    # if item.title == "Peliculas":
        # itemlist.append(Item(channel=item.channel, title='Ultimas', url=url + "estrenos/", action='list_all',
                             # thumbnail=get_thumb('last', auto=True)))
    # else:
        # itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=url + "novedades/", action='list_all',
                             # thumbnail=get_thumb('last', auto=True)))
    
    # itemlist.append(Item(channel=item.channel, title='Recomendadas', url=url + "mejor-valoradas/",
                         # action='list_all', thumbnail=get_thumb('recomendadas', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Todas', url=item.url, action='list_all',
                         thumbnail=get_thumb('all', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Popular', url=alfa_urlparse.build_url(item.url, query='genero=&año=0&nota=0&sort=popular'), action='list_all',
                         thumbnail=get_thumb('all', auto=True)))    
    
    itemlist.append(Item(channel=item.channel, title='Generos', url=item.url, action='section',
                         thumbnail=get_thumb('genres', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Año', url=item.url, action='section',
                         thumbnail=get_thumb('years', auto=True)))
    
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    
    response = httptools.downloadpage(host, referer=host, headers=headers, canonical=canonical)
    
    if referer:
        data = httptools.downloadpage(url, timeout=TIMEOUT, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=TIMEOUT, canonical=canonical).data
        # data = httptools.downloadpage(url, timeout=TIMEOUT, referer=host, canonical=canonical).data
    
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    
    return soup


def get_language(lang_data):
    logger.info()
    
    language = list()
    
    lang_list = lang_data.find_all("span", class_="flag")
    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["style"], r'/flags/(.*?).png\)')
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    
    return language


def section(item):
    logger.info()
    
    itemlist = list()
    # url = item.url.replace('peliculas', 'pelicula')
    
    # soup = create_soup(host)
    soup = create_soup(item.url)
    
    if item.title == "Generos":
        matches = soup.find("select", attrs={"name": "genero"})
        base_url = "%s?genero=%s&nota=0&sort=updated&page=1"
    else:
        matches = soup.find("select", attrs={"name": "año"})
        base_url = "%s?genero=0&año=%s&nota=0&sort=updated&page=1"
    
    for elem in matches.find_all("option"):
        gendata = elem.get('value', '')
        title = elem.text
        url_section = base_url % (item.url, gendata)
        
        if gendata:
            itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url_section))
    
    return itemlist


def list_all(item):
    logger.info()
    itemlist = list()
    
    try:
        # soup = create_soup(host)
        # logger.debug(soup)
        soup = create_soup(item.url)
    except Exception:
        return itemlist
    # logger.debug(soup)
    matches = soup.find("div", class_="movies-grid").find_all("div", class_='card') #id=re.compile(r"^post-\d+")
    
    for elem in matches:
        url = elem.a["href"]
        title = elem.img["alt"]
        thumb = elem.img["src"]
        try:
            year = elem.find('span', class_='card__year').text.strip()
        except Exception:
            year = '-'
        
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})
        
        if "novedades" in item.url:
            try:
                season, episode = scrapertools.find_single_match(title, '\:\s*(\d+).(\d+)')
                new_item.contentSeason = int(season)
                new_item.contentEpisodeNumber = int(episode)
                title = re.sub('\:\s*\d+.\d+', '', title)
                new_item.title = '%sx%s - %s' % (new_item.contentSeason, str(new_item.contentEpisodeNumber).zfill(2), title)
            except Exception:
                new_item.contentSeason = 1
                new_item.contentEpisodeNumber = 0
            new_item.contentSerieName = title
            new_item.action = "findvideos"
            new_item.contentType = 'episode'
        elif "pelicula" in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = 'movie'
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.contentType = 'tvshow'
            new_item.context = filtertools.context(item, list_language, list_quality)
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    try:
        url_next_page = soup.find("a", rel="next")["href"]
    except Exception:
        return itemlist
    
    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))
    
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    try:
        # soup = create_soup(host)
        soup = create_soup(item.url).find("select", id="season-select")
        
        matches = soup.find_all("option")
    except Exception:
        return itemlist
    
    infoLabels = item.infoLabels
    
    for elem in matches:
        try:
            season = int(elem["value"])
        except Exception:
            season = 1
        title = "Temporada %s" % season
        infoLabels["season"] = season
        
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
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
        # soup = create_soup(host)
        soup = create_soup(item.url).find("div", attrs={"data-season-panel": season})
        matches = soup.find_all("a")
    except Exception:
        return itemlist
    
    for elem in matches:
        url = elem["href"]
        ep_num = elem.find('p', class_='ep-num')
        epi_num = ep_num.text.strip().replace("E", "")
        infoLabels["episode"] = epi_num
        title = "%sx%s" % (season, epi_num)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels, contentType='episode'))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist


def findvideos(item):
    logger.info()
    
    return planbtools.build_findvideos(canonical, list_language, item)


def search(item, texto):
    logger.info()
    
    try:
        item.url = alfa_urlparse.update_query(item.url, {'q': texto})
        
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


