# -*- coding: utf-8 -*-
import sys
import re
import datetime

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

from bs4 import BeautifulSoup
from core import httptools, scrapertools, servertools
from core.item import Item
from platformcode import config, logger, platformtools
from channelselector import get_thumb
from modules import autoplay
from lib import strptime_fix

IDIOMAS = {'VOSE': 'VOSE', 'CAST': 'CAST'}

list_language = list(IDIOMAS.values())
list_servers = ['streamsb', 'fembed', 'uqload', 'streamtape', 'videobin', 'mp4upload']
list_quality = []

meses = {'Enero':    1, 'Febrero':    2, 'Marzo':       3,
         'Abril':    4, 'Mayo':       5, 'Junio':       6,
         'Julio':    7, 'Agosto':     8, 'Septiembre':  9,
         'Octubre': 10, 'Noviembre': 11, 'Diciembre':  12}

canonical = {
             'channel': 'yohentai', 
             'host': config.get_setting("current_host", 'yohentai', default=''), 
             'host_alt': ["https://yohentai.net/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)

    # itemlist.append(
        # Item(
            # action = "recent",
            # channel = item.channel,
            # title = "Recientes",
            # thumbnail = get_thumb("recents", auto=True),
            # viewType = "tvshows"
        # )
    # )
    # itemlist.append(
        # Item(
            # action = "list_all",
            # channel = item.channel,
            # list_type = "newepisodes",
            # title = "Nuevos episodios",
            # thumbnail = get_thumb("new episodes", auto=True),
            # url = host,
            # viewType = "episodes"
        # )
    # )
    # itemlist.append(
        # Item(
            # action = "list_all",
            # channel = item.channel,
            # list_type = "onair",
            # title = "En emisión",
            # thumbnail = get_thumb("on air", auto=True),
            # url = "{}emision".format(host),
            # viewType = "tvshows"
        # )
    # )
    
    # itemlist.append(
        # Item(
            # action = "list_all",
            # channel = item.channel,
            # list_type = "popular",
            # title = "Populares",
            # thumbnail = get_thumb("hot", auto=True),
            # url = "{}search?p=1".format(host),
            # viewType = "tvshows"
        # )
    # )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            list_type = "all",
            title = "Todos los hentai",
            thumbnail = get_thumb("all", auto=True),
            url = "{}search".format(host),
            viewType = "tvshows"
        )
    )
    itemlist.append(
        Item(
            action = "genres",
            channel = item.channel,
            list_type = "genres",
            title = "Géneros",
            thumbnail = get_thumb("genres", auto=True),
            url = "{}search".format(host),
            viewType = "tvshows"
        )
    )
    itemlist.append(
        Item(
            action = "genres",
            channel = item.channel,
            list_type = "year",
            title = "Año",
            thumbnail = get_thumb("year", auto=True),
            url = "{}search".format(host),
            viewType = "tvshows"
        )
    )
    # itemlist.append(
        # Item(
            # action = "genres",
            # channel = item.channel,
            # list_type = "status",
            # title = "Estado",
            # thumbnail = get_thumb("on air", auto=True),
            # url = "{}search".format(host),
            # viewType = "tvshows"
        # )
    # )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            list_type = "all",
            title = "Buscar",
            thumbnail = get_thumb("search", auto=True),
            url = "{}search".format(host),
            viewType = "tvshows"
        )
    )
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def setting_channel(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret

def get_source(url, soup=True, post=None, headers=None):
    logger.info()

    data = httptools.downloadpage(url, post=post, headers=headers, canonical=canonical).data
    if soup:
        return BeautifulSoup(data, "html5lib")
    else:
        return data

def setEpisodeData(item, title):
    logger.info()

    title = title.lower()

    language = ""
    if 'castellano' in title:
        language = "CAST"
        title = title.replace('castellano', '')
    else:
        language = "VOSE"

    epname = title.replace('sub español', '').replace(item.title.lower(), '').strip()
    epnum = int(scrapertools.find_single_match(epname, '\d+'))
    title = "Episodio {} [{}]".format(epnum, language)

    return title, epnum, language

def formatDate(scpdate):
    # Capturamos cada componente
    scpdate = scrapertools.find_multiple_matches(scpdate, '(\d+) de (\w+) (\d+)')
    if len(scpdate) > 0:
        scpdate = scpdate[0]
        # Rearmamos la fecha pero con mes en inglés
        scpdate = "{}/{}/{}".format(scpdate[0], meses.get(scpdate[1], 'January'), scpdate[2])
        # Creamos la fecha
        return datetime.datetime.strptime(scpdate, "%d/%m/%Y")
    else:
        return None

def recent(categoria):
    item = Item(
        action = "recent",
        channel = "yohentai",
        list_type = "recent",
        thumbnail = get_thumb("recents", auto=True),
        title = "Recientes",
        url = host,
        viewType = "videos"
        )
    return list_all(item)

def genres(item):
    logger.info()

    itemlist = []
    soup = get_source(item.url).find_all('div', class_='my-3')
    if item.list_type == 'genres':
        genres = soup[0].find_all('label')
    elif item.list_type == 'year':
        genres = soup[2].find_all('label')
    # elif item.list_type == 'status':
        # genres = [x for x in soup.find('div', class_='estados_ls').find_all('a') if x.get('href') != ""]

    for g in genres:
        
        id = g['for'].replace("cb_", "").replace("cba_", "")
        title = g.text
        if item.list_type == 'year':
            year = id
            genre = ""
        else:
            genre = id
            year = ""
        
        itemlist.append(
            item.clone(
                action = 'list_all',
                title = title,
                url = '{}search?genero={}&fecha={}&p=1'.format(host, genre, year)
            )
        )
    
    if item.list_type == 'genres': itemlist.sort(key=lambda x: x.title)
    
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []
    soup = get_source(item.url)
    
    if item.list_type == "recent":
        section = soup.find('div', class_='tvLast').find_all('div', class_='inner_tv')
    else:
        section = soup.find('div', class_='container-lg').find_all('li', class_='col')
    
    for div in section:
        infoLabels = {}
        infoLabels['year'] = int(div.find('span', class_='text-muted').text) if div.find('span', class_='text-muted') else None
        infoLabels['episode'] = int(div.find('span', class_='episode').text) if div.find('span', class_='episode') else None
        action = "episodesxseason" if item.list_type != "newepisodes" else "findvideos"
        contentTitle = div.h2.text if item.list_type == "newepisodes" else div.h2.text
        title = "E{}: {}".format(infoLabels['episode'], contentTitle) if infoLabels.get('episode') is not None else contentTitle
        thumbnail = div.img['data-src'] if item.list_type in ["recent", "newepisodes"] else div.img['data-src']
        url = div.a['href']
        
        itemlist.append(
            Item(
                action = action,
                channel = item.channel,
                contentSerieName = contentTitle,
                fanart = thumbnail,
                infoLabels = infoLabels,
                title = title,
                thumbnail = thumbnail,
                url = url,
                viewType = "episodes"
            )
        )
    
    nextpage = soup.find('ul', class_='pagination')
    if nextpage:
        nextpage = nextpage.find_all('a')[-1]['href']
        itemlist.append(
            Item(
                action = 'list_all',
                channel =  item.channel,
                fanart = item.fanart,
                list_type = item.list_type,
                text_color = "yellow",
                title =  'Siguiente página >',
                url = nextpage #"{}{}".format(url, nextpage.parent['href'])
            )
        )
    
    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    itemlist.extend(episodesxseason(item, True))
    return itemlist

def episodesxseason(item, get_episodes = False):
    logger.info()
    itemlist = []
    
    soup = get_source(item.url)
    fanart = soup.select_one('.Banner').find('img')['src'] if soup.select_one('.Banner') else None
    
    item.infoLabels['plot'] = soup.find('div', class_='mb-3').text.strip()
    item.infoLabels['season'] = 1
    
    genmatch = [x.text.strip() for x in soup.find('div', class_='lh-lg').find_all('a')]
    # genmatch.append(item.infoLabels['status'])
    
    if len(genmatch):
        item.infoLabels['genre'] = ", ".join(genmatch)
        item.infoLabels['plot'] = "[COLOR yellow]Géneros:[/COLOR] {}\n\n{}".format(item.infoLabels['genre'], item.infoLabels['plot'])
    
    url = soup.find('div', class_='caplist')['data-ajax']
    token = soup.find(attrs={'name': 'csrf-token'})['content']
    post= {'_token': token, 'order': 1}
    headers=''
    
    data = httptools.downloadpage(url, post=post, headers=headers, canonical=canonical).json
    matches = data['eps']
    for match in matches:
        infoLabels = item.infoLabels
        cap = match['num']
        title = "%sx%s" % (item.infoLabels['season'], cap)
        infoLabels["episode"] = cap
        name = item.url.split("/")[-1]
        name = name.replace("sub-espanol", "")
        name += "capitulo-%s" % cap
        url = "%sver/%s" %(host, name)
        itemlist.append(
            item.clone(
                action = "findvideos",
                channel = item.channel,
                contentTitle = item.title,
                fanart = fanart,
                infoLabels = infoLabels,
                language = "",
                title = title,
                url = url
            )
        )

    # itemlist.reverse()

    if get_episodes == False and config.get_videolibrary_support() and len(itemlist) > 0:
        if itemlist[0].infoLabels['tmdb_id']:
            itemlist.append(
                Item(
                    channel = item.channel,
                    title = '[COLOR yellow]{}[/COLOR]'.format(config.get_localized_string(30161)),
                    url = item.url,
                    action = "add_serie_to_library",
                    extra = "episodios",
                    contentSerieName = item.contentSerieName
                )
            )
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    pattern = 'src="(.+?)"'
    soup = get_source(item.url)
    matches = soup.find_all('li', id='play-video')
    for elem in matches:
        url = elem.button['data-player']
        import base64
        url = base64.b64decode(url).decode("utf8")
        itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    autoplay.start(itemlist, item)
    return itemlist


def search(item, text):
    logger.info()
    itemlist = []
    if text != '':
        try:
            results = httptools.downloadpage("{}ajax/search/{}".format(host, text)).json
            for result in results:
                itemlist.append(
                    Item(
                        action = "episodesxseason",
                        channel = item.channel,
                        contentSerieName = result['nombre'],
                        plot = result['sinopsis'],
                        thumbnail = '{}assets/img/serie/imagen/{}'.format(host, result['imagen']),
                        title = result['nombre'],
                        url = '{}hentai/{}'.format(host, result['seo']),
                        viewType = "episodes"
                    )
                )
            return itemlist
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
            return itemlist
