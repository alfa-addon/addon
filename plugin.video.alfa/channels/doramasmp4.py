# -*- coding: utf-8 -*-
# -*- Channel DoramasMP4 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

HOST = 'https://www17.doramasmp4.com/'
host = httptools.downloadpage('https://www17.doramasmp4.com/', only_headers=True).url

IDIOMAS = {'sub': 'VOSE', 'VO': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['okru', 'directo', 'thevimeo', 'rcdnme', 'gplay']

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel= item.channel, title="Doramas", action="list_all",
                         url=host + 'catalogue?format%5B%5D=drama&sort=latest',
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))
    
    itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="latest_episodes",
                        url=host, thumbnail=get_thumb('new episodes', auto=True), type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Variedades", action="list_all",
                         url=host + 'catalogue?format%5B%5D=varieties&sort=latest',
                         thumbnail='', type='dorama'))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         url=host + 'catalogue?format%5B%5D=movie&sort=latest',
                         thumbnail=get_thumb('movies', auto=True), type='movie'))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         url=host + 'catalogue', type='dorama',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section", 
                         url=host + 'catalogue', type='dorama',
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por País", action="section", 
                         url=host + 'catalogue', type='dorama',
                         thumbnail=get_thumb('country', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title = 'Buscar...', action="search", url= host+'ajax/search.php',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

# def doramas_menu(item):
#     logger.info()

#     itemlist =[]

#     itemlist.append(Item(channel=item.channel, title="Últimas", action="list_all", type='dorama',
#                          url=host + 'catalogue?format%5B%5D=drama&sort=latest', thumbnail=get_thumb('last', auto=True)))
#     from lib import alfa_assistant
#     if alfa_assistant.open_alfa_assistant(getWebViewInfo=True):
#     #En la web salta cf v2
#         itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="latest_episodes",
#                             url=host + 'latest-episodes', thumbnail=get_thumb('new episodes', auto=True), type='dorama'))
    
#     itemlist.append(Item(channel=item.channel, title="Corea", action="list_all", type='dorama',
#                          url=host + 'catalogue?country%5B%5D=south-korea', thumbnail=get_thumb('dorama', auto=True)))

#     itemlist.append(Item(channel=item.channel, title="China", action="list_all", type='dorama',
#                          url=host + 'catalogue?country%5B%5D=china', thumbnail=get_thumb('dorama', auto=True)))
    
#     itemlist.append(Item(channel=item.channel, title="Japón", action="list_all", type='dorama',
#                          url=host + 'catalogue?country%5B%5D=japan', thumbnail=get_thumb('dorama', auto=True)))

#     itemlist.append(Item(channel=item.channel, title="Tailandia", action="list_all", type='dorama',
#                          url=host + 'catalogue?country%5B%5D=south-korea', thumbnail=get_thumb('dorama', auto=True)))
#     return itemlist

def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)

    patron = '<div class="col-lg-2 col-md-3 col-6 mb-3"><a href="([^"]+)".*?<img src="([^"]+)".*?'
    patron += 'txt-size-12">(\d{4})<.*?text-truncate">([^<]+)<.*?description">([^<]+)<.*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    media_type = item.type
    for scrapedurl, scrapedthumbnail, year, scrapedtitle, scrapedplot in matches:
        url = scrapedurl
        scrapedtitle = scrapedtitle
        thumbnail = re.sub(r'/resize/\w+/\d+x\d+@', '/original/poster/', scrapedthumbnail)
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url, mode=item.mode,
                        thumbnail=thumbnail, type=media_type, infoLabels={'year':year})
        if media_type != 'dorama':
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
            new_item.type = item.type

        else:
            new_item.contentSerieName=scrapedtitle
            new_item.action = 'episodios'
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" aria-label="Netx">')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                                 url=host+'catalogue'+next_page, thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 type=item.type))
    return itemlist

def latest_episodes(item):
    logger.info()
    itemlist = []
    infoLabels = dict()
    data = get_source(item.url)
    patron = 'shadow-lg rounded.*? href="([^"]+)".*?src="([^"]+)".*?style="">([^<]+)<.*?>Capítulo (\d+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedep in matches:

        title = '%s: 1x%s' % (scrapedtitle, scrapedep)
        contentSerieName = scrapedtitle
        infoLabels['episode'] = scrapedep
        infoLabels['season'] = 1
        thumbnail = re.sub(r'/\d+x\d+@', '/1200x720@', scrapedthumbnail)
        itemlist.append(Item(channel=item.channel, action='findvideos', url=scrapedurl, thumbnail=thumbnail,
                             title=title, contentSerieName=contentSerieName, type='episode', infoLabels=infoLabels,
                             from_last=True))

    #tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    
    data = get_source(item.url)
    patron = '<a itemprop="url".*?href="([^"]+)".*?title="(.*?) Cap.*?".*?>Capítulo (\d+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    
    if not matches and item.mode in ("search", "section"):
        
        del item.contentSerieName
        item.contentTitle = item.title
        
        tmdb.set_infoLabels_itemlist([item], seekTmdb=True)
        
        return findvideos(item)

    for scrapedurl, scrapedtitle, scrapedep in matches:
        url = scrapedurl
        contentEpisodeNumber = scrapedep

        infoLabels['season'] = 1
        infoLabels['episode'] = contentEpisodeNumber

        if scrapedtitle != '':
            title = '%sx%s - %s' % ('1',scrapedep, scrapedtitle)
        else:
            title = 'episodio %s' % scrapedep

        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentEpisodeNumber=contentEpisodeNumber, type='episode', infoLabels=infoLabels))


    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios", text_color='yellow'))
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    infoLabels = item.infoLabels
    if item.from_last:
        data = httptools.downloadpage(host+'ajax/search.php',
                     post={"q": item.contentSerieName}).data
        patron = r'>(\d{4})</div>'
        year = scrapertools.find_single_match(data, patron)
        item.infoLabels['year'] = year
        tmdb.set_infoLabels_itemlist([item], seekTmdb=True)

    data = get_source(item.url)
    
    patron = 'link="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if '</strong> ¡Este capítulo no tiene subtítulos, solo audio original! </div>' in data:
        language = IDIOMAS['vo']
    else:
        language = IDIOMAS['sub']

    #if item.type !='episode' and '<meta property=article:section content=Pelicula>' not in data:
    # if item.type !='episode' and item.type != 'movie':
    #     item.type = 'dorama'
    #     item.contentSerieName = item.contentTitle
    #     item.contentTitle = ''
    #     return episodios(item)
    # else:

    for video_url in matches:
        headers = {'referer': item.url}
        token = scrapertools.find_single_match(video_url, 'token=(.*)')
        #
        video_data = httptools.downloadpage(video_url, headers=headers, follow_redirects=False).data
        url = scrapertools.find_single_match(video_data, '(?:<iframe class=".*?"|<source) src="([^"]+)"')

        if "redirect.php" in url:
            video_data = httptools.downloadpage(url, headers=headers, follow_redirects=False).data
            url = scrapertools.find_single_match(video_data, "window.location.href = '([^']+)'")

        if url:

            new_item = Item(channel=item.channel, title='[%s] [%s]', url=url,
                            action='play', language = language, infoLabels=infoLabels)

            itemlist.append(new_item)

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))


    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search_results(item):
    logger.info()
    itemlist = list()
    infoLabels = dict()
    data = httptools.downloadpage(item.url, post={"q": item.texto}).data
    data = re.sub(r'\n|\r|\t', '', data)
    
    patron = r'border-bottom" href="([^"]+)">.*?'
    patron += r'src="([^"]+)">.*?-500">([^<]+)</div>.*?'
    patron += r'>(\d{4})</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, thumb, title, year in matches:
        thumb = re.sub('/resize/poster/\d+x\d+@', '/original/poster/', thumb)
        infoLabels['year'] = year
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=thumb, action="episodios",
                             mode="search", contentSerieName=title, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def section(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, '>Todo los generos</button>.*?<button class')
    
    elif 'Años' in item.title:
        data = scrapertools.find_single_match(data, '>Todo los años</button>.*?<button class')

    elif 'Por Pa' in item.title:
        data = scrapertools.find_single_match(data, '>Todo los paises</button>.*?<button class')

    patron = 'input" id="([^"]+)".*?name="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for id, name in matches:
        title = id.capitalize()
        id = id.replace('-','+')
        url = '%s?%s=%s' % (item.url, name, id)
        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action='list_all', type=item.type, mode="section"))
    #TODO ordenar lista categorias
    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    item.texto = texto.replace(" ", "+")
    if texto != '':
        try:
            return search_results(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist
