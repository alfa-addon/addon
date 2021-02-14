# -*- coding: utf-8 -*-
# -*- Channel Mundo Donghua -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys, re
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools, autoplay
from channels import renumbertools
from core import tmdb


IDIOMAS = {'vose': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['directo', 'dailymotion']

host = "https://www.mundodonghua.com/"

def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", url=host+ 'lista-episodios', 
                        action="list_all", thumbnail=get_thumb('new episodes', auto=True), neweps=True))

    itemlist.append(Item(channel=item.channel, title="Emision", url=host + 'lista-donghuas-emision',
                         action="list_all", thumbnail=get_thumb('on air', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Finalizadas", url=host+ 'lista-donghuas-finalizados',
                         action="list_all", thumbnail=get_thumb('anime', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Todas", url=host+'lista-donghuas',
                        action="list_all", thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", url=host, action="genres",
                        thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", url=host + 'busquedas/', action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    data = httptools.downloadpage(url, headers={'Referer':referer}).data
    
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup

def genres(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    for elem in soup.find_all("div", class_="col-xs-6 p-0"):
        url = host+elem.a["href"]
        title = elem.a.text.strip()
        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action='list_all'))

    return itemlist

def list_all(item):
    logger.info()

    itemlist = list()
    
    action = "episodios"
    if item.neweps:
        action = "findvideos"

    soup = create_soup(item.url)


    for elem in soup.find_all("div", class_=re.compile("item col-lg-\d col-md-\d col-xs")):
        
        url = host+elem.a["href"]
        title = elem.h5.text.strip()
        thumb = host+elem.img["src"]
        typo = elem.a.find('div', class_="img fit-1").text.strip()
        
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        
        if typo.lower() == 'película':
            url = url.replace('/donghua/', 'ver/') + '/1'
            itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                             thumbnail=thumb, contentTitle=title, plot=typo, typo=typo))
        else:
            itemlist.append(Item(channel=item.channel, title=title, url=url, action=action,
                             thumbnail=thumb, contentSerieName=title, context=context, plot=typo))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    try:
        url_next_page = soup.find("ul", class_="pagination").find_all("a")[-1]
        if url_next_page.text:
            url_next_page = ''
        else:
            url_next_page = url_next_page["href"]
    except:
        return itemlist

    url_next_page = host + url_next_page

    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>",
                             url=url_next_page, action='list_all'))
    return itemlist

def episodios(item):
    logger.info()

    itemlist = list()
    first_url = ""

    infoLabels = item.infoLabels

    soup = create_soup(item.url)
    ep_list = soup.find("ul", class_="donghua-list")
    try:
        plot = soup.find("p", class_="text-justify fc-dark").text
    except:
        plot = ""
    # try:
    #     state = soup.find("span", class_="badge bg-success")
    # except:
    #     state = ''


    for elem in ep_list.find_all("a"):
        
        url = host+elem["href"]

        # if not first_url and state:
        #     first_url = url
        epi_num = scrapertools.find_single_match(elem.text.strip(), "(\d+)$")
        season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, int(epi_num))
        infoLabels['season'] =  season
        infoLabels['episode'] = episode
        title = '%sx%s - Episodio %s' % (season, episode, episode)
        itemlist.append(Item(channel=item.channel, title=title, url=url,
                            plot=plot, thumbnail=item.thumbnail,
                            action='findvideos', infoLabels=infoLabels))

    itemlist = itemlist[::-1]
    
    # if first_url and state:
    #     epi_num = int(scrapertools.find_single_match(first_url, "(\d+)$"))+1
    #     url = re.sub("(\d+)$", str(epi_num), first_url)
    #     season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, int(epi_num))
    #     infoLabels['season'] =  season
    #     infoLabels['episode'] = episode
    #     title = '%sx%s - Episodio %s' % (season, episode, episode)
    #     itemlist.append(Item(channel=item.channel, title=title, url=url, 
    #                         action='findvideos', infoLabels=infoLabels))


    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))

    return itemlist

def findvideos(item):
    logger.info()
    from lib import jsunpack
    import base64

    itemlist = list()

    data = httptools.downloadpage(item.url).data
    #logger.error(data)
    matches = scrapertools.find_multiple_matches(data, "(eval.*?)\n")
    if len(matches) > 1:
        for pack in matches:
            unpack = jsunpack.unpack(pack)
            #logger.error(unpack)
            url = scrapertools.find_single_match(unpack, 'file(?:"|):"([^"]+)')
            if not url.startswith('http'):
                url = 'http:'+url

            itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                             infoLabels=item.infoLabels))

    else:
        unpack = jsunpack.unpack(matches[0])
        #logger.error(unpack)
        slugs = scrapertools.find_multiple_matches(unpack, '"slug":"([^"]+)')
        if slugs:
            for slug in slugs:
                url = '%sapi_donghua.php?slug=%s' %(host, slug)
                data = httptools.downloadpage(url, headers={'Referer': item.url}).json[0]
                #logger.error(data)
                if data.get('url',''):
                    url = 'https://www.dailymotion.com/video/'+base64.b64decode(data['url'])
                elif data.get('source', ''):
                    url = data['source'][0].get('file','')
                    if not url.startswith('http'):
                        url = 'http:'+url

                itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                                 infoLabels=item.infoLabels))
        else:
            url = scrapertools.find_single_match(unpack, 'file(?:"|):"([^"]+)')
            if not url.startswith('http'):
                url = 'http:'+url

            itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url, language=IDIOMAS['vose'],
                                 infoLabels=item.infoLabels))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and itemlist > 0 and item.typo:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return list_all(item)
    else:
        return []
