# -*- coding: utf-8 -*-
# -*- Channel CineDeTodo -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools



host = 'https://www.cinedetodo.net/'

IDIOMAS = {'Latino': 'LAT'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gounlimited', 'rapidvideo', 'vshare', 'clipwatching', 'jawclowd', 'streamango']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Películas", action="sub_menu", url=host,
                         thumbnail=get_thumb('last', auto=True), type='MovieList'))

    itemlist.append(Item(channel=item.channel, title="Series", action="sub_menu", url=host,
                         thumbnail=get_thumb('last', auto=True), type='Series'))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all", url=host,
                         thumbnail=get_thumb('last', auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", section='genre',
                         thumbnail=get_thumb('genres', auto=True), type=item.type ))

    if item.type != 'Series':
        itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", section='alpha',
                             thumbnail=get_thumb('alphabet', auto=True), type=item.type))



    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    full_data = data
    if item.section != '':
        data = scrapertools.find_single_match(data, 'class="MovieList NoLmtxt(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data, '<!--<%s>.*?class="MovieList NoLmtxt(.*?)</ul>' % item.type)

    if item.section == 'alpha':
        patron = '<span class="Num">\d+.*?<a href="([^"]+)" class.*?<img src="([^"]+)" alt=.*?'
        patron += '<strong>([^"]+)</strong>.*?<td>(\d{4})</td>'
        matches = re.compile(patron, re.DOTALL).findall(full_data)
    else:
        patron = '<article.*?<a href="(.*?)">.*?<img src="(.*?)" alt=.*?'
        patron += '<h3 class="Title">(.*?)<\/h3>.*?date_range">(\d+)<'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:

        url = scrapedurl
        if year == '':
            year = '-'
        if "|" in scrapedtitle:
            scrapedtitle= scrapedtitle.split("|")
            cleantitle = scrapedtitle[0].strip()
        else:
            cleantitle = scrapedtitle

        cleantitle = re.sub('\(.*?\)', '', cleantitle)

        if not config.get_setting('unify'):
            title = '%s [%s]'%(cleantitle, year)
        else:
            title = cleantitle
        thumbnail = 'http:'+scrapedthumbnail

        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        infoLabels = {'year': year}
                        )

        if 'series' not in url:
            new_item.contentTitle = cleantitle
            new_item.action='findvideos'

        else:
            new_item.contentSerieName = cleantitle
            new_item.action = 'seasons'

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    #  Paginación

    url_next_page = scrapertools.find_single_match(full_data,'<a class="next.*?href="([^"]+)">')
    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                             type=item.type))
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    if item.type == 'Series':
        url = host + '?tr_post_type=2'
    else:
        url = host + '?tr_post_type=1'

    data = get_source(url)
    action = 'list_all'


    if item.section == 'genre':
        patron = '<a href="([^ ]+)" class="Button STPb">(.*?)</a>'
    elif item.section == 'alpha':
        patron = '<li><a href="(.*?letter.*?)">(.*?)</a>'
        action = 'list_all'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        url = data_one
        title = data_two
        if title != 'Ver más':
            if item.type == 'Series':
                url =url + '?tr_post_type=2'
            else:
                url = url + '?tr_post_type=1'
                if 'serie'in title.lower():
                    continue
            new_item = Item(channel=item.channel, title= title, url=url, action=action, section=item.section,
                            type=item.type)
            itemlist.append(new_item)

    return itemlist


def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='Temporada <span>(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        season = season.lower().replace('temporada','')
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
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

    itemlist = []

    full_data=get_source(item.url)
    data = scrapertools.find_single_match(full_data, 'Temporada <span>\d+.*?</ul>')
    patron='<span class="Num">(\d+)<.*?<a href="([^"]+)".*?"MvTbTtl".*?">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedepisode, scrapedurl, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist



def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    data = scrapertools.decodeHtmlentities(data)
    patron = 'id="(Opt\d+)">.*?src="([^"]+)" frameborder.*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, scrapedurl in matches:
        scrapedurl = scrapedurl.replace('"','').replace('&#038;','&')
        data_video = get_source(scrapedurl)
        url = scrapertools.find_single_match(data_video, '<div class="Video">.*?src="([^"]+)" frameborder')
        opt_data = scrapertools.find_single_match(data,'"%s"><span>.*?</span>.*?<span>(.*?)</span>'%option).split('-')
        language = opt_data[0].strip()
        language = re.sub('\(|\)', '', language)
        quality = opt_data[1].strip()
        if url != '' and 'youtube' not in url:
            itemlist.append(Item(channel=item.channel, title='%s', url=url, language=IDIOMAS[language], quality=quality,
                                 action='play', infoLabels=item.infoLabels))
        elif 'youtube' in url:
            trailer = Item(channel=item.channel, title='Trailer', url=url, action='play', server='youtube')

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    try:
        itemlist.append(trailer)
    except:
        pass

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))


    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.section = 'search'
    if texto != '':
        return list_all(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host+'animacion/?tr_post_type=1'
        elif categoria == 'terror':
            item.url = host+'terror/?tr_post_type=1'
        item.type = 'MovieList'
        item.section = 'search'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
