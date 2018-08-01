# -*- coding: utf-8 -*-
# -*- Channel SeriesBlanco -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://seriesblanco.xyz/'

IDIOMAS = {'es': 'Cast', 'la': 'Lat', 'vos': 'VOSE', 'vo': 'VO'}
list_language = IDIOMAS.values()
list_quality = ['SD', 'Micro-HD-720p', '720p', 'HDitunes', 'Micro-HD-1080p' ]
list_servers = ['powvideo','yourupload', 'openload', 'gamovideo', 'flashx', 'clipwatching', 'streamango', 'streamcloud']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="Nuevos Capitulos",
                         action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True),
                         url=host))

    itemlist.append(Item(channel=item.channel,
                         title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url=host + 'listado/',
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="section",
                         thumbnail=get_thumb('genres', auto=True),
                         url=host,
                         ))

    itemlist.append(Item(channel=item.channel,
                         title="A - Z",
                         action="section",
                         thumbnail=get_thumb('alphabet', auto=True),
                         url=host+'listado/', ))

    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    contentSerieName = ''

    patron = "<div style='float.*?<a href='(.*?)'>.*?src='(.*?)' title='(.*?)'"
    matches = re.compile(patron, re.DOTALL).findall(data)


    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:

        url = host + scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=scrapedtitle,
                             context=filtertools.context(item, list_language, list_quality),
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # #Paginacion

    if itemlist != []:
        base_page = scrapertools.find_single_match(item.url,'(.*?)?')
        next_page = scrapertools.find_single_match(data, '</span><a href=?pagina=2>>></a>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="lista",
                                 title='Siguiente >>>',
                                 url=base_page+next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 ))
    return itemlist

def section(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    if item.title == 'Generos':
        patron = '<li><a href=([^ ]+)><i class=fa fa-bookmark-o></i> (.*?)</a></li>'
    elif item.title == 'A - Z':
        patron = "<a dir='ltr' href=(.*?) class='label label-primary'>(.*?)</a>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        if item.title == 'Generos':
            url = host + scrapedurl
        else:
            url = scrapedurl
        title = scrapedtitle
        itemlist.append(Item(channel=item.channel,
                             action='list_all',
                             title=title,
                             url=url
                             ))
    return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<span itemprop=seasonNumber class=fa fa-arrow-down>.*?Temporada (\d+) '
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels=item.infoLabels
    for scrapedseason in matches:
        url = item.url
        title = 'Temporada %s' % scrapedseason
        contentSeasonNumber = scrapedseason
        infoLabels['season'] = contentSeasonNumber
        thumbnail = item.thumbnail
        itemlist.append(Item(channel=item.channel,
                             action="episodesxseason",
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSeasonNumber=contentSeasonNumber,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             ))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)

    season = item.contentSeasonNumber
    season_data = scrapertools.find_single_match(data, '<div id=collapse%s.*?panel-primary' % season)
    patron = "<td><a href='([^ ]+)'.*?itemprop='episodeNumber'>%s+x(\d+)</span> - (.*?) </a>.*?(/banderas.*?)</td>" % season
    matches = re.compile(patron, re.DOTALL).findall(season_data)
    infoLabels = item.infoLabels
    for scrapedurl, scraped_episode, scrapedtitle, lang_data in matches:
        url = host + scrapedurl
        title = '%sx%s - %s' % (season, scraped_episode, scrapedtitle.strip())
        infoLabels['episode'] = scraped_episode
        thumbnail = item.thumbnail
        title, language = add_language(title, lang_data)
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             language=language,
                             infoLabels=infoLabels
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = filtertools.get_links(itemlist, item, list_language)

    return itemlist

def new_episodes(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = "padding-left:15px'><a href=(.*?) >.*?src='(.*?)' title=.*? alt='(.*?) (\d+x\d+)'.*?"
    patron += "<span class='strong'>.*?</span>(.*?)</button></a></div>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedinfo, lang_data in matches:


        url = host+scrapedurl
        thumbnail = scrapedthumbnail
        scrapedinfo = scrapedinfo.split('x')
        season = scrapedinfo[0]
        episode = scrapedinfo[1]
        title = '%s - %sx%s' % (scrapedtitle, season, episode )
        title, language = add_language(title, lang_data)
        itemlist.append(Item(channel=item.channel,
                             action='seasons',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             language=language,
                              ))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def add_language(title, string):
    logger.info()
    languages = scrapertools.find_multiple_matches(string, '/banderas/(.*?).png')
    language = []
    for lang in languages:

        if 'jap' in lang or lang not in IDIOMAS:
            lang = 'vos'

        if len(languages) == 1:
            language = IDIOMAS[lang]
            if not config.get_setting('unify'):
                title = '%s [%s]' % (title, language)
        else:
            language.append(IDIOMAS[lang])
            if not config.get_setting('unify'):
                title = '%s [%s]' % (title, IDIOMAS[lang])

    return title, language


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)

    patron = "<a href=([^ ]+) target=_blank><img src='/servidores/(.*?).(?:png|jpg)'.*?sno.*?"
    patron += "<span>(.*?)<.*?(/banderas.*?)td"
    matches = re.compile(patron, re.DOTALL).findall(data)


    for scrapedurl, server, quality, lang_data in matches:

        title = server.capitalize()
        if quality == '':
            quality = 'SD'
        title = '%s [%s]' % (title, quality)
        title, language = add_language(title, lang_data)
        thumbnail = item.thumbnail

        enlace_id, serie_id, se, ep = scrapertools.find_single_match(scrapedurl,'enlace(\d+)/(\d+)/(\d+)/(\d+)/')

        url = host + 'ajax/load_enlace.php?serie=%s&temp=%s&cap=%s&id=%s' % (serie_id, se, ep, enlace_id)
        itemlist.append(Item(channel=item.channel,
                             title=title,
                             url=url,
                             action="play",
                             thumbnail=thumbnail,
                             server=server,
                             quality=quality,
                             language=language,
                             infoLabels=item.infoLabels
                             ))
    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return sorted(itemlist, key=lambda it: it.language)


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, follow_redirects=False).data
    itemlist = servertools.find_video_items(data=data)
    for videoitem in itemlist:
        videoitem.infoLabels = item.infoLabels


    return itemlist

def search_results(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'finder.php', post=item.post).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = "<a href='(.*?)'>.*?src=(.*?) style.*?value=(.*?)>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel,
                             title=scrapedtitle,
                             url=host+scrapedurl,
                             action="seasons",
                             thumbnail=scrapedthumb,
                             contentSerieName=scrapedtitle,
                             context=filtertools.context(item, list_language, list_quality)
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def search(item, texto):
    logger.info()
    import urllib
    if texto != '':
        post = {'query':texto}
        post = urllib.urlencode(post)
        item.post = post

        return search_results(item)
