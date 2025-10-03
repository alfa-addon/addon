# -*- coding: utf-8 -*-
# -*- Channel SoloLatino -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64
from bs4 import BeautifulSoup

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import jsontools
from lib import jsunpack
from channelselector import get_thumb
from platformcode import config, logger
from modules import filtertools
from modules import autoplay


IDIOMAS = {'2': 'VOSE', "0": "LAT", "1": "CAST", "LAT": "LAT"}

list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'gvideo',
    'fembed',
    'directo'
    ]

canonical = {
             'channel': 'sololatino', 
             'host': config.get_setting("current_host", 'sololatino', default=''), 
             'host_alt': ["https://sololatino.net/"], 
             'host_black_list': [], 
             'pattern': ['<meta\s*property="og:url"\s*content="([^"]+)"'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'forced_proxy_ifnot_assistant': 'ProxyCF', 'CF_stat': True, 'cf_assistant_if_proxy': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
patron_host = '((?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?[\w|\-]+\.\w+)(?:\/|\?|$)'
TIMEOUT = 30


def mainlist(item):
    logger.info()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=host + "peliculas/",
                         thumbnail=get_thumb('movies', auto=True), type="pelicula"))
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'series/', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Anime', url=host + 'animes/', action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def sub_menu(item):
    logger.info()
    
    itemlist = list()
    url = item.url.replace('peliculas', 'pelicula')
    
    if item.title == "Peliculas":
        itemlist.append(Item(channel=item.channel, title='Ultimas', url=url + "estrenos/", action='list_all',
                             thumbnail=get_thumb('last', auto=True)))
    else:
        itemlist.append(Item(channel=item.channel, title='Últimos Episodios', url=url + "novedades/", action='list_all',
                             thumbnail=get_thumb('last', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Recomendadas', url=url + "mejor-valoradas/",
                         action='list_all', thumbnail=get_thumb('recomendadas', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Todas', url=item.url, action='list_all',
                         thumbnail=get_thumb('all', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True), url=item.url))
    
    itemlist.append(Item(channel=item.channel, title='Años', action='section',
                         thumbnail=get_thumb('years', auto=True), url=item.url))
    
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    
    if referer:
        data = httptools.downloadpage(url, timeout=TIMEOUT, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, timeout=TIMEOUT, canonical=canonical).data
    
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    
    return soup


def get_language(lang_data):
    logger.info()
    
    language = list()
    
    lang_list = lang_data.find_all("span", class_="flag")
    for lang in lang_list:
        lang = scrapertools.find_single_match(lang["style"], r'/flags/(.*?).png\)')
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    
    return language


def section(item):
    logger.info()
    
    itemlist = list()
    url = item.url.replace('peliculas', 'pelicula')
    
    soup = create_soup(item.url)
    
    if item.title == "Generos":
        matches = soup.find("ul",  class_="Ageneros")
        base_url = "%sfiltro/?genre=%s&year="
    else:
        matches = soup.find("ul", class_="Ayears", id="tipo_cat_1")
        base_url = "%sfiltro/?genre=&year=%s"
    
    for elem in matches.find_all("li"):
        gendata = elem.get('data-value', '')
        title = elem.text
        url_section = base_url % (url, gendata)
        
        if gendata:
            itemlist.append(Item(channel=item.channel, title=title, action="list_all", url=url_section))
    
    return itemlist


def list_all(item):
    logger.info()
    itemlist = list()
    
    try:
        soup = create_soup(item.url)
    except:
        return itemlist
    
    matches = soup.find("div", class_="content").find_all("article", id=re.compile(r"^post-\d+"))
    
    for elem in matches:
        url = elem.a["href"]
        title = elem.img["alt"]
        thumb = elem.img["data-srcset"]
        try:
            year = elem.p.text
        except:
            year = '-'
        
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, infoLabels={"year": year})
        
        if "novedades" in item.url:
            try:
                season, episode = scrapertools.find_single_match(title, '\:\s*(\d+).(\d+)')
                new_item.contentSeason = int(season)
                new_item.contentEpisodeNumber = int(episode)
                title = re.sub('\:\s*\d+.\d+', '', title)
                new_item.title = '%sx%s - %s' % (new_item.contentSeason, str(new_item.contentEpisodeNumber).zfill(2), title)
            except:
                new_item.contentSeason = 1
                new_item.contentEpisodeNumber = 0
            new_item.contentSerieName = title
            new_item.action = "findvideos"
            new_item.contentType = 'episode'
        elif "pelicula" in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = 'movie'
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.contentType = 'tvshow'
            new_item.context = filtertools.context(item, list_language, list_quality)
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    try:
        url_next_page = soup.find_all("div", class_="pagMovidy")[-1].a["href"]
    except:
        return itemlist
    
    if url_next_page and len(matches) > 16:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))
    
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    try:
        soup = create_soup(item.url).find("div", id="seasons")
        
        matches = soup.find_all("div", class_="clickSeason")
    except:
        return itemlist
    
    infoLabels = item.infoLabels
    
    for elem in matches:
        try:
            season = int(elem["data-season"])
        except:
            season = 1
        title = "Temporada %s" % season
        infoLabels["season"] = season
        
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
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
    itemlist = list()
    
    try:
        soup = create_soup(item.url).find("div", id="seasons")
        matches = soup.find_all("div", class_="se-c")
    except:
        return itemlist
    
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    
    for elem in matches:
        if elem["data-season"] != str(season):
            continue
        
        epi_list = elem.find("ul", class_="episodios")
        for epi in epi_list.find_all("li"):
            info = epi.find("div", class_="episodiotitle")
            url = epi.a["href"]
            epi_name = info.find("div", class_="epst").text
            epi_num = epi.find("div", class_="numerando").text.split(" - ")[1]
            infoLabels["episode"] = epi_num
            title = "%sx%s - %s" % (season, epi_num, epi_name)
            
            itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                 infoLabels=infoLabels, contentType='episode'))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url)
    matches = soup.find("div", class_="contEP")
    url = matches.iframe['src']
    
    data = httptools.downloadpage(url).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    
    if "embed69" in url:
        import ast
        
        clave = scrapertools.find_single_match(data, r"decryptLink\(server.link, '(.+?)'\),")
        dataLinkString = scrapertools.find_single_match(data, r"dataLink\s*=\s*([^;]+)")
        
        dataLinkString = dataLinkString.replace(r"\/", "/")
        dataLink = ast.literal_eval(dataLinkString)
        
        for langSection in dataLink:
            language = langSection.get('video_language', 'LAT')
            language = IDIOMAS.get(language, language)
            for elem in langSection['sortedEmbeds']:
                if elem['servername'] != "download":
                    vid = elem['link']
                    if clave:
                        from lib.crylink import crylink
                        vid = crylink(vid, clave)
                    else:
                        vid = scrapertools.find_single_match(vid, '\.(eyJs.*?)\.')
                        vid += "="
                        vid = base64.b64decode(vid).decode()
                        vid = scrapertools.find_single_match(vid, '"link":"([^"]+)"')
                    itemlist.append(Item(channel=item.channel, title='%s', action='play', url=vid,
                                           language=language, infoLabels=item.infoLabels))
    
    else:
        matches = soup.find('div', class_='OptionsLangDisp').find_all('li')
        for elem in matches:
            vid = elem['onclick']
            lang = elem['data-lang']
            server = elem.span.text.strip()
            vid = scrapertools.find_single_match(vid, "go_to_player(?:Vast|)\('([^']+)")
            if vid.startswith("http"):
                vid = vid
            elif vid:
                try:
                    vid = base64.b64decode(vid).decode()
                except (ValueError, TypeError):
                    vid = url
            else:
                continue
            
            if "1fichier=" in vid or "1fichier" in server:
                vid = scrapertools.find_single_match(vid, '=\?([A-z0-9]+)')
                vid = "https://1fichier.com/?%s" %url
            
            language = IDIOMAS.get(lang, lang)
            if "plusvip" not in vid:
                itemlist.append(Item(channel=item.channel, title='%s', action='play', url=vid,
                                           language=language, infoLabels=item.infoLabels))
    
    itemlist.sort(key=lambda x: x.language)
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'peliculas'
        elif categoria == 'infantiles':
            item.url = host + 'peliculas/filtro/?genre=animacion-2'
        elif categoria == 'terror':
            item.url = host + 'peliculas/filtro/?genre=terror-2/'
        item.first = 0
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    
    return itemlist
