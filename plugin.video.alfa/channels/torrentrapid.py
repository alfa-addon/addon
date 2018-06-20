# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
import datetime

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools

host = 'http://torrentrapid.com/'

item = Item()
if not item.channel:
    item.channel = scrapertools.find_single_match(host, r'(\w+)\.com\/')
__modo_grafico__ = config.get_setting('modo_grafico', item.channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel)

def mainlist(item):
    logger.info()

    itemlist = []

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_docus = get_thumb("channels_documentary.png")
    thumb_buscar = get_thumb("search.png")
    thumb_settings = get_thumb("setting_0.png")

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host,
                         extra="peliculas", thumbnail=thumb_pelis ))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series",
                         thumbnail=thumb_series))
                         
    itemlist.append(Item(channel=item.channel, action="submenu", title="Documentales", url=host, extra="varios",
                         thumbnail=thumb_docus))
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", url=host + "buscar", thumbnail=thumb_buscar))
        
    itemlist.append(
        Item(channel=item.channel, action="", title="[COLOR yellow]Configuración de Servidores:[/COLOR]", url="", thumbnail=thumb_settings))
    itemlist.append(
        Item(channel=item.channel, action="settingCanal", title="Servidores para Ver Online y Descargas", url="", thumbnail=thumb_settings))

    return itemlist

    
def settingCanal(item):
    from platformcode import platformtools
    return platformtools.show_channel_settings()

    
def submenu(item):
    logger.info()
    itemlist = []

    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist     #Algo no funciona, pintamos lo que tenemos
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("'", '"').replace('/series"', '/series/"')   #Compatibilidad con mispelisy.series.com

    host_dom = host.replace("https://", "").replace("http://", "").replace("www.", "")
    patron = '<li><a href="http://(?:www.)?' + host_dom + item.extra + '/">.*?<ul.*?>(.*?)</ul>'
    if "pelisyseries.com" in host and item.extra == "varios":      #compatibilidad con mispelisy.series.com
        data = '<a href="' + host + 'varios/" title="Documentales"><i class="icon-rocket"></i> Documentales</a>'
    else:
        if data:
            data = scrapertools.get_match(data, patron)
            if not data:
                logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        else:
            return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    patron = '<.*?href="([^"]+)".*?>([^>]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, extra=item.extra))
        itemlist.append(
            Item(channel=item.channel, action="alfabeto", title=title + " [A-Z]", url=url, extra=item.extra))
            
    if item.extra == "peliculas":
        itemlist.append(Item(channel=item.channel, action="listado", title="Películas 4K", url=host + "peliculas-hd/4kultrahd/", extra=item.extra))
        itemlist.append(
            Item(channel=item.channel, action="alfabeto", title="Películas 4K" + " [A-Z]", url=host + "peliculas-hd/4kultrahd/", extra=item.extra))
            
    return itemlist


def alfabeto(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    patron = '<ul class="alfabeto">(.*?)</ul>'
    if data:
        data = scrapertools.get_match(data, patron)
    else:
        return itemlist

    patron = '<a href="([^"]+)"[^>]+>([^>]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.upper()
        url = scrapedurl

        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, extra=item.extra))

    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    clase = "pelilist"      # etiqueta para localizar zona de listado de contenidos
    url_next_page =''       # Controlde paginación
    cnt_tot = 30            # Poner el num. máximo de items por página

    if item.totalItems:
        del item.totalItems

    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Establecemos los valores básicos en función del tipo de contenido
    if item.extra == "peliculas":
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True                                          #Sí hay paginación
    elif item.extra == "series" and not "/miniseries" in item.url:
        item.action = "episodios"
        item.contentType = "tvshow"
        pag = True
    elif item.extra == "varios" or "/miniseries" in item.url:
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True
    
    #Selecciona el tramo de la página con el listado de contenidos
    patron = '<ul class="' + clase + '">(.*?)</ul>'
    if data:
        fichas = scrapertools.get_match(data, patron)
        if not fichas and not '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:         #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        elif '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:                          #no hay vídeos
            return itemlist
    else:
        return itemlist
    page_extra = clase

    #Scrapea los datos de cada vídeo.  Título alternativo se mantiene, aunque no se usa de momento
    patron = '<a href="([^"]+).*?'  # la url
    patron += 'title="([^"]+).*?'  # el titulo
    patron += '<img.*?src="([^"]+)"[^>]+>.*?'   # el thumbnail
    patron += '<h2.*?>(.*?)?<\/h2>'  # titulo alternativo.  Se trunca en títulos largos
    patron += '<span>([^<].*?)?<'  # la calidad
    matches = re.compile(patron, re.DOTALL).findall(fichas)
    if not matches:                             #error
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + fichas)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("MATCHES: " + str(len(matches)))
    #logger.debug(matches)
    #logger.debug("patron: " + patron + " / fichas: " + fichas)

    # Identifico la página actual y el total de páginas para el pie de página
    total_pag  = scrapertools.find_single_match(data,'<a href=".*?(\d+)?">Last<\/a><\/li>')

    if not item.post_num:
        post_num = 1
    else:
        post_num = int(item.post_num) + 1
    if not total_pag:
        total_pag = 1
    #Calcula las páginas del canal por cada página de la web
    total_pag = int(total_pag) * int((float(len(matches))/float(cnt_tot)) + 0.999999)
    
    # Preparamos la paginación.
    if not item.cnt_pag:
        cnt_pag = 0
    else:
        cnt_pag = item.cnt_pag
        del item.cnt_pag
    
    matches_cnt = len(matches)
    if item.next_page != 'b':
        if matches_cnt > cnt_pag + cnt_tot:
            url_next_page = item.url
        matches = matches[cnt_pag:cnt_pag+cnt_tot]
        next_page = ''
        if matches_cnt <= cnt_pag + (cnt_tot * 2):
            if pag:
                next_page = 'b'
        modo = 'continue'
    else:
        matches = matches[cnt_pag:cnt_pag+cnt_tot]
        next_page = 'a'
        patron_next_page  = '<a href="([^"]+)">Next<\/a>'
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])
            modo = 'next'
    
    # Avanzamos el contador de líneas en una página
    if item.next_page:
        del item.next_page
    if modo == 'next':
        cnt_pag = 0
    else:
        cnt_pag += cnt_tot

    #Tratamos todos los contenidos, creardo una variable local de Item
    for scrapedurl, scrapedtitle, scrapedthumbnail, title_alt, calidad in matches:
        item_local = item.clone()
        if item_local.tipo:
            del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.post_num:
            del item_local.post_num
        if item_local.category:
            del item_local.category

        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        title = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        title_alt = re.sub('\r\n', '', title_alt).decode('iso-8859-1').encode('utf8').strip()
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ").replace(".", " ")
        title_alt = title_alt.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ")
        
        item_local.quality = calidad
        title_subs = []
        
        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower() or ".com/pelicula/" in scrapedurl  or ".com/series-vo" in scrapedurl or "-vo/" in scrapedurl or "vos" in calidad.lower() or "vose" in calidad.lower() or "v.o.s" in calidad.lower() or "sub" in calidad.lower() or ".com/peliculas-vo" in item.url:
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "").replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "").replace(" VO", "").replace("Subtitulos", "")
        if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" in scrapedurl or "latino" in calidad.lower() or "argentina" in calidad.lower():
            item_local.language += ["LAT"]
        
        #Guardamos info de 3D en calidad y limpiamos
        if "3d" in title.lower():
            if not "3d" in item_local.quality.lower():
                item_local.quality = item_local.quality + " 3D"
            calidad3D = scrapertools.find_single_match(title, r'\s(3[d|D]\s\w+)')
            if calidad3D:
                item_local.quality = item_local.quality.replace("3D", calidad3D)
            title = re.sub(r'\s3[d|D]\s\w+', '', title)
            title = re.sub(r'\s3[d|D]', '', title)
            title_alt = re.sub(r'\s3[d|D]\s\w+', '', title_alt)
            title_alt = re.sub(r'\s3[d|D]', '', title_alt)
            if "imax" in title.lower():
                item_local.quality = item_local.quality + " IMAX"
                title = title.replace(" IMAX", "").replace(" imax", "")
                title_alt = title_alt.replace(" IMAX", "").replace(" imax", "")
        if "2d" in title.lower():
            title = title.replace("(2D)", "").replace("(2d)", "").replace("2D", "").replace("2d", "")
            title_subs += ["[2D]"]
        
        #Extraemos info adicional del título y la guardamos para después de TMDB
        if "temp" in title.lower() or "cap" in title.lower():        #Eliminamos Temporada, solo nos interesa la serie completa
            title = re.sub(r' - [t|T]emp\w+ \d+ Comp\w+\d+[x|X]\d+', ' Completa', title)
            title = re.sub(r' - [t|T]emp\w+ \d+x\d+', '', title)
            title = re.sub(r' - [t|T]emp\w+ \d+', '', title)
            title = re.sub(r' - [t|T]emp\w+.*?\d+', '', title)
            title = re.sub(r' [t|T]emp.*?\d+x\d+', '', title)
            title = re.sub(r' [t|T]emp.*?\d+', '', title)
            title = re.sub(r' [c|C]ap.*?\d+', '', title)
        if "audio" in title.lower():        #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower() or "multileng" in title.lower() or "multileng" in item_local.quality.lower() or (("espa" in title.lower() or "spani" in title.lower()) and "VOS" in item_local.language):
            item_local.language[0:0] = ["DUAL"]
            title = re.sub(r'\[[D|d]ual.*?\]', '', title)
            title = re.sub(r'\[[M|m]ultileng.*?\]', '', title)
            item_local.quality = re.sub(r'\[[M|m]ultileng.*?\]', '', item_local.quality)
        if "duolog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Duologia", "").replace(" duologia", "").replace(" Duolog", "").replace(" duolog", "")
        if "trilog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Trilogia", "").replace(" trilogia", "").replace(" Trilog", "").replace(" trilog", "")
        if "extendida" in title.lower():
            title_subs += ["[V. Extendida]"]
            title = title.replace(" Version Extendida", "").replace(" (Version Extendida)", "").replace(" V. Extendida", "").replace(" VExtendida", "").replace(" V Extendida", "")
        if "saga" in title.lower():
            title = title.replace(" Saga Completa", "").replace(" saga sompleta", "").replace(" Saga", "").replace(" saga", "")
            title_subs += ["[Saga]"]
        if "colecc" in title.lower() or "completa" in title.lower():
            title = title.replace(" Coleccion", "").replace(" coleccion", "").replace(" Colecci", "").replace(" colecci", "").replace(" Completa", "").replace(" completa", "").replace(" COMPLETA", "")
        if scrapertools.find_single_match(title, r'(- [m|M].*?serie ?\w+)'):
            title = re.sub(r'- [m|M].*?serie ?\w+', '', title)
            title_subs += ["[Miniserie]"]

        #Limpiamos restos en título
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "").replace("ingles", "").replace("Inglés", "").replace("Ingles", "").replace("Ingl", "").replace("Engl", "").replace("Calidad", "").replace("de la Serie", "")
        title_alt = title_alt.replace("Castellano", "").replace("castellano", "").replace("inglés", "").replace("ingles", "").replace("Inglés", "").replace("Ingles", "").replace("Ingl", "").replace("Engl", "").replace("Calidad", "").replace("de la Serie", "")
        
        #Limpiamos cabeceras y colas del título
        title = re.sub(r'Descargar\s\w+\-\w+', '', title)
        title = re.sub(r'\(COMPLE.*?\)', '', title)
        title = re.sub(r'\(\d{4}\)$', '', title)
        title = re.sub(r'\d{4}$', '', title)
        title = re.sub(r' \d+x\d+', '', title)
        title = re.sub(r' x\d+', '', title)
        
        title = title.replace("Ver online ", "").replace("Descarga Serie HD ", "").replace("Descargar Serie HD ", "").replace("Descarga Serie ", "").replace("Descargar Serie ", "").replace("Ver en linea ", "").replace("Ver en linea", "").replace("HD ", "").replace("(Proper)", "").replace("RatDVD", "").replace("DVDRiP", "").replace("DVDRIP", "").replace("DVDRip", "").replace("DVDR", "").replace("DVD9", "").replace("DVD", "").replace("DVBRIP", "").replace("DVB", "").replace("LINE", "").replace("- ES ", "").replace("ES ", "").replace("COMPLETA", "").replace("(", "-").replace(")", "-").replace(".", " ").strip()
        
        title = title.replace("Descargar torrent ", "").replace("Descarga Gratis ", "").replace("Descargar Estreno ", "").replace("Descargar Estrenos ", "").replace("Pelicula en latino ", "").replace("Descargar Pelicula ", "").replace("Descargar Peliculas ", "").replace("Descargar peliculas ", "").replace("Descargar Todas ", "").replace("Descargar Otras ", "").replace("Descargar ", "").replace("Descarga ", "").replace("Bajar ", "").replace("HDRIP ", "").replace("HDRiP ", "").replace("HDRip ", "").replace("RIP ", "").replace("Rip", "").replace("RiP", "").replace("XviD", "").replace("AC3 5.1", "").replace("AC3", "").replace("1080p ", "").replace("720p ", "").replace("DVD-Screener ", "").replace("TS-Screener ", "").replace("Screener ", "").replace("BdRemux ", "").replace("BR ", "").replace("4KULTRA", "").replace("FULLBluRay", "").replace("FullBluRay", "").replace("BluRay", "").replace("Bonus Disc", "").replace("de Cine ", "").replace("TeleCine ", "").replace("latino", "").replace("Latino", "").replace("argentina", "").replace("Argentina", "").strip()
        
        if title.endswith("torrent gratis"): title = title[:-15]
        if title.endswith("gratis"): title = title[:-7]
        if title.endswith("torrent"): title = title[:-8]
        if title.endswith("en HD"): title = title[:-6]
        if title.endswith(" -"): title = title[:-2]
        if "en espa" in title: title = title[:-11]
        
        item_local.quality = item_local.quality.replace("gratis ", "")
        if "HDR" in title:
            title = title.replace(" HDR", "")
            if not "HDR" in item_local.quality:
                item_local.quality += " HDR"
        
        title = title.strip()
        title_alt = title_alt.strip()
        item_local.quality = item_local.quality.strip()

        if not title:       #Usamos solo el title_alt en caso de que no exista el título original
            title = title_alt
            if not title:
                title = "SIN TITULO"
        
        #Limpieza final del título y guardado en las variables según su tipo de contenido
        title = scrapertools.remove_htmltags(title)
        item_local.title = title
        if item_local.contentType == "movie":
            item_local.contentTitle = title
        else:
            item_local.contentSerieName = title
        
        #Guardamos el resto de variables del vídeo
        item_local.url = scrapedurl
        item_local.thumbnail = scrapedthumbnail
        item_local.contentThumbnail = scrapedthumbnail

        #Guardamos el año que puede venir en la url, por si luego no hay resultados desde TMDB
        year = ''
        if item_local.contentType == "movie": 
            year = scrapertools.find_single_match(scrapedurl, r'(\d{4})')
        if year >= "1900" and year <= "2040" and year != "2020":
            title_subs += [year]
        item_local.infoLabels['year'] = '-'
        
        #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
        item_local.title_subs = title_subs
        
        #Agrega el item local a la lista itemlist
        itemlist.append(item_local.clone())

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="mainlist", title="No se ha podido cargar el listado"))
    else:
        if url_next_page:
            itemlist.append(
                Item(channel=item.channel, action="listado", title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + str(post_num) + " de " + str(total_pag), url=url_next_page, next_page=next_page, cnt_pag=cnt_pag, post_num=post_num, pag=pag, modo=modo, extra=item.extra))
                
    #logger.debug(url_next_page + " / " + next_page + " / " + str(matches_cnt) + " / " + str(cnt_pag)+ " / " + str(total_pag)  + " / " + str(pag)  + " / " + modo + " / " + item.extra)
    
    return itemlist

def listado_busqueda(item):
    logger.info()
    itemlist = []
    cnt_tot = 40            # Poner el num. máximo de items por página.  Dejamos que la web lo controle
    cnt_title = 0           # Contador de líneas insertadas en Itemlist
    cnt_pag = 0             # Contador de líneas leídas de Matches

    if item.cnt_pag:
        cnt_pag = item.cnt_pag      # Se guarda en la lista de páginas anteriores en Item
        del item.cnt_pag
    if item.totalItems:
        del item.totalItems
    if item.text_bold:
        del item.text_bold
    if item.text_color:
        del item.text_color

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []        # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista = item.title_lista      # Se usa la lista de páginas anteriores en Item
    title_lista_alt = []
    for url in title_lista:
        title_lista_alt += [url]        #hacemos una copia no vinculada de title_lista
    matches = []
    cnt_next = 0
    total_pag = 1
    post_num = 1
    
    #Máximo num. de líneas permitidas por TMDB. Máx de 5 páginas por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot and cnt_next < 5:

        try:
            data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
        except:
            logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        cnt_next += 1
        if not data:        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Obtiene la dirección de la próxima página, si la hay
        try:
            post_actual = item.post     #Guardamos el post actual por si hay overflow de Itemlist y hay que hechar marcha atrás
            get, post, total_pag = scrapertools.find_single_match(data, '<ul class="pagination">.*?<a\s*href="([^"]+)"(?:\s*onClick=".*?\(\'([^"]+)\'\);">Next<\/a>.*?onClick=".*?\(\'([^"]+)\'\);">Last<\/a>)')
        except:
            post = False
            cnt_next = 99       #No hay más páginas.  Salir del bucle después de procesar ésta

        if post:        #puntero a la siguiente página.  Cada página de la web tiene 30 entradas
            if "pg" in item.post:
                item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
            else:
                item.post += "&pg=%s" % post
            post_num = int(post)-1      #Guardo página actual

        # Preparamos un patron que pretence recoger todos los datos significativos del video
        pattern = '<ul class="%s">(.*?)</ul>' % item.pattern            #seleccionamos el bloque que nos interesa 
        data_alt = data
        data = scrapertools.get_match(data, pattern)
        #pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img.*?src="(?P<thumb>[^"]+)?".*?<h2.*?>(?P<title>.*?)?<\/h2>'
        pattern = '<li[^>]*><a href="(?P<scrapedurl>[^"]+).*?'          #url
        pattern += 'title="(?P<scrapedtitle>[^"]+).*?'                  #título
        pattern += '<img.*?src="(?P<scrapedthumbnail>[^"]+)?".*?'       #thumb
        pattern += '<h2.*?(?P<calidad>\[.*?)?<\/h2.*?'                  #calidad
        pattern += '<span.*?>\d+-\d+-(?P<year>\d{4})?<\/span>*.?'       #año
        pattern += '<span.*?>(?P<size>\d+[\.|\s].*?[GB|MB])?<\/span>'   #tamaño (significativo para peliculas)
        matches_alt = re.compile(pattern, re.DOTALL).findall(data)
        if not matches_alt and not '<h3><strong>( 0 ) Resultados encontrados </strong>' in data_alt:        #error
            logger.error("ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web " + " / PATRON: " + pattern + " / DATA: " + data_alt)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #Ahora se hace una simulación para saber cuantas líneas podemos albergar en este Itemlist.
        #Se controlará cuantas páginas web se tienen que leer para rellenar la lista, sin pasarse
        
        title_lista_alt_for = []         #usamos está lista de urls para el FOR, luego la integramos en la del WHILE
        for scrapedurl, scrapedtitle, scrapedthumbnail, calidad, year, size in matches_alt:
            
            #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
            #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
            #Cuando llega al num. máximo de entradas por página, la pinta y guarda los contadores y la lista de series
            scrapedurl_alt = scrapedurl
            if "pelisyseries.com" in host:          #Excepción para mispelisyseries.com.
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+-al-\d+', '', scrapedurl_alt) #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/\d{5,7}', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                if scrapedurl_alt in title_lista_alt:       # si ya se ha tratado, pasamos al siguiente item
                    continue                                # solo guardamos la url para series y docus

            if scrapedurl_alt in title_lista_alt or scrapedurl_alt in title_lista_alt_for:  # si ya se ha tratado, pasamos al siguiente item
                continue                            # solo guardamos la url para series y docus

            if ".com/serie" in scrapedurl or "/serie" in scrapedurl or "-serie" in scrapedurl or "varios/" in scrapedurl:
                title_lista_alt_for += [scrapedurl_alt]

            if "juego/" in scrapedurl:      # no mostramos lo que no sean videos
                continue
            cnt_title += 1                  # Sería una línea real más para Itemlist
            
            #Control de página
            if cnt_title > cnt_tot*0.65:        #si se acerca al máximo num. de lineas por pagina, tratamos lo que tenemos
                cnt_next = 99                   #Casi completo, no sobrepasar con la siguiente página
                if cnt_title > cnt_tot:
                    cnt_title = 99              #Sobrepasado el máximo.  Ignoro página actual
                    item.post = post_actual     #Restauro puntero "next" a la página actual, para releearla en otra pasada
                    post_num -= 1               #Restauro puntero a la página actual en el pie de página
                    break

        if cnt_title <= cnt_tot:
            matches.extend(matches_alt)         #Acumulamos las entradas a tratar. Si nos hemos pasado ignoro última página
            title_lista_alt.extend(title_lista_alt_for)
    
    #logger.debug("PATRON: " + pattern)
    #logger.debug(matches)
    #logger.debug(title_lista_alt)
    #logger.debug(data)

    cnt_title = 0
    for scrapedurl, scrapedtitle, scrapedthumbnail, calidad, year, size in matches:
        cnt_pag += 1 
        
        #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
        #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
        #El control de página ya se ha realizado más arriba
        if "pelisyseries.com" in host:          #Excepción para mispelisyseries.com.
                scrapedurl_alt = scrapedurl
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+-al-\d+', '', scrapedurl_alt) #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/\d{5,7}', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                if scrapedurl_alt in title_lista:       # si ya se ha tratado, pasamos al siguiente item
                    continue                                # solo guardamos la url para series y docus

        if scrapedurl in title_lista:       # si ya se ha tratado, pasamos al siguiente item
            continue                            # solo guardamos la url para series y docus

        if ".com/serie" in scrapedurl or "/serie" in scrapedurl or "-serie" in scrapedurl or "varios/" in scrapedurl:
            if "pelisyseries.com" in host:
                title_lista += [scrapedurl_alt]
            else:
                title_lista += [scrapedurl]
        if "juego/" in scrapedurl or "xbox" in scrapedurl.lower() or "xbox" in scrapedtitle.lower() or "windows" in scrapedtitle.lower() or "windows" in calidad.lower() or "nintendo" in scrapedtitle.lower() or "xbox" in calidad.lower() or "epub" in calidad.lower() or "pdf" in calidad.lower() or "pcdvd" in calidad.lower() or "crack" in calidad.lower():      # no mostramos lo que no sean videos
            continue
        cnt_title += 1                  # Sería una línea real más para Itemlist
        
        #Creamos una copia de Item para cada contenido
        item_local = item.clone()
        if item_local.category:
            del item_local.category
        if item_local.tipo:
            del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.post:
            del item_local.post
        if item_local.pattern:
            del item_local.pattern
        if item_local.title_lista:
            del item_local.title_lista
        item_local.adult = True
        del item_local.adult
        item_local.folder = True
        del item_local.folder
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        
        #Establecemos los valores básicos en función del tipo de contenido
        if (".com/serie" in scrapedurl or "/serie" in scrapedurl or "-serie" in scrapedurl) and not "/miniseries" in scrapedurl:      #Series
            item_local.action = "episodios"
            item_local.contentType = "tvshow"
            item_local.extra = "series"
        elif "varios/" in scrapedurl or "/miniseries" in scrapedurl:               #Documentales y varios
            item_local.action = "findvideos"
            item_local.contentType = "movie"
            item_local.extra = "varios"
        else:                                       #Películas
            item_local.action = "findvideos"
            item_local.contentType = "movie"
            item_local.extra = "peliculas"
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        title = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ")
        
        item_local.quality = scrapertools.htmlclean(calidad)
        title_subs = []
        
        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower() or ".com/pelicula/" in scrapedurl  or ".com/series-vo" in scrapedurl or "-vo/" in scrapedurl or "vos" in calidad.lower() or "vose" in calidad.lower() or "v.o.s" in calidad.lower() or "sub" in calidad.lower() or ".com/peliculas-vo" in item.url:
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "").replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "").replace(" VO", "").replace("Subtitulos", "")
        if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" in scrapedurl or "latino" in calidad.lower() or "argentina" in calidad.lower():
            item_local.language += ["LAT"]
        
        #Guardamos info de 3D en calidad y limpiamos
        if "3d" in title.lower():
            if not "3d" in item_local.quality.lower():
                item_local.quality = "3D " + item_local.quality
            calidad3D = scrapertools.find_single_match(title, r'\s(3[d|D]\s\w+)')
            if calidad3D:
                item_local.quality = item_local.quality.replace("3D", calidad3D)
            title = re.sub(r'\s3[d|D]\s\w+', '', title)
            title = re.sub(r'\s3[d|D]', '', title)
            if "imax" in title.lower():
                item_local.quality = item_local.quality + " IMAX"
                title = title.replace(" IMAX", "").replace(" imax", "")
        if "2d" in title.lower():
            title = title.replace("(2D)", "").replace("(2d)", "").replace("2D", "").replace("2d", "")
            title_subs += ["[2D]"]
        
        #Extraemos info adicional del título y la guardamos para después de TMDB
        if ("temp" in title.lower() or "cap" in title.lower()) and item_local.contentType != "movie":
            #Eliminamos Temporada de Series, solo nos interesa la serie completa
            title = re.sub(r' - [t|T]emp\w+ \d+ Comp\w+\d+[x|X]\d+', ' Completa', title)
            title = re.sub(r' - [t|T]emp\w+ \d+[x|X]\d+', '', title)
            title = re.sub(r' - [t|T]emp\w+ \d+', '', title)
            title = re.sub(r' - [t|T]emp\w+.*?\d+', '', title)
            title = re.sub(r' [t|T]emp.*?\d+[x|X]\d+', '', title)
            title = re.sub(r' [t|T]emp.*?\d+', '', title)
            title = re.sub(r' [c|C]ap.*?\d+', '', title)
        if "audio" in title.lower():        #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower() or "multileng" in title.lower() or "multileng" in item_local.quality.lower() or (("espa" in title.lower() or "spani" in title.lower()) and "VOS" in item_local.language):
            item_local.language[0:0] = ["DUAL"]
            title = re.sub(r'\[[D|d]ual.*?\]', '', title)
            title = re.sub(r'\[[M|m]ultileng.*?\]', '', title)
            item_local.quality = re.sub(r'\[[M|m]ultileng.*?\]', '', item_local.quality)
        if "duolog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Duologia", "").replace(" duologia", "").replace(" Duolog", "").replace(" duolog", "")
        if "trilog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Trilogia", "").replace(" trilogia", "").replace(" Trilog", "").replace(" trilog", "")
        if "extendida" in title.lower():
            title_subs += ["[V. Extendida]"]
            title = title.replace(" Version Extendida", "").replace(" (Version Extendida)", "").replace(" V. Extendida", "").replace(" VExtendida", "").replace(" V Extendida", "")
        if "saga" in title.lower():
            title = title.replace(" Saga Completa", "").replace(" saga completa", "").replace(" Saga", "").replace(" saga", "")
            title_subs += ["[Saga]"]
        if "colecc" in title.lower() or "completa" in title.lower():
            title = title.replace(" Coleccion", "").replace(" coleccion", "").replace(" Colecci", "").replace(" colecci", "").replace(" Completa", "").replace(" completa", "").replace(" COMPLETA", "")
            title_subs += ["[Saga]"]
        if scrapertools.find_single_match(title, r'(- [m|M].*?serie ?\w+)'):
            title = re.sub(r'- [m|M].*?serie ?\w+', '', title)
            title_subs += ["[Miniserie]"]

        #Limpiamos restos en título
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "").replace("ingles", "").replace("Inglés", "").replace("Ingles", "").replace("Ing", "").replace("Eng", "").replace("Calidad", "").replace("de la Serie", "")
        
        #Limpiamos cabeceras y colas del título
        title = re.sub(r'Descargar\s\w+\-\w+', '', title)
        title = re.sub(r'\(COMPLE.*?\)', '', title)
        title = re.sub(r'\(\d{4}\)$', '', title)
        title = re.sub(r'\d{4}$', '', title)
        title = re.sub(r' \d+x\d+', '', title)
        title = re.sub(r' x\d+', '', title)
        
        title = title.replace("Ver online ", "").replace("Descarga Serie HD ", "").replace("Descargar Serie HD ", "").replace("Descarga Serie ", "").replace("Descargar Serie ", "").replace("Ver en linea ", "").replace("Ver en linea", "").replace("HD ", "").replace("(Proper)", "").replace("RatDVD", "").replace("DVDRiP", "").replace("DVDRIP", "").replace("DVDRip", "").replace("DVDR", "").replace("DVD9", "").replace("DVD", "").replace("DVBRIP", "").replace("DVB", "").replace("LINE", "").replace("- ES ", "").replace("ES ", "").replace("COMPLETA", "").replace("(", "-").replace(")", "-").replace(".", " ").strip()
        
        title = title.replace("Descargar torrent ", "").replace("Descarga Gratis ", "").replace("Descargar Estreno ", "").replace("Descargar Estrenos ", "").replace("Pelicula en latino ", "").replace("Descargar Pelicula ", "").replace("Descargar Peliculas ", "").replace("Descargar peliculas ", "").replace("Descargar Todas ", "").replace("Descargar Otras ", "").replace("Descargar ", "").replace("Descarga ", "").replace("Bajar ", "").replace("HDRIP ", "").replace("HDRiP ", "").replace("HDRip ", "").replace("RIP ", "").replace("Rip", "").replace("RiP", "").replace("XviD", "").replace("AC3 5.1", "").replace("AC3", "").replace("1080p ", "").replace("720p ", "").replace("DVD-Screener ", "").replace("TS-Screener ", "").replace("Screener ", "").replace("BdRemux ", "").replace("BR ", "").replace("4KULTRA", "").replace("FULLBluRay", "").replace("FullBluRay", "").replace("BluRay", "").replace("Bonus Disc", "").replace("de Cine ", "").replace("TeleCine ", "").replace("latino", "").replace("Latino", "").replace("argentina", "").replace("Argentina", "").strip()
        
        if "pelisyseries.com" in host and item_local.contentType == "tvshow":
            titulo = ''
            title = title.lower()
            title = re.sub(r'\d+[x|X]\d+', '', title)
            while len(title) > 0:
                palabra = scrapertools.find_single_match(title, r'(^[A-Za-z0-9_.-?ñ]+)')
                if not palabra:
                    break
                title = title.replace(palabra, '')
                title = re.sub(r'^\s+\??', '', title)
                title = re.sub(r'^-\s?', '', title)
                titulo += palabra + " "
                palabra = ""
            title = titulo.title()
        
        if title.endswith("torrent gratis"): title = title[:-15]
        if title.endswith("gratis"): title = title[:-7]
        if title.endswith("torrent"): title = title[:-8]
        if title.endswith("en HD"): title = title[:-6]
        if title.endswith(" -"): title = title[:-2]
        if "en espa" in title: title = title[:-11]
        #title = re.sub(r'^\s', '', title)
        title = title.replace("a?o", 'año').replace("a?O", 'año').replace("A?o", 'Año').replace("A?O", 'Año').strip()

        #Preparamos calidad
        item_local.quality = item_local.quality.replace("[ ", "").replace(" ]", "")     #Preparamos calidad para Series
        item_local.quality = re.sub(r'\[\d{4}\]', '', item_local.quality)               #Quitar año, si lo tiene
        item_local.quality = re.sub(r'\[Cap.*?\]', '', item_local.quality)              #Quitar episodios, si lo tiene
        item_local.quality = re.sub(r'\[Docu.*?\]', '', item_local.quality)             #Quitar tipo contenidos, si lo tiene
        #Mirar si es DUAL
        if "VOS" in item_local.language and "DUAL" not in item_local.language and ("[sp" in item_local.quality.lower() or "espa" in item_local.quality.lower() or "cast" in item_local.quality.lower() or "spani" in item_local.quality.lower()):
            item_local.language[0:0] = ["DUAL"]    
        if ("[es-" in item_local.quality.lower() or (("cast" in item_local.quality.lower() or "espa" in item_local.quality.lower() or "spani" in item_local.quality.lower()) and ("eng" in item_local.quality.lower() or "ing" in item_local.quality.lower()))) and "DUAL" not in item_local.language:     #Mirar si es DUAL
            item_local.language[0:0] = ["DUAL"]                                         #Salvar DUAL en idioma
            item_local.quality = re.sub(r'\[[es|ES]-\w+]', '', item_local.quality)      #borrar DUAL
        item_local.quality = re.sub(r'[\s|-][c|C]aste.+', '', item_local.quality)       #Borrar después de Castellano
        item_local.quality = re.sub(r'[\s|-][e|E]spa.+', '', item_local.quality)        #Borrar después de Español
        item_local.quality = re.sub(r'[\s|-|\[][s|S]pani.+', '', item_local.quality)    #Borrar después de Spanish
        item_local.quality = re.sub(r'[\s|-][i|I|e|E]ngl.+', '', item_local.quality)    #Borrar después de Inglés-English
        item_local.quality = item_local.quality.replace("[", "").replace("]", " ").replace("ALTA DEFINICION", "HDTV").replace(" Cap", "")
        #Borrar palabras innecesarias restantes
        item_local.quality = item_local.quality.replace("Espaol", "").replace("Español", "").replace("Espa", "").replace("Castellano ", "").replace("Castellano", "").replace("Spanish", "").replace("English", "").replace("Ingles", "").replace("Latino", "").replace("+Subs", "").replace("-Subs", "").replace("Subs", "").replace("VOSE", "").replace("VOS", "").strip()
        
        #Limpieza final del título y guardado en las variables según su tipo de contenido
        item_local.title = title
        if item_local.contentType == "movie":
            item_local.contentTitle = title
            size = size.replace(".", ",")
            item_local.quality = '%s [%s]' % (item_local.quality, size)
        else:
            item_local.contentSerieName = title
        
        #Guardamos el resto de variables del vídeo
        item_local.url = scrapedurl
        item_local.thumbnail = scrapedthumbnail
        item_local.contentThumbnail = scrapedthumbnail

        #Guardamos el año que puede venir en la url, por si luego no hay resultados desde TMDB
        if year >= "1900" and year <= "2040" and year != "2020":
            title_subs += [year]
        item_local.infoLabels['year'] = '-'
        
        #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
        item_local.title_subs = title_subs

        # Codigo para rescatar lo que se pueda en pelisy.series.com de Series para la Videoteca.  la URL apunta al capítulo y no a la Serie.  Nombre de Serie frecuentemente en blanco. Se obtiene de Thumb, así como el id de la serie
        if ("/serie" in item_local.url or "-serie" in item_local.url) and "pelisyseries.com" in host:
            #Extraer la calidad de la serie basados en la info de la url
            if "seriehd" in url:
                calidad_mps = "series-hd/"
            elif "serievo" in url or "serie-vo" in url:
                calidad_mps = "series-vo/"
            else:
                calidad_mps = "series/"
                
            if "no_image" in scrapedthumbnail:
                real_title_mps = item_local.title
            else:
                real_title_mps = re.sub(r'.*?\/\d+_', '', scrapedthumbnail)
                real_title_mps = re.sub(r'\.\w+.*?', '', real_title_mps)
            
            #Extraer el ID de la serie desde Thumbs (4 dígitos).  Si no hay, nulo
            if "/0_" not in scrapedthumbnail and not "no_image" in scrapedthumbnail:
                serieid = scrapertools.find_single_match(scrapedthumbnail, r'.*?\/\w\/(?P<serieid>\d+).*?.*')
                if len(serieid) > 5:
                    serieid = ""
            else:
                serieid = ""

            #detectar si la url creada de tvshow es válida o hay que volver atras 
            url_id = host + calidad_mps + real_title_mps + "/" + serieid        #A veces necesita el serieid...
            url_tvshow = host + calidad_mps + real_title_mps + "/"              #... otras no.  A probar...
            
            #Leemos la página, a ver  si es una página de episodios
            data_serie = data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(url_id).data)
            data_serie = unicode(data_serie, "iso-8859-1", errors="replace").encode("utf-8")
            data_serie = data_serie.replace("chapters", "buscar-list")
            
            pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"       #Patrón de lista de episodios
            if not scrapertools.find_single_match(data_serie, pattern) and serieid:     #no es válida la página, 
                                                                                        #intentarlo con la otra url
                data_serie = data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(url_tvshow).data)
                data_serie = unicode(data_serie, "iso-8859-1", errors="replace").encode("utf-8")
                data_serie = data_serie.replace("chapters", "buscar-list")
                
                if not scrapertools.find_single_match(data_serie, pattern):     #No ha habido suerte ...
                    item_local.contentType = "movie"                            #tratarlo el capítulo como película
                    item_local.extra = "peliculas"
                else:
                    item_local.url = url_tvshow         #Cambiamos url de episodio por el de serie
            else:
                item_local.url = url_id                 #Cambiamos url de episodio por el de serie

            #logger.debug("url: " + item_local.url + " / title o/n: " + item_local.title + " / " + real_title_mps + " / calidad_mps : " + calidad_mps + " / contentType : " + item_local.contentType)
            
            item_local.title = real_title_mps           #Esperemos que el nuevo título esté bien
        
        #Agrega el item local a la lista itemlist
        itemlist.append(item_local.clone())
        
    if not item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global
        return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado_busqueda", title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + str(post_num) + " de " + str(total_pag), thumbnail=get_thumb("next.png"), title_lista=title_lista, cnt_pag=cnt_pag))
                                   
    #logger.debug("Titulos: " + str(len(itemlist)) + " Matches: " + str(len(matches)) + " Post: " + str(item.post) + " / " + str(post_actual) + " / " + str(total_pag))

    return itemlist

def findvideos(item):
    from core import channeltools
    logger.info()
    itemlist = []
    
    # Cualquiera de las tres opciones son válidas
    # item.url = item.url.replace(".com/",".com/ver-online/")
    # item.url = item.url.replace(".com/",".com/descarga-directa/")
    item.url = item.url.replace(".com/", ".com/descarga-torrent/")
    
    #Función para limitar la verificación de enlaces de Servidores para Ver online y Descargas
    try:
        #Inicializamos las variables por si hay un error en medio del proceso
        channel_exclude = []
        ver_enlaces = []
        ver_enlaces_veronline = -1                  #Ver todos los enlaces Ver Online
        verificar_enlaces_veronline = -1            #Verificar todos los enlaces Ver Online
        verificar_enlaces_veronline_validos = True  #"¿Contar sólo enlaces 'verificados' en Ver Online?"
        excluir_enlaces_veronline = []              #Lista vacía de servidores excluidos en Ver Online
        ver_enlaces_descargas = 0                   #Ver todos los enlaces Descargar
        verificar_enlaces_descargas = -1            #Verificar todos los enlaces Descargar
        verificar_enlaces_descargas_validos = True  #"¿Contar sólo enlaces 'verificados' en Descargar?"
        excluir_enlaces_descargas = []              #Lista vacía de servidores excluidos en Descargar
        
        #Leemos las opciones de permitir Servidores para Ver Online y Descargas
        #Cargamos en .json del canal para ver las listas de valores en  settings
        channel_exclude = channeltools.get_channel_json(item.channel)
        for settings in channel_exclude['settings']:                                #Se recorren todos los settings
            if settings['id'] == "clonenewpct1_excluir1_enlaces_veronline":         #lista de enlaces a excluir
                max_excl = int(settings['max_excl'])                                #Máximo número de servidores excluidos
                channel_exclude = settings['lvalues']                               #Cargamos la lista de servidores
            if settings['id'] == "clonenewpct1_ver_enlaces_descargas":              #Número de enlances a ver o verificar
                ver_enlaces = settings['lvalues']                                   #Cargamos la lista de num. de enlaces
    
        #Primer loop para enlaces de Ver Online.  
        #Carga la variable de ver
        ver_enlaces_veronline = int(config.get_setting("clonenewpct1_ver_enlaces_veronline", item.channel))
        if ver_enlaces_veronline == 1:      #a "Todos" le damos valor -1.  Para "No" dejamos 0
            ver_enlaces_veronline = -1
        if ver_enlaces_veronline > 1:       #para los demás valores, tomamos los de la lista
            ver_enlaces_veronline = int(ver_enlaces[ver_enlaces_veronline])
    
        #Carga la variable de verificar
        verificar_enlaces_veronline = int(config.get_setting("clonenewpct1_verificar_enlaces_veronline", item.channel))
        if verificar_enlaces_veronline == 1:        #a "Todos" le damos valor -1.  Para "No" dejamos 0
            verificar_enlaces_veronline = -1
        if verificar_enlaces_veronline > 1:         #para los demás valores, tomamos los de la lista
            verificar_enlaces_veronline = int(ver_enlaces[verificar_enlaces_veronline])

        #Carga la variable de contar sólo los servidores verificados
        verificar_enlaces_veronline_validos = int(config.get_setting("clonenewpct1_verificar_enlaces_veronline_validos", item.channel))

        #Carga la variable de lista de servidores excluidos
        x = 1
        for x in range(1, max_excl+1):          #recorremos todas las opciones de canales exluidos
            valor = str(config.get_setting("clonenewpct1_excluir%s_enlaces_veronline" % x, item.channel))
            valor = int(valor)
            if valor > 0:       #Evitamos "No"
                excluir_enlaces_veronline += [channel_exclude[valor]]       #Añadimos el nombre de servidor excluido a la lista
            x += 1

        #Segundo loop para enlaces de Descargar.  
        #Carga la variable de ver
        ver_enlaces_descargas = int(config.get_setting("clonenewpct1_ver_enlaces_descargas", item.channel))
        if ver_enlaces_descargas == 1:      #a "Todos" le damos valor -1.  Para "No" dejamos 0
            ver_enlaces_descargas = -1
        if ver_enlaces_descargas > 1:       #para los demás valores, tomamos los de la lista
            ver_enlaces_descargas = int(ver_enlaces[ver_enlaces_descargas])
    
        #Carga la variable de verificar
        verificar_enlaces_descargas = int(config.get_setting("clonenewpct1_verificar_enlaces_descargas", item.channel))
        if verificar_enlaces_descargas == 1:    #a "Todos" le damos valor -1.  Para "No" dejamos 0
            verificar_enlaces_descargas = -1
        if verificar_enlaces_descargas > 1:     #para los demás valores, tomamos los de la lista
            verificar_enlaces_descargas = int(ver_enlaces[verificar_enlaces_descargas])

        #Carga la variable de contar sólo los servidores verificados
        verificar_enlaces_descargas_validos = int(config.get_setting("clonenewpct1_verificar_enlaces_descargas_validos", item.channel))

        #Carga la variable de lista de servidores excluidos
        x = 1
        for x in range(1, max_excl+1):      #recorremos todas las opciones de canales exluidos
            valor = str(config.get_setting("clonenewpct1_excluir%s_enlaces_descargas" % x, item.channel))
            valor = int(valor)
            if valor > 0:       #Evitamos "No"
                excluir_enlaces_descargas += [channel_exclude[valor]]       #Añadimos el nombre de servidor excluido a la lista
            x += 1

    except Exception, ex:           #En caso de error, lo mostramos y reseteamos todas las variables
        logger.error("Error en la lectura de parámentros del .json del canal: " + item.channel + " \n%s" % ex)
        #Mostrar los errores
        logger.error(ver_enlaces_veronline)
        logger.error(verificar_enlaces_veronline)
        logger.error(verificar_enlaces_veronline_validos)
        logger.error(excluir_enlaces_veronline)
        logger.error(ver_enlaces_descargas)
        logger.error(verificar_enlaces_descargas)
        logger.error(verificar_enlaces_descargas_validos)
        logger.error(excluir_enlaces_descargas)
        #Resetear las variables a sus valores por defecto
        ver_enlaces_veronline = -1                  #Ver todos los enlaces Ver Online
        verificar_enlaces_veronline = -1            #Verificar todos los enlaces Ver Online
        verificar_enlaces_veronline_validos = True  #"¿Contar sólo enlaces 'verificados' en Ver Online?"
        excluir_enlaces_veronline = []              #Lista vacía de servidores excluidos en Ver Online
        ver_enlaces_descargas = 0                   #Ver todos los enlaces Descargar
        verificar_enlaces_descargas = -1            #Verificar todos los enlaces Descargar
        verificar_enlaces_descargas_validos = True  #"¿Contar sólo enlaces 'verificados' en Descargar?"
        excluir_enlaces_descargas = []              #Lista vacía de servidores excluidos en Descargar
    
    # Descarga la página
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("$!", "#!").replace("'", "\"").replace("Ã±", "ñ").replace("//pictures", "/pictures")

    #Añadimos el tamaño para todos
    size = scrapertools.find_single_match(data, '<div class="entry-left".*?><a href=".*?span class=.*?>Size:<\/strong>?\s(\d+?\.?\d*?\s\w[b|B])<\/span>')
    size = size.replace(".", ",")       #sustituimos . por , porque Unify lo borra
    if not size:
        size = scrapertools.find_single_match(item.quality, '\s\[(\d+,?\d*?\s\w[b|B])\]')
    else:
        item.title = re.sub(r'\s\[\d+,?\d*?\s\w[b|B]\]', '', item.title)    #Quitamos size de título, si lo traía
        item.title = '%s [%s]' % (item.title, size)                         #Agregamos size al final del título
    item.quality = re.sub(r'\s\[\d+,?\d*?\s\w[b|B]\]', '', item.quality)    #Quitamos size de calidad, si lo traía
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Generamos una copia de Item para trabajar sobre ella
    item_local = item.clone()
    
    # obtenemos la url torrent
    patron = 'class="btn-torrent">.*?window.location.href = "(.*?)";'
    item_local.url = scrapertools.find_single_match(data, patron)
    if not item_local.url:                             #error
        logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    item_local.url = item_local.url.replace(" ", "%20")             #sustituimos espacios por %20, por si acaso
    #logger.debug("Patron: " + patron + " url: " + item_local.url)
    #logger.debug(data)

    #Ahora pintamos el link del Torrent, si lo hay
    if item_local.url:		# Hay Torrent ?
        item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))        #Preparamos título de Torrent
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip() #Quitamos etiquetas vacías
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title).strip() #Quitamos colores vacíos
        item_local.alive = "??"             #Calidad del link sin verificar
        item_local.action = "play"          #Visualizar vídeo
        item_local.server = "torrent"       #Servidor
        if size:
            quality = '%s [%s]' % (item_local.quality, size)        #Agregamos size al final del título
        else:
            quality = item_local.quality
        
        itemlist.append(item_local.clone(quality=quality))          #Pintar pantalla
    
    logger.debug("TORRENT: " + item_local.url + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + size + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
    #logger.debug(item_local)

    # VER vídeos, descargar vídeos un link,  o múltiples links
    host_dom = host.replace("https://", "").replace("http://", "").replace("www.", "")
    data = data.replace("http://tumejorserie.com/descargar/url_encript.php?link=", "(")
    data = re.sub(r'javascript:;" onClick="popup\("http:\/\/(?:www.)?' + host_dom + '\w{1,9}\/library\/include\/ajax\/get_modallinks.php\?links=', "", data)

    # Nuevo sistema de scrapeo de servidores creado por Torrentlocula, compatible con otros clones de Newpct1
    patron = '<div class=\"box1\"[^<]+<img src=\"([^<]+)?" style[^<]+><\/div[^<]+<div class="box2">([^<]+)?<\/div[^<]+<div class="box3">([^<]+)?'
    patron += '<\/div[^<]+<div class="box4">([^<]+)?<\/div[^<]+<div class="box5"><a href=(.*?)? rel.*?'
    patron += '<\/div[^<]+<div class="box6">([^<]+)?<'

    enlaces_ver = re.compile(patron, re.DOTALL).findall(data)
    enlaces_descargar = enlaces_ver
    #logger.debug(enlaces_ver)

    #Recorre todos los links de VER, si está permitido
    cnt_enl_ver = 1
    cnt_enl_verif = 1
    for logo, servidor, idioma, calidad, enlace, title in enlaces_ver:
        if ver_enlaces_veronline == 0:      #Si no se quiere Ver Online, se sale del bloque
            break
        if "ver" in title.lower():
            servidor = servidor.replace("streamin", "streaminto")

            if servidor.capitalize() in excluir_enlaces_veronline:       #Servidor excluido, pasamos al siguiente
                continue
            mostrar_server = True
            if config.get_setting("hidepremium"):       #Si no se aceptan servidore premium, se ignoran
                mostrar_server = servertools.is_server_enabled(servidor)
                
            #logger.debug("VER: url: " + enlace + " / title: " + title + " / servidor: " + servidor + " / idioma: " + idioma)
            
            #Si el servidor es válido, se comprueban si los links están activos
            if mostrar_server:
                try:
                    if cnt_enl_ver <= ver_enlaces_veronline or ver_enlaces_veronline == -1:
                        devuelve = servertools.findvideosbyserver(enlace, servidor)     #existe el link ?
                        if verificar_enlaces_veronline == 0:
                            cnt_enl_ver += 1
                    else:
                        break       #Si se ha agotado el contador de verificación, se sale de Ver Online
                    
                    if devuelve:                                    #Hay link
                        enlace = devuelve[0][1]                     #Se guarda el link
                        item_local.alive = "??"                     #Se asume poe defecto que es link es dudoso
                        if verificar_enlaces_veronline != 0:        #Se quiere verificar si el link está activo?
                            if cnt_enl_verif <= verificar_enlaces_veronline or verificar_enlaces_veronline == -1: #contador?
                                #Llama a la subfunción de check_list_links(itemlist) para cada link de servidor
                                item_local.alive = servertools.check_video_link(enlace, servidor)       #activo el link ?
                                if verificar_enlaces_veronline_validos:     #Los links tienen que ser válidos para contarlos?
                                    if item_local.alive == "Ok":            #Sí
                                        cnt_enl_verif += 1                      #Movemos los contadores
                                        cnt_enl_ver += 1                        #Movemos los contadores
                                else:                                       #Si no es necesario que sean links válidos, sumamos
                                    cnt_enl_verif += 1                          #Movemos los contadores
                                    cnt_enl_ver += 1                            #Movemos los contadores
                            else:
                                break       #Si se ha agotado el contador de verificación, se sale de Ver Online

                        #Si el link no está activo se ignora
                        if item_local.alive == "??":        #dudoso
                            item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), item_local.quality, str(item_local.language))
                        elif item_local.alive.lower() == "no":      #No está activo.  Lo preparo, pero no lo pinto
                            item_local.title = '[COLOR red][%s][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.alive, servidor.capitalize(), item_local.quality, str(item_local.language))
                            logger.debug(item_local.alive + ": ALIVE / " + title + " / " + servidor + " / " + enlace)
                            raise
                        else:               #Sí está activo
                            item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), item_local.quality, str(item_local.language))

                        #Preparamos el resto de variables de Item para ver los vídeos en directo    
                        item_local.action = "play"
                        item_local.server = servidor
                        item_local.url = enlace
                        item_local.title = item_local.title.replace("[]", "").strip()
                        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip()
                        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title).strip()
                        itemlist.append(item_local.clone())
                except:
                    pass

    #Ahora vemos los enlaces de DESCARGAR
    if len(enlaces_descargar) > 0 and ver_enlaces_descargas != 0:
        
        #Pintamos un pseudo-título de Descargas
        if not item.unify:                  #Si Titulos Inteligentes NO seleccionados:
            itemlist.append(item_local.clone(title="[COLOR gold]**- Enlaces Descargar: -**[/COLOR]", action=""))
        else:
            itemlist.append(item_local.clone(title="[COLOR gold] Enlaces Descargar: [/COLOR]", action=""))

    #Recorre todos los links de DESCARGAR
    cnt_enl_ver = 1
    cnt_enl_verif = 1
    for logo, servidor, idioma, calidad, enlace, title in enlaces_descargar:
        if ver_enlaces_descargas == 0:
            break

        if "Ver" not in title:
            servidor = servidor.replace("uploaded", "uploadedto")
            partes = enlace.split(" ")      #Partimos el enlace en cada link de las partes
            title = "Descarga"              #Usamos la palabra reservada de Unify para que no formatee el título

            if servidor.capitalize() in excluir_enlaces_descargas:       #Servidor excluido, pasamos al siguiente
                continue
            
            #logger.debug("DESCARGAR: url: " + enlace + " / title: " + title + title + " / servidor: " + servidor + " / idioma: " + idioma)
            
            #Recorremos cada una de las partes.  Vemos si el primer link está activo.  Si no lo está ignoramos todo el enlace
            p = 1
            for enlace in partes:
                if not item.unify:         #Si titles Inteligentes NO seleccionados:
                    parte_title = "[COLOR yellow][%s][/COLOR] %s (%s/%s) [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]" % (servidor.capitalize(), title, p, len(partes), item_local.quality, str(item_local.language))
                else:
                    parte_title = "[COLOR yellow]%s-[/COLOR] %s %s/%s [COLOR limegreen]-%s[/COLOR] [COLOR red]-%s[/COLOR]" % (servidor.capitalize(), title, p, len(partes), item_local.quality, str(item_local.language))
                p += 1
                mostrar_server = True
                if config.get_setting("hidepremium"):       #Si no se aceptan servidore premium, se ignoran
                    mostrar_server = servertools.is_server_enabled(servidor)

                #Si el servidor es válido, se comprueban si los links están activos
                if mostrar_server:
                    try:
                        if cnt_enl_ver <= ver_enlaces_descargas or ver_enlaces_descargas == -1:
                            devuelve = servertools.findvideosbyserver(enlace, servidor)     #activo el link ?
                            if verificar_enlaces_descargas == 0:
                                cnt_enl_ver += 1
                        else:
                            ver_enlaces_descargas = 0       #FORZAR SALIR de DESCARGAS
                            break       #Si se ha agotado el contador de verificación, se sale de "Enlace"

                        if devuelve:
                            enlace = devuelve[0][1]
                            
                            #Verifica si está activo el primer link.  Si no lo está se ignora el enlace-servidor entero
                            if p <= 2:
                                item_local.alive = "??"                     #Se asume poe defecto que es link es dudoso
                                if verificar_enlaces_descargas != 0:        #Se quiere verificar si el link está activo?
                                    if cnt_enl_verif <= verificar_enlaces_descargas or verificar_enlaces_descargas == -1: #contador?
                                        #Llama a la subfunción de check_list_links(itemlist) para primer link de servidor
                                        item_local.alive = servertools.check_video_link(enlace, servidor)  #activo el link ?
                                        if verificar_enlaces_descargas_validos:     #Los links tienen que ser válidos para contarlos?
                                            if item_local.alive == "Ok":    #Sí
                                                cnt_enl_verif += 1              #Movemos los contadores
                                                cnt_enl_ver += 1                #Movemos los contadores
                                        else:                           #Si no es necesario que sean links válidos, sumamos
                                            cnt_enl_verif += 1                  #Movemos los contadores
                                            cnt_enl_ver += 1                    #Movemos los contadores
                                    else:
                                        ver_enlaces_descargas = 0               #FORZAR SALIR de DESCARGAS
                                        break       #Si se ha agotado el contador de verificación, se sale de "Enlace"
                                
                                if item_local.alive == "??":        #dudoso
                                    if not item.unify:         #Si titles Inteligentes NO seleccionados:
                                        parte_title = '[COLOR yellow][?][/COLOR] %s' % (parte_title)
                                    else:
                                        parte_title = '[COLOR yellow]%s[/COLOR]-%s' % (item_local.alive, parte_title)
                                elif item_local.alive.lower() == "no":       #No está activo.  Lo preparo, pero no lo pinto
                                    if not item.unify:         #Si titles Inteligentes NO seleccionados:
                                        parte_title = '[COLOR red][%s][/COLOR] %s' % (item_local.alive, parte_title)
                                    else:
                                        parte_title = '[COLOR red]%s[/COLOR]-%s' % (item_local.alive, parte_title)
                                    logger.debug(item_local.alive + ": ALIVE / " + title + " / " + servidor + " / " + enlace)
                                    break

                            #Preparamos el resto de variables de Item para descargar los vídeos
                            item_local.action = "play"
                            item_local.server = servidor
                            item_local.url = enlace
                            item_local.title = parte_title.replace("[]", "").strip()
                            item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip()
                            item_local.title = re.sub(r'\[COLOR \w+\]-\[\/COLOR\]', '', item_local.title).strip()
                            itemlist.append(item_local.clone())
                    except:
                        pass
                    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    max_temp = 1
    y = []
    if modo_ultima_temp and item.library_playcounts:         #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)
    
    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    if not item.infoLabels['tmdb_id']:
        tmdb.set_infoLabels(item, True)
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    except:                                                                             #Algún error de proceso, salimos
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    #Busca y pre-carga todas las páginas de episodios que componen las serie, para obtener la url de cada página
    pattern = '<ul class="%s">(.*?)</ul>' % "pagination"  # item.pattern
    pagination = scrapertools.find_single_match(data, pattern)
    if pagination:
        if "/pg/" in item.url:
            act_page = int(scrapertools.find_single_match(item.url, r'\/pg\/(\d+)'))    #Num página actual
        else:
            act_page = 1
        pattern = '<li><a href="([^"]+)">Last<\/a>'                                 #Busca última página
        full_url = scrapertools.find_single_match(pagination, pattern)
        url, last_page = scrapertools.find_single_match(full_url, r'(.*?\/pg\/)(\d+)')
        last_page = int(last_page)
        list_pages = [item.url]
        for x in range(act_page + 1, last_page + 1):   #carga cada página para obtener la url de la siguiente
            #LAS SIGUIENTES 3 LINEAS ANULADAS: no es necesario leer la pagína siguiente. Se supone que está activa
            #response = httptools.downloadpage('%s%s'% (url,x))
            #if response.sucess:
            #    list_pages.append("%s%s" % (url, x))    #Guarda la url de la siguiente página en una lista
            list_pages.append("%s%s" % (url, x))    #Guarda la url de la siguiente página en una lista
    else:
        list_pages = [item.url]

    season = max_temp
    if item.library_playcounts or item.tmdb_stat:       #Comprobamos si realmente sabemos el num. máximo de temporadas
        num_temporadas_flag = True
    else:
        num_temporadas_flag = False
    for page in list_pages:         #Recorre la lista de páginas
        if not list_pages:
            break
        try:
            if not data:
                data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(page).data)
            data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
            data = data.replace("chapters", "buscar-list")   #Compatibilidad con mispelisy.series.com
            pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"  # item.pattern
            data = scrapertools.get_match(data, pattern)
            if not data:
                raise
        except:
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + pattern + " / " + str(list_pages) + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        if "pelisyseries.com" in host:
            pattern = '<li[^>]*><div class.*?src="(?P<thumb>[^"]+)?".*?<a class.*?href="(?P<url>[^"]+).*?<h3[^>]+>(?P<info>.*?)?<\/h3>.*?<\/li>'
        else:
            pattern = '<li[^>]*><a href="(?P<url>[^"]+).*?<img.*?src="(?P<thumb>[^"]+)?".*?<h2[^>]+>(?P<info>.*?)?<\/h2>'
        matches = re.compile(pattern, re.DOTALL).findall(data)
        if not matches:                             #error
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + pattern + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("patron: " + pattern)
        #logger.debug(matches)    
        
        #Empezamos a generar cada episodio
        for url, thumb, info in matches:
            if "pelisyseries.com" in host:  #En esta web están en diferente orden
                interm = url
                url = thumb
                thumb = interm
            
            item_local = item.clone()       #Creamos copia local de Item por episodio
            item_local.url = url
            item_local.contentThumbnail = thumb
            estado = True                   #Buena calidad de datos por defecto

            if "<span" in info:  # new style
                pattern = ".*?[^>]+>.*?Temporada\s*(?P<season>\d+)?.*?Capitulo(?:s)?\s*(?P<episode>\d+)?" \
                          "(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)?<\/span>\s*Calidad\s*<span[^>]+>" \
                          "[\[]\s*(?P<quality>.*?)?\s*[\]]<\/span>"
                if "Especial" in info: # Capitulos Especiales
                    pattern = ".*?[^>]+>.*?Temporada.*?\[.*?(?P<season>\d+).*?\].*?Capitulo.*?\[\s*(?P<episode>\d+).*?\]?(?:.*?(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)?<\/span>\s*Calidad\s*<span[^>]+>[\[]\s*(?P<quality>.*?)?\s*[\]]<\/span>"
                
                if not scrapertools.find_single_match(info, pattern):   #en caso de error de formato, creo uno básico
                    logger.debug("patron episodioNEW: " + pattern)
                    logger.debug(info)
                    logger.debug(item_local.url)
                    info = '><strong>%sTemporada %s Capitulo 0</strong> - <span >Español Castellano</span> Calidad <span >[%s]</span>' % (item_local.contentSerieName, season, item_local.quality)

            else:  # old style.  Se intenta buscar un patrón que encaje con los diversos formatos antiguos.  Si no, se crea
                pattern = '\[(?P<quality>.*?)\]\[Cap.(?P<season>\d).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?\].*?(?P<lang>.*)?'        #Patrón básico por defecto

                if scrapertools.find_single_match(info, '\[\d{3}\]'):
                    info = re.sub(r'\[(\d{3}\])', r'[Cap.\1', info)
                elif scrapertools.find_single_match(info, 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<lang>\w+)\]?'):
                    pattern = 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<lang>\w+)\]?'
                elif scrapertools.find_single_match(info, '\[Cap.\d{2}_\d{2}\]'):
                    info = re.sub(r'\[Cap.(\d{2})_(\d{2})\]', r'[Cap.1\1_1\2]', info)
                elif scrapertools.find_single_match(info, '\[Cap.([A-Za-z]+)\]'):
                    info = re.sub(r'\[Cap.([A-Za-z]+)\]', '[Cap.100]', info)
                elif "completa" in info.lower():
                    info = info.replace("COMPLETA", "Caps. 01_99")
                    pattern = 'Temp.*?(?P<season>\d+).*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<quality>.*?)\].*?\[(?P<lang>\w+)\]?'
                if scrapertools.find_single_match(info, '\[Cap.\d{2,3}'):
                    pattern = "\[(?P<quality>.*?)\].*?\[Cap.(?P<season>\d).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)" \
                          "(?P<episode2>\d{2}))?.*?\].*?(?:\[(?P<lang>.*?)\])?"
                elif scrapertools.find_single_match(info, 'Cap.\d{2,3}'):
                    pattern = ".*?Temp.*?\s(?P<quality>.*?)\s.*?Cap.(?P<season>\d).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?\s(?P<lang>.*)?"
                elif scrapertools.find_single_match(info, '(?P<quality>.*?)?(?P<season>\d)[x|X|\.](?P<episode>\d{2})\s?(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?(?P<lang>.*)?'):
                    pattern = "(?P<quality>.*?)?(?P<season>\d)[x|X|\.](?P<episode>\d{2})\s?(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?(?P<lang>.*)?"
                    estado = False      #Mala calidad de datos
                if not scrapertools.find_single_match(info, pattern):   #en caso de error de formato, creo uno básico
                    logger.debug("patron episodioOLD: " + pattern)
                    logger.debug(info)
                    logger.debug(item_local.url)
                    info = '%s - Temp.%s [%s][Cap.%s00][Spanish]' % (item_local.contentSerieName, season, item_local.quality, season)
                    estado = False      #Mala calidad de datos
            
            r = re.compile(pattern)
            match = [m.groupdict() for m in r.finditer(info)][0]
            if not match:                             #error
                logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + pattern + " / DATA: " + info)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

            if match['season'] is None: match['season'] = season    #Si no se encuentran valores, pero poner lo básico
            if match['episode'] is None: match['episode'] = "0"
            try:
                match['season'] = int(match['season'])
                match['episode'] = int(match['episode'])
            except:
                logger.error("ERROR 07: EPISODIOS: Error en número de Temporada o Episodio: " + " / TEMPORADA/EPISODIO: " + str(match['season']) + " / " + str(match['episode']) + " / NUM_TEMPORADA: " + str(max_temp) + " / " + str(season) + " / MATCHES: " + str(matches))

            #logger.error("TEMPORADA: " + str(match['season']) + " / " + str(match['episode']) + " / " + str(match['episode2']) + " / NUM_TEMPORADA: " + str(max_temp) + " / " + str(season) + " / PATRON: " + pattern)
            if num_temporadas_flag and match['season'] != season and match['season'] > max_temp + 1:
                #Si el num de temporada está fuera de control, se trata pone en num. de temporada actual
                #logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(match['season']) + " / " + str(match['episode']) + " / NUM_TEMPORADA: " + str(max_temp) + " / " + str(season) + " / PATRON: " + pattern + " / MATCHES: " + str(matches))
                #logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(match['season']) + " / " + str(match['episode']) + " / NUM_TEMPORADA: " + str(max_temp) + " / " + str(season) + " / PATRON: " + pattern)
                match['season'] = season
                item_local.contentSeason = season
            else:
                item_local.contentSeason = match['season']
                season = match['season']
                if match['episode'] > 0:
                    num_temporadas_flag = True
                if season > max_temp:
                    max_temp = season
                    
            if match['quality'] and not item_local.quality and estado == True:
                item_local.quality = match['quality']       #Si hay quality se coge, si no, la de la serie
                item_local.quality = item_local.quality.replace("ALTA DEFINICION", "HDTV")
            
            if match['lang'] and estado == False:
                match['lang'] = match['lang'].replace("- ", "")
                item_local.infoLabels['episodio_titulo'] = match['lang']
                item_local.infoLabels['title'] = item_local.infoLabels['episodio_titulo']

            item_local.contentEpisodeNumber = match['episode']
            
            if match['episode'] == 0: match['episode'] = 1      #Evitar errores en Videoteca
            if match["episode2"]:       #Hay episodio dos? es una entrada múltiple?
                item_local.title = "%sx%s al %s -" % (str(match["season"]), str(match["episode"]).zfill(2), str(match["episode2"]).zfill(2))            #Creamos un título con el rango de episodios
            else:                   #Si es un solo episodio, se formatea ya
                item_local.title = "%sx%s -" % (match["season"], str(match["episode"]).zfill(2))
            
            if modo_ultima_temp and item.library_playcounts:        #Si solo se actualiza la última temporada de Videoteca
                if item_local.contentSeason < max_temp:
                    list_pages = []         #Sale del bucle de leer páginas
                    break                   #Sale del bucle actual del FOR de episodios por página
                #if ('%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))) in item.library_playcounts:
                #    continue
                    
            if item_local.active:
                del item_local.active
            if item_local.category:
                del item_local.category
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            item_local.context = "['buscar_trailer']"
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            item_local.extra = "episodios"
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
            
            itemlist.append(item_local.clone())
            
        data = ''

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
    
    item.title = "newest"
    item.category = "newest"
    item.action = "listado"
    item.channel = scrapertools.find_single_match(host, r'(\w+)\.com\/')
    
    try:
        if categoria == 'peliculas':
            item.url = host+'peliculas/'
            item.extra = "peliculas"
            itemlist = listado(item)
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()
                
        if categoria == 'series':
            item.url = host+'series/'
            item.extra = "series"
            itemlist.extend(listado(item))
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()
                
        if categoria == '4k':
            item.url = host+'peliculas-hd/4kultrahd/'
            item.extra = "peliculas"
            itemlist.extend(listado(item))
            if ">> Página siguiente" in itemlist[-1].title:
                 itemlist.pop()
                
        if categoria == 'anime':
            item.url = host+'anime/'
            item.extra = "peliculas"
            itemlist.extend(listado(item))
            if ">> Página siguiente" in itemlist[-1].title:
                 itemlist.pop()
                                 
        if categoria == 'documentales':
            item.url = host+'documentales/'
            item.extra = "varios"
            itemlist.extend(listado(item))
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()
                
        if categoria == 'latino':
            item.url = host+'peliculas-latino/'
            item.extra = "peliculas"
            itemlist.extend(listado(item))
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
