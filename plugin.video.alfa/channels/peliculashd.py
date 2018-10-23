# -*- coding: utf-8 -*-
# -*- Channel PeliculasHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import base64

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from lib import jsunpack
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'Latino': 'Latino', 'Español': 'Castellano', 'VOSE': 'VOSE'}
list_language = IDIOMAS.values()

list_quality = []

list_servers = [
    'directo',
    'openload',
    'rapidvideo'
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'peliculashd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'peliculashd')

host = 'https://peliculashd.site/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'/genero/serie', action='list_all', type='tvshows',
                         thumbnail= get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Anime', url=host + '/genero/anime', action='list_all', type='tvshows',
                         thumbnail=get_thumb('anime', auto=True)))

    itemlist.append(
        Item(channel=item.channel, title='Telenovelas', url=host + '/genero/telenovelas-teleseries', action='list_all', type='tvshows',
             thumbnail=get_thumb('telenovelas', auto=True)))

    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + '?s=', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
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
    duplicados=[]
    full_data = get_source(host+'/'+item.type)
    if 'Genero' in item.title:
        data = scrapertools.find_single_match(full_data, '<a>Generos</a>(.*?)</ul>')
    elif 'Año' in item.title:
        data = scrapertools.find_single_match(full_data, '<h2>Busqueda por Año</h2>(.*?)</ul>')
    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        plot=''
        title = scrapedtitle
        url = scrapedurl
        if title not in duplicados and title.lower() != 'proximamente':
            itemlist.append(Item(channel=item.channel, url=url, title=title, plot=plot, action='list_all',
                                 type=item.type))
            duplicados.append(title)

    return itemlist

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    if item.type ==  'movies':
        patron = '<article id="post-\d+" class="item movies"><div class="poster">\s?<img src="([^"]+)" alt="([^"]+)">.*?'
        patron += '"quality">([^<]+)</span><\/div>\s?<a href="([^"]+)">.*?</h3>.*?<span>([^<]+)</'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedtitle, quality, scrapedurl, year in matches:


            title = '%s [%s] [%s]' % (scrapedtitle, year, quality)
            contentTitle = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='findvideos',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentTitle=contentTitle,
                            quality=quality,
                            infoLabels={'year':year}))

    elif item.type ==  'tvshows':
        patron = '<article id="post-\d+" class="item tvshows"><div class="poster">\s?<img src="([^"]+)" alt="([^"]+)">.*?'
        patron += '<\/div>\s?<a href="([^"]+)">.*?</h3>.*?<span>([^<]+)</'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:
            title = scrapedtitle
            contentSerieName = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='seasons',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentSerieName=contentSerieName,
                            infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    #url_next_page = scrapertools.find_single_match(data,"<a class='arrow_pag' href=([^>]+)><i id='nextpagination'")
    url_next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^ ]+)" />')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='Temporada \d+'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        season = season.lower().replace('temporada','')
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
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
    patron='class="numerando">%s - (\d+)</div><div class="episodiotitle">.?<a href="([^"]+)">([^<]+)<' % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedepisode, scrapedurl, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', type='tv',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()
    from lib import generictools
    import urllib
    itemlist = []
    data = get_source(item.url)
    patron = 'data-post="(\d+)" data-nume="(\d+).*?class="title">([^>]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for pt, nm, language in matches:

        if 'sub' in language.lower() or language not in IDIOMAS:
            language = 'VOSE'
        post = {'action': 'doo_player_ajax', 'post': pt, 'nume': nm}
        post = urllib.urlencode(post)
        new_data = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=post,
                                          headers={'Referer': item.url}).data
        hidden_url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        new_data = get_source(hidden_url)
        matches = scrapertools.find_multiple_matches(new_data, '\["\d+","([^"]+)",\d+\]')
        for url in matches:
            if not config.get_setting('unify'):

                title = ' [%s]' % IDIOMAS[language]

            else:
                title = ''
            url = url.replace('\\/', '/')
            if 'playdrive' in url:
                new_data = get_source(url)
                url = scrapertools.find_single_match(new_data, 'file:"([^"]+)"')
            itemlist.append(Item(channel=item.channel, title='%s' + title, url=url, action='play',
                                 language=IDIOMAS[language], infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron = '<article>.*?<a href="([^"]+)">.?<img src="([^"]+)" alt="([^"]+)" />.?<span class="(tvshows|movies)".*?'
    patron += '"meta".*?"year">([^<]+)<(.*?)<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle, type, year, lang_data, scrapedplot in matches:

        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb
        plot = scrapedplot
        language = get_language(lang_data)
        if language:
            action = 'findvideos'
        else:
            action = 'seasons'

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             action=action, type=type, language=language, infoLabels={'year':year})
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
            item.url = host + 'movies/'
        elif categoria == 'infantiles':
            item.url = host + 'genero/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genero/terror/'
        elif categoria == 'anime':
            item.url = host + 'genero/anime/'
        item.type='movies'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
