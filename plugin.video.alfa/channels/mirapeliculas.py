# -*- coding: utf-8 -*-
#------------------------------------------------------------

import re

from modules import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb
from core import servertools
from core import urlparse
from modules import filtertools
from bs4 import BeautifulSoup

IDIOMAS = {'Latino': 'LAT', 'Español': 'ESP', 'Subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())
list_servers = []
list_quality = []

forced_proxy_opt = 'ProxyCF'

canonical = {
             'channel': 'mirapeliculas', 
             'host': config.get_setting("current_host", 'mirapeliculas', default=''), 
             'host_alt': ["https://ww2.dipelis.com/"], 
             'host_black_list': ["https://mirapeliculasde.com/"], 
             'pattern': '<link\s*rel="[^>]*icon"[^>]+href="([^"]+)"', 
             'set_tls': True, 'set_tls_min': False, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
host_save = host

timeout = 5

__channel__ = canonical['channel']
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
__modo_grafico__ = config.get_setting('modo_grafico', __channel__, True)



def mainlist(item):
    logger.info()
    
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Peliculas", action="lista_all", url= host + "page/1", language=[]))
    itemlist.append(item.clone(title="Series", action="lista_all", url= host + "series/", language=[]))
    # itemlist.append(item.clone(title="Novedades", action="lista", url= host + "ver/estrenos/", language=[]))
    # itemlist.append(item.clone(title="Castellano", action="lista", url= host + "ver/castellano/", language=['CAST']))
    # itemlist.append(item.clone(title="Latino", action="lista", url= host + "ver/latino/", language=['LAT']))
    # itemlist.append(item.clone(title="Subtituladas", action="lista", url= host + "ver/subtituladas/", language=['VOSE']))
    itemlist.append(item.clone(title="Categorias", action="categorias", url= host, language=[]))
    itemlist.append(item.clone(title="Buscar", action="search", language=[]))
    
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False, language=[]))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def configuracion(item):
    
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    
    return ret


def search(item, texto):
    logger.info()
    
    texto = texto.replace(" ", "+")
    item.url = host + "buscar/?q=%s" % texto
    
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find('ul', class_='category-list').find_all('li')
    
    # data = httptools.downloadpage(item.url, canonical=canonical).data
    
    # patron  = '<li class="cat-item cat-item-3"><a href="([^"]+)" title="([^"]+)">'
    # matches = re.compile(patron,re.DOTALL).findall(data)
    
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        cantidad = elem.span.text.strip()
        title = "%s (%s)" %(title, cantidad)
        itemlist.append(item.clone(channel=item.channel, action="lista_all", url=url, title=title))
    
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, timeout=timeout, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=timeout, canonical=canonical).data
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista_all(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='new-films').find_all('article', class_='movie-card')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        quality = elem.find(class_=re.compile('(?:poster-|)badge')).text.strip()
        year = elem.find(class_=re.compile('(?:poster-|)year')).text.strip()
        
        new_item = Item(channel=item.channel, url=url, title=title, thumbnail=thumbnail, 
                        quality=quality, infoLabels={"year": year or '-'})
        if "/serie/" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
        itemlist.append(new_item)
        # itemlist.append(item.clone(action="findvideos", title=title, url=url,
                                   # infoLabels={'year': year or '-'}, 
                                   # thumbnail=thumbnail, quality=calidad, 
                                   # contentType='movie', contentTitle=title))
    
    tmdb.set_infoLabels(itemlist, True)
    
    pagination = soup.find('div', class_='pagenavi')
    if pagination.span.find_next_sibling("a"):
        next_page = pagination.span.find_next_sibling("a")['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    temporada = []
    
    infoLabels = item.infoLabels
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='chapter-list').find_all('a')
    for elem in matches:
        titulo = elem.text.strip()
        tempo = scrapertools.find_single_match(titulo, r'(\d+)(?:X|x)\d+ ')
        if tempo and not tempo in temporada:
            temporada.append(tempo)
    for season in temporada:
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action="episodesxseasons",
                             infoLabels=infoLabels))
    itemlist.reverse()
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
    matches = soup.find('div', class_='chapter-list').find_all('a')
    for elem in matches:
        url = elem['href']
        if re.search(r'%s(?:X|x)\d+' %season, url):
            cap = scrapertools.find_single_match(url, 'x(\d+)')
            if int(cap) < 10:
                cap = "0%s" % cap
            title = "%sx%s" % (season, cap)
            infoLabels["episode"] = cap
            itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                                     infoLabels=infoLabels))
    itemlist.reverse()
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
    itemlist = []
    
    data = httptools.downloadpage(item.url, canonical=canonical).data
    
    patron = '"(\\w{2,3})":\[(.*?)\]'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for lang, videos in matches:
        if videos:
            videos = videos.split(',')
            for elem in videos:
                url = elem.replace("\\/", "/")
                itemlist.append(item.clone(action="play", title='%s', url=url, language=lang))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    
    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist



