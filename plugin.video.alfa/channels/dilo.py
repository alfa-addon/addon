# -*- coding: utf-8 -*-
# -*- Channel Dilo -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido
    import urllib

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

host = 'https://www.dilo.nu/'

IDIOMAS = {'Español': 'CAST', 'Latino': 'LAT', 'Subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['openload', 'streamango', 'powvideo', 'clipwatching', 'streamplay', 'streamcherry', 'gamovideo']

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url, forced_proxy_opt='ProxyWeb').data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos capitulos", action="latest_episodes", url=host,
                         page=0, thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Ultimas", action="list_all",  url=host + 'catalogue?sort=latest',
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Mas vistas", action="list_all", url=host + 'catalogue?sort=most-week',
                         thumbnail=get_thumb('more watched', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + 'catalogue',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         url=host + 'catalogue', thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por Años", action="section", url=host + 'catalogue',
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Por País", action="section", url=host + 'catalogue',
                         thumbnail=get_thumb('country', auto=True)))

    itemlist.append(Item(channel=item.channel, title = 'Buscar', action="search", url= host+'search?s=',
                         thumbnail=get_thumb('search', auto=True)))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<div class="col-lg-2 col-md-3 col-6 mb-3"><a href="([^"]+)".*?<img src="([^"]+)".*?'
    patron += 'font-weight-500">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = urlparse.urljoin(host, scrapedurl)
        scrapedtitle = scrapedtitle
        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, title=scrapedtitle, url=url,
                        thumbnail=thumbnail)

        new_item.contentSerieName = scrapedtitle
        new_item.action = 'seasons'
        new_item.context = filtertools.context(item, list_language, list_quality)
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:

        page_base = host + 'catalogue'
        next_page = scrapertools.find_single_match(data, '<a href="([^ ]+)" aria-label="Netx">')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="list_all", title='Siguiente >>>',
                                 url=page_base+next_page, thumbnail=get_thumb("more.png"),
                                 type=item.type))
    return itemlist



def section(item):
    logger.info()

    itemlist = []
    data=get_source(item.url)

    patron = 'input" id="([^"]+)".*?name="([^"]+)".*?'
    patron += '<label.*?>([^<]+)</label>'

    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, '>Todos los generos</button>.*?<button class')
    elif 'Años' in item.title:
        data = scrapertools.find_single_match(data, '>Todos los años</button>.*?<button class')

    elif 'País' in item.title:
        data = scrapertools.find_single_match(data, '>Todos los países</button>.*?<button class')

    matches = re.compile(patron, re.DOTALL).findall(data)

    for id, name, title in matches:
        id = id.replace('-','+')
        url = '%s?%s=%s' % (item.url, name, id)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='list_all'))

    return itemlist


def latest_episodes(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<a class="media" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?'
    patron += 'width: 97%">([^<]+)</div><div>(\d+x\d+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    logger.info("page=%s" % item.page)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedcontent, scrapedep in matches[item.page:item.page + 30]:
        title = '%s' % (scrapedtitle.replace(' Online sub español', ''))
        contentSerieName = scrapedcontent
        itemlist.append(Item(channel=item.channel, action='findvideos', url=urlparse.urljoin(host, scrapedurl), thumbnail=scrapedthumbnail,
                             title=title, contentSerieName=contentSerieName, type='episode'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color="yellow"))
    else:
        next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
        if next_page:
            itemlist.append(item.clone(url=next_page, page=0, title="» Siguiente »", text_color="0xFF994D00"))


    return itemlist

def latest_shows(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    data = scrapertools.find_single_match(data, '>Nuevas series</div>.*?text-uppercase"')
    patron = '<div class="col-lg-3 col-md-4 col-6 mb-3"><a href="([^"]+)".*?src="([^"]+)".*?weight-500">([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapedtitle
        contentSerieName = scrapedtitle
        itemlist.append(Item(channel=item.channel, action='seasons', url=urlparse.urljoin(host, scrapedurl), thumbnail=scrapedthumbnail,
                             title=title, contentSerieName=contentSerieName))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    serie_id = scrapertools.find_single_match(data, '{"item_id": (\d+)}')
    post = {'item_id': serie_id}
    post = urllib.urlencode(post)
    seasons_url = '%sapi/web/seasons.php' % host
    headers = {'Referer':item.url}
    data = httptools.downloadpage(seasons_url, post=post, headers=headers).json
    infoLabels = item.infoLabels
    for dict in data:
        season = dict['number']

        if season != '0':
            infoLabels['season'] = season
            title = 'Temporada %s' % season
            itemlist.append(Item(channel=item.channel, url=item.url, title=title, action='episodesxseason',
                                 contentSeasonNumber=season, id=serie_id, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodesxseason(item):
    logger.info()
    logger.info()

    itemlist = []
    season = item.infoLabels['season']
    post = {'item_id': item.id, 'season_number': season}
    post = urllib.urlencode(post)

    seasons_url = '%sapi/web/episodes.php' % host
    headers = {'Referer': item.url}
    data = httptools.downloadpage(seasons_url, post=post, headers=headers).json
    infoLabels = item.infoLabels
    for dict in data:
        episode = dict['number']
        epi_name = dict['name']
        title = '%sx%s - %s' % (season, episode, epi_name)
        url = '%s%s/' % (host, dict['permalink'])
        infoLabels['episode'] = episode
        itemlist.append(Item(channel=item.channel, title=title, action='findvideos', url=url,
                             contentEpisodeNumber=episode, id=item.id, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'data-link="([^"]+)">.*?500">([^<]+)<.*?>Reproducir en ([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for enc_url, server, language in matches:
        if not config.get_setting('unify'):
            title = ' [%s]' % language
        else:
            title = ''

        itemlist.append(Item(channel=item.channel, title='%s'+title, url=urlparse.urljoin(host, enc_url), action='play',
                              language=IDIOMAS[language], server=server, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist



def decode_link(enc_url):
    logger.info()
    url = ""
    try:
        #new_data = get_source(enc_url)
        new_data = httptools.downloadpage(enc_url).data
        if "gamovideo" in enc_url:
            url = scrapertools.find_single_match(new_data, '<a href="([^"]+)"')
        else:
            new_enc_url = scrapertools.find_single_match(new_data, 'src="([^"]+)"')

            try:
                url = httptools.downloadpage(new_enc_url, follow_redirects=False).headers['location']
            except:
                if not 'jquery' in new_enc_url:
                    url = new_enc_url
    except:
        pass
    return url


def play(item):
    logger.info()
    itemlist = []
    if item.server not in ['openload', 'streamcherry', 'streamango']:
        item.server = ''
    item.url = decode_link(item.url)
    if not item.url:
        return []
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist

def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist
