# -*- coding: utf-8 -*-
# -*- Channel RepelisHD -*-
# -*- Created for Rebel-addon -*-
# -*- By the Rebel Developer -*-

from core import urlparse as alfa_urlparse
import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb
from bs4 import BeautifulSoup
from channelselector import get_thumb

from lib import planbtools


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'sub': 'VOSE'}
CUSTOM_FILTER = {'castellano': 'Castellano', 'latino': 'Latino', 'subtitulado': 'sub'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = []


thumbmx = 'http://flags.fmcdn.net/data/flags/normal/mx.png'
thumbes = 'http://flags.fmcdn.net/data/flags/normal/es.png'
thumbus = 'http://flags.fmcdn.net/data/flags/normal/us.png'


forced_proxy_opt = 'ProxySSL'

#  "https://repelishd.cam/"
#  "https://cinehdplus.gratis/"  "https://cinehdplus.cam/" 

#  "https://cinehdplus.org/"  "https://cinehdplus.net/"(OUT)

canonical = {
             'channel': 'repelishd', 
             'host': config.get_setting("current_host", 'repelishd', default=''), 
             'host_alt': ["https://cinehdplus.surf/"], 
             'host_black_list': ["https://cinehdplus.ceo/", "https://cinehdplus.gratis/", "https://cinehdplus.cam/"], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*title='], 
             # 'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'cf_assistant': False, 'CF_stat': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'CF': False, 'CF_test': False, 'alfa_s': True, 'host_alt_findb': [2,11]
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = list()
    
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="list_all", url=alfa_urlparse.build_url(host, u'{}/page/1/'.format("cine")), thumbnail=get_thumb("movies", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Series", action="list_all", url=alfa_urlparse.build_url(host, u'{}/page/1/'.format("series")), thumbnail=get_thumb("tvshows", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas")), thumbnail=get_thumb("genres", auto=True), extra=item.extra))
    itemlist.append(Item(channel=item.channel, title="Años", action="anno", url=host, thumbnail=get_thumb("year", auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host, thumbnail=get_thumb("search", auto=True)))
    
    return itemlist


def create_soup(url, referer=None, post=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    if post:
        data = httptools.downloadpage(url, post=post, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url, referer=host)
    matches = soup.find_all("div", class_="card")
    for elem in matches:
        lang = list()
        url = elem.a["href"]
        title = elem.img["alt"]
        try:
            thumb = elem.img["data-src"]
        except Exception:
            thumb = elem.img["src"]
        
        languages = elem.find_all("img", class_="idioma")
        for l in languages:
            if not l["alt"] in lang:
                lang.append(l["alt"])
        year = elem.find("span", class_="year").text
        
        new_item = Item(channel=item.channel, title=title, url=url, thumbnail=thumb, 
                        language=lang, infoLabels={"year": year})
        
        es_serie = bool(re.search(r"/series/", item.url))
        
        if es_serie:
            new_item.contentSerieName = title
            new_item.action = "seasons"
            new_item.contentType = 'tvshow'
        else:
            new_item.contentTitle = title
            new_item.action = "findvideos"
            new_item.contentType = 'movie'
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    try:
        next_page = soup.find(class_="catalog__paginator").find_all("a")[-1]
        if not "index.php" in item.url:
            next_page = next_page["href"]
            next_page = scrapertools.find_single_match(next_page, 'page/(\d+)')
            next_page = re.sub(r"page/\d+", "page/{0}".format(next_page), item.url)
        else:
            next_page = next_page["onclick"]
            next_page = scrapertools.find_single_match(next_page, '(\d+)')
            next_page = re.sub(r"&search_start=\d+", "&search_start={0}".format(next_page), item.url)
            
        if next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all'))
    except Exception:
        pass
    
    return itemlist


def section(item):
    logger.info()
    itemlist = list()
    
    soup = create_soup(item.url)
    matches = soup.find("ul", class_="genres").find_all("li")
    for elem in matches:
        url = elem.a['href']
        title = url.replace(host, '').replace("/", "")
        if "series" in title or "cine" in title or "proximas" in title: continue
        url = item.url.replace("peliculas", title)
        title = title.capitalize()
        itemlist.append(item.clone(title=title, url=url, action="list_all"))
    
    return itemlist


def anno(item):
    logger.info()
    from datetime import datetime
    
    itemlist = []
    
    now = datetime.now()
    year = int(now.year)
    while year >= 1980:
        itemlist.append(item.clone(title="%s" %year, action="list_all", url= alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas"), query=[('language', u'{}'.format(item.extra)), ('years', u'{};{}'.format(u'{}'.format(year), u'{}'.format(year)))])))
        year -= 1
    itemlist.append(item.clone(title="70s", action="list_all", url= alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas"), query=[('language', u'{}'.format(item.extra)), ('years', '1970;1979')])))
    itemlist.append(item.clone(title="60s", action="list_all", url= alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas"), query=[('language', u'{}'.format(item.extra)), ('years', '1960;1969')])))
    itemlist.append(item.clone(title="50s", action="list_all", url= alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas"), query=[('language', u'{}'.format(item.extra)), ('years', '1950;1959')])))
    itemlist.append(item.clone(title="<40s", action="list_all", url= alfa_urlparse.build_url(host, u'{}/page/1/'.format("peliculas"), query=[('language', u'{}'.format(item.extra)), ('years', '1930;1949')])))
    
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    soup = None
    if not infoLabels.get('imdb_id', ''):
        soup = create_soup(item.url)
        imdb = scrapertools.find_single_match(str(soup), r"imdb\s*=\s*'([^']+)'")
        if imdb:
            infoLabels['imdb_id'] = imdb
            item.infoLabels['imdb_id'] = imdb

    if infoLabels.get('number_of_seasons', ''):
        numeros = [n for n in range(1, int(infoLabels['number_of_seasons'])+1)]
    else:
        reales = planbtools.host_alt_findb_fun(item, seasons=True)

        if reales:
            numeros = [str(n) for n in sorted(reales.keys())]
        else:
            if soup is None:
                soup = create_soup(item.url)
            bloque = soup.find('div', class_='tt_season')
            if bloque:
                numeros = [e.text.strip() for e in bloque.find_all("a")]
            else:
                maximo = scrapertools.find_single_match(str(soup), r"DEFAULT_MAX_SEASONS\s*=\s*(\d+)")
                numeros = [str(n) for n in range(1, int(maximo) + 1)] if maximo else []
    
    for season in numeros:
        title = "Temporada %s" % season
        infoLabels["season"] = season
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
    logger.info(item)
    itemlist = list()
    
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    
    if infoLabels.get('temporada_num_episodios', '') or infoLabels.get('last_episode_to_air', ''):
        numeros = [n for n in range(1, (int(infoLabels.get('last_episode_to_air', '') or infoLabels.get('temporada_num_episodios', ''))+1))]
    else:
        reales = planbtools.host_alt_findb_fun(item, seasons=True)
        try:
            de_lsrc = reales.get(int(season), []) if reales else []
        except Exception:
            de_lsrc = []
        
        if de_lsrc:
            numeros = [str(n) for n in de_lsrc]
        else:
            soup = create_soup(item.url)
            lista = None
            try:
                lista = soup.find("div", id="season-%s" % season).find("ul")
            except Exception:
                lista = None
            
            if lista:
                numeros = [e.a.text.strip() for e in lista.find_all("li")]
            else:
                maximo = scrapertools.find_single_match(str(soup), r"DEFAULT_MAX_EPISODES\s*=\s*(\d+)")
                numeros = [str(n) for n in range(1, int(maximo) + 1)] if maximo else []
    
    for cap in numeros:
        title = "%sx%s" % (season, cap)
        infoLabels['episode'] = cap
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='findvideos', infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    return itemlist


def findvideos(item):
    logger.info()
    
    return planbtools.build_findvideos(canonical, list_language, item)


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = alfa_urlparse.build_url(host, 'index.php', query=[('do', 'search'), ('subaction', 'search'), ('search_start', '1'), ('story', texto)])
    if texto != '':
        return list_all(item)
    else:
        return []

