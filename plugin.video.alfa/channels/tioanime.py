# -*- coding: utf-8 -*-
# -*- Channel Tio TioAnime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from modules import filtertools
from modules import autoplay
from modules import renumbertools
from core import tmdb


IDIOMAS = {'vose': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['directo', 'fembed', 'okru',  'mailru', 'mega', 'youtupload']

canonical = {
             'channel': 'tioanime', 
             'host': config.get_setting("current_host", 'tioanime', default=''), 
             'host_alt': ["https://tioanime.com/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", url=host, action="new_episodes",
                         thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Emision",
                         url=host + 'directorio?type%5B%5D=0&year=1950%2C2020&status=1&sort=recent',
                         action="list_all", thumbnail=get_thumb('on air', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Ultimos", url=host+'directorio', action="list_all",
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Peliculas", url=host + 'directorio?type%5B%5D=1',
                         c_type="movie", action="list_all", thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title="OVAs", url=host + 'directorio?type%5B%5D=2',
                         action="list_all", thumbnail=""))

    itemlist.append(Item(channel=item.channel, title="Especiales", url=host + 'directorio?type%5B%5D=3',
                         action="list_all", thumbnail=""))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", url=host + 'directorio?q=', action="search",
                         thumbnail=get_thumb('search', auto=True)))
    
    itemlist = renumbertools.show_option(item.channel, itemlist)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def new_episodes(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("article", class_="episode")

    for elem in matches:
        url = host + elem.a["href"]
        title = elem.h3.text
        thumb = host + elem.figure.img["src"]

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             thumbnail=thumb, contentSerieName=title))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("article", class_="anime")
    
    if not item.c_type:
        item.c_type = "tvshow"

    for elem in matches:
        url = host + elem.a["href"]
        title = elem.h3.text
        thumb = host + elem.figure.img["src"]
        
        new_item = Item(channel=item.channel, title=title, url=url, 
                        action='episodios', thumbnail=thumb, infoLabels={'year': '-'})
        
        title, item.c_type = get_type_from_title(title, item.c_type)
        
        if item.c_type == "tvshow":
            title, season = get_season_from_title(title)
            new_item.contentSerieName = title
            new_item.contentSeason = season
            new_item.context = renumbertools.context(item)
            new_item.contentType = 'tvshow'
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = host + soup.find("a", rel="next")["href"]
        if url_next_page and len(itemlist) > 8:
            itemlist.append(item.clone(title="Siguiente >>", url=url_next_page))
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host + "directorio")
    matches = soup.find("select", id="genero").find_all("option")

    for elem in matches:
        title = elem.text
        url = "{0}directorio?genero%5B%5D={1}&year=1950%2C2020&status=2&sort=recent".format(host, elem["value"])

        itemlist.append(Item(channel=item.channel, url=url, title=title, action="list_all"))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    data = httptools.downloadpage(item.url, canonical=canonical).data

    info = eval(scrapertools.find_single_match(data, "var anime_info = (\[.*?\])"))
    epi_list = eval(scrapertools.find_single_match(data, "var episodes = (\[.*?\])"))

    infoLabels = item.infoLabels

    for epi in epi_list[::-1]:
        url = "%sver/%s-%s" % (host, info[1], epi)
        epi_num = epi
        infoLabels['season'], infoLabels['episode'] = renumbertools.numbered_for_trakt(item.channel, item.contentSerieName, item.contentSeason, int(epi_num or 1))
        
        title = '1x%s - Episodio %s' % (epi_num, epi_num)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    next_episode_air_date = get_next_episode_air_date(info)
    if next_episode_air_date:
        for item in itemlist:
            item.infoLabels['next_episode_air_date'] = next_episode_air_date

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    data = httptools.downloadpage(item.url, canonical=canonical).data

    videos = eval(scrapertools.find_single_match(data, "var videos = (\[.*?);"))

    for v_data in videos:
        server = v_data[0]
        url = v_data[1].replace("\/", "/")

        if server.lower() == "umi":
            url = url.replace("gocdn.html#", "gocdn.php?v=")
            url = httptools.downloadpage(url, headers={"x-requested-with": "XMLHttpRequest"}).json["file"]

        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return list_all(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    itemlist = []
    item = Item()
    if categoria == 'anime':
        item.url = host
        itemlist = new_episodes(item)
    return itemlist


def get_next_episode_air_date(info):
    """
    Extracts the next episode air date from the anime info.
    :param info: The anime info dictionary.
    :return: The next episode air date or None if not available.
    """

    if len(info) > 3:
        date = info[3].split('-')
        return '{}/{}/{}'.format(date[2], date[1], date[0]) if len(date) == 3 else info[3]
    
    return None


def get_season_from_title(title):
    """
    Extracts the season number from the title.
    :param title: The title of the anime.
    :return: The title and the season number or 1 if not found.
    """
    season = scrapertools.find_single_match(title, '(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season')
    if not season:
        season = scrapertools.find_single_match(title, '(?i)(?:season|temporada)\s*(\d+)')
        if season:
            title = re.sub('(?i)\s*(?:season|temporada)\s*\d+', '', title)
    else:
        title = re.sub('(?i)\s*\d+\s*(?:st|nd|rd|th)\s+season', '', title)
    
    return title.strip(), int(season) if season else 1


def get_type_from_title(title, c_type):
    """
    Tries to deduce if it is a movie depending on the title.
    :param title: The title of the anime.
    :return: c_type string - movie or tvshow, and
             title string - the title cleaned.
    """
    patern = r'(?i)\s*(?:the|)\s*movie\s*(?:\d+|)'
    res = re.search(patern, title, flags=re.DOTALL)
    if res:
        c_type = 'movie'
        title = title.replace(res.group(0), '').strip()
    
    return title.strip(), c_type