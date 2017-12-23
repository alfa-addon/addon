# -*- coding: utf-8 -*-

import re
import urllib
import unicodedata

from core import channeltools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

idiomas1 = {"/es.png":"CAST","/en_es.png":"VOSE","/la.png":"LAT","/en.png":"ENG"}
domain = "yaske.ro"
HOST = "http://www." + domain
HOST_MOVIES = "http://peliculas." + domain + "/now_playing/"
HOST_TVSHOWS = "http://series." + domain + "/popular/"
HOST_TVSHOWS_TPL = "http://series." + domain + "/tpl"
parameters = channeltools.get_channel_parameters('yaske')
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
color1, color2, color3 = ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E']


def mainlist(item):
    logger.info()
    itemlist = []
    item.url = HOST
    item.text_color = color2
    item.fanart = fanart_host
    thumbnail = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/4/verdes/%s.png"

    itemlist.append(item.clone(title="Peliculas", text_bold=True, viewcontent='movies',
                               thumbnail=thumbnail % 'novedades', viewmode="movie_with_plot"))
    itemlist.append(item.clone(title="    Novedades", action="peliculas", viewcontent='movies',
                               url=HOST_MOVIES,
                               thumbnail=thumbnail % 'novedades', viewmode="movie_with_plot"))
    itemlist.append(item.clone(title="    Estrenos", action="peliculas",
                               url=HOST + "/premiere", thumbnail=thumbnail % 'estrenos'))
    itemlist.append(item.clone(title="    Género", action="menu_buscar_contenido", thumbnail=thumbnail % 'generos', viewmode="thumbnails",
                               url=HOST
                               ))
    itemlist.append(item.clone(title="    Buscar película", action="search", thumbnail=thumbnail % 'buscar',
                               type = "movie" ))

    itemlist.append(item.clone(title="Series", text_bold=True, viewcontent='movies',
                               thumbnail=thumbnail % 'novedades', viewmode="movie_with_plot"))
    itemlist.append(item.clone(title="    Novedades", action="series", viewcontent='movies',
                               url=HOST_TVSHOWS,
                               thumbnail=thumbnail % 'novedades', viewmode="movie_with_plot"))
    itemlist.append(item.clone(title="    Buscar serie", action="search", thumbnail=thumbnail % 'buscar',
                               type = "tvshow" ))

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    url_p = scrapertools.find_single_match(item.url, '(.*?).page=')
    page = scrapertools.find_single_match(item.url, 'page=([0-9]+)')
    if not page:
        page = 1
        url_p = item.url
    else:
        page = int(page) + 1
    if "search" in item.url:
        url_p += "&page=%s" %page
    else:
        url_p += "?page=%s" %page
    data = httptools.downloadpage(url_p).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '(?s)class="post-item-image btn-play-item".*?'
    patron += 'href="(http://series[^"]+)">.*?'
    patron += '<img data-original="([^"]+)".*?'
    patron += 'glyphicon-play-circle"></i>([^<]+).*?'
    patron += 'glyphicon-calendar"></i>([^<]+).*?'
    patron += 'text-muted f-14">(.*?)</h3'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedepisodes, year, scrapedtitle in matches:
        scrapedepisodes.strip()
        year = year.strip()
        contentSerieName = scrapertools.htmlclean(scrapedtitle.strip())
        title = "%s (%s)" %(contentSerieName, scrapedepisodes)
        if "series" in scrapedurl:
            itemlist.append(Item(channel=item.channel, action="temporadas", title=title, url=scrapedurl,
                                 thumbnail=scrapedthumbnail, contentSerieName=contentSerieName,
                                 infoLabels={"year": year}, text_color=color1))
    # Obtenemos los datos basicos de todas las peliculas mediante multihilos
    tmdb.set_infoLabels(itemlist, True)

    # Si es necesario añadir paginacion
    patron_next_page = 'href="([^"]+)">\s*&raquo;'
    matches_next_page = scrapertools.find_single_match(data, patron_next_page)
    if matches_next_page and len(itemlist)>0:
       itemlist.append(
            Item(channel=item.channel, action="series", title=">> Página siguiente", thumbnail=thumbnail_host,
                 url=url_p, folder=True, text_color=color3, text_bold=True))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    post = []
    data = httptools.downloadpage(item.url).data
    patron  = 'media-object" src="([^"]+).*?'
    patron += 'media-heading">([^<]+).*?'
    patron += '<code>(.*?)</div>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, scrapedcapitulos in matches:
        id = scrapertools.find_single_match(item.url, "yaske.ro/([0-9]+)")
        season = scrapertools.find_single_match(scrapedtitle, "[0-9]+")
        title = scrapedtitle + " (%s)" %scrapedcapitulos.replace("</code>","").replace("\n","")
        post = {"data[season]" : season, "data[id]" : id, "name" : "list_episodes" , "both" : "0", "type" : "template"}
        post = urllib.urlencode(post)
        item.infoLabels["season"] = season
        itemlist.append(item.clone(action = "capitulos",
                             post = post,
                             title = title,
                             url = HOST_TVSHOWS_TPL
                             ))
    tmdb.set_infoLabels(itemlist)
    if config.get_videolibrary_support():
        itemlist.append(Item(channel=item.channel, title =""))
        itemlist.append(item.clone(action = "add_serie_to_library",
                             channel = item.channel,
                             extra = "episodios",
                             title = '[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url = item.url
                             ))
    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    for tempitem in templist:
        itemlist += capitulos(tempitem)
    return itemlist


def capitulos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, post=item.post).data
    data = data.replace("<wbr>","")
    patron  = 'href=."([^"]+).*?'
    patron += 'media-heading.">([^<]+).*?'
    patron += 'fecha de emisi.*?: ([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapeddate in matches:
        scrapedtitle = scrapedtitle + " (%s)" %scrapeddate
        episode = scrapertools.find_single_match(scrapedurl, "capitulo-([0-9]+)")
        query = item.contentSerieName + " " + scrapertools.find_single_match(scrapedtitle, "\w+")
        item.infoLabels["episode"] = episode
        itemlist.append(item.clone(action = "findvideos",
                            title = scrapedtitle.decode("unicode-escape"),
                            query = query.replace(" ","+"),
                            url = scrapedurl.replace("\\","")
                            ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    try:
        item.url = HOST + "/search/?query=" + texto.replace(' ', '+')
        item.extra = ""
        if item.type == "movie":
            itemlist.extend(peliculas(item))
        else:
            itemlist.extend(series(item))
        if itemlist[-1].title == ">> Página siguiente":
            item_pag = itemlist[-1]
            itemlist = sorted(itemlist[:-1], key=lambda Item: Item.contentTitle)
            itemlist.append(item_pag)
        else:
            itemlist = sorted(itemlist, key=lambda Item: Item.contentTitle)
        return itemlist
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = HOST
        elif categoria == 'infantiles':
            item.url = HOST + "/genre/16/"
        elif categoria == 'terror':
            item.url = HOST + "/genre/27/"
        else:
            return []
        itemlist = peliculas(item)
        if itemlist[-1].title == ">> Página siguiente":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    url_p = scrapertools.find_single_match(item.url, '(.*?).page=')
    page = scrapertools.find_single_match(item.url, 'page=([0-9]+)')
    if not page:
        page = 1
        url_p = item.url
    else:
        page = int(page) + 1
    if "search" in item.url:
        url_p += "&page=%s" %page
    else:
        url_p += "?page=%s" %page
    data = httptools.downloadpage(url_p).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '(?s)class="post-item-image btn-play-item".*?'
    patron += 'href="([^"]+)">.*?'
    patron += '<img data-original="([^"]+)".*?'
    patron += 'glyphicon-calendar"></i>([^<]+).*?'
    patron += 'post(.*?)</div.*?'
    patron += 'text-muted f-14">(.*?)</h3'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, year, idiomas, scrapedtitle in matches:
        query = scrapertools.find_single_match(scrapedurl, 'yaske.ro/[0-9]+/(.*?)/').replace("-","+")
        year = year.strip()
        patronidiomas = '<img src="([^"]+)"'
        matchesidiomas = scrapertools.find_multiple_matches(idiomas, patronidiomas)
        idiomas_disponibles = []
        for idioma in matchesidiomas:
            for lang in idiomas1.keys():
                if idioma.endswith(lang):
                    idiomas_disponibles.append(idiomas1[lang])
        if idiomas_disponibles:
            idiomas_disponibles = "[" + "/".join(idiomas_disponibles) + "]"
            contentTitle = scrapertools.htmlclean(scrapedtitle.strip())
            title = "%s %s" % (contentTitle, idiomas_disponibles)
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl,
                                 thumbnail=scrapedthumbnail, contentTitle=contentTitle, query = query,
                                 infoLabels={"year": year}, text_color=color1))
    # Obtenemos los datos basicos de todas las peliculas mediante multihilos
    tmdb.set_infoLabels(itemlist)

    # Si es necesario añadir paginacion
    patron_next_page = 'href="([^"]+)">\s*&raquo;'
    matches_next_page = scrapertools.find_single_match(data, patron_next_page)
    if matches_next_page and len(itemlist)>0:
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=">> Página siguiente", thumbnail=thumbnail_host,
                 url=url_p, folder=True, text_color=color3, text_bold=True))
    return itemlist


def menu_buscar_contenido(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'Generos.*?</ul>'
    data = scrapertools.find_single_match(data, patron)
    patron = 'href="([^"]+)">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        url = HOST + scrapedurl
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = scrapedtitle,
                             url = url,
                             text_color = color1,
                             contentType = 'movie',
                             folder = True,
                             viewmode = "movie_with_plot"
                             ))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    sublist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?s)id="online".*?server="([^"]+)"'
    mserver = scrapertools.find_single_match(data, patron)
    if not item.query:
        item.query = scrapertools.find_single_match(item.url, "peliculas.*?/[0-9]+/([^/]+)").replace("-","+")
    url_m = "http://olimpo.link/?q=%s&server=%s" %(item.query, mserver)
    patron  = 'class="favicon.*?domain=(?:www\.|)([^\.]+).*?text-overflow.*?href="([^"]+).*?'
    patron += '\[([^\]]+)\].*?\[([^\]]+)\]'
    data = httptools.downloadpage(url_m).data
    matches = scrapertools.find_multiple_matches(data, patron)
    page = 2
    while len(matches)>0:
        for server, url, idioma, calidad in matches:
            if "drive" in server:
                server = "gvideo"
            sublist.append(item.clone(action="play", url=url, folder=False, text_color=color1, quality=calidad.strip(),
                                  language=idioma.strip(),
                                  server = server,
                                  title="Ver en %s %s" %(server, calidad)
                                  ))
        data = httptools.downloadpage(url_m + "&page=%s" %page).data
        matches = scrapertools.find_multiple_matches(data, patron)
        page +=1
    sublist = sorted(sublist, key=lambda Item: Item.quality + Item.server)
    for k in ["Español", "Latino", "Ingles - Sub Español", "Ingles"]:
        lista_idioma = filter(lambda i: i.language == k, sublist)
        if lista_idioma:
            itemlist.append(item.clone(title=k, folder=False, infoLabels = "",
                                 text_color=color2, text_bold=True, thumbnail=thumbnail_host))
            itemlist.extend(lista_idioma)

    tmdb.set_infoLabels(itemlist, True)
    # Insertar items "Buscar trailer" y "Añadir a la videoteca"
    if itemlist and item.extra != "library":
        title = "%s [Buscar trailer]" % (item.contentTitle)
        itemlist.insert(0, item.clone(channel="trailertools", action="buscartrailer",
                                      text_color=color3, title=title, viewmode="list"))

        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, text_color="green",
                                 contentTitle=item.contentTitle, extra="library", thumbnail=thumbnail_host))
    return itemlist

def play(item):
    logger.info()
    itemlist = []
    ddd = httptools.downloadpage(item.url).data
    url = "http://olimpo.link" + scrapertools.find_single_match(ddd, '<iframe src="([^"]+)')
    item.url = httptools.downloadpage(url + "&ge=1", follow_redirects=False, only_headers=True).headers.get("location", "")
    itemlist.append(item.clone(server = ""))
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist
