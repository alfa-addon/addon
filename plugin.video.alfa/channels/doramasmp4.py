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

IDIOMAS = {'sub': 'VOSE', 'VO': 'VO'}
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
                         url=host + 'catalogue?format=pelicula', thumbnail=get_thumb('movies', auto=True),
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
    patron = '<div class=col-lg-2 col-md-3 col-6><a href=(.*?) title=.*?'
    patron += '<img src=(.*?) alt=(.*?) class=img-fluid>.*?bg-primary text-capitalize>(.*?)</span>'

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
                                 url=page_base+next_page, thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 type=item.type))
    return itemlist


def latest_episodes(item):
    logger.info()
    itemlist = []
    infoLabels = dict()
    data = get_source(item.url)
    patron = '<div class=col-lg-3 col-md-6 mb-2><a href=(.*?) title=.*?'
    patron +='<img src=(.*?) alt.*?truncate-width>(.*?)<.*?mb-1>(.*?)<'
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
    logger.debug(data)
    patron = '<a itemprop=url href=(.*?) title=.*? class=media.*?truncate-width>(.*?)<.*?'
    patron +='text-muted mb-1>Capítulo (.*?)</div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels

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
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodes", text_color='yellow'))
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []
    duplicated = []
    headers={'referer':item.url}
    data = get_source(item.url)
    logger.debug(data)
    patron = 'animated pulse data-url=(.*?)>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if '</strong> ¡Este capítulo no tiene subtítulos, solo audio original! </div>' in data:
        language = IDIOMAS['vo']
    else:
        language = IDIOMAS['sub']

    if item.type !='episode' and '<meta property=article:section content=Pelicula>' not in data:
        item.type = 'dorama'
        item.contentSerieName = item.contentTitle
        item.contentTitle = ''
        return episodes(item)
    else:

        for video_url in matches:
            video_data = httptools.downloadpage(video_url, headers=headers).data
            server = ''
            if 'Media player DMP4' in video_data:
                url = scrapertools.find_single_match(video_data, "sources: \[\{'file':'(.*?)'")
                server = 'Directo'
            else:
                url = scrapertools.find_single_match(video_data, '<iframe src="(.*?)".*?scrolling="no"')
            new_item = Item(channel=item.channel, title='[%s] [%s]', url=url, action='play', language = language)
            if server !='':
                new_item.server = server
            itemlist.append(new_item)

        # for video_item in itemlist:
        #     if 'sgl.php' in video_item.url:
        #         headers = {'referer': item.url}
        #         patron_gvideo = "'file':'(.*?)','type'"
        #         data_gvideo = httptools.downloadpage(video_item.url, headers=headers).data
        #         video_item.url = scrapertools.find_single_match(data_gvideo, patron_gvideo)
        #
        #     duplicated.append(video_item.url)
        #     video_item.channel = item.channel
        #     video_item.infoLabels = item.infoLabels
        #     video_item.language=IDIOMAS['sub']
        #
        # patron = 'var item = {id: (\d+), episode: (\d+),'
        # matches = re.compile(patron, re.DOTALL).findall(data)
        #
        # for id, episode in matches:
        #     data_json=jsontools.load(httptools.downloadpage(host+'/api/stream/?id=%s&episode=%s' %(id, episode)).data)
        #     sources = data_json['options']
        #     for src in sources:
        #         url = sources[src]
        #
        #         if 'sgl.php' in url:
        #             headers = {'referer':item.url}
        #             patron_gvideo = "'file':'(.*?)','type'"
        #             data_gvideo = httptools.downloadpage(url, headers = headers).data
        #             url = scrapertools.find_single_match(data_gvideo, patron_gvideo)
        #
        #         new_item = Item(channel=item.channel, title='%s', url=url, language=IDIOMAS['sub'], action='play',
        #                         infoLabels=item.infoLabels)
        #         if url != '' and url not in duplicated:
        #             itemlist.append(new_item)
        #             duplicated.append(url)
        itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

        # Requerido para FilterTools

        itemlist = filtertools.get_links(itemlist, item, list_language)

        # Requerido para AutoPlay

        autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'search'
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist
