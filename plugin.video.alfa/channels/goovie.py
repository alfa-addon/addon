# -*- coding: utf-8 -*-
# -*- Channel Goovie -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'1':'Cast', '2':'Lat', '3':'VOSE', '4':'VO'}
list_language = IDIOMAS.values()

CALIDADES = {'1':'1080','2':'720','3':'480','4':'360'}

list_quality = ['1080', '720', '480', '360']

list_servers = [
    'powvideo'
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'goovie')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'goovie')

host = 'https://goovie.co/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', type='peliculas',
                         thumbnail= get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', action='sub_menu', type='series',
                         thumbnail= get_thumb('tvshows', auto=True)))
    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + 'search?go=', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + item.type, action='list_all',
                         thumbnail=get_thumb('all', auto=True), type=item.type))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type=item.type))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type=item.type))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def get_language(lang_data):
    logger.info()
    language = []

    lang_list = scrapertools.find_multiple_matches(lang_data, '/flags/(.*?).png\)')
    for lang in lang_list:
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    return language

def section(item):
    logger.info()
    itemlist=[]
    data = get_source(host+item.type)

    if 'Genero' in item.title:
        data = scrapertools.find_single_match(data, 'genero.*?</ul>')
    elif 'Año' in item.title:
        data = scrapertools.find_single_match(data, 'año.*?</ul>')
    patron = '<a href=(.*?) >(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        itemlist.append(Item(channel=item.channel, url=scrapedurl, title=title, action='list_all',
                                 type=item.type))
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    #logger.debug(data)
    #return
    if item.type ==  'peliculas':
        patron = '<article class=Items>.*?<img src=(.*?) />.*?<a href=(.*?)><h2>(.*?)</h2>.*?'
        patron += "<p>(.*?)</p><span>(\d{4}) /.*?</span>.*?'(\d+)'"
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedurl, scrapedtitle, scrapedplot, year, video_id in matches:

            title = '%s [%s]' % (scrapedtitle, year)
            contentTitle = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='findvideos',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentTitle=contentTitle,
                            video_id=video_id,
                            infoLabels={'year':year}))

    elif item.type ==  'series':
        patron = '<article class=GoItemEp>.*?<a href=(.*?)>.*?<img src=(.*?) />.*?'
        patron +='<h2>(.*?)</h2><p>(.*?)</p><span>(\d{4}) /'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot, year in matches:
            title = scrapedtitle
            contentSerieName = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='seasons',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            plot=scrapedplot,
                            contentSerieName=contentSerieName,
                            infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data,"<link rel=next href=(.*?) />")
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='<div class=season temporada-(\d+)>'
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

    data=get_source(item.url)
    logger.debug(data)
    patron= "ViewEpisode\('(\d+)', this\)><div class=num>%s - (\d+)</div>" % item.infoLabels['season']
    patron += ".*?src=(.*?) />.*?namep>(.*?)<span>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for video_id, scrapedepisode, scrapedthumbnail, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=item.url, thumbnail=scrapedthumbnail,
                             action='findvideos', video_id=video_id, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()
    from lib import jsunpack
    itemlist = []
    headers = {'referer':item.url}
    if item.video_id == '':
        find_id = get_source(item.url)
        #logger.debug(find_id)
        #return
        item.video_id = scrapertools.find_single_match(find_id, 'var centerClick = (\d+);')
    url = 'https://goovie.co/api/links/%s' % item.video_id
    data = httptools.downloadpage(url, headers=headers).data
    video_list = jsontools.load(data)
    for video_info in video_list:
        logger.debug(video_info)
        url = video_info['visor']
        plot = 'idioma: %s calidad: %s' % (video_info['idioma'], video_info['calidad'])
        data = httptools.downloadpage(url, headers=headers, follow_redirects=False).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        packed = scrapertools.find_single_match(data, '(eval\(.*?);var')
        unpacked = jsunpack.unpack(packed)
        logger.debug('unpacked %s' % unpacked)
        server = scrapertools.find_single_match(unpacked, "src:.'(http://\D+)/")
        id = scrapertools.find_single_match(unpacked, "src:.'http://\D+/.*?description:.'(.*?).'")
        if server == '':
            if 'powvideo' in unpacked:
                id = scrapertools.find_single_match(unpacked ,",description:.'(.*?).'")
                server= 'https://powvideo.net'
        url = '%s/%s' % (server, id)
        if server != '' and id != '':
            language = IDIOMAS[video_info['idioma']]
            quality = CALIDADES[video_info['calidad']]
            title = ' [%s] [%s]' % (language, quality)
            itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', language=language,
                                 quality=quality))

    itmelist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return sorted(itemlist, key=lambda i: i.language)


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.type = 'peliculas'
    if texto != '':
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    logger.debug(data)
    patron = '<article class=Items>.*?href=(.*?)>.*?typeContent>(.*?)<.*?'
    patron += '<img src=(.*?) />.*?<h2>(.*?)</h2><p>(.*?)</p><span>(\d{4})<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, content_type ,scrapedthumb, scrapedtitle, scrapedplot, year in matches:

        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb
        plot = scrapedplot
        if content_type != 'Serie':
            action = 'findvideos'
        else:
            action = 'seasons'

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             action=action, type=content_type, infoLabels={'year':year})
        if new_item.action == 'findvideos':
            new_item.contentTitle = new_item.title
        else:
            new_item.contentSerieName = new_item.title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'peliculas'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/generos/animación'
        elif categoria == 'terror':
            item.url = host + 'peliculas/generos/terror'
        item.type='peliculas'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
