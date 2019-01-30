# -*- coding: utf-8 -*-

import re, urllib

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools
from channels import filtertools


host = 'https://pelis123.tv/'


IDIOMAS = {'LAT': 'LAT', 'ESP':'ESP', 'VOSE': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'fembed', 'directo']
list_quality = []

__channel__='pelis123'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Nuevas películas', action = 'list_all', url = host + 'film.html', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'featured.html', search_type = 'movie' ))
    # ~ itemlist.append(item.clone( title = 'Estrenos de cine', action = 'list_all', url = host + 'cinema.html', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Nuevas series', action = 'list_all', url = host + 'series.html', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def anios(item):
    logger.info()
    return extraer_opciones(item, 'year')

def generos(item):
    logger.info()
    return extraer_opciones(item, 'genre')

def idiomas(item):
    logger.info()
    return extraer_opciones(item, 'lang')

def paises(item):
    logger.info()
    return extraer_opciones(item, 'country')

def extraer_opciones(item, select_id):
    itemlist = []

    url = host + 'search.html'
    data = httptools.downloadpage(url).data
    # ~ logger.debug(data)
    url += '?type=' + ('series' if item.search_type == 'tvshow' else 'movies')
    url += '&order=last_update&order_by=desc'

    bloque = scrapertools.find_single_match(data, '<select name="%s"[^>]*>(.*?)</select>' % select_id)
    
    matches = re.compile('<option value="([^"]+)">([^<]+)', re.DOTALL).findall(bloque)
    for valor, titulo in matches:
        itemlist.append(item.clone( title=titulo.capitalize(), url= url + '&' + select_id + '=' + valor, action='list_all' ))

    if select_id == 'year': # años en orden inverso
        return sorted(itemlist, key=lambda it: it.title, reverse=True)
    else:
        return sorted(itemlist, key=lambda it: it.title)


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def detectar_idiomas(txt):
    languages = []
    if 'Castellano' in txt: languages.append('ESP')
    if 'Latino' in txt: languages.append('LAT')
    if 'Subtitulado' in txt: languages.append('VOSE')
    return languages

def detectar_idioma(txt):
    languages = detectar_idiomas(txt)
    if len(languages) > 0: return languages[0]
    return '?'

def list_all(item):
    logger.info()
    itemlist = []
    
    es_busqueda = '&q=' in item.url

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    patron = '<div class="tray-item" episode-tag="([^"]+)">\s*<div class="tray-item-content">'
    patron += '\s*<a href="([^"]+)">\s*<img class="[^"]*" src="([^"]+)">'
    patron += '.*?<div class="tray-item-title">([^<]+)</div>'
    patron += '.*?<div class="tray-item-title-en">([^<]+)</div>'
    patron += '.*?<div class="tray-item-quality">([^<]+)</div>'
    patron += '.*?<div class="tray-item-episode">([^<]+)</div>'
    patron += '.*? data-original-title=".*? \((\d+)\)"'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    for langs, url, thumb, title, title_en, quality, episode, year in matches:
        th = scrapertools.find_single_match(thumb, r'poster%2F(.*?)$')
        thumb = 'https://cdn.pelis123.tv/poster/' + th
        
        languages = detectar_idiomas(langs)
        
        tipo = 'movie' if 'MIN' in episode else 'tvshow'
        if item.search_type not in ['all', tipo]: continue

        if tipo == 'tvshow':
            m = re.match('(.*?) S\d+$', title)
            if m: title = m.group(1)

        title = title.strip()
        quality = quality.strip().upper()
        
        titulo = title
        if len(languages) > 0: 
            titulo += ' [COLOR pink][%s][/COLOR]' % ','.join(languages)
        if quality != '': 
            titulo += ' [COLOR pink][%s][/COLOR]' % quality
        if item.search_type == 'all': 
            titulo += ' [COLOR %s](%s)[/COLOR]' % ('red' if tipo == 'tvshow' else 'green', tipo)
            
        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            if es_busqueda: # descartar series que se repiten con diferentes temporadas
                if title in [it.contentSerieName for it in itemlist]: continue
                
            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, 'active">\d+</a>(?:\s*</div>\s*<div class="btn-group">|)\s*<a href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    matches = re.compile('href="([^"]+)" class="[^"]*">Temporada (\d+)</a>', re.DOTALL).findall(data)
    for url, numtempo in matches:
        itemlist.append(item.clone( action='episodesxseason', title='Temporada %s' % numtempo, url = url,
                                    contentType='season', contentSeason=numtempo ))
        
    m = re.match('.*?-season-(\d+)-[a-z0-9A-Z]+-[a-z0-9A-Z]+\.html$', item.url)
    if m:
        itemlist.append(item.clone( action='episodesxseason', title='Temporada %s' % m.group(1), url = item.url,
                                    contentType='season', contentSeason=m.group(1) ))
    tmdb.set_infoLabels(itemlist)
    
    # if len(itemlist) == 1:
        # itemlist = seasons_episodes(itemlist[0])

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    
    
    # return sorted(itemlist, key=lambda it: it.title)
    return itemlist


# ~ # Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
# ~ def tracking_all_episodes(item):
    # ~ return episodios(item)
    
    
def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
# def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    url = scrapertools.find_single_match(data, 'href="([^"]+)" action="watch"')
    data = httptools.downloadpage(url).data
    # ~ logger.debug(data)

    patron = '<div class="watch-playlist-item(?:  playing|) " data-season="(\d+)" data-episode="(\d+)">'
    patron += '\s*<a href="([^"]+)"'
    patron += '.*?<img src="([^"]+)"'
    patron += '.*?<span class="watch-playlist-title">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for season, episode, url, thumb, title in matches:
        if item.contentSeason and item.contentSeason != int(season):
            continue

        titulo = '%sx%s %s' % (season, episode, title)
        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def detectar_server(servidor):
    servidor = servidor.lower()
    if 'server ' in servidor: return 'directo'
    elif servidor == 'fast': return 'fembed'
    # ~ elif 'server 1' in servidor: return 'fastproxycdn' # inexistente
    # ~ elif 'server 4' in servidor: return '404' # error 404 !?
    return servidor

def findvideos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)')

    # ~ https://pelis123.tv/watch/blackkklansman-2018-ocffc-ux2.html
    # ~ https://pelis123.tv/watch/lethal-weapon-season-1-episode-18-oa06e-fds.html
    movie_id = scrapertools.find_single_match(item.url, '([a-z0-9A-Z]+-[a-z0-9A-Z]+)\.html$')
    m = re.match('.*?-episode-(\d+)-[a-z0-9A-Z]+-[a-z0-9A-Z]+\.html$', item.url)
    episode = m.group(1) if m else ''

    url = host + 'ajax/watch/list'
    post = 'movie_id=%s&episode=%s' % (movie_id, episode)
    headers = { 'X-CSRF-TOKEN': token }
    data = jsontools.load(httptools.downloadpage(url, post=post, headers=headers).data)
    # ~ logger.debug(data)
    for idioma, enlaces in data['list'].items():
        for servidor, url in enlaces.items():
            titulo = detectar_server(servidor)
            titulo += ' [%s]' % detectar_idioma(idioma)
            titulo +=  item.quality
            for url_play in url:
                itemlist.append(item.clone( channel = item.channel, action = 'play', server = detectar_server(servidor),
                                      title = titulo, url = url_play, 
                                      language = detectar_idioma(idioma), quality = 'HD'  #, other = servidor
                               ))
                               
    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle))
    
    
    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url, ignore_response_code=True).data
    # ~ logger.debug(data)
    
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)')
    if url == '':
        url = scrapertools.find_single_match(data, '<source src="([^"]+)')

    if 'fastproxycdn.net' in url: url = '' # ya no existe
        
    # ~ logger.debug(url)
    if url != '':
        itemlist.append(item.clone(url = url))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    if item.search_type == "" :
        item.search_type = 'all'
    try:
        item.url = host + 'search.html'
        item.url += '?type=' + ('series' if item.search_type == 'tvshow' else 'movies' if item.search_type == 'movie' else '')
        item.url += '&order=last_update&order_by=desc'
        item.url += '&q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
