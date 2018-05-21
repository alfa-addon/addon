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

host = "https://pepecine.io"

IDIOMAS = {'es': 'Español', 'en': 'Inglés', 'la': 'Latino', 'su': 'VOSE', 'vo': 'VO', 'otro': 'OVOS'}
list_idiomas = IDIOMAS.values()
list_language = ['default']

perpage = 20

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(title = "Películas"))

    itemlist.append(item.clone(
                         title  = "    Últimas películas",
                         url    = host + '/las-peliculas-online',
                         action = 'list_latest',
                         type   = 'movie'))

    itemlist.append(item.clone(title  = "    Películas por género",
                               url    = host + '/ver-pelicula',
                               action = 'genero',
                               type   = 'movie'))

    itemlist.append(item.clone(title  = "    Todas las películas",
                               url    = host + '/ver-pelicula',
                               action = 'list_all',
                               type   = 'movie'))

    itemlist.append(Item(title = "Series"))

    itemlist.append(item.clone(title  = "    Últimas series",
                               url    = host + '/las-series-online',
                               action = 'list_latest',
                               type   = 'series'))

    itemlist.append(item.clone(title  = "    Series por género",
                               url    = host + '/ver-serie-tv',
                               action = 'genero',
                               type   = 'series'))

    itemlist.append(item.clone(title  = "    Todas las series",
                               url    = host + '/ver-serie-tv',
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
    data = get_source(data_url)
    patron = "<div class='online'>.*?<img src=(.*?) class=.*?alt=(.*?) title=.*?"
    patron += "<b><a href=(.*?) target=.*?align=right><div class=s7>(.*?) <"
    matches = re.compile(patron,re.DOTALL).findall(data)
    count = 0
    for thumbnail, title, url, language in matches:
        count += 1

        if count < item.indexp:
            continue

        if count >= item.indexp + perpage:
            break;

        path = scrapertools.find_single_match(thumbnail, "w\w+(/\w+.....)")
        filtro_list = {"poster_path": path}
        filtro_list = filtro_list.items()
        itemlist.append(item.clone(action       = 'findvideos',
                                   title        = title,
                                   url          = host + url,
                                   thumbnail    = thumbnail,
                                   language     = language,
                                   infoLabels   = {'filtro': filtro_list},
                                   )
                            )
    tmdb.set_infoLabels(itemlist)

    # Desde novedades no tenemos el elemento item.channel
    if item.channel:
        itemlist.append(item.clone(title = "Página siguiente >>>",
                                   indexp = item.indexp + perpage
                                   )
                        )
        if item.indexp > 1:
            itemlist.append(item.clone(title = "<<< Página anterior",
                                       indexp = item.indexp - perpage
                                       )
                            )

    return itemlist

def list_all(item):
    logger.info()
    itemlist=[]

    if not item.page:
        item.page = 1

    genero = scrapertools.find_single_match(item.url, "genre=(\w+)")
    data= get_source(item.url)
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
            new_item.contentTitle = element['title']
            new_item.fulltitle = element['title']
            if new_item.extra != "links_encoded":
                new_item.url = host + "/ver-pelicula/" + str(element['id'])

        elif item.type == 'series':
                new_item.action = 'seasons'
                new_item.url = host + "/ver-serie-tv/" + str(element['id'])
                new_item.show = element['title']

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    itemlist.append(item.clone(title = 'Página siguiente >>>',
                               page  = item.page + 1))

    if (int(item.page) > 1):
        itemlist.append(item.clone(title = '<<< Página anterior',
                                   page  = item.page - 1))

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
    data = httptools.downloadpage(item.url).data

    reSeasons = re.findall("href *= *[\"']([^\"']+)[\"'][^\"']+[\"']sezon[^>]+>([^<]+)+", data)

    itemlist = [item.clone(action = "seasons_episodes",
                          title = title,
                          url = url) for url, title in reSeasons]

    if len(itemlist) == 1:
        itemlist = seasons_episodes(itemlist[0])

    # Opción "Añadir esta serie a la videoteca de XBMC"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios"))

    return itemlist

def seasons_episodes(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    reEpisodes = re.findall("<a[^>]+col-sm-3[^>]+href *= *[\"'](?P<url>[^\"']+).*?<img[^>]+src *= *[\"'](?P<thumbnail>[^\"']+).*?<a[^>]+>(?P<title>.*?)</a>", data, re.MULTILINE | re.DOTALL)

    seasons = [item.clone(action = "findvideos",
                          title = re.sub("<b>Episodio (\d+)</b> - T(\d+) \|[^\|]*\| ".format(item.show), "\g<2>x\g<1> - ", title),
                          thumbnail = thumbnail,
                          url = url) for url, thumbnail, title in reEpisodes]

    return seasons


def findvideos(item):
    logger.info()
    itemlist=[]

    if item.extra != "links_encoded":

        # data = httptools.downloadpage(item.url).data
        # linksRE = re.findall("getFavicon\('(?P<url>[^']+)[^>]+>[^>]+>(?P<language>[^<]+).+?<td[^>]+>(?P<quality>[^<]*).+?<td[^>]+>(?P<antiquity>[^<]*)", data, re.MULTILINE | re.DOTALL)
        # for url, language, quality, antiquity in linksRE:
        #     logger.info("URL = " + url);


        data = httptools.downloadpage(item.url).data
        patron  = "renderTab.bind.*?'([^']+).*?"
        patron += "app.utils.getFavicon.*?<img [^>]*src *= *[\"']/([^\.]+).*?"
        patron += 'color:#B1FFC5;">([^<]+)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl, language, scrapedquality in matches:
            isDD = language.startswith("z")
            if isDD:
                language = language[1:]

            language = language[0:2]
            language = IDIOMAS.get(language, language)

            title = ("Ver" if not isDD else "Descargar") + " enlace en %s [" + language + "] [" + scrapedquality + "]"
            if not isDD:
                itemlist.append(item.clone(action = 'play',
                                           title = title,
                                           url = scrapedurl,
                                           language = language
                                           )
                                )
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    else:
        for link in item.url:

            language = scrapertools.find_single_match(link['label'], '/([^\.]+)')
            isDD = language.startswith("z")
            if isDD:
                language = language[1:]

            language = language[0:2]

            if not isDD:
                itemlist.append(item.clone(action='play',
                                     title = item.title,
                                     url= link['url'],
                                     language=IDIOMAS.get(language, language),
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
