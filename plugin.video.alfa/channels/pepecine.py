# -*- coding: utf-8 -*-
# -*- Channel PepeCine -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urlparse

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item, InfoLabels
from platformcode import config, logger
from channels import filtertools

host = "https://pepecine.me" # "https://pepecine.io"

IDIOMAS = {'c': 'Castellano', 'i': 'Inglés', 'l': 'Latino', 's': 'VOSE', 'v': 'VO'}
list_idiomas = IDIOMAS.values()
list_language = ['default']

perpage = 20

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(title = "Películas"))

    itemlist.append(item.clone(
                         title  = "    Últimas películas",
                         url    = host + '/mis-peliculas-online',
                         action = 'list_latest',
                         type   = 'movie'))

    itemlist.append(item.clone(title  = "    Películas por género",
                               url    = host + '/ver-la-pelicula',
                               action = 'genero',
                               type   = 'movie'))

    itemlist.append(item.clone(title  = "    Todas las películas",
                               url    = host + '/ver-la-pelicula',
                               action = 'list_all',
                               type   = 'movie'))

    itemlist.append(Item(title = "Series"))

    itemlist.append(item.clone(title  = "    Últimos episodios",
                               url    = host + '/mis-series-online',
                               action = 'list_latest',
                               type   = 'series'))

    itemlist.append(item.clone(title  = "    Series por género",
                               url    = host + '/ver-la-serie',
                               action = 'genero',
                               type   = 'series'))

    itemlist.append(item.clone(title  = "    Todas las series",
                               url    = host + '/ver-la-serie',
                               action ='list_all',
                               type   = 'series'))

    itemlist.append(item.clone(title  = "Buscar",
                               url    = host + '/donde-ver?q=',
                               action ='search',
                               type   = 'movie'))

    return itemlist


def genero(item):
    logger.info()
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    patron  = '<a href="(\?genre[^"]+)"[^>]*>[^>]+>(.+?)</li>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action = "list_all",
                                   title = scrapedtitle,
                                   url = item.url + scrapedurl
                        ))
    return itemlist

def newest(categoria):
    logger.info("categoria: %s" % categoria)
    itemlist = []

    if categoria == 'peliculas':
        itemlist = list_latest(Item(url    = host + '/las-peliculas-online',
                                    type   = 'movie'))
    elif categoria == 'series':
        itemlist = list_latest(Item(url    = host + '/las-series-online',
                                    type   = 'series'))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.extra = "busca"
    if texto == '':
        return []

    return sub_search(item)

def search_section(item, data, sectionType):
    logger.info()
    sectionResultsRE = re.findall("<a[^<]+href *= *[\"'](?P<url>[^\"']+)[^>]>[^<]*<img[^>]+src *= *[\"'](?P<thumbnail>[^\"']+).*?<figcaption[^\"']*[\"'](?P<title>.*?)\">", data, re.MULTILINE | re.DOTALL)

    itemlist = []
    for url, thumbnail, title in sectionResultsRE:
        newitem = item.clone(action = "seasons" if sectionType == "series" else "findvideos",
                             title = title,
                             thumbnail = thumbnail,
                             url = url)
        if sectionType == "series":
            newitem.show = title;
        itemlist.append(newitem)

    return itemlist

def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    searchSections = re.findall("<div[^>]+id *= *[\"'](?:movies|series)[\"'].*?</div>", data, re.MULTILINE | re.DOTALL)

    logger.info("Search sections = {0}".format(len(searchSections)))
    itemlist.extend(search_section(item, searchSections[0], "movies"))
    itemlist.extend(search_section(item, searchSections[1], "series"))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_latest(item):
    logger.info()

    if not item.indexp:
        item.indexp = 1

    itemlist = []
    data = get_source(item.url)
    data_url= scrapertools.find_single_match(data,'<iframe.*?src=(.*?) ')
    data = get_source(data_url).decode('iso-8859-1').encode('utf8')
    patron = "<div class='online'>.*?<img src=(.*?) class=.*?alt=(.*?) title=.*?"
    patron += "<b><a href=(.*?) target=.*?align=right><div class=s7>(.*?) <"
    matches = re.compile(patron,re.DOTALL).findall(data)
    # Como len(matches)=300, se controla una paginación interna y se muestran en bloques de 20 (perpage)
    # Se descartan enlaces repetidos en la misma paginación pq algunas pelis se duplican por el idioma/calidad pero apuntan a la misma url
    count = 0
    for thumbnail, title, url, language in matches:
        count += 1

        if count < item.indexp:
            continue

        isDD, language = _extraer_dd_idioma(language)
        if isDD: 
            continue

        repe = False
        for it in itemlist:
            if it.url == host + url:
                repe = True
                break
        if repe:
            continue

        path = scrapertools.find_single_match(thumbnail, "w\w+(/\w+.....)")
        filtro_list = {"poster_path": path}
        filtro_list = filtro_list.items()

        new_item = item.clone(action       = 'findvideos',
                              title        = title,
                              url          = host + url,
                              thumbnail    = thumbnail,
                              language     = language,
                              infoLabels   = {'filtro': filtro_list, 'year': '-'}
                             )

        if item.type == 'series':
            new_item.contentType = 'episode'
            season_episode = scrapertools.find_single_match(title, ' (\d+)x(\d+)')
            if season_episode:
                new_item.contentSeason = season_episode[0]
                new_item.contentEpisodeNumber = season_episode[1]
                new_item.contentSerieName = re.sub(r' \d+x\d+', '', title).strip()
            else:
                new_item.contentSerieName = title
        else:
            new_item.contentType = 'movie'
            new_item.contentTitle = title

        itemlist.append(new_item)

        if len(itemlist) >= perpage:
            break;

    tmdb.set_infoLabels(itemlist)

    # Desde novedades no tenemos el elemento item.channel
    if item.channel and len(itemlist) >= perpage and count + 1 <= len(matches):
        itemlist.append( item.clone(title = "Página siguiente >>>", indexp = count + 1) )

    return itemlist

def list_all(item):
    logger.info()
    itemlist=[]

    if not item.page:
        item.page = 1

    genero = scrapertools.find_single_match(item.url, "genre=(\w+)")
    data = get_source(item.url)
    token = scrapertools.find_single_match(data, "token:.*?'(.*?)'")
    url = host+'/titles/paginate?_token=%s&perPage=%d&page=%d&order=mc_num_of_votesDesc&type=%s&minRating=&maxRating=&availToStream=1&genres[]=%s' % (token, perpage, item.page, item.type, genero)
    data = httptools.downloadpage(url).data

    if item.type == "series":
        # Remove links to speed-up (a lot!) json load
        data = re.sub(",? *[\"']link[\"'] *: *\[.+?\] *([,}])", "\g<1>", data)

    dict_data = jsontools.load(data)
    items = dict_data['items']

    for element in items:
        new_item = item.clone(
                       title = element['title']+' [%s]' % element['year'],
                       plot = element['plot'],
                       thumbnail = element['poster'],
                       infoLabels = {'year':element['year']})

        if "link" in element:
            new_item.url = element["link"]
            new_item.extra = "links_encoded"

        if item.type == 'movie':
            new_item.action = 'findvideos'
            new_item.contentType = 'movie'
            new_item.contentTitle = element['title']
            new_item.fulltitle = element['title']
            if new_item.extra != "links_encoded":
                new_item.url = host + "/ver-la-pelicula/" + str(element['id'])

        elif item.type == 'series':
                new_item.action = 'seasons'
                new_item.url = host + "/ver-la-serie/" + str(element['id'])
                new_item.show = element['title']
                new_item.contentType = 'tvshow'
                new_item.contentSerieName = element['title']

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    itemlist.append(item.clone(title = 'Página siguiente >>>',
                               page  = item.page + 1))

    return itemlist

def episodios(item):
    logger.info("url: %s" % item.url)
    itemlist = seasons(item)

    if len(itemlist) > 0 and itemlist[0].action != "findvideos":
        episodes = []
        for season in itemlist:
            episodes.extend([episode for episode in seasons_episodes(season)])
        itemlist = episodes

    return itemlist

def seasons(item):
    logger.info()
    itemlist=[]

    data = httptools.downloadpage(item.url).data

    reSeasons = re.findall("href *= *[\"']([^\"']+)[\"'][^\"']+[\"']sezon[^>]+>([^<]+)+", data)
    for url, title in reSeasons:
        new_item = item.clone(action = "seasons_episodes", title = title, url = url)
        new_item.contentType = 'season'
        new_item.contentSeason = title.replace('Temporada', '').strip()
        itemlist.append(new_item)        

    if len(itemlist) == 1:
        itemlist = seasons_episodes(itemlist[0])

    tmdb.set_infoLabels(itemlist)

    # Opción "Añadir esta serie a la videoteca de XBMC"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios"))

    return itemlist

def seasons_episodes(item):
    logger.info()
    itemlist=[]

    data = httptools.downloadpage(item.url).data

    reEpisodes = re.findall('<li class="media bord">(.*?)</li>', data, re.MULTILINE | re.DOTALL)
    for epi in reEpisodes:
        new_item = item.clone(action = "findvideos")
        new_item.url = scrapertools.find_single_match(epi, ' href="([^"]*)')
        new_item.thumbnail = scrapertools.find_single_match(epi, ' src="([^"]*)')
        new_item.contentType = 'episode'
        new_item.contentEpisodeNumber = scrapertools.find_single_match(epi, '<b>Episodio (\d+)</b>')
        title = scrapertools.find_single_match(epi, '<b>Episodio \d+</b> - T\d+ \|[^\|]*\| ([^<]*)').strip()
        new_item.title = '%sx%s - %s' % (str(item.contentSeason), str(new_item.contentEpisodeNumber), title)
            
        itemlist.append(new_item)        

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist=[]

    if item.extra != "links_encoded":
        data = httptools.downloadpage(item.url).data
        patron  = "renderTab\.bind[^']+'([^']+)"
        patron += '.*?<b[^>]*>([^<]*)<img src='
        patron += '.*?<td [^>]*>([^<]*)'
        patron += '.*?<td [^>]*>([^<]*)'

        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl, language, scrapedquality, scrapedwhen in matches:
            isDD, language = _extraer_dd_idioma(language)
            if not isDD:
                title = "%s [" + language + "] [" + scrapedquality + "] [" + scrapedwhen + "]"
                itemlist.append(item.clone(action = 'play',
                                           title = title,
                                           url = scrapedurl,
                                           language = language
                                           )
                                )
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    else:
        for link in item.url:
            isDD, language = _extraer_dd_idioma(link['label'])
            if not isDD:
                itemlist.append(item.clone(action='play',
                                     title = item.title,
                                     url= link['url'],
                                     language=language,
                                     quality=link['quality']))

        itemlist=servertools.get_servers_itemlist(itemlist)
        for videoitem in itemlist:
            videoitem.title = '%s [%s] [%s]' % (videoitem.server.capitalize(), videoitem.language, videoitem.quality)

    tmdb.set_infoLabels(itemlist)
    if itemlist and not item.show:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la videoteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(item.clone(title="Añadir a la videoteca",
                                           text_color="green",
                                           action="add_pelicula_to_library"
                                     ))
    return filtertools.get_links(itemlist, item, list_idiomas)


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]

# idiomas: l, c, s, i, v  (lat, cast, subt, inglés, vo). Si empieza por z es descarga directa
def _extraer_dd_idioma(lang):
    lang = lang.strip().lower()
    isDD = lang.startswith('z')
    lg = lang[1] if isDD else lang[0]
    return isDD, IDIOMAS.get(lg, lang)
