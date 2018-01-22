# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config, logger

tgenero = {"Comedia": "https://s7.postimg.org/ne9g9zgwb/comedia.png",
           "Suspense": "https://s13.postimg.org/wmw6vl1cn/suspenso.png",
           "Drama": "https://s16.postimg.org/94sia332d/drama.png",
           "Acción": "https://s3.postimg.org/y6o9puflv/accion.png",
           "Aventura": "https://s10.postimg.org/6su40czih/aventura.png",
           "Romance": "https://s15.postimg.org/fb5j8cl63/romance.png",
           "Animación": "https://s13.postimg.org/5on877l87/animacion.png",
           "Ciencia ficción": "https://s9.postimg.org/diu70s7j3/cienciaficcion.png",
           "Terror": "https://s7.postimg.org/yi0gij3gb/terror.png",
           "Documental": "https://s16.postimg.org/7xjj4bmol/documental.png",
           "Música": "https://s29.postimg.org/bbxmdh9c7/musical.png",
           "Fantasía": "https://s13.postimg.org/65ylohgvb/fantasia.png",
           "Misterio": "https://s1.postimg.org/w7fdgf2vj/misterio.png",
           "Crimen": "https://s4.postimg.org/6z27zhirx/crimen.png",
           "Familia": "https://s7.postimg.org/6s7vdhqrf/familiar.png",
           "Guerra": "https://s4.postimg.org/n1h2jp2jh/guerra.png",
           "Western": "https://s23.postimg.org/lzyfbjzhn/western.png",
           "Historia": "https://s15.postimg.org/fmc050h1n/historia.png"
           }

thumbletras = {'#': 'https://s32.postimg.org/drojt686d/image.png',
               'a': 'https://s32.postimg.org/llp5ekfz9/image.png',
               'b': 'https://s32.postimg.org/y1qgm1yp1/image.png',
               'c': 'https://s32.postimg.org/vlon87gmd/image.png',
               'd': 'https://s32.postimg.org/3zlvnix9h/image.png',
               'e': 'https://s32.postimg.org/bgv32qmsl/image.png',
               'f': 'https://s32.postimg.org/y6u7vq605/image.png',
               'g': 'https://s32.postimg.org/9237ib6jp/image.png',
               'h': 'https://s32.postimg.org/812yt6pk5/image.png',
               'i': 'https://s32.postimg.org/6nbbxvqat/image.png',
               'j': 'https://s32.postimg.org/axpztgvdx/image.png',
               'k': 'https://s32.postimg.org/976yrzdut/image.png',
               'l': 'https://s32.postimg.org/fmal2e9yd/image.png',
               'm': 'https://s32.postimg.org/m19lz2go5/image.png',
               'n': 'https://s32.postimg.org/b2ycgvs2t/image.png',
               'o': 'https://s32.postimg.org/c6igsucpx/image.png',
               'p': 'https://s32.postimg.org/jnro82291/image.png',
               'q': 'https://s32.postimg.org/ve5lpfv1h/image.png',
               'r': 'https://s32.postimg.org/nmovqvqw5/image.png',
               's': 'https://s32.postimg.org/zd2t89jol/image.png',
               't': 'https://s32.postimg.org/wk9lo8jc5/image.png',
               'u': 'https://s32.postimg.org/w8s5bh2w5/image.png',
               'v': 'https://s32.postimg.org/e7dlrey91/image.png',
               'w': 'https://s32.postimg.org/fnp49k15x/image.png',
               'x': 'https://s32.postimg.org/dkep1w1d1/image.png',
               'y': 'https://s32.postimg.org/um7j3zg85/image.png',
               'z': 'https://s32.postimg.org/jb4vfm9d1/image.png'
               }

audio = {'Latino': '[COLOR limegreen]LATINO[/COLOR]', 'Español': '[COLOR yellow]ESPAÑOL[/COLOR]',
         'Sub Español': '[COLOR red]SUB ESPAÑOL[/COLOR]'}

host = 'http://pelisgratis.tv/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="lista",
                               thumbnail='https://s21.postimg.org/fy69wzm93/estrenos.png',
                               fanart='https://s21.postimg.org/fy69wzm93/estrenos.png',
                               url=host + 'estrenos'
                               ))

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               fanart='https://s18.postimg.org/fwvaeo6qh/todas.png',
                               url=host
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               thumbnail='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               fanart='https://s3.postimg.org/5s9jg2wtf/generos.png',
                               extra='generos'
                               ))

    itemlist.append(item.clone(title="Alfabetico",
                               action="seccion",
                               url=host,
                               thumbnail='https://s17.postimg.org/fwi1y99en/a-z.png',
                               fanart='https://s17.postimg.org/fwi1y99en/a-z.png',
                               extra='a-z'
                               ))

    itemlist.append(item.clone(title="Mas Vistas",
                               action="lista",
                               thumbnail='https://s9.postimg.org/wmhzu9d7z/vistas.png',
                               fanart='https://s9.postimg.org/wmhzu9d7z/vistas.png',
                               url=host + 'peliculas-mas-vistas'
                               ))

    itemlist.append(item.clone(title="Mas Votadas",
                               action="lista",
                               thumbnail='https://s7.postimg.org/9kg1nthzf/votadas.png',
                               fanart='https://s7.postimg.org/9kg1nthzf/votadas.png',
                               url=host + 'peliculas-mas-votadas'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '?s=',
                               thumbnail='https://s30.postimg.org/pei7txpa9/buscar.png',
                               fanart='https://s30.postimg.org/pei7txpa9/buscar.png'
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
                                       thumbnail='https://s32.postimg.org/4zppxf5j9/siguiente.png'
                                       ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.extra == 'generos':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?)>(.*?)<\/li>'
    elif item.extra == 'a-z':
        patron = '<li><a href=(.*?)>(\w|#)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        thumbnail = ''
        if item.extra == 'generos':
            title = re.sub(r'<\/a> \(\d+\)', '', scrapedtitle)
            cantidad = re.findall(r'.*?<\/a> \((\d+)\)', scrapedtitle)
            th_title = title
            title = title + ' (' + cantidad[0] + ')'
            if th_title in tgenero:
                thumbnail = tgenero[th_title]
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
    patron = '<div class=TPlayer.*?\s+id=(.*?)><iframe width=560 height=315 src=(.*?) frameborder=0'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for opt, urls_page in matches:
        logger.debug ('option: %s' % opt)
        language = scrapertools.find_single_match (data,'data-TPlayerNv=%s><span>Opción <strong>.'
                                                        '<\/strong><\/span>.*?<span>(.*?)<\/span'%opt)

        video_data = httptools.downloadpage(urls_page).data
        servers = scrapertools.find_multiple_matches(video_data,'<button id="(.*?)"')
        for server in servers:
            quality = item.quality
            info_urls = urls_page.replace('embed','get')
            video_info=httptools.downloadpage(info_urls+'/'+server).data
            video_info =  jsontools.load(video_info)
            video_id = video_info['extid']
            video_server = video_info['server']
            video_status = video_info['status']
            if video_status in ['finished', 'propio']:
                if video_status == 'finished':
                    url = 'https://'+video_server+'/embed/'+video_id
                else:
                    url = 'https://'+video_server+'/e/'+video_id
                title = item.contentTitle + ' [%s] [%s]'%(quality, language)
                itemlist.append(item.clone(title=title,
                                           url=url,
                                           action='play',
                                           language=language,
                                           quality=quality
                                           ))
    itemlist = servertools.get_servers_itemlist(itemlist)
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
