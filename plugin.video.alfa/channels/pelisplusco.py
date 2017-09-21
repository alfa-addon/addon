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


audio = {'Latino':'[COLOR limegreen]LATINO[/COLOR]', 'Subtitulado':'[COLOR red]Subtitulado[/COLOR]'}

host = 'http://pelisplus.co'

def mainlist(item):
    logger.info()

    itemlist = []
    
    itemlist.append(item.clone(title="Estrenos",
                               action="lista",
                               thumbnail='https://s12.postimg.org/iygbg8ip9/todas.png',
                               fanart='https://s12.postimg.org/iygbg8ip9/todas.png',
                               url = host+'/estrenos/',
                               type = 'normal'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               thumbnail='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               seccion='generos'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host,
                               thumbnail='https://s8.postimg.org/7eoedwfg5/pora_o.png',
                               fanart='https://s8.postimg.org/7eoedwfg5/pora_o.png',
                               seccion='anios'
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

    if item.type not in ['normal', 'seccion']:
        post = {'page':item.page, 'type':item.type,'id':item.id}
        post = urllib.urlencode(post)
        logger.debug('post: %s'%post)
        data =httptools.downloadpage(item.url, post=post).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    else:
        data = get_source(item.url)
    logger.debug (data)
    #return
    patron = '<div class=item-pelicula><a href=(.*?)><figure><img src=https:(.*?)'
    patron += ' alt=><\/figure><p>(.*?)<\/p><span>(.*?)<\/span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        url = host+scrapedurl
        thumbnail = scrapedthumbnail
        plot= ''
        contentTitle=scrapedtitle
        title = contentTitle
        year = scrapedyear
        fanart =''
        
        itemlist.append(item.clone(action='findvideos' ,
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   plot=plot,
                                   fanart=fanart,
                                   contentTitle = contentTitle,
                                   infoLabels ={'year':year}
                                       ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb =True)
 #Paginacion

    next_page_valid = scrapertools.find_single_match(data, '<div class=butmore page=(.*?) id=(.*?) type=(.*?) '
                                                          'limit=.*?>')
    if item.type != 'normal' and (len(itemlist)>19 or next_page_valid):
        if next_page_valid:
            page = str(int(next_page_valid[0])+1)
            id = next_page_valid[1]
            type = next_page_valid[2]
        else:
            page = str(int(item.page)+1)
            id = item.id
            type = item.type
        url = host+'/pagination'
        itemlist.append(item.clone(action = "lista",
                                   title = 'Siguiente >>>',
                                   page=page,
                                   url = url,
                                   id = id,
                                   type = type,
                                   thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'
                                   ))
    return itemlist

def seccion(item):
    logger.info()
    itemlist = []
    post = dict()
    data = get_source(item.url)
    logger.debug('data: %s'%data)
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

        thumbnail = ''
        fanart = ''
        url = host+scrapedurl

        itemlist.append(
            Item(channel=item.channel,
                 action="lista",
                 title=title,
                 fulltitle=item.title,
                 url=url,
                 thumbnail=thumbnail,
                 fanart=fanart,
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


def findvideos(item):
    logger.info()
    itemlist = []
    templist = []
    video_list = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    logger.debug('data findvideos: %s'%data)
    patron = 'data-iframe=0><a>(.*?) - (.*?)<.*?data-source=(.*?) data.*?-srt=(.*?) '
    matches = matches = re.compile(patron, re.DOTALL).findall(data)

    for language, quality, url, sub in matches:
        logger.debug('url: %s'%url)

        if 'http' not in url :

            new_url = 'https://onevideo.tv/api/player?key=90503e3de26d45e455b55e9dc54f015b3d1d4150&link' \
                      '=%s&srt=%s' % (url, sub)
            headers = {'Referer':new_url}
            data = httptools.downloadpage(new_url, headers = headers).data
            data = re.sub(r'\\', "", data)
            logger.debug('one video: %s'%data)
            video_list.extend(servertools.find_video_items(data=data))

            for video_url in video_list:
                video_url.channel = item.channel
                video_url.action = 'play'
                #video_url.title = item.title + '(%s) (%s)' % (language, video_url.server)
                video_url.title = video_url.url
                video_url.quality = quality
                video_url.language = language
                video_url.subtitle = sub
                video_url.contentTitle=item.title
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
# def findvideos(item):
#     logger.info()
#     itemlist=[]
#     data = get_source(item.url)
#     logger.debug (data)
#     patron = 'data-srt=(.*?) data-iframe=0 data-source=(.*?)><a>(.*?) - 1080p<\/a>'
#     #sub = scrapertools.find_single_match('')
#     matches = re.compile(patron, re.DOTALL).findall(data)
#
#     for sub, id, lang in matches:
#         new_url = 'http://iplay.one/api/embed?id=%s&token=8908d9f846&%s' % (id, sub)
#         data= get_source(new_url)
#         logger.debug(data)
#         patron = 'file:(.*?),label:(.*?),'
#         matches = re.compile(patron, re.DOTALL).findall(data)
#         for scrapedurl, quality in matches:
#             url = scrapedurl
#
#             title = item.contentTitle+' (%s) (%s)'%(quality, audio[lang])
#             itemlist.append(item.clone(action='play',
#                                  url=scrapedurl,
#                                  title=title,
#                                  quality=quality,
#                                  language=lang,
#                                  subtitle=sub
#                                  ))
#
#
#     return itemlist

