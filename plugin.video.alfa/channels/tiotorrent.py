# -*- coding: utf-8 -*-
# -*- Channel TioTorrent -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from channelselector import get_thumb
from platformcode import logger
from platformcode import config
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb

host = 'http://www.tiotorrent.com/'

def mainlist(item):
    logger.info()

    itemlist = []
    
    itemlist.append(item.clone(title="Peliculas",
                               action="movie_list",
                               thumbnail=get_thumb("channels_movie.png")
                               ))

    itemlist.append(item.clone(title="Series",
                               action="series_list",
                               thumbnail=get_thumb("channels_tvshow.png")
                               ))
    return itemlist


def movie_list(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="lista",
                               url=host + 'estrenos-de-cine',
                               extra='movie'
                               ))

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               url=host + 'peliculas',
                               extra='movie'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '/peliculas/?pTit=',
                               thumbnail=get_thumb("search.png"),
                               extra='movie'
                               ))
    return itemlist


def series_list(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               url=host + 'series',
                               extra='serie'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '/series/?pTit=',
                               thumbnail=get_thumb("search.png"),
                               extra='serie'
                               ))
    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def lista (item):
    logger.info ()
    itemlist = []
    data = get_source(item.url)
    if item.extra == 'movie':
        patron = "<div class=moviesbox.*?><a href=(.*?)>.*?image:url\('(.*?)'\)>.*?<b>.*?>(.*?)<"
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            url = scrapedurl
            thumbnail = scrapedthumbnail
            contentTitle = scrapedtitle.decode('latin1').encode('utf8')
            title = contentTitle
            filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w396", "")
            filtro_list = {"poster_path": filtro_thumb}
            filtro_list = filtro_list.items()

            itemlist.append(item.clone(action='findvideos',
                                       title=title, url=url,
                                       thumbnail=thumbnail,
                                       contentTitle=contentTitle,
                                       infoLabels={'filtro': filtro_list},
                                       extra=item.extra
                                       ))
    else:
        patron = "<div class=moviesbox.*?>.*?episode>(.*?)x(.*?)<.*?href=(.*?)>.*?image:url\('(.*?)'.*?href.*?>(.*?)<"
        matches = re.compile(patron, re.DOTALL).findall(data)
        for season, episode, scrapedurl, scrapedthumbnail, scrapedtitle in matches:
            url = scrapedurl
            thumbnail = scrapedthumbnail
            contentSerieName = scrapedtitle
            title = '%s' % contentSerieName
            filtro_thumb = scrapedthumbnail.replace("https://image.tmdb.org/t/p/w396", "")
            filtro_list = {"poster_path": filtro_thumb}
            filtro_list = filtro_list.items()
            contentSeason=season
            contentEpisode=episode
            itemlist.append(item.clone(action='seasons',
                                       title=title,
                                       url=url,
                                       thumbnail=thumbnail,
                                       contentSerieName=contentSerieName,
                                       contentSeason=contentSeason,
                                       contentEpisode=contentEpisode,
                                       infoLabels={'filtro': filtro_list},
                                       extra=item.extra
                                       ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb =True)
 #Paginacion

    if itemlist !=[]:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data,'<span class=pagination_next><a href=(.*?)>')
        import inspect
        if next_page !='':
           itemlist.append(item.clone(action = "lista",
                                      title = 'Siguiente >>>',
                                      url = next_page,
                                      thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'
                                      ))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return lista(item)
    else:
        return []


def seasons(item):
    logger.info()
    itemlist=[]
    infoLabels = item.infoLabels
    data=get_source(item.url)
    patron ='href=javascript:showSeasson\(.*?\); id=.*?>Temporada (.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for season in matches:
        title='Temporada %s' % season
        infoLabels['season'] = season
        itemlist.append(Item(channel=item.channel,
                             title= title,
                             url=item.url,
                             action='episodesxseasons',
                             contentSeasonNumber=season,
                             contentSerieName=item.contentSerieName,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    itemlist = itemlist[::-1]
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="all_episodes", contentSerieName=item.contentSerieName))

    return itemlist

def all_episodes(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist

def episodesxseasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron = "<div class=corner-episode>%sx(.\d+)<\/div><a href=(.*?)>.*?" % item.contentSeasonNumber
    patron += "image:url\('(.*?)'.*?href.*?>(%s)<" % item.contentSerieName
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels=item.infoLabels
    for episode, scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        contentEpisodeNumber=episode
        season = item.contentSeasonNumber
        url=scrapedurl
        thumbnail=scrapedthumbnail
        infoLabels['episode']=episode
        title = '%sx%s - %s' % (season, episode, item.contentSerieName)
        itemlist.append(Item(channel=item.channel,
                             action='findvideos',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=item.contentSerieName,
                             contentEpisodeNumber=contentEpisodeNumber,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist[::-1]


def findvideos(item):
    logger.info()
    itemlist=[]
    data = get_source(item.url)
    patron = "<a class=dload.*? target=_blank>.*?<\/a><i>(.*?)<\/i>.*?<a href=.*?showDownload\((.*?)\);"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for quality, extra_info in matches:
        extra_info= extra_info.replace("'",'')
        extra_info= extra_info.split(',')
        title = '%s [%s]' % (item.contentTitle, quality)
        url = extra_info[1]
        if item.extra == 'movie':
            url = extra_info[1]
        else:
            url = extra_info[2]
        server = 'torrent'
        itemlist.append(Item(channel=item.channel,
                             title=title,
                             contentTitle= item.title,
                             url=url,
                             action='play',
                             quality=quality,
                             server=server,
                             thumbnail = item.infoLabels['thumbnail'],
                             infoLabels=item.infoLabels
                             ))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_pelicula_to_library",
                             extra="findvideos",
                             contentTitle=item.contentTitle
                             ))

    return itemlist


def newest(category):
    logger.info()
    item = Item()
    try:
        if category in  ['peliculas', 'torrent']:
            item.url = host + 'estrenos-de-cine'
            item.extra='movie'
            itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
        if category == 'torrent':

            item.url = host+'series'
            item.extra = 'serie'
            itemlist.extend(lista(item))

        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
