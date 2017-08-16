# -*- coding: utf-8 -*-
# -*- Channel TVSeriesdk -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://ver-peliculas.io/"


def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(
        Item(channel=item.channel,
             title="Peliculas",
             action="listado",
             url=host + "peliculas/",
             thumbnail=get_thumb("channels_movie.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Español",
             action="listado",
             url=host + "peliculas/en-espanol/"
             ))
    itemlist.append(
        Item(channel=item.channel,
             title="Latino",
             action="listado",
             url=host + "peliculas/en-latino/",
             thumbnail=get_thumb("channels_latino.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Subtituladas",
             action="listado",
             url=host + "peliculas/subtituladas/",
             thumbnail=get_thumb("channels_vos.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Categorias",
             action="categories",
             url=host
             ))
    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host + "core/ajax/suggest_search",
             thumbnail=get_thumb("search.png")))

    return itemlist


def categories(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    section = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')

    matches = re.compile('<li><a href="([^"]+)"[^>]+>(.*?)</a>', re.DOTALL).findall(section)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel,
                             action="listado",
                             title=title,
                             url=url
                             ))

    return itemlist


def search(item, texto):
    logger.info()

    try:
        itemlist = []
        post = "keyword=%s" % texto
        data = httptools.downloadpage(item.url, post=post).data
        data = data.replace('\\"', '"').replace('\\/', '/')
        logger.debug("data %s" % data)

        pattern = 'url\((.*?)\).+?<a href="([^"]+)".*?class="ss-title">(.*?)</a>'
        matches = re.compile(pattern, re.DOTALL).findall(data)

        for thumb, url, title in matches:
            itemlist.append(Item(channel=item.channel,
                                 action="findvideos",
                                 title=title,
                                 url=url,
                                 thumbnail=thumb
                                 ))

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def listado(item):
    logger.info()
    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    logger.debug(data)
    pattern = '<a href="([^"]+)"[^>]+><img (?:src)?(?:data-original)?="([^"]+)".*?alt="([^"]+)"'
    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url, thumb, title in matches:
        title = title.replace("Película", "", 1)
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             url=url,
                             thumbnail=thumb,
                             contentTitle=title
                             ))

    pagination = scrapertools.find_single_match(data, '<ul class="pagination">(.*?)</ul>')
    if pagination:
        next_page = scrapertools.find_single_match(pagination, '<a href="#">\d+</a>.*?<a href="([^"]+)">')
        if next_page:
            url = urlparse.urljoin(host, next_page)
            itemlist.append(Item(channel=item.channel,
                                 action="listado",
                                 title=">> Página siguiente",
                                 url=url,
                                 thumbnail=get_thumb("next.png")))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url, add_referer=True).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def findvideos(item):
    logger.info()
    duplicated = []

    data = get_source(item.url)
    video_info = scrapertools.find_single_match(data, "load_player\('(.*?)','(.*?)'\);")
    movie_info = scrapertools.find_single_match(item.url, 'http:\/\/ver-peliculas\.io\/peliculas\/(\d+)-(.*?)-\d{'
                                                          '4}-online\.')
    movie_id = movie_info[0]
    movie_name = movie_info[1]
    sub = video_info[1]
    url_base = 'http://ver-peliculas.io/core/api.php?id=%s&slug=%s' % (movie_id, movie_name)
    data = httptools.downloadpage(url_base).data
    json_data = jsontools.load(data)
    video_list = json_data['lista']
    itemlist = []
    for videoitem in video_list:
        video_base_url = 'http://ver-peliculas.io/core/videofinal.php'
        if video_list[videoitem] != None:
            video_lang = video_list[videoitem]
            languages = ['latino', 'spanish', 'subtitulos']
            for lang in languages:
                if video_lang[lang] != None:
                    if not isinstance(video_lang[lang], int):
                        video_id = video_lang[lang][0]["video"]
                        post = {"video": video_id, "sub": sub}
                        post = urllib.urlencode(post)
                        data = httptools.downloadpage(video_base_url, post=post).data
                        playlist = jsontools.load(data)
                        sources = playlist[['playlist'][0]]
                        server = playlist['server']

                        for video_link in sources:
                            url = video_link['sources']
                            if 'onevideo' in url:
                                data = get_source(url)
                                g_urls = servertools.findvideos(data=data)
                                url = g_urls[0][1]
                                server = g_urls[0][0]
                            if url not in duplicated:
                                lang = lang.capitalize()
                                if lang == 'Spanish':
                                    lang = 'Español'
                                title = '(%s) %s (%s)' % (server, item.title, lang)
                                thumbnail = servertools.guess_server_thumbnail(server)
                                itemlist.append(item.clone(title=title,
                                                           url=url,
                                                           server=server,
                                                           thumbnail=thumbnail,
                                                           action='play'
                                                           ))
                                duplicated.append(url)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle
                 ))

    return itemlist


def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host + "peliculas/"
        elif category == 'infantiles':
            item.url = host + 'categorias/peliculas-de-animacion.html'
        itemlist = listado(item)
        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
