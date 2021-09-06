# -*- coding: utf-8 -*-
# -*- Channel SonPelisHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                                               # Usamos el nativo de PY2 que es más rápido

import re
import base64

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from bs4 import BeautifulSoup

host = 'https://sonpelishd.net/'


def mainlist(item):
    logger.info()

    itemlist = []

    # itemlist.append(item.clone(title="Peliculas",
                               # type = 1,
                               # action="list_all",
                               # thumbnail=get_thumb('movies', auto=True),
                               # url=host + 'pelicula'
                               # ))

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=host + 'page/1?s'
                               ))

    itemlist.append(item.clone(title="Series",
                               type = 1,
                               action="list_all",
                               thumbnail=get_thumb('movies', auto=True),
                               url=host + 'serie'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'page/1?s',
                               thumbnail=get_thumb('genres', auto=True),
                               seccion='generos-pelicula'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'page/1?s',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='fecha-estreno'
                               ))

    # itemlist.append(item.clone(title="Calidad",
                               # action="seccion",
                               # url=host + 'page/1?s',
                               # thumbnail=get_thumb('quality', auto=True),
                               # seccion='calidad'
                               # ))

    itemlist.append(item.clone(title="Buscar", action="search",
                               thumbnail=get_thumb('search', auto=True),
                               url=host + '?s='
                               ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def seccion(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if item.seccion == 'generos-pelicula':
        matches = soup.find('nav', class_='genres').find_all("li")
    else:
        matches = soup.find('nav', class_='releases').find_all("li")
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail =""
        itemlist.append(item.clone(action='list_all',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail
                                   ))
    return itemlist


def create_soup(url, referer=None, post=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if item.type:
        matches = soup.find('div', id='archive-content').find_all("article")
    else:
        matches = soup.find_all("article")
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.img['src']
        title = elem.img['alt']
        year = elem.find(class_='year')
        if year: year = year.text.strip()
        else: year= elem.find(class_='metadata').find('span').text.strip()

        new_item = item.clone(url=url, title=title, thumbnail=thumbnail, infoLabels={"year": year})
        if "serie" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    next_page = soup.find(class_='icon-chevron-right' )
    if next_page:
        next_page = next_page.parent['href']
        itemlist.append(item.clone(action="list_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find("div", id="seasons")
    matches = soup.find_all("div", class_="se-q")
    infoLabels = item.infoLabels
    for elem in matches:
        season = elem.find("span", class_="se-t").text
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(item.clone(title=title, action="episodesxseasons", infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                        action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist



def episodesxseasons(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find("div", id="seasons")
    matches = soup.find_all("ul")
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    for elem in matches[(int(season)-1)]:
        url = elem.a['href']
        epi = elem['class']
        epi = str(epi[0]).replace("mark-", "")
        infoLabels["episode"] = epi
        title = "%sx%s - Episodio %s" % (season, epi, epi)
        itemlist.append(item.clone(url=url, title=title, action="findvideos", infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all("li", id=re.compile(r"^player-option-\d+"))
    
    for elem in matches:
        lang = elem.find('span', class_='title').text
        data_post = elem['data-post']
        type = elem['data-type']
        num = elem['data-nume']
        url = 'https://sonpelishd.net/wp-admin/admin-ajax.php'
        post = {'action': 'doo_player_ajax', 'post': data_post, 'nume': num, 'type': type}
        data = httptools.downloadpage(url, post=post).json
        url = data['embed_url']
        if url:
            itemlist.append(item.clone(title= "%s", url=url, action='play', language=lang))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    if item.infoLabels['mediatype'] == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle
                                 ))

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'page/1/?s'

        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'

        elif categoria == 'terror':
            item.url = host + 'category/terror/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

