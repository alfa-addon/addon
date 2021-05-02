# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re
import time
import traceback

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from lib import generictools
from channels import filtertools
from channels import autoplay


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']

host = 'https://www.reinventorrent.com/'
domain = 'www.reinventorrent.com'
channel = 'madeintorrent'
categoria = channel.capitalize()

__modo_grafico__ = config.get_setting('modo_grafico', channel)
IDIOMAS_TMDB = {0: 'es', 1: 'en', 2: 'es,en'}
idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', channel)]    # Idioma base para TMDB
idioma_busqueda_VO = IDIOMAS_TMDB[2]                                                # Idioma para VO
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel) #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel) * 2
season_colapse = config.get_setting('season_colapse', channel)                  # Season colapse?
filter_languages = config.get_setting('filter_languages', channel)              # Filtrado de idiomas?


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_documentales = get_thumb("channels_documentary.png")

    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", 
                url=host, thumbnail=thumb_pelis, extra="peliculas"))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", 
                url=host, thumbnail=thumb_series, extra="series"))
    
    itemlist.append(Item(channel=item.channel, title="Documentales", action="listado", 
                url=host + "documentales.html", thumbnail=thumb_documentales, extra="documentales"))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host, thumbnail=thumb_buscar, extra="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                folder=False, thumbnail=thumb_separador))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)                                #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return


def submenu(item):
    logger.info()
    
    itemlist = []
    
    patron = '<li\s*class="*sp-menu-item[^>]*>\s*<a\s*href="*([^>]+)"*\s*>'
    patron += '(?:\s*<i\s*class="*fa\s*fa[^>]+>\s*<\/i>)?\s*([^<]+)<\/a>'

    data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout,  s2=False, 
                                          patron=patron, item=item, itemlist=[])    # Descargamos la página

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not success or itemlist:                                                 # Si ERROR o lista de errores ...
        return itemlist                                                         # ... Salimos
        
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    for scrapedurl, scrapedtitle in matches:
        if item.extra in scrapedurl:
            url = urlparse.urljoin(host, scrapedurl)
            title = scrapedtitle.capitalize().strip()
            if item.extra == title.lower():
                title += ' TOD@S'
            itemlist.append(item.clone(action="listado", title=title, url=url))
                        
    return itemlist


def listado(item):                                                              # Listado principal y de búsquedas
    logger.info()
    
    itemlist = []
    item.category = categoria
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    last_page_print = 1                                                         # Última página inicial, para píe de página
    page_factor = 1.0                                                           # Factor de conversión de pag. web a pag. Alfa
    search_lines = 30                                                           # Número de líneas por página web en search
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    if item.page_factor:
        page_factor = float(item.page_factor)                                   # Si viene de una pasada anterior, lo usamos
        del item.page_factor                                                    # ... y lo borramos
    if item.search_lines:
        search_lines = int(item.search_lines)                                   # Si viene de una pasada anterior, lo usamos
        del item.search_lines                                                   # ... y lo borramos
    if item.last_page_print:
        last_page_print = item.last_page_print                                  # Si viene de una pasada anterior, lo usamos
        del item.last_page_print                                                # ... y lo borramos
    
    cnt_tot = 30                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    if item.cnt_tot_match:
        cnt_tot_match = float(item.cnt_tot_match)                               # restauramos el contador TOTAL de líneas procesadas de matches
        del item.cnt_tot_match
    else:
        cnt_tot_match = 0.0                                                     # Contador TOTAL de líneas procesadas de matches
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                            # Después de este tiempo pintamos (segundos)
    timeout_search = timeout * 2                                                # Timeout para descargas
    if item.extra == 'search' and item.extra2 == 'episodios':                   # Si viene de episodio que quitan los límites
        cnt_tot = 999
        fin = inicio + 30

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                                        # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
    matches = []
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
        
    post = None
    if item.post:                                                               # Rescatamos el Post, si lo hay
        post = item.post
    
    next_page_url = item.url
    # Máximo num. de líneas permitidas por TMDB. Máx de 5 segundos por Itemlist para no degradar el rendimiento
    while (cnt_title < cnt_tot and curr_page <= last_page and fin > time.time()) or item.matches:
    
        # Descarga la página
        data = ''
        cnt_match = 0                                                           # Contador de líneas procesadas de matches
        
        if not item.matches:                                                    # si no viene de una pasada anterior, descargamos
            data, success, code, item, itemlist = generictools.downloadpage(next_page_url, 
                                          timeout=timeout_search, post=post, s2=False, 
                                          item=item, itemlist=itemlist)         # Descargamos la página)
            
            # Verificamos si se ha cargado una página correcta
            curr_page += 1                                                      # Apunto ya a la página siguiente
            if not data or not success:                                         # Si la web está caída salimos sin dar error
                if len(itemlist) > 1:                                           # Si hay algo que pintar lo pintamos 
                    last_page = 0
                    break
                
                logger.error("ERROR 01: LISTADO: La Web no responde o la URL es erronea ")
                itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: LISTADO:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log', 
                        folder=False))
                return itemlist                                                 # Si no hay nada más, salimos directamente
        
        if item.extra == 'search':
            #Patrón para búsquedas
            patron = '<div\s*id="*fgsdhkrhskhs"*\s*>\s*()<a\s*href="*([^>]+)"*\s*>\s*([^<]+)<\/a>(?:.*?<div\s*class="*fjewiqo"*>\s*([^<]+)<)?.*?<img.*?src="*((?:http|\/)[^"]+(?:\.jpg|\.png))"*(?:.*?<div\s*id=[^>]+>\s*([^<]*)<)?(?:.*?<i\s*class="*fa[^>]+><\/i>\s*([^<]+)<)?'
        else:
            #Patrón para pelis, series y documentales
            patron = 'data-index="*(\d*)"*>\s*<div\s*id="*[^>]+"*>\s*<a\s*href='
            patron += '"*([^>]+)"*\s*>\s*([^<]+)<\/a>\s*<\/div>(?:.*?<div\s*'
            patron += '(?:id="*mjikfdoia|class="*fjewiqo)"*>\s*([^<]+)<)?(?:.*?<div\s*class='
            patron += '"*ansias"*>\s*([^<]*)<)?.*?<img.*?src="*((?:http|\/)[^"]+(?:\.jpg|\.png))"*'
            patron += '.*?<div\s*id="*vfdsyydystyretg"*>\s*([^<]+)<\/div>'

        if not item.matches:                                                    # De pasada anterior?
            matches = re.compile(patron, re.DOTALL).findall(data)
        else:
            matches = item.matches
            del item.matches
            
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        if not matches and item.extra != 'search' and not item.extra2:          #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
            break                                                               #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        if not matches and item.extra == 'search':                              #búsqueda vacía
            if len(itemlist) > 0:                                               # Si hay algo que pintar lo pintamos
                last_page = 0
                break
            return itemlist                                                     #Salimos

        #Buscamos la última página
        if last_page == 99999:                                                  #Si es el valor inicial, buscamos
            if item.extra == 'search':
                patron_post = '(?i)"*\/component\/sjk2filter\/\?theme=[^>]+start=(\d+)[^>]*"*>\s*final\s*<\/a>'
                patron_page = '(?i)<div\s*class="*k2PaginationCounter"*[^>]*>\s*\S+gina\s*\d+\s*de\s*(\d+)\s*<\/div>'
                last_page = 1
                search_lines = len(matches)
                if scrapertools.find_single_match(data, patron_post):
                    search_lines = scrapertools.find_single_match(data, patron_post)
                    last_page = scrapertools.find_single_match(data, patron_page)
                    try:
                        search_lines = int(search_lines)
                        last_page = int(last_page)
                    except:
                        logger.error(traceback.format_exc())
                        last_page = 1
                        search_lines = len(matches)
                        last_page_print = int((float(len(matches)) / float(cnt_tot)) + 0.999999)
                last_page_print = int((float(search_lines) / float(cnt_tot)) + 0.999999)
            else:
                # Localizamos en número de widget para pedir más páginas, y lo ponemos como post
                patron_post = "option=com_minitekwall&task=masonry.getContent&widget_id=(\d+)"
                widget_num = scrapertools.find_single_match(data, patron_post)
                post = "option=com_minitekwall&task=masonry.getContent&widget_id=%s&grid=columns&page=1" % widget_num
                next_page_url = host + 'index.php'
                
                # Localizamos el número total de enlaces disponibles y lo dividimos por num máx de entradas para calcular el num total de páginas
                patron_last = '<h1\s*class="*itemTitle"*>\s*Categoria:[^\(]+\((\d+)\)\s*<\/h1>'
                try:
                    last_page = int((float(scrapertools.find_single_match(data, patron_last)) / float(cnt_tot)) + 0.999999)
                    #page_factor = float(len(matches)) / float(cnt_tot)
                except:                                                         #Si no lo encuentra, lo ponemos a 999
                    logger.error(traceback.format_exc())
                    last_page = 1
                    last_page_print = int((float(len(matches)) / float(cnt_tot)) + 0.999999)
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page) + ' / search_lines: ' + str(search_lines))
            
        #Buscamos la próxima página
        if item.extra != 'search':
            post = re.sub(r'page=\d+', 'page=%s' % str(curr_page), post)
        #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page) + \
        #            ' / last_page_print: ' + str(last_page_print) + ' / search_lines: ' + str(search_lines))
        
        #Empezamos el procesado de matches
        for index, scrapedurl, scrapedtitle, scrapedyear, _scrapedlanguage, _scrapedthumb, scrapedquality in matches:
            cnt_match += 1
            
            if item.extra == 'search':
                scrapedlanguage = _scrapedthumb
                scrapedthumb = _scrapedlanguage
            else:
                scrapedlanguage = _scrapedlanguage
                scrapedthumb = _scrapedthumb
            
            # Se eliminan enlaces que no sean pelis, series y documentales
            if item.extra == 'search':
                if '/pelicula' not in scrapedurl and '/serie' not in scrapedurl and '/documental' not in scrapedurl:
                    continue
            
            title = scrapedtitle
            title = scrapertools.remove_htmltags(title).rstrip('.')             # Removemos Tags del título
            url = scrapedurl

            title_subs = []                                                     #creamos una lista para guardar info importante
            
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&#8217;", "'")\
                    .replace("&amp;", "&")

            # Se filtran las entradas para evitar duplicados de Temporadas
            url_list = url
            if url_list in title_lista:                                         #Si ya hemos procesado el título, lo ignoramos
                continue
            else:
                title_lista += [url_list]                                       #la añadimos a la lista de títulos

            cnt_title += 1                                                      # Incrementamos el contador de entradas válidas
            
            item_local = item.clone()                                           #Creamos copia de Item para trabajar
            if item_local.tipo:                                                 #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            if item_local.post:
                del item_local.post
            item_local.extra2 = True
            del item_local.extra2
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
            
            # Después de un Search se restablecen las categorías
            if item_local.extra == 'search':
                if '/serie' in url or '/documental' in url:
                    item_local.extra = 'series'                                 # Serie búsqueda
                else:
                    item_local.extra = 'peliculas'                              # Película búsqueda

            # Procesamos idiomas
            language = scrapertools.remove_htmltags(scrapedlanguage).strip()
            item_local.language = []                                            #creamos lista para los idiomas
            if 'ntegrados' in language or 'Sub Forzados' in language or ('Sub' in language \
                    and not ('cast' in language.lower() or 'espa' in \
                    language.lower())) or 'V.O.' in language:
                item_local.language = ['VOS']                                   # añadimos VOS
            if 'cast' in language.lower() or ('espa' in language.lower() and not 'lat' in language.lower()): 
                item_local.language += ['CAST']                                 # añadimos CAST
            if 'lat' in language.lower(): 
                item_local.language += ['LAT']                                  # añadimos CAST
            if 'dual' in language.lower() or 'varios' in language.lower() or \
                        (('cast' in language.lower() or 'espa' in language.lower() \
                        or 'lat' in language.lower()) and 'ingl' in language.lower()):
                item_local.language += ['DUAL']                                 # añadimos DUAL
            if not item_local.language:
                item_local.language = ['CAST']                                  # [CAST] por defecto
                
            # Procesamos Calidad
            if scrapedquality:
                item_local.quality = scrapertools.remove_htmltags(scrapedquality).strip()       # iniciamos calidad
                if '3d' in scrapedquality.lower() and not '3d' in item_local.quality.lower():
                    item_local.quality += ', 3D'
            if not item_local.quality:
                item_local.quality = '720p'
                
            item_local.thumbnail = urlparse.urljoin(host, scrapedthumb)         #iniciamos thumbnail

            item_local.url = urlparse.urljoin(host, url)                        #guardamos la url final
            item_local.context = "['buscar_trailer']"                           #... y el contexto

            # Guardamos los formatos para peliculas, series y documentales
            if item_local.extra == 'peliculas' or 'peliculas' in item_local.url:
                # Guardamos los formatos para películas
                item_local.contentType = "movie"
                item_local.action = "findvideos"
            else:
                # Guardamos los formatos para series y documentales
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = season_colapse                      #Muestra las series agrupadas por temporadas?

            #Limpiamos el título de la basura innecesaria
            if item_local.contentType == "tvshow":
                title = scrapertools.find_single_match(title, '(^.*?)\s*(?:$|\(|\[|-)')

            title = re.sub(r'(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', '', title).strip()
            item_local.quality = re.sub(r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', 
                        '', item_local.quality).strip()

            #Analizamos el año.  Si no está claro ponemos '-'
            try:
                year = int(scrapertools.find_single_match(scrapedyear, '\d{4}'))
            except:
                year = '-'
            item_local.infoLabels["year"] = year
            title = re.sub('\(\d{4}\)', '', title).rstrip()
            
            #Terminamos de limpiar el título
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').replace('[4K]', '').replace('(4K)', '').strip().lower().title()
            item_local.from_title = title.strip().lower().title()           #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()
            
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
                
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" \
                        or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if filter_languages > 0:                                            #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                             #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                           # Recalculamos los items después del filtrado
            if cnt_title >= cnt_tot and (len(matches) - cnt_match) + cnt_title > cnt_tot * 1.3:     #Contador de líneas añadidas
                break
            
            #logger.debug(item_local)
    
        matches = matches[cnt_match:]                                           # Salvamos la entradas no procesadas
        cnt_tot_match += cnt_match                                              # Calcular el num. total de items mostrados
        
        #Buscamos la próxima página
        if item.extra == 'search':
            logger.error(cnt_tot_match)
            next_page_url = re.sub(r'start=\d+', 'start=%s' % str(int(cnt_tot_match)), next_page_url)
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__, idioma_busqueda=idioma_busqueda)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page or len(matches) > 0:
        curr_page_print = int(cnt_tot_match / float(cnt_tot))
        if curr_page_print < 1:
            curr_page_print = 1
        if last_page:
            if last_page > 1:
                last_page_print = int((last_page * page_factor) + 0.999999)
            title = '%s de %s' % (curr_page_print, last_page_print)
        else:
            title = '%s' % curr_page_print

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " 
                        + title, title_lista=title_lista, url=next_page_url, extra=item.extra, 
                        extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page), 
                        page_factor=str(page_factor), cnt_tot_match=str(cnt_tot_match), matches=matches, 
                        last_page_print=str(last_page_print), post=post, search_lines=str(search_lines)))

    return itemlist

    
def findvideos(item):
    logger.info()
    from core import filetools
    
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    matches = []
    data = ''
    code = 0
    
    #logger.debug(item)

    #Bajamos los datos de la página y seleccionamos el bloque
    patron = '<li>\s*<a\s*title="*[^"]+"*\s*href="*([^>]+)"*\s*>\s*([^<]+)<\/a>\s*<\/li>'
    
    if not item.matches:
        data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout, 
                                          s2=False, item=item, itemlist=[])     # Descargamos la página)

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if (not data and not item.matches) or code == 999:
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            if len(item.emergency_urls) > 1:
                matches = item.emergency_urls[1]                                #Restauramos matches de vídeos
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    if not item.armagedon:
        if not item.matches:
            matches = re.compile(patron, re.DOTALL).findall(data)
        else:
            matches = item.matches
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    if not matches:                                                             #error
        return itemlist

    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                                #Iniciamos emergency_urls
        item.emergency_urls.append([])                                          #Reservamos el espacio para los .torrents locales
        item.emergency_urls.append(matches)                                     #Salvamnos matches de los vídeos...  

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora tratamos los enlaces .torrent con las diferentes calidades
    for scrapedurl, info in matches:
        scrapedpassword = ''
        scrapedquality = info
        language = info

        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        item_local.url = urlparse.urljoin(host, scrapedurl)

        # Restauramos urls de emergencia si es necesario
        local_torr = ''
        if item.emergency_urls and not item.videolibray_emergency_urls:
            item_local.torrent_alt = item.emergency_urls[0][0]                  #Guardamos la url del .Torrent ALTERNATIVA
            if item.armagedon:
                item_local.url = item.emergency_urls[0][0]                      #Restauramos la url
                if item_local.url.startswith("\\") or item_local.url.startswith("/"):
                    if item.contentType == 'movie':
                        FOLDER = config.get_setting("folder_movies")
                    else:
                        FOLDER = config.get_setting("folder_tvshows")
                    local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
            if len(item.emergency_urls[0]) > 1:
                del item.emergency_urls[0][0]
        
        # Procesamos la calidad
        if len(matches) == 1:
            item_local.quality = item.quality
        else:
            if item_local.contentType == 'movie':
                patron_q = '(?:\[|\(|\-\s*)([^\)]+)(?:\]|\)|\s*\-)'
            else:
                patron_q = '(?:\[|\(|\-\s*)(HD[^\)]+)(?:\]|\)|\s*\-)'
            patron_al = '(.*?\d+x\d+\s*(?:al\s*(?:\d+x)?\d+\s*)?)'
            if not scrapertools.find_single_match(scrapedquality, patron_q):
                scrapedquality = item.quality
                patron_q = ''
            if patron_q:
                scrapedquality = scrapertools.find_single_match(scrapedquality, patron_q)
                scrapedquality = re.sub(patron_al, '', scrapedquality)          # Quitamos basura del título
            item_local.quality = scrapedquality                                 # Copiamos la calidad
            if '3D' in item.quality and not '3D' in item_local.quality:
                item_local.quality = '3D ' + item_local.quality

        # Procesamos idiomas
        item_local.language = []                                                #creamos lista para los idiomas
        if len(matches) == 1:
            item_local.language = item.language
        else:
            if 'ntegrados' in language or 'Sub Forzados' in language or ('Sub' in language \
                        and not ('cast' in language.lower() or 'espa' in \
                        language.lower())) or 'V.O.' in language:
                item_local.language = ['VOS']                                   # añadimos VOS
            if 'cast' in language.lower() or ('espa' in language.lower() and not 'lat' in language.lower()): 
                item_local.language += ['CAST']                                 # añadimos CAST
            if 'lat' in language.lower(): 
                item_local.language += ['LAT']                                  # añadimos CAST
            if 'dual' in language.lower() or 'varios' in language.lower() or \
                        (('cast' in language.lower() or 'espa' in language.lower() \
                        or 'lat' in language.lower()) and 'ingl' in language.lower()):
                item_local.language += ['DUAL']                                 # añadimos DUAL
            if not item_local.language:
                item_local.language = item.language                             # por defecto el original
        
        #Buscamos tamaño en el archivo .torrent
        size = ''
        if item_local.torrent_info:
            size = item_local.torrent_info
        if not size and not item.videolibray_emergency_urls and not item_local.url.startswith('magnet:'):
            if not item.armagedon:
                size = generictools.get_torrent_size(item_local.url, local_torr=local_torr) #Buscamos el tamaño en el .torrent desde la web
                if 'ERROR' in size and item.emergency_urls and not item.videolibray_emergency_urls:
                    item_local.armagedon = True
                    item_local.url = item.emergency_urls[0][0]                      #Restauramos la url
                    local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
                    size = generictools.get_torrent_size(item_local.url, local_torr=local_torr) #Buscamos el tamaño en el .torrent emergencia
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s, ' % size                             #Agregamos size
        if item_local.url.startswith('magnet:') and not 'Magnet' in item_local.torrent_info:
            item_local.torrent_info += ' Magnet'
        if item_local.torrent_info:
            item_local.torrent_info = item_local.torrent_info.strip().strip(',')
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info
        size = size.replace(',', '.')
        size = scrapertools.find_single_match(size, '\d+\.\d+')
        if not size: size = 0
        try:
            item_local.size = float(size)
            if 'M·B' in item_local.torrent_info:
                item_local.size = float(item_local.size / 1000)
        except:
            item_local.size = 0
   
        # Guadamos la password del RAR
        password = scrapedpassword
        # Si tiene contraseña, la guardamos y la pintamos
        if password or item.password:
            if not item.password: item.password = password
            item_local.password = item.password
            itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                        + item_local.password + "'", folder=False))
        
        # Guardamos urls de emergencia si se viene desde un Lookup de creación de Videoteca
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(item_local.url)                       #guardamos la url y nos vamos
            continue

        if item_local.armagedon:
            item_local.quality = '[COLOR hotpink][E][/COLOR] [COLOR limegreen]%s[/COLOR]' % item_local.quality
        
        #Ahora pintamos el link del Torrent
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language), \
                        item_local.torrent_info)
        
        #Preparamos título y calidad, quitando etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        
        if not size or 'Magnet' in size:
            item_local.alive = "??"                                             #Calidad del link sin verificar
        elif 'ERROR' in size and 'Pincha' in size:
            item_local.alive = "ok"                                             #link en error, CF challenge, Chrome disponible
        elif 'ERROR' in size and 'Introduce' in size:
            item_local.alive = "??"                                             #link en error, CF challenge, ruta de descarga no disponible
            item_local.channel = 'setting'
            item_local.action = 'setting_torrent'
            item_local.unify = False
            item_local.folder = False
            item_local.item_org = item.tourl()
        elif 'ERROR' in size:
            item_local.alive = "no"                                             #Calidad del link en error, CF challenge?
        else:
            item_local.alive = "ok"                                             #Calidad del link verificada
        if item_local.channel != 'setting':
            item_local.action = "play"                                          #Visualizar vídeo
            item_local.server = "torrent"                                       #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)

    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        return item                                                             #... nos vamos
    
    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        if len(itemlist_f) > 1:
            itemlist_f = sorted(itemlist_f, key=lambda it: int(it.size), reverse=True)      #clasificamos
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, 
                        title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))
        
        if len(itemlist_t) > 1:
            itemlist_t = sorted(itemlist_t, key=lambda it: int(it.size), reverse=True)      #clasificamos
        if len(itemlist_t) == 0:
            if len(itemlist) == 0 or (len(itemlist) > 0 and itemlist[-1].server != 'torrent'):
                return []
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist
    

def episodios(item):
    logger.info()
    
    itemlist = []
    item.category = categoria
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                 #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                 #... salvamos el num de sesión a pintar
            item.from_num_season_colapse = season_display
            del item.season_colapse
            item.contentType = "tvshow"
            if item.from_title_season_colapse:
                item.title = item.from_title_season_colapse
                del item.from_title_season_colapse
                if item.infoLabels['title']:
                    del item.infoLabels['title']
        del item.infoLabels['season']
    if item.contentEpisodeNumber:
        del item.infoLabels['episode']
    if season_display == 0 and item.from_num_season_colapse:
        season_display = item.from_num_season_colapse

    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    idioma = idioma_busqueda
    if 'VO' in str(item.language):
        idioma = idioma_busqueda_VO
    try:
        tmdb.set_infoLabels(item, True, idioma_busqueda=idioma)
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                                    #Si hay una migración de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    # Vemos la última temporada de TMDB y del .nfo
    max_temp = 1
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                        #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    # Si la series tiene solo una temporada, o se lista solo una temporada, guardamos la url y seguimos normalmente
    list_temp = []
    list_temp.append(item.url)

    # Descarga las páginas
    for url in list_temp:                                                       # Recorre todas las temporadas encontradas
        patron = '<li>\s*<a\s*title="*[^"]+"*\s*href="*([^>]+)"*\s*>\s*([^<]+)<\/a>\s*<\/li>'
        
        data, success, code, item, itemlist = generictools.downloadpage(url, timeout=timeout*2, s2=False, 
                                          patron=patron, item=item, itemlist=itemlist)  # Descargamos la página
        
        #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
        if not success:                                                         # Si ERROR o lista de errores ...
            itemlist.append(item.clone(action='', title=item.category + ': CODE: ' +
                             '[COLOR yellow]' + str(code) + '[/COLOR]: ERROR 01: EPISODIOS: ' + 
                             'La Web no responde o ha cambiado de URL'))
            return itemlist                                                     # ... Salimos

        matches_alt = re.compile(patron, re.DOTALL).findall(data)

        #logger.debug("PATRON: " + patron)
        #logger.debug(matches_alt)
        #logger.debug(data)
        
        # Ordenamos los episodios
        matches = []
        x = 0
        patron_cap = '(?i).*?((?:\()?)cap\S*\s*(\d{1})x'
        for scrapedurl, info in matches_alt:
            if scrapertools.find_single_match(info, patron_cap):
                try:
                    matches.append((scrapedurl, scrapertools.remove_htmltags(re.sub(patron_cap, r'\1cap. 0\2x' , info))))
                except:
                    matches.append((scrapedurl, scrapertools.remove_htmltags(info)))
            else:
                matches.append((scrapedurl, scrapertools.remove_htmltags(info)))
        matches = sorted(matches, key=lambda mt: mt[1])

        # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
        x = 0
        season_num = 1
        episode_num = 1
        for scrapedurl, info in matches:
            scrapedquality = info
            language = info
            scrapedsize = ''
            episode_al = ''
            
            item_local = item.clone()
            item_local.action = "findvideos"
            item_local.contentType = "episode"
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
            if item_local.channel_host:
                del item_local.channel_host
            if item_local.active:
                del item_local.active
            if item_local.contentTitle:
                del item_local.infoLabels['title']
            if item_local.season_colapse:
                del item_local.season_colapse

            item_local.url = urlparse.urljoin(host, scrapedurl)                 # Usamos las url de la temporada, no hay de episodio
            item_local.matches = []
            item_local.matches.append(matches[x])                               # Salvado Matches de cada episodio
            x += 1
            item_local.context = "['buscar_trailer']"
            if not item_local.infoLabels['poster_path']:
                item_local.thumbnail = item_local.infoLabels['thumbnail']
            
            # Extraemos números de temporada y episodio
            try:
                patron_num_tit = '.*?(\d+)x(\d+)\s*'
                patron_num_tit2 = '(?i).*?cap.?\s*(\d+)\s*'
                patron_num_url = '(?i)temp\w+a-(\d+)x(\d+)'
                if 'completa' in info:
                    episode_num = 1
                elif scrapertools.find_single_match(info, patron_num_tit):
                    season_num, episode_num = scrapertools.find_single_match(info, patron_num_tit)
                elif scrapertools.find_single_match(item_local.url, patron_num_url):
                    season_num, episode_num = scrapertools.find_single_match(item_local.url, patron_num_url)
                elif scrapertools.find_single_match(info, patron_num_tit2):
                    episode_num = scrapertools.find_single_match(info, patron_num_tit2)
            except:
                pass
            try:
                season_num = int(season_num)
                item_local.contentSeason = season_num
            except:
                item_local.contentSeason = 1
                season_num = item_local.contentSeason
            try:
                episode_num = int(episode_num)
                item_local.contentEpisodeNumber = episode_num
            except:
                item_local.contentEpisodeNumber = 0
                episode_num = item_local.contentEpisodeNumber
            episode_num += 1
            patron_al = '.*?\d+x\d+\s*al\s*(?:\d+x)?(\d+)'
            episode_al = scrapertools.find_single_match(info, patron_al)

            if episode_al:                                                      #Hay episodio dos? es una entrada múltiple?
                item_local.title = '%sx%s al %s -' % (str(item_local.contentSeason), \
                        str(item_local.contentEpisodeNumber).zfill(2), episode_al)      #Creamos un título con el rango de episodios
            else:                                                               #Si es un solo episodio, se formatea ya
                item_local.title = '%sx%s -' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2))
                        
            if season_display > 0:                                              # Son de la temporada estos episodios?
                if item_local.contentSeason > season_display:
                    break
                elif item_local.contentSeason < season_display:
                    continue
                    
            if modo_ultima_temp_alt and item.library_playcounts:                # Si solo se actualiza la última temporada de Videoteca
                if item_local.contentSeason < max_temp:
                    continue                                                    # Sale del bucle actual del FOR

            # Procesamos la calidad
            patron_q = '(?:\[|\(|\-\s*)(HD[^\)]+)(?:\]|\)|\s*\-)'
            patron_al = '(.*?\d+x\d+\s*(?:al\s*(?:\d+x)?\d+\s*)?)'
            if not scrapertools.find_single_match(scrapedquality, patron_q):
                scrapedquality = item.quality
                patron_q = ''
            if patron_q:
                scrapedquality = scrapertools.find_single_match(scrapedquality, patron_q)
                scrapedquality = re.sub(patron_al, '', scrapedquality)          # Quitamos basura del título
            item_local.quality = scrapedquality                                 # Copiamos la calidad
            if '3D' in item.quality and not '3D' in item_local.quality:
                item_local.quality = '3D ' + item_local.quality
            
            # Procesamos idiomas
            item_local.language = []                                            #creamos lista para los idiomas
            patron_l = '[\]|\)]\s*(.*?)$'
            if not scrapertools.find_single_match(language, patron_l):
                language = item.quality
                patron_l = ''
            if patron_l:
                language = scrapertools.find_single_match(language, patron_l)
                language = re.sub(r'(?i).?reparado.?', '', language).strip()
            if 'ntegrados' in language or 'Sub Forzados' in language or ('Sub' in language \
                        and not ('cast' in language.lower() or 'espa' in \
                        language.lower())) or 'V.O.' in language:
                item_local.language = ['VOS']                                   # añadimos VOS
            if 'cast' in language.lower() or ('espa' in language.lower() and not 'lat' in language.lower()): 
                item_local.language += ['CAST']                                 # añadimos CAST
            if 'lat' in language.lower(): 
                item_local.language += ['LAT']                                  # añadimos CAST
            if 'dual' in language.lower() or 'varios' in language.lower() or \
                        (('cast' in language.lower() or 'espa' in language.lower() \
                        or 'lat' in language.lower()) and 'ingl' in language.lower()):
                item_local.language += ['DUAL']                                 # añadimos DUAL
            if not item_local.language:
                item_local.language = item.language                             # por defecto el original
            
            # Comprobamos si hay más de un enlace por episodio, entonces los agrupamos
            if len(itemlist) > 0 and item_local.contentSeason == itemlist[-1].contentSeason \
                        and item_local.contentEpisodeNumber == itemlist[-1].contentEpisodeNumber \
                        and itemlist[-1].contentEpisodeNumber != 0:             # solo guardamos un episodio ...
                if itemlist[-1].quality:
                    if len(item_local.quality) < 5 or (item_local.quality not in itemlist[-1].quality):
                        itemlist[-1].quality += ", " + item_local.quality           # ... pero acumulamos las calidades
                else:
                    itemlist[-1].quality = item_local.quality
                if itemlist[-1].language:
                    if item_local.language[0] not in str(itemlist[-1].language):
                        itemlist[-1].language += item_local.language            # ... pero acumulamos idiomas
                else:
                    itemlist[-1].language = item_local.language
                if episode_al and not ' al ' in itemlist[-1].title:
                    itemlist[-1].title = item_local.title
                itemlist[-1].matches.append(item_local.matches[0])              # Salvado Matches en el episodio anterior
                continue                                                        # ignoramos el episodio duplicado

            itemlist.append(item_local.clone())

            #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True, idioma_busqueda=idioma)

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist


def actualizar_titulos(item):
    logger.info()
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = generictools.update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    
    try:
        item.url = host + 'component/sjk2filter/?Itemid=101&theme=sj-template&isc=1&ordering=rdate&searchword=%s&start=0' % texto
        item.extra = 'search'

        if texto:
            return listado(item)
        else:
            return []
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    
    try:
        if categoria in ['peliculas', 'torrent', '4k']:
            item.url = host + "peliculas.html"
            if categoria in ['4k']: item.url = host + "peliculas/4k.html"
            item.extra = "peliculas"
            item.extra2 = "novedades"
            item.action = "listado"
            itemlist.extend(listado(item))
                
        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()
        
        if categoria in ['series', 'torrent']:
            item.category_new= 'newest'
            item.url = host + "series.html"
            item.extra = "series"
            item.extra2 = "novedades"
            item.action = "listado"
            itemlist.extend(listado(item))

        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()
            
        if categoria in ['documentales', 'torrent']:
            item.category_new= 'newest'
            item.url = host + "documentales.html"
            item.extra = "documentales"
            item.extra2 = "novedades"
            item.action = "listado"
            itemlist.extend(listado(item))

        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []

    return itemlist
