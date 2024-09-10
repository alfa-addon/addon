# -*- coding: utf-8 -*-
# -*- Channel Cuevana2español -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from channelselector import get_thumb
from modules import autoplay
from modules import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

IDIOMAS = {'Latino': 'Latino',"espanol":"Español","Subtitulado":"Subtitulado"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['fembed', 'streamtape', 'gvideo', 'Jawcloud']
forced_proxy_opt = 'ProxySSL'

canonical = {
             'channel': 'cuevana2espanol', 
             'host': config.get_setting("current_host", 'cuevana2espanol', default=''), 
             'host_alt': ["https://www.cuevana2espanol.net/"], 
             'host_black_list': ["https://www.cuevana2espanol.icu/", "https://cuevana2espanol.com/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt,  
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

encoding = "utf-8"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = "/pelicula"
tv_path = '/serie'
language = []
url_replace = []

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu', url=host+'archives/movies/page/', 
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Series',  action='sub_menu', url=host+'archives/series', 
                         thumbnail=get_thumb('tvshows', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Últimas', url=item.url, action='list_all', pagina=1,
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Estrenos', url=item.url+'/releases', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Tendencias Semana', url=item.url+'/top/week', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))

    itemlist.append(Item(channel=item.channel, title='Tendencias Día', url=item.url+'/top/day', action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type=item.c_type))
    
    if item.c_type == 'peliculas':
        itemlist.append(Item(channel=item.channel, title='Generos', action='section', url=host,
                             thumbnail=get_thumb('genres', auto=True), c_type=item.c_type))
    else:
        itemlist.append(Item(channel=item.channel, title='Episodios', action='list_all', url=host+'archives/episodes',
                             thumbnail=get_thumb('episodes', auto=True), c_type='episodios'))

    return itemlist


def section(item):
    logger.info()

    genres = {'Acción': 'genres/accion/', 
              'Animación': 'genres/animacion/', 
              'Crimen': 'genres/crimen/', 
              'Familia': 'genres/familia/', 
              'Misterio': 'genres/misterio/', 
              'Suspense': 'genres/suspenso/', 
              'Aventura': 'genres/aventura/', 
              'Ciencia Ficción': 'genres/ciencia-ficcion/', 
              'Drama': 'genres/drama/', 
              'Fantasía': 'genres/fantasia/', 
              'Romance': 'genres/romance/', 
              'Terror': 'genres/terror/'
              }

    return AlfaChannel.section(item, section_list=genres, **kwargs)


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url + "%s" %item.pagina, encoding=encoding, canonical=canonical).data
    logger.info("Intel11 %s" %data)
    patron  = '(?ims)bdOz3.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<h3>([^<]+).*?'
    patron += '<span>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    scrapertools.printMatches(matches)
    
    for url, title, annio in matches:
        idioma = "Latino"
        item.infoLabels['year'] = annio
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = title,
                                   contentTitle = title,
                                   thumbnail = "",
                                   url = url,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, 'class="page-link" href="([^"]+)')
    if url_pagina != "":
        paginax = "Pagina: %s" %(item.pagina + 1)
        itemlist.append(Item(channel = item.channel, action = "list_all", title = paginax, url = item.url, pagina = item.pagina + 1))
    return itemlist


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item, **kwargs)


def episodios(item):
    logger.info()
    
    itemlist = []
    
    templist = seasons(item)
    
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    kwargs['matches_post_get_video_options'] = findvideos_matches

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, **kwargs)


def episodesxseason_matches(item, matches_int, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)

    for x, elem_season in enumerate(matches_int):
        #logger.error(elem_season)

        if item.contentSeason != elem_season.get('number', 1): continue
        for elem in elem_season.get('episodes', []):
            elem_json = {}
            #logger.error(elem)

            elem_json['url'] = findS.get('episode_url', '') % (host, elem.get('slug', {}).get('name', ''), 
                                                               item.contentSeason, elem.get('slug', {}).get('episode', 1))
            elem_json['title'] = elem.get('title', '')
            elem_json['season'] = item.contentSeason
            elem_json['episode'] = int(elem.get('number', '1') or '1')
            elem_json['thumbnail'] = elem.get('image', '')

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())

    return matches


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(host + item.url, encoding=encoding, canonical=canonical).data
    


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()

    matches = []
    findS = AHkwargs.get('finds', finds)
    servers = {'drive': 'gvideo', 'fembed': 'fembed', "player": "oprem", "openplay": "oprem", "embed": "mystream"}

    for lang, elem in list(matches_int.items()):
        #logger.error(elem)

        for link in elem:
            elem_json = {}
            #logger.error(link)

            elem_json['server'] = link.get('cyberlocker', '')
            elem_json['url'] = link.get('result', '')
            elem_json['language'] = '*%s' % lang
            elem_json['quality'] = '*%s' % link.get('quality', '')
            elem_json['title'] = '%s'

            if not elem_json['url']: continue

            if elem_json['server'].lower() in ["waaw", "jetload"]: continue
            if elem_json['server'].lower() in servers:
               elem_json['server'] = servers[elem_json['server'].lower()]

            matches.append(elem_json.copy())

    return matches, langs


def play(item):
    logger.info()
    
    kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': -1, 'cf_assistant': False, 'follow_redirects': True, 
              'headers': {'Referer': host}, 'CF': False, 'canonical': {}}
    item.setMimeType = 'application/vnd.apple.mpegurl'

    soup = AlfaChannel.create_soup(item.url, **kwargs)
    if not soup or not soup.find("script"):
        return []
    soup = soup.find("script", string=re.compile('start.onclick')).string

    item.url = scrapertools.find_single_match(str(soup), "url\s*=\s*'([^']+)'")
    if item.url:
        itemlist = servertools.get_servers_itemlist([item])
    else:
        itemlist = []

    if item.server.lower() == "zplayer":
        item.url += "|referer=%s" % host
        
        itemlist = [item]
    
    return itemlist


def actualizar_titulos(item):
    logger.info()
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    return AlfaChannel.do_actualizar_titulos(item)


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + 'search?q=' + texto

        if texto:
            item.c_type = 'search'
            item.texto = texto
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)

    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'archives/movies'

        itemlist = list_all(item)

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
