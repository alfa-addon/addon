# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools, autoplay
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www.ultrapeliculashd.com'

thumbletras = {'#': 'https://s32.postimg.cc/drojt686d/image.png',
               'a': 'https://s32.postimg.cc/llp5ekfz9/image.png',
               'b': 'https://s32.postimg.cc/y1qgm1yp1/image.png',
               'c': 'https://s32.postimg.cc/vlon87gmd/image.png',
               'd': 'https://s32.postimg.cc/3zlvnix9h/image.png',
               'e': 'https://s32.postimg.cc/bgv32qmsl/image.png',
               'f': 'https://s32.postimg.cc/y6u7vq605/image.png',
               'g': 'https://s32.postimg.cc/9237ib6jp/image.png',
               'h': 'https://s32.postimg.cc/812yt6pk5/image.png',
               'i': 'https://s32.postimg.cc/6nbbxvqat/image.png',
               'j': 'https://s32.postimg.cc/axpztgvdx/image.png',
               'k': 'https://s32.postimg.cc/976yrzdut/image.png',
               'l': 'https://s32.postimg.cc/fmal2e9yd/image.png',
               'm': 'https://s32.postimg.cc/m19lz2go5/image.png',
               'n': 'https://s32.postimg.cc/b2ycgvs2t/image.png',
               'o': 'https://s32.postimg.cc/c6igsucpx/image.png',
               'p': 'https://s32.postimg.cc/jnro82291/image.png',
               'q': 'https://s32.postimg.cc/ve5lpfv1h/image.png',
               'r': 'https://s32.postimg.cc/nmovqvqw5/image.png',
               's': 'https://s32.postimg.cc/zd2t89jol/image.png',
               't': 'https://s32.postimg.cc/wk9lo8jc5/image.png',
               'u': 'https://s32.postimg.cc/w8s5bh2w5/image.png',
               'v': 'https://s32.postimg.cc/e7dlrey91/image.png',
               'w': 'https://s32.postimg.cc/fnp49k15x/image.png',
               'x': 'https://s32.postimg.cc/dkep1w1d1/image.png',
               'y': 'https://s32.postimg.cc/um7j3zg85/image.png',
               'z': 'https://s32.postimg.cc/jb4vfm9d1/image.png'
               }

IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'SUB':'VOSE'}
list_language = IDIOMAS.values()
list_quality = ['default', '1080p', 'HD', 'CAM']
list_servers = ['fembed', 'uqload']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Estrenos",
                         action="lista",
                         thumbnail=get_thumb('premieres', auto=True),
                         url=host + '/genre/estreno/'
                         ))

    itemlist.append(Item(channel=item.channel, title="Actualizadas",
                         action="lista",
                         thumbnail=get_thumb('updated', auto=True),
                         url=host + '/movies/'
                         ))

    itemlist.append(Item(channel=item.channel, title="Destacadas",
                         action="lista",
                         thumbnail=get_thumb('hot', auto=True),
                         url=host + '/genre/destacados/'
                         ))

    itemlist.append(Item(channel=item.channel, title="Generos",
                         action="generos",
                         url=host,
                         thumbnail=get_thumb('genres', auto=True)
                         ))

    itemlist.append(Item(channel=item.channel, title="Alfabetico",
                         action="seccion",
                         url=host,
                         thumbnail=get_thumb('alphabet', auto=True),
                         extra='alfabetico'
                         ))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host + '/?s=',
                         thumbnail=get_thumb('search', auto=True)
                         ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    patron = '<article id=.*?<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += r'quality">([^<]+).*?<a href="([^"]+)">.*?<span>(\d{4})'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, quality, url, year in matches:
        
        thumbnail = re.sub(r'p/w\d+', 'p/original', scrapedthumbnail)
        contentTitle = re.sub(r'\(\d{4}\)| / .*| 4K', '', scrapedtitle).strip()
        title = contentTitle
        
        if not config.get_setting("unify"):
            title += ' [COLOR blue](%s)[/COLOR] [COLOR khaki][%s][/COLOR]' % (year, quality)

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title,
                             contentTitle=contentTitle, url=url, quality=quality,
                             thumbnail=thumbnail, infoLabels={'year': year}))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if next_page and itemlist:
        itemlist.append(Item(channel=item.channel, action="lista",
                             title='Siguiente >>>', url=next_page))
    return itemlist

def search_results(item):
    logger.info()
    
    itemlist = []
    data = get_source(item.url)

    patron = '<article><div class="image">.*?<a href="([^"]+)"><img src="([^"]+)" '
    patron += 'alt="([^"]+)" /><span class="movies">.*?year">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, scrapedthumbnail, scrapedtitle, year in matches:

        thumbnail = re.sub(r'p/w\d+', 'p/original', scrapedthumbnail)
        contentTitle = re.sub(r'\d{4}$| / .*| 4K|\(\)', '', scrapedtitle).strip()
        title = contentTitle

        if not config.get_setting("unify"):
            title += ' [COLOR blue](%s)[/COLOR]' % (year)


        itemlist.append(Item(channel=item.channel, action="findvideos", title=title,
                             contentTitle=contentTitle, url=url,
                             thumbnail=thumbnail, infoLabels={'year': year}))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion
    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if next_page and itemlist:
        itemlist.append(Item(channel=item.channel, action="search_results",
                             title='Siguiente >>>', url=next_page))
    return itemlist




def generos(item):
    logger.info()
    itemlist = []
    not_allowed = ['PRÓXIMAMENTE', 'ESTRENOS HD', '4K ULTRA HD']
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'genres menu-item-.*?><a href=(.*?)>(.*?)<'
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        title = scrapedtitle
        url = scrapedurl
        if scrapedtitle not in not_allowed:
            not_allowed.append(scrapedtitle)
            itemlist.append(Item(channel=item.channel, action="lista",
                                 title=title, url=url
                                 ))
    itemlist.sort(key=lambda it:it.title)
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'glossary=(.*?)>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedid, scrapedtitle in matches:
        if scrapedtitle.lower() in thumbletras:
            thumbnail = thumbletras[scrapedtitle.lower()]
        title = scrapedtitle
        id = scrapedid

        itemlist.append(
            Item(channel=item.channel, action="alpha",
                 title=title, id = id))
    return itemlist

def alpha(item):
    logger.info()

    itemlist = []

    url = '%s/wp-json/dooplay/glossary/?term=%s&nonce=4e850b7d59&type=all' % (host, item.id)
    dict_data = httptools.downloadpage(url).json
    if 'error' not in dict_data:
        for elem in dict_data:
            elem = dict_data[elem]
            thumb = re.sub(r'-\d+x\d+.jpg', '.jpg', elem['img'])
            itemlist.append(Item(channel=item.channel, action='findvideos', title = elem['title'],
                                 url=elem['url'], thumbnail=thumb))
    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def findvideos(item):
    from lib import jsunpack
    logger.info()
    itemlist = []
    title = ''
    
    full_data = get_source(item.url)
    quality = item.quality or scrapertools.find_single_match(full_data, 'qualityx">([^<]+)')

    patron = '<div id="([^"]+)" class="play-box-iframe.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(full_data)
    for option, video_url in matches:
        language = scrapertools.find_single_match(full_data, '"#%s">.*?-->(.*?)(?:\s|<)' % option)
        if 'sub' in language.lower():
            language = 'SUB'
        language = IDIOMAS[language]

        if 'hideload' in video_url:
            srv, new_id = scrapertools.find_single_match(video_url, r"\?(\w)d=(\w+)")
            new_url = 'https://www.ultrapeliculashd.com/hideload/?%sr=%s' % (srv, new_id[::-1])
            try:
                video_url = httptools.downloadpage(new_url, headers={'Referer': video_url}, timeout=2).url
            except:
                continue
        
        elif 'drive/player' in video_url:
            continue
        
        if not config.get_setting("unify"):
            title = ' [%s] [%s]' % (quality, language)

        new_item = (Item(channel=item.channel, title='%s'+title, url=video_url, action='play', quality=quality,
                         language=language,  infoLabels=item.infoLabels))
        itemlist.append(new_item)


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title %  i.server.capitalize())


    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return search_results(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.extra = 'estrenos/'
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + '/genre/estrenos/'

        elif categoria == 'infantiles':
            item.url = host + '/genre/animacion/'

        elif categoria == 'terror':
            item.url = host + '/genre/terror/'

        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
