# -*- coding: utf-8 -*-

import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from core import tmdb
from core.item import Item
from platformcode import logger, config
from channels import autoplay
from channels import filtertools

tgenero = {"Comedia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
           "Drama": "https://s16.postimg.cc/94sia332d/drama.png",
           "Acción": "https://s3.postimg.cc/y6o9puflv/accion.png",
           "Aventura": "https://s10.postimg.cc/6su40czih/aventura.png",
           "Romance": "https://s15.postimg.cc/fb5j8cl63/romance.png",
           "Ciencia ficción": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
           "Terror": "https://s7.postimg.cc/yi0gij3gb/terror.png",
           "Fantasía": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
           "Misterio": "https://s1.postimg.cc/w7fdgf2vj/misterio.png",
           "Crimen": "https://s4.postimg.cc/6z27zhirx/crimen.png",
           "Hentai": "https://s29.postimg.cc/aamrngu2f/hentai.png",
           "Magia": "https://s9.postimg.cc/nhkfzqffj/magia.png",
           "Psicológico": "https://s13.postimg.cc/m9ghzr86f/psicologico.png",
           "Sobrenatural": "https://s9.postimg.cc/6hxbvd4ov/sobrenatural.png",
           "Torneo": "https://s2.postimg.cc/ajoxkk9ih/torneo.png",
           "Thriller": "https://s22.postimg.cc/5y9g0jsu9/thriller.png",
           "Otros": "https://s30.postimg.cc/uj5tslenl/otros.png"}

host = "http://www.animeshd.tv"

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'poseidonhd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'poseidonhd')


IDIOMAS = {'Castellano':'CAST','Latino': 'LAT', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'openload', 'gvideo', 'streamango']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []


    itemlist.append(item.clone(title="Castellano",
                               action="lista",
                               thumbnail=get_thumb('channels_spanish.png'),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + '/castellano'))

    itemlist.append(item.clone(title="Latino",
                               action="lista",
                               thumbnail=get_thumb('channels_latino.png'),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + '/latino'))

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail=get_thumb('all', auto=True),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + '/buscar?t=todo&q='))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               url=host,
                               thumbnail=get_thumb('genres', auto=True),
                               fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png'))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '/buscar?t=todo&q=',
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'
                               ))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)


    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def lista(item):
    logger.info()

    itemlist = []

    post = ''
    if item.extra in ['episodios']:
        post = {'tipo': 'episodios', '_token': 'rAqVX74O9HVHFFigST3M9lMa5VL7seIO7fT8PBkl'}
        post = urllib.urlencode(post)
    data = get_source(item.url)
    patron = 'class="anime"><a href="([^"]+)">'
    patron +='<div class="cover" style="background-image: url\((.*?)\)">.*?<h2>([^<]+)<\/h2>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = scrapedurl
        thumbnail = host + scrapedthumbnail
        title = scrapedtitle
        itemlist.append(item.clone(action='episodios',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentSerieName=title,
                                   context=filtertools.context(item, list_language, list_quality)
                                   ))

        # Paginacion
    next_page = scrapertools.find_single_match(data,
                                               '<a href="([^"]+)" data-ci-pagination-page="\d+" rel="next"')
    next_page_url = scrapertools.decodeHtmlentities(next_page)
    if next_page_url != "":
        itemlist.append(Item(channel=item.channel,
                             action="lista",
                             title=">> Página siguiente",
                             url=next_page_url,
                             thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                             ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def generos(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<a href="https:\/\/www\.animeshd\.tv\/genero\/([^"]+)">([^<]+)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        if title == 'Recuentos de la vida':
            title = 'Otros'
        genero = scrapertools.decodeHtmlentities(scrapedurl)
        thumbnail = ''
        if title in tgenero:
            thumbnail = tgenero[title]

        url = 'http://www.animeshd.tv/genero/%s' % genero
        itemlist.append(item.clone(action='lista', title=title, url=url, thumbnail=thumbnail))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<li id="epi-.*? class="list-group-item.*?"><a href="([^"]+)".*?'
    patron += 'class="badge".*?width="25" title="([^"]+)">.*?<\/span>(.*?) (\d+)<\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, scrapedlang, scrapedtitle, episode in matches:
        language = scrapedlang
        title = scrapedtitle + " " + "1x" + episode
        url = scrapedurl
        infoLabels['season'] ='1'
        infoLabels['episode'] = episode

        itemlist.append(Item(channel=item.channel, title=title, contentSerieName=item.contentSerieName, url=url,
                             action='findvideos', language=IDIOMAS[language], infoLabels=infoLabels))
           
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra1='library'))
    
    return itemlist

def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = "<option value=(.*?) data-content=.*?width='16'> (.*?) <span class='text-muted'>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, language in matches:
        if 'jpg' in scrapedurl:
            vip_data = httptools.downloadpage(scrapedurl, follow_redirects=False)
            scrapedurl = vip_data.headers['location']
        title = '%s [%s]'
        itemlist.append(item.clone(title=title, url=scrapedurl.strip(), action='play',
                        language=IDIOMAS[language]))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
