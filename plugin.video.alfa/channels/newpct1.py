# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb

host = 'http://newpct1.com/'

def mainlist(item):
    logger.info()

    itemlist = []

    thumb_pelis=get_thumb("channels_movie.png")
    thumb_series=get_thumb("channels_tvshow.png")
    thumb_search = get_thumb("search.png")

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host,
                         extra="peliculas", thumbnail=thumb_pelis ))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series",
                         thumbnail=thumb_series))
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", url=host + "buscar", thumbnail=thumb_search))

    return itemlist


def search(item, texto):
    logger.info("search:" + texto)
    texto = texto.replace(" ", "+")
    item.url = "http://www.newpct1.com/index.php?page=buscar&q=%27" + texto + "%27&ordenar=Fecha&inon=Descendente"
    item.extra = "buscar-list"
    try:
        itemlist = completo(item)

        # Esta pagina coloca a veces contenido duplicado, intentamos descartarlo
        dict_aux = {}
        for i in itemlist:
            if not i.url in dict_aux:
                dict_aux[i.url] = i
            else:
                itemlist.remove(i)

        return itemlist


    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def submenu(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    patron = '<li><a href="http://(?:www.)?newpct1.com/' + item.extra + '/">.*?<ul>(.*?)</ul>'
    data = scrapertools.get_match(data, patron)

    patron = '<a href="([^"]+)".*?>([^>]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, extra="pelilist"))
        itemlist.append(
            Item(channel=item.channel, action="alfabeto", title=title + " [A-Z]", url=url, extra="pelilist"))

    return itemlist


def alfabeto(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    patron = '<ul class="alfabeto">(.*?)</ul>'
    data = scrapertools.get_match(data, patron)

    patron = '<a href="([^"]+)"[^>]+>([^>]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.upper()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, extra=item.extra))

    return itemlist


def listado(item):
    logger.info()
    # logger.info("[newpct1.py] listado url=" + item.url)
    itemlist = []
    url_next_page =''

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    #logger.debug(data)
    logger.debug('item.modo: %s'%item.modo)
    logger.debug('item.extra: %s'%item.extra)

    if item.modo != 'next' or item.modo =='':
        logger.debug('item.title: %s'% item.title)
        patron = '<ul class="' + item.extra + '">(.*?)</ul>'
        logger.debug("patron=" + patron)
        fichas = scrapertools.get_match(data, patron)
        page_extra = item.extra
    else:
        fichas = data
        page_extra = item.extra

    # <li><a href="http://www.newpct1.com/pelicula/x-men-dias-del-futuro-pasado/ts-screener/" title="Descargar XMen Dias Del Futuro gratis"><img src="http://www.newpct1.com/pictures/f/58066_x-men-dias-del-futuro--blurayrip-ac3-5.1.jpg" width="130" height="180" alt="Descargar XMen Dias Del Futuro gratis"><h2>XMen Dias Del Futuro </h2><span>BluRayRip AC3 5.1</span></a></li>
    patron = '<li><a href="([^"]+).*?'  # url
    patron += 'title="([^"]+).*?'  # titulo
    patron += '<img src="([^"]+)"[^>]+>.*?'  # thumbnail
    patron += '<span>([^<]*)</span>'  # calidad

    matches = re.compile(patron, re.DOTALL).findall(fichas)
    logger.debug('item.next_page: %s'%item.next_page)


    # Paginacion
    if item.next_page != 'b':
        if len(matches) > 30:
            url_next_page = item.url
        matches = matches[:30]
        next_page = 'b'
        modo = 'continue'
    else:
        matches = matches[30:]
        next_page = 'a'
        patron_next_page = '<a href="([^"]+)">Next<\/a>'
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = matches_next_page[0]
            modo = 'next'

    for scrapedurl, scrapedtitle, scrapedthumbnail, calidad in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        action = "findvideos"
        extra = ""
        year = scrapertools.find_single_match(scrapedthumbnail, r'-(\d{4})')
        if "1.com/series" in url:
            action = "episodios"
            extra = "serie"


            title = scrapertools.find_single_match(title, '([^-]+)')
            title = title.replace("Ver online", "", 1).replace("Descarga Serie HD", "", 1).replace("Ver en linea", "",
                                                                                                   1).strip()
            # logger.info("[newpct1.py] titulo="+title)

        else:
            title = title.replace("Descargar", "", 1).strip()
            if title.endswith("gratis"): title = title[:-7]

        show = title
        if item.extra != "buscar-list":
            title = title + ' ' + calidad

        context = ""
        context_title = scrapertools.find_single_match(url, "http://(?:www.)?newpct1.com/(.*?)/(.*?)/")
        #logger.debug('context_title[0]: %s' % context_title[0])
        if context_title:
            try:
                context = context_title[0].replace("descargar-", "").replace("pelicula", "movie").replace("series",
                                                                                                              "tvshow")
                context_title = context_title[1].replace("-", " ")
                if re.search('\d{4}', context_title[-4:]):
                    context_title = context_title[:-4]
                elif re.search('\(\d{4}\)', context_title[-6:]):
                    context_title = context_title[:-6]

            except:
                context_title = show
        logger.debug('contxt title: %s'%context_title)
        logger.debug('year: %s' % year)

        logger.debug('context: %s' % context)
        if not 'array' in title:
            new_item = Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                            extra = extra,
                     show = context_title, contentTitle=context_title, contentType=context,
                     context=["buscar_trailer"], infoLabels= {'year':year})
            if year:
                tmdb.set_infoLabels_item(new_item, seekTmdb = True)
            itemlist.append(new_item)




    if url_next_page:
        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente",
                             url=url_next_page, next_page=next_page, folder=True,
                             text_color='yellow', text_bold=True, modo = modo, plot = extra,
                             extra = page_extra))
    # if "pagination" in data:
    #     patron = '<ul class="pagination">(.*?)</ul>'
    #     paginacion = scrapertools.get_match(data, patron)
    #
    #     if "Next" in paginacion:
    #         url_next_page = scrapertools.get_match(paginacion, '<a href="(http[^>]+)>Next</a>')[:-1].replace(" ", "%20")
    #         itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente", url=url_next_page,
    #                              extra=item.extra))
            # logger.info("[newpct1.py] listado items:" + str(len(itemlist)))
    return itemlist

def listado2(item):
    logger.info()
    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    logger.debug(data)
    list_chars = [["Ã±", "ñ"]]

    for el in list_chars:
        data = re.sub(r"%s" % el[0], el[1], data)

    try:
        # logger.debug("data %s " % data)
        get, post = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a class="current" href.*?'
                                                         '<a\s*href="([^"]+)"(?:\s*onClick=".*?\'([^"]+)\'.*?")')
    except:
        post = False

    if post:
        # logger.debug("post %s" % post)
        # logger.debug("item.post %s" % item.post)
        if "pg" in item.post:
            item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
            # logger.debug("item.post %s" % item.post)
        else:
            item.post += "&pg=%s" % post
            # logger.debug("item.post %s" % item.post)

    # logger.debug("data %s " % next_page)

    pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
    data = scrapertools.get_match(data, pattern)
    # logger.debug("data %s " % data)

    pattern = '<li><a href="(?P<url>[^"]+)".*?<img src="(?P<img>[^"]+)"[^>]+>.*?<h2.*?>\s*(?P<title>.*?)\s*</h2>'

    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url, thumb, title in matches:
        # fix encoding for title
        title = scrapertools.htmlclean(title)
        title = title.replace("ï¿½", "ñ")

        # logger.debug("\n\nu %s " % url)
        # logger.debug("\nb %s " % thumb)
        # logger.debug("\nt %s " % title)

        # title is the clean way but it doesn't work if it's a long, so we have to use title_to_fix
        # title_fix = False
        # if title.endswith(".."):
        #     title = title_to_fix
        #     title_fix = True

        # no mostramos lo que no sean videos
        if "/juego/" in url or "/varios/" in url:
            continue

        if ".com/series" in url:
            # title = scrapertools.find_single_match(title, '([^-]+)')
            # title = title.replace("Ver online", "", 1).replace("Ver en linea", "", 1). \
            #     replace("Descarga Serie HD", "", 1).strip()

            show = title
            # if quality:
            #     title = "%s [%s]" % (title, quality)

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumb,
                                 context=["buscar_trailer"], show=show))

        else:
            # title = title.replace("Descargar", "", 1).strip()
            # if title.endswith("gratis"):
            #     title = title[:-6].strip()

            # if quality:
            #     title = "%s [%s]" % (title, quality)

                itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                     context=["buscar_trailer"]))

    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado2", title=">> Página siguiente",
                                   thumbnail=get_thumb("next.png")))

    return itemlist




def completo(item):
    logger.info()
    itemlist = []
    categoryID = ""

    # Guarda el valor por si son etiquetas para que lo vea 'listadofichas'
    item_extra = item.extra
    item_show = item.show
    item_title = item.title
    infoLabels = item.infoLabels

    # Lee las entradas
    if item_extra.startswith("serie"):
        ultimo_action = "get_episodios"

        if item.extra != "serie_add":
            '''
            # Afinar mas la busqueda
            if item_extra=="serie-hd":
                categoryID=buscar_en_subcategoria(item.show,'1469')
            elif item_extra=="serie-vo":
                categoryID=buscar_en_subcategoria(item.show,'775')
            elif item_extra=="serie-tv":
                categoryID=buscar_en_subcategoria(item.show,'767')
            if categoryID !="":
                item.url=item.url.replace("categoryID=","categoryID="+categoryID)

            #Fanart
            oTvdb= TvDb()
            serieID=oTvdb.get_serieId_by_title(item.show)
            fanart = oTvdb.get_graphics_by_serieId(serieID)
            if len(fanart)>0:
                item.fanart = fanart[0]'''
            # try:
            #     from core.tmdb import Tmdb
            #     oTmdb = Tmdb(texto_buscado=item.show, tipo="tv", idioma_busqueda="es")
            #     item.fanart = oTmdb.get_backdrop()
            #     item.plot = oTmdb.get_sinopsis()
            #     print item.plot
            # except:
            #     pass
        else:
            item_title = item.show

        items_programas = get_episodios(item)
    else:
        ultimo_action = "listado"
        items_programas = listado(item)

    if len(items_programas) == 0:
        return itemlist  # devolver lista vacia

    salir = False
    while not salir:

        # Saca la URL de la siguiente página
        ultimo_item = items_programas[len(items_programas) - 1]

        # Páginas intermedias
        if ultimo_item.action == ultimo_action:
            # Quita el elemento de "Página siguiente"
            ultimo_item = items_programas.pop()

            # Añade las entradas de la página a la lista completa
            itemlist.extend(items_programas)

            # Carga la siguiente página
            ultimo_item.extra = item_extra
            ultimo_item.show = item_show
            ultimo_item.title = item_title
            logger.debug("url=" + ultimo_item.url)
            if item_extra.startswith("serie"):
                items_programas = get_episodios(ultimo_item)
            else:
                items_programas = listado(ultimo_item)

        # Última página
        else:
            # Añade a la lista completa y sale
            itemlist.extend(items_programas)
            salir = True

    if (config.get_videolibrary_support() and len(itemlist) > 0 and item.extra.startswith("serie")):
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la biblioteca", url=item.url,
                             action="add_serie_to_library", extra="completo###serie_add", show=item.show))
    logger.debug("items=" + str(len(itemlist)))
    return itemlist


def buscar_en_subcategoria(titulo, categoria):
    data = httptools.downloadpage("http://www.newpct1.com/pct1/library/include/ajax/get_subcategory.php",
                                  post="categoryIDR=" + categoria).data
    data = data.replace("</option>", " </option>")
    patron = '<option value="(\d+)">(' + titulo.replace(" ", "\s").replace("(", "/(").replace(")",
                                                                                              "/)") + '\s[^<]*)</option>'
    logger.debug("data=" + data)
    logger.debug("patron=" + patron)
    matches = re.compile(patron, re.DOTALL | re.IGNORECASE).findall(data)

    if len(matches) == 0: matches = [('', '')]
    logger.debug("resultado=" + matches[0][0])
    return matches[0][0]


def findvideos(item):
    logger.info()
    itemlist = []

    ## Cualquiera de las tres opciones son válidas
    # item.url = item.url.replace("1.com/","1.com/ver-online/")
    # item.url = item.url.replace("1.com/","1.com/descarga-directa/")
    item.url = item.url.replace("1.com/", "1.com/descarga-torrent/")

    # Descarga la página
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    title = scrapertools.find_single_match(data, "<h1><strong>([^<]+)</strong>[^<]+</h1>")
    title += scrapertools.find_single_match(data, "<h1><strong>[^<]+</strong>([^<]+)</h1>")
    caratula = scrapertools.find_single_match(data, '<div class="entry-left">.*?src="([^"]+)"')

    # <a href="http://tumejorjuego.com/download/index.php?link=descargar-torrent/058310_yo-frankenstein-blurayrip-ac3-51.html" title="Descargar torrent de Yo Frankenstein " class="btn-torrent" target="_blank">Descarga tu Archivo torrent!</a>

    patron = '<a href="([^"]+)" title="[^"]+" class="btn-torrent" target="_blank">'

    # escraped torrent
    url = scrapertools.find_single_match(data, patron)
    if url != "":
        itemlist.append(
            Item(channel=item.channel, action="play", server="torrent", title=title + " [torrent]", fulltitle=title,
                 url=url, thumbnail=caratula, plot=item.plot, folder=False))

    logger.debug("matar %s" % data)
    # escraped ver vídeos, descargar vídeos un link, múltiples liks
    data = data.replace("'", '"')
    data = data.replace(
        'javascript:;" onClick="popup("http://www.newpct1.com/pct1/library/include/ajax/get_modallinks.php?links=', "")
    data = data.replace("http://tumejorserie.com/descargar/url_encript.php?link=", "")
    data = data.replace("$!", "#!")

    patron_descargar = '<div id="tab2"[^>]+>.*?</ul>'
    patron_ver = '<div id="tab3"[^>]+>.*?</ul>'

    match_ver = scrapertools.find_single_match(data, patron_ver)
    match_descargar = scrapertools.find_single_match(data, patron_descargar)

    patron = '<div class="box1"><img src="([^"]+)".*?'  # logo
    patron += '<div class="box2">([^<]+)</div>'  # servidor
    patron += '<div class="box3">([^<]+)</div>'  # idioma
    patron += '<div class="box4">([^<]+)</div>'  # calidad
    patron += '<div class="box5"><a href="([^"]+)".*?'  # enlace
    patron += '<div class="box6">([^<]+)</div>'  # titulo

    enlaces_ver = re.compile(patron, re.DOTALL).findall(match_ver)
    enlaces_descargar = re.compile(patron, re.DOTALL).findall(match_descargar)

    for logo, servidor, idioma, calidad, enlace, titulo in enlaces_ver:
        servidor = servidor.replace("streamin", "streaminto")
        titulo = titulo + " [" + servidor + "]"
        mostrar_server = True
        if config.get_setting("hidepremium"):
            mostrar_server = servertools.is_server_enabled(servidor)
        if mostrar_server:
            try:
                devuelve = servertools.findvideosbyserver(enlace, servidor)
                if devuelve:
                    enlace = devuelve[0][1]
                    itemlist.append(
                        Item(fanart=item.fanart, channel=item.channel, action="play", server=servidor, title=titulo,
                             fulltitle=item.title, url=enlace, thumbnail=logo, plot=item.plot, folder=False))
            except:
                pass

    for logo, servidor, idioma, calidad, enlace, titulo in enlaces_descargar:
        servidor = servidor.replace("uploaded", "uploadedto")
        partes = enlace.split(" ")
        p = 1
        for enlace in partes:
            parte_titulo = titulo + " (%s/%s)" % (p, len(partes)) + " [" + servidor + "]"
            p += 1
            mostrar_server = True
            if config.get_setting("hidepremium"):
                mostrar_server = servertools.is_server_enabled(servidor)
            if mostrar_server:
                try:
                    devuelve = servertools.findvideosbyserver(enlace, servidor)
                    if devuelve:
                        enlace = devuelve[0][1]
                        itemlist.append(Item(fanart=item.fanart, channel=item.channel, action="play", server=servidor,
                                             title=parte_titulo, fulltitle=item.title, url=enlace, thumbnail=logo,
                                             plot=item.plot, folder=False))
                except:
                    pass
    return itemlist


# def episodios(item):
#     # Necesario para las actualizaciones automaticas
#     infoLabels= item.infoLabels
#     infoLabels['show']=item.show
#     return completo(Item(item.clone(url=item.url, extra="serie_add", infoLabels=infoLabels)))

def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    # logger.debug("data %s " % data)
    pattern = '<ul class="%s">(.*?)</ul>' % "pagination"  # item.pattern
    pagination = scrapertools.find_single_match(data, pattern)
    # logger.debug("pagination %s" % pagination)
    if pagination:
        pattern = '<li><a href="([^"]+)">Last<\/a>'
        full_url = scrapertools.find_single_match(pagination, pattern)
        url, last_page = scrapertools.find_single_match(full_url, r'(.*?\/pg\/)(\d+)')
        list_pages = []
        for x in range(1, int(last_page) + 1):
            list_pages.append("%s%s" % (url, x))
            # logger.debug("data %s%s" % (url, x))
            # logger.debug("list_pages %s" % list_pages)
    else:
        list_pages = [item.url]

    for index, page in enumerate(list_pages):
        logger.debug("Loading page %s/%s url=%s" % (index, len(list_pages), page))
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(page).data)
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

        pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"  # item.pattern
        data = scrapertools.get_match(data, pattern)
        # logger.debug("data %s " % data)

        pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img src="(?P<thumb>[^"]+)".*?<h2[^>]+>(?P<info>.*?)</h2>'
        matches = re.compile(pattern, re.DOTALL).findall(data)
        # logger.debug("data %s " % matches)

        for url, thumb, info in matches:
            # logger.debug("info %s" % info)

            if "<span" in info:  # new style
                pattern = ".*?[^>]+>.*?Temporada\s*(?P<season>\d+)\s*Capitulo(?:s)?\s*(?P<episode>\d+)" \
                          "(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)</span>\s*Calidad\s*<span[^>]+>" \
                          "[\[]\s*(?P<quality>.*?)\s*[\]]</span>"
                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]

                if match["episode2"]:
                    multi = True
                    title = "%s (%sx%s-%s) [%s][%s]" % (item.show, match["season"], str(match["episode"]).zfill(2),
                                                        str(match["episode2"]).zfill(2), match["lang"],
                                                        match["quality"])
                else:
                    multi = False
                    title = "%s (%sx%s) [%s][%s]" % (item.show, match["season"], str(match["episode"]).zfill(2),
                                                     match["lang"], match["quality"])

            else:  # old style
                pattern = "\[(?P<quality>.*?)\].*?\[Cap.(?P<season>\d+)(?P<episode>\d{2})(?:_(?P<season2>\d+)" \
                          "(?P<episode2>\d{2}))?.*?\].*?(?:\[(?P<lang>.*?)\])?"

                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]
                # logger.debug("data %s" % match)

                str_lang = ""
                if match["lang"] is not None:
                    str_lang = "[%s]" % match["lang"]

                if match["season2"] and match["episode2"]:
                    multi = True
                    if match["season"] == match["season2"]:

                        title = "%s (%sx%s-%s) %s[%s]" % (item.show, match["season"], match["episode"],
                                                          match["episode2"], str_lang, match["quality"])
                    else:
                        title = "%s (%sx%s-%sx%s) %s[%s]" % (item.show, match["season"], match["episode"],
                                                             match["season2"], match["episode2"], str_lang,
                                                             match["quality"])
                else:
                    title = "%s (%sx%s) %s[%s]" % (item.show, match["season"], match["episode"], str_lang,
                                                   match["quality"])
                    multi = False

            season = match['season']
            episode = match['episode']
            infoLabels['season']= season
            infoLabels['episode'] = episode
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                 quality=item.quality, multi=multi, contentSeason=season,
                                 contentEpisodeNumber=episode, infoLabels = infoLabels))

    # order list
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    if len(itemlist) > 1:
        return sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

    return itemlist

def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.post = "q=%s" % texto
        item.pattern = "buscar-list"
        itemlist = listado2(item)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
