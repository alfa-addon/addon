# -*- coding: utf-8 -*-

import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb


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

audio = {'Latino': '[COLOR limegreen]LATINO[/COLOR]', 'Español': '[COLOR yellow]ESPAÑOL[/COLOR]',
         'Sub Español': '[COLOR red]SUB ESPAÑOL[/COLOR]'}

host = 'http://pelisgratis.tv/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="lista",
                               thumbnail=get_thumb('premieres', auto=True),
                               url=host + 'estrenos'
                               ))

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail=get_thumb('all', auto=True),
                               url=host
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               thumbnail=get_thumb('genres', auto=True),
                               extra='generos'
                               ))

    itemlist.append(item.clone(title="Alfabetico",
                               action="seccion",
                               url=host,
                               thumbnail=get_thumb('alphabet', auto=True),
                               extra='a-z'
                               ))

    itemlist.append(item.clone(title="Mas Vistas",
                               action="lista",
                               thumbnail=get_thumb('more watched', auto=True),
                               url=host + 'peliculas-mas-vistas'
                               ))

    itemlist.append(item.clone(title="Mas Votadas",
                               action="lista",
                               thumbnail=get_thumb('more voted', auto=True),
                               url=host + 'peliculas-mas-votadas'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '?s=',
                               thumbnail=get_thumb('search', auto=True)
                               ))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url, add_referer=True).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def lista(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = 'class=(?:MvTbImg|TPostMv).*?href=(.*?)\/(?:>| class).*?src=(.*?) '
    patron += 'class=Title>(.*?)<.*?(?:<td|class=Year)>(.*?)<.*?(?:<td|class=Description)>(.*?)<(?:\/td|\/p)>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedplot in matches:
        url = scrapedurl
        thumbnail = scrapedthumbnail
        plot = scrapedplot
        quality = ''
        contentTitle = scrapedtitle
        title = contentTitle
        year = scrapedyear

        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   plot=plot,
                                   contentTitle=contentTitle,
                                   quality=quality,
                                   infoLabels={'year': year}
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<a class=nextpostslink rel=next href=(.*?)>')
        if next_page != '':
            itemlist.append(item.clone(action="lista",
                                       title='Siguiente >>>',
                                       url=next_page,
                                       thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'
                                       ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.extra == 'generos':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?)>(.*?)</a><\/li>'
    elif item.extra == 'a-z':
        patron = '<li><a href=(.*?)>(\w|#)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        thumbnail = ''
        if item.extra == 'generos':
            #cantidad = re.findall(r'.*?<\/a> \((\d+)\)', scrapedtitle)
            title = scrapedtitle
        else:
            title = scrapedtitle
            if title.lower() in thumbletras:
                thumbnail = thumbletras[title.lower()]

        itemlist.append(item.clone(action='lista', title=title, url=url, thumbnail=thumbnail))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return lista(item)


def findvideos(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<div class=TPlayerTb.Current id=(.*?)>.*?src=(.*?) frameborder'
    matches = re.compile(patron, re.DOTALL).findall(data)
    base_link = 'https://repros.live/player/ajaxdata'
    for opt, urls_page in matches:
        language = scrapertools.find_single_match (data,'TPlayerNv>.*?tplayernv=%s><span>Opción.*?<span>(.*?)</span>' % opt)
        headers = {'referer':item.url}
        if 'trembed' in urls_page:
            urls_page = scrapertools.decodeHtmlentities(urls_page)
            sub_data=httptools.downloadpage(urls_page).data
            urls_page = scrapertools.find_single_match(sub_data, 'src="(.*?)" ')
        video_data = httptools.downloadpage(urls_page, headers=headers).data
        servers = scrapertools.find_multiple_matches(video_data,'data-player="(.*?)" data-embed="(.*?)">')
        for server, code in servers:
            post = {'codigo':code}
            post = urllib.urlencode(post)
            video_json=jsontools.load(httptools.downloadpage('https://repros.live/player/ajaxdata', post=post).data)
            url = video_json['url']
            itemlist.append(item.clone(title='[%s][%s]',
                                       url=url,
                                       action='play',
                                       language=language,
                                       ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # categoria='peliculas'
    try:
        if categoria == 'peliculas':
            item.url = host + 'estrenos'
        elif categoria == 'infantiles':
            item.url = host + 'animacion'
        elif categoria == 'terror':
            item.url = host + 'terror'
        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
