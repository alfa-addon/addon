# -*- coding: utf-8 -*-
# -*- Channel Estrenos Anime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import urlparse
from core.item import Item
from platformcode import config, logger, platformtools
from modules import filtertools
from modules import autoplay
from modules import renumbertools
from core import tmdb


IDIOMAS = {'vose': 'VOSE', 'latino': 'LAT'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['filemoon', 'voe', 'streamtape', 'bigwarp', 'mixdrop', 'doodstream']

canonical = {
             'channel': 'estrenosanime', 
             'host': config.get_setting("current_host", 'estrenosanime', default=''), 
             'host_alt': ["https://estrenosanime.net/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)
    
    soup = create_soup(host)
    menus = soup.select('#sidebar_menu > ul > li')
    
    for i, menu in enumerate(menus):
        submenu = menu.select_one('div.nav-link')
        if submenu:
            title = submenu.getText(strip=True)
            itemlist.append(
                item.clone(
                    title=title,
                    action="section",
                    index=i,
                    plot="{} > {}".format(item.title, title)
                )
            )

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",
                         thumbnail=get_thumb('search', auto=True)))
    
    itemlist.append(Item(action = "setting_channel", channel = item.channel,
                         plot = "Configurar canal", title = "Configurar canal", 
                         thumbnail = get_thumb("setting_0.png")))
    
    itemlist = renumbertools.show_option(item.channel, itemlist)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def setting_channel(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


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


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("div", class_="flw-item")
    
    for elem in matches:
        link = elem.find('h3', class_="film-name").a
        url = host.rstrip('/') + link["href"]
        if str(link["href"]).startswith('/anime/'):
            url = url.replace('/anime/', '/ver/')
            url += '-episodio-1'
        title = link.getText(strip=True)
        thumb = elem.find('img', class_="film-poster-img")["data-src"]
        plot = elem.select_one('div.film-detail > div.description').getText(strip=True)
        new_item = Item(channel=item.channel, url=url, title=title,
                        thumbnail=thumb, infoLabels={'year': '-'}, plot=plot)
        
        title, lang = get_lang_from_title(title)
        new_item.language = lang
        
        info = elem.select('span.fdi-item')
        c_type = get_type(info[0].getText(strip=True)) if len(info) > 0 else 'tvshow'
        # year = info[2].getText(strip=True) if len(info) > 2 else '-'
        # new_item.infoLabels['year'] = year
                
        if c_type == "tvshow":
            title, season = get_season_from_title(title)
            new_item.contentSerieName = get_single_title(title)
            new_item.contentSeason = season
            new_item.context = renumbertools.context(new_item)
            if 'ultimo-episodios' in item.url:
                new_item.contentType = "episode"
                new_item.action='findvideos'
                episode_div = elem.select_one('div.tick-item.tick-eps.amp-algn')
                if episode_div:
                    episode = episode_div.getText(strip=True)
                    episode = episode.split(' ')[1]
                    if "/" in episode:
                        episode = episode.split("/")[0]
                    episode = int(episode)
                else:
                    episode = 1
                new_item.infoLabels['season'] = season
                new_item.infoLabels['episode'] = episode
                new_item.title = '{0}x{1} - Episodio {1}'.format(season, episode)
            else:
                new_item.contentType = "tvshow"
                new_item.action='episodios'
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = get_single_title(title)
            new_item.action='findvideos'

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        next_page = soup.find('div', class_="pagination").find('a', string='Siguiente')
        if next_page:
            next_page_url = next_page['href']
            if not next_page_url.startswith('http'):
                next_page_url = "{}{}/{}".format(
                    host.rstrip('/'),
                    get_url_folder(item.url),
                    next_page_url
                )
            itemlist.append(
                item.clone(
                    title = "Siguiente página",
                    thumbnail = get_thumb("next", auto=True),
                    url = next_page_url
                )
            )
    except:
        pass

    return itemlist


def section(item):
    logger.info()

    itemlist = list()

    soup = create_soup(host)
    menus = soup.select('#sidebar_menu > ul > li')
    links = menus[item.index].select('a.nav-link')
    for link in links:
        title = link.string
        if title:
            url = str(link.get('href', '')).replace('../','')
            itemlist.append(
                item.clone(
                    title=title, 
                    url=host+url,
                    action="list_all",
                    plot="{} > {}".format(item.title, title)
                )
            )

    return itemlist


def episodios(item):
    logger.info()

    itemlist = list()
    
    soup = create_soup(item.url)
    match = soup.find("div", id="episodes-content")
    
    if not match:
        return itemlist
    
    infoLabels = item.infoLabels

    for link in match.find_all("a"):
        url = host.rstrip('/') + link["href"]
        epi_num = link.div.getText(strip=True)
        infoLabels['season'], infoLabels['episode'] = renumbertools.numbered_for_trakt(item.channel, item.contentSerieName, item.contentSeason, int(epi_num or 1))
        
        title = '{0}x{1} - Episodio {1}'.format(infoLabels['season'], infoLabels['episode'])
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos', infoLabels=infoLabels))

    itemlist.reverse()
    
    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    iframe = soup.select_one("div.player-frame > iframe")
    
    if not iframe:
        return itemlist
    
    multiserver_url = iframe["src"]
    
    data = httptools.downloadpage(multiserver_url, canonical=canonical).data
    pattern = r"go_to_player(?:Vast|)\('([^']+)"
    urls = scrapertools.find_multiple_matches(data, pattern)

    for url in urls:
        itemlist.append(Item(channel=item.channel, title='%s', action='play', 
                             url=url, language=item.language,
                             infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    
    # Filtra los enlaces cuyos servidores no fueron resueltos por servertools

    itemlist = [i for i in itemlist if i.title != "Directo"]

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        if texto != '':
            texto = texto.replace(" ", "+")
            item.url = host.rstrip('/') + '/search?keyword=' + texto
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
        item.url = host.rstrip('/') + '/ultimo-episodios'
        itemlist = list_all(item)
    return itemlist


def get_season_from_title(title):
    """
    Extracts the season number from the title.
    :param title: The title of the anime.
    :return: The title and the season number or 1 if not found.
    """
    
    patern1 = r'(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season'
    patern2 = r'(?i)(?:season|temporada|part)\s*(\d+)'
    
    season = scrapertools.find_single_match(title, patern1)
    if not season:
        season = scrapertools.find_single_match(title, patern2)
        if season:
            title = re.sub(patern2, '', title)
    else:
        title = re.sub(patern1, '', title)
    
    return title.strip(), int(season) if season else 1


def get_lang_from_title(title):
    """
    Extracts the language from the title.
    :param title: The title of the item.
    :return: The title and the language.
    """
    latino = ' (Latino)'
    if latino in title:
        lang = 'LAT'
        title = title.replace(latino, '')
    else:
        lang = 'VOSE'
    return title, lang


def get_type(c_type):
    if "Pelicula" in c_type:
        c_type = "movie"
    else:
        c_type = "tvshow"
    
    return c_type


def get_url_folder(url):
    """
    Extracts the path components (representing folders) from a given URL.
    """
    parsed_url = urlparse.urlparse(url)
    path = parsed_url.path
    
    # Remove the filename if present, leaving only the directory path
    if '/' in path:
        # Split the path and take all parts except the last one (filename)
        folder_path_parts = path.split('/')[:-1]
        folder_path = '/'.join(folder_path_parts)
    else:
        folder_path = "" # No folder path if only a filename or root
        
    return folder_path


def get_single_title(title):
    if ':' in title:
        title = title.split(':')[0]
    return title.strip()