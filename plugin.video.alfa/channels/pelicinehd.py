# -*- coding: utf-8 -*-
# -*- Channel PeliCineHD -*-
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
from modules import autoplay
from platformcode import config, logger
from channelselector import get_thumb
import base64

forced_proxy_opt = ""

canonical = {
             'channel': 'pelicinehd', 
             'host': config.get_setting("current_host", 'pelicinehd', default=''),
             'host_alt': ["https://pelicinehd.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]



SERVER = {
          "hlswish": "streamwish", "playerwish": "streamwish", "ghbrisk": "streamwish", "iplayerhls": "streamwish",
           "listeamed": "vidguard", "1fichier":"onefichier", "luluvdo": "lulustream", "lulu": "lulustream",
           "dhtpre": "vidhidepro", "peytonepre": "vidhidepro", "smoothpre": "vidhidepro", 
           "movearnpre": "vidhidepro", "seraphinapl": "vidhidepro", "bingezove": "vidhidepro", 
           "dingtezuni": "vidhidepro", "dinisglows": "vidhidepro", "mivalyo": "vidhidepro",
           "filemoon": "filemoon", "voe":"voe"
          }


IDIOMAS = {'mexico': 'LAT', 'latíno': 'LAT', 'espana': 'CAST', 'ingles': 'VOSE'}

list_language = list(IDIOMAS.values())
list_servers = list(set(SERVER.values()))
list_quality = []



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
    matches = soup.find_all("li", id=re.compile(r"^post-\d+"))
    for elem in matches:
        try:
            quality = ""
            year = ""
            
            id = elem['id'].replace("post-", "")
            url = elem.get("href", '') or elem.a.get("href", '')
            thumb = elem.img['src']
            if not thumb.startswith("https"):
                thumb = "https:%s" % thumb
            title = elem.find('div', class_='Title') or elem.h3 or elem.h2
            year = elem.find('span', class_='year') or elem.find('span', class_='year-tag') \
                                                    or elem.find('span', class_='Date')
            if title:
                title = title.get_text(strip=True)
            if year:
                year = year.text.strip()
            language = []
            if elem.find('span', class_='lang'):
                matches = elem.find('span', class_='lang').find_all('img')
                for elem in matches:
                    lang = scrapertools.find_single_match(elem['src'], '/([A-z]+).png').lower()
                    language.append(IDIOMAS.get(lang, lang))
            
            new_item = Item(channel=item.channel, url=url, title=title, thumbnail=thumb, quality = quality, id=id,
                            language=language, infoLabels={"year": year})
            
            if "series" in url or "serie" in url:
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
    
    if soup.find("a", string=re.compile(r"^(?:Next|SIGUIENTE)")):
        next_page = soup.find("a", string=re.compile(r"^(?:Next|SIGUIENTE)"))['href']
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    
    return itemlist



def section(item):
    logger.info()
    import string

    itemlist = list()
    soup = create_soup(item.url)
    
    if item.title == "Generos":
        matches = soup.find_all("li", class_="menu-item-object-category")
        for elem in matches:
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                                 url=url, type=item.type))

    elif item.title == "Por Año":
        soup = soup.find('section', id='torofilm_movies_annee-2')
        for elem in soup.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text
            itemlist.append(Item(channel=item.channel, title=title, action="list_all",
                                 url=url, type=item.type))
        itemlist.reverse()
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url)
    matches = soup.find_all('li', class_='sel-temp')
    for elem in matches:
        id = elem.a['data-post']
        season = elem.a['data-season']
        title = "Temporada %s" % season
        url = "%swp-admin/admin-ajax.php?action=action_select_season&season=%s&post=%s" % (host,season, id)
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="episodesxseasons", id=id,
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
    
    post= "action=action_select_season&season=%s&post=%s" % (season, item.id)
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    data = httptools.downloadpage(item.url, post=post, headers=headers, canonical=canonical).data
    soup = BeautifulSoup(data, "html.parser", from_encoding="utf-8")
    matches = soup.find_all('article')
    
    for elem in matches:
        url = elem.a['href']
        
        cap = elem.find('span', class_='num-epi').text.strip().split('x')[-1]
        if int(cap) < 10:
            cap = "0%s" % cap
        title = "%sx%s" % (season, cap)
        infoLabels["episode"] = cap
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                               language=item.language, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
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
    match0 = soup.find('aside', class_='video-player').find_all('iframe')
    match1 = soup.find('aside', class_='video-options').find_all(class_='server')
    
    for elem, serv in zip(match0, match1):
        url = elem['data-src']
        url = re.sub("amp;|#038;", "", url)
        serv = serv.text.strip().split("-")
        server = serv[0].strip().lower()
        if not SERVER.get(server,''):
            server = ""
        else:
            server = SERVER.get(server,server)
        lang = serv[-1].strip().lower().replace(" hd", "")
        language = IDIOMAS.get(lang, lang)
        
        quality = ""
        
        itemlist.append(Item(channel=item.channel, url=url, action='play', server=server,  # plot=len(match0),
                            infoLabels=infoLabels, language=language, quality=quality))
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist

def play(item):
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url)
    url = soup.iframe['src']
    devuelve = servertools.findvideosbyserver(url, item.server)
    if devuelve:
        item.url =  devuelve[0][1]
    itemlist = servertools.get_servers_itemlist([item.clone(url=url, server="")])
    
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url = "%s?s=%s" %(host, texto)
            return list_all(item)
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

