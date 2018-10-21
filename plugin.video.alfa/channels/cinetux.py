# -*- coding: utf-8 -*-

import re
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'Latino': 'Latino', 'Subtitulado': 'Subtitulado', 'Español': 'Español', 'SUB': 'SUB' }
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'okru', 'vidoza', 'openload', 'powvideo', 'netutv','gvideo']


CHANNEL_HOST = "http://www.cinetux.to/"

# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'cinetux')
__perfil__ = config.get_setting('perfil', 'cinetux')

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', 'cinetux')]


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    item.viewmode = viewmode
    data = httptools.downloadpage(CHANNEL_HOST + "pelicula").data
    total = scrapertools.find_single_match(data, "Películas</h1><span>(.*?)</span>")
    titulo = "Peliculas (%s)" %total
    itemlist.append(item.clone(title=titulo, text_color=color2, action="", text_bold=True))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "pelicula",
                               thumbnail=get_thumb('newest', auto=True),
                               text_color=color1))
    itemlist.append(item.clone(action="destacadas", title="      Destacadas", url=CHANNEL_HOST + "mas-vistos/",
                               thumbnail=get_thumb('hot', auto=True),
                               text_color=color1))
    itemlist.append(item.clone(action="idioma", title="      Por idioma", text_color=color1,
                               thumbnail=get_thumb('language', auto=True)))
    itemlist.append(item.clone(action="generos", title="      Por géneros", url=CHANNEL_HOST,
                               thumbnail=get_thumb('genres', auto=True),
                               text_color=color1))

    itemlist.append(item.clone(title="Documentales", text_bold=True, text_color=color2, action=""))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "genero/documental/", text_color=color1,
                               thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(item.clone(action="peliculas", title="      Por orden alfabético", text_color=color1, url=CHANNEL_HOST + "genero/documental/?orderby=title&order=asc&gdsr_order=asc",
                               thumbnail=get_thumb('alphabet', auto=True)))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(action="search", title="Buscar...", text_color=color3,
                               thumbnail=get_thumb('search', auto=True)))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = CHANNEL_HOST + "?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = CHANNEL_HOST
            item.action = "peliculas"

        elif categoria == 'documentales':
            item.url = CHANNEL_HOST + "genero/documental/"
            item.action = "peliculas"

        elif categoria == 'infantiles':
            item.url = CHANNEL_HOST + "genero/animacion/"
            item.action = "peliculas"

        elif categoria == 'terror':
            item.url = CHANNEL_HOST + "genero/terror/"
            item.action = "peliculas"

        elif categoria == 'castellano':
            item.url = CHANNEL_HOST + "idioma/espanol/"
            item.action = "peliculas"

        elif categoria == 'latino':
            item.url = CHANNEL_HOST + "idioma/latino/"
            item.action = "peliculas"

        itemlist = peliculas(item)
        if itemlist[-1].action == "peliculas":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    patron = '(?s)class="(?:result-item|item movies)">.*?<img src="([^"]+)'
    patron += '.*?alt="([^"]+)"'
    patron += '(.*?)'
    patron += 'href="([^"]+)"'
    patron += '.*?(?:<span>|<span class="year">)(.+?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, quality, scrapedurl, scrapedyear in matches:
        quality = scrapertools.find_single_match(quality, '.*?quality">([^<]+)')
        try:
            fulltitle = scrapedtitle
            year = scrapertools.find_single_match(scrapedyear,'\d{4}')
            if "/" in fulltitle:
                fulltitle = fulltitle.split(" /", 1)[0]
            scrapedtitle = "%s (%s)" % (fulltitle, year)
        except:
            fulltitle = scrapedtitle
        if quality:
            scrapedtitle += "  [%s]" % quality
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=fulltitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentType="movie", quality=quality)
        if year:
            new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone(action="peliculas", title=">> Página siguiente", url=next_page_link,
                                   text_color=color3))
    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'peliculas_destacadas.*?class="letter_home"')
    patron = '(?s)title="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'
    patron += 'src="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        scrapedurl = CHANNEL_HOST + scrapedurl
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentType="movie"
                              ))
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link:
        itemlist.append(
            item.clone(action="destacadas", title=">> Página siguiente", url=next_page_link, text_color=color3))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?s)dos_columnas">(.*?)</ul>')
    patron = '<li><a.*?href="/([^"]+)">(.*?)</li>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        scrapedurl = CHANNEL_HOST + scrapedurl
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        scrapedtitle = unicode(scrapedtitle, "utf8").capitalize().encode("utf8")
        if scrapedtitle == "Erotico" and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(item.clone(action="peliculas", title=scrapedtitle, url=scrapedurl))
    return itemlist


def idioma(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="peliculas", title="Español", url= CHANNEL_HOST + "idioma/espanol/"))
    itemlist.append(item.clone(action="peliculas", title="Latino", url= CHANNEL_HOST + "idioma/latino/"))
    itemlist.append(item.clone(action="peliculas", title="VOSE", url= CHANNEL_HOST + "idioma/subtitulado/"))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    try:
        filtro_idioma = config.get_setting("filterlanguages", item.channel)
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_idioma = 3
        filtro_enlaces = 2
    dict_idiomas = {'Español': 2, 'Latino': 1, 'Subtitulado': 0}
    data = httptools.downloadpage(item.url).data
    if filtro_enlaces != 0:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "online", item)
        return
        if list_enlaces:
            itemlist.append(item.clone(action="", title="Enlaces Online", text_color=color1,
                                       text_bold=True))
            itemlist.extend(list_enlaces)
    if filtro_enlaces != 1:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "descarga", item)
        if list_enlaces:
            itemlist.append(item.clone(action="", title="Enlaces Descarga", text_color=color1,
                                       text_bold=True))
            itemlist.extend(list_enlaces)
    tmdb.set_infoLabels(item, __modo_grafico__)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if itemlist:
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, fulltitle = item.fulltitle
                                     ))
    return itemlist


# def bloque_enlaces(data, filtro_idioma, dict_idiomas, type, item):
#     logger.info()
#     lista_enlaces = []
#     matches = []
#     if type == "online": t_tipo = "Ver Online"
#     if type == "descarga": t_tipo = "Descargar"
#     data = data.replace("\n", "")
#     if type == "online":
#         patron = '(?is)class="playex.*?sheader'
#         bloque1 = scrapertools.find_single_match(data, patron)
#         patron = '(?is)#(option-[^"]+).*?png">([^<]+)'
#         match = scrapertools.find_multiple_matches(data, patron)
#         for scrapedoption, language in match:
#             scrapedserver = ""
#             lazy = ""
#             if "lazy" in bloque1:
#                 lazy = "lazy-"
#             patron = '(?s)id="%s".*?metaframe.*?%ssrc="([^"]+)' % (scrapedoption, lazy)
#             url = scrapertools.find_single_match(bloque1, patron)
#             if "goo.gl" in url:
#                 url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
#             if "drive.php" in url:
#                 scrapedserver = "gvideo"
#             if "player" in url:
#                 scrapedserver = scrapertools.find_single_match(url, 'player/(\w+)')
#                 if "ok" in scrapedserver: scrapedserver = "okru"
#             matches.append([url, scrapedserver, "", language.strip(), t_tipo])
#     bloque2 = scrapertools.find_single_match(data, '(?s)box_links.*?dt_social_single')
#     bloque2 = bloque2.replace("\t", "").replace("\r", "")
#     patron = '(?s)optn" href="([^"]+)'
#     patron += '.*?alt="([^\.]+)'
#     patron += '.*?src.*?src="[^>]+"?/>([^<]+)'
#     patron += '.*?src="[^>]+"?/>([^<]+)'
#     patron += '.*?/span>([^<]+)'
#     matches.extend(scrapertools.find_multiple_matches(bloque2, patron))
#     filtrados = []
#     for match in matches:
#         scrapedurl = match[0]
#         scrapedserver = match[1]
#         scrapedcalidad = match[2]
#         language = match[3]
#         scrapedtipo = match[4]
#         if t_tipo.upper() not in scrapedtipo.upper():
#             continue
#         title = "   Mirror en %s (" + language + ")"
#         if len(scrapedcalidad.strip()) > 0:
#             title += " (Calidad " + scrapedcalidad.strip() + ")"
#
#         if filtro_idioma == 3 or item.filtro:
#             lista_enlaces.append(item.clone(title=title, action="play", text_color=color2,
#                                             url=scrapedurl, server=scrapedserver,
#                                             extra=item.url, contentThumbnail = item.thumbnail,
#                                             language=language))
#         else:
#             idioma = dict_idiomas[language]
#             if idioma == filtro_idioma:
#                 lista_enlaces.append(item.clone(title=title, action="play", text_color=color2,
#                                                 url=scrapedurl, server=scrapedserver,
#                                                 extra=item.url, contentThumbnail = item.thumbnail,
#                                                 language=language))
#             else:
#                 if language not in filtrados:
#                     filtrados.append(language)
#     lista_enlaces = servertools.get_servers_itemlist(lista_enlaces, lambda i: i.title % i.server.capitalize())
#     if filtro_idioma != 3:
#         if len(filtrados) > 0:
#             title = "Mostrar también enlaces filtrados en %s" % ", ".join(filtrados)
#             lista_enlaces.append(item.clone(title=title, action="findvideos", url=item.url, text_color=color3,
#                                             filtro=True))
#     return lista_enlaces
#
#
# def play(item):
#     logger.info()
#     itemlist = []
#     if "api.cinetux" in item.url or item.server == "okru" or "drive.php" in item.url or "youtube" in item.url:
#         data = httptools.downloadpage(item.url, headers={'Referer': item.extra}).data.replace("\\", "")
#         id = scrapertools.find_single_match(data, 'img src="[^#]+#(.*?)"')
#         item.url = "http://docs.google.com/get_video_info?docid=" + id
#         if item.server == "okru":
#             item.url = "https://ok.ru/videoembed/" + id
#         if item.server == "youtube":
#             item.url = "https://www.youtube.com/embed/" + id
#     elif "links" in item.url or "www.cinetux.me" in item.url:
#         data = httptools.downloadpage(item.url).data
#         scrapedurl = scrapertools.find_single_match(data, '<a href="(http[^"]+)')
#         if scrapedurl == "":
#             scrapedurl = scrapertools.find_single_match(data, '(?i)frame.*?src="(http[^"]+)')
#             if scrapedurl == "":
#                 scrapedurl = scrapertools.find_single_match(data, 'replace."([^"]+)"')
#         elif "goo.gl" in scrapedurl:
#             scrapedurl = httptools.downloadpage(scrapedurl, follow_redirects=False, only_headers=True).headers.get(
#                 "location", "")
#         item.url = scrapedurl
#     item.server = ""
#     itemlist.append(item.clone())
#     itemlist = servertools.get_servers_itemlist(itemlist)
#     for i in itemlist:
#         i.thumbnail = i.contentThumbnail
#     return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer == None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def findvideos(item):
    import urllib
    logger.info()

    itemlist=[]

    data = get_source(item.url)

    patron = 'class="title">([^>]+)</span>.*?data-type="([^"]+)" data-post="(\d+)" data-nume="(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for language, tp, pt, nm in matches:

        post = {'action':'doo_player_ajax', 'post':pt, 'nume':nm, 'type':tp}
        post = urllib.urlencode(post)
        new_data = httptools.downloadpage(CHANNEL_HOST+'wp-admin/admin-ajax.php', post=post, headers={'Referer':item.url}).data
        if not config.get_setting('unify'):
            if item.quality == '':
                quality = 'SD'
            else:
                quality = item.quality
            title = ' [%s][%s]' % (quality, IDIOMAS[language])
        else:
            title = ''
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        itemlist.append(Item(channel=item.channel, title ='%s'+title, url=url, action='play', quality=item.quality,
                             language=IDIOMAS[language], infoLabels=item.infoLabels))

    patron = "<a class='optn' href='([^']+)'.*?<img src='.*?>([^<]+)<.*?<img src='.*?>([^<]+)<"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for hidden_url, quality, language in matches:

        if not config.get_setting('unify'):
            title = ' [%s][%s]' % (quality, IDIOMAS[language])
        else:
            title = ''
        new_data = get_source(hidden_url)
        url = scrapertools.find_single_match(new_data, '"url":"([^"]+)"')
        url = url.replace('\\/', '/')
        itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', quality=quality,
                             language=IDIOMAS[language], infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist