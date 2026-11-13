# -*- coding: utf-8 -*-
# -*- Channel SeriesKao -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
from core import urlparse as alfa_urlparse
import sys
import base64
import re

from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from core import urlparse
from channelselector import get_thumb
from platformcode import config, logger
from modules import filtertools
from modules import autoplay
from bs4 import BeautifulSoup

IDIOMAS = {'2': 'VOSE', "0": "LAT", "1": "CAST", "JAP": "JA", "SUB": "VOSE", "LAT": "LAT"}

list_language = list(dict.fromkeys(IDIOMAS.values()))

list_quality = []

list_servers = [
    'gvideo',
    'fembed',
    'streamwish',
    'vidhidepro',
    'voe',
    'directo'
    ]

canonical = {
             'channel': 'serieskao', 
             'host': config.get_setting("current_host", 'serieskao', default=''), 
             'host_alt': ["https://serieskao.top/"], 
             'host_black_list': ["https://serieskao.org/", "https://serieskao.net/"], 
             'pattern': [r'<link\s*rel="canonical"\s*href="(\w+\:\/\/[^\/]+\/)'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1,
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    # itemlist.append(Item(channel=item.channel, title='embed69', action='findvideos', url="https://serieskao.top/pelicula/la-promesa-de-irene-bxKhP7"))
    # itemlist.append(Item(channel=item.channel, title='xupalace', action='findvideos', url="https://serieskao.top/pelicula/no-way-out-2023"))
    
    itemlist.append(Item(channel=item.channel, title='Todas', action='list_all', url=alfa_urlparse.build_url(host, 'peliculas'),
                         thumbnail=get_thumb('movies', auto=True), type="peliculas"))
    # itemlist.append(Item(channel=item.channel, title='Por Género', action='genres', url=host,
                         # thumbnail=get_thumb('movies', auto=True), type="peliculas"))
    # itemlist.append(Item(channel=item.channel, title='Año', action='genres', url=host,
                         # thumbnail=get_thumb('movies', auto=True), type="peliculas"))
    itemlist.append(Item(channel=item.channel, title='Series', url=alfa_urlparse.build_url(host, 'series'), action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True), type="series"))
    # itemlist.append(Item(channel=item.channel, title='Por Género', action='genres', url=host,
                         # thumbnail=get_thumb('tvshows', auto=True), type="series"))
    # itemlist.append(Item(channel=item.channel, title='Año', action='genres', url=host,
                         # thumbnail=get_thumb('tvshows', auto=True), type="series"))
    itemlist.append(Item(channel=item.channel, title='Anime', url=alfa_urlparse.build_url(host, 'animes'), action='list_all',
                         thumbnail=get_thumb('anime', auto=True), type="animes"))
    itemlist.append(Item(channel=item.channel, title='Dorama', url=alfa_urlparse.build_url(host, 'generos/dorama'), action='list_all',
                         thumbnail=get_thumb('anime', auto=True), type="series"))
    itemlist.append(Item(channel=item.channel, title='Por Género', action='genres', url=host,
                         thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Año', action='genres', url=host,
                         thumbnail=get_thumb('year', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail=get_thumb("search", auto=True)))
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def genres(item):
    logger.info()
    itemlist = list()
    existe = set()
    data = httptools.downloadpage(item.url).data
    if 'Por Género' in item.title:
        matches = scrapertools.find_multiple_matches(data, '(?is)href="/(genero[^"]+)"[^>]+>([^<]+)')
    else:
        matches = scrapertools.find_multiple_matches(data, r'(?is)href="/(year[^"]+)"[^>]+>(\d+)<')
    for url, title in matches:
        if url in existe:
            continue
        existe.add(url)
        itemlist.append(Item(channel=item.channel, title=title, url=alfa_urlparse.urljoin(host, url),
                 action="list_all"))
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = list()
    year = ""
    soup = create_soup(item.url)
    matches = soup.find_all("a", class_="card__link")
    for elem in matches:
        url = elem['href']
        title = elem.h2.text if elem.h2 else elem.get_text(strip=True)
        thumbnail = elem.img['src'] if elem.img else ''
        year = elem.find('span', class_='card__badge--year')
        if year:
            year = year.text.strip()
        else:
            year = '-'
        url = urlparse.urljoin(item.url,url)
        
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, infoLabels={"year": year})
        if "/serie/" in url or "/anime/" in url:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.context = filtertools.context(item, list_language, list_quality)
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    next_page = soup.find(attrs={"aria-label": re.compile(r"^(?:Next|Siguiente)")})
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="list_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url)
    select = soup.find('select', id='temporadas_select')
    if not select:
        # Serie sin temporadas/episodios publicados todavia
        return itemlist
    infoLabels = dict(item.infoLabels)
    for elem in select.find_all('option'):
        season = scrapertools.find_single_match(elem.text, r'\d+')
        if not season:
            continue
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title="Temporada %s" %season, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.add_videolibrary:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    templist = [x for x in templist if x.action == 'episodesxseasons']
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)
    
    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = dict(item.infoLabels)
    season = item.infoLabels["season"]
    
    id = "season-%s" %season
    
    soup = create_soup(item.url)
    div = soup.find('div', id=id)
    if not div:
        return itemlist
    
    base = item.url.split('#')[0].rstrip('/')
    for elem in div.find_all('a'):
        url = elem.get('href', '')
        epi_num = elem.get('data-episode') or scrapertools.find_single_match(url, r'#s\d+-e(\d+)')
        if not epi_num:
            continue
        infoLabels["episode"] = epi_num
        title = "%sx%s" % (season, epi_num)
        # La web ya no usa /capitulo/N: ruta canonica /temporada/N/capitulo/M
        url = "%s/temporada/%s/capitulo/%s" % (base, season, epi_num)
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist


def findvideos(item):
    import ast
    from lib.unshortenit import bypass_embed69
    
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url)
    # La ficha incluye primero el trailer (#trailer-iframe, src="about:blank").
    # Hay que usar el reproductor real.
    iframe = soup.find('iframe', id='player-iframe')
    if iframe is None:
        iframe = soup.find('iframe', src=re.compile(r'/(?:vidurl|embed69)/'))
    if iframe is None:
        return itemlist
    url = urlparse.urljoin(item.url, (iframe.get('src') or '').strip())
    if not url.startswith('http'):
        return itemlist
    
    data = httptools.downloadpage(url).data
    if not data:
        return itemlist
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    
    cont = soup.find('div', class_='OptionsLangDisp')
    if cont:
        for elem in cont.find_all('li'):
            lang = elem.get('data-lang', '')
            server = elem.span.get_text(strip=True) if elem.span else ''
            vid = elem.get('data-url') or ''
            if not vid:
                onclick = elem.get('onclick', '')
                vid = scrapertools.find_single_match(onclick, r"go_to_player(?:Vast|)\('([^']+)")
                if vid and not vid.startswith('http'):
                    try:
                        vid = base64.b64decode(vid).decode()
                    except (ValueError, TypeError):
                        vid = ''
            if not vid:
                continue
            if "plusvip" in vid:
                continue
            if "1fichier" in vid or "1fichier" in server:
                if not vid.startswith('http'):
                    code = scrapertools.find_single_match(vid, r'=\?([A-Za-z0-9]+)')
                    if not code:
                        continue
                    vid = alfa_urlparse.urlunsplit(('https', '1fichier.com', '/', code, ''))
            language = IDIOMAS.get(lang, lang or 'LAT')
            itemlist.append(Item(channel=item.channel, title='%s', action='play', url=vid,
                                 language=language, infoLabels=item.infoLabels))
    
    elif 'dataLink' in data:
        
        clave, data = bypass_embed69(data)
        
        dataLinkString = scrapertools.find_single_match(data, r"dataLink\s*=\s*([^;]+)")
        if not dataLinkString:
            return itemlist
        dataLinkString = dataLinkString.replace(r"\/", "/")
        dataLink = ast.literal_eval(dataLinkString)
        
        for langSection in dataLink:
            language = langSection.get('video_language', 'LAT')
            language = IDIOMAS.get(language, language)
            for elem in langSection.get('sortedEmbeds', []):
                if elem['servername'] != "download":
                    vid = elem['link']
                    if not clave:
                        vid = scrapertools.find_single_match(vid, r'\.(eyJs.*?)\.')
                        vid += "="
                        vid = base64.b64decode(vid).decode()
                        vid = scrapertools.find_single_match(vid, '"link":"([^"]+)"')
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
        _url_query_texto = texto
        texto = texto.replace(" ", "+")
        item.url = alfa_urlparse.build_url(host, 'search', query=[('s', u'{}'.format(_url_query_texto))])

        # item.url = item.url + texto
        item.extra = "buscar"

        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except Exception:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = alfa_urlparse.build_url(host, 'peliculas')
        elif categoria == 'infantiles':
            item.url = alfa_urlparse.build_url(host, 'generos/animacion')
        elif categoria == 'terror':
            item.url = alfa_urlparse.build_url(host, 'generos/terror')
        else:
            return []
        item.first = 0
        itemlist = list_all(item)
        if itemlist and itemlist[-1].action == 'list_all':
            itemlist.pop()
    except Exception:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    
    return itemlist
