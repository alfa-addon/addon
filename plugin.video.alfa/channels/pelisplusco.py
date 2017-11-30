# -*- coding: utf-8 -*-
# -*- Channel PelisPlus.co -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from platformcode import logger
from platformcode import config
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb


host = 'http://pelisplus.co'

def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Peliculas",
                               action="movie_menu",
                               ))

    itemlist.append(item.clone(title="Series",
                               action="series_menu",
                               ))

    return itemlist

def movie_menu(item):

    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="list_all",
                               url = host+'/estrenos/',
                               type = 'normal'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               seccion='generos'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host,
                               seccion='anios'
                               ))

    return itemlist

def series_menu(item):

    logger.info()

    itemlist =[]

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               url=host + '/series/',
                               type='serie'
                               ))

    return itemlist


def get_source(url):

    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all (item):
    logger.info ()
    itemlist = []

    if item.type not in ['normal', 'seccion', 'serie']:
        post = {'page':item.page, 'type':item.type,'id':item.id}
        post = urllib.urlencode(post)
        data =httptools.downloadpage(item.url, post=post).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    else:
        data = get_source(item.url)
    if item.type == 'serie' or item.type == 'recents':
        contentType = 'serie'
        action = 'seasons'
    else:
        contentType = 'pelicula'
        action = 'findvideos'

    patron = 'item-%s><a href=(.*?)><figure><img.*?data-src=(.*?) alt=.*?<p>(.*?)<\/p><span>(\d{4})<\/span>'%contentType

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        url = host+scrapedurl+'p001/'
        thumbnail = scrapedthumbnail
        plot= ''
        contentTitle=scrapedtitle
        title = contentTitle
        year = scrapedyear
        fanart =''
        
        new_item=item.clone(action=action,
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            plot=plot,
                            fanart=fanart,
                            infoLabels ={'year':year}
                            )
        if contentType =='serie':
            new_item.contentSerieName=title
        else:
            new_item.contentTitle = title
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb =True)
 #Paginacion

    next_page_valid = scrapertools.find_single_match(data, '<div class=butmore(?: site=series|) page=(.*?) id=(.*?) '
                                                           'type=(.*?) limit=.*?>')
    if item.type != 'normal' and (len(itemlist)>19 or next_page_valid):
        type = item.type
        if item.type == 'serie':
            type = 'recents'
        if next_page_valid:
            page = str(int(next_page_valid[0])+1)
            if item.type != 'recents':
                id = next_page_valid[1]
                type = next_page_valid[2]
            else:
                id =''
        else:
            page = str(int(item.page)+1)
            id = item.id

        if type =='recents':
            type_pagination = '/series/pagination'
        else:
            type_pagination = '/pagination'

        url = host+type_pagination

        itemlist.append(item.clone(action = "list_all",
                                   title = 'Siguiente >>>',
                                   page=page,
                                   url = url,
                                   id = id,
                                   type = type
                                   ))
    return itemlist

def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.seccion == 'generos':
        patron = '<li><a href=(.*?)><i class=ion-cube><\/i>(.*?)<\/span>'
        type = 'genre'
    elif item.seccion == 'anios':
        patron = '<li><a href=(\/peliculas.*?)>(\d{4})<\/a>'
        type = 'year'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        if item.seccion == 'generos':
            cant = re.sub(r'.*?<span class=cant-genre>','',scrapedtitle)
            only_title = re.sub(r'<.*','',scrapedtitle).rstrip()
            title = only_title+' (%s)'%cant

        url = host+scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="list_all",
                 title=title,
                 fulltitle=item.title,
                 url=url,
                 type = 'seccion'
                 ))
        # Paginacion

        if itemlist != []:
            next_page = scrapertools.find_single_match(data, '<li><a class= item href=(.*?)&limit=.*?>Siguiente <')
            next_page_url = host + next_page
            import inspect
            if next_page != '':
                itemlist.append(item.clone(action="seccion",
                                           title='Siguiente >>>',
                                           url=next_page_url,
                                           thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png'
                                           ))

    return itemlist


def seasons(item):
    logger.info()
    itemlist =[]

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron ='<i class=ion-chevron-down arrow><\/i>(.*?)<\/div>'
    matches = matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels=item.infoLabels

    for title in matches:
        season = title.replace('Temporada ','')
        infoLabels['season'] = season
        itemlist.append(Item(
                             channel=item.channel,
                             title=title,
                             url=item.url,
                             action='season_episodes',
                             contentSerieName= item.contentSerieName,
                             contentSeasonNumber = season,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist[::-1]

def season_episodes(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    season = str(item.infoLabels['season'])
    patron = '<a href=(.*?temporada-%s\/.*?) title=.*?i-play><\/i> (.*?)<\/a>'%season
    matches = matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for url, episode in matches:
        episodenumber = re.sub('C.* ','',episode)
        infoLabels['episode'] = episodenumber
        itemlist.append(Item(channel=item.channel,
                        title= episode,
                        url = host+url,
                        action = 'findvideos',
                        infoLabels=infoLabels,
                        contentEpisodeNumber=episode
                        ))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    return itemlist[::-1]


def findvideos(item):
    logger.info()
    itemlist = []
    video_list = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'data-source=(.*?) .*?tab.*?data.*?srt=(.*?) data-iframe=><a>(.*?)\s?-\s?(.*?)<\/a>'

    matches = matches = re.compile(patron, re.DOTALL).findall(data)

    for url, sub, language, quality in matches:

        if 'http' not in url:

            new_url = 'https://onevideo.tv/api/player?key=90503e3de26d45e455b55e9dc54f015b3d1d4150&link' \
                      '=%s&srt=%s' % (url, sub)
            data = httptools.downloadpage(new_url).data
            data = re.sub(r'\\', "", data)
            video_list.extend(servertools.find_video_items(data=data))

            for video_url in video_list:
                video_url.channel = item.channel
                video_url.action = 'play'
                video_url.title = item.title + '(%s) (%s)' % (language, video_url.server)
                if video_url.language == '':
                    video_url.language = language
                video_url.subtitle = sub
                video_url.contentTitle=item.contentTitle
        else:
            server = servertools.get_server_from_url(url)
            video_list.append(item.clone(title=item.title,
                                         url=url,
                                         action='play',
                                         quality = quality,
                                         language = language,
                                         server=server,
                                         subtitle = sub
                                         ))


    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle
                 ))

    return video_list

