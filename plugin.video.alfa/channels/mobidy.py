# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools, channeltools
from channels import filtertools

from bs4 import BeautifulSoup
from channelselector import get_thumb

host = 'https://movidy.mobi'


SERVER = {'www.fembed.com': 'Fembed', 'femax20.com': 'Fembed', '1fichier.com': 'Onefichier', 'uqload.com': 'Uqload' , 'uptobox.com': 'Uptobox',
          'streamsb.net': 'Streamsb', 'dood.so': 'Doodstream', 'embed.mystream.to': 'Mystream', 'streamtape.com': 'Streamtape',
          'fastplay.to': 'Fastplay',
         }


IDIOMAS = {"es": "CAST", "la": "LAT", "lat": "LAT", "en": "VOSE"}

list_language = list(IDIOMAS.values())
list_quality = []
list_servers = list(SERVER.values())

__channel__='mobidy'

parameters = channeltools.get_channel_parameters(__channel__)
unif = parameters['force_unify']


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Peliculas" , action="sub_menu", url= host + "/secure/titles?type=", type="movie", thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(item.clone(title="Series", action="sub_menu", url= host + "/secure/titles?type=", type="series", thumbnail=get_thumb("tvshows", auto=True)))
    itemlist.append(item.clone(title="Buscar...", action="search", thumbnail=get_thumb("search", auto=True)))
    
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def sub_menu(item):
    logger.info()
    itemlist = []
    disponible = "onlyStreamable=true&perPage=16&page=1"
    if item.genero:
        genero = item.genero
        disponible = "%s&%s" %(genero,disponible)
    itemlist.append(item.clone(title="Estreno" , action="lista", url= item.url + "%s&order=release_date:desc&%s" % (item.type,disponible), thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(item.clone(title="Popular" , action="lista", url= item.url + "%s&%s" % (item.type,disponible), thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(item.clone(title="Ultimas agregadas" , action="lista", url= item.url + "%s&order=created_at:desc&%s" % (item.type,disponible), thumbnail=get_thumb("movies", auto=True)))
    if not item.genero:
        itemlist.append(item.clone(title="Genero" , action="categorias", url= item.url + "%s&%s" % (item.type,disponible), thumbnail=get_thumb('genres', auto=True)))

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Accion", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=accion", section=item.section) )
    itemlist.append(item.clone(title="Aventura", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=aventura", section=item.section) )
    itemlist.append(item.clone(title="Comedia", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=comedia", section=item.section) )
    itemlist.append(item.clone(title="Terror", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=terror", section=item.section) )
    itemlist.append(item.clone(title="Suspense", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=suspenso", section=item.section) )
    itemlist.append(item.clone(title="Documental", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=documental", section=item.section) )
    itemlist.append(item.clone(title="Misterio", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=misterio", section=item.section) )
    itemlist.append(item.clone(title="Fantasia", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=fantasia", section=item.section) )
    itemlist.append(item.clone(title="Animacion", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=animacion", section=item.section) )
    itemlist.append(item.clone(title="Horror", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=horror", section=item.section) )
    itemlist.append(item.clone(title="Musical", action="sub_menu", url= host + "/secure/titles?type=%s" %item.type, genero="genre=musica", section=item.section) )
    
    
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "%20")
        item.url = "%s/secure/search/%s?limit=" % (host, texto)
        if texto != "":
            return lista(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    if "/search/" in item.url:
        matches= data["results"]
    else:
        matches= data["pagination"]["data"]
    for elem in matches:
        id = elem["id"]
        thumbnail = elem['poster']
        title = elem['name']
        if "title" in elem["type"]:
            tv_show = elem['is_series']
            year = elem['year']
        contentTitle = title
        if not year:
            year = '-'
        if not thumbnail.startswith("https"):
            thumbnail = "%s/%s" % (host,thumbnail)
        if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
            if tv_show:
                title = "[COLOR darkorange]%s[/COLOR]" % title
            if year != "-":
                title = "%s [COLOR cyan](%s)[/COLOR]" % (title,year)
        else:
            title = title
        new_item = Item(channel=item.channel, title=title, thumbnail=thumbnail, infoLabels={"year": year})
        if tv_show:
            new_item.url = "%s/secure/titles/%s?titleId=%s&seasonNumber=" %(host,id,id)
            new_item.action = "seasons"
            new_item.contentSerieName = contentTitle
        else:
            new_item.url = "%s/secure/titles/%s?titleId=%s" %(host,id,id)
            new_item.action = "findvideos"
            new_item.contentTitle = contentTitle
        if "title" in elem["type"]:
            itemlist.append(new_item)
    tmdb.set_infoLabels(itemlist, True)
    if not "/search/" in item.url:
        next_page = data["pagination"]["next_page_url"]
        pag = scrapertools.find_single_match(item.url, "(.*?)&page=")
        if next_page:
            next_page = next_page.replace("/?", "&")
            next_page = "%s%s" % (pag, next_page)
            next_page = urlparse.urljoin(item.url,next_page)
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    data = httptools.downloadpage(item.url).json
    for elem in data["title"]["seasons"]:
        season = elem["number"]
        cap_num = elem["episode_count"]
        if season < 10:
            season = "0%s" %season
        title = "Temporada %s" % season
        infoLabels["season"] = season
        url= "%s%s" %(item.url,season)
        itemlist.append(item.clone(title=title, url=url, action="episodesxseasons", cap_num=cap_num, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    infoLabels = item.infoLabels
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    a = 1
    while a <= item.cap_num:
        cap = a
        if int(cap) < 10:
            cap = "0%s" % cap
        title = "%sx%s" % (season, cap)
        infoLabels["episode"] = cap
        url= "%s&episodeNumber=%s" %(item.url,cap)
        a += 1
        itemlist.append(item.clone(title=title, url=url, action="findvideos",
                                 infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
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
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    for elem in data["title"]["videos"]:
        url = elem['url']
        lang = elem['language']
        cat = elem["category"]
        lang = IDIOMAS.get(lang, lang)
        server = scrapertools.find_single_match(url, "https://(.*?)/")
        server = SERVER.get(server,server)
        if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
            if "trailer" in cat:
                title= "[COLOR darkgreen]Trailer[/COLOR] [COLOR darkgrey][%s][/COLOR]" %lang
            else:
                title = "%s [COLOR darkgrey][%s][/COLOR]" %(server,lang)
        else:
            if "trailer" in cat:
                server = ""
                title = "Trailer"
            else:
                title = ""
        itemlist.append(item.clone(action="play", title=title, url=url, server=server, language=lang))
    itemlist.sort(key=lambda it: (it.language))
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(item.clone(action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    logger.debug("ITEM: %s" % item)
    itemlist = servertools.get_servers_itemlist([item.clone(url=item.url, server="")])
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist
