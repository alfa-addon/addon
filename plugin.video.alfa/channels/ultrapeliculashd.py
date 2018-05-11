# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.ultrapeliculashd.com'

tgenero = {"ACCIÓN": "https://s3.postimg.cc/y6o9puflv/accion.png,",
           "ANIMACIÓN": "https://s13.postimg.cc/5on877l87/animacion.png",
           "AVENTURA": "https://s10.postimg.cc/6su40czih/aventura.png",
           "CIENCIA FICCIÓN": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
           "COMEDIA": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
           "CRIMEN": "https://s4.postimg.cc/6z27zhirx/crimen.png",
           "DRAMA": "https://s16.postimg.cc/94sia332d/drama.png",
           "ESTRENOS": "https://s21.postimg.cc/fy69wzm93/estrenos.png",
           "FAMILIA": "https://s7.postimg.cc/6s7vdhqrf/familiar.png",
           "FANTASÍA": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
           "GUERRA": "https://s4.postimg.cc/n1h2jp2jh/guerra.png",
           "INFANTIL": "https://s23.postimg.cc/g5rmazozv/infantil.png",
           "MISTERIO": "https://s1.postimg.cc/w7fdgf2vj/misterio.png",
           "ROMANCE": "https://s15.postimg.cc/fb5j8cl63/romance.png",
           "SUSPENSO": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
           "TERROR": "https://s7.postimg.cc/yi0gij3gb/terror.png"
           }

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

tcalidad = {'1080P': 'https://s21.postimg.cc/4h1s0t1wn/hd1080.png',
            '720P': 'https://s12.postimg.cc/lthu7v4q5/hd720.png', "HD": "https://s27.postimg.cc/m2dhhkrur/image.png"}


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + '/movies/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               url=host,
                               thumbnail='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                               fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png'
                               ))

    itemlist.append(item.clone(title="Alfabetico",
                               action="seccion",
                               url=host,
                               thumbnail='https://s17.postimg.cc/fwi1y99en/a-z.png',
                               fanart='https://s17.postimg.cc/fwi1y99en/a-z.png',
                               extra='alfabetico'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '/?s=',
                               thumbnail='https://s30.postimg.cc/pei7txpa9/buscar.png',
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'
                               ))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if item.extra != 'buscar':
        patron = '<article id=.*?<img src=(.*?) alt=(.*?)>.*?<a href=(.*?)>.*?</h3><span>(.*?)<'
    else:
        patron = '<article><div class=image>.*?<a href=(.*?)\/><img src=(.*?) alt=(.*?) \/>.*?year>(.*?)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, scrapedyear in matches:
        if item.extra == 'buscar':
            aux = scrapedthumbnail
            scrapedthumbnail=scrapedtitle
            scrapedtitle = scrapedurl
            scrapedurl =  aux


        url = scrapedurl
        thumbnail = scrapedthumbnail
        contentTitle = re.sub(r'\d{4}', '', scrapedtitle)
        contentTitle = contentTitle.replace('|', '')
        contentTitle = contentTitle.strip(' ')
        title = scrapertools.decodeHtmlentities(contentTitle)
        year = scrapedyear
        fanart = ''


        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=item.title, url=url,
                             thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle, infoLabels={'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<link rel=next href=(.*?) />')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="lista", title='Siguiente >>>', url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    logger.debug(data)
    patron = 'genres menu-item-.*?><a href=(.*?)>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        thumbnail = ''
        fanart = ''
        if scrapedtitle in tgenero:
            thumbnail = tgenero[scrapedtitle]
        title = scrapedtitle
        url = scrapedurl
        if scrapedtitle not in ['PRÓXIMAMENTE', 'EN CINE']:
            itemlist.append(item.clone(action="lista",
                                       title=title,
                                       fulltitle=item.title,
                                       url=url,
                                       thumbnail=thumbnail,
                                       fanart=fanart
                                       ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'glossary=(.*?)>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedid, scrapedtitle in matches:
        thumbnail = ''
        if scrapedtitle.lower() in thumbletras:
            thumbnail = thumbletras[scrapedtitle.lower()]
        fanart = ''
        title = scrapedtitle
        id = scrapedid

        itemlist.append(
            Item(channel=item.channel, action="alpha", title=title, fulltitle=item.title, thumbnail=thumbnail,
                 fanart=fanart, id = id))
    return itemlist

def alpha(item):
    logger.info()

    itemlist = []

    url = 'https://www.ultrapeliculashd.com/wp-json/dooplay/glossary/?term=%s&nonce=4e850b7d59&type=all' % item.id
    data = httptools.downloadpage(url).data
    dict_data = jsontools.load(data)
    logger.debug(dict_data)

    for elem in dict_data:
        logger.debug(dict_data[elem])
        elem = dict_data[elem]
        itemlist.append(Item(channel=item.channel, action='findvideos', title = elem['title'], url=elem['url'],
                             thumbnail=elem['img']))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    #logger.debug(data)
    patron = '<iframe.*?rptss src=(.*?) (?:width.*?|frameborder.*?) allowfullscreen><\/iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for video_url in matches:
        logger.debug('video_url: %s' % video_url)
        if 'stream' in video_url and 'streamango' not in video_url:
            data = httptools.downloadpage('https:'+video_url).data
            logger.debug(data)
            if not 'iframe' in video_url:
                new_url=scrapertools.find_single_match(data, 'iframe src="(.*?)"')
                new_data = httptools.downloadpage(new_url).data
            logger.debug('new_data %s' % new_data)
            url= ''
            try:
                url, quality = scrapertools.find_single_match(new_data, 'file:.*?(?:\"|\')(https.*?)(?:\"|\'),'
                                                                        'label:.*?(?:\"|\')(.*?)(?:\"|\'),')
            except:
                pass
            if url != '':
                headers_string = '|Referer=%s' % url
                url = url.replace('download', 'preview')+headers_string

                sub = scrapertools.find_single_match(new_data, 'file:.*?"(.*?srt)"')
                new_item = (Item(title=item.title, url=url, quality=quality, subtitle=sub, server='directo'))
                itemlist.append(new_item)
        else:
            itemlist.extend(servertools.find_video_items(data=video_url))

    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.action = 'play'
        videoitem.thumbnail = item.thumbnail
        videoitem.infoLabels = item.infoLabels
        videoitem.title = item.contentTitle + ' (' + videoitem.server + ')'
        if 'youtube' in videoitem.url:
            videoitem.title = '[COLOR orange]Trailer en Youtube[/COLOR]'

    itemlist = servertools.get_servers_itemlist(itemlist)

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
            item.extra = 'buscar'
            return lista(item)
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
