# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb

host = 'http://torrentlocura.com/'

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
                         
    itemlist.append(Item(channel=item.channel, action="submenu", title="Documentales", url=host, extra="varios",
                         thumbnail=thumb_series))
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", url=host + "buscar", thumbnail=thumb_search))

    return itemlist

def submenu(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("'", "\"").replace("/series\"", "/series/\"")   #Compatibilidad con mispelisy.series.com

    #patron = '<li><a href="http://(?:www.)?torrentlocura.com/' + item.extra + '/">.*?<ul>(.*?)</ul>'
    patron = '<li><.*?href="'+item.url+item.extra + '/">.*?<ul.*?>(.*?)</ul>' #Filtrado por url, compatibilidad con mispelisy.series.com
    #logger.debug("patron: " + patron + " / data: " + data)
    if "pelisyseries.com" in host and item.extra == "varios":      #compatibilidad con mispelisy.series.com
        data = '<a href="http://torrentlocura.com/varios/" title="Documentales"><i class="icon-rocket"></i> Documentales</a>'
    else:
        data = scrapertools.get_match(data, patron)

    patron = '<.*?href="([^"]+)".*?>([^>]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, extra="pelilist"))
        itemlist.append(
            Item(channel=item.channel, action="alfabeto", title=title + " [A-Z]", url=url, extra="pelilist"))
            
    if item.extra == "peliculas":
        itemlist.append(Item(channel=item.channel, action="listado", title="Películas 4K", url=host + "peliculas-hd/4kultrahd/", extra="pelilist"))
        itemlist.append(
            Item(channel=item.channel, action="alfabeto", title="Películas 4K" + " [A-Z]", url=host + "peliculas-hd/4kultrahd/", extra="pelilist"))
            
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
    itemlist = []
    url_next_page =''

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
	#data = httptools.downloadpage(item.url).data
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
	
    logger.debug('item.modo: %s'%item.modo)
    logger.debug('item.extra: %s'%item.extra)

    if item.modo != 'next' or item.modo =='':
        logger.debug('item.title: %s'% item.title)
        patron = '<ul class="' + item.extra + '">(.*?)</ul>'
        fichas = scrapertools.get_match(data, patron)
        page_extra = item.extra
    else:
        fichas = data
        page_extra = item.extra

    patron = '<a href="([^"]+).*?'  # la url
    patron += 'title="([^"]+).*?'  # el titulo
    patron += '<img.*?src="([^"]+)"[^>]+>.*?'  # el thumbnail
    patron += '<h2.*?>(.*?)?<\/h2>'  # titulo alternativo
    patron += '<span>([^<].*?)?<'  # la calidad
    #logger.debug("patron: " + patron + " / fichas: " + fichas)
    matches = re.compile(patron, re.DOTALL).findall(fichas)
    #logger.debug('item.next_page: %s'%item.next_page)
    #logger.debug(matches)

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

    for scrapedurl, scrapedtitle, scrapedthumbnail, title_alt, calidad in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        action = "findvideos"
        extra = ""
        context = "movie"
        year = scrapertools.find_single_match(scrapedthumbnail, r'-(\d{4})')

        if ".com/serie" in url and "/miniseries" not in url:
            action = "episodios"
            extra = "serie"
            context = "tvshow"

            title = scrapertools.find_single_match(title, '([^-]+)')
            title = title.replace("Ver online", "", 1).replace("Descarga Serie HD", "", 1).replace("Ver en linea ", "",
                                                                                                   1).strip()

        else:
            title = title.replace("Descargar torrent ", "", 1).replace("Descarga Gratis ", "", 1).replace("Descargar Estreno ", "", 1).replace("Pelicula en latino ", "", 1).replace("Descargar Pelicula ", "", 1).replace("Descargar", "", 1).replace("Descarga", "", 1).replace("Bajar", "", 1).strip()
            if title.endswith("gratis"): title = title[:-7]
            if title.endswith("torrent"): title = title[:-8]
            if title.endswith("en HD"): title = title[:-6]
            
        if title == "":
            title = title_alt
        context_title = title_alt
        show = title_alt
        #if item.extra != "buscar-list":
        #    title = title + '[' + calidad + "]"

        #Este bucle parece obsoleto:
        #context = ""
        #context_title = scrapertools.find_single_match(url, "http://(?:www.)?torrentlocura.com/(.*?)/(.*?)/")
        #if context_title:
        #    try:
        #        context = context_title[0].replace("descargar-", "").replace("descargar", "").replace("pelicula", "movie").replace("series", "tvshow").replace("-hd", "").replace("-vo", "")
        #        context_title = context_title[1].replace("-", " ")
        #        if re.search('\d{4}', context_title[-4:]):
        #            context_title = context_title[:-4]
        #        elif re.search('\(\d{4}\)', context_title[-6:]):
        #            context_title = context_title[:-6]
        #
        #    except:
        #        context_title = show
        #        

        #logger.debug('contxt title: %s'%context_title)
        #logger.debug('year: %s' % year)
        #logger.debug('context: %s' % context)
        
        if not 'array' in title:
            itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                    extra = extra, show = context_title, contentTitle=context_title, contentType=context, quality=calidad,
                    context=["buscar_trailer"], infoLabels= {'year':year}))

        logger.debug("url: " + url + " / title: " + title + " / contxt title: " + context_title + " / context: " + context + " / calidad: " + calidad+ " / year: " + year)

    tmdb.set_infoLabels(itemlist, True)

    if url_next_page:
        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente",
                             url=url_next_page, next_page=next_page, folder=True,
                             text_color='yellow', text_bold=True, modo = modo, plot = extra,
                             extra = page_extra))
    return itemlist

def listado_busqueda(item):
    logger.info()
    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    
    list_chars = [["Ã±", "ñ"]]

    for el in list_chars:
        data = re.sub(r"%s" % el[0], el[1], data)

    try:
        get, post = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a class="current" href.*?'
                                                         '<a\s*href="([^"]+)"(?:\s*onClick=".*?\'([^"]+)\'.*?")')
    except:
        post = False

    if post:
        if "pg" in item.post:
            item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
        else:
            item.post += "&pg=%s" % post

    pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
    data = scrapertools.get_match(data, pattern)
    pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img.*?src="(?P<thumb>[^"]+)?".*?<h2.*?>(?P<title>.*?)?<\/h2>'
    matches = re.compile(pattern, re.DOTALL).findall(data)
    #logger.debug("patron: " + pattern)
    #logger.debug(matches)

    for url, thumb, title in matches:
        real_title = scrapertools.find_single_match(title, r'<strong.*?>(.*?)Temporada.*?<\/strong>')        #series
        if real_title == "":
            real_title = scrapertools.find_single_match(title, r'(.*?)\[.*?]')        #movies
        real_title = scrapertools.remove_htmltags(real_title).decode('iso-8859-1').encode('utf-8')
        real_title = scrapertools.htmlclean(real_title)
        calidad = scrapertools.find_single_match(title, r'.*?\s*Calidad.*?<span[^>]+>[\[]\s*(?P<quality>.*?)\s*[\]]<\/span>')       #series
        if calidad == "":
            calidad = scrapertools.find_single_match(title, r'..*?(\[.*?.*\])')          #movies
        year = scrapertools.find_single_match(thumb, r'-(\d{4})')
        
        # fix encoding for title
        title = scrapertools.htmlclean(title)
        title = title.replace("ï¿½", "ñ").replace("Temp", " Temp").replace("Esp", " Esp").replace("Ing", " Ing").replace("Eng", " Eng")
        title = re.sub(r'(Calidad.*?\])', '', title)
        
        if real_title == "":
            real_title = title
        if calidad == "":
            calidad = title
        context = "movie"

        # no mostramos lo que no sean videos
        if "juego/" in url:
            continue

        # Codigo para rescatar lo que se puede en pelisy.series.com de Series para la Videoteca.  la URL apunta al capítulo y no a la Serie.  Nombre de Serie frecuentemente en blanco. Se obtiene de Thumb, así como el id de la serie
        if ("/serie" in url or "-serie" in url) and "pelisyseries.com" in host:
            calidad_mps = "series/"
            if "seriehd" in url:
                calidad_mps = "series-hd/"
            if "serievo" in url:
                calidad_mps = "series-vo/"
            if "serie-vo" in url:
                calidad_mps = "series-vo/"
            
            real_title_mps = re.sub(r'.*?\/\d+_', '', thumb)
            real_title_mps = re.sub(r'\.\w+.*?', '', real_title_mps)
            
            if "/0_" not in thumb:
                serieid = scrapertools.find_single_match(thumb, r'.*?\/\w\/(?P<serieid>\d+).*?.*')
                if len(serieid) > 5:
                    serieid = ""
            else:
                serieid = ""
                
            url = host + calidad_mps + real_title_mps + "/" + serieid
            
            real_title_mps = real_title_mps.replace("-", " ")
            #logger.debug("url: " + url + " / title: " + title + " / real_title: " + real_title + " / real_title_mps: " + real_title_mps + " / calidad_mps : " + calidad_mps)
            real_title = real_title_mps
        
        show = real_title

        if ".com/serie" in url and "/miniseries" not in url:
            
            context = "tvshow"

            itemlist.append(Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumb, quality=calidad,
                show=show, extra="serie", context=["buscar_trailer"], contentType=context, contentTitle=real_title, contentSerieName=real_title, infoLabels= {'year':year}))
        else:

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb, quality=calidad,
                show=show, context=["buscar_trailer"], contentType=context, contentTitle=real_title, infoLabels= {'year':year}))
    
        logger.debug("url: " + url + " / title: " + title + " / real_title: " + real_title + " / show: " + show + " / calidad: " + calidad)
    
    tmdb.set_infoLabels(itemlist, True)
    
    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado_busqueda", title=">> Página siguiente",
                                   thumbnail=get_thumb("next.png")))

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    ## Cualquiera de las tres opciones son válidas
    # item.url = item.url.replace(".com/",".com/ver-online/")
    # item.url = item.url.replace(".com/",".com/descarga-directa/")
    item.url = item.url.replace(".com/", ".com/descarga-torrent/")

    # Descarga la página
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("$!", "#!").replace("'", "\"").replace("Ã±", "ñ").replace("//pictures", "/pictures")
    
    title = scrapertools.find_single_match(data, "<h1.*?<strong>([^<]+)<\/strong>.*?<\/h1>")	#corregido para adaptarlo a mispelisy.series.com
    title += scrapertools.find_single_match(data, "<h1.*?<strong>[^<]+<\/strong>([^<]+)<\/h1>")	#corregido para adaptarlo a mispelisy.series.com
    #caratula = scrapertools.find_single_match(data, '<div class="entry-left">.*?src="([^"]+)"')
    caratula = scrapertools.find_single_match(data, '<h1.*?<img.*?src="([^"]+)')

    patron = 'openTorrent.*?title=".*?class="btn-torrent">.*?function openTorrent.*?href = "(.*?)";'
    #logger.debug("patron: " + patron + " / data: " + data)
    # escraped torrent
    url = scrapertools.find_single_match(data, patron)

    if "Temp" in title and item.quality != "":		#scrapear información duplicada en Series
        title = re.sub(r'Temp.*?\[', '[', title)
        title = re.sub(r'\[Cap.*?\]', '', title)
        title = str(item.contentSeason) + "x" + str(item.contentEpisodeNumber) + " - " + item.contentTitle + ", " + title
    
    if url != "":		#Torrent
        itemlist.append(
            Item(channel=item.channel, action="play", server="torrent", title=title, quality=title, fulltitle=title,
                 url=url, thumbnail=caratula, plot=item.plot, folder=False))
    
	logger.debug("url: " + url + " / title: " + title + " / calidad: " + item.quality + " / context: " + str(item.context))

    # escraped ver vídeos, descargar vídeos un link, múltiples liks

    data = data.replace("http://tumejorserie.com/descargar/url_encript.php?link=", "(")
    data = re.sub(r'javascript:;" onClick="popup\("http:\/\/(?:www.)?torrentlocura.com\/\w{1,9}\/library\/include\/ajax\/get_modallinks.php\?links=', "", data)
    #logger.debug("matar %s" % data)

    # Antiguo sistema de scrapeo de servidores usado por Newpct1.  Como no funciona con torrent.locura, se sustituye por este más común
    #patron_descargar = '<div id="tab2"[^>]+>.*?</ul>'
    #patron_ver = '<div id="tab3"[^>]+>.*?</ul>'

    #match_ver = scrapertools.find_single_match(data, patron_ver)
    #match_descargar = scrapertools.find_single_match(data, patron_descargar)

    #patron = '<div class="box1"><img src="([^"]+)".*?'  # logo
    #patron += '<div class="box2">([^<]+)</div>'  # servidor
    #patron += '<div class="box3">([^<]+)</div>'  # idioma
    #patron += '<div class="box4">([^<]+)</div>'  # calidad
    #patron += '<div class="box5"><a href="([^"]+)".*?'  # enlace
    #patron += '<div class="box6">([^<]+)</div>'  # titulo

    #enlaces_ver = re.compile(patron, re.DOTALL).findall(match_ver)
    #enlaces_descargar = re.compile(patron, re.DOTALL).findall(match_descargar)

    # Nuevo sistema de scrapeo de servidores creado por Torrentlocula, compatible con otros clones de Newpct1
    patron = '<div class=\"box1\"[^<]+<img src=\"([^<]+)?" style[^<]+><\/div[^<]+<div class="box2">([^<]+)?<\/div[^<]+<div class="box3">([^<]+)?'
    patron += '<\/div[^<]+<div class="box4">([^<]+)?<\/div[^<]+<div class="box5"><a href=(.*?)? rel.*?'
    patron += '<\/div[^<]+<div class="box6">([^<]+)?<'
    #logger.debug("Patron: " + patron)

    enlaces_ver = re.compile(patron, re.DOTALL).findall(data)
    enlaces_descargar = enlaces_ver
    #logger.debug(enlaces_ver)
    
    if len(enlaces_ver) > 0:
        itemlist.append(item.clone(title="", action="", folder=False))
        itemlist.append(item.clone(title=" Enlaces Ver: ", action="", text_color="green", folder=False))

    for logo, servidor, idioma, calidad, enlace, titulo in enlaces_ver:
        if "Ver" in titulo:
            servidor = servidor.replace("streamin", "streaminto")
            titulo = title
            mostrar_server = True
            if config.get_setting("hidepremium"):
                mostrar_server = servertools.is_server_enabled(servidor)
            logger.debug("url: " + enlace + " / title: " + title + " / servidor: " + servidor + " / idioma: " + idioma)
            if mostrar_server:
                try:
                    devuelve = servertools.findvideosbyserver(enlace, servidor)
                    if devuelve:
                        enlace = devuelve[0][1]
                        itemlist.append(
                            Item(fanart=item.fanart, channel=item.channel, action="play", server=servidor, title=titulo, quality=titulo,
                                fulltitle=titulo, url=enlace, thumbnail=logo, plot=item.plot, folder=False))
                except:
                    pass

    if len(enlaces_descargar) > 0:
        itemlist.append(item.clone(title="", action="", folder=False))
        itemlist.append(item.clone(title=" Enlaces Descargar: ", action="", text_color="green", folder=False))

    for logo, servidor, idioma, calidad, enlace, titulo in enlaces_descargar:
        if "Ver" not in titulo:
            servidor = servidor.replace("uploaded", "uploadedto")
            partes = enlace.split(" ")
            titulo = "Partes "
            p = 1
            logger.debug("url: " + enlace + " / title: " + title + " / servidor: " + servidor + " / idioma: " + idioma)
            for enlace in partes:
                parte_titulo = titulo + " (%s/%s)" % (p, len(partes)) + " - " + title 
                p += 1
                mostrar_server = True
                if config.get_setting("hidepremium"):
                    mostrar_server = servertools.is_server_enabled(servidor)
                if mostrar_server:
                    try:
                        devuelve = servertools.findvideosbyserver(enlace, servidor)
                        if devuelve:
                            enlace = devuelve[0][1]
                            itemlist.append(Item(fanart=item.fanart, channel=item.channel, action="play", server=servidor, quality=parte_titulo,
                                             title=parte_titulo, fulltitle=parte_titulo, url=enlace, thumbnail=logo,
                                             plot=item.plot, folder=False))
                    except:
                        pass
                    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    calidad = item.quality
    
    pattern = '<ul class="%s">(.*?)</ul>' % "pagination"  # item.pattern
    pagination = scrapertools.find_single_match(data, pattern)
    if pagination:
        pattern = '<li><a href="([^"]+)">Last<\/a>'
        full_url = scrapertools.find_single_match(pagination, pattern)
        url, last_page = scrapertools.find_single_match(full_url, r'(.*?\/pg\/)(\d+)')
        list_pages = [item.url]
        for x in range(2, int(last_page) + 1):
            response = httptools.downloadpage('%s%s'% (url,x))
            if response.sucess:
                list_pages.append("%s%s" % (url, x))
    else:
        list_pages = [item.url]

    for index, page in enumerate(list_pages):
        logger.debug("Loading page %s/%s url=%s" % (index, len(list_pages), page))
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(page).data)
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        data = data.replace("chapters", "buscar-list")   #Compatibilidad con mispelisy.series.com
        pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"  # item.pattern
        data = scrapertools.get_match(data, pattern)
        #logger.debug("data: " + data)    

        if "pelisyseries.com" in host:
            pattern = '<li[^>]*><div class.*?src="(?P<thumb>[^"]+)?".*?<a class.*?href="(?P<url>[^"]+).*?<h3[^>]+>(?P<info>.*?)?<\/h3>.*?<\/li>'
        else:
            pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img.*?src="(?P<thumb>[^"]+)?".*?<h2[^>]+>(?P<info>.*?)?<\/h2>'
        matches = re.compile(pattern, re.DOTALL).findall(data)
        #logger.debug("patron: " + pattern)
        #logger.debug(matches)    
        
        season = "1"

        for url, thumb, info in matches:

            if "pelisyseries.com" in host:
                interm = url
                url = thumb
                thumb = interm

            if "<span" in info:  # new style
                pattern = ".*?[^>]+>.*?Temporada\s*(?P<season>\d+)?.*?Capitulo(?:s)?\s*(?P<episode>\d+)?" \
                          "(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)?<\/span>\s*Calidad\s*<span[^>]+>" \
                          "[\[]\s*(?P<quality>.*?)?\s*[\]]<\/span>"
                if "Especial" in info: # Capitulos Especiales
                    pattern = ".*?[^>]+>.*?Temporada.*?\[.*?(?P<season>\d+).*?\].*?Capitulo.*?\[\s*(?P<episode>\d+).*?\]?(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)?<\/span>\s*Calidad\s*<span[^>]+>[\[]\s*(?P<quality>.*?)?\s*[\]]<\/span>"
                logger.debug("patron: " + pattern)
                logger.debug(info)
                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]

                if match['season'] is None: match['season'] = season
                if match['episode'] is None: match['episode'] = "0"
                if match['quality']: item.quality = match['quality']

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
                pattern = "\[(?P<quality>.*?)\].*?\[Cap.(?P<season>\d+).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)" \
                          "(?P<episode2>\d{2}))?.*?\].*?(?:\[(?P<lang>.*?)\])?"
                logger.debug("patron: " + pattern)
                logger.debug(info)
                r = re.compile(pattern)
                match = [m.groupdict() for m in r.finditer(info)][0]
                #logger.debug("data %s" % match)
                
                #if match['season'] is "": match['season'] = season
                #if match['episode'] is "": match['episode'] = "0"
                #logger.debug(match)

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
            logger.debug("title: " + title + " / url: " + url + " / calidad: " + item.quality + " / multi: " + str(multi) + " / Season: " + str(season) + " / EpisodeNumber: " + str(episode))
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                                 quality=item.quality, multi=multi, contentSeason=season,
                                 contentEpisodeNumber=episode, infoLabels = infoLabels))
    # order list
    #tmdb.set_infoLabels(itemlist, True)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library", extra="episodios", quality=calidad))

    return itemlist

def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.post = "q=%s" % texto
        item.pattern = "buscar-list"
        itemlist = listado_busqueda(item)

        return itemlist

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
        item.extra = 'pelilist'
        if categoria == 'torrent':
            item.url = host+'peliculas/'

            itemlist = listado(item)
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()
            item.url = host+'series/'
            itemlist.extend(listado(item))
            if itemlist[-1].title == ">> Página siguiente":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
