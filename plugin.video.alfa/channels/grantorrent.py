# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools

host = "https://grantorrent.net/"

dict_url_seasons = dict()
__modo_grafico__ = config.get_setting('modo_grafico', 'grantorrent')
modo_serie_temp = config.get_setting('seleccionar_serie_temporada', 'grantorrent')
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', 'grantorrent')


def mainlist(item):
    logger.info()

    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_buscar = get_thumb("search.png")
    thumb_settings = get_thumb("setting_0.png")

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host, extra="peliculas", thumbnail=thumb_pelis))

    #Buscar películas
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar en Películas >>", url=host, extra="peliculas", thumbnail=thumb_buscar))
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series", thumbnail=thumb_series))

    #Buscar series
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar en Series >>", url=host + "series/", extra="series", thumbnail=thumb_buscar))
    
    itemlist.append(
        Item(channel=item.channel, action="", title="[COLOR yellow]Configuración del Canal:[/COLOR]", url="", thumbnail=thumb_settings))
    itemlist.append(
        Item(channel=item.channel, action="settingCanal", title="Opciones de Videoteca y TMDB", url="", thumbnail=thumb_settings))

    return itemlist

    
def settingCanal(item):
    from platformcode import platformtools
    return platformtools.show_channel_settings()


def submenu(item):
    logger.info()
    itemlist = []
    
    thumb_buscar = get_thumb("search.png")
    
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist     #Algo no funciona, pintamos lo que tenemos
    
    if item.extra == "peliculas":
        patron = '<li class="navigation-top">.*?<a href="(.*?)".*?class="nav"> (.*?)\s?<\/a><\/li>'     
        matches = re.compile(patron, re.DOTALL).findall(data)
        
        itemlist.append(item.clone(action="listado", title="Novedades", url=host))       #Menú principal películas
    
        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('utf8').encode('utf8').strip()
        
            if not "películas" in scrapedtitle.lower():    #Evita la entrada de ayudas y demás
                continue

            itemlist.append(item.clone(action="listado", title=scrapedtitle, url=scrapedurl))       #Menú películas

    else:                  #Tratamos Series
        patron = '<li class="navigation-top-dcha">.*?<a href="(.*?)".*?class="series"> (.*?)\s?<\/a><\/li>'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('utf8').encode('utf8').strip()

            itemlist.append(item.clone(action="listado", title=scrapedtitle, url=scrapedurl))       #Menú series

    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    cnt_tot = 40            # Poner el num. máximo de items por página
    cnt_title = 0           # Contador de líneas insertadas en Itemlist
    result_mode = config.get_setting("result_mode", channel="search")       # Búsquedas globales: listado completo o no
    
    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []        # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista = item.title_lista      # Se usa la lista de páginas anteriores en Item
    title_lista_alt = []    # Creamos otra lista para esta pasada
    for url in title_lista:
        title_lista_alt += [url]        #hacemos una copia no vinculada de title_lista
    matches = []
    cnt_next = 0            #num de página próxima
    cnt_top = 10            #max. num de páginas web a leer antes de pintar
    total_pag = 1
    post_num = 1            #num pagina actual
    
    #Máximo num. de líneas permitidas por TMDB (40). Máx de 5 páginas por Itemlist para no degradar el rendimiento.  
    #Si itemlist sigue vacío después de leer 5 páginas, se pueden llegar a leer hasta 10 páginas para encontrar algo

    while cnt_title <= cnt_tot and cnt_next < cnt_top:
        # Descarga la página
        try:
            if not item.post:
                item.post = item.url
            video_section = ''
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.post).data)
            video_section = scrapertools.find_single_match(data, '<div class="contenedor-home">(.*?</div>)</div></div>')
        except:
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + video_section)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        cnt_next += 1
        if not data:        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + video_section)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Obtiene la dirección de la próxima página, si la hay
        try:
            patron = '<div class="nav-links">.*?<a class="next page.*?href="(.*?)"'
            next_page = scrapertools.find_single_match(data, patron)                        #url próxima página    
            post = scrapertools.find_single_match(next_page, '\/page\/(\d+)\/')             #número próxima página
            if next_page:                                                                   #Hay próxima página?
                patron = '<div class="nav-links">.*?'
                patron += "href='.*?\/page\/\d+\/.*?'>(\d+)<\/a>\s?"
                patron += '<a class="next page-numbers"'
                total_pag = scrapertools.find_single_match(data, patron)                    #guarda el núm total de páginas
            
        except:
            post = False
            cnt_next = 99       #No hay más páginas.  Salir del bucle después de procesar ésta

        if post:                #puntero a la siguiente página.  Cada página de la web tiene 30 entradas
            if "page/" in item.post:
                item.post = re.sub(r"page\/\d+\/", "page/%s/" % post, item.post)
            else:
                if "/series" in item.post:
                    item.post = re.sub(r"\/series\/", "/series/page/%s/" % post, item.post)
                elif "/categoria" in item.post:
                    item.post = re.sub(r"\/$", "/page/%s/" % post, item.post)
                else:
                    item.post = re.sub(r"\.net\/", ".net/page/%s/" % post, item.post)
                
            post_num = int(post) - 1      #Guardo página actual
        else:
            post = False
            cnt_next = 99       #No hay más páginas.  Salir del bucle después de procesar ésta

        # Preparamos un patron que pretende recoger todos los datos significativos del video
        patron = '<a href="(?P<url>[^"]+)"><img.*?src="(?P<thumb>[^"]+)".*?'
        if "categoria" in item.url or item.media == "search":     #Patron distinto para páginas de Categorías o Búsquedas
            patron += 'class="attachment-(?P<quality>.*?)-(?P<lang>[^\s]+)\s.*?'
        else:
            patron += 'class="bloque-superior">\s*(?P<quality>.*?)\s*<div class="imagen-idioma">\s*<img src=".*?icono_(?P<lang>[^\.]+).*?'
        patron += '<div class="bloque-inferior">\s*(?P<title>.*?)\s*<\/div>\s?<div class="bloque-date">\s*(?P<date>.*?)\s*<\/div>'

        matches_alt = re.compile(patron, re.DOTALL).findall(video_section)
        if not matches_alt and not '<div class="titulo-load-core">0 resultados' in data:       #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Ahora se hace una simulación para saber cuantas líneas podemos albergar en este Itemlist.
        #Se controlará cuantas páginas web se tienen que leer para rellenar la lista, sin pasarse

        title_lista_alt_for = []         #usamos está lista de urls para el FOR, luego la integramos en la del WHILE
        for scrapedurl, scrapedthumb, quality, lang, scrapedtitle, date in matches_alt:
            #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
            #Se analiza si la url de la serie o pelicula ya se ha listado antes.  Si es así, esa entrada se ignora
            #Cuando llega al num. máximo de entradas por página, la pinta y guarda los contadores y la lista de series
            
            scrapedurl_alt = scrapedurl
            if modo_serie_temp == 1:        #si está en modo Serie agrupamos todos los episodios en una línea
                scrapedurl_alt = re.sub(r'-temporada.*?-\d+.*', '/', scrapedurl_alt)
                scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '/', scrapedurl_alt)             #quita los datos de Temporada/episodio
            else:                           #si es modo Temporada, se agrupan a una línea por Temporada
                num_temp = scrapertools.find_single_match(scrapedurl_alt, '-?(\d+)x')    #captura num de Temporada
                scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '-temporada-%s-completa' % num_temp, scrapedurl_alt) #epis. a Temporada

            if scrapedurl_alt in title_lista_alt or scrapedurl_alt in title_lista_alt_for:  # si ya se ha tratado, pasamos al siguiente item
                continue
            title_lista_alt_for += [scrapedurl_alt]
            cnt_title += 1                      # Sería una línea real más para Itemlist
            
            #Control de página
            if cnt_title > cnt_tot*0.65:        #si se acerca al máximo num. de lineas por pagina, tratamos lo que tenemos
                cnt_next = 99                   #Casi completo, no sobrepasar con la siguiente página
                if cnt_title > cnt_tot:
                    cnt_title = 99              #Sobrepasado el máximo.  Ignoro página actual
                    #Restauro puntero "next" a la página actual, para releearla en otra pasada, y salgo
                    item.post = re.sub(r"page\/\d+\/", "page/%s/" % post_num, item.post)
                    break

            if cnt_title > 0:        #Si se ha llegado a las 5 páginas tratadas, pintamos.  Si no continuamos un poco
                if cnt_next >= cnt_top*0.5:
                    cnt_next = 99

        if cnt_title <= cnt_tot:
            matches.extend(matches_alt)         #Acumulamos las entradas a tratar. Si nos hemos pasado ignoro última página
            title_lista_alt.extend(title_lista_alt_for)
    
        #logger.debug("BUCLE: " + item.post + " / post: " +  str(post) + " / post_num: " + str(post_num) + " / cnt_next: " + str(cnt_next) + " / " + str(title_lista_alt))
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(video_section)     
    
    cnt_title = 0
    for scrapedurl, scrapedthumb, quality, lang, scrapedtitle, date in matches:
        
        #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
        #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
        #El control de página ya se ha realizado más arriba

        scrapedurl_alt = scrapedurl
        if modo_serie_temp == 1:        #si está en modo Serie agrupamos todos los episodios en una línea
            scrapedurl_alt = re.sub(r'-temporada.*?-\d+.*', '/', scrapedurl_alt)
            scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '/', scrapedurl_alt)             #quita los datos de Temporada/episodio
        else:                           #si es modo Temporada, se agrupan a una línea por Temporada
            num_temp = scrapertools.find_single_match(scrapedurl_alt, '-?(\d+)x')    #captura num de Temporada
            scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '-temporada-%s-completa' % num_temp, scrapedurl_alt) #epis. a Temporada

        if scrapedurl_alt in title_lista:       # si ya se ha tratado, pasamos al siguiente item
            continue                            # solo guardamos la url para series y docus
        title_lista += [scrapedurl_alt]
        cnt_title += 1                          # Sería una línea real más para Itemlist

        item_local = item.clone()       #Creamos copia de Item para trabajar y limpiamos campos innecesarios
        if item_local.media:            #Viene de Búsquedas
            del item_local.media
        if item_local.title_lista:
            del item_local.title_lista
        item_local.post = True
        del item_local.post
        if item_local.category:
            del item_local.category
        item_local.context = "['buscar_trailer']"
        
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').encode('utf8').strip()      #Decode-encode utf8
        title = re.sub(r"\s{2}", " ", title)
        title = title.replace("&#8217;", "'").replace("\xc3\x97", "x")
        item_local.url = urlparse.urljoin(host, scrapedurl)

        if "categoria" in item.url:                 #En páginas de Categorias no viene ni la calidad ni el idioma
            item_local.quality = scrapertools.find_single_match(item.url, r'\/categoria\/(.*?)\/')
            if "4k" in item_local.quality.lower():
                item_local.quality = "4K HDR"       #Maquillamos un poco la calidad
            lang = ''                               #Ignoramos el idioma
        elif not "post" in quality:
            item_local.quality = quality            #Salvamos la calidad en el resto de páginas
        
        item_local.language = []                    #Verificamos el idioma por si encontramos algo
        if "latino" in lang.lower() or "latino" in item.url or "latino" in title.lower():
            item_local.language += ["LAT"]
        if "ingles" in lang.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
            if "VOSE" in lang.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
                item_local.language += ["VOS"]
            else:
                item_local.language += ["VO"]
        if "dual" in lang.lower() or "dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
            
        #Limpiamos el título de la basuna innecesaria
        title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Reparado)", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("(Latino)", "").replace("Latino", "")
        title = title.replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("(HDRip)", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "")
            
        if item_local.extra == "peliculas":                 #preparamos Item para películas
            if "/serie" in scrapedurl or "/serie" in item.url:
                continue
            item_local.contentType = "movie"
            item_local.action = "findvideos"
            title = scrapertools.htmlclean(title)           #Quitamos html restante
            item_local.contentTitle = title.strip()
        else:                                               #preparamos Item para series
            if not "/serie" in scrapedurl and not "/serie" in item.url:
                continue
            if modo_serie_temp == 1:                        #si está en modo Serie
                item_local.contentType = "tvshow"
                item_local.extra = "tvshow"
            else:                                           #si no, en modo temporada
                item_local.contentType = "season"
                item_local.extra = "season"
            item_local.action = "episodios"
            title = re.sub(r'[t|T]emp.*?\d+.*', '', title)  #Limpiamos temporadas completas, solo queremos la serie entera
            title = re.sub(r'\d?\d?&#.*', '', title)        #Limpiamos temporada y episodio
            title = re.sub(r'\d+[x|×]\d+.*', '', title)     #Limpiamos temporada y episodio
            title = scrapertools.htmlclean(title)           #Quitamos html restante
            item_local.contentSerieName = title.strip()

        item_local.title = title.strip()                    #Salvamos el título
        item_local.infoLabels['year'] = "-"                 #Reseteamos el año para que TMDB nos lo de
        
        #Agrega el item local a la lista itemlist
        itemlist.append(item_local.clone())

    if not item.category and result_mode == 0:   #Si este campo no existe, viene de la primera pasada de una búsqueda global
        return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorrar tiempo
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    #Gestionamos el paginador
    patron = '<div class="nav-links">.*?<a class="next page.*?href="(.*?)"'
    next_page = scrapertools.find_single_match(data, patron)                        #url próxima página    
    #next_page_num = scrapertools.find_single_match(next_page, '\/page\/(\d+)\/')    #número próxima página
    if next_page:                                                                   #Hay próxima página?
        patron = '<div class="nav-links">.*?'
        patron += "href='.*?\/page\/\d+\/.*?'>(\d+)<\/a>\s?"
        patron += '<a class="next page-numbers"'
        last_page = scrapertools.find_single_match(data, patron)                    #cargamos la última página
        
        if last_page:                                                               #Sabemos la ultima página?
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s de %s' % (post_num, last_page)
        else:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s' % post_num
        
        itemlist.append(item.clone(action="listado", title=title, url=next_page, thumbnail=get_thumb("next.png"), title_lista=title_lista))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    #Bajamos los datos de la página
    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    data = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')     #Seleccionamos la zona de links
    
    patron = '\/icono_.*?png" title="(?P<lang>.*?)?" [^>]+><\/td><td>(?P<quality>.*?)?<?\/td>.*?<td>(?P<size>.*?)?<\/td><td><a class="link" href="(?P<url>.*?)?"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                             #error
        logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
            
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora recorremos todos los links por calidades
    for lang, quality, size, scrapedurl in matches:
        temp_epi = ''
        if item.contentType == "episode":       #En Series los campos están en otro orden.  No hay size, en su lugar sxe
            temp_epi = quality
            quality = size
            size = ''
            contentSeason = ''
            contentEpisodeNumber = ''
            try:                                #obtenemos la temporada y episodio de la página y la comparamos con Item
                if "temporada" in temp_epi.lower():
                    contentSeason = scrapertools.find_single_match(temp_epi, r'[t|T]emporada.*?(\d+)')
                    contentSeason = int(contentSeason)
                    contentEpisodeNumber = 1
                else:
                    if scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)'):
                        contentSeason, contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)')
                    if not contentEpisodeNumber:
                        contentSeason = scrapertools.find_single_match(item.url, r'temporadas?-(\d+)')  #num de temporada
                        if not contentEpisodeNumber:
                            contentSeason = 1
                        contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)-')
                        if not contentEpisodeNumber:
                            contentEpisodeNumber = 1
                    contentSeason = int(contentSeason)
                    contentEpisodeNumber = int(contentEpisodeNumber)
            except:
                logger.error("ERROR 03: FINDVIDEOS: Error en número de Episodio: " + temp_epi + " / " + str(contentSeason) + " / " + str(contentEpisodeNumber))
                continue                        
            if (contentSeason != item.contentSeason or contentEpisodeNumber != item.contentEpisodeNumber) and item.contentEpisodeNumber != 0:
                continue                        #si no son iguales, lo ignoramos

        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        
        #Verificamos el idioma por si encontramos algo
        if not item_local.language:
            if "latino" in lang.lower() or "latino" in scrapedurl:
                item_local.language += ["LAT"]
            if "ingles" in lang.lower() or "ingles" in scrapedurl or "vose" in scrapedurl or "vose" in scrapedurl:
                if "VOSE" in lang.lower() or "sub" in lang.lower() or "vose" in scrapedurl or "vose" in scrapedurl:
                    item_local.language += ["VOS"]
                else:
                    item_local.language += ["VO"]
            if "dual" in lang.lower() or "dual" in scrapedurl:
                item_local.language[0:0] = ["DUAL"]

        #Tratamos la calidad y tamaño de cada link
        if quality:
            item_local.quality = quality
        if "temporada" in temp_epi.lower():
            item_local.quality = '%s [Temporada]' % item_local.quality
        #if size and item_local.contentType != "episode":
        if size:
            size = size.replace(".", ",").replace("B,", " B").replace("b,", " b")
            item_local.quality = '%s [%s]' % (item_local.quality, size)

        #Salvamos la url del .torrent
        if scrapedurl:
            item_local.url = scrapedurl
            item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))        #Preparamos título de Torrent
            item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip() #Quitamos etiquetas vacías
            item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title).strip() #Quitamos colores vacíos
            item_local.alive = "??"                 #Calidad del link sin verificar
            item_local.action = "play"              #Visualizar vídeo
            item_local.server = "torrent"           #Seridor Torrent
        
            itemlist.append(item_local.clone())     #Pintar pantalla
            
        #logger.debug("TORRENT: " + item_local.url + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality)
        #logger.debug(item_local)

    return itemlist

    
def episodios(item):
    logger.info()
    itemlist = []
    temp_actual_num = 0
    temp_actual = ''
    temp_previous = ''
    temp_next = ''
    item.extra = "episodios"
    
    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    if not item.infoLabels['tmdb_id']:
        tmdb.set_infoLabels(item, True)

    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)    #Cargamos los datos de la página

        patron_actual = '<link rel="canonical" href="(.*?)"'                            #Patrón de url temporada actual
        patron_actual_num = 'temporadas?-(\d+)'                                         #Patrón de núm. de temporada actual
        patron_previous = '<a class="temp-anterior" href="(.*?)">'                      #Patrón de url temporada anterior
        patron_next = '<a class="temp-siguiente" href="(.*?)">'                         #Patrón de url temporada próxima
        temp_actual = scrapertools.find_single_match(data, patron_actual)               #url actual de la temporada
        item.url = temp_actual                              #Salvamos la temporada actual como primera para la Videoteca
        temp_next = scrapertools.find_single_match(data, patron_next)                   #url de temporada siguiente
        temp_previous = scrapertools.find_single_match(data, patron_previous)           #url de temporada anterior
        temp_advance = 'back'                                           #por defecto procesamos temporadas hacia atrás
        temp_actual_num = scrapertools.find_single_match(temp_actual, patron_actual_num)    #num de la temporada actual
        if not temp_actual_num:                                                         #Si el formato es extraño...
            temp_actual_num = 1                                                         #... ponemos 1 como valor
        temp_actual_num = int(temp_actual_num)
        contentSeason = temp_actual_num                                                 #Salvamos el núm de temporada actual
        temp_previous_num = scrapertools.find_single_match(temp_previous, patron_actual_num)    #num de la temporada previa
        temp_previous_num = int(temp_actual_num)
    except:                                                                             #Algún error de proceso, salimos
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    max_temp = 1
    if item.library_playcounts:         #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        max_temp = int(max(matches))
    
    if not item.library_playcounts:     #no viene de Videoteca, se ponen valores de configuración o de la pasada anterior
        if not item.contentType:
            if modo_serie_temp == 0:
                item.contentType = "season"
            else:
                item.contentType = "tvshow"
                if item.contentSeason:
                    del item.infoLabels['season']

    elif max_temp < item.infoLabels["number_of_seasons"]:       #Si tenemos en .nfo menos temporadas, Temp.
        item.contentType = "season"

    elif max_temp >= item.infoLabels["number_of_seasons"]:      #Si tenemos en .nfo igaual o más temporadas, investigar
        cnt_s = 0
        for s in item.library_playcounts:       #Ver cuántas Temporadas hay en Videoteca
            if "season" in s:
                cnt_s += 1

        if cnt_s > 1:                           #hay más de 1 temporada en Videoteca, es Serie?
            if temp_actual_num > 1:             #Temp. actual > 1, parece Temporada
                s = 1
                while s <= item.infoLabels["number_of_seasons"]:                #Buscamos la primera Temporada de Videoteca
                    if item.library_playcounts.has_key('season %d' % s):        #Buscamos si la Temporada 1 existe
                        if item.library_playcounts["season %d" % s] < temp_actual_num:    #Si menor que actual, es Temp.
                            item.contentType = "season"
                        else:
                            item.contentType = "tvshow"     #No es Temporada 1, pero es más baja que la actual.  Es Serie
                        break
                    s += 1
            else:                               #Sí, es Serie
                item.contentType = "tvshow"

        else:                                   #Solo hay una temporada en la Videoteca
            if temp_actual_num > 1:             #es Temporada la actual?
                if item.contentSeason:
                    item.contentType = "season" #Si está informado el num de Temp. se creó como Temporada
                else:
                    item.contentType = "tvshow" #Si no, es Serie que no tiene Temp. 1
            else:                               #Si es Temp. 1, se procesa según el valor de configuración    
                if modo_serie_temp == 0:        #Es Temporada
                    item.contentType = "season"
                else:                           #Es Serie
                    item.contentType = "tvshow"
    else:
        item.contentType = "list"

    temp_lista = []
    temp_bucle = 0
    temp_next_alt = ''
    while temp_actual != '':                            #revisamos las temporadas hasta el final
        if not data:                                    #si no hay datos, descargamos. Si los hay de loop anterior, los usamos
            try:
                data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(temp_actual).data)
                
                #Controla que no haya un bucle en la cadena de links entre temporadas
                if scrapertools.find_single_match(temp_actual, patron_actual_num) in temp_lista:
                    temp_bucle += 1
                    if temp_bucle > 5:      #Si ha pasado por aquí más de 5 veces es que algo anda mal
                        logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                        itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                        data = ''
                        return itemlist     #Algo no funciona con los links, pintamos lo que tenemos
                    if temp_advance == "back":     #Se salta una temporada hacia atrás
                        logger.error("ERROR 05: EPISODIOS: Temporada duplicada.  Link BACK erroneo: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / Bucle: " + str(temp_bucle) + " / DATA: " + data)
                        temp_actual = scrapertools.find_single_match(data, patron_previous) #url de temporada anterior
                        data = ''
                        continue        #volvemos a leer página con la url de la anterior
                    if temp_advance == "forw":     #Se salta una temporada hacia adelante
                        logger.error("ERROR 05: EPISODIOS: Temporada duplicada.  Link FORW erroneo: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / Bucle: " + str(temp_bucle) + " / DATA: " + data)
                        temp_actual = scrapertools.find_single_match(data, patron_next)     #url de temporada siguiente
                        data = ''
                        continue        #volvemos a leer página con la url de la siguiente
                
                #Comprobamos si se ha saltado una Temporada
                if temp_advance == "back":                          #Avanza marcha atrás?
                    temp_num_alt = int(scrapertools.find_single_match(temp_actual, patron_actual_num))  #nuevo num. Temp.
                    if temp_num_alt < temp_actual_num - 1:          #Hay un salto a la Temp. anterior, o más?
                        temp_next_alt = scrapertools.find_single_match(data, patron_next)   #url de temporada siguiente
                        temp_num_alt = int(scrapertools.find_single_match(temp_next_alt, patron_actual_num))
                        #Localizamos la Temp. siguiente y nos aseguramos que no está procesada
                        if temp_num_alt <= temp_actual_num - 1 and temp_num_alt not in temp_lista:
                            temp_actual_alt = temp_next_alt         #url actual de la temporada = url de la siguiente
                            temp_previous_alt = temp_actual         #url temporada anterior = url de la actual anterior
                            logger.error("ERROR 06: EPISODIOS: Se ha saltado una Temporda: Actual: " + temp_actual + " / Actual ALT: " + temp_actual_alt + " / Previa: " + temp_previous  + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Bucle: " + str(temp_bucle))
                            temp_actual = temp_actual_alt           #url actual de la temporada = url de la siguiente
                            temp_bucle += 1
                            if temp_bucle > 5:                      #Evitamos loops infinitos
                                logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                                data = ''
                                itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                                return itemlist     #Algo no funciona con los links, pintamos lo que tenemos
                            data = ''
                            continue                #volvemos a leer página con la url de la siguiente
                
                #Comprobamos si se ha saltado una Temporada
                if temp_advance == "forw":                          #Avanza marcha adelante?
                    temp_num_alt = int(scrapertools.find_single_match(temp_actual, patron_actual_num))  #nuevo num. Temp.
                    if temp_num_alt > temp_actual_num + 1:          #Hay un salto a la Temp. siguiente, o más?
                        temp_previous_alt = scrapertools.find_single_match(data, patron_previous)   #url de temporada anterior
                        temp_num_alt = int(scrapertools.find_single_match(temp_previous_alt, patron_actual_num))
                        #Localizamos la Temp. anterior y nos aseguramos que no está procesada
                        if temp_num_alt >= temp_actual_num + 1 and temp_num_alt not in temp_lista:
                            temp_actual_alt = temp_previous_alt     #url actual de la temporada = url de la anterior
                            temp_next_alt = temp_actual             #url temporada siguiente = url de la actual anterior
                            logger.error("ERROR 06: EPISODIOS: Se ha saltado una Temporda: Actual: " + temp_actual + " / Actual ALT: " + temp_actual_alt + " / Previa: " + temp_previous  + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Bucle: " + str(temp_bucle))
                            temp_actual = temp_actual_alt           #url actual de la temporada = url de la siguiente
                            temp_bucle += 1
                            if temp_bucle > 5:                      #Evitamos loops infinitos
                                logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                                data = ''
                                itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                                return itemlist     #Algo no funciona con los links, pintamos lo que tenemos
                            data = ''
                            continue                #volvemos a leer página con la url de la siguiente

                temp_actual_num = scrapertools.find_single_match(temp_actual, patron_actual_num)    #num de la temporada actual
                temp_actual_num = int(temp_actual_num)
                temp_previous = scrapertools.find_single_match(data, patron_previous)           #url de temporada anterior
                if temp_advance == 'forw':  #si estamos con temporadas previas, dejamos la url de la siguiente temporada inicial
                    temp_next = scrapertools.find_single_match(data, patron_next)               #url de temporada siguiente
                    temp_previous = ''                  #ya están procesadas las temporadas previas, no volvemos a hacerlo
            
            except:                                     #Error al leer o procesar la página actual? Salimos
                logger.error("ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        if item.contentType == "season":
            temp_advance = ''                           #Es la única temporada
            if temp_next and item.library_playcounts:   #Permitimos en actualización de Videoteca añadir nuevas temporadas
                temp_advance = 'forw'                   #Si hay nueva temporada, pasamos a esa como actual
            temp_previous = ''                          #lo limpiamos, por control
            item.url = temp_actual                      #Salvamos la temporada actual como primera para la Videoteca
            contentSeason = temp_actual_num             #Salvamos el núm de temporada
        elif temp_previous:                             #Para Series, vamos retrocediendo y procesando temporadas
            if temp_advance == 'back':
                if not modo_ultima_temp:                #Actualiza la Serie entera en la Videoteca?
                    item.url = temp_previous            #Salvamos la temporada previa como primera para la Videoteca
                contentSeason = temp_previous_num       #Salvamos en núm de temporada
            temp_advance = 'back'                       #hay temporadas anteriores, iremos marcha atrás procesándolas
        elif temp_next:
            if temp_advance == 'back':                  #Esta es la primera temporada disponible
                if not modo_ultima_temp:                #Actualiza la Serie entera en la Videoteca?
                    item.url = temp_actual              #Salvamos la temporada actual como primera para la Videoteca
                contentSeason = temp_actual_num         #Salvamos en núm de temporada
            else:
                if modo_ultima_temp and not item.library_playcounts:        #Actualiza la última Temporada en la Videoteca?
                    item.url = temp_next                #Salvamos la temporada siguiente como primera para la Videoteca
            temp_advance = 'forw'                       #No hay temporadas anteriores, pero sí posteriores.  Las procesamos
        else:
            temp_advance = ''                           #lo limpiamos, por control
        
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        data = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')     #Seleccionamos la zona de links
        
        patron = '\/icono_.*?png" title="(?P<lang>.*?)?" [^>]+><\/td><td>(?P<temp_epi>.*?)?<?\/td>.*?<td>(?P<quality>.*?)?<\/td><td><a class="link" href="(?P<url>.*?)?"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:                             #error
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Ahora recorremos todos los links por calidades
        for lang, temp_epi, quality, scrapedurl in matches:     #la URL apunta ya al .torrent. nos quedamos con la URL de temporada
            #Generamos una copia de Item para trabajar sobre ella y la rellenamos.  Borramos etiquetas innecesarias
            item_local = item.clone()
            if item_local.category:
                del item_local.category
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            item_local.context = "['buscar_trailer']"
            item_local.url = temp_actual                        #salvamos la URL de la temporada
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            #item_local.contentSeason = temp_actual_num          #salvamos num de temporada
            item_local.title = re.sub(r'\[COLOR limegreen\]\[.*?\]\[\/COLOR\]', '', item_local.title)
            if item_local.library_playcounts:
                del item_local.library_playcounts
            if item_local.library_urls:
                del item_local.library_urls
            if item_local.path:
                del item_local.path
            if item_local.update_last:
                del item_local.update_last
            if item_local.update_next:
                del item_local.update_next

            #Verificamos el idioma por si encontramos algo
            if not item_local.language:
                if "latino" in lang.lower() or "latino" in scrapedurl:
                    item_local.language += ["LAT"]
                if "ingles" in lang.lower() or "ingles" in scrapedurl or "vose" in scrapedurl or "vose" in scrapedurl:
                    if "VOSE" in lang.lower() or "sub" in lang.lower() or "vose" in scrapedurl or "vose" in scrapedurl:
                        item_local.language += ["VOS"]
                    else:
                        item_local.language += ["VO"]
                if "dual" in lang.lower() or "dual" in scrapedurl:
                    item_local.language[0:0] = ["DUAL"]
            
            try:
                if "temporada" in temp_epi.lower() or "completa" in temp_epi.lower():     #si es una temporada en vez de un episodio, lo aceptamos como episodio 1
                    item_local.contentSeason = scrapertools.find_single_match(temp_epi, r'[t|T]emporada.*?(\d+)')
                    if not item_local.contentSeason:
                        item_local.contentSeason = temp_actual_num
                    item_local.contentSeason = int(item_local.contentSeason)
                    item_local.contentEpisodeNumber = 1
                else:                                   #si es un episodio lo guardamos
                    if scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)'):
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)')
                    if not item_local.contentSeason:
                        item_local.contentSeason = temp_actual_num
                    item_local.contentSeason = int(item_local.contentSeason)
                    #item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'\d+&#.*?;(\d+)')
                    if not item_local.contentEpisodeNumber:
                        item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)-')
                        if not item_local.contentEpisodeNumber:
                            item_local.contentEpisodeNumber = 0
                    item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
            except:
                logger.error("ERROR 07: EPISODIOS: Error en número de Temporada o Episodio: " + temp_epi)
                continue                                #si da un error pasamos del episodio
                
            if item_local.contentSeason != temp_actual_num:     #A veces es diferente el num de Temp. de la URL y de
                temp_actual_num = item_local.contentSeason      #los episodios. Anatomia de Grey Temp. 14

            if "-" in temp_epi:                         #episodios múltiples
                episode2 = scrapertools.find_single_match(temp_epi, r'-(\d+)')
                item_local.title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(episode2).zfill(2))                  #Creamos un título con el rango de episodios
            elif "temporada" in temp_epi.lower() or "completa" in temp_epi.lower():       #Temporada completa
                episode2 = 99
                item_local.title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(episode2).zfill(2))                  #Creamos un título con el rango ficticio de episodios
            elif item_local.contentEpisodeNumber == 0:  #episodio extraño
                item_local.title = '%sx%s - %s' % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), temp_epi)
            else:                                       #episodio normal
                item_local.title = '%sx%s -' % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2))
            
            if len(itemlist) > 0 and item_local.contentSeason == itemlist[-1].contentSeason and item_local.contentEpisodeNumber == itemlist[-1].contentEpisodeNumber and item_local.title == itemlist[-1].title and itemlist[-1].contentEpisodeNumber != 0:     #solo guardamos un episodio ...
                if itemlist[-1].quality:
                    itemlist[-1].quality += ", " + quality          #... pero acumulamos las calidades
                else:
                    itemlist[-1].quality = quality
                continue                                            #ignoramos el episodio duplicado
            else:
                item_local.quality = quality

            itemlist.append(item_local.clone())                     #guardamos el episodio

            #logger.debug("EPISODIOS: " + temp_actual + " (" + str (item_local.contentSeason) + "x" + str (item_local.contentEpisodeNumber) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista Temps: " + str(temp_lista))
            #logger.debug(item_local)
        
        temp_lista += [temp_actual_num]
        if temp_advance == 'back':
            temp_actual = temp_previous                     #hay temporadas anteriores, iremos marcha atrás procesándolas
        elif temp_advance == 'forw':
            temp_actual = temp_next                         #hay temporadas posteriores.  Las procesamos
        else:
            temp_actual = ''                                #No hay más temporadas, salimos

        data = ''                                           #Limpiamos data para forzar la lectura en la próxima pasada
        
    item.contentSeason_save = contentSeason                 #Guardamos temporalemente este contador
    
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos

    # Pasada por TMDB y clasificación de lista por temporada y episodio
    tmdb.set_infoLabels(itemlist, True)

    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
        
    return itemlist


def actualizar_titulos(item):
    logger.info()
    itemlist = []
    
    from platformcode import launcher
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return launcher.run(item)
    
    
def search(item, texto):
    logger.info("texto:" + texto)
    texto = texto.replace(" ", "+")
    itemlist = []
    
    item.url = "%s?s=%s" % (item.url, texto)
    item.media = "search"               #Marcar para "Listado": igual comportamiento que "Categorías"

    try:
        if "series/" in item.url:
            item.extra = "series"
            item.title = "Series"
        else:
            item.extra = "peliculas"
            item.title = "Películas"

        itemlist = listado(item)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("ERROR: %s: SEARCH" % line)
        return []
