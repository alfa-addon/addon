# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys

import re
import traceback

from platformcode import config, logger
from core.item import Item
from core import servertools, channeltools, tmdb
from core import httptools
from modules import filtertools
from modules import autoplay

PY3 = sys.version_info[0] >= 3

if PY3:
    from lib import alfaresolver_py3 as alfaresolver
else:
    from lib import alfaresolver


SERVER = {
          "hlswish": "streamwish", "playerwish": "streamwish", "ghbrisk": "streamwish", "iplayerhls": "streamwish",
           "listeamed": "vidguard", "1fichier":"onefichier", "luluvdo": "lulustream", "lulu": "lulustream",
           "dhtpre": "vidhidepro", "peytonepre": "vidhidepro", "smoothpre": "vidhidepro"
          }

IDIOMAS = {"es": "CAST", "la": "LAT", "en_ES": "VOSE", "sub-es": "VOSE"}

CALIDADES = {
    "69efbcea-12fa-4de8-bd19-02fa4f3278e0":"HD-1080p",
    "0cff0831-29ef-402d-8261-2c9f1880d807":"HD-720p",
    "d9297a62-c289-4780-8c00-dab7d3249839":"HD-TS",
    "5f744bff-7374-40c2-8f22-bb493823d3b9":"CAM",
    "042a13b8-ea18-4e56-9d4e-aec2684746ec":"SD"
}

list_language = list(IDIOMAS.values())
list_quality = list(CALIDADES.values())
list_servers = list(set(SERVER.values()))

__channel__='yaske'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except Exception:
    __modo_grafico__ = True

parameters = channeltools.get_channel_parameters(__channel__)



canonical = {
             'channel': 'yaske', 
             'host': config.get_setting("current_host", 'yaske', default=''), 
             'host_alt': ["https://yaske.ru/"], 
             'host_black_list': [], 
             'pattern': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

api = "%sapi/v1/channel/" %host

def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Estrenos Peliculas" , action="lista", url=api + "31?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1"))
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="lista", url=api + "2?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1"))
    itemlist.append(Item(channel=item.channel, title="Estrenos Series" , action="lista", url=api + "30?0returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1"))
    itemlist.append(Item(channel=item.channel, title="Series" , action="lista", url=api + "3?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1"))
    itemlist.append(Item(channel=item.channel, title="Anime" , action="lista", url=api + "117?0returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1"))
    # itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "api/v1/value-lists/titleFilterLanguages,productionCountries,genres,titleFilterAgeRatings"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "%sapi/v1/search/%s?loader=searchPage" % (host,texto)
    try:
        return lista(item)
    except Exception:
        logger.error(traceback.format_exc())
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, referer=host, canonical=canonical).json
    if "/search/" in item.url:
        items = data['results']
        pagination = None
    elif data.get('pagination',''):
        items = data['pagination']['data']
        pagination = data['pagination']
    else:
        items = data['channel']['content']['data']
        pagination = None
    
    shown_half = 1 if item.half else 0
    items_half = 25
    items = items[items_half:] if shown_half == 1 else items[:items_half]
    
    for elem in items:
        series = elem['is_series']
        title = elem['name']
        thumbnail = elem['poster']
        
        language = []
        if elem.get('availableLanguages', ''):
            idiomas = elem['availableLanguages']
            for idioma in idiomas:
                lang = idioma['language']
                language.append(IDIOMAS.get(lang, lang))
        
        year = '-'
        if elem.get('year', ''):
            year = elem['year']
        
        new_item = Item(channel=item.channel, title=title, thumbnail=thumbnail, 
                        language=language, infoLabels={"year": year})
        if series:
            new_item.id = elem['id']
            # new_item.id = elem['primary_video']['title_id']
            # if elem.get('primary_video', ''):
                # new_item.season_num = elem['primary_video']['season_num']
                # https://yaske.ru/api/v1/titles/39?loader=titlePage
            # new_item.url = "%sapi/v1/titles/%s/seasons/" %(host, new_item.id)
            new_item.url = "%sapi/v1/titles/%s?loader=titlePage" %(host, new_item.id)
            new_item.action = "seasons"
            new_item.contentSerieName = title
        else:
            if elem.get('primary_video', ''):
                vid = elem['primary_video']['id']
                new_item.url = "%sapi/v1/watch/%s" %(host, vid)
            else:
                new_item.id = elem['id']
            new_item.action = "findvideos"
            new_item.contentTitle = title
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, True)
    
    if shown_half == 0:
        itemlist.append(item.clone(title="Siguiente >", half=1))
    
    elif pagination and pagination.get('next_page', ''):
        next_page =pagination['next_page']
        if next_page:
            next_page = re.sub(r"&page=\d+", "&page={0}".format(next_page), item.url)
            itemlist.append(item.clone(title="Siguiente >", half=0, url=next_page))
            # itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    
    infoLabels = item.infoLabels
    
    url = "%sapi/v1/titles/%s?loader=titlePage" %(host, item.id)
    data = httptools.downloadpage(url, referer=host, canonical=canonical).json
    
    try:
        item.season_num = data['title']['primary_video']['season_num']# if data['title'].get('primary_video', '') else data['seasons']['total']
    except:
        item.season_num = data['seasons']['total']
    
    total = int(item.season_num)
    te = 1
    while te <= total:
        season = te
        url = "%sapi/v1/titles/%s/seasons/%s?loader=seasonPage" %(host, item.id, season)
        te +=1
        if int(season) < 10:
            season = "0%s" %season
        title = "Temporada %s" % season
        infoLabels["season"] = season
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="episodesxseasons",
                             infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url, id= item.id,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    
    season = infoLabels["season"]
    
    data = httptools.downloadpage(item.url, referer=host, canonical=canonical).json
    data = data['episodes']
    for elem in data['data']:
        if elem['primary_video']:
            vid = elem['primary_video']['id']
            url = "%sapi/v1/watch/%s" %(host, vid)
            cap =  elem['primary_video']['episode_num']
            if int(cap) < 10:
                cap = "0%s" % cap
            title = "%sx%s" % (season, cap)
            infoLabels["episode"] = cap
            itemlist.append(Item(channel=item.channel, title=title, url=url, action="findvideos",
                                     infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    a = len(itemlist)-1
    for i in itemlist:
        if a >= 0:
            title= itemlist[a].title
            titulo = itemlist[a].infoLabels['episodio_titulo']
            title = "%s %s" %(title, titulo)
            itemlist[a].title = title
            a -= 1
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist[:-1]:
        itemlist += episodesxseasons(tempitem)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    if not item.url:
        url = "%sapi/v1/titles/%s?loader=titlePage" %(host, item.id)
        data = httptools.downloadpage(url, referer=host, canonical=canonical).json
        if data['title'].get('primary_video',''):
            vid = data['title']['primary_video']['id']
            item.url = "%sapi/v1/watch/%s" %(host, vid)
    if item.url:
        data = httptools.downloadpage(item.url, referer=host, canonical=canonical).json
    series = ""
    if data['title'].get('is_series'):
        series = data['title']['is_series']
    
    videos = data['title']['videos']
    if data['title'].get('downloads', ''):
        videos += data['title']['downloads']
    elif data.get('alternative_videos', ''):
        videos += data['alternative_videos']
    links = []
    for elem in videos:
        # link = elem['src']
        hash = elem['hash']
        if hash in links:
            continue
        else: 
            links.append(hash)
        quality = CALIDADES.get(elem['quality'], 'HD-1080p')
        lang = elem['language']
        domain = elem['domain'].split(".")[0].lower()
        if domain in ["katfile", "nitroflare", "dailyuploads"]:
            continue
        language = IDIOMAS.get(lang, lang)
        server = SERVER.get(domain,domain)
        # itemlist.append(Item(channel=item.channel, action="play", server=server, title=server, contentTitle = item.contentTitle, url=hash, language=language))
        itemlist.append(item.clone(action="play", server=server, contentTitle = item.contentTitle, url=hash, language=language, quality=quality))
    
    # Ordenar por language
    itemlist.sort(key=lambda x: x.language)
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not series:
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist


def play(item):
    logger.info()
    
    url = alfaresolver.go_to_the_pub(item.url)
    
    devuelve = servertools.findvideosbyserver(url, item.server)
    if devuelve:
        item.url =  devuelve[0][1]
    
    return [item]


# def play(item):
    # logger.info()
    # itemlist = []
    
    # url = alfaresolver.go_to_the_pub(item.url)
    # itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    # itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # return itemlist
