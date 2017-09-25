# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

CHANNEL_HOST = "http://www.cinetux.net/"

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
    itemlist = []
    item.viewmode = viewmode

    data = httptools.downloadpage(CHANNEL_HOST).data
    total = scrapertools.find_single_match(data, "TENEMOS\s<b>(.*?)</b>")
    titulo = "Peliculas (%s)" % total
    itemlist.append(item.clone(title=titulo, text_color=color2, action="", text_bold=True))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "pelicula",
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Directors%20Chair.png",
                               text_color=color1))
    itemlist.append(item.clone(action="destacadas", title="      Destacadas", url="http://www.cinetux.net/mas-vistos/",
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Favorites.png",
                               text_color=color1))
    itemlist.append(item.clone(action="idioma", title="      Por idioma", text_color=color1))
    itemlist.append(item.clone(action="generos", title="      Por géneros", url=CHANNEL_HOST,
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Genre.png",
                               text_color=color1))

    itemlist.append(item.clone(title="Documentales", text_bold=True, text_color=color2, action=""))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "genero/documental/", text_color=color1,
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/Documentaries.png"))
    itemlist.append(item.clone(action="peliculas", title="      Por orden alfabético", text_color=color1, url=CHANNEL_HOST + "genero/documental/?orderby=title&order=asc&gdsr_order=asc",
                               thumbnail="https://raw.githubusercontent.com/master-1970/resources/master/images/genres"
                                         "/0/A-Z.png"))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(action="search", title="Buscar...", text_color=color3))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "http://www.cinetux.net/?s="
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
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        elif categoria == 'documentales':
            item.url = CHANNEL_HOST + "genero/documental/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

        elif categoria == 'infantiles':
            item.url = CHANNEL_HOST + "genero/infantil/"
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
    patron += '.*?(?:<span>|<span class="year">)([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, calidad, scrapedurl, scrapedyear in matches:
        calidad = scrapertools.find_single_match(calidad, '.*?quality">([^<]+)')
        try:
            fulltitle = scrapedtitle
            year = scrapedyear.replace("&nbsp;", "")
            if "/" in fulltitle:
                fulltitle = fulltitle.split(" /", 1)[0]
            scrapedtitle = "%s (%s)" % (fulltitle, year)
        except:
            fulltitle = scrapedtitle
        if calidad:
            scrapedtitle += "  [%s]" % calidad
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=fulltitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentTitle=fulltitle, contentType="movie")
        if year:
            new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)

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

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    bloque = scrapertools.find_single_match(data, 'peliculas_destacadas.*?class="single-page')
    patron = '(?s)title="([^"]+)"'
    patron += '.href="([^"]+)"'
    patron += '.*?src="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        scrapedurl = "http://www.cinetux.net" + scrapedurl
        scrapedtitle = scrapedtitle.replace("Ver ", "")
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentTitle=scrapedtitle, contentType="movie")
        itemlist.append(new_item)

    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link:
        itemlist.append(
            item.clone(action="destacadas", title=">> Página siguiente", url=next_page_link, text_color=color3))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?s)dos_columnas">(.*?)</ul>')
    # Extrae las entradas
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

    # Busca el argumento
    data = httptools.downloadpage(item.url).data
    year = scrapertools.find_single_match(item.title, "\(([0-9]+)")

    if year and item.extra != "library":
        item.infoLabels['year'] = int(year)
        # Ampliamos datos en tmdb
        if not item.infoLabels['plot']:
            try:
                tmdb.set_infoLabels(item, __modo_grafico__)
            except:
                pass

    if not item.infoLabels.get('plot'):
        plot = scrapertools.find_single_match(data, '<div class="sinopsis"><p>(.*?)</p>')
        item.infoLabels['plot'] = plot

    if filtro_enlaces != 0:
        list_enlaces = bloque_enlaces(data, filtro_idioma, dict_idiomas, "online", item)
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

    if itemlist:
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la videoteca"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     filtro=True, action="add_pelicula_to_library", url=item.url,
                                     infoLabels={'title': item.fulltitle}, fulltitle=item.fulltitle,
                                     extra="library"))

    else:
        itemlist.append(item.clone(title="No hay enlaces disponibles", action="", text_color=color3))
    return itemlist


def bloque_enlaces(data, filtro_idioma, dict_idiomas, type, item):
    logger.info()
    lista_enlaces = []
    matches = []
    if type == "online": t_tipo = "Ver Online"
    if type == "descarga": t_tipo = "Descargar"
    data = data.replace("\n", "")
    if type == "online":
        patron = '(?is)class="playex.*?visualizaciones'
        bloque1 = scrapertools.find_single_match(data, patron)
        patron = '(?is)#(option-[^"]+).*?png">([^<]+)'
        match = scrapertools.find_multiple_matches(data, patron)
        for scrapedoption, language in match:
            scrapedserver = ""
            lazy = ""
            if "lazy" in bloque1:
                lazy = "lazy-"
            patron = '(?s)id="%s".*?metaframe.*?%ssrc="([^"]+)' % (scrapedoption, lazy)
            url = scrapertools.find_single_match(bloque1, patron)
            if "goo.gl" in url:
                url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
            if "player" in url:
                scrapedserver = scrapertools.find_single_match(url, 'player/(\w+)')
            matches.append([url, scrapedserver, "", language.strip(), t_tipo])
    bloque2 = scrapertools.find_single_match(data, '(?s)box_links.*?dt_social_single')
    bloque2 = bloque2.replace("\t", "").replace("\r", "")
    patron = '(?s)optn" href="([^"]+)'
    patron += '.*?title="([^\.]+)'
    patron += '.*?src.*?src="[^>]+"?/>([^<]+)'
    patron += '.*?src="[^>]+"?/>([^<]+)'
    patron += '.*?/span>([^<]+)'
    matches.extend(scrapertools.find_multiple_matches(bloque2, patron))
    filtrados = []
    for match in matches:
        scrapedurl = match[0]
        scrapedserver = match[1]
        scrapedcalidad = match[2]
        scrapedlanguage = match[3]
        scrapedtipo = match[4]
        if t_tipo.upper() not in scrapedtipo.upper():
            continue
        title = "   Mirror en %s (" + scrapedlanguage + ")"
        if len(scrapedcalidad.strip()) > 0:
            title += " (Calidad " + scrapedcalidad.strip() + ")"

        if filtro_idioma == 3 or item.filtro:
            lista_enlaces.append(item.clone(title=title, action="play", text_color=color2,
                                            url=scrapedurl, server=scrapedserver, idioma=scrapedlanguage,
                                            extra=item.url, contentThumbnail = item.thumbnail))
        else:
            idioma = dict_idiomas[language]
            if idioma == filtro_idioma:
                lista_enlaces.append(item.clone(title=title, text_color=color2, action="play", url=scrapedurl,
                                                extra=item.url, contentThumbnail = item.thumbnail))
            else:
                if language not in filtrados:
                    filtrados.append(language)
    if filtro_idioma != 3:
        if len(filtrados) > 0:
            title = "Mostrar enlaces filtrados en %s" % ", ".join(filtrados)
            lista_enlaces.append(item.clone(title=title, action="findvideos", url=item.url, text_color=color3,
                                            filtro=True))
    lista_enlaces = servertools.get_servers_itemlist(lista_enlaces, lambda i: i.title % i.server.capitalize())
    return lista_enlaces


def play(item):
    logger.info()
    itemlist = []
    if "api.cinetux" in item.url:
        data = httptools.downloadpage(item.url, headers={'Referer': item.extra}).data.replace("\\", "")
        id = scrapertools.find_single_match(data, 'img src="[^#]+#(.*?)"')
        item.url = "https://youtube.googleapis.com/embed/?status=ok&hl=es&allow_embed=1&ps=docs&partnerid=30&hd=1&autoplay=0&cc_load_policy=1&showinfo=0&docid=" + id
    elif "links" in item.url or "www.cinetux.me" in item.url:
        data = httptools.downloadpage(item.url).data
        scrapedurl = scrapertools.find_single_match(data, '<a href="(http[^"]+)')
        if scrapedurl == "":
            scrapedurl = scrapertools.find_single_match(data, '(?i)frame.*?src="(http[^"]+)')
            if scrapedurl == "":
                scrapedurl = scrapertools.find_single_match(data, 'replace."([^"]+)"')
        elif "goo.gl" in scrapedurl:
            scrapedurl = httptools.downloadpage(scrapedurl, follow_redirects=False, only_headers=True).headers.get(
                "location", "")
        item.url = scrapedurl
    item.thumbnail = item.contentThumbnail
    item.server = servertools.get_server_from_url(item.url)
    return [item]
