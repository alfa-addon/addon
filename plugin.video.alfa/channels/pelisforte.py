# -*- coding: utf-8 -*-
# -*- Channel PelisForte -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from modules import autoplay
from modules import filtertools
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools
from core.item import Item
# from lib.AlfaChannelHelper import ToroFilm
from platformcode import config, logger
from channelselector import get_thumb
from bs4 import BeautifulSoup

# AlfaChannel = ToroFilm(host, "")

forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'pelisforte', 
             'host': config.get_setting("current_host", 'pelisforte', default=''), 
             'host_alt': ["https://www1.pelisforte.se/"], 
             'host_black_list': ["https://pelisforte.co/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


IDIOMAS = {'Subtitulado': 'VOSE', 'Latino': 'LAT', 'Castellano': 'CAST'}
SERVER = {'swish': 'Streamwish', 'vgfplay': 'Vidguard', 'playpf': 'Tiwikiwi',
          'filemoon': 'Filemoon', 'okhd': 'Okhd', 'bf0skv': 'Filemoon'}

list_language = list(IDIOMAS.values())
list_servers = list(SERVER.values())
list_quality = []


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)


    itemlist.append(Item(channel=item.channel, title="Novedades", action="list_all",
                         url=host + "pelicula",
                         thumbnail=get_thumb("newest", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all",
                         url=host + "pelis/idiomas/castellano", extra = "CAST",
                         thumbnail=get_thumb("cast", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all",
                         url=host + "pelis/idiomas/espanol-latino", extra = "LAT",
                         thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all",
                         url=host + "pelis/idiomas/subtituladas-p02", extra = "VOSE",
                         thumbnail=get_thumb("vose", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Sagas", action="section", url=host + "portal002",
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host + "portal002",
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="alphabet", url=host + "portal002",
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Años", action="alphabet", url=host + "portal002",
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, post=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
        
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('ul', class_='post-lst').find_all("li", class_=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.h2.text.strip()
        thumbnail = elem.img['src']
        year = elem.find('span', class_='year').text.strip()
        if year == '':
            year = '-'
        
        extra = ""
        if item.extra: extra= item.extra
        
        itemlist.append(Item(channel=item.channel, action = "findvideos", url=url, title=title, contentTitle = title, 
                             thumbnail=thumbnail, extra=extra, infoLabels={"year": year}))
    
    tmdb.set_infoLabels(itemlist, True)
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    next_page = soup.find('a', class_='current')
    if next_page and next_page.find_next_sibling("a"):
        next_page = next_page.find_next_sibling("a")['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="list_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist



def section(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "Sagas" in item.title:
        matches = soup.find("li", id="menu-item-11504").find_all("li")
    else:
        matches = soup.find("li", id="menu-item-77").find_all("li")
    for elem in matches:
        url = elem.a['href']
        title= elem.a.text.strip()
        itemlist.append(Item(channel=item.channel, action = "list_all", url=url, title=title))
    return itemlist


def alphabet(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "Años" in item.title:
        matches = soup.find("section", id="torofilm_movies_annee-2").find_all("li")
        matches.reverse()
    else:
        matches = soup.find("section", id="wdgt_letter-2").find_all("li")
    for elem in matches:
        url = elem.a['href']
        title= elem.a.text.strip()
        itemlist.append(Item(channel=item.channel, action = "list_all", url=url, title=title))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url).find('section', class_='player')
    matches = soup.find_all("iframe")
    servers = soup.find_all("span", class_="server")
    for elem, serv in zip(matches, servers):
        url = elem['data-src']
        url = url.replace("?h=", "r.php?h=")
        srv, lang = serv.text.split(" -")
        srv = srv.strip().lower()
        lang = lang.strip().split(" ")[-1]
        language=IDIOMAS.get(lang, lang)
        server=SERVER.get(srv, srv)
        
        itemlist.append(Item(channel=item.channel, action='play', url=url,
                             server=server , language=language, infoLabels=infoLabels))
    
    itemlist = sorted(itemlist, key=lambda i: (i.language, i.server))
    
    if item.extra:
        itemlist = [i for i in itemlist if i.language == item.extra]
    else:
        # Requerido para FilterTools
        itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action='add_pelicula_to_library', extra=item.extra,
                             contentTitle=item.contentTitle))
    elif config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action='add_pelicula_to_library',
                             contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = httptools.downloadpage(item.url).url
    if not "vgfplay" in url and not "listeamed" in url and not "bf0skv" in url:
        url += "|Referer=%s" %item.url
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "%20")
        item.url = "%s/page/1?s=%s" % (host, texto)
        if texto != "":
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + "pelicula"
        elif categoria == 'latino':
            item.url = host + "pelis/idiomas/espanol-latino"
        elif categoria == 'castellano':
            item.url = host + "pelis/idiomas/castellano"
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/animacion-p04'
        elif categoria == 'terror':
            item.url = host + 'peliculas/terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def fix_title(*args):
    args[2].title = re.sub(r'(/.*)| 1$', '', args[2].title)
    return args[2]