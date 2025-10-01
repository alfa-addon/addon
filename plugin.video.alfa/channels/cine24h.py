# -*- coding: utf-8 -*-
# -*- Channel Cine24H -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from bs4 import BeautifulSoup
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from modules import filtertools
from modules import autoplay
from platformcode import config, logger
from channelselector import get_thumb
import base64


canonical = {
             'channel': 'cine24h', 
             'host': config.get_setting("current_host", 'cine24h', default=''),
             'host_alt': ["https://cine24h.online/", "https://esp.cine24h.online/", "https://sub.cine24h.online/"], 
             'host_black_list': ["https://cine24h.net/"], 
             'pattern': '<link\s*rel="icon"\s*href="([^"]+)"', 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }


host_lang = config.get_setting('host_lang', channel='cine24h')
if config.get_setting("current_host", canonical['channel'], default='') != canonical['host_alt'][host_lang] and config.get_setting("current_host", canonical['channel'], default='') in canonical['host_alt']:
    config.set_setting("current_host", canonical['host_alt'][host_lang], canonical['channel'])
host = config.get_setting("current_host", canonical['channel'], default='') or canonical['host_alt'][host_lang]


IDIOMAS = {'LAT': 'LAT', 'ESP': 'CAST', 'SUB': 'VOSE'}
list_language = list(IDIOMAS.values())
list_servers = ['fembed', 'mystream', 'uptobox', 'gounlimited']
list_quality = ['720HD']



def settingCanal(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ''

def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")

    return soup


def mainlist(item):
    logger.info()
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all", 
                         url=host + 'peliculas/',
                         thumbnail=get_thumb("movies", auto=True)))
    
    # itemlist.append(Item(channel=item.channel, title="Más Vistas", action="list_all", 
                         # url=host + 'peliculas-mas-vistas/',
                         # thumbnail=get_thumb("more watched", auto=True)))
    
    # itemlist.append(Item(channel=item.channel, title="Mejor Valoradas", action="list_all", 
                         # url=host + 'peliculas-mas-valoradas/',
                         # thumbnail=get_thumb("more voted", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", 
                         url=host + 'series/',
                         thumbnail=get_thumb("tvshows", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb("genres", auto=True), type=1))
    
    itemlist.append(Item(channel=item.channel, title="Por Año", action="section", url=host,
                         thumbnail=get_thumb("year", auto=True), type=1))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))
    
    itemlist.append(Item(channel=item.channel,
                         title="Configurar Canal...",
                         text_color="turquoise",
                         action="settingCanal",
                         thumbnail=get_thumb('setting_0.png'),
                         url=''
                         ))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def list_all(item):
    logger.info()
    itemlist = list()
    
    
    soup = create_soup(item.url)
    matches = soup.find_all("article")
    
    shown_half = 1 if item.half else 0
    items_half = 30
    matches = matches[items_half:] if shown_half == 1 else matches[:items_half]
    
    for elem in matches:
        langs = list()
        try:
            quality = ""
            year = ""
            url = elem.get("href", '') or elem.a.get("href", '')
            thumb = elem.img['src']
            if not thumb.startswith("https"):
                thumb = "https:%s" % thumb
            title = elem.find('div', class_='Title') or elem.h3 or elem.h2
            year = elem.find('span', class_='Year') or elem.find('span', class_='year-tag') \
                                                    or elem.find('span', class_='Date')
            if title:
                title = title.get_text(strip=True)
            if year:
                year = year.text.strip()
            if elem.find('div', class_='language-box'):
                lang_items = elem.find_all('div', class_='lang-item')
                for lang in lang_items:
                    lang = lang.span.get_text(strip=True)
                    language = IDIOMAS.get(lang, lang)
                    langs.append(language)
            
            new_item = Item(channel=item.channel, url=url, title=title, thumbnail=thumb, quality = quality,
                            language=langs, infoLabels={"year": year})
            
            if "series" in url or "serie" in url:
                seasons = ""
                seasons = elem.find('span', class_='se') or elem.find('span', class_='Se') or elem.find('span', class_='seasons')
                if seasons:
                    seasons = seasons.text.strip()
                    new_item.seasons = seasons.replace(" Temp.", "")
                new_item.action = "seasons"
                new_item.contentSerieName = title
            else:
                new_item.action = "findvideos"
                new_item.contentTitle = title
            itemlist.append(new_item)
            
        
        except:
            logger.error(elem)
            pass
            # continue
        
        
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    if shown_half == 0:
        itemlist.append(item.clone(title="Siguiente >", half=1))
    else:
        try:
            next_page = soup.find("a", class_="next page-numbers")["href"]
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
        except:
            pass

    return itemlist



def section(item):
    logger.info()
    import string

    itemlist = list()
    soup = create_soup(item.url).find_all("ul", class_="sub-menu")
    if item.title == "Generos":
        soup = soup[1]
        for elem in soup.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                                 url=url, type=item.type))

    elif item.title == "Por Año":
        soup = soup[0]
        for elem in soup.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                                 url=url, type=item.type))

    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    seasons = ""
    if item.seasons.isdigit():
        seasons = int(item.seasons)
    if not seasons:
        soup = create_soup(item.url)
        matches = soup.find_all('div', class_='AABox')
        seasons = len(matches)
    a=0
    while seasons > a:
        a += 1
        if a < 10:
            season = "0%s" %a
        else:
            season = a
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseasons",
                             language=item.language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='AABox')[int(season)-1]
    matches = matches.find_all('a', class_='MvTbImg')
    for elem in matches:
        url = elem['href']
        cap = scrapertools.find_single_match(url, 'x(\d+)')
        if int(cap) < 10:
            cap = "0%s" % cap
        title = "%sx%s" % (season, cap)
        infoLabels["episode"] = cap
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                               language=item.language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    a = len(itemlist)-1
    for i in itemlist:
        if a >= 0:
            title= itemlist[a].title
            titulo = itemlist[a].infoLabels['episodio_titulo']
            title = "%s %s" %(title, titulo)
            itemlist[a].title = title
            a -= 1
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist[:-1]:
        itemlist += episodesxseasons(tempitem)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url)
    match = soup.find_all("div", class_="drpdn")
    for leng in match:
        lang = leng.span.text.strip()
        if "LAT" in lang: lang = "LAT"
        if "ESP" in lang: lang = "CAST"
        if "SUB" in lang: lang = "SUB"
        matches = leng.find_all('li')
        for elem in matches:
            url = get_url(elem['data-src'])
            itemlist.append(Item(channel=item.channel, url=url, action='play', title= "%s",
                        infoLabels=infoLabels, language=lang))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    itemlist.sort(key=lambda x: x.server)
    itemlist.sort(key=lambda x: x.language)
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            return list_all(item)
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def fix_title(title):
    title = re.sub(r'\((.*)', '', title)
    title = re.sub(r'\[(.*?)\]', '', title)
    return title

def get_url(url):
    url = base64.b64decode(url).decode("utf8")
    url = re.sub("amp;|#038;", "", url)
    soup = create_soup(url)
    url = soup.iframe['src']
    return url

