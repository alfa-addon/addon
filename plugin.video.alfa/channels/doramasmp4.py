# -*- coding: utf-8 -*-
# -*- Channel DoramasMP4 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

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

host = 'https://www.doramasmp4.com/'

IDIOMAS = {'sub': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload', 'streamango', 'netutv', 'okru', 'directo', 'mp4upload']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel= item.channel, title="Doramas", action="doramas_menu",
                         thumbnail=get_thumb('doramas', auto=True), type='dorama'))
    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         url=host + 'catalogue?type[]=pelicula', thumbnail=get_thumb('movies', auto=True),
                         type='movie'))
    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url= host+'search?q=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def doramas_menu(item):
    logger.info()

    itemlist =[]

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'catalogue',
                         thumbnail=get_thumb('all', auto=True), type='dorama'))
    itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="latest_episodes",
                         url=host + 'latest-episodes', thumbnail=get_thumb('new episodes', auto=True), type='dorama'))
    return itemlist

def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    patron = '<a class=item_episode href=(.*?) title=.*?<img src=(.*?) title=.*?title>(.*?)'
    patron += '</div> <div class=options> <span>(.*?)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedtype in matches:
        url = scrapedurl
        scrapedtype = scrapedtype.lower()
        scrapedtitle = scrapedtitle
        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url,
                        thumbnail=thumbnail, type=scrapedtype)
        if scrapedtype != 'dorama':
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle

        else:
            new_item.contentSerieName=scrapedtitle
            new_item.action = 'episodes'
        itemlist.append(new_item)


    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        if item.type != 'dorama':
            page_base = host+'catalogue?type[]=pelicula'
        else:
            page_base = host + 'catalogue'
        next_page = scrapertools.find_single_match(data, '<a href=([^ ]+) aria-label=Netx>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                                 url=page_base+next_page, thumbnail='https://s16.postimg.org/9okdu7hhx/siguiente.png',
                                 type=item.type))
    return itemlist


def latest_episodes(item):
    logger.info()
    itemlist = []
    infoLabels = dict()
    data = get_source(item.url)

    patron = '<a class=episode href=(.*?) title=.*?<img src=(.*?) title=.*?title>(.*?)</div>.*?episode>(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedep in matches:
        title = '%s %s' % (scrapedtitle, scrapedep)
        contentSerieName = scrapedtitle
        itemlist.append(Item(channel=item.channel, action='findvideos', url=scrapedurl, thumbnail=scrapedthumbnail,
                             title=title, contentSerieName=contentSerieName, type='episode'))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def episodes(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<li class=link_episode><a itemprop=url href=(.*?) title=.*?itemprop=name>(.*?)'
    patron += '</span></a><meta itemprop=episodeNumber content=(.*?) /></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels

    for scrapedurl, scrapedtitle, scrapedep in matches:
        url = scrapedurl
        contentEpisodeNumber = scrapedep

        infoLabels['season'] = 1
        infoLabels['episode'] = contentEpisodeNumber

        if scrapedtitle != '':
            title = scrapedtitle
        else:
            title = 'episodio %s' % scrapedep

        infoLabels = item.infoLabels

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             contentEpisodeNumber=contentEpisodeNumber, type='episode', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    duplicated = []
    data = get_source(item.url)
    if item.type !='episode' and '<meta property=article:section content=Pelicula>' not in data:
        item.type = 'dorama'
        item.contentSerieName = item.contentTitle
        item.contentTitle = ''
        return episodes(item)
    else:
        itemlist.extend(servertools.find_video_items(data=data))
        for video_item in itemlist:
            if 'sgl.php' in video_item.url:
                headers = {'referer': item.url}
                patron_gvideo = "'file':'(.*?)','type'"
                data_gvideo = httptools.downloadpage(video_item.url, headers=headers).data
                video_item.url = scrapertools.find_single_match(data_gvideo, patron_gvideo)

            duplicated.append(video_item.url)
            video_item.channel = item.channel
            video_item.infoLabels = item.infoLabels
            video_item.language=IDIOMAS['sub']

        patron = 'var item = {id: (\d+), episode: (\d+),'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for id, episode in matches:
            data_json=jsontools.load(httptools.downloadpage(host+'/api/stream/?id=%s&episode=%s' %(id, episode)).data)
            sources = data_json['options']
            for src in sources:
                url = sources[src]

                if 'sgl.php' in url:
                    headers = {'referer':item.url}
                    patron_gvideo = "'file':'(.*?)','type'"
                    data_gvideo = httptools.downloadpage(url, headers = headers).data
                    url = scrapertools.find_single_match(data_gvideo, patron_gvideo)

                new_item = Item(channel=item.channel, title='%s', url=url, language=IDIOMAS['sub'], action='play',
                                infoLabels=item.infoLabels)
                if url != '' and url not in duplicated:
                    itemlist.append(new_item)
                    duplicated.append(url)
        try:
            itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
        except:
            pass


        # Requerido para FilterTools

        itemlist = filtertools.get_links(itemlist, item, list_language)

        # Requerido para AutoPlay

        autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'search'
    if texto != '':
        return list_all(item)
