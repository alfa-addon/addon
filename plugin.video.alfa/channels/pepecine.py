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

host = "https://pepecine.tv"
perpage = 20

def mainlist1(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Películas", action='movies_menu'))
    #itemlist.append(item.clone(title="Series", action='tvshows_menu'))
    return itemlist

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel,
                         title="Ultimas",
                         url=host+'/tv-peliculas-online',
                         action='list_latest',
                         indexp=1,
                         type='movie'))
    itemlist.append(Item(channel=item.channel,
                               title="Todas",
                               url= host+'/ver-online',
                               action='list_all',
                               page='1',
                               type='movie'))
    itemlist.append(Item(channel=item.channel,
                               title="Género",
                               url= host,
                               action='genero',
                               page='1',
                               type='movie'))
    itemlist.append(Item(channel=item.channel, title = "", action =""))
    itemlist.append(Item(channel=item.channel,
                               title="Buscar",
                               url= host+'/esta-online?q=',
                               action='search',
                               page='1',
                               type='movie'))
    return itemlist


def genero(item):
    logger.info()
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    data = data.replace("\n","")
    bloque = scrapertools.find_single_match(data, 'Peliculas</h2><div id="SlideMenu1" class="s2">.*?SlideMenu1_Folder">.*?</ul></li>')
    patron  = '<a href="([^"]+).*?'
    patron += '<li>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(action = "list_all",
                             channel = item.channel,
                             page='1',
                             title = scrapedtitle,
                             type= item.type,
                             url = host + scrapedurl
                             ))
    return itemlist


def tvshows_menu(item):
    logger.info()
    itemlist=[]
    itemlist.append(Item(channel=item.channel,
                         title="Ultimas",
                         url=host+'/ver-tv-serie-online',
                         action='list_latest',
                         type='serie'))
    itemlist.append(item.clone(title="Todas",
                               url=host + '/serie-tv',
                               action='list_all',
                               page='1',
                               type='series'))
    itemlist.append(item.clone(title="Buscar",
                               url= host+'/esta-online?q=',
                               action='search',
                               page='1',
                               type='series'))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.extra = "busca"
    if texto != '':
        return sub_search(item)
    else:
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    f1 = "Peliculas"
    action = "findvideos"
    if item.type == "series":
        action = "list_all"
        f1 = "Series"
    patron = 'Ver %s .*?id="%s' %(f1, item.type)
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'col-sm-4 pretty-figure">\s*<a href="([^"]+).*?'
    patron += 'src="([^"]+).*?'
    patron += 'title="([^"]+).*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        path = scrapertools.find_single_match(scrapedthumbnail, "w\w+(/\w+.....)")
        filtro_list = {"poster_path": path}
        filtro_list = filtro_list.items()
        itemlist.append(item.clone(action = "findvideos",
                                   extra = "one",
                                   infoLabels={'filtro': filtro_list},
                                   thumbnail = scrapedthumbnail,
                                   title = scrapedtitle,
                                   fulltitle = scrapedtitle,
                                   url = scrapedurl
                                   ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_latest(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    data_url= scrapertools.find_single_match(data,'<iframe.*?src=(.*?) style')
    data = get_source(data_url)
    patron = "<div class='online'>.*?<img src=(.*?) class=.*?alt=(.*?) title=.*?"
    patron += "<b><a href=(.*?) target=.*?align=right><div class=s7>(.*?) <"
    matches = re.compile(patron,re.DOTALL).findall(data)
    count = 0
    for thumbnail, title, url, language in matches:
        count +=1
        if count >= item.indexp and count < item.indexp + perpage:
            path = scrapertools.find_single_match(thumbnail, "w\w+(/\w+.....)")
            filtro_list = {"poster_path": path}
            filtro_list = filtro_list.items()
            itemlist.append(Item(channel=item.channel,
                                 title=title,
                                 fulltitle=title,
                                 contentTitle=title,
                                 url=host+url,
                                 thumbnail=thumbnail,
                                 language=language,
                                 infoLabels={'filtro': filtro_list},
                                 extra="one",
                                 action='findvideos'))
    tmdb.set_infoLabels(itemlist)
    item.indexp += perpage
    itemlist.append(Item(channel=item.channel,
                         title="Siguiente >>",
                         url=item.url,
                         extra="one",
                         indexp=item.indexp,
                         action='list_latest'))
    return itemlist


def list_all(item):
    logger.info()
    itemlist=[]
    genero = scrapertools.find_single_match(item.url, "genre=(\w+)")
    data= get_source(item.url)
    token = scrapertools.find_single_match(data, "token:.*?'(.*?)'")
    url = host+'/titles/paginate?_token=%s&perPage=24&page=%s&order=mc_num_of_votesDesc&type=%s&minRating=&maxRating=&availToStream=1&genres[]=%s' % (token, item.page, item.type, genero)
    data = httptools.downloadpage(url).data
    dict_data = jsontools.load(data)
    items = dict_data['items']
    for dict in items:
        new_item = Item(channel=item.channel,
                       title=dict['title']+' [%s]' % dict['year'],
                       plot = dict['plot'],
                       thumbnail=dict['poster'],
                       url=dict['link'],
                       infoLabels={'year':dict['year']})
        if item.type == 'movie':
            new_item.contentTitle=dict['title']
            new_item.fulltitle=dict['title']
            new_item.action = 'findvideos'
        elif item.type == 'series':
                new_item.contentSerieName = dict['title']
                new_item.action = ''
        itemlist.append(new_item)
    tmdb.set_infoLabels(itemlist)
    itemlist.append(item.clone(title='Siguiente>>>',
                               url=item.url,
                               action='list_all',
                               type= item.type,
                               page=str(int(item.page) + 1)))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist=[]
    if item.extra == "one":
        data = httptools.downloadpage(item.url).data
        patron  = "renderTab.bind.*?'([^']+).*?"
        patron += "app.utils.getFavicon.*?<b>(.*?) .*?"
        patron += 'color:#B1FFC5;">([^<]+)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl, scrapedlanguage, scrapedquality in matches:
            title = "Ver enlace en %s " + "[" + scrapedlanguage + "]" + "[" + scrapedquality + "]"
            if scrapedlanguage != 'zc':
                itemlist.append(item.clone(action='play',
                                     title=title,
                                     url=scrapedurl,
                                     language=scrapedlanguage
                                     ))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    else:
        for link in item.url:
            language = scrapertools.find_single_match(link['label'], '(.*?) <img')
            if language != 'zc':
                itemlist.append(item.clone(action='play',
                                     title=item.title,
                                     url= link['url'],
                                     language=language,
                                     quality=link['quality']))
        itemlist=servertools.get_servers_itemlist(itemlist)
        for videoitem in itemlist:
            videoitem.title = '%s [%s]' % (videoitem.server.capitalize(), videoitem.language.capitalize())
    tmdb.set_infoLabels(itemlist)
    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la videoteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     fulltitle = item.fulltitle
                                     ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
