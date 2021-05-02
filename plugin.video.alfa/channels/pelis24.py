# -*- coding: utf-8 -*-
# -*- Channel CanalPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "pelis24"

host = "https://www.pelis24.in/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""


list_quality = ['HD 1080p', 'HDRip', 'TS-Screener']
list_servers = ['upstream', 'uqload', 'clipwatching', 'streamtape', 'aparat', 'steamz']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Novedades", action="peliculas", thumbnail=get_thumb('newest', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'movies/', viewmode="movie_with_plot"),

                # item.clone(title="Tendencias", action="peliculas", thumbnail=get_thumb('newest', auto=True),
                #            text_blod=True, page=0, viewcontent='movies',
                #            url=host + 'tendencias/?get=movies', viewmode="movie_with_plot"),

                item.clone(title="Estrenos", action="peliculas", thumbnail=get_thumb('estrenos', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'genre/estrenos/', viewmode="movie_with_plot"),
                
                item.clone(title="Castellano", action="peliculas", thumbnail=get_thumb('cast', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'genre/castellano/', viewmode="movie_with_plot"),
                item.clone(title="Latino", action="peliculas", thumbnail=get_thumb('lat', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'genre/latino/', viewmode="movie_with_plot"),
                
                item.clone(title="Generos", action="genres", thumbnail=get_thumb('genres', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),
                
                item.clone(title="Años", action="genres", thumbnail=get_thumb('year', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                item.clone(title="A-Z", action="alphabet", thumbnail=get_thumb('alphabet', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                item.clone(title="Buscar...", action="search", thumbnail=get_thumb('search', auto=True),
                           text_blod=True, url=host, page=0)]

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return sub_search(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\s{2}", "", data)
    #data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
    data = scrapertools.find_single_match(data, '</h1>(.*?)</article></div></div>')
    patron = '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'
    patron += 'year">(.*?)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for  scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:
        if 'tvshows' not in scrapedurl:
            itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, contentTitle=scrapedtitle,
                                       action="findvideos", infoLabels={"year": year},
                                       thumbnail=scrapedthumbnail, text_color=color3))

    paginacion = scrapertools.find_single_match(data, "<span class=\"current\">\d+</span><a href='([^']+)'")

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=paginacion,
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    #data = scrapertools.decodeHtmlentities(data)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\s{2}", "", data)
    bloq = scrapertools.find_single_match(data, 
            'class="archive_post">(.*?)resppages') or data

    # img, title
    patron = '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += 'quality">([^<]+)<.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'span>.*?(\d{4})<'

    matches = scrapertools.find_multiple_matches(bloq, patron)
    
    #logger.info(patron)
    #logger.info(matches)
    #logger.info(bloq)

    for scrapedthumbnail, scrapedtitle, quality, scrapedurl, year in matches[item.page:item.page + 30]:
        scrapedtitle = re.sub(r'\d{4}$', '', scrapedtitle).strip()
        title = '%s [COLOR yellowgreen](%s)[/COLOR]' % (scrapedtitle, quality)

        itemlist.append(Item(channel=__channel__, action="findvideos", text_color=color3,
                             url=scrapedurl, infoLabels={'year': year}, quality=quality,
                             contentTitle=scrapedtitle, thumbnail=scrapedthumbnail,
                             title=title, context="buscar_trailer"))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="» Siguiente »", text_color=color3))
    else:
        next_page = scrapertools.find_single_match(data, '<a class=\'arrow_pag\' href="([^"]+)"')
        if next_page:
            itemlist.append(Item(channel=item.channel, url=next_page, page=0, 
                                title="Siguiente >>", text_color=color3))

    return itemlist


def alphabet(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|&nbsp;|<br>", "", data)
    data = scrapertools.decodeHtmlentities(data)
    
    json_api, nonce = scrapertools.find_single_match(data, '"glossary":"([^"]+)","nonce":"([^"]+)"')
    json_api = json_api.replace("\\", "")
    patron_todas = '<ul class="glossary"(.*?)</li></ul></div>'
    bloq = scrapertools.find_single_match(data, patron_todas)
    patron = 'data-glossary="([^"]+)">([^<]+)</a>'  # url, title
    matches = scrapertools.find_multiple_matches(bloq, patron)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = scrapedurl.replace('09', '1')
        url = json_api+"?term=%s&nonce=%s&type=movies" % (scrapedurl, nonce)
        itemlist.append(item.clone(title=scrapedtitle, url=url, action="api_peliculas"))
    return itemlist

def api_peliculas(item):
    logger.info()
    itemlist = []
    json_data = httptools.downloadpage(item.url).json

    for _id, val in list(json_data.items()):
        url = val['url']
        title = val['title']
        thumbnail = val['img']
        try:
            year = val['year']
        except:
            year = "-"
        itemlist.append(Item(channel=__channel__, action="findvideos", text_color=color3,
                             url=url, infoLabels={'year': year},
                             contentTitle=title, thumbnail=thumbnail,
                             title=title, context="buscar_trailer"))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    return itemlist

def genres(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    # logger.info(data)
    pbloq = '<nav class="releases".*?</nav>'
    if 'Generos' in item.title:
        pbloq = '<nav class="genres".*?</nav>'
    bloq = scrapertools.find_single_match(data, pbloq)
    patron = '<li.*?><a href="([^"]+)">([^<]+)</a>'  # url, title
    matches = re.compile(patron, re.DOTALL).findall(bloq)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(channel=item.channel, action="peliculas", title=scrapedtitle, page=0,
                                   url=scrapedurl, text_color=color3, viewmode="movie_with_plot"))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    list_language = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = data.replace("'",'"')
    
    patron = 'data-type="([^"]+)" data-post="(\d+)" data-nume="(\d+)'
    patron += '.*?title">([^<]+).*?server">(\w+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for _type, pid, num, lang, server in matches:
        
        lang = lang.lower().strip()
        languages = {'latino': '[COLOR cornflowerblue][LAT][/COLOR]',
                     'castellano': '[COLOR limegreen][CAST][/COLOR]',
                     'español': '[COLOR limegreen][CAST][/COLOR]',
                     'sub español': '[COLOR grey][VOSE][/COLOR]',
                     'subtitulado': '[COLOR grey][VOSE][/COLOR]',
                     'sup espaÑol': '[COLOR grey][VOSE][/COLOR]',
                     'sub': '[COLOR grey][VOSE][/COLOR]',
                     'ingles': '[COLOR red][VOS][/COLOR]'}
        lang = languages.get(lang, lang)
        
        #tratando con los idiomas
        language = scrapertools.find_single_match(lang, '\((\w+)\)')
        list_language.append(language)

        post = {'action': 'doo_player_ajax', 'post': pid, 'nume': num, 'type':_type}
        post_url = '%swp-admin/admin-ajax.php' % host
        new_data = httptools.downloadpage(post_url, post=post, headers={'Referer':item.url}).data
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        
        title = "»» [COLOR yellow](%s)[/COLOR] [COLOR goldenrod](%s)[/COLOR] %s ««" % (
            server.title(), item.quality, lang)
        # if 'google' not in url and 'directo' not in server:

        itemlist.append(item.clone(action='play', url=url, title=title, language=language, text_color=color3))

    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist.sort(key=lambda it: it.language, reverse=False)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             contentTitle=item.contentTitle))

    return itemlist
