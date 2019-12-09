# -*- coding: utf-8 -*-
# -*- Channel TVAnime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from core import tmdb
from core.item import Item
from platformcode import logger, config
from channels import autoplay
from channels import filtertools
from channels import renumbertools

host = "https://monoschinos.com/"

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'animespace')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'animespace')

IDIOMAS = {'VOSE': 'VOSE', 'Latino':'LAT', 'Castellano':'CAST'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'openload', 'streamango']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel, title="Ultimas",
                               action="list_all",
                               thumbnail=get_thumb('last', auto=True),
                               url=host + 'emision'))

    itemlist.append(Item(channel=item.channel, title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=host + 'animes'))

    itemlist.append(Item(channel=item.channel, title="Anime",
                              action="list_all",
                              thumbnail=get_thumb('anime', auto=True),
                              url=host + 'categoria/anime'))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         action="list_all",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host + 'categoria/pelicula'))

    itemlist.append(Item(channel=item.channel, title="OVAs",
                              action="list_all",
                              thumbnail='',
                              url=host + 'categoria/ova'))

    itemlist.append(Item(channel=item.channel, title="ONAs",
                              action="list_all",
                              thumbnail='',
                              url=host + 'categoria/ona'))


    itemlist.append(Item(channel=item.channel, title="Especiales",
                              action="list_all",
                              thumbnail='',
                              url=host + 'categoria/especial'))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                               action="search",
                               url=host + 'search?q=',
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'
                               ))

    autoplay.show_option(item.channel, itemlist)
    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<article.*?href="([^"]+)">.*?src="([^"]+)".*?'
    patron +=  '<h3 class="Title">([^<]+)</h3>.*?"fecha">([^<]+)<.*?</i>([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year, type in matches:
        type = type.strip().lower()
        url = scrapedurl
        thumbnail = scrapedthumbnail
        if 'latino' in scrapedtitle.lower():
            lang = 'Latino'
        elif 'castellano' in scrapedtitle.lower():
            lang = 'Castellano'
        else:
            lang = 'VOSE'
        title = re.sub('Audio|Latino|Castellano', '', scrapedtitle)
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        new_item= Item(channel=item.channel,
                       action='episodios',
                       title=title,
                       url=url,
                       thumbnail=thumbnail,
                       language = lang,
                       infoLabels={'year':year}
                       )
        if type != 'anime':
            new_item.contentTitle=title
        else:
            new_item.plot=type
            new_item.contentSerieName=title
            new_item.context = context
        itemlist.append(new_item)

        # Paginacion
    next_page = scrapertools.find_single_match(data,
                                               '"page-item active">.*?</a>.*?<a class="page-link" href="([^"]+)">')

    if next_page != "":
        actual_page = scrapertools.find_single_match(item.url, '([^\?]+)?')
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=actual_page + next_page,
                             thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                             ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
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

def new_episodes(item):
    logger.info()

    itemlist = []

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<section class="caps">.*?</section>')
    patron = '<article.*?<a href="([^"]+)">.*?src="([^"]+)".*?'
    patron += '<span class="episode">.*?</i>([^<]+)</span>.*?<h2 class="Title">([^<]+)</h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, epi, scrapedtitle in matches:
        url = scrapedurl
        if 'latino' in scrapedtitle.lower():
            lang = 'Latino'
        elif 'castellano' in scrapedtitle.lower():
            lang = 'Castellano'
        else:
            lang = 'VOSE'
        scrapedtitle = re.sub('Audio|Latino|Castellano', '', scrapedtitle)
        title = '%s - Episodio %s' % (scrapedtitle, epi)
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=scrapedthumbnail,
                             action='findvideos', language=lang))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<a class="item" href="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl in matches:
        episode = scrapertools.find_single_match(scrapedurl, '.*?episodio-(\d+)')
        lang = item.language
        season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, int(episode))
        title = "%sx%s - %s" % (season, str(episode).zfill(2),item.contentSerieName)
        url = scrapedurl
        infoLabels['season'] = season
        infoLabels['episode'] = episode

        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.contentSerieName, url=url,
                             action='findvideos', language=lang, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = itemlist[::-1]
    if item.contentSerieName != '' and config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def findvideos(item):
    import urllib
    logger.info()

    itemlist = []
    g_host = 'https://storage.googleapis.com/proven-reality-256313.appspot.com/'

    data = get_source(item.url)
    patron = r'%sreproductor\?url=([^&]+)' % host
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        server = ''
        scrapedurl = urllib.unquote(scrapedurl)
        
        if "cl?url=" in scrapedurl:
            scrapedurl = scrapertools.find_single_match(scrapedurl, '\?url=(.*)')
            url = g_host + scrapedurl.replace('+', '%20')
            server = "directo"
        
        elif '?url=' in  scrapedurl:
            url = scrapertools.find_single_match(scrapedurl, '.*?url=([^&]+)?')
        else:
            url = scrapedurl
            

        if url:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, action='play',
                                 language = item.language, infoLabels=item.infoLabels, server=server))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url=host
        itemlist = new_episodes(item)
    return itemlist
