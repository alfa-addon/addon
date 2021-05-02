# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# GenericTools
# ------------------------------------------------------------
# Código reusable de diferentes partes de los canales que pueden
# ser llamadados desde otros canales, y así carificar el formato
# y resultado de cada canal y reducir el costo su mantenimiento
# ------------------------------------------------------------

from __future__ import division
from builtins import zip
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

from builtins import range
from past.utils import old_div

import re
import os
import datetime
import time
import traceback
import inspect
import json
import base64

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import channeltools
from core import filetools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools
from lib import jsunpack

channel_py = "newpct1"
intervenido_judicial = 'Dominio intervenido por la Autoridad Judicial'
intervenido_policia = 'Judicial_Policia_Nacional'
intervenido_guardia = 'Judicial_Guardia_Civil'
intervenido_sucuri = 'Access Denied - Sucuri Website Firewall'
idioma_busqueda = 'es'
idioma_busqueda_VO = 'es,en'
movies_videolibrary_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_movies"))
series_videolibrary_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
list_nfos = []


def downloadpage(url, post=None, headers=None, random_headers=False, replace_headers=False, 
                 only_headers=False, referer=None, follow_redirects=True, timeout=None, 
                 proxy=True, proxy_web=False, proxy_addr_forced={}, forced_proxy=None, domain_name='', 
                 proxy_retries=1, CF=False, CF_test=True, file=None, filename=None, ignore_response_code=True, 
                 alfa_s=False, decode_code='', json=False, s2=None, patron='', quote_rep=False, 
                 forced_proxy_opt=None, no_comments=True, item={}, itemlist=[]):
    
    # Función "wraper" que puede ser llamada desde los canales para descargar páginas de forma unificada y evitar
    # tener que hacer todas las comprobaciones dentro del canal, lo que dificulta su mantenimiento y mejora.
    # La llamada tiene todos los parámetros típicos que puede usar un canal al descargar.
    
    if not PY3:
        funcion = inspect.stack()[1][3]                                         # Identifica el nombre de la función que llama
    else:
        funcion = inspect.stack()[1].function
    ERROR_01 = '%s: La Web no responde o ha cambiado de URL: ' % funcion.upper()    # Prepara los literales de los errores posibles
    ERROR_02 = '%s: Ha cambiado la estructura de la Web. Reportar el error con el log: ' % funcion.upper()
    if s2 is None and funcion == 'findvideos':                                  # Si es "findvideos" no sustituye los \s{2,}
        s2 = False                                                              # para no corromper las contraseñas de los .RAR
    elif s2 is None:
        s2 = True
    if referer is not None:
        if headers is None:
            headers = {'Referer':referer}
        else:
            headers['Referer'] = referer
    data = ''
    success = False
    code = 999
    if not item: item = Item()
    if not isinstance(url, (str, unicode, bytes)):
        logger.error('Formato de url incompatible: %s (%s)' % (str(url), str(type(url))))
        return ('', success, code, item, itemlist)


    try:
        response = httptools.downloadpage(url, post=post, headers=headers, random_headers=random_headers, 
                                          replace_headers=replace_headers, only_headers=only_headers, 
                                          follow_redirects=follow_redirects, encoding=decode_code, 
                                          timeout=timeout, proxy=proxy, proxy_web=proxy_web, forced_proxy_opt=forced_proxy_opt,  
                                          proxy_addr_forced=proxy_addr_forced, forced_proxy=forced_proxy, 
                                          proxy_retries=proxy_retries, CF=CF, CF_test=CF_test, file=file, filename=filename, 
                                          ignore_response_code=ignore_response_code, alfa_s=alfa_s)
        if response:
            if json and response.json:
                data = response.json
            else:
                data = response.data
            success = response.sucess
            code = response.code
            if decode_code is not None and response.encoding is not None:
                decode_code = response.encoding
            if success and only_headers:
                data = response.headers
                return (data, success, code, item, itemlist)
            if success and 'Content-Type' in response.headers and not 'text/html' \
                                in response.headers['Content-Type'] and not 'json' \
                                in response.headers['Content-Type'] and not 'xml' \
                                in response.headers['Content-Type']:
                return (data, success, code, item, itemlist)

        if data:
            data = js2py_conversion(data, url, domain_name=domain_name, timeout=timeout, 
                                channel=item.channel, headers=headers, referer=referer, 
                                post=post, follow_redirects=follow_redirects)   # En caso de que sea necesario la conversión js2py
            
            data = re.sub(r"\n|\r|\t", "", data).replace("'", '"')              # Reemplaza caracteres innecesarios
            if quote_rep:
                data = data.replace("'", '"')                                   # Reemplaza ' por "
            if s2:
                data = re.sub(r"\s{2,}", "", data)                              # Reemplaza blancos innecesarios, salvo en "findvideos"
            if no_comments:
                data = re.sub(r"(<!--.*?-->)", "", data)                        # Reemplaza comentarios
            if decode_code is None:                                             # Si se especifica, se decodifica con el código dado
                decode_code = 'utf8'
            if not PY3 and isinstance(data, str) and decode_code:
                data = unicode(data, decode_code, errors="replace").encode("utf8")
            elif PY3 and isinstance(data, bytes):
                if not decode_code: decode_code = 'utf8'
                data = data.decode(decode_code)
            if patron and not scrapertools.find_single_match(data, patron):     # Se comprueba que el patrón funciona
                code = 999                                                      # Si no funciona, se pasa error
                try:
                    logger.error('ERROR 02: ' + ERROR_02 + str(item.url) + " CODE: " + str(code) 
                            + " PATRON: " + str(patron) + " DATA: " + str(data))
                except:
                    logger.error('ERROR 02: ' + ERROR_02 + str(item.url) + " CODE: " + str(code)
                            + " PATRON: " + str(patron) + " DATA: ")
                if funcion != 'episodios':
                    itemlist.append(item.clone(action='', title=item.category + ': CODE: ' +
                             '[COLOR yellow]' + str(code) + '[/COLOR]: ERROR 02: ' + ERROR_02))
        else:                                                                   # Si no hay datos, se verifica la razón
            data = ''
            item = web_intervenida(item, data)                                  #Verificamos que no haya sido clausurada
            if item.intervencion:                                               #Sí ha sido clausurada judicialmente
                for clone_inter, autoridad in item.intervencion:
                    thumb_intervenido = get_thumb(autoridad)
                    if funcion != 'episodios':
                        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                            clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                            '. Reportar el problema en el foro', thumbnail=thumb_intervenido, 
                            folder=False))
            elif not success:
                logger.error('ERROR 01: ' + ERROR_01 + str(item.url) + " CODE: " + str(code) 
                                 + " PATRON: " + str(patron) + " DATA: ")
                if funcion != 'episodios':
                    itemlist.append(item.clone(action='', title=item.category + ': CODE: ' +
                             '[COLOR yellow]' + str(code) + '[/COLOR]: ERROR 01: ' + ERROR_01))
    except:
        logger.error(traceback.format_exc())
    
    return (data, success, code, item, itemlist)


def convert_url_base64(url, host='', rep_blanks=True):
    logger.info('URL: ' + url + ', HOST: ' + host)

    url_base64 = url
    if len(url_base64) > 1 and not 'magnet:' in url_base64 and not '.torrent' in url_base64:
        patron_php = 'php(?:#|\?u=)(.*?$)'
        if scrapertools.find_single_match(url_base64, patron_php):
            url_base64 = scrapertools.find_single_match(url_base64, patron_php)
        try:
            # Da hasta 20 pasadas o hasta que de error
            for x in range(20):
                url_base64 = base64.b64decode(url_base64).decode('utf-8')
            logger.info('Url base64 después de 20 pasadas (incompleta): %s' % url_base64)
        except:
            if url_base64 and url_base64 != url:
                logger.info('Url base64 convertida: %s' % url_base64)
                if rep_blanks: url_base64 = url_base64.replace(' ', '%20')
            #logger.error(traceback.format_exc())
            if not url_base64:
                url_base64 = url
                
    if host and host not in url_base64 and not url_base64.startswith('magnet:'):
        url_base64 = urlparse.urljoin(host, url_base64)
        if url_base64 != url:
            host_name = scrapertools.find_single_match(url_base64, '(http.*\:\/\/(?:.*ww[^\.]*)?\.?[^\.]+\.\w+(?:\.\w+)?)(?:\/|\?|$)')
            url_base64 = re.sub(host_name, host, url_base64)
            logger.info('Url base64 urlparsed: %s' % url_base64)
        
    
    return url_base64


def js2py_conversion(data, url, domain_name='', channel='', post=None, referer=None, headers=None, 
                     timeout=10, follow_redirects=True, proxy_retries=1):

    if PY3 and isinstance(data, bytes):
        if not b'Javascript is required' in data:
            return data
    elif not 'Javascript is required' in data:
        return data
    
    from lib import js2py
    
    # Obtiene nombre del dominio para la cookie
    if not domain_name:
        domain_name = scrapertools.find_single_match(url, 'http.*\:\/\/(?:.*ww[^\.]*)?(\.?[^\.]+\.\w+(?:\.\w+)?)(?:\/|\?|$)')
    logger.info(domain_name)

    # Obtiene nombre del canal que hace la llamada para marcarlo en su settings.xml
    if not channel and channel is not None:
        channel = inspect.getmodule(inspect.currentframe().f_back.f_back)
        try:
            channel = channel.__name__.split('.')[1]
        except:
            channel = ""
    
    # Obtiene el código JS
    if PY3 and isinstance(data, bytes):
        data = "".join(chr(x) for x in bytes(data))
    patron = ',\s*S="([^"]+)"'
    data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        patron = ",\s*S='([^']+)'"
        data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        logger.error('js2py_conversion: NO data_new')
        return data
        
    # Descompone el código Base64
    try:
        # Da hasta 10 pasadas o hasta que de error
        for x in range(10):
            data_end = base64.b64decode(data_new).decode('utf-8')
            data_new = data_end
    except:
        js2py_code = data_new
    else:
        logger.error('js2py_conversion: base64 data_new NO Funciona: ' + str(data_new))
        return data
    if not js2py_code:
        logger.error('js2py_conversion: NO js2py_code BASE64')
        return data

    def atob(s):
        import base64
        return base64.b64decode('{}'.format(s)).decode('utf-8')
     
    # Hace las llamadas a js2py para obtener la cookie
    js2py_code = js2py_code.replace('document', 'window').replace(" location.reload();", "")
    js2py.disable_pyimport()
    context = js2py.EvalJs({'atob': atob})
    new_cookie = context.eval(js2py_code)
    
    logger.info('new_cookie: ' + new_cookie)

    # Construye y salva la la cookie
    dict_cookie = {'domain': domain_name,}

    if ';' in new_cookie:
        new_cookie = new_cookie.split(';')[0].strip()
        namec, valuec = new_cookie.split('=')
        dict_cookie['name'] = namec.strip()
        dict_cookie['value'] = valuec.strip()
    res = httptools.set_cookies(dict_cookie)
    
    # Si existe channel se marca en settings como cookie regenerada
    if channel:
        try:
            config.set_setting("cookie_ren", True, channel=channel)
        except:
            pass

    # Se ejecuta de nuevo la descarga de la página, ya con la nueva cookie
    data_new = ''
    data_new = re.sub(r"\n|\r|\t", "", httptools.downloadpage(url, 
                timeout=timeout, headers=headers, referer=referer, post=post, 
                follow_redirects=follow_redirects, proxy_retries=proxy_retries).data)
    if data_new:
        data = data_new
    
    return data


def update_title(item):
    logger.info()
    from core import scraper

    """
    Utilidad para desambiguar Títulos antes de añadirlos a la Videoteca.  Puede ser llamado desde Videolibrarytools
    o desde Episodios en un Canal.  Si se llama desde un canal, la llamada sería así (incluida en post_tmdb_episodios(item, itemlist)):
    
        #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
        item.from_action = item.action      #Salvamos la acción...
        item.from_title = item.title        #... y el título
        itemlist.append(item.clone(title="** [COLOR limegreen]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="episodios", tmdb_stat=False))
    
    El canal deberá añadir un método para poder recibir la llamada desde Kodi/Alfa, y poder llamar a este método:
    
    def actualizar_titulos(item):
        logger.info()
        itemlist = []
        from lib import generictools
        from platformcode import launcher
        
        item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
        
        #Volvemos a la siguiente acción en el canal
        return launcher.run(item)
    
    Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado, borrando los IDs existentes
    El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
    o puede cancelar e introducir un nuevo título en la segunda pantalla
    Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
    Si lo hace en "Completar Información", cambia al nuevo título, pero no busca en TMDB.  Hay que hacerlo de nuevo
    Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir
    """
    #logger.debug(item)
    
    #Restauramos y borramos las etiquetas intermedias (si se ha llamado desde el canal)
    if item.from_action:
        item.action = item.from_action
        del item.from_action
    if item.from_update:
        if item.from_title_tmdb:            #Si se salvó el título del contenido devuelto por TMDB, se restaura.
            item.title = item.from_title_tmdb
    else:
        item.add_videolibrary = True        #Estamos Añadiendo a la Videoteca.  Indicador para control de uso de los Canales
    if item.add_videolibrary:
        if item.season_colapse: del item.season_colapse
        if item.from_num_season_colapse: del item.from_num_season_colapse
        if item.from_title_season_colapse: del item.from_title_season_colapse
        if item.contentType == "movie":
            if item.from_title_tmdb:        #Si se salvó el título del contenido devuelto por TMDB, se restaura.
                item.title = item.from_title_tmdb
            del item.add_videolibrary
        if item.channel_host:               #Borramos ya el indicador para que no se guarde en la Videoteca
            del item.channel_host
        if item.contentTitle:
            item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
            item.title = re.sub(r' -%s-' % item.category, '', item.title)
    if item.contentType == 'movie':
        from_title_tmdb = item.contentTitle
    else:
        from_title_tmdb = item.contentSerieName
    
    #Sólo ejecutamos este código si no se ha hecho antes en el Canal.  Por ejemplo, si se ha llamado desde Episodios o Findvideos,
    #ya no se ejecutará al Añadia a Videoteca, aunque desde el canal se podrá llamar tantas veces como se quiera, 
    #o hasta que encuentre un título no ambiguo
    if item.tmdb_stat:
        if item.from_title_tmdb: del item.from_title_tmdb
        if item.from_title: del item.from_title
        item.from_update = True
        del item.from_update
        if item.contentType == "movie":
            if item.channel == channel_py:  #Si es una peli de NewPct1, ponemos el nombre del clone
                item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
    else:
        new_item = item.clone()             #Salvamos el Item inicial para restaurarlo si el usuario cancela
        if item.contentType == "movie":
            if item.channel == channel_py:  #Si es una peli de NewPct1, ponemos el nombre del clone
                item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
        #Borramos los IDs y el año para forzar a TMDB que nos pregunte
        if item.infoLabels['tmdb_id'] or item.infoLabels['tmdb_id'] == None: item.infoLabels['tmdb_id'] = ''
        if item.infoLabels['tvdb_id'] or item.infoLabels['tvdb_id'] == None: item.infoLabels['tvdb_id'] = ''
        if item.infoLabels['imdb_id'] or item.infoLabels['imdb_id'] == None: item.infoLabels['imdb_id'] = ''
        if item.infoLabels['season']: del item.infoLabels['season'] #Funciona mal con num. de Temporada.  Luego lo restauramos
        item.infoLabels['year'] = '-'
        
        if item.from_title:
            if item.from_title_tmdb:
                if scrapertools.find_single_match(item.from_title_tmdb, '^(?:\[COLOR \w+\])?(.*?)(?:\[)'):
                    from_title_tmdb = scrapertools.find_single_match(item.from_title_tmdb, '^(?:\[COLOR \w+\])?(.*?)(?:\[)').strip()
            item.title = item.title.replace(from_title_tmdb, item.from_title)
            item.infoLabels['title'] = item.from_title
            
            if item.from_title_tmdb: del item.from_title_tmdb
        if not item.from_update and item.from_title: del item.from_title

        if item.contentSerieName:           #Copiamos el título para que sirva de referencia en menú "Completar Información"
            item.infoLabels['originaltitle'] = item.contentSerieName
            item.contentTitle = item.contentSerieName
        else:
            item.infoLabels['originaltitle'] = item.contentTitle
            
        scraper_return = scraper.find_and_set_infoLabels(item)

        if not scraper_return:  #Si el usuario ha cancelado, restituimos los datos a la situación inicial y nos vamos
            item = new_item.clone()
        else:
            #Si el usuario ha cambiado los datos en "Completar Información" hay que ver el título definitivo en TMDB
            if not item.infoLabels['tmdb_id']:
                if item.contentSerieName:
                    item.contentSerieName = item.contentTitle                       #Se pone título nuevo
                item.infoLabels['noscrap_id'] = ''                                  #Se resetea, por si acaso
                item.infoLabels['year'] = '-'                                       #Se resetea, por si acaso
                scraper_return = scraper.find_and_set_infoLabels(item)              #Se intenta de nuevo

                #Parece que el usuario ha cancelado de nuevo.  Restituimos los datos a la situación inicial
                if not scraper_return or not item.infoLabels['tmdb_id']:
                    item = new_item.clone()
                else:
                    item.tmdb_stat = True           #Marcamos Item como procesado correctamente por TMDB (pasada 2)
            else:
                item.tmdb_stat = True               #Marcamos Item como procesado correctamente por TMDB (pasada 1)

            #Si el usuario ha seleccionado una opción distinta o cambiado algo, ajustamos los títulos
            if item.contentType != 'movie' or item.from_update:
                item.channel = new_item.channel     #Restuaramos el nombre del canal, por si lo habíamos cambiado
            if item.tmdb_stat == True:
                if new_item.contentSerieName:       #Si es serie...
                    if config.get_setting("filter_languages", item.channel, default=-1) >= 0:
                        item.title_from_channel = new_item.contentSerieName         #Guardo el título incial para Filtertools
                        item.contentSerieName = new_item.contentSerieName           #Guardo el título incial para Filtertools
                    else:
                        item.title = item.title.replace(new_item.contentSerieName, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                        item.contentSerieName = item.contentTitle
                    if new_item.contentSeason: item.contentSeason = new_item.contentSeason      #Restauramos Temporada
                    if item.infoLabels['title']: del item.infoLabels['title']       #Borramos título de peli (es serie)
                else:                                                               #Si es película...
                    item.title = item.title.replace(new_item.contentTitle, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                if new_item.infoLabels['year']:                                     #Actualizamos el Año en el título
                    item.title = item.title.replace(str(new_item.infoLabels['year']), str(item.infoLabels['year']))
                if new_item.infoLabels['rating']:                                   #Actualizamos en Rating en el título
                    try:
                        rating_old = ''
                        if new_item.infoLabels['rating'] and new_item.infoLabels['rating'] != 0.0:
                            rating_old = float(new_item.infoLabels['rating'])
                            rating_old = round(rating_old, 1)
                        rating_new = ''
                        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
                            rating_new = float(item.infoLabels['rating'])
                            rating_new = round(rating_new, 1)
                        item.title = item.title.replace("[" + str(rating_old) + "]", "[" + str(rating_new) + "]")
                    except:
                        logger.error(traceback.format_exc())
                if item.wanted:                                         #Actualizamos Wanted, si existe
                    item.wanted = item.contentTitle
                if new_item.contentSeason:                              #Restauramos el núm. de Temporada después de TMDB
                    item.contentSeason = new_item.contentSeason
                    
                if item.from_update:                                    #Si la llamda es desde el menú del canal...
                    item.from_update = True 
                    del item.from_update
                    xlistitem = refresh_screen(item)                    #Refrescamos la pantallas con el nuevo Item
                    
        #Para evitar el "efecto memoria" de TMDB, se le llama con un título ficticio para que resetee los buffers
        if item.contentSerieName:
            new_item.infoLabels['tmdb_id'] = '289'                      #una serie no ambigua
        else:
            new_item.infoLabels['tmdb_id'] = '111'                      #una peli no ambigua
        new_item.infoLabels['year'] = '-'
        if new_item.contentSeason:
            del new_item.infoLabels['season']                           #Funciona mal con num. de Temporada
        scraper_return = scraper.find_and_set_infoLabels(new_item)
        
    #logger.debug(item)
    
    return item
    

def refresh_screen(item):
    logger.info()
    
    """
    #### Compatibilidad con Kodi 18 ####
    
    Refresca la pantalla con el nuevo Item después que haber establecido un dialogo que ha causado el cambio de Item
    Crea un xlistitem para engañar a Kodi con la función xbmcplugin.setResolvedUrl FALSE
    
    Entrada: item:          El Item actualizado
    Salida: xlistitem       El xlistitem creado, por si resulta de alguna utilidad posterior
    """

    try:
        import xbmcplugin
        import xbmcgui
        
        xlistitem = xbmcgui.ListItem(path=item.url)                     #Creamos xlistitem por compatibilidad con Kodi 18
        if config.get_platform(True)['num_version'] >= 16.0:
            xlistitem.setArt({"thumb": item.contentThumbnail})          #Cargamos el thumb
        else:
            xlistitem.setThumbnailImage(item.contentThumbnail)
        xlistitem.setInfo("video", item.infoLabels)                     #Copiamos infoLabel

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xlistitem)   #Preparamos el entorno para evitar error Kod1 18
        time.sleep(1)                                                   #Dejamos tiempo para que se ejecute
    except:
        logger.error(traceback.format_exc())
    
    platformtools.itemlist_update(item)                                 #refrescamos la pantalla con el nuevo Item
    
    return xlistitem
    
    
def post_tmdb_listado(item, itemlist):
    logger.info()
    global video_list
    
    itemlist_fo = []
    
    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Listado y Listado_Búsqueda.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.
    
    También restaura varios datos salvados desde el título antes de pasarlo por TMDB, ya que mantenerlos no habría encontrado el título (title_subs)
    
    La llamada al método desde Listado o Listado_Buscar, despues de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    """
    #logger.debug(item)
    
    #Borramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel_alt:
        channel_alt = item.channel_alt
        del item.channel_alt
    if item.url_alt:
        del item.url_alt

    #Ajustamos el nombre de la categoría
    if item.category_new == "newest":                           #Viene de Novedades.  Lo marcamos para Unify
        item.from_channel = 'news'
        del item.category_new

    #Cargo la lista de peliculas, series y documentales de la videoteca.  Se usa luego para Descargas
    res, video_list = check_title_in_videolibray(item, video_list_init=True)
    #logger.debug(video_list)
    
    # Pasada por TMDB a Serie, para datos adicionales, y mejorar la experiencia en Novedades
    if len(itemlist) > 0 and (itemlist[-1].contentType != 'movie' or item.action == 'search' or item.extra == 'novedades'):
        idioma = idioma_busqueda
        if 'VO' in str(itemlist[-1].language):
            idioma = idioma_busqueda_VO
        tmdb.set_infoLabels(itemlist, seekTmdb=True, idioma_busqueda=idioma)
    
    for item_local in itemlist:                                 #Recorremos el Itemlist generado por el canal
        item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
        #item_local.title = re.sub(r'online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title, flags=re.IGNORECASE).strip()
        title = item_local.title
        season = 0
        episode = 0
        idioma = idioma_busqueda
        if 'VO' in str(item_local.language):
            idioma = idioma_busqueda_VO
        #logger.debug(item_local)
        
        item_local.last_page = 0
        del item_local.last_page                                #Borramos restos de paginación
        en_videoteca = ''

        if item_local.contentSeason_save:                       #Restauramos el num. de Temporada
            item_local.contentSeason = item_local.contentSeason_save

        #Borramos valores para cada Contenido si ha habido fail-over
        if item_local.channel_alt:
            del item_local.channel_alt
        if item_local.url_alt:
            del item_local.url_alt
        if item_local.extra2:
            del item_local.extra2
        if item_local.library_filter_show:
            del item_local.library_filter_show
        if item_local.channel_host:
            del item_local.channel_host
        if item_local.category_new == "newest":                 #Viene de Novedades.  Lo marcamos para Unify
            item_local.from_channel = 'news'
            del item_local.category_new

        #Ajustamos el nombre de la categoría
        if item_local.channel == channel_py:
            item_local.category = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        
        #Restauramos la info adicional guarda en la lista title_subs, y la borramos de Item
        title_add = ' '
        if item_local.title_subs:
            for title_subs in item_local.title_subs:
                if "audio" in title_subs.lower():                               #se restaura info de Audio
                    title_add += scrapertools.find_single_match(title_subs, r'[a|A]udio (.*?)')
                    continue
                if scrapertools.find_single_match(title_subs, r'^(\d{4})$'):    #Se restaura el año, s no lo ha dado TMDB
                    if not item_local.infoLabels['year'] or item_local.infoLabels['year'] == "-":
                        item_local.infoLabels['year'] = scrapertools.find_single_match(title_subs, r'(\d{4})')
                    continue

                title_add = title_add.rstrip()
                if scrapertools.find_single_match(title_subs, r'Episodio\s*(\d+)x(\d+)'):
                    title_subs += ' (MAX_EPISODIOS)'
                title_add = '%s -%s-' % (title_add, title_subs)                 #se agregan el resto de etiquetas salvadas
        item_local.title_subs = []
        del item_local.title_subs

        #Preparamos el Rating del vídeo
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            logger.error(traceback.format_exc())

        __modo_grafico__ = config.get_setting('modo_grafico', item.channel)    
        
        # Si TMDB no ha encontrado el vídeo limpiamos el año
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
            
        #Si traía el TMDB-ID, pero no ha funcionado, lo reseteamos e intentamos de nuevo
        if item_local.infoLabels['tmdb_id'] and not item_local.infoLabels['originaltitle']:
            logger.info("*** TMDB-ID erroneo, reseteamos y reintentamos: %s" % item_local.infoLabels['tmdb_id'])
            del item_local.infoLabels['tmdb_id']                        #puede traer un TMDB-ID erroneo
            try:
                tmdb.set_infoLabels_item(item_local, __modo_grafico__, idioma_busqueda=idioma) #pasamos otra vez por TMDB
            except:
                logger.error(traceback.format_exc())
            logger.info("*** TMDB-ID erroneo reseteado: %s" % item_local.infoLabels['tmdb_id'])
        
        # Si TMDB no ha encontrado nada y hemos usado el año de la web, lo intentamos sin año
        if not item_local.infoLabels['tmdb_id']:
            if item_local.infoLabels['year']:                   #lo intentamos de nuevo solo si había año, puede que erroneo
                year = item_local.infoLabels['year']            #salvamos el año por si no tiene éxito la nueva búsqueda
                item_local.infoLabels['year'] = "-"             #reseteo el año
                try:
                    tmdb.set_infoLabels_item(item_local, __modo_grafico__, idioma_busqueda=idioma) #pasamos otra vez por TMDB
                except:
                    logger.error(traceback.format_exc())
                if not item_local.infoLabels['tmdb_id']:        #ha tenido éxito?
                    item_local.infoLabels['year'] = year        #no, restauramos el año y lo dejamos ya

        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        if item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        if item_local.from_title:
            if item_local.contentType == 'movie':
                item_local.contentTitle = item_local.from_title
                item_local.title = item_local.from_title
            else:
                item_local.contentSerieName = item_local.from_title
            if item_local.contentType == 'season':
                item_local.title = item_local.from_title
            item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
            title = item_local.title
        
        #Limpiamos calidad de títulos originales que se hayan podido colar
        if item_local.infoLabels['originaltitle'].lower() in item_local.quality.lower():
            item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality)
            #item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality, flags=re.IGNORECASE)
        
        # Preparamos el título para series, con los núm. de temporadas, si las hay
        if item_local.contentType in ['season', 'tvshow', 'episode']:
            
            # Pasada por TMDB a Serie, para datos adicionales, y mejorar la experiencia en Novedades
            if scrapertools.find_single_match(title_add, r'Episodio\s*(\d+)x(\d+)') and item_local.infoLabels['tmdb_id']:
                # Salva los datos de la Serie y lo transforma temporalmente en Season o Episode
                contentPlot = item_local.contentPlot
                contentType = item_local.contentType
                season, episode = scrapertools.find_single_match(title_add, r'Episodio\s*(\d+)x(\d+)')
                episode_max = int(episode)
                item_local.infoLabels['season'] = season
                if '-al-' not in title_add:
                    item_local.infoLabels['episode'] = episode
                    item_local.contentType = "episode"
                else:
                    item_local.contentType = "season"
                    episode_max = int(scrapertools.find_single_match(title_add, r'Episodio\s*\d+x\d+-al-(\d+)'))

                try:
                    if item_local.infoLabels['tmdb_id']:
                        tmdb.set_infoLabels_item(item_local, seekTmdb=True, idioma_busqueda=idioma)  #TMDB de la serie
                except:
                    logger.error(traceback.format_exc())
                
                # Restaura los datos de infoLabels a su estado original, menos plot y año
                item_local.infoLabels['year'] = scrapertools.find_single_match(item_local.infoLabels['aired'], r'\d{4}')
                if item_local.infoLabels.get('temporada_num_episodios', 0) >= episode_max:
                    tot_epis = ' (de %s' % str(item_local.infoLabels['temporada_num_episodios'])
                    if item_local.infoLabels.get('number_of_seasons', 0) > 1 \
                            and item_local.infoLabels.get('number_of_episodes', 0) > 0:
                        tot_epis += ', de %sx%s' % (str(item_local.infoLabels['number_of_seasons']), \
                            str(item_local.infoLabels['number_of_episodes']))
                    tot_epis += ')'
                    title_add = title_add.replace(' (MAX_EPISODIOS)', tot_epis)
                else:
                    title_add = title_add.replace(' (MAX_EPISODIOS)', '')
                if contentPlot[10:] != item_local.contentPlot[10:]:
                    item_local.contentPlot += '\n\n%s' % contentPlot
                item_local.contentType = contentType
                if item_local.contentType in ['tvshow']: del item_local.infoLabels['season']
                if item_local.contentType in ['season', 'tvshow'] and item_local.contentEpisodeNumber: del item_local.infoLabels['episode']

            # Exploramos los diferentes formatos
            if item_local.contentType == "episode":
                #Si no está el título del episodio, pero sí está en "title", lo rescatamos
                if not item_local.infoLabels['episodio_titulo'] and item_local.infoLabels['title'].lower() \
                            != item_local.infoLabels['tvshowtitle'].lower():
                    item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['title']

                if "Temporada" in title:                    #Compatibilizamos "Temporada" con Unify
                    title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
                if " al " in title:                         #Si son episodios múltiples, ponemos nombre de serie
                    if " al 99" in title.lower():           #Temporada completa.  Buscamos num total de episodios
                        title = title.replace("99", str(item_local.infoLabels['temporada_num_episodios']))
                    title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
                elif item_local.infoLabels['episodio_titulo']:
                    title = '%s %s, %s' % (title, item_local.infoLabels['episodio_titulo'], item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s, %s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.contentSerieName, item_local.infoLabels['year'], rating)
                    
                else:                                       #Si no hay título de episodio, ponermos el nombre de la serie
                    if item_local.contentSerieName not in title:
                        title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)
                    
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    if "Episodio" in title_add:
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, 'Episodio (\d+)x(\d+)')
                        title = '%s [%s] [%s]' % (title, item_local.infoLabels['year'], rating)

            elif item_local.contentType == "season":
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, '-(\d+)x')
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, '-temporadas?-(\d+)')
                if item_local.contentSeason:
                    title = '%s -Temporada %s' % (title, str(item_local.contentSeason))
                    if not item_local.contentSeason_save:                           #Restauramos el num. de Temporada
                        item_local.contentSeason_save = item_local.contentSeason    #Y lo volvemos a salvar
                    del item_local.infoLabels['season']         #Funciona mal con num. de Temporada.  Luego lo restauramos
                else:
                    title = '%s -Temporada !!!' % (title)

            elif (item.action == "search" or item.extra == "search" or item_local.from_channel == "news") and not \
                        (item_local.extra == "varios" or item_local.extra == "documentales"):
                title += " -Serie-"
                if item_local.from_channel == "news":
                    title_add += " -Serie-"

        if (item_local.extra == "varios" or item_local.extra == "documentales") \
                        and (item.action == "search" or item.extra == "search" or \
                        item.action == "listado_busqueda" or item_local.from_channel == "news"):
            title += " -Varios-"
            item_local.contentTitle += " -Varios-"
            if item_local.from_channel == "news":
                title_add += " -Varios-"
        
        if item_local.contentType != 'movie' and item_local.infoLabels['tmdb_id'] \
                        and ((item_local.infoLabels['imdb_id'] \
                        and item_local.infoLabels['imdb_id'] in str(video_list)) \
                        or 'tmdb_'+item_local.infoLabels['tmdb_id'] in str(video_list) \
                    or item_local.contentTitle.lower()+' [' in str(video_list)):
            id_tmdb = item_local.infoLabels['imdb_id']
            if not id_tmdb:
                id_tmdb = "tmdb_%s" % item_local.infoLabels['tmdb_id']
            item_local.video_path = "%s [%s]" % (item_local.contentSerieName, id_tmdb)
            item_local.url_tvshow = item_local.url
            season_episode = ''
            if season and episode:
                season_episode = '%sx%s.strm' % (str(season), str(episode).zfill(2))
            if check_marks_in_videolibray(item_local, strm=season_episode):
                item_local.infoLabels["playcount"] = 1
            if item_local.video_path:
                item_local = context_for_videolibray(item_local)
                en_videoteca = '(V)-'

        title += title_add.replace(' (MAX_EPISODIOS)', '')                      #Se añaden etiquetas adicionales, si las hay

        #Ahora maquillamos un poco los titulos dependiendo de si se han seleccionado títulos inteleigentes o no
        if not config.get_setting("unify"):                                     #Si Titulos Inteligentes NO seleccionados:
            title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_local.infoLabels['year']), rating, item_local.quality, str(item_local.language))

        elif item_local.action:                                                 #Si Titulos Inteligentes SÍ seleccionados:
            title = title.replace("[", "-").replace("]", "-").replace(".", ",").replace("GB", "G B")\
                        .replace("Gb", "G b").replace("gb", "g b").replace("MB", "M B")\
                        .replace("Mb", "M b").replace("mb", "m b")
        
        #Limpiamos las etiquetas vacías
        if item_local.infoLabels['episodio_titulo']:
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace(" []", "").strip()
        title = title.replace("--", "").replace(" []", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', title).strip()
        title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', title).strip()
    
        #Viene de Novedades.  Lo preparamos para Unify
        if item_local.from_channel == "news":
            """
            if scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/'):
                title += ' -%s-' % scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            else:
                title += ' -%s-' % item_local.channel.capitalize()
            if item_local.contentType == "movie":
                if scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/'):
                    item_local.contentTitle += ' -%s-' % scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
                else:
                    item_local.contentTitle += ' -%s-' % item_local.channel.capitalize()
            """
            if item_local.contentType in ['season', 'tvshow']:
                title = '%s %s' % (item_local.contentSerieName, title_add)
            elif "Episodio " in title:
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, 'Episodio (\d+)x(\d+)')

        if item_local.infoLabels['status'] and (item_local.infoLabels['status'].lower() == "ended" \
                        or item_local.infoLabels['status'].lower() == "canceled"):
            title += ' [TERM]'
        
        item_local.title = en_videoteca + title
        item_local.contentTitle = en_videoteca + item_local.contentTitle
        
        #logger.debug("url: " + item_local.url + " / title: " + item_local.title + " / content title: " + item_local.contentTitle + "/" + item_local.contentSerieName + " / calidad: " + item_local.quality + "[" + str(item_local.language) + "]" + " / year: " + str(item_local.infoLabels['year']))
        
        #logger.debug(item_local)
    
    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt and item.from_channel != "news":
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] inaccesible'))
    
    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist
        
    if item.from_channel:
        del item.from_channel
        
    return (item, itemlist)


def post_tmdb_seasons(item, itemlist, url='serie'):
    logger.info()
    
    """
        
    Pasada para gestión del menú de Temporadas de una Serie
    
    La clave de activación de este método es la variable item.season_colapse que pone el canal en el Item de Listado.
    Esta variable tendrá que desaparecer cuando se añada a la Videoteca para que se analicen los episodios de la forma tradicional
    
    Repasa todos los episodios producidos en itemlist por "episodios" del canal para extraer las temporadas.  Pone un título para Todas la Temps.
    Crea un menú con las diferentes temporadas, así como con los títulos de Actualización de Título y de Añadir a Videoteca
    Si ha habido un Fail-over o una Intervención Judicial, también lo anuncia
    
    La llamada al método desde Episodios, antes de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)
        
    Si solo hay una temporada, devuelte el itemlist original para que se pinten los episodios de la forma tradicional
    
    """
    #logger.debug(item)
    
    season = 0
    itemlist_temporadas = []
    itemlist_fo = []
    
    if config.get_setting("no_pile_on_seasons", 'videolibrary') == 2:           #Si no se quiere mostrar por temporadas, nos vamos...
        if item.season_colapse:                                                 #Quitamos el indicador de listado por Temporadas
            del item.season_colapse
        return (item, itemlist)
    
    #Restauramos valores si ha habido fail-over
    channel_alt = ''
    channel_alt_org = item.channel_alt
    category = item.category
    url_alt = ''
    if item.channel == channel_py:
        if item.channel_alt:
            channel_alt = item.category
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    else:
        if item.channel_alt:
            channel_alt = item.channel
            item.channel = item.channel_alt
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    if item.url_alt:
        url_alt = item.url
        item.url = item.url_alt
        del item.url_alt
    
    # Si está en la videoteca, listamos los episodios vistos/no vistos
    episode_list = {}
    if item.video_path:
        res, episode_list = check_marks_in_videolibray(item, video_list_init=True)
    
    # Primero creamos un título para TODAS las Temporadas
    # Pasada por TMDB a Serie, para datos adicionales
    idioma = idioma_busqueda
    if 'VO' in str(item.language):
        idioma = idioma_busqueda_VO
    try:
        tmdb.set_infoLabels_item(item, seekTmdb=True, idioma_busqueda=idioma)  #TMDB de la serie
    except:
        logger.error(traceback.format_exc())
    
    item_season = item.clone()
    if item_season.season_colapse:                                              #Quitamos el indicador de listado por Temporadas
        del item_season.season_colapse
    title = '** Todas las Temporadas'                                           #Agregamos título de TODAS las Temporadas (modo tradicional)
    if item_season.infoLabels['number_of_episodes']:                            #Ponemos el núm de episodios de la Serie
        title += ' [%sx%s epi]' % (str(item_season.infoLabels['number_of_seasons']), \
                str(item_season.infoLabels['number_of_episodes']))
    
    rating = ''                                                                 #Ponemos el rating, si es diferente del de la Serie
    if item_season.infoLabels['rating'] and item_season.infoLabels['rating'] != 0.0:
        try:
            rating = float(item_season.infoLabels['rating'])
            rating = round(rating, 1)
        except:
            logger.error(traceback.format_exc())
    if rating and rating == 0.0:
        rating = ''
    
    if not config.get_setting("unify"):                                         #Si Titulos Inteligentes NO seleccionados:
        title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % \
                (title, str(item_season.infoLabels['year']), rating, item_season.quality, str(item_season.language))
    else:                                                                       #Lo arreglamos un poco para Unify
        title = title.replace('[', '-').replace(']', '-').replace('.', ',').strip()
    title = title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
    
    if config.get_setting("show_all_seasons", 'videolibrary'):
        itemlist_temporadas.append(item_season.clone(title=title, from_title_season_colapse=item.title))
    
    #Repasamos todos los episodios para detectar las diferentes temporadas
    marca_visto = None
    for item_local in itemlist:
        if item_local.contentSeason != season:
            season = item_local.contentSeason                                   #Si se detecta una temporada distinta se prepara un título
            if marca_visto and len(itemlist_temporadas) > 0 and itemlist_temporadas[-1].contentSeason:
                itemlist_temporadas[-1].infoLabels['playcount'] = 1
            marca_visto = None
            item_season = item.clone()
            item_season.contentSeason = item_local.contentSeason                #Se pone el núm de Temporada para obtener mejores datos de TMDB
            item_season.contentType = 'season'
            item_season.title = 'Temporada %s' % item_season.contentSeason
            if item_season.video_path:
                item_season = context_for_videolibray(item_season)
            if url != 'serie':
                if item_local.url_tvshow:
                    item_season.url = item_local.url_tvshow
                else:
                    item_season.url = item_local.url
            itemlist_temporadas.append(item_season.clone(from_title_season_colapse=item.title))

        if item_local.video_path: 
            season_episode = '%sx%s.strm' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
            if episode_list.get(season_episode, 0) >= 1:
                if marca_visto or marca_visto is None:
                    marca_visto = True
            else:
                marca_visto = False
    else:
        # Trata la última temporada
        if marca_visto and len(itemlist_temporadas) > 0 and itemlist_temporadas[-1].contentSeason:
            itemlist_temporadas[-1].infoLabels['playcount'] = 1
            
    #Si hay más de una temporada se sigue, o se ha forzado a listar por temporadas, si no se devuelve el Itemlist original
    if len(itemlist_temporadas) > 2 or config.get_setting("no_pile_on_seasons", 'videolibrary') == 0:
        for item_local in itemlist_temporadas:
            if "** Todas las Temporadas" in item_local.title:                   #Si es el título de TODAS las Temporadas, lo ignoramos
                continue
            
            # Pasada por TMDB a las Temporada
            try:
                tmdb.set_infoLabels_item(item_local, seekTmdb=True, idioma_busqueda=idioma)    #TMDB de cada Temp
            except:
                logger.error(traceback.format_exc())
        
            if item_local.infoLabels['temporada_air_date']:                     #Fecha de emisión de la Temp
                item_local.title += ' [%s]' % str(scrapertools.find_single_match(str(item_local.infoLabels['temporada_air_date']), r'\/(\d{4})'))
            
            #rating = ''                                                        #Ponemos el rating, si es diferente del de la Serie
            #if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
            #    try:
            #        rating = float(item_local.infoLabels['rating'])
            #        rating = round(rating, 1)
            #    except:
            #        logger.error(traceback.format_exc())
            #if rating and rating > 0.0:
            #    item_local.title += ' [%s]' % str(rating)
            
            if item_local.infoLabels['temporada_num_episodios']:                #Núm. de episodios de la Temp
                item_local.title += ' [%s epi]' % str(item_local.infoLabels['temporada_num_episodios'])
                
            if not config.get_setting("unify"):                                 #Si Titulos Inteligentes NO seleccionados:
                item_local.title = '%s [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.quality, str(item_local.language))
            elif item_local.action:                                 #Si Titulos Inteligentes SÍ seleccionados:
                item_local.title = item_local.title.replace("[", "-").replace("]", "-").replace(".", ",").replace("GB", "G B").replace("Gb", "G b").replace("gb", "g b").replace("MB", "M B").replace("Mb", "M b").replace("mb", "m b")
            item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
            
            #logger.debug(item_local)
        
    else:                                   #Si hay más de una temporada se sigue, si no se devuelve el Itemlist original
        if item.season_colapse:
            del item.season_colapse
        if channel_alt_org:                 # Si ha habido fail-over, restauramos los valores previos
            item.channel_alt = channel_alt_org
            item.category = channel_alt
            item.url_alt = item.url
            item.url = url_alt
        return (item, itemlist)
    
    #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
    itemlist_temporadas.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))
    
    #Es un canal estándar, sólo una linea de Añadir a Videoteca
    title = ''
    if item.infoLabels['status'] and (item.infoLabels['status'].lower() == "ended" \
                        or item.infoLabels['status'].lower() == "canceled"):
        title += ' [TERM]'
    itemlist_temporadas.append(item_season.clone(title="[COLOR yellow]Añadir esta serie a videoteca-[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))

    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() + '[/COLOR] inaccesible'))
    
    if len(itemlist_fo) > 0:
        itemlist_temporadas = itemlist_fo + itemlist_temporadas
    
    return (item, itemlist_temporadas)
    
    
def post_tmdb_episodios(item, itemlist):
    logger.info()
    itemlist_fo = []
        
    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Episodios.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.

    Lleva un control del num. de episodios por temporada, tratando de arreglar los errores de la Web y de TMDB
    
    La llamada al método desde Episodios, despues de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    """
    #logger.debug(item)
    
    modo_serie_temp = config.get_setting('seleccionar_serie_temporada', item.channel, default=0)
    modo_ultima_temp = ''
    if config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is True or config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is False:
        modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel)

    #Inicia variables para el control del núm de episodios por temporada
    num_episodios = 1
    num_episodios_lista = []
    for i in range(0, 50):  num_episodios_lista += [0]
    num_temporada = 1
    num_temporada_max = 99
    num_episodios_flag = True
    episode_list = {}
    if item.library_urls or item.add_videolibrary:
        if item.video_path:
            del item.video_path
    elif item.video_path:
        res, episode_list = check_marks_in_videolibray(item, video_list_init=True)
    
    #Restauramos el num de Temporada para hacer más flexible la elección de Videoteca
    contentSeason = item.contentSeason
    if item.contentSeason_save:
        contentSeason = item.contentSeason_save
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save

    #Ajustamos el nombre de la categoría
    if item.channel == channel_py:
        item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
    
    #Restauramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel == channel_py:
        if item.channel_alt or item.channel_redir:
            channel_alt = item.category
            item.category = item.channel_redir.capitalize() or item.channel_alt.capitalize()
            if item.channel_alt: del item.channel_alt
    else:
        if item.channel_alt or item.channel_redir:
            channel_alt = item.channel
            item.channel = item.channel_redir.lower() or item.channel_alt.lower()
            item.category = item.channel_redir.capitalize() or item.channel_alt.capitalize()
            if item.channel_alt: del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt
    if item.title_from_channel:
        del item.title_from_channel
    if item.ow_force:
        del item.ow_force
    if item.season_colapse:
        del item.season_colapse
    if item.from_action:
        del item.from_action
    if item.from_channel:
        del item.from_channel
    if item.library_filter_show:
        del item.library_filter_show
    if item.channel_host:
        del item.channel_host
        
    for item_local in itemlist:                                                 #Recorremos el Itemlist generado por el canal
        if item_local.add_videolibrary:
            del item_local.add_videolibrary
        if item_local.add_menu:
            del item_local.add_menu
        if item_local.contentSeason_save:
            del item_local.contentSeason_save
        if item_local.title_from_channel:
            del item_local.title_from_channel
        if item_local.library_playcounts:
            del item_local.library_playcounts
        if item_local.library_urls:
            del item_local.library_urls
        if item_local.path:
            del item_local.path
        if item_local.nfo:
            del item_local.nfo
        if item_local.update_last:
            del item_local.update_last
        if item_local.update_next:
            del item_local.update_next
        if item_local.channel_host:
            del item_local.channel_host
        if item_local.intervencion:
            del item_local.intervencion
        if item_local.ow_force:
            del item_local.ow_force
        if item_local.season_colapse:
            del item_local.season_colapse
        if item_local.from_action:
            del item_local.from_action
        if item_local.from_channel:
            del item_local.from_channel
        if item_local.emergency_urls and isinstance(item_local.emergency_urls, dict):
            del item_local.emergency_urls
        if item_local.library_filter_show:
            del item_local.library_filter_show
        if item_local.extra2:
            del item_local.extra2
        if (item.library_urls or item.add_videolibrary) and item_local.video_path:
            del item_local.video_path
        item_local.wanted = 'xyz'
        del item_local.wanted
        item_local.text_color = 'xyz'
        del item_local.text_color
        item_local.tmdb_stat = 'xyz'
        del item_local.tmdb_stat
        item_local.totalItems = 'xyz'
        del item_local.totalItems
        item_local.unify = 'xyz'
        del item_local.unify
        item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
        if not item_local.url_tvshow:
            item_local.url_tvshow = item.url                                    # Salvamos la url de la serie/temporada para descargas
        
        #logger.debug(item_local)

        #Ajustamos el nombre del canal si es un clone de NewPct1 y viene de Videoteca. Tomamos el canal original, no el actual
        if item_local.channel == channel_py and (item.library_urls or item.add_videolibrary):
            item_local.channel = item_local.category.lower()
            #if item.library_urls or item.add_videolibrary:                     # Si videne de videoteca cambiamos el nombre de canal al clone
            #    item_local.channel = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').lower()
            #item_local.category = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        #Restauramos valores para cada Episodio si ha habido fail-over de un clone de NewPct1
        if (item_local.channel_alt or item_local.channel_redir) and not item.downloadFilename:
            #item_local.channel = item_local.channel_redir.lower() or item_local.channel_alt.lower()
            item_local.category = item_local.channel_redir.capitalize() or item_local.channel_alt.capitalize()
            if item_local.channel_alt: del item_local.channel_alt
            #if item_local.channel_redir: del item_local.channel_redir
        if (item_local.channel_alt or item_local.channel_redir) and item.downloadFilename:
            item_local.channel_alt = channel_alt
        if item_local.url_alt:
            host_act = scrapertools.find_single_match(item_local.url, '(http.*\:\/\/(?:www.)?\w+\.\w+\/)')
            host_org = scrapertools.find_single_match(item_local.url_alt, '(http.*\:\/\/(?:www.)?\w+\.\w+\/)')
            dom_sufix_act = scrapertools.find_single_match(host_act, ':\/\/(.*?)\/*$').replace('.', '-')
            dom_sufix_org = scrapertools.find_single_match(host_org, ':\/\/(.*?)\/*$').replace('.', '-')
            if dom_sufix_act:
                item_local.url = item_local.url.replace(dom_sufix_act, dom_sufix_org)
            else:
                item_local.url += dom_sufix_org
            item_local.url = item_local.url.replace(host_act, host_org)
            del item_local.url_alt
            
        #Si el título de la serie está verificado en TMDB, se intenta descubrir los eisodios fuera de rango,
        #que son probables errores de la Web
        if item.tmdb_stat:
            if item_local.infoLabels['number_of_seasons']:
                #Si el num de temporada está fuera de control, se pone 0, y se reclasifica itemlist
                if item_local.contentSeason > item_local.infoLabels['number_of_seasons'] + 1:
                    logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(item_local.infoLabels['number_of_seasons']) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
                else:
                    num_temporada_max = item_local.infoLabels['number_of_seasons']
            else:
                if item_local.contentSeason > num_temporada_max + 1:
                    logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(num_temporada_max) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
        
        #Salvamos en número de episodios de la temporada
        try:
            if not item_local.infoLabels['temporada_num_episodios']:
                item_local.infoLabels['temporada_num_episodios'] = 0
            if num_temporada != item_local.contentSeason:
                num_temporada = item_local.contentSeason
                num_episodios = 0
            if item_local.infoLabels['number_of_seasons'] == 1 and item_local.infoLabels['number_of_episodes'] > item_local.infoLabels['temporada_num_episodios']:
                item_local.infoLabels['temporada_num_episodios'] = item_local.infoLabels['number_of_episodes']
            if item_local.infoLabels['temporada_num_episodios'] and item_local.infoLabels['temporada_num_episodios'] > int(num_episodios):
                num_episodios = item_local.infoLabels['temporada_num_episodios']
        except:
            num_episodios = 0
            logger.error(traceback.format_exc())
        
        #Preparamos el Rating del vídeo
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            logger.error(traceback.format_exc())
        
        # Si TMDB no ha encontrado el vídeo limpiamos el año
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        elif item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        #Limpiamos calidad de títulos originales que se hayan podido colar
        if item_local.infoLabels['originaltitle'].lower() in item_local.quality.lower():
            item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality)
            #item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality, flags=re.IGNORECASE)
        
        #Si no está el título del episodio, pero sí está en "title", lo rescatamos
        if not item_local.infoLabels['episodio_titulo'] and item_local.infoLabels['title'].lower() != item_local.infoLabels['tvshowtitle'].lower():
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['title']
        item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace('GB', 'G B').replace('MB', 'M B')
        
        #Preparamos el título para que sea compatible con Añadir Serie a Videoteca
        if "Temporada" in item_local.title:             #Compatibilizamos "Temporada" con Unify
            item_local.title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
        if " al " in item_local.title:                  #Si son episodios múltiples, ponemos nombre de serie
            if " al 99" in item_local.title.lower():    #Temporada completa.  Buscamos num total de episodios de la temporada
                item_local.title = item_local.title.replace("99", str(num_episodios))
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(item_local.title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
        elif item_local.infoLabels['episodio_titulo']:
            item_local.title = '%s %s' % (item_local.title, item_local.infoLabels['episodio_titulo']) 
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.infoLabels['year'], rating)
            
        else:                                           #Si no hay título de episodio, ponermos el nombre de la serie
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
        #Si está en la Videoteca, se verifica y está visto/no visto
        season_episode = '%sx%s.strm' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
        if item_local.video_path and episode_list.get(season_episode, 0) >= 1:
            item_local.infoLabels["playcount"] = 1
        if item_local.video_path:
            item_local = context_for_videolibray(item_local)
        
        #Componemos el título final, aunque con Unify usará infoLabels['episodio_titulo']
        item_local.infoLabels['title'] = item_local.infoLabels['episodio_titulo']
        if item_local.action:
            item_local.title = item_local.title.replace("[", "-").replace("]", "-")
        item_local.title = '%s [%s] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.infoLabels['year'], rating, item_local.quality, str(item_local.language))
    
        #Quitamos campos vacíos
        item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace("[]", "").strip()
        item_local.infoLabels['title'] = item_local.infoLabels['title'].replace("[]", "").strip()
        item_local.title = item_local.title.replace("[]", "").strip()
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?-?\s?\]?\]\[\/COLOR\]', '', item_local.title).strip()
        item_local.title = re.sub(r'\s?\[COLOR \w+\]-?\s?\[\/COLOR\]', '', item_local.title).strip()
        item_local.title = item_local.title.replace(".", ",").replace("GB", "G B").replace("Gb", "G b")\
                        .replace("gb", "g b").replace("MB", "M B").replace("Mb", "M b").replace("mb", "m b")
        
        #Si la información de num. total de episodios de TMDB no es correcta, tratamos de calcularla
        if num_episodios < item_local.contentEpisodeNumber:
            num_episodios = item_local.contentEpisodeNumber
        if num_episodios > item_local.contentEpisodeNumber:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        if num_episodios and not item_local.infoLabels['temporada_num_episodios']:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        try:
            num_episodios_lista[item_local.contentSeason] = num_episodios
        except:
            logger.error(traceback.format_exc())

        #logger.debug("title: " + item_local.title + " / url: " + item_local.url + " / calidad: " + item_local.quality + " / Season: " + str(item_local.contentSeason) + " / EpisodeNumber: " + str(item_local.contentEpisodeNumber) + " / num_episodios_lista: " + str(num_episodios_lista) + str(num_episodios_flag))
        #logger.debug(item_local)

    #Si está actualizando videoteca de una serie NewPct1, restauramos el channel con el nombre del clone
    if item.channel == channel_py and (item.library_playcounts or item.add_videolibrary):
        if item.channel_redir:
            item.channel = item.channel_redir.lower()
        else:
            item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
    if item.channel_redir:
        del item.channel_redir
    
    #Terminado el repaso de cada episodio, cerramos con el pié de página
    #En primer lugar actualizamos todos los episodios con su núm máximo de episodios por temporada
    try:
        if not num_episodios_flag:              #Si el num de episodios no está informado, acualizamos episodios de toda la serie
            for item_local in itemlist:
                item_local.infoLabels['temporada_num_episodios'] = int(num_episodios_lista[item_local.contentSeason])
    except:
        logger.error("ERROR 07: EPISODIOS: Num de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(num_temporada_max) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
        logger.error(traceback.format_exc())
    
    #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
    poster = item.infoLabels['temporada_poster']
    if not poster: poster = item.infoLabels['thumbnail']
    if not item.downloadFilename:                           #... si no viene de Descargas
        itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", 
                    action="actualizar_titulos", tmdb_stat=False, from_action=item.action, contentType='episode', 
                    from_title_tmdb=item.title, from_update=True, thumbnail=poster))
    
    #Borro num. Temporada si no viene de menú de Añadir a Videoteca y no está actualizando la Videoteca
    if not item.library_playcounts:                         #si no está actualizando la Videoteca
        if modo_serie_temp > 0:                             #y puede cambiara a serie-temporada
            if item.contentSeason and not item.add_menu:
                del item.infoLabels['season']               #La decisión de ponerlo o no se toma en la zona de menús

    #Ponemos el título de Añadir a la Videoteca, con el núm. de episodios de la última temporada y el estado de la Serie
    if config.get_videolibrary_support() and len(itemlist) > 1 and not item.downloadFilename:
        item_local = itemlist[-2]
        title = ''
        
        if item_local.infoLabels['temporada_num_episodios']:
            title += ' [%sx%s' % (item_local.infoLabels['season'], item_local.infoLabels['temporada_num_episodios'])
        
        if item_local.infoLabels['number_of_episodes'] and item_local.infoLabels['number_of_seasons'] > 1:
            title += ' de %sx%s' % (str(item_local.infoLabels['number_of_seasons']), \
                    str(item_local.infoLabels['number_of_episodes']))   
        title += ']'
        
        if item_local.infoLabels['status'] and item_local.infoLabels['status'].lower() == "ended":
            title += ' [TERM]'
            
        if item_local.quality:      #La Videoteca no toma la calidad del episodio, sino de la serie.  Pongo del episodio
            item.quality = item_local.quality
        
        if modo_serie_temp > 0:
            #Estamos en un canal que puede seleccionar entre gestionar Series completas o por Temporadas
            #Tendrá una línea para Añadir la Serie completa y otra para Añadir sólo la Temporada actual

            if item.action == 'get_seasons':                    #si es actualización desde videoteca, título estándar
                #Si hay una nueva Temporada, se activa como la actual
                try:
                    if item.library_urls[scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')] != item.url and (item.contentType == "season" or modo_ultima_temp):
                        item.library_urls[scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')] = item.url     #Se actualiza la url apuntando a la última Temporada
                        from core import videolibrarytools      #Se fuerza la actualización de la url en el .nfo
                        itemlist_fake = []                      #Se crea un Itemlist vacio para actualizar solo el .nfo
                        videolibrarytools.save_tvshow(item, itemlist_fake)      #Se actualiza el .nfo
                except:
                    logger.error("ERROR 08: EPISODIOS: No se ha podido actualizar la URL a la nueva Temporada")
                    logger.error(traceback.format_exc())
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", extra="episodios", contentType='episode'))
                
            elif modo_serie_temp == 1:      #si es Serie damos la opción de guardar la última temporada o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir última Temp. a Videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, \
                            url=item_local.url, extra="episodios", add_menu=True))
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", contentType="tvshow", extra="episodios", add_menu=True))

            else:                           #si no, damos la opción de guardar la temporada actual o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", contentType="tvshow", extra="episodios", add_menu=True))
                if item.add_videolibrary and not item.add_menu:
                    item.contentSeason = contentSeason
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Temp. a Videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, \
                            extra="episodios", add_menu=True))

        else:                               #Es un canal estándar, sólo una linea de Añadir a Videoteca
            itemlist.append(item.clone(title="[COLOR yellow]Añadir esta serie a videoteca-[/COLOR]" + \
                            title, action="add_serie_to_library", extra="episodios", add_menu=True, 
                            contentType='episode'))
        
    #Si intervención judicial, alerto!!!
    if item.intervencion and not item.downloadFilename:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() \
                            + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', \
                            thumbnail=thumb_intervenido, contentType='episode'))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt and not item.downloadFilename:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() 
                        + '[/COLOR] [ALT ] en uso', contentType='episode'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() 
                        + '[/COLOR] inaccesible', contentType='episode'))
    
    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist

    if item.add_videolibrary:                               #Estamos Añadiendo a la Videoteca.
        del item.add_videolibrary                           #Borramos ya el indicador
        if item.add_menu:                                   #Opción que avisa si se ha añadido a la Videoteca 
            del item.add_menu                               #desde la página de Episodios o desde Menú Contextual   

    #logger.debug(item)
    
    return (item, itemlist)


def find_seasons(item, modo_ultima_temp_alt, max_temp, max_nfo, list_temps=[], patron_season='', patron_quality=''):
    logger.info()
    
    # Si hay varias temporadas, buscamos todas las ocurrencias y las filtrados por TMDB, calidad e idioma
    list_temp = []
    itemlist = []

    if not patron_quality:
        patron_quality = '(?i)(?:Temporada|Miniserie)(?:-(.*?)(?:\.|\/|-$|$))'
    try:
        item_search = item.clone()
        item_search.extra = 'search'
        item_search.extra2 = 'episodios'
        title = scrapertools.find_single_match(item_search.contentSerieName, '(^.*?)\s*(?:$|\(|\[)')    # Limpiamos un poco el título
        item_search.title = title
        item_search.infoLabels = {}                                             # Limpiamos infoLabels
        
        # Llamamos a 'Listado' para que procese la búsqueda
        channel = __import__('channels.%s' % item_search.channel, None, None, ["channels.%s" % item_search.channel])
        itemlist = getattr(channel, "search")(item_search, title.lower())

        if len(itemlist) == 0:
            list_temps.append(item.url)

        for item_found in itemlist:                                             # Procesamos el Itemlist de respuesta
            #logger.debug(item_found.infoLabels['tmdb_id'] + ' / ' + item.infoLabels['tmdb_id'])
            #logger.debug(str(item_found.language) + ' / ' + str(item.language))
            #logger.debug(str(item_found.quality) + ' / ' + str(item.quality))
            if item_found.url in str(list_temps):                               # Si ya está la url, pasamos a la siguiente
                continue
            if not item_found.infoLabels['tmdb_id']:                            # tiene TMDB?
                continue
            if item_found.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']:  # Es el mismo TMDB?
                continue
            if item.language and item_found.language:                           # Es el mismo Idioma?
                if item.language != item_found.language:
                    continue
            if item.quality and item_found.quality:                             # Es la misma Calidad?, si la hay...
                if item.quality != item_found.quality:
                    continue
            elif scrapertools.find_single_match(item.url, patron_quality) != \
                        scrapertools.find_single_match(item_found.url, patron_quality):  # Coincide la calidad? (alternativo)
                continue
            list_temps.append(item_found.url)                                   # Si hay ocurrencia, guardamos la url
        
        if len(list_temps) > 1:
            list_temps = sorted(list_temps)                                     # Clasificamos las urls
            item.url = list_temps[-1]                                           # Guardamos la url de la última Temporada en .NFO

        if not patron_season:
            patron_season = '(?i)-(\d+)-(?:Temporada|Miniserie)'                # Probamos este patron de temporadas
            if not scrapertools.find_single_match(list_temps[-1], patron_season):   # Está la Temporada en la url en este formato?
                patron_season = '(?i)(?:Temporada|Miniserie)-(\d+)'             # ... usamos otro

        if max_temp >= max_nfo and item.library_playcounts and modo_ultima_temp_alt:    # Si viene de videoteca, solo tratamos lo nuevo
            for url in list_temps:
                if scrapertools.find_single_match(url, patron_season):          # Está la Temporada en la url?
                    try:                                                        # Miramos si la Temporada está procesada
                        if int(scrapertools.find_single_match(url, patron_season)) >= max_nfo:
                            list_temp.append(url)                               # No está procesada, la añadimos
                    except:
                        list_temp.append(url)
                else:                                                           # Si no está la Temporada en la url, se añade la url
                    list_temp.append(url)                                       # Por seguridad, la añadimos
        else:
            list_temp = list_temps[:]
    
    except:
        list_temp = []
        list_temp.append(item.url)
        logger.error(traceback.format_exc())
    
    #logger.debug(list_temp)
    
    return list_temp

    
def post_tmdb_findvideos(item, itemlist):
    logger.info()
    
    """
        
    Llamada para crear un pseudo título con todos los datos relevantes del vídeo.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título. Lleva un control del num. de episodios por temporada
    
    La llamada al método desde Findvideos, al principio, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
        
    En Itemlist devuelve un Item con el pseudotítulo.  Ahí el canal irá agregando el resto.
    
    """
    #logger.debug(item)
 
    # Saber si estamos en una ventana emergente lanzada desde una viñeta del menú principal,
    # con la función "play_from_library"
    item.unify = False
    Window_IsMedia = False
    try:
        import xbmc
        if xbmc.getCondVisibility('Window.IsMedia') == 1:
            Window_IsMedia = True
            item.unify = config.get_setting("unify")
    except:
        item.unify = config.get_setting("unify")
        logger.error(traceback.format_exc())
    
    if item.contentSeason_save:                                                 #Restauramos el num. de Temporada
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save
    
    if item.library_filter_show:
        del item.library_filter_show

    #Salvamos la información de max num. de episodios por temporada para despues de TMDB
    num_episodios = item.contentEpisodeNumber
    if item.infoLabels['temporada_num_episodios'] and item.contentEpisodeNumber <= item.infoLabels['temporada_num_episodios']:
        num_episodios = item.infoLabels['temporada_num_episodios']

    # Obtener la información actualizada del vídeo.  En una segunda lectura de TMDB da más información que en la primera
    #if not item.infoLabels['tmdb_id'] or (not item.infoLabels['episodio_titulo'] and item.contentType == 'episode'):
    #    tmdb.set_infoLabels_item(item, True)
    #elif (not item.infoLabels['tvdb_id'] and item.contentType == 'episode') or item.contentChannel == "videolibrary":
    #    tmdb.set_infoLabels_item(item, True)
    idioma = idioma_busqueda
    if 'VO' in str(item.language):
        idioma = idioma_busqueda_VO
    try:
        tmdb.set_infoLabels_item(item, seekTmdb=True, idioma_busqueda=idioma)   #TMDB de cada Temp
    except:
        logger.error(traceback.format_exc())
    #Restauramos la información de max num. de episodios por temporada despues de TMDB
    try:
        if item.infoLabels['temporada_num_episodios']:
            if int(num_episodios) > int(item.infoLabels['temporada_num_episodios']):
                item.infoLabels['temporada_num_episodios'] = num_episodios
        else:
            item.infoLabels['temporada_num_episodios'] = num_episodios
        if item.infoLabels['number_of_seasons'] == 1 and item.infoLabels['number_of_episodes'] > item.infoLabels['temporada_num_episodios']:
            item.infoLabels['temporada_num_episodios'] = item.infoLabels['number_of_episodes']
    except:
        logger.error(traceback.format_exc())

    #Si no existe "clean_plot" se crea a partir de "plot"
    if not item.clean_plot and item.infoLabels['plot']:
        item.clean_plot = item.infoLabels['plot']
    
    #Ajustamos el nombre de la categoría
    if item.channel == channel_py:
        category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        if category:
            item.category = category
            
    # Comprobamos las marcas de visto/no visto
    playcount = 0
    if item.video_path and check_marks_in_videolibray(item):
        playcount = 1
    
    if not config.get_setting("pseudo_titulos", item.channel, default=False) or item.downloadFilename:
        if playcount:
            item.infoLabels["playcount"] = 1
        return (item, itemlist)
    
    if item.armagedon:                                                          #Es una situación catastrófica?
        itemlist.append(item.clone(action='', title=item.category + ': [COLOR hotpink]Usando enlaces de emergencia[/COLOR]', 
                        folder=False))
    
    #Quitamos el la categoría o nombre del título, si lo tiene
    if item.contentTitle:
        item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
        item.title = re.sub(r' -%s-' % item.category, '', item.title)
    
    #Limpiamos de año y rating de episodios
    if item.infoLabels['episodio_titulo']:
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\[.*?\]', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\(.*?\)', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = item.infoLabels['episodio_titulo'].replace(item.contentSerieName, '')
    if item.infoLabels['aired'] and item.contentType == "episode":
        item.infoLabels['year'] = scrapertools.find_single_match(str(item.infoLabels['aired']), r'\/(\d{4})')

    rating = ''                                                                 #Ponemos el rating
    try:
        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
            rating = float(item.infoLabels['rating'])
            rating = round(rating, 1)
            if rating == 0.0:
                    rating = ''
    except:
        logger.error(traceback.format_exc())

    if item.quality.lower() in ['gb', 'mb']:
        item.quality = item.quality.replace('GB', 'G B').replace('Gb', 'G b').replace('MB', 'M B').replace('Mb', 'M b')

    #busco "duration" en infoLabels
    tiempo = 0
    if item.infoLabels['duration']:
        try:
            if config.get_platform(True)['num_version'] < 18 or not Window_IsMedia:
                tiempo = item.infoLabels['duration']
            elif xbmc.getCondVisibility('Window.IsMedia') == 1:
                item.quality = re.sub(r'\s?\[\d+:\d+\ h]', '', item.quality)
            else:
                tiempo = item.infoLabels['duration']
        except:
            tiempo = item.infoLabels['duration']
            logger.error(traceback.format_exc())
    
    elif item.contentChannel == 'videolibrary':                                     #No hay, viene de la Videoteca? buscamos en la DB
    #Leo de la BD de Kodi la duración de la película o episodio.  En "from_fields" se pueden poner las columnas que se quiera
        nun_records = 0
        try:
            if item.contentType == 'movie':
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c11')  #Leo de la BD de Kodi la duración de la película
            else:
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c09')  #Leo de la BD de Kodi la duración del episodio
        except:
            logger.error(traceback.format_exc())
        if nun_records > 0:                                                         #Hay registros?
            #Es un array, busco el campo del registro: añadir en el FOR un fieldX por nueva columna
            for strFileName, field1 in records: 
                tiempo = field1

    try:                                                                            #calculamos el timepo en hh:mm
        tiempo_final = int(tiempo)                                                  #lo convierto a int, pero puede se null
        if tiempo_final > 0:                                                        #Si el tiempo está a 0, pasamos
            if tiempo_final > 700:                                                  #Si está en segundos
                tiempo_final = old_div(tiempo_final, 60)                            #Lo transformo a minutos
            #horas = tiempo_final / 60
            horas = old_div(tiempo_final, 60)                                       #Lo transformo a horas
            resto = tiempo_final - (horas * 60)                                     #guardo el resto de minutos de la hora
            if not scrapertools.find_single_match(item.quality, '(\[\d+:\d+)'):     #si ya tiene la duración, pasamos
                item.quality += ' [/COLOR][COLOR white][%s:%s h]' % (str(horas).zfill(2), str(resto).zfill(2))     #Lo agrego a Calidad del Servidor
    except:
        logger.error(traceback.format_exc())
        
    #Ajustamos el nombre de la categoría
    if item.channel != channel_py:
        item.category = item.channel.capitalize()
    
    #Formateamos de forma especial el título para un episodio
    title = ''
    title_gen = ''
    if item.contentType == "episode":                                                           #Series
        title = '%sx%s' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))    #Temporada y Episodio
        if item.infoLabels['temporada_num_episodios']:
            title = '%s (de %s' % (title, str(item.infoLabels['temporada_num_episodios']))     #Total Episodios
            
        if item.infoLabels['number_of_episodes'] and item.infoLabels['number_of_seasons'] > 1:
            title += ', de %sx%s' % (str(item.infoLabels['number_of_seasons']), \
                    str(item.infoLabels['number_of_episodes']))   
        title += ')'
        
        #Si son episodios múltiples, y viene de Videoteca, ponemos nombre de serie        
        if (" al " in item.title or " Al " in item.title) and not "al " in item.infoLabels['episodio_titulo']: 
            title = '%s al %s - ' % (title, scrapertools.find_single_match(item.title, '[al|Al] (\d+)'))
        else:
            title = '%s %s' % (title, item.infoLabels['episodio_titulo'])                       #Título Episodio
        title_gen = '%s, ' % title
        
    if item.contentType == "episode" or item.contentType == "season":                           #Series o Temporadas
        title_gen += '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] [%s]' % \
                        (item.contentSerieName, item.infoLabels['year'], rating, item.quality, str(item.language), \
                        scrapertools.find_single_match(item.title, '\s\[(\d+,?\d*?\s\w[b|B])\]'))   #Rating, Calidad, Idioma, Tamaño
        if item.infoLabels['status'] and (item.infoLabels['status'].lower() == "ended" \
                        or item.infoLabels['status'].lower() == "canceled"):
            title_gen = '[TERM.] %s' % title_gen            #Marca cuando la Serie está terminada y no va a haber más producción
        item.title = title_gen

    else:                                                   #Películas
        title = item.title
        title_gen += '%s [COLOR yellow][%s][/COLOR] [%s]' % (item.contentTitle, item.infoLabels['year'], rating)  #Rating, Calidad, Idioma, Tamaño

    #Limpiamos etiquetas vacías
    title_gen = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', title_gen).strip()  #Quitamos etiquetas vacías
    title_gen = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', title_gen).strip()            #Quitamos colores vacíos
    title_gen = title_gen.replace(" []", "").strip()                                    #Quitamos etiquetas vacías
    title_videoteca = title_gen                                                         #Salvamos el título para Videoteca

    if not item.unify:                                                      #Si Titulos Inteligentes NO seleccionados:
        title_gen = '**- [COLOR gold]Enlaces Ver: [/COLOR]%s[COLOR gold] -**[/COLOR]' % (title_gen)
    else:                                                                   #Si Titulos Inteligentes SÍ seleccionados:
        title_gen = '[COLOR gold]Enlaces Ver: [/COLOR]%s' % (title_gen)    

    if item.channel_alt:
        title_gen = '[COLOR yellow]%s [/COLOR][ALT]: %s' % (item.category.capitalize(), title_gen)
    #elif (config.get_setting("quit_channel_name", "videolibrary") == 1 or item.channel == channel_py) and item.contentChannel == "videolibrary":
    else:
        title_gen = '[COLOR white]%s: %s' % (item.category.capitalize(), title_gen)

    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido, folder=False))
        del item.intervencion
    
    #Pintamos el pseudo-título con toda la información disponible del vídeo
    itemlist.append(item.clone(action="", title=title_gen, folder=False))       #Título con todos los datos del vídeo
    
    if item.action == 'show_result':                                            #Viene de una búsqueda global
        channel = item.channel.capitalize()
        if item.from_channel == channel_py or item.channel == channel_py:
            channel = item.category
        elif item.from_channel:
            channel = item.from_channel.capitalize()
        item.quality = '[COLOR yellow][%s][/COLOR] %s' % (channel, item.quality)
    
    #agregamos la opción de Añadir a Videoteca para péliculas (no series)
    if (item.contentType == 'movie' or item.contentType == 'season') and item.contentChannel != "videolibrary":
        #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
        itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="peliculas", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))
        
    if item.contentType == 'movie' and item.contentChannel != "videolibrary":
        itemlist.append(item.clone(title="**-[COLOR yellow] Añadir a la videoteca [/COLOR]-**", 
                    action="add_pelicula_to_library", extra="peliculas", from_action=item.action, 
                    from_title_tmdb=item.title))
    
    #Añadimos la opción de ver trailers
    if item.contentChannel != "videolibrary":
        itemlist.append(item.clone(channel="trailertools", title="**-[COLOR magenta] Buscar Trailer [/COLOR]-**", 
                    action="buscartrailer", context=""))
        
    #Si tiene contraseña, la pintamos
    if 'RAR-' in item.torrent_info and not item.password:
        item = find_rar_password(item)
    if item.password:
        itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                    + item.password + "'", folder=False))
    
    #Si es ventana damos la opción de descarga, ya que no hay menú contextual
    if not Window_IsMedia:
        if item.contentChannel: del item.contentChannel
        if item.contentType == 'movie': contentType = 'Película'
        if item.contentType == 'episode': contentType = 'Episodio'
        itemlist.append(item.clone(title="-Descargar %s-" % contentType, channel="downloads", server='torrent', 
                        action="save_download", from_channel=item.channel, from_action='play', folder=False))
        if item.contentType == 'episode':
            itemlist.append(item.clone(title="-Descargar Epis NO Vistos-", channel="downloads", contentType="tvshow", 
                        action="save_download", from_channel=item.channel, from_action='episodios', folder=False,  
                        sub_action="unseen"))
            item.quality = scrapertools.find_single_match(item.quality, '(.*?)\s\[')
            itemlist.append(item.clone(title="-Descargar Temporada-", channel="downloads", contentType="season", 
                        action="save_download", from_channel=item.channel, from_action='episodios', folder=False,  
                        sub_action="season"))
            itemlist.append(item.clone(title="-Descargar Serie-", channel="downloads", contentType="tvshow", 
                        action="save_download", from_channel=item.channel, from_action='episodios', folder=False,  
                        sub_action="tvshow"))

    if playcount:
        item.infoLabels["playcount"] = 1
    #logger.debug(item)
    
    return (item, itemlist)


def identifying_links(data, timeout=15, headers=None, referer=None, post=None, follow_redirects=True):
    if not PY3:
        from lib import alfaresolver
    else:
        from lib import alfaresolver_py3 as alfaresolver
    
    patron = '<script\s*src="([^"]+\/lazy\/js\/\S*.js)"\s*type="text\/\w+script">\s*<\/script>'
    url = scrapertools.find_single_match(data, patron)
    data_new = httptools.downloadpage(url, timeout=timeout, headers=headers, referer=referer, 
                                      post=post, follow_redirects=follow_redirects, alfa_s=True).data
    if PY3 and isinstance(data_new, bytes):
        data_new = "".join(chr(x) for x in bytes(data_new))
    data_new = re.sub(r"\n|\r|\t", "", data_new)
    
    try:
        for x in range(10):
            data_new = alfaresolver.identifying_links(data_new)
            
    except:
        pass

    return data_new.replace("'", '"')


def check_title_in_videolibray(item, video_list_init=False):
    logger.info()
    
    """
    Comprueba si el item listado está en la videoteca Alfa.  Si lo está devuelve True
    Si se ha marcado "video_list_init", se devuleve la lista de peliculas y series en la videoteca Alfa
    """
    
    global video_list
    res = False

    if not item.infoLabels['tmdb_id'] and not video_list_init:
        return res, ''
        
    if item.video_path and not video_list_init:
        return True, ''
    
    if item.contentType == 'movie' or video_list_init:
        videolibrary_path = movies_videolibrary_path
        if video_list_init:
            video_list = filetools.listdir(videolibrary_path)
    if item.contentType != 'movie' or video_list_init:
        videolibrary_path = series_videolibrary_path
        if video_list_init:
            video_list += filetools.listdir(videolibrary_path)
            return True, video_list

    if not filetools.exists(videolibrary_path):
        return res, ''
    
    for title in filetools.listdir(videolibrary_path):
        if item.infoLabels['imdb_id'] in title or item.infoLabels['tmdb_id'] in title:
            res = True
            break

    return res, video_list


def check_nfo_quality(item):
    logger.info("%s [%s], %s" % (item.contentSerieName.lower(), item.infoLabels['imdb_id'] \
                    or 'tmdb_'+item.infoLabels['tmdb_id'], item.infoLabels['quality']))
    global list_nfos
    
    """
    Comprueba si la calidad del item listado coincide con la del .nfo de la serie en la videoteca.  Devuelve True si coincide
    """
    
    if not item.infoLabels['imdb_id'] and not item.infoLabels['tmdb_id']:
        return False
    
    id_tmdb = item.infoLabels['imdb_id']
    if not id_tmdb:
        id_tmdb = "tmdb_%s" % item.infoLabels['tmdb_id']
    serie_name = "%s [%s]" % (item.contentSerieName.lower(), id_tmdb)
    serie_name_tmdb = "%s [tmdb_%s]" % (item.contentSerieName.lower(), item.infoLabels['tmdb_id'])
        
    if serie_name not in str(list_nfos):
        from core import videolibrarytools
        head_nfo, nfo = videolibrarytools.read_nfo(filetools.join(series_videolibrary_path, serie_name, 'tvshow.nfo'))

        if nfo and nfo.infoLabels['quality'] and serie_name not in str(list_nfos):
            list_nfos.append((serie_name, nfo.infoLabels['quality']))
            list_nfos.append((serie_name_tmdb, nfo.infoLabels['quality']))

    for serie, quality in list_nfos:
        if (serie == serie_name or serie == serie_name_tmdb) and quality == item.infoLabels['quality']:
            return True

    return False


def check_marks_in_videolibray(item, strm='', video_list_init=False):
    logger.info()
    
    """
    Comprueba si el item listado está visto/no visto en la videoteca Kodi.  Si lo está devuelve True
    """
    
    from platformcode import xbmc_videolibrary
    ret = False
    
    season_episode = strm
    if not season_episode and item.contentSeason and item.contentEpisodeNumber:
        season_episode = '%sx%s.strm' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))
    
    episode_list = xbmc_videolibrary.get_videos_watched_on_kodi(item, list_videos=True)

    if video_list_init:
        if episode_list: ret = True
        return ret, episode_list

    if not episode_list and item.video_path:
        del item.video_path
        return False
    
    if season_episode and episode_list.get(season_episode, 0) >= 1:
        return True
    else:
        return False


def context_for_videolibray(item):
    logger.info()

    if not item.video_path:
        return item

    if item.contentType == 'tvshow':
        poner_marca = config.get_localized_string(60021)
        quitar_marca = config.get_localized_string(60020)
    elif item.contentType == 'season':
        poner_marca = config.get_localized_string(60029)
        quitar_marca = config.get_localized_string(60028)
    else:
        poner_marca = config.get_localized_string(60033)
        quitar_marca = config.get_localized_string(60032)

    item.context = [{"title": quitar_marca,
                     "action": "mark_video_as_watched",
                     "channel": "videolibrary",
                     "playcount": 0},
                    {"title": poner_marca,
                     "action": "mark_video_as_watched",
                     "channel": "videolibrary",
                     "playcount": 1},
                    {"title": config.get_localized_string(70269),
                     "action": "update_tvshow",
                     "channel": "videolibrary"}]

    return item


def find_rar_password(item):
    logger.info()
    
    # Si no hay, buscamos en páginas alternativas
    rar_search = [
                 ['1', 'https://pctreload1.com/', [['<input\s*type="text"\s*id="txt_password"\s*' + \
                                'name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"']], [['capitulo-[^0][^\d]', 'None'], \
                                ['capitulo-', 'capitulo-0'], ['capitulos-', 'capitulos-0']]], 
                 ['1', 'https://pctfenix.com/', [['<input\s*type="text"\s*id="txt_password"\s*' + \
                                'name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"']], [['descargar\/', ''], ['capitulo-[^0][^\d]', 'None'], \
                                ['capitulo-', 'capitulo-0'], ['capitulos-', 'capitulos-0']]], 
                 ['1', 'https://pctmix1.com/', [['<input\s*type="text"\s*id="txt_password"\s*' + \
                                'name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"']], [['capitulo-[^0][^\d]', 'None'], \
                                ['capitulo-', 'capitulo-0'], ['capitulos-', 'capitulos-0']]], 
                 ['2', 'https://grantorrent.net/', [[]], [['series(?:-\d+)?\/', 'descargar/serie-en-hd/'], \
                                ['-temporada', '/temporada'], ['^((?!serie).)*$', 'None'], \
                                ['.net\/', '.net/descargar/peliculas-castellano/'], ['\/$', '/blurayrip-ac3-5-1/']]], 
                 ['2', 'https://mejortorrent1.net/', [[]], [['^((?!temporada).)*$', 'None'], \
                                ['.net\/', '.net/descargar/peliculas-castellano/'], ['-microhd-1080p\/$', '']]]
    ]
    
    #             ['1', 'http://planetatorrent.com/', [['<input\s*type="text"\s*id="txt_password"\s*' + \
    #                            'name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"']], [['capitulo-0', 'capitulo-'], \
    #                            ['capitulos-0', 'capitulos-']]], 
    
    url_host = scrapertools.find_single_match(item.url, '(http.*\:\/\/(?:www.)?\w+\.\w+\/)')
    dom_sufix_org = scrapertools.find_single_match(item.url, ':\/\/(.*?)[\/|?]').replace('.', '-')
    url_host_act = url_host
    url_password = item.url
    if item.referer:
        url_password = item.referer
    
    for y in ['2', '1']:
        for active, clone_id, regex_list, regex_url_list in rar_search:
            x = str(y)
            if item.password: break
            if active != x: continue
            if x == '2' and clone_id not in url_host: continue
            if x == '1' and clone_id in item.url: continue
            url_password = url_password.replace(url_host_act, clone_id)
            url_host_act = scrapertools.find_single_match(url_password, '(http.*\:\/\/(?:www.)?\w+\.\w+\/)')

            dom_sufix_clone = scrapertools.find_single_match(url_host_act, ':\/\/(.*?)\/*$').replace('.', '-')
            if 'descargas2020' not in dom_sufix_clone and 'descargas2020' not in \
                        dom_sufix_clone and 'pctreload' not in dom_sufix_clone and \
                        'pctmix' not in dom_sufix_clone: dom_sufix_clone = ''
            dom_sufix_clone = dom_sufix_clone.replace('pctmix1-com', 'pctreload1-com')
            if dom_sufix_org and url_password.endswith(dom_sufix_org):
                url_password = url_password.replace(dom_sufix_org, dom_sufix_clone)
            else:
                url_password += dom_sufix_clone
            dom_sufix_org = dom_sufix_clone

            for regex, regex_rep in regex_url_list:
                if regex_rep == 'None':
                    if scrapertools.find_single_match(url_password, regex):
                        continue
                    else:
                        break
                if regex:
                    url_password = re.sub(regex, regex_rep, url_password)
            if 'grantorrent' in url_password:
                if item.contentType == 'episode':
                    url_password = '%scapitulo-%s/' % (url_password, item.contentEpisodeNumber)
            
            if x != '1': continue
            if url_host == clone_id: continue
            try:
                data_password = ''
                data_password = re.sub(r"\n|\r|\t|(<!--.*?-->)", "", httptools.downloadpage(url_password).data)
                data_password = data_password.replace("$!", "#!").replace("'", "\"").replace("Ã±", "ñ").replace("//pictures", "/pictures")
            except:
                logger.error(traceback.format_exc(1))
            
            for regex_alt in regex_list:
                for regex in regex_alt:
                    if scrapertools.find_single_match(data_password, regex):
                        item.password = scrapertools.find_single_match(data_password, regex)
                        break
    
    logger.info('Contraseña vídeo: %s' % item.password)
    return item


def get_torrent_size(url, referer=None, post=None, torrents_path=None, data_torrent=False, \
                        timeout=5, file_list=False, lookup=True, local_torr=None, headers=None, \
                        force=False, short_pad=False, subtitles=False):
    logger.info()
    from servers import torrent
    
    """
    
    Módulo extraido del antiguo canal ZenTorrent
    
    Calcula el tamaño de los archivos que contienen un .torrent.  Descarga el archivo .torrent en una carpeta,
    lo lee y descodifica.  Si contiene múltiples archivos, suma el tamaño de todos ellos
    
    Llamada:            generictools.get_torrent_size(url, data_torrent=False)
    Entrada: url:       url del archivo .torrent
    Entrada: referer:   url de referer en caso de llamada con post
    Entrada: post:      contenido del post en caso de llamada con post
    Entrada: data_torrent:  Flag por si se quiere el contenido del .torretn de vuelta
    Salida: size:       str con el tamaño y tipo de medida ( MB, GB, etc)
    Salida: torrent_f:  dict() con el contenido del .torrent (opcional)
    Salida: files:      dict() con los nombres de los archivos del torrent y su tamaño (opcional)
    
    """
    
    def convert_size(size):
        import math
        if (size == 0):
            return '0B'
        size_name = ("B", "KB", "M·B", "G·B", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        #s = round(size / p, 2)
        s = round(old_div(size, p), 2)
        return '%s %s' % (s, size_name[i])
    
    def decode(text):
        try:
            src = tokenize(text)
            if not PY3:
                data = decode_item(src.next, src.next())                        #Py2
            else:
                data = decode_item(src.__next__, next(src))                     #Py3
            for token in src:                                                   # look for more tokens
                raise SyntaxError("trailing junk")
        except (AttributeError, ValueError, StopIteration):
            try:
                data = data
            except:
                data = src

        return data
        
    def tokenize(text, match=re.compile("([idel])|(\d+):|(-?\d+)").match):
        i = 0
        while i < len(text):
            m = match(text, i)
            s = m.group(m.lastindex)
            i = m.end()
            if m.lastindex == 2:
                yield "s"
                yield text[i:i + int(s)]
                i = i + int(s)
            else:
                yield s

    def decode_item(next, token):
        if token == "i":
            # integer: "i" value "e"
            data = int(next())
            if next() != "e":
                raise ValueError
        elif token == "s":
            # string: "s" value (virtual tokens)
            data = next()
        elif token == "l" or token == "d":
            # container: "l" (or "d") values "e"
            data = []
            tok = next()
            while tok != "e":
                data.append(decode_item(next, tok))
                tok = next()
            if token == "d":
                #data = dict(zip(data[0::2], data[1::2]))
                data = dict(list(zip(data[0::2], data[1::2])))
        else:
            raise ValueError
        return data
        
    
    #Móludo principal
    size = ''
    torrent_f = ''
    torrent_file = ''
    files = {}
    if PY3 and isinstance(url, bytes):
        url = "".join(chr(x) for x in bytes(url))
    if PY3 and isinstance(torrents_path, bytes):
        torrents_path = "".join(chr(x) for x in bytes(torrents_path))
    if PY3 and isinstance(referer, bytes):
        referer = "".join(chr(x) for x in bytes(referer))
    if PY3 and isinstance(post, bytes):
        post = "".join(chr(x) for x in bytes(post))
    if PY3 and isinstance(headers, bytes):
        headers = "".join(chr(x) for x in bytes(headers))

    try:
        #torrents_path = config.get_videolibrary_path() + '/torrents'            #path para dejar el .torrent

        #if not os.path.exists(torrents_path):
        #    os.mkdir(torrents_path)                                             #si no está la carpeta la creamos
        
        #urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
        #urllib.urlretrieve(url, torrents_path + "/generictools.torrent")        #desacargamos el .torrent a la carpeta
        #torrent_file = open(torrents_path + "/generictools.torrent", "rb").read()   #leemos el .torrent
        
        # Si es lookup, verifica si el canal tiene activado el Autoplay.  Si es así, retorna sin hacer el lookup
        if lookup and not force and not local_torr:
            is_channel = inspect.getmodule(inspect.currentframe().f_back)
            is_channel = scrapertools.find_single_match(str(is_channel), "<module\s*'channels\.(.*?)'")
            if is_channel:
                from channels import autoplay
                res = autoplay.is_active(is_channel)
                if res:
                    return 'autoplay'
        
        if not lookup: timeout = timeout * 3
        if (url and not local_torr) or url.startswith("magnet"):
            torrents_path, torrent_file, subtitles_list = torrent.caching_torrents(url, \
                        referer=referer, post=post, torrents_path=torrents_path, \
                        timeout=timeout, lookup=lookup, data_torrent=True, headers=headers)
        elif local_torr:
            torrent_file = filetools.read(local_torr, mode='rb')
            torrents_path = local_torr
        
        if not torrents_path or torrents_path == 'CF_BLOCKED' or (PY3 and isinstance(torrent_file, bytes) \
                    and torrent_file.startswith(b"magnet")) or (not PY3 and torrent_file.startswith("magnet")):
            size = 'ERROR'
            
            # si el archivo .torrent está bloqueado con CF, se intentará descargarlo a través de un browser externo
            if torrent_file and torrents_path == 'CF_BLOCKED':
                size += ' [COLOR hotpink][B]BLOQUEO[/B][/COLOR]'
                browser, res = call_browser('', lookup=True, strict=True)
                if not browser:
                    browser, res = call_browser('', lookup=True)
                if not browser:
                    size += ': [COLOR magenta][B]Instala un browser externo para usar este enlace[/B][/COLOR] (Chrome, Firefox, Opera)'
                elif res is None and not config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                    size += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
                elif res is None and config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                    size += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                elif res or config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                    if res and res is not True:
                        config.set_setting("capture_thru_browser_path", res, server="torrent")
                        size += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                    elif res and not config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                        size += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
                    else:
                        size += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                else:
                    size += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
            
            if not lookup and subtitles:
                return (size, torrents_path, torrent_f, files, subtitles_list)
            elif not lookup:
                return (size, torrents_path, torrent_f, files)
            elif file_list and data_torrent:
                return (size, torrent_f, files)
            elif file_list:
                return (size, files)
            elif data_torrent:
                return (size, torrent_f)
            return size                                         #Si hay un error, devolvemos el "size" y "torrent" vacíos

        if PY3 and isinstance(torrent_file, bytes):                             # Convertimos a String para poder hacer el decode
            torrent_file = "".join(chr(x) for x in torrent_file)
        torrent_f = decode(torrent_file)                                        #decodificamos el .torrent

        #si sólo tiene un archivo, tomamos la longitud y la convertimos a una unidad legible, si no dará error
        try:
            sizet = torrent_f["info"]['length']
            size = convert_size(sizet)
            
            files = torrent_f["info"].copy()
            if 'path' not in files: files.update({'path': ['']})
            if 'piece length' in files: del files['piece length']
            if 'pieces' in files: del files['pieces']
            if 'name' in files: del files['name']
            files = [files]
            files.append({"__name": torrent_f["info"]["name"], 'length': 0})
        except:
            pass
            
        #si tiene múltiples archivos sumamos la longitud de todos
        if not size:
            try:
                check_video = scrapertools.find_multiple_matches(str(torrent_f["info"]["files"]), "'length': (\d+).*?}")
                sizet = sum([int(i) for i in check_video])
                size = convert_size(sizet)
                
                files = torrent_f["info"]["files"][:]
                files.append({"__name": torrent_f["info"]["name"], 'length': 0})
                
            except:
                size = 'ERROR'

    except:
        size = 'ERROR'
        logger.error('ERROR al buscar el tamaño de un .Torrent: ' + str(url))
        logger.error(traceback.format_exc())
        
    #try:
    #    os.remove(torrents_path + "/generictools.torrent")                      #borramos el .torrent
    #except:
    #    pass

    if '.rar' in str(files):
        size = '[COLOR magenta][B]RAR-[/B][/COLOR]%s' % size
        
    # Puede haber errores de decode en los paths.  Se intentan arreglar
    try:
        for entry in files:
            for file, path in list(entry.items()):
                if file == 'path':
                    for x, file_r in enumerate(path):
                        entry[file][x] = scrapertools.decode_utf8_error(file_r)
                elif file == '__name':
                    entry[file] = scrapertools.decode_utf8_error(path)
    except:
        logger.error(traceback.format_exc())
        
    #logger.debug(str(url))
    logger.info(str(size))
    
    if not lookup and subtitles:
        return (size, torrents_path, torrent_f, files, subtitles_list)
    elif not lookup:
        return (size, torrents_path, torrent_f, files)
    elif file_list and data_torrent:
        return (size, torrent_f, files)
    elif file_list:
        return (size, files)
    elif data_torrent:
        return (size, torrent_f)
    return size 

    
def get_field_from_kodi_DB(item, from_fields='*', files='file'):
    logger.info()
    from builtins import next
    """
        
    Llamada para leer de la DB de Kodi los campos que se reciben de entrada (from_fields, por defecto "*") del vídeo señalado en Item
    Obviamente esto solo funciona con Kodi y si la película o serie está catalogada en las Videotecas de Alfa y Kodi
    Se puede pedir que la búdqueda se haga por archivos (defecto), o por carpeta (series)
    
    La llamada es:
        nun_records, records = generictools.get_field_from_kodi_DB(item, from_fields='cXX[, cYY,...]'[, files = 'file|folder'])
    
    Devuelve el num de registros encontrados y los registros.  Es importante que el llamador verifique que "nun_records > 0" antes de tratar "records"
    
    """

    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    VIDEOLIBRARY_PATH = config.get_videolibrary_config_path()
    VIDEOLIBRARY_REAL_PATH = config.get_videolibrary_path()
    
    if item.contentType == 'movie':                             #Agrego la carpeta correspondiente al path de la Videoteca
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_MOVIES)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
        folder = FOLDER_MOVIES
    else:
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_TVSHOWS)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
        folder = FOLDER_TVSHOWS

    #raiz, carpetas, ficheros = filetools.walk(path).next()
    raiz, carpetas, ficheros = next(filetools.walk(path))      #listo las series o películas en la Videoteca
    carpetas = [filetools.join(path, f) for f in carpetas]      #agrego la carpeta del contenido al path
    for carpeta in carpetas:                                    #busco el contenido seleccionado en la lista de carpetas
        if item.contentType == 'movie' and (item.contentTitle.lower() in carpeta or item.contentTitle in carpeta):                                                        #Películas?
            path = carpeta                                      #Almacenamos la carpeta en el path
            break
        elif item.contentType in ['tvshow', 'season', 'episode'] and (item.contentSerieName.lower() in carpeta or item.contentSerieName in carpeta):                           #Series?
            path = carpeta                                      #Almacenamos la carpeta en el path
            break
    
    path2 += '/%s/' % scrapertools.find_single_match(path, '%s.(.*?\s\[.*?\])' % folder) #Agregamos la carpeta de la Serie o Películas, formato Android
    file_search = '%'                                           #Por defecto busca todos los archivos de la carpeta
    if files == 'file':                                         #Si se ha pedido son un archivo (defecto), se busca
        if item.contentType == 'episode':                       #Si es episodio, se pone el nombre, si no de deja %
            file_search = '%sx%s.strm' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))  #Nombre para episodios

    if "\\" in path:                                            #Ajustamos los / en función de la plataforma
        path = path.replace("/", "\\")
        path += "\\"                                            #Terminamos el path con un /
    else:
        path += "/"

    if FOLDER_TVSHOWS in path:                                  #Compruebo si es CINE o SERIE
        contentType = "episode_view"                            #Marco la tabla de BBDD de Kodi Video
    else:
        contentType = "movie_view"                              #Marco la tabla de BBDD de Kodi Video
    path1 = path.replace("\\\\", "\\")                          #para la SQL solo necesito la carpeta
    path2 = path2.replace("\\", "/")                            #Formato no Windows

    #Ejecutmos la sentencia SQL
    if not from_fields:
        from_fields = '*'
    else:
        from_fields = 'strFileName, %s' % from_fields           #al menos dos campos, porque uno solo genera cosas raras
    sql = 'select %s from %s where (strPath like "%s" or strPath like "%s") and strFileName like "%s"' % (from_fields, contentType, path1, path2, file_search)
    nun_records = 0
    records = None
    try:
        if config.is_xbmc():
            from platformcode import xbmc_videolibrary
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)      #ejecución de la SQL
            records = filetools.decode(records, trans_none=0)                   # Decode de records, cambiando None por 0
            if nun_records == 0:                                                #hay error?
                logger.error("Error en la SQL: " + sql + ": 0 registros")       #No estará catalogada o hay un error en el SQL
    except:
        logger.error(traceback.format_exc())
             
    return (nun_records, records)
    
    
def fail_over_newpct1(item, patron, patron2=None, timeout=None):
    logger.info()
    import ast
    
    """
        
    Llamada para encontrar una web alternativa a un canal caído, clone de NewPct1
    
    Creamos una array con los datos de los canales alternativos.  Los datos de la tupla son:
    
        - active = 0,1      Indica si el canal no está activo o sí lo está
        - channel           nombre del canal alternativo
        - channel_host      host del canal alternativo, utilizado para el reemplazo de parte de la url
        - contentType       indica que tipo de contenido que soporta el nuevo canal en fail-overs
        - action_excluded   lista las acciones que está excluidas para ese canal
    
    La llamada al método desde el principio de Submenu, Listado_Búsqueda, Episodios y Findvideos, es:
    
        from lib import generictools
        item, data = generictools.fail_over_newpct1(item, patron[, patron2=][, timeout=])
        
        - Entrada:  patron: con este patron permite verificar si los datos de la nueva web son buenos
        - Entrada (opcional): patron2: segundo patron opcional
        - Entrada (opcional): timeout: valor de espera máximo en download de página.  Por defecto 3
        - Entrada (opcional): patron=True: pide que sólo verifique si el canal en uso está activo, si no, ofrece otro
        - Salida:   data:   devuelve los datos del la nueva web.  Si vuelve vacía es que no se ha encontrado alternativa
    
    """
    #logger.debug(item)
    
    if timeout == None:
        timeout = config.get_setting('clonenewpct1_timeout_downloadpage', channel_py)           #Timeout downloadpage
    if timeout == 0: timeout = None
    if item.action == "search" or item.action == "listado_busqueda": timeout = timeout * 2      #Mas tiempo para búsquedas
    
    data = ''
    channel_failed = ''
    url_alt = []
    decode_code = 'iso-8859-1'
    item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
    if not item.extra2:
        item.extra2 = 'z9z8z7z6z5'

    patron_alt = ''
    verify_torrent = ''
    if patron is not True and '|' in patron:                                    #Comprobamos si hay dos patrones alternativos
        try:
            verify_torrent, patron1, patron_alt = patron.split('|')             #Si es así, los separamos y los tratamos
            patron = patron1
        except:
            logger.error(traceback.format_exc())
    patron = patron.replace('¡', '|')
        
    #Array con los datos de los canales alternativos
    #Cargamos en .json del canal para ver las listas de valores en settings
    fail_over = channeltools.get_channel_json(channel_py)
    for settings in fail_over['settings']:                                      #Se recorren todos los settings
        if settings['id'] == "clonenewpct1_channels_list":                      #Encontramos en setting
            fail_over = settings['default']                                     #Carga lista de clones
            break
    fail_over_list = ast.literal_eval(fail_over)
    #logger.debug(str(fail_over_list))

    if item.from_channel and item.from_channel != 'videolibrary':               #Desde search puede venir con el nombre de canal equivocado
        item.channel = item.from_channel
    #Recorremos el Array identificando el canal que falla
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        if item.channel == channel_py:
            if channel != item.category.lower():                                #es el canal/categoría que falla?
                continue
        else:
            if channel != item.channel:                                         #es el canal que falla?
                continue
        channel_failed = channel                                                #salvamos el nombre del canal o categoría
        channel_host_failed = channel_host                                      #salvamos el nombre del host
        channel_url_failed = item.url                                           #salvamos la url
        #logger.debug(channel_failed + ' / ' + channel_host_failed)
        
        if patron == True and active == '1':                                    #solo nos han pedido verificar el clone
            return (item, data)                                                 #nos vamos, con el mismo clone, si está activo
        if (item.action == 'episodios' or item.action == "update_tvshow" or item.action == "get_seasons" or item.action == 'findvideos') and item.contentType not in contentType:          #soporta el fail_over de este contenido?
            logger.error("ERROR 99: " + item.action.upper() + ": Acción no soportada para Fail-Over en canal: " + item.url)
            return (item, data)                         #no soporta el fail_over de este contenido, no podemos hacer nada
        break
        
    if not channel_failed:
        logger.error('NO CHANNEL FAILED: Patrón: ' + str(patron) + \
                    ' / fail_over_list: ' + str(fail_over_list))
        logger.error(item)
        return (item, data)                                                     #Algo no ha funcionado, no podemos hacer nada

    #Recorremos el Array identificando canales activos que funcionen, distintos del caído, que soporten el contenido
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        data_alt = ''
        if channel == channel_failed or active == '0' or item.action in action_excluded or item.extra2 in action_excluded:  #es válido el nuevo canal?
            continue
        if (item.action == 'episodios' or item.action == "update_tvshow" or \
                    item.action == "get_seasons" or item.action == 'findvideos') and \
                    item.contentType not in contentType:                        #soporta el contenido?
            continue

        #Hacemos el cambio de nombre de canal y url, conservando las anteriores como ALT
        item.channel_alt = channel_failed
        if item.channel != channel_py:
            item.channel = channel
        item.category = channel.capitalize()
        item.url_alt = channel_url_failed
        item.url = channel_url_failed
        #channel_host_bis = re.sub(r'(?i)http.*://', '', channel_host)[:-1]
        channel_host_bis = channel_host[:-1]
        #channel_host_failed_bis = re.sub(r'(?i)http.*://', '', channel_host_failed)
        channel_host_failed_bis = scrapertools.find_single_match(item.url, \
                            '((?:http.*\:)?\/\/(?:www\.)?[^\?|\/]+)(?:\?|\/)')
        item.url = item.url.replace(channel_host_failed_bis, channel_host_bis)

        if item.url.endswith('-org'):
            item.url = item.url.replace(channel_failed, channel)
            item.url = re.sub('\/\w+(-\w+)$', r'/%s\1' % channel, item.url)
        if channel == 'pctreload1' or channel == 'pctmix1':
            item.url = re.sub('\/\w+-\w+$', '/pctreload1-com', item.url)
            #item.url = re.sub('\/\w+-\w+$', '/pctnew-org', item.url)
        
        item = verify_channel_regex(item, fail_over_list)                       # Procesamos los regex de url que tenga el clone
        url_alt += [item.url]                                                   # salvamos la url para el bucle
        item.channel_host = channel_host
        #logger.debug(str(url_alt))
        
        #quitamos el código de series, porque puede variar entre webs
        if item.action == "episodios" or item.action == "get_seasons" or item.action == "update_tvshow":
            url_alt += [re.sub(r'\/\d+\/?$', '', item.url)]   #parece que con el título solo ecuentra la serie, normalmente...
        
        
        #si es un episodio, generalizamos la url para que se pueda encontrar en otro clone.  Quitamos la calidad del final de la url
        elif item.action == "findvideos" and item.contentType == "episode":
            try:
                #quitamos el 0 a la izquierda del episodio.  Algunos clones no lo aceptan
                inter1, inter2, inter3 = scrapertools.find_single_match(item.url, '(http.*?\/temporada-\d+.*?\/capitulo.?-)(\d+)(.*?\/)')
                if inter2.startswith('0'):
                    inter2 = re.sub(r'^0', '', inter2)
                else:
                    if len(inter2) == 1:
                        inter2 = '0%s' % inter2
                if inter1 + inter2 + inter3 not in url_alt:
                    url_alt += [inter1 + inter2 + inter3]
                
                #en este formato solo quitamos la calidad del final de la url
                if scrapertools.find_single_match(item.url, 'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/') not in url_alt:
                    url_alt += [scrapertools.find_single_match(item.url, 'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/')]
            except:
                logger.error("ERROR 88: " + item.action + ": Error al convertir la url: " + item.url)
                logger.error(traceback.format_exc())
        logger.debug('URLs convertidas: ' + str(url_alt))

        if patron == True:                                                      #solo nos han pedido verificar el clone
            return (item, data)                                                 #nos vamos, con un nuevo clone
        
        #Leemos la nueva url.. Puede haber varias alternativas a la url original
        for url in url_alt:
            try:
                if item.post:
                    data = re.sub(r"\n|\r|\t|(<!--.*?-->)", "", httptools.downloadpage(url, post=item.post, timeout=timeout).data)
                else:
                    data = re.sub(r"\n|\r|\t|(<!--.*?-->)", "", httptools.downloadpage(url, timeout=timeout).data)
                if not PY3:
                    data = unicode(data, decode_code, errors="replace").encode("utf-8")
                data_comillas = data.replace("'", '"')
            except:
                data = ''
                logger.error(traceback.format_exc())
            if not data:                                                        #no ha habido suerte, probamos con la siguiente url
                logger.error("ERROR 01: " + item.action + ": La Web no responde o la URL es erronea: " + url)
                continue
        
            #Hemos logrado leer la web, validamos si encontramos un línk válido en esta estructura
            #Evitar páginas engañosas que puede meter al canal en un loop infinito
            if (not ".com/images/no_imagen.jpg" in data and not ".com/images/imagen-no-disponible.jpg" in data) or item.action != "episodios":
                if patron:
                    data_alt = scrapertools.find_single_match(data, patron)
                    if not data_alt:
                        data_alt = scrapertools.find_single_match(data_comillas, patron)
                        if not data_alt and patron_alt:
                            data_alt = scrapertools.find_single_match(data, patron_alt)
                            if not data_alt and patron_alt:
                                data_alt = scrapertools.find_single_match(data_comillas, patron_alt)
                    if patron2 is not None:
                        data_alt = scrapertools.find_single_match(data_alt, patron2)
                    if not data_alt:                                            #no ha habido suerte, probamos con el siguiente canal
                        logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " \
                                        + url + " / Patron: " + patron + " / " + patron_alt)
                        web_intervenida(item, data)
                        data = ''
                        continue
                    else:
                        if not "'" in data_alt:
                            data = data.replace("'", '"')
                        item.url = url                                          #guardamos la url que funciona
                        break                                                   #por fin !!!  Este canal parece que funciona
                else:
                    #Función especial para encontrar en otro clone un .torrent válido
                    if verify_torrent == 'torrent:check:status':
                        from servers import torrent
                        if not data_alt.startswith("http"):                     #Si le falta el http.: lo ponemos
                            data_alt = scrapertools.find_single_match(item.channel_host, '(\w+:)//') + data_alt
                        if torrent.verify_url_torrent(data_alt):                #verificamos si el .torrent existe
                            item.url = url                                      #guardamos la url que funciona
                            break                                               #nos vamos, con la nueva url del .torrent verificada
                        data = ''
                        continue                                                #no vale el .torrent, continuamos
                    item.url = url                                              #guardamos la url que funciona, sin verificar
                    break                                                       #por fin !!!  Este canal parece que funciona
            else:
                logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " 
                            + url + " / Patron: " + patron + " / " +patron_alt)
                web_intervenida(item, data)
                data = ''
                continue
                
        if not data:                                                            #no ha habido suerte, probamos con el siguiente clone
            url_alt = []
            continue
        else:
            break
    
    del item.extra2                                                             #Borramos acción temporal excluyente
    if not data:                                                                #Si no ha logrado encontrar nada, salimos limpiando variables
        if item.channel == channel_py:
            if item.channel_alt:
                item.category = item.channel_alt.capitalize()
                del item.channel_alt
        else:
            if item.channel_alt:
                item.channel = item.channel_alt
                del item.channel_alt
        if item.url_alt: 
            item.url = item.url_alt
            del item.url_alt
        item.channel_host = channel_host_failed
    
    #logger.debug(item)
    
    return (item, data)

    
def verify_channel(channel):
    
    #Lista con los datos de los canales alternativos
    #Cargamos en .json del canal para ver las listas de valores en settings
    clones = channeltools.get_channel_json(channel_py)
    for settings in clones['settings']:                                         #Se recorren todos los settings
        if settings['id'] == "clonenewpct1_channels_list":                      #Encontramos en setting
            clones = settings['default']                                        #Carga lista de clones
            channel_alt = "'%s'" % channel
            if channel_alt in str(clones):                                      #Si es un clon se pone como canal newpct1, si no se deja
                channel = channel_py
            break

    return channel
    

def verify_channel_regex(item, clone_list):
    
    try:
        for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list:
            if channel_clone != item.category.lower():
                continue
            if not info_clone:
                break

            info_clone = info_clone.split(';')
            for pareja in info_clone:
                par = pareja.split(',')
                if par[1] == 'null':
                    par[1] = ''
                item.url = re.sub(par[0], par[1], item.url)
            break
        
        if item.action == 'findvideos' and 'pctreload' not in item.category.lower():
            if '/descargar/' not in item.url:
                item.url = re.sub(r'\.com\/', '.com/descargar/', item.url)
                item.url = re.sub(r'\.net\/', '.net/descargar/', item.url)
    except:
        logger.error(traceback.format_exc(1))
            
    return item

    
def web_intervenida(item, data, desactivar=True):
    logger.info()
    
    """
        
    Llamada para verificar si la caída de un clone de Newpct1 es debido a una intervención judicial
    
    La llamada al método desde  es:
    
        from lib import generictools
        item = generictools.web_intervenida(item, data[, desactivar=True])
        
        - Entrada:  data: resultado de la descarga.  Nos permite analizar si se trata de una intervención
        - Entrada:  desactivar=True:  indica que desactiva el canal o clone en caso de intervención judicial
        - Salida:   item.intervencion: devuele un array con el nombre del clone intervenido y el thumb de la autoridad que interviene.  El canal puede anunciarlo.
        - Salida:   Si es un clone de Newpct1, se desactiva el clone en el .json del Canal.  Si es otro canal, se desactiva el canal en su .json.
    
    """
    
    intervencion = ()
    judicial = ''

    #Verificamos que sea una intervención judicial
    if intervenido_policia in data or intervenido_guardia in data or intervenido_sucuri in data:
        if intervenido_guardia in data:
            judicial = 'intervenido_gc.png'                             #thumb de la Benemérita
        if intervenido_policia in data:
            judicial = 'intervenido_pn.jpeg'                            #thumb de la Policia Nacional
        if intervenido_sucuri in data:
            judicial = 'intervenido_sucuri.png'                         #thumb de Sucuri
        category = item.category
        if not item.category:
            category = item.channel
        intervencion = (category, judicial)                     #Guardamos el nombre canal/categoría y el thumb judicial
        if not item.intervencion:
            item.intervencion = []                                      #Si no existe el array, lo creamos
        item.intervencion += [intervencion]                             #Añadimos esta intervención al array
        
        logger.error("ERROR 99: " + category + ": " + judicial + ": " + item.url + ": DESACTIVADO=" + str(desactivar) + " / DATA: " + data)
        
        if desactivar == False:                                         #Si no queremos desactivar el canal, nos vamos
            return item
        
        #Cargamos en .json del canal para ver las listas de valores en settings.  Carga las claves desordenadas !!!
        json_data = channeltools.get_channel_json(item.channel)
        
        if item.channel == channel_py:                                  #Si es un clone de Newpct1, lo desactivamos
            for settings in json_data['settings']:                      #Se recorren todos los settings
                if settings['id'] == "clonenewpct1_channels_list":      #Encontramos en setting
                    action_excluded = scrapertools.find_single_match(settings['default'], "\('\d', '%s', '[^']+', '[^']*', '([^']*)'\)" % item.category.lower())               #extraemos el valor de action_excluded
                    if action_excluded:
                        if "intervenido" not in action_excluded:
                            action_excluded += ', %s' % judicial        #Agregamos el thumb de la autoridad judicial
                    else:
                        action_excluded = '%s' % judicial
                        
                    #Reemplazamos el estado a desactivado y agregamos el thumb de la autoridad judicial
                    settings['default'] = re.sub(r"\('\d', '%s', ('[^']+', '[^']*'), '[^']*'\)" % item.category.lower(),  r"('0', '%s', \1, '%s')" % (item.category.lower(), action_excluded), settings['default'])

                    break
        else:
            #json_data['active'] = False                                 #Se desactiva el canal
            json_data['thumbnail'] = ', thumb_%s' % judicial            #Guardamos el thumb de la autoridad judicial

        #Guardamos los cambios hechos en el .json
        try:
            if item.channel != channel_py:
                disabled = config.set_setting('enabled', False, item.channel)           #Desactivamos el canal
                disabled = config.set_setting('include_in_global_search', False, item.channel)      #Lo sacamos de las búquedas globales
            channel_path = filetools.join(config.get_runtime_path(), "channels", item.channel + ".json")
            with open(channel_path, 'w') as outfile:                                    #Grabamos el .json actualizado
                json.dump(json_data, outfile, sort_keys = True, indent = 2, ensure_ascii = False)
        except:
            logger.error("ERROR 98 al salvar el archivo: %s" % channel_path)
            logger.error(traceback.format_exc())

    #logger.debug(item)
    
    return item

    
def redirect_clone_newpct1(item, head_nfo=None, it=None, path=False, overwrite=False, lookup=False):
    logger.info()
    from builtins import next
    
    """
        
    Llamada para redirigir cualquier llamada a un clone de NewPct1 a NewPct1.py, o de una url de un canal caido a una alternativa
    Incluye las llamadas estándar del canal y la llamadas externas:
        - Play fron Library
        - Videolibrary Update
        
    La lógica es reemplazar item.channel por "newpct1" y dejar el nombre del clone en item.category.
    De esta forma utiliza siempre el código de NewPct1.py, aunque con las urls y apariencia del clone seleccionado por el usuario.
    
    En el caso de un canal/clone caído o intervenido judicialmente, puede reemplazar el canal en item.channel, o el clone en item.category, y la parte de item.url que se introduzca en una tabla.  Esta conversión sólo se realiza si el canal original está inactivo, pero lo realiza siempre para los clones, o si el canal de origen y destino son los mismos.
    
    Este método interroga el .json de NewPct1 para extraer la lista de canales clones.  Si item.channel es un clone de NewPct1 y está en esa lista, actualiza item.channel='newpct1'
    
    También en este .json está la tabla para la conversión de canales y urls:
        - activo:       está o no activa esta entrada
        - canal_org:    canal o clone de origen
        - canal_des:    canal o clone de destino (puede ser el mismo)
        - url_org:      parte de la url a sustituir de canal o clone de origen
        - url_des:      parte de la url a sustituir de canal o clone de destino
        - patron1:      expresión Regex aplicable a la url (opcional)
        - patron2:      expresión Regex aplicable a la url (opcional)
        - patron3:      expresión Regex aplicable a la url (opcional)
        - patron4:      expresión Regex aplicable a la url (opcional)
        - patron5:      expresión Regex aplicable a la url (opcional)
        - content_inc:  contenido al que aplica esta entrada, o * (item.contentType o item.extra)
        - content_exc:  contenido que se excluye de esta entrada (item.contentType) (opcional).  opción para 'emerg'
        - ow_force:     indicador para la acción de "videolibrary_service.py".  Puede crear la variable item.ow_force:
                            - force:    indica al canal que analize toda la serie y que videolibrary_service la reescriba
                            - auto:     indica a videolibrary_service que la reescriba
                            - no:       no acción para videolibrary_service, solo redirige en visionado de videolibrary
                            - del:      borra las estrucuturas de un determinado canal en videolibrary_service, quizás creadas por errores de un canal
                            - emerg:    funcionalidad muy similar a la de "del".  se general dinámicamente cada vez que entra un canal con el estado activado en el .json de "emergency_urls".  Permite cargar las urls de emergencia en todos los elementos existentes de la Videoteca para canal afectado
        ejemplos: 
        ('1', 'mejortorrent', 'mejortorrent1', 'http://www.mejortorrent.com/', 'https://mejortorrent1.com/', '(http.?:\/\/.*?\/)', 'http.?:\/\/.*?\/.*?-torrent.?-[^-]+-(?:[^-]+-)([^0-9]+-)', 'http.?:\/\/.*?\/.*?-torrent.?-[^-]+-(?:[^-]+-)[^0-9]+-\\d+-(Temporada-).html', 'http.?:\/\/.*?\/.*?-torrent.?-[^-]+-(?:[^-]+-)[^0-9]+-(\\d+)-', '', 'tvshow, season', '', 'force'), 
        ('1', 'mejortorrent', 'mejortorrent1', 'http://www.mejortorrent.com/', 'https://mejortorrent1.com/', '(http.?:\/\/.*?\/)', 'http.?:\/\/.*?\/.*?-torrent.?-[^-]+-([^.]+).html', '', '', '', 'movie', '', 'force')",
        ('1', 'torrentrapid', 'torrentlocura', 'http://torrentrapid.com/', 'http://torrentlocura.com/', '', '', '', '', '', '*', '', 'no'),
        ('1', 'newpct1', '', '', '', '', '', '', '', '', '*', '', 'del'),
        ('1', 'torrentrapid', 'torrentrapid', '', '', '', '', '', '', '', '*', '1 ó 2', 'emerg'),
    
    La llamada recibe el parámetro Item, el .nfo y los devuleve actualizados, así como opcionalmente el parámetro "overwrite· que puede forzar la reescritura de todos los archivos de la serie, y el parámetro "path" si viene de videolibrary_service.  Por último, recibe opcionalmente el parámetro "lookup" si se quiere solo averigurar si habrá migración para ese título, pero sin realizarla.
    
    """
    #logger.debug(item)
    #if it != None: logger.debug(it)
    if not item and not it:
        return (item, it, False)
    if not it:
        it = Item()
    if item: item_back = item.clone()
    it_back = it.clone()
    ow_force_param = True
    update_stat = 0
    delete_stat = 0
    canal_org_des_list = []
    json_path_list = []
    emergency_urls_force = False
    status_migration =  False
    patron_category = 'http.*\:\/\/(?:.*ww[^\.]*\.)?([^\.]+)\.[^\/]+(?:\/|\?|$)'
    
    #if item.ow_force == '1':                                       #Ha podido qudar activado de una pasada anteriores
    #    del item.ow_force
    #    logger.error('** item.ow_force: ' + item.path)             #aviso que ha habido una incidencia
    if it.ow_force == '1':                                          #Ha podido quedar activado de una pasada anterior
        del it.ow_force
        if path and it.infoLabels['mediatype'] in ['tvshow', 'season']:
            try:
                nfo = filetools.join(path, '/tvshow.nfo')
                filetools.write(nfo, head_nfo + it.tojson())                #escribo el .nfo de la peli por si aborta update
                logger.error('** .nfo ACTUALIZADO: it.ow_force: ' + nfo)    #aviso que ha habido una incidencia
            except:
                logger.error('** .nfo ERROR actualizar: it.ow_force: %s' % nfo)     #aviso que ha habido una incidencia
                logger.error(traceback.format_exc(1))
    
    # Si no existe el path al .nfo, se regenera
    if it.library_urls and head_nfo and path and not it.path:
        try:
            it.path = filetools.join(' ', filetools.basename(path)).strip()
            nfo = filetools.join(path, '/tvshow.nfo')
            filetools.write(nfo, head_nfo + it.tojson())                    #escribo el .nfo de la peli por si aborta update
            logger.error('** .nfo ACTUALIZADO: it.path: %s' % it.path)      #aviso que ha habido una incidencia
        except:
            logger.error('** .nfo ERROR actualizar: it.path: %s' % it.path) #aviso que ha habido una incidencia
            logger.error(traceback.format_exc(1))

    #Array con los datos de los canales alternativos
    #Cargamos en .json de Newpct1 para ver las listas de valores en settings
    fail_over_list = channeltools.get_channel_json(channel_py)
    for settings in fail_over_list['settings']:                             #Se recorren todos los settings
        if settings['id'] == "clonenewpct1_channels_list":                  #Encontramos en setting
            fail_over_list = settings['default']                            #Carga lista de clones
        if settings['id'] == "intervenidos_channels_list":                  #Encontramos en setting
            intervencion = settings['default']                              #Carga lista de clones y canales intervenidos

    #primero tratamos los clones de Newpct1
    channel_alt = item.channel
    #if item.url and not it.library_urls:
    #    channel_alt = scrapertools.find_single_match(item.url, patron_category).lower()     #Salvamos en nombre del canal o clone
    #    if not channel_alt:
    #        channel_alt = item.channel
    channel = "'%s'" % channel_alt
    category = ''
    if channel_alt != 'videolibrary':
        item.category = channel_alt.capitalize()
        category = "'%s'" % channel_alt
    channel_py_alt = 'xyz123'
    if channel in fail_over_list :                      #Si es un clone de Newpct1, se actualiza el canal y la categoría
        item.channel = channel_py
        item.category = scrapertools.find_single_match(item.url, patron_category).capitalize()
        channel_py_alt = "'%s'" % channel_py
        if item.channel_host:                                               #y se borran resto de pasadas anteriores
            del item.channel_host

    if it.emergency_urls:
        item.emergency_urls = it.emergency_urls                             #Refrescar desde el .nfo


    #Analizamos si hay series o películas que migrar, debido a que se ha activado en el .json del canal la opción "guardar" 
    #"emergency_urls = 1", y hay que calcularla para todos los episodios y película existentes en la Videoteca.
    #Si "emergency_urls" está activada para uno o más canales, se verifica en el .nfo del vídeo si ya se ha realizado
    #la carga de las urls de emergencia.  Sí se ha hecho, se ignora el proceso de conversión.  Si no, se convierte por el
    #canal en curso cuando hay item.url, o para todos los canales en item.library_urls si no hay un canal específico en curso.
    #El mecanismo consiste en generar una regla temporal de migración para cada canal activado.  Esta regla actua borrando
    #todos los .json de la serie/película.  En el caso de la serie, el proceso de actualización de la videoteca los regenerará
    #automáticamente.  En el caso de peliculas, se general aquí el json actualizado y se marca el .nfo como actualizado.
    #Cuando en el .json se activa "Borrar", "emergency_urls = 2", se borran todos los enlaces existentes
    #Cuando en el .json se activa "Actualizar", "emergency_urls = 3", se actualizan todos los enlaces existentes
    
    """
    if it.verified_encode:
        try:
            del it.verified_encode
            it.path = filetools.join(' ', filetools.basename(path)).strip()
            nfo = filetools.join(path, '/tvshow.nfo')
            filetools.write(nfo, head_nfo + it.tojson())                                #escribo el .nfo de la peli por si aborta update
            logger.error('** .nfo ACTUALIZADO: it.verified_encode: %s' % it.path)       #aviso que ha habido una incidencia
        except:
            logger.error('** .nfo ERROR actualizar: it.verified_encode: %s' % it.path)  #aviso que ha habido una incidencia
            logger.error(traceback.format_exc(1))
    
    if not it.verified_encode and path and it.library_playcounts and it.infoLabels['mediatype'] in ['tvshow', 'season', 'episode']:
        it = borrar_episodio_add_videolibrary(path, head_nfo, it)
    
    try:
        item, it = borrar_jsons_dups(item, it, path, head_nfo)      #TEMPORAL: Reparación de Videoteca con Newpct1
    except:
        logger.error('Error en el proceso de borrar_jsons_dups')
        logger.error(traceback.format_exc())
       
    status_migration = regenerate_clones()                          #TEMPORAL: Reparación de Videoteca con Newpct1
    
    verify_cached_torrents()                                        #TEMPORAL: verificamos si los .torrents son correctos
    try:                                                            #Si ha habido errores, vemos la lista y los reparamos
        json_error_path = filetools.join(config.get_runtime_path(), 'error_cached_torrents.json')
        if filetools.exists(json_error_path):                               #hay erroer que hay que reparar?
            from core import jsontools
            json_error_file = jsontools.load(filetools.read(json_error_path))   #Leemos la lista de errores
            if not json_error_file:
                filetools.remove(json_error_path)                           #si ya no quedan errores, borramos el .json
            elif path in json_error_file:                                   #está este títu,o en la lista de errores?
                json_error_file.pop(path)                                   #sí.  Lo quitamos
                if not json_error_file:
                    filetools.remove(json_error_path)                       #si ya no quedan errores, borramos el .json
                else:
                    filetools.write(json_error_path, jsontools.dump(json_error_file))   #si quedan, actualizamos el .json
                if item.contentType == 'movie':                             #si es una pelicula, forzamos su actualización
                    emergency_urls_force = True
                else:                                                       #si es una serie, que regenere los episodios que faltan (en error)
                    item.ow_force = '1'                                     #... de todas las temporadas
    except:
        logger.error('Error en el proceso de REPARACION de vídeos con .torrents dañados')
        logger.error(traceback.format_exc())

    #Arreglo temporal para Newpct1
    try:
        if channel in fail_over_list or channel_alt == 'videolibrary':
            channel_bis = channel_py
            if not item.url and it.library_urls and channel_alt == 'videolibrary':
                for canal_vid, url_vid in it.library_urls.items():              #Se recorre "item.library_urls" para buscar canales candidatos
                    canal_vid_alt = "'%s'" % canal_vid
                    if canal_vid_alt in fail_over_list:                         #Se busca si es un clone de newpct1
                        channel_bis = channel_py
                        channel_alt = canal_vid
                        channel = "'%s'" % channel_alt
                        break
                    else:
                        channel_bis = canal_vid
            if channel_bis == channel_py and config.get_setting("emergency_urls", channel_bis) == 1 and config.get_setting("emergency_urls_torrents", channel_bis) and item.emergency_urls and item.emergency_urls.get(channel_alt, False):
                raiz, carpetas_series, ficheros = filetools.walk(path).next()
                objetivo = '[%s]_01.torrent' % channel_alt
                encontrado = False
                for fichero in ficheros:
                    if objetivo in fichero:
                        encontrado = True
                        break
                if not encontrado:
                    logger.error('REGENERANDO: ' + str(item.emergency_urls))
                    item.emergency_urls.pop(channel_alt, None)
        except:
        logger.error('Error en el proceso de RECARGA de URLs de Emergencia')
        logger.error(traceback.format_exc())
    """
        
    try:    
        if item.url and not channel_py in item.url and it.emergency_urls:       #Viene de actualización de videoteca de series
            #Analizamos si el canal ya tiene las urls de emergencia: guardar o borrar
            if (config.get_setting("emergency_urls", item.channel) == 1 and (not item.emergency_urls \
                        or (item.emergency_urls and not item.emergency_urls.get(channel_alt, False)))) or \
                        (config.get_setting("emergency_urls", item.channel) == 2 \
                        and item.emergency_urls.get(channel_alt, False)) or \
                        config.get_setting("emergency_urls", item.channel) == 3 or emergency_urls_force:
                intervencion += ", ('1', '%s', '%s', '', '', '', '', '', '', '', '*', '%s', 'emerg')" % \
                        (channel_alt, channel_alt, config.get_setting("emergency_urls", item.channel))

        elif it.library_urls:                                                   #Viene de "listar peliculas´"
            for canal_vid, url_vid in list(it.library_urls.items()):            #Se recorre "item.library_urls" para buscar canales candidatos
                if canal_vid == channel_py:                                     #Si tiene Newcpt1 en canal, es un error
                    continue
                canal_vid_alt = "'%s'" % canal_vid
                if canal_vid_alt in fail_over_list:                             #Se busca si es un clone de newpct1
                    channel_bis = channel_py
                else:
                    channel_bis = canal_vid
                #Analizamos si el canal ya tiene las urls de emergencia: guardar o borrar
                if (config.get_setting("emergency_urls", channel_bis) == 1 and (not it.emergency_urls \
                        or (it.emergency_urls and not it.emergency_urls.get(canal_vid, False)))) \
                        or (config.get_setting("emergency_urls", channel_bis) == 2 \
                        and it.emergency_urls.get(canal_vid, False)) or \
                        config.get_setting("emergency_urls", channel_bis) == 3 or emergency_urls_force:
                    intervencion += ", ('1', '%s', '%s', '', '', '', '', '', '', '', '*', '%s', 'emerg')" % \
                        (canal_vid, canal_vid, config.get_setting("emergency_urls", channel_bis))
    except:
        logger.error('Error en el proceso de ALMACENAMIENTO de URLs de Emergencia')
        logger.error(traceback.format_exc())

    #Ahora tratamos las webs intervenidas, tranformamos la url, el nfo y borramos los archivos obsoletos de la serie
    if (channel not in intervencion and channel_py_alt not in intervencion and \
                        category not in intervencion and channel_alt != 'videolibrary') or not \
                        item.title or status_migration:                     #lookup o migración
        return (item, it, overwrite)                                        #... el canal/clone está listado
        
    import ast
    intervencion_list = ast.literal_eval(intervencion)                      #Convertir a Array el string
    #logger.debug(intervencion_list)

    if lookup == True:
        overwrite = False                                                   #Solo avisamos si hay cambios
    i = 0
    for activo, canal_org, canal_des, url_org, url_des, patron1, patron2, patron3, patron4, patron5, content_inc, content_exc, ow_force in intervencion_list:
        i += 1
        opt = ''
        #Es esta nuestra entrada?
        if activo == '1' and (canal_org == channel_alt or canal_org == item.category.lower() or channel_alt == 'videolibrary' or ow_force == 'del' or ow_force == 'emerg'):     
            
            if item.url:
                logger.debug('INTERV. LIST: ' + str(intervencion_list[i-1]) + 
                            ' / CHANNEL: ' + str(channel_alt) + ' / URL: ' + 
                            str(item.url))
            
            if ow_force == 'del' or ow_force == 'emerg':    #Si es un borrado de estructuras erroneas, hacemos un proceso aparte
                canal_des_def = canal_des                   #Si hay canal de sustitución para item.library_urls, lo usamos
                if not canal_des_def and canal_org in item.library_urls and len(item.library_urls) == 1:    #Si no, lo extraemos de la url
                    canal_des_def = scrapertools.find_single_match(item.library_urls[canal_org], patron_category).lower()            #salvamos la url actual de la estructura a borrar
                url_total = ''
                if item.url:
                    url_total = item.url                                    #Si existe item.url, lo salvamos para futuro uso
                if item.library_urls and canal_org in item.library_urls:    #Si existe una entrada con el canal a borrar, lo procesamos
                    if lookup == True:                                      #Queremos que el canal solo visualice sin migración?
                        overwrite = True                                    #Avisamos que hay cambios
                        continue
                    logger.error('** REGLA: ' + canal_org + ', ' + canal_des+ ', ' + ow_force)
                    logger.error('item.library_urls PREVIA: ' + str(item.library_urls))
                    url_total = item.library_urls[canal_org]                #salvamos la url actual de la estructura a borrar
                    url_total_status = False
                    if len(item.library_urls) == 1 or canal_des:            #si el nuevo canal no existe ya...
                        item.library_urls.update({canal_des_def: url_total})    #restauramos la url con el nuevo canal
                        url_total_status = True                             #marcamos esta url como válida
                        overwrite = True                                    #Le decimos que sobreescriba todos los .jsons
                        item.ow_force = '1'                                 #Le decimos que revise todas las temporadas
                    if len(item.library_urls) > 1 and ow_force == 'del':
                        item.library_urls.pop(canal_org, None)              #borramos la url del canal a borrar
                        overwrite = True                                    #Le decimos que sobreescriba todos los .jsons
                        item.ow_force = '1'                                 #Le decimos que revise todas las temporadas
                    if it.library_urls:
                        it.library_urls = item.library_urls                 #lo salvamos en el .nfo, si lo hay
                        
                    if item.url and item.url == url_total and url_total_status == False:    #si la url es la del canal borrado...
                        for canal_vid, url_vid in list(item.library_urls.items()):
                            canal_vid_alt = "'%s'" % canal_vid
                            if canal_vid_alt not in intervencion:           #... la sustituimos por la primera válida
                                item.url = url_vid                          
                                break
                        if canal_vid_alt in fail_over_list:         #Si es un clone de Newpct1, salvamos la nueva categoría
                            item.category = scrapertools.find_single_match(item.url, patron_category).capitalize()      #Salvamos categoría
                        else:
                            item.category = canal_vid.capitalize()          #si no, salvamos nueva categoría
                    logger.error('item.library_urls ACTUALIZADA: ' + str(item.library_urls))
                
                if lookup == False:                                         #si es migración completa...
                    delete_stat += 1                                        #Ya hemos actualizado algo, o habrá que hacerlo...
                    if ow_force == 'emerg': opt = content_exc               #Salvamos la opción de Guardar o Borrar enlaces
                    canal_org_des_list += [(canal_org, canal_des, url_total, opt, ow_force)]     #salvamos el resultado para su proceso

            else:
                if channel_alt == 'videolibrary':                           #Viene de videolibrary.list_movies: IMPRESCINDIBLE
                    for canal_vid, url_vid in list(item.library_urls.items()):
                        if canal_org != canal_vid:              #Miramos si canal_org de la regla está en item.library_urls
                            continue
                        else:
                            channel_alt = canal_org                         #Sí, ponermos el nombre del canal de origen
                            channel_b = "'%s'" % canal_org
                            if channel_b in fail_over_list:                 #Si es un clone de Newpct1, se actualiza a newpct1
                                channel_alt = channel_py
                    if channel_alt == 'videolibrary':
                        continue

                if item.contentType == "list":                              #Si viene de Videolibrary, le cambiamos ya el canal
                    if item.channel != channel_py:
                        item.channel = canal_des                            #Cambiamos el canal.  Si es clone, lo hace el canal
                        continue                                            #Salimos sin hacer nada más. item está casi vacío
                
                if item.contentType and item.contentType not in content_inc and "*" not in content_inc:  #Está el contenido el la lista de incluidos
                    continue
                
                if item.contentType and item.contentType in content_exc:    #Está el contenido excluido?
                    continue
                channel_enabled = 0
                channel_enabled_alt = 1
                if item.channel != channel_py:
                    try:
                        if channeltools.is_enabled(channel_alt): channel_enabled = 1    #Verificamos que el canal esté inactivo
                        if config.get_setting('enabled', channel_alt) == False: channel_enabled_alt = 0
                        channel_enabled = channel_enabled * channel_enabled_alt         #Si está inactivo en algún sitio, tomamos eso
                    except:
                        pass
                if channel_enabled == 1 and canal_org != canal_des:         #Si el canal está activo, puede ser solo...
                    continue                                                #... una intervención que afecte solo a una región
                #if ow_force == 'no' and it.library_urls:                    #Esta regla solo vale para findvideos...
                #    continue                                                #... salidmos si estamos actualizando
                if lookup == True:                                          #Queremos que el canal solo visualice sin migración?
                    if ow_force != 'no':
                        overwrite = True                                    #Avisamos que hay cambios
                    continue                                                #Salimos sin tocar archivos

                url_total = ''
                if item.url:
                    url_total = item.url
                elif not item.url and item.library_urls:
                    url_total = item.library_urls[canal_org]
                
                if item.channel == channel_py:                  #Si es un clone de Newpct1, salvamos la nueva categoría
                    item.category = scrapertools.find_single_match(item.url, patron_category).capitalize()      #Salvamos categoría
                    if canal_org != item.category.lower():
                        item.category_alt = canal_org.capitalize()
                else:
                    item.category = canal_des.capitalize()                      #si no, salvamos nueva categoría
                
                if url_org == '*':                                              #Si se quiere cambiar desde cualquier url ...
                    url_host = scrapertools.find_single_match(url_total, '(http.*\:\/\/(?:.*ww[^\.]*\.)?[^\.]+\.[^\/]+)(?:\/|\?|$)')
                    if url_host: url_total = url_total.replace(url_host, url_des)   #reemplazamos una parte de url
                elif url_des.startswith('http'):
                    if item.channel != channel_py or (item.channel == channel_py \
                            and item.category.lower() == canal_org):
                        url_total = scrapertools.find_single_match(url_total, \
                            'http.*\:\/\/(?:.*ww[^\.]*\.)?[^\?|\/]+(.*?$)')     #quitamos el http*:// inicial
                        url_total = urlparse.urljoin(url_des, url_total)        #reemplazamos una parte de url
                else:
                    if url_host: url_total = url_total.replace(url_org, url_des)    #reemplazamos una parte de url
                url = ''
                if patron1:                                                     #Hay expresión regex?
                    url += scrapertools.find_single_match(url_total, patron1)   #La aplicamos a url
                if patron2:                                                     #Hay más expresión regex?
                    url += scrapertools.find_single_match(url_total, patron2)   #La aplicamos a url
                if patron3:                                                     #Hay más expresión regex?
                    url += scrapertools.find_single_match(url_total, patron3)   #La aplicamos a url
                if patron4:                                                     #Hay más expresión regex?
                    url += scrapertools.find_single_match(url_total, patron4)   #La aplicamos a url
                if patron5:                                                     #Hay más expresión regex?
                    url += scrapertools.find_single_match(url_total, patron5)   #La aplicamos a url
                if url:
                    url_total = url                                     #Guardamos la suma de los resultados intermedios
                if item.channel == channel_py or channel in fail_over_list:     #Si es Newpct1...
                    #if item.contentType == "tvshow" and ow_force != 'no':       #parece que con el título encuentra.., ### VIGILAR
                    if item.contentType in ["tvshow", "season"] and canal_org not in canal_des: #parece que con el título solo encuentra..,
                        url_total = re.sub(r'\/\d{4,20}\/*$', '', url_total)    #mejor la serie, a menos que sea una redir del mismo canal
                        item.channel_redir = item.category
                update_stat += 1                                                #Ya hemos actualizado algo
                canal_org_des_list += [(canal_org, canal_des, url_total, opt, ow_force)]   #salvamos el resultado para su proceso
            
    if update_stat > 0 or delete_stat > 0:                  #Ha habido alguna actualización o borrado?  Entonces salvamos
        if (update_stat > 0 and path != False) or item.ow_force == '1':
            logger.error('** Lista de Actualizaciones a realizar: ' + str(canal_org_des_list))
        for canal_org_def, canal_des_def, url_total, opt_def, ow_force_def in canal_org_des_list:   #pasamos por todas las "parejas" cambiadas
            url_total_def = url_total
            if ow_force_def != 'del' and ow_force_def != 'emerg':
                if item.url:
                    item.url = url_total                                        #Salvamos la url convertida
                if item.library_urls:
                    item.library_urls.pop(canal_org_def, None)
                    item.library_urls.update({canal_des_def: url_total})
                    it.library_urls = item.library_urls
                if item.channel != channel_py and item.channel != 'videolibrary':
                    item.channel = canal_des_def                    #Cambiamos el canal.  Si es clone, lo hace el canal
                    if channel_alt == item.category.lower():                    #Actualizamos la Categoría y si la tenía
                        item.category = item.channel.capitalize()
                if ow_force_def == 'force' and item.contentType != 'movie':     #Queremos que el canal revise la serie entera?
                    item.ow_force = '1'                                         #Se lo decimos
                if ow_force_def in ['force', 'auto']:                           #Sobreescribir la series?
                    overwrite = True                                            #Sí, lo marcamos

        if it.library_urls and path != False and ow_force_def != 'no':          #Continuamos si hay .nfo, path, y queremos actualizarlo
            item.update_next = '1'
            del item.update_next                                    #Borramos estos campos para forzar la actualización ya
            it.update_next = '1'
            del it.update_next
        
            #Verificamos que las webs de los canales estén activas antes de borrar los .json, para asegurar que se pueden regenerar
            i = 0
            canal_org_des_list_ALT = []                                         #Creamos esta lista para salvar las parejas
            canal_org_des_list_ALT.extend(canal_org_des_list)                   #... y borrar de la original las web caidas
            for canal_org_def, canal_des_def, url_total, opt_def, ow_force_def in canal_org_des_list_ALT: #pasamos por las "parejas" a borrar
                if "magnet:" in url_total or not isinstance(url_total, str):    #Si la url es un Magnet, o es una lista, pasamos
                    i += 1
                    continue
                try:
                    response = httptools.downloadpage(url_total)
                except:
                    logger.error(traceback.format_exc())
                    logger.error('Web ' + canal_des_def.upper() + ' ERROR.  Regla no procesada: ' + str(canal_org_des_list[i]))
                    del canal_org_des_list[i]                                   #Borro regla
                    continue                                                    #... y paso a la siguiente
                if not response:
                    logger.error('Web ' + canal_des_def.upper() + ' INACTIVA.  Regla no procesada: ' + str(canal_org_des_list[i]))
                    del canal_org_des_list[i]                                   #Borro regla
                    continue                                                    #... y paso a la siguiente
                i += 1
            if i == 0:
                item = item_back.clone()                                        #Restauro las imágenes inciales
                it = it_back.clone()
                item.torrent_caching_fail = True                                #Marcamos el proceso como fallido
                return (item, it, False)

            # Listamos todos los ficheros de la serie, asi evitamos tener que comprobar si existe uno por uno
            canal_erase_list = []
            from core import videolibrarytools
            #raiz, carpetas_series, ficheros = filetools.walk(path).next()
            raiz, carpetas_series, ficheros = next(filetools.walk(path))
            ficheros = [filetools.join(path, f) for f in ficheros]      #Almacenamos la lista de archivos de la carpeta
            #logger.error(ficheros)
            for archivo in ficheros:
                for canal_org_def, canal_des_def, url_total, opt_def, ow_force_def in canal_org_des_list: #pasamos por las "parejas" a borrar
                    canal_erase = '[%s]' % canal_org_def
                    canal_erase_alt = "'%s'" % canal_org_def
                    canal_new = '[%s]' % canal_des_def
                    archivo_alt = "'%s'" % scrapertools.find_single_match(archivo, '\[(\w+)\].json')
                    if archivo_alt == "''": archivo_alt = "'xyz123'"
                    #logger.error(canal_erase + canal_new + archivo + archivo_alt)
                    #Borramos los .json que sean de los canal afectados, incluidos todos los de los clones de newpct1 si éste es el canal
                    if canal_erase in archivo or (ow_force_def == 'emerg' and canal_erase_alt in fail_over_list and archivo_alt in fail_over_list and it.contentType != 'movie'):
                        if canal_des_def and it.contentType == 'movie' and not '.torrent' in archivo:   #Si es película ...
                            item_json = ''
                            item_json = Item().fromjson(filetools.read(archivo))    #leemos el .json ante de borrarlo para salvar...
                            if not item_json:                                   #error al leer el .json.  Algo no funciona...
                                continue
                            title = item_json.title                             #... el título con su formato
                            language = item_json.language                       #... los idiomas, que no están en el .nfo
                            wanted = item_json.wanted                           #... y wanted con el título original
                            json_path = archivo.replace(canal_erase, canal_new) #Salvamos el path del .json para luego crearlo
                            json_path_list += [(canal_org_def, canal_des_def, url_total, json_path, title, language, wanted, ow_force_def, opt_def, archivo)]
                        filetools.remove(archivo)                               #Borramos el .json y el .torrent
                        logger.error('** BORRAMOS: ' + str(archivo))
                        if ow_force_def == 'del' or ow_force_def == 'emerg':    #Si la función es 'del' or 'emerg' ...
                            overwrite = True                                    #Le decimos que sobreescriba todos los .jsons
                            item.ow_force = '1'                                 #Le decimos que revise todas las temporadas
            
                #Si se ha cambiado algo, se actualizan los .nfo
                if it.nfo: del it.nfo                                           #Borramos variables innecesarias
                if it.path: del it.path                                         #Borramos variables innecesarias
                if it.text_color: del it.text_color                             #Borramos variables innecesarias
                if item.contentType == "movie" and ".nfo" in archivo:           #Para películas
                    archivo_nfo = archivo                                       #Guardamos el path del .nfo para futuro uso
                    if it.ow_force: del it.ow_force
                    filetools.write(archivo, head_nfo + it.tojson())            #escribo el .nfo de la peli
                if item.contentType != "movie" and "tvshow.nfo" in archivo:
                    archivo_nfo = archivo                                       #Guardamos el path del .nfo para futuro uso
                    filetools.write(archivo, head_nfo + it.tojson())            #escribo el tvshow.nfo por si aborta update
            
            #Aquí convertimos las películas.  Después de borrado el .json, dejamos que videolibrarytools lo regenere
            if item.contentType == "movie":                                     #Dejamos que regenere el archivo .json
                item_movie = item.clone()
                if item_movie.ow_force: del item_movie.ow_force
                item_movie.update_last = '1'
                if item_movie.update_last: del item_movie.update_last
                if item_movie.library_playcounts: del item_movie.library_playcounts     #Borramos lo que no es necesario en el .json
                if item_movie.library_urls: del item_movie.library_urls
                if item_movie.nfo: del item_movie.nfo
                if item_movie.path: del item_movie.path
                if item_movie.strm_path: del item_movie.strm_path
                if item_movie.text_color: del item_movie.text_color
                if item_movie.channel_host: del item_movie.channel_host
                if not item_movie.context: item_movie.context = "['buscar_trailer']"
                if not item_movie.extra: item_movie.extra = "peliculas"
                
                if json_path_list:
                    logger.error('** .json LIST: ' + str(json_path_list))
                for canal_org_def, canal_des_def, url_total, json_path, title, language, wanted, ow_force_def, opt_def, archivo in json_path_list:                                      #pasamos por todos canales
                    logger.error('** ESCRIBIMOS: ' + json_path)
                    item_movie.emergency_urls = False
                    del item_movie.emergency_urls
                    item_movie.channel = canal_des_def                          #mombre del canal migrado
                    if not item_movie.category: item_movie.category = canal_des_def.capitalize()        #categoría
                    item_movie.url = url_total                                  #url migrada
                    if title: item_movie.title = title                          #restaurmos el título con formato
                    if language: item_movie.language = language                 #restaurmos los idiomas
                    if wanted: item_movie.wanted = wanted                       #restaurmos wanted
                    item_movie.added_replacing = canal_org_def                  #guardamos la traza del canal reemplazado
                    
                    if ow_force_def == 'emerg' and opt_def in ['1', '3']:       #Si era una op. para añadir/actualizar urls de emergencia ...
                        item_movie = videolibrarytools.emergency_urls(item_movie, None, archivo)   #... ejecutamos "findvideos" del canal para obtenerlas
                        if item_movie.channel_host: del item_movie.channel_host
                        if item_movie.unify: del item_movie.unify
                        if item_movie.extra2: del item_movie.extra2
                        if item_movie.emergency_urls:                           #... si las hay ...
                            if it.emergency_urls and not isinstance(it.emergency_urls, dict):
                                del it.emergency_urls
                            if not it.emergency_urls:                           #... lo actualizamos en el .nfo
                                it.emergency_urls = dict()                      #... iniciamos la variable si no existe
                            if it.library_urls.get(canal_des_def, False):       #... y si existe el canal
                                it.emergency_urls.update({canal_des_def: True}) #... se marca como activo
                            if it.ow_force: del it.ow_force
                            filetools.write(archivo_nfo, head_nfo + it.tojson())        #actualizo el .nfo de la peli    
                        else:
                            logger.error('Error en FINDVIDEOS: ' + archivo + ' / Regla: ' + canal_org_def + ', ' + opt_def + ', ' + ow_force_def)

                    if ow_force_def == 'emerg' and opt_def == '2':  #Si era una operación para borrar urls de emergencia ...
                        if it.emergency_urls and not isinstance(it.emergency_urls, dict):
                            del it.emergency_urls
                        if it.emergency_urls and it.emergency_urls.get(item_movie.channel, False):
                            it.emergency_urls.pop(item_movie.channel, None)     #borramos la entrada del .nfo
                            if it.ow_force: del it.ow_force
                            filetools.write(archivo_nfo, head_nfo + it.tojson())        #actualizo el .nfo de la peli    

                    filetools.write(json_path, item_movie.tojson())             #Salvamos el nuevo .json de la película

    if (update_stat > 0 and path != False and ow_force_def in ['force', 'auto']) or item.ow_force == '1' or len(json_path_list) > 0:
        logger.error('ITEM cambiado')
        if it.emergency_urls:
            logger.error(it.emergency_urls)
        logger.error(item)
    if update_stat > 0 and path == False:
        if it.library_urls:
            logger.debug('URL cambiada: '+ str(it.library_urls))
        else:
            logger.debug('URL cambiada: '+ str(item.url))

    return (item, it, overwrite)
    

def borrar_episodio_add_videolibrary(path, head_nfo, nfo):
    logger.info()
    # Por error se ha creado un episodio en la actualización de la videteca que hace referencia a "añadir a la Videoteca"
    # Hay que borrar ese episodio completo (json, strm, nfo, torrents) y borraar la entrada de library_playcounts del .nfo
    # Hay que restaurar la temporada/serie como vista/no vista y hay que limpiar el Catálogo de Kodi para que borre los episodios

    from channels import videolibrary

    # Pasamos por todos los episodios de la SERIE
    sesxepi_list = []
    season = 0
    files = sorted(filetools.listdir(path), reverse=True)
    for file in files:
        if not '.json' in file:
            continue
            
        # Localizamos y cargamos el .json con el error
        """
        json_file = Item(path=filetools.join(path, file)).fromjson(
                    filetools.read(filetools.join(path, file)))
        if not 'serie a videoteca' in json_file.title.lower() and not \
                    'temp. a videoteca' in json_file.title.lower() and not \
                    'vista previa videoteca' in json_file.title.lower():
            continue
        """
        json_file = filetools.read(filetools.join(path, file))
        if 'infoLabels' in json_file:
            continue
            
        # Estraemos el nº de temporada y episodio para localizar y borrar los otros archivos del episodio (strm, nfo, torrents)
        sesxepi = '%sx%s' % (str(scrapertools.find_single_match(file, '^(\d+)x\d+\s*\[')), \
                    str(scrapertools.find_single_match(file, '^\d+x(\d+)\s*\[')).zfill(2))
        sesxepi_list += [sesxepi]
        season = str(scrapertools.find_single_match(file, '^(\d+)x\d+\s*\['))
        for file in files:
            if file.startswith(sesxepi):
                filetools.remove(filetools.join(path, file))
                logger.error('Episodio borrado: %s' % file)
        break
            
    logger.error('Serie: %s, Episodios: %s' % (filetools.basename(path), str(sesxepi_list)))
    """
    if sesxepi_list:
        # Actualizamos el .nfo borrado las entradas de library_playcounts que no procedan
        for epi, valor in list(nfo.library_playcounts.items()):
            if epi in str(sesxepi_list):
                nfo.library_playcounts.pop(epi, None)
                logger.error('pop %s: %s' % (epi, valor))
        
        # Llamamos al método que reestablece los vistos/no vistos en el .nfo
        nfo.active = 1
        nfo = videolibrary.check_season_playcount(nfo, season)
        config.set_setting('cleanlibrary', True, 'videolibrary')
        logger.error('.nfo actualizado de Serie: %s, %s' % (nfo.infoLabels['tvshowtitle'], nfo.library_playcounts))
    """
    nfo.verified_encode = True
    if nfo.verified: del nfo.verified
    filetools.write(filetools.join(path, 'tvshow.nfo'), head_nfo + nfo.tojson())
    
    return nfo


def borrar_jsons_dups(item, it, path, head_nfo):
    logger.info()
    
    contentType = ['tvshow', 'season']
    if it.contentType not in contentType or it.channel != 'videolibrary' or not item \
                or not it or not path or not head_nfo:
        return item, it
    
    logger.error('Conversión de : [%s]' % it.contentSerieName)
    claves = []
    for clave, value in list(it.library_urls.items()):
        claves.append(clave)
    
    if it.emergency_urls:
        nfo_upd = False
        for clave, value in list(it.emergency_urls.items()):
            if clave in claves:
                continue
            item.emergency_urls.pop(clave, None)
            it.emergency_urls.pop(clave, None)
            nfo_upd = True
            logger.error('Emergency_urls borrado: [%s] de %s' % (clave, str(claves)))
        if nfo_upd:
            nfo = filetools.join(path, '/tvshow.nfo')
            filetools.write(nfo, head_nfo + it.tojson())                        #escribo el .nfo
        
    if path:
        file_list = filetools.listdir(path)
        for file in file_list:
            file_del = filetools.join(path, file)
            if os.path.splitext(file_del)[1] in ['.json', '.torrent']:
                if not scrapertools.find_single_match(file, '\[(\w+)\]') in claves:
                    filetools.remove(file_del)
                    logger.error('Archivo borrado: "%s" de %s' % (file, str(claves)))

    return item, it


def verify_cached_torrents():
    logger.info()
    import json
    
    """
    Verifica que todos los archivos .torrent estén descomprimidos.  Si no lo están, los descomprime y regraba
    
    Método para uso temporal y controlado
    
    Deja el archivo verify_cached_torrents.json como marca de que se ha ejecutado para esa versión de Alfa
    """
    
    try:
        #Localiza los paths donde dejar el archivo .json de control, y de la Videoteca
        json_path = filetools.exists(filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json'))
        if json_path:
            logger.info('Torrents verificados anteriormente: NOS VAMOS')
            return
        json_path = filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json')
        json_error_path = filetools.join(config.get_runtime_path(), 'error_cached_torrents.json')
        json_error_path_BK = filetools.join(config.get_runtime_path(), 'error_cached_torrents_BK.json')
            
        #Calculamos el path absoluto a partir de la Videoteca
        torrents_movies = movies_videolibrary_path                              #path de CINE
        torrents_series = series_videolibrary_path                              #path de SERIES
        
        #Inicializa variables
        torren_list = []
        torren_list.append(torrents_movies)
        torren_list.append(torrents_series)
        i = 0
        j = 0
        k = 0
        descomprimidos = []
        errores = []
        json_data = dict()
        
        #Recorre las carpetas de CINE y SERIES de la Videoteca, leyendo, descomprimiendo y regrabando los archivos .torrent
        for contentType in torren_list:
            for root, folders, files in filetools.walk(contentType):
                for file in files:
                    if not '.torrent' in file:
                        continue
                    i += 1
                    torrent_file = ''
                    torrent_path = filetools.join(root, file)
                    torrent_file = filetools.read(torrent_path)
                    if not scrapertools.find_single_match(torrent_file, '^d\d+:\w+\d+:'):
                        logger.debug('Torrent comprimido: DESCOMPRIMIENDO: ' + str(torrent_path))
                        try:
                            torrent_file_deco = ''
                            import zlib
                            torrent_file_deco = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(torrent_file)
                        except:
                            k += 1
                            errores += [torrent_path]
                            logger.error(traceback.format_exc())
                            logger.error('No es un archivo TORRENT. Archivo borrado: ' + str(torrent_path))
                            if not json_data.get(root, False):
                                json_data[root] = 'ERROR'
                            if scrapertools.find_single_match(file, '^\d+x\d+'):
                                torrent_json = re.sub(r'\]_\d+.torrent$', '].json', torrent_path)
                                filetools.remove(torrent_json)
                            filetools.remove(torrent_path)
                            continue
                                                
                        if not scrapertools.find_single_match(torrent_file_deco, '^d\d+:\w+\d+:'):
                            logger.error('Error de DESCOMPRESIÓN: ' + str(torrent_path))
                            k += 1
                            errores += [torrent_path]
                        else:
                            filetools.write(torrent_path, torrent_file_deco)
                            j += 1
                            descomprimidos += [torrent_path]
                    else:
                        #logger.info('Torrent OK.  No hace falta descompresión: ' + str(torrent_path))
                        h = 0

        if json_data:
            filetools.write(json_error_path, json.dumps(json_data))
        filetools.write(json_error_path_BK, json.dumps(json_data))
        filetools.write(json_path, json.dumps({"torrent_verify": True}))
    except:
        logger.error('Error en el proceso de VERIFICACIÓN de los .torrents')
        logger.error(traceback.format_exc())
        
    logger.error(str(i) + ' archivos .torrent revisados. / ' + str(j) + ' descomporimidos / ' + str(k) + ' errores')
    if descomprimidos:
        logger.error('Lista de .torrents DESCOMPRIMIDOS: ' + str(descomprimidos))
    if errores:
        logger.error('Lista de .torrents en ERROR: ' + str(errores))


def regenerate_clones():
    logger.info()
    import json
    from core import videolibrarytools
    
    """
    Regenera los archivos .json que ha sido machacado con la migración.  También borrar los archivos tvshow.nfo en
    películas.
    
    Método para uso temporal y controlado
    """
    
    try:
        #Localiza los paths donde dejar el archivo .json de control, y de la Videoteca
        json_path = filetools.exists(filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json'))
        if json_path:
            logger.info('Videoteca reparada anteriormente: NOS VAMOS')
            return False
        json_path = filetools.join(config.get_runtime_path(), 'verify_cached_torrents.json')
        filetools.write(json_path, json.dumps({"CINE_verify": True}))   #Evita que se lance otro proceso simultaneo
        json_error_path = filetools.join(config.get_runtime_path(), 'error_cached_torrents.json')
        json_error_path_BK = filetools.join(config.get_runtime_path(), 'error_cached_torrents_BK.json')
            
        #Calculamos el path absoluto a partir de la Videoteca
        torrents_movies = movies_videolibrary_path                              #path de CINE
        torrents_series = series_videolibrary_path                              #path de SERIES
        
        #Cargamos en .json de Newpct1 para ver las listas de valores en settings
        fail_over_list = channeltools.get_channel_json(channel_py)
        for settings in fail_over_list['settings']:                             #Se recorren todos los settings
            if settings['id'] == "clonenewpct1_channels_list":                  #Encontramos en setting
                fail_over_list = settings['default']                            #Carga lista de clones
        
        #Inicializa variables
        torren_list = []
        torren_list.append(torrents_movies)
        #torren_list.append(torrents_series)
        i = 0
        j = 0
        k = 0
        descomprimidos = []
        errores = []
        json_data = dict()
        
        #Recorre las carpetas de CINE y SERIES de la Videoteca, leyendo, descomprimiendo y regrabando los archivos .torrent
        for contentType in torren_list:
            for root, folders, files in filetools.walk(contentType):
                nfo = ''
                newpct1 = False
                file_list = str(files)
                logger.error(file_list)
                
                #Borra los archivos Tvshow.nfo y verifica si el .nfo tiene más de un canal y uno es clone Newpct1
                for file in files:
                    #logger.info('file - nfos: ' + file)
                    if 'tvshow.nfo' in file:
                        file_path = filetools.join(root, 'tvshow.nfo')
                        filetools.remove(file_path)
                        continue
                    
                    if '.nfo' in file:
                        peli_name = file.replace('.nfo', '')
                        nfo = ''
                        try:
                            head_nfo, nfo = videolibrarytools.read_nfo(filetools.join(root, file))
                        except:
                            logger.error('** NFO: error de lectura en: ' + file)
                            break
                        if not nfo:
                            logger.error('** NFO: error de lectura en: ' + file)
                            break
                        if nfo.ow_force:                #Si tiene ow_force lo quitamos para evitar futuros problemas
                            del nfo.ow_force
                            try:
                                filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    #actualizo el .nfo
                            except:
                                logger.error('** NFO: error de escritura en: ' + file)
                                break
                        
                        if '.torrent' not in file_list and nfo.emergency_urls:
                            del nfo.emergency_urls                              #Si tiene emergency_urls, lo reseteamos
                            try:
                                filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    #actualizo el .nfo
                            except:
                                logger.error('** NFO: error de escritura en: ' + file)
                                break
                            newpct1 = True                                      #marcamos par a resetar los .jsons
                        
                        if len(nfo.library_urls) > 1:                           #Tiene más de un canal?
                            for canal, url in list(nfo.library_urls.items()):
                                canal_json = "[%s].json" % canal
                                if canal_json not in file_list:                 #Canal zomby, lo borramos
                                    logger.error('pop: ' + canal)
                                    nfo.library_urls.pop(canal, None)
                                    if nfo.emergency_urls:
                                        del nfo.emergency_urls                  #Si tiene emergency_urls, lo reseteamos
                                    try:
                                        filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    #actualizo el .nfo
                                    except:
                                        logger.error('** NFO: error de escritura en: ' + file)
                                        break
                                    newpct1 = True                              #marcamos par a resetar los .jsons
                                
                                canal_nwepct1 = "'%s'" % canal
                                if canal_nwepct1 in fail_over_list:             #Algún canal es clone de Newpct1
                                    newpct1 = True                              #Si es que sí, lo marcamos
                                    if nfo.emergency_urls:
                                        del nfo.emergency_urls                  #Si tiene emergency_urls, lo reseteamos
                                        try:
                                            filetools.write(filetools.join(root, file), head_nfo + nfo.tojson())    #actualizo el .nfo
                                        except:
                                            logger.error('** NFO: error de escritura en: ' + file)
                                            break

                #Zona para arrelgar los archivos .json
                if not newpct1:
                    continue
                for file in files:
                    file_path = filetools.join(root, file)
                    if '.json' in file:
                        logger.info('** file: ' + file)
                        canal_json = scrapertools.find_single_match(file, '\[(\w+)\].json')
                        if canal_json not in nfo.library_urls:
                            filetools.remove(file_path)                             #borramos el .json es un zomby
                        item_movie = ''
                        try:
                            item_movie = Item().fromjson(filetools.read(file_path)) #leemos el .json
                        except:
                            logger.error('** JSON: error de lectura en: ' + file)
                            continue
                        if not item_movie:
                            logger.error('** JSON: error de lectura en: ' + file)
                            continue
                        if item_movie.emergency_urls: del item_movie.emergency_urls
                        item_movie.channel = canal_json                             #mombre del canal
                        item_movie.category = canal_json.capitalize()               #categoría
                        item_movie.url = nfo.library_urls[canal_json]               #url
                        if scrapertools.find_single_match(item_movie.title, '(.*?)\[\d+.\d+\s*.\s*B\]'):
                            item_movie.title = scrapertools.find_single_match(item_movie.title, '(.*?)\[\d+.\d+\s*.\s*B\]').strip()                                                 #quitamos Size
                        if item_movie.added_replacing: del item_movie.added_replacing   #quitamos traza del canal reemplazado
                        try:
                            filetools.write(file_path, item_movie.tojson())         #Salvamos el nuevo .json de la película
                        except:
                            logger.error('** JSON: error de escritura en: ' + file)
                        else:
                            errores += [file]
                    if '.torrent' in file:
                        filetools.remove(file_path)                                 #borramos los .torrent salvados
                        
                            
        logger.error('** Lista de peliculas reparadas: ' + str(errores))
        filetools.write(json_error_path, json.dumps(json_data))
        filetools.write(json_error_path_BK, json.dumps(json_data))
        filetools.write(json_path, json.dumps({"CINE_verify": True}))                        
    except:
        filetools.remove(json_path)                             #borramos el bloqueo para que se pueda lanzar de nuevo
        logger.error('Error en el proceso de REPARACIÓN de Videoteca de CINE')
        logger.error(traceback.format_exc())
    
    return True

                            
def call_browser(url, download_path='', lookup=False, strict=False, wait=False, intent='', dataType=''):
    logger.info()
    # Basado en el código de "Chrome Launcher 1.2.0" de Jani (@rasjani) Mikkonen
    # Llama a un browser disponible y le pasa una url
    import xbmc
    import subprocess
    
    exePath = {}
    PATHS = []
    PM_LIST = ''
    creationFlags = 0
    prefs_file = ''
    res = None
    browsers = []
    SAVED_D_PATH = config.get_setting("capture_thru_browser_path", server="torrent", default="")

    try:
        # Establecemos las variables relativas a cada browser
        browser_params = {
                          "chrome": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                     ['--start-maximized', '--disable-translate', '--disable-new-tab-first-run', 
                                     '--no-default-browser-check', '--no-first-run '], 
                                     '', '"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"'], 
                          "chromium": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                       ['--noerordialogs', '--disable-session-crashed-bubble', '--disable-infobars', '--start-maximized'], 
                                       '', '"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"'], 
                          "firefox": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                      [], 
                                      'Default=(.*?)[\r|\n]', 'user_pref\s*\("browser.download.dir",\s*"([^"]+)"\)'], 
                          "opera": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                    [], 
                                    '', '"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"']
                         }

        # Establecemos las variables relativas a cada plataforma
        if xbmc.getCondVisibility("system.platform.Android"):
            try:
                ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
            except:
                ANDROID_STORAGE = ''
            if not ANDROID_STORAGE:
                if "'HOME'" in os.environ:
                    ANDROID_STORAGE = scrapertools.find_single_match(os.getenv('HOME'), '^(\/.*?)\/')
                    if not ANDROID_STORAGE:
                        ANDROID_STORAGE = '/storage'
                else:
                    ANDROID_STORAGE = '/storage'
            
            exePath = {
                       "chrome": [[ANDROID_STORAGE + '/emulated/0/Android/data/com.android.chrome',
                                   ANDROID_STORAGE + '/emulated/0/Android/data/com.chrome.canary'], 
                                  0, 'ANDROID_DATA', [], ['/user/0/com.android.chrome/app_chrome/Default/Preferences', 
                                  '/user/0/com.chrome.canary/app_chrome/Default/Preferences']], 
                       "chromium": [[ANDROID_STORAGE + '/emulated/0/Android/data/org.bromite.chromium', 
                                     ANDROID_STORAGE + '/emulated/0/Android/data/org.chromium.webview_shell'], 
                                    0, 'ANDROID_DATA', [], ['/user/0/org.bromite.chromium/app_chrome/Default/Preferences', 
                                    '/user/0/org.chromium.webview_shell/app_chrome/Default/Preferences']], 
                       "firefox": [[ANDROID_STORAGE + '/emulated/0/Android/data/org.mozilla.firefox'], 
                                   0, 'ANDROID_DATA', ['/user/0/org.mozilla.firefox/files/mozilla/installs.ini', 
                                   '/user/0/org.mozilla.firefox/files/mozilla/profiles.ini'], ['prefs.js']],
                       "opera": [[ANDROID_STORAGE + '/emulated/0/Android/data/com.opera.browser', 
                                  ANDROID_STORAGE + '/emulated/0/Android/data/com.vewd.core.integration.dia', 
                                  os.getenv('ANDROID_DATA') + '/user/0/com.vewd.core.integration.dia', 
                                  ANDROID_STORAGE + '/emulated/0/Android/data/com.opera.sdk.example', 
                                  os.getenv('ANDROID_DATA') + '/user/0/com.opera.sdk.example'], 
                                 0, 'ANDROID_DATA', [], ['/user/0/com.opera.browser/Preferences', 
                                 'user/0/com.vewd.core.integration.dia/Preferences', 'user/0/com.opera.sdk.example/Preferences']]
                      }
        
            PATHS = [ANDROID_STORAGE + '/emulated/0/Android/data', os.getenv('ANDROID_DATA') + '/user/0']
            DOWNLOADS_PATH = [filetools.join(ANDROID_STORAGE, 'emulated/0/Download')]
            
            commands = [['pm', 'list', 'packages'], ['pm', 'list packages']]
            try:
                for command in commands:
                    try:
                        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        PM_LIST, error_cmd = p.communicate()
                        if not error_cmd:
                            break
                    except:
                        continue
                if not PM_LIST: raise
                
                if PY3 and isinstance(PM_LIST, bytes):
                    PM_LIST = PM_LIST.decode()
                PM_LIST = PM_LIST.replace('\n', ', ')
            except:
                logger.error(command)
                if config.is_rooted(silent=True) == 'rooted':
                    commands = [['su', '-c', 'pm list packages'], ['su', '-c', 'pm',  'list', 'packages'], \
                                ['su', '-0', 'pm list packages'], ['su', '-0', 'pm',  'list', 'packages']]
                    for command in commands:
                        try:
                            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            PM_LIST, error_cmd = p.communicate()
                            if not error_cmd:
                                break
                        except Exception as e:
                            if not PY3:
                                e = unicode(str(e), "utf8", errors="replace").encode("utf8")
                            elif PY3 and isinstance(e, bytes):
                                e = e.decode("utf8")
                            logger.info('Command ERROR: %s, %s' % (str(command), str(e)), force=True)
                            continue
                    
                    if PY3 and isinstance(PM_LIST, bytes):
                        PM_LIST = PM_LIST.decode()
                    PM_LIST = PM_LIST.replace('\n', ', ')
                
            #logger.info('PACKAGE LIST: %s' % PM_LIST, force=True)

            PREF_PATHS = [ANDROID_STORAGE + '/emulated/0/Android/data']
            PREF_PATHS += [os.getenv('ANDROID_DATA') + '/user/0']
        
        elif xbmc.getCondVisibility("system.platform.Windows"):
            exePath = {
                       "chrome": [['%PATH%\\Google\\Chrome\\Application\\chrome.exe'], 
                                  0x00000008, 'LOCALAPPDATA', [], ['\\Google\\Chrome\\User Data\\Default\\Preferences']], 
                       "chromium": [[os.getenv('LOCALAPPDATA') + '\\Chromium\\Application\\chrome.exe'], 
                                    0x00000008, 'LOCALAPPDATA', [], ['\\Chromium\\User Data\\Default\\Preferences']], 
                       "firefox": [['%PATH%\\Mozilla Firefox\\firefox.exe'], 
                                   0x00000008, 'APPDATA', ['\\Mozilla\\Firefox\\installs.ini'], ['prefs.js']],
                       "opera": [[os.getenv('LOCALAPPDATA') + '\\Programs\\Opera\\launcher.exe'], 
                                 0x00000008, 'APPDATA', [], ['\\Opera Software\\Opera Stable\\Preferences']]
                      }
                      
            PATHS = [os.getenv('PROGRAMFILES')]
            PATHS += [os.getenv('PROGRAMFILES(X86)')]
            if not PATHS:
                PATHS = ['C:\\Program Files', 'C:\\Program Files (x86)']
            DOWNLOADS_PATH = [filetools.join(os.getenv('SYSTEMDRIVE'), os.getenv('HOMEPATH'), 'Downloads'), \
                                'D:\\Downloads', 'D:\\Mis documentos\\Downloads']
                
            PREF_PATHS = [os.getenv('LOCALAPPDATA')]
            PREF_PATHS += [os.getenv('APPDATA')]

        elif xbmc.getCondVisibility("system.platform.OSX"):
            exePath = {
                       "chrome": [['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'], 
                                  0, 'HOME', [], ['Library/Application Support/Google/Chrome/Default/Preferences']], 
                       "chromium": [['/Applications/Chromium.app/Contents/MacOS/Chromium'], 
                                    0, 'HOME', [], ['Library/Application Support/Chromium/Default/Preferences']], 
                       "firefox": [['/Applications/Firefox.app/Contents/MacOS/firefox'], 
                                   0, 'HOME', ['Library/Application Support/Firefox/installs.ini'], ['prefs.js']],
                       "opera": [['/Applications/Firefox.app/Contents/MacOS/opera'], 
                                 0, 'HOME', [], ['/Library/Application Support/com.operasoftware.Opera/Preferences']]
                      }
            
            PATHS = ['/Applications']
            DOWNLOADS_PATH = [filetools.join(os.getenv('HOME'), 'Descargas'), filetools.join(os.getenv('HOME'), 'Downloads')]
            
            PREF_PATHS = [filetools.join(os.getenv('HOME'), '/Library/Application Support')]
            
        elif xbmc.getCondVisibility("system.platform.Linux.RaspberryPi"):
            exePath = {
                       "chrome": [['%PATH%/google-chrome', '%PATH%/google-chrome-stable'], 
                                  0, 'HOME', [], ['.config/google-chrome/Default/Preferences', 
                                  '.config/google-chrome-stable/Default/Preferences', 
                                  'snap/google-chrome/current/.config/google-chrome/Default/Preferences']],
                       "opera": [['%PATH%/opera'], 
                                 0, 'HOME', [], ['.config/opera/Preferences', 
                                 'snap/opera/current/.config/opera/Preferences']], 
                       "firefox": [['%PATH%/firefox'], 
                                   0, 'HOME', ['.mozilla/firefox/installs.ini', 
                                   'snap/mozilla/current/.mozilla/firefox/installs.ini'], ['prefs.js']], 
                       "chromium": [['%PATH%/chromium', '%PATH%/chromium-browser'], 
                                    0, 'HOME', [], ['.config/chromium/Default/Preferences', 
                                    'snap/chromium/current/.config/chromium/Default/Preferences']]
                      }
            
            PATHS = ['/usr/bin', '/usr/local/bin', '/usr/sbin', '/usr/local/sbin']
            xpaths = os.getenv('PATH').split(':')
            if xpaths:
                for xpath in xpaths:
                    if xpath not in PATHS:
                        PATHS += [xpath]
            DOWNLOADS_PATH = [filetools.join(os.getenv('HOME'), 'Descargas'), 
                              filetools.join(os.getenv('HOME'), 'descargas'), 
                              filetools.join(os.getenv('HOME'), 'Downloads'), 
                              filetools.join(os.getenv('HOME'), 'downloads')]
            
            PREF_PATHS = [os.getenv('HOME')]
            PREF_PATHS += [filetools.join(os.getenv('HOME'), '.config')]
            PREF_PATHS += [filetools.join(os.getenv('HOME'), 'snap')]
        
        elif xbmc.getCondVisibility("system.platform.Linux"):
            exePath = {
                       "chrome": [['%PATH%/google-chrome', '%PATH%/google-chrome-stable'], 
                                  0, 'HOME', [], ['.config/google-chrome/Default/Preferences', 
                                  '.config/google-chrome-stable/Default/Preferences', 
                                  'snap/google-chrome/current/.config/google-chrome/Default/Preferences']], 
                       "chromium": [['%PATH%/chromium', '%PATH%/chromium-browser'], 
                                    0, 'HOME', [], ['.config/chromium/Default/Preferences', 
                                    'snap/chromium/current/.config/chromium/Default/Preferences']],
                       "opera": [['%PATH%/opera'], 
                                 0, 'HOME', [], ['.config/opera/Preferences', 
                                 'snap/opera/current/.config/opera/Preferences']], 
                       "firefox": [['%PATH%/firefox'], 
                                   0, 'HOME', ['.mozilla/firefox/installs.ini', 
                                   'snap/mozilla/current/.mozilla/firefox/installs.ini'], ['prefs.js']]
                      }
            
            PATHS = ['/usr/bin', '/usr/local/bin', '/usr/sbin', '/usr/local/sbin']
            xpaths = os.getenv('PATH').split(':')
            if xpaths:
                for xpath in xpaths:
                    if xpath not in PATHS:
                        PATHS += [xpath]
            DOWNLOADS_PATH = [filetools.join(os.getenv('HOME'), 'Descargas'), 
                            filetools.join(os.getenv('HOME'), 'descargas'), 
                            filetools.join(os.getenv('HOME'), 'Downloads'), 
                            filetools.join(os.getenv('HOME'), 'downloads')]
            
            PREF_PATHS = [os.getenv('HOME')]
            PREF_PATHS += [filetools.join(os.getenv('HOME'), '.config')]
            PREF_PATHS += [filetools.join(os.getenv('HOME'), 'snap')]

        else:
            return (False, False)
            
        # Añadimos PATHS adicionales para listar carpetas de Preferencias
        for browser, paths in list(exePath.items()):
            for path in paths[4]:
                if filetools.dirname(path):
                    PREF_PATHS += [filetools.join(os.getenv(paths[2]), filetools.dirname(path))]
            for path in paths[3]:
                if filetools.dirname(path):
                    PREF_PATHS += [filetools.join(os.getenv(paths[2]), filetools.dirname(path))]

        
        # Buscamos si está instalado un browser soportado
        for browser, paths in list(exePath.items()):
            for path in paths[0]:
                #if browser != 'chromium': continue
                if path.startswith('%PATH%'):
                    for PATH in PATHS:
                        xpath = path.replace('%PATH%', PATH)
                        if filetools.exists(xpath):
                            path = xpath
                            break
                    else:
                        if PM_LIST and filetools.basename(xpath) in PM_LIST:
                            path = xpath
                            break
                        continue

                # Se comprueba que los paths de ejecución existen.  En el caso de Android se comprueban los paths de configuración en sdcard
                if filetools.basename(path) in PM_LIST or filetools.exists(path):
                    creationFlags = paths[1]
                    try:
                        prefs_file = os.getenv(paths[2])
                        if not prefs_file and xbmc.getCondVisibility("system.platform.Android"):
                            prefs_file = '/data'
                    except:
                        if xbmc.getCondVisibility("system.platform.Android"):
                            prefs_file = '/data'
                    break
            else:
                continue
            
            browsers.append((browser, path))
            logger.info('BROWSER: %s, PATH: %s, PREFS_FILE: %s, LOOKUP: %s, STRICIT: %s, DOWNLOAD_PATH: %s, SAVED_D_PATH: %s' % \
                                (browser, path, prefs_file, lookup, strict, download_path, SAVED_D_PATH), force=True)
            # Cuando se necesita conocer el path de Downloads
            if lookup or download_path:
                res = True
                if not prefs_file:
                    return (browser.capitalize(), res)
                
                # Buscamos el path correcto para obtener el archivo de preferencias
                if paths[3]:
                    for prefs_path in paths[3]:
                        if filetools.exists(filetools.join(prefs_file, prefs_path)):
                            break
                else:
                    for prefs_path in paths[4]:
                        if filetools.exists(filetools.join(prefs_file, prefs_path)):
                            break
                
                # Opción especial para Firefox
                if browser_params[browser][2]:
                    installs = filetools.join(prefs_file, prefs_path)
                    scraper = browser_params[browser][2]
                    if xbmc.getCondVisibility("system.platform.Android"):
                        scraper = scraper.replace('Default', 'Path')
                    profile = scrapertools.find_single_match(filetools.read(installs, silent=True), scraper)
                    prefs_file = filetools.join(prefs_file, filetools.dirname(prefs_path), profile)
                    prefs_path = paths[4][0]
                
                # Accedemos al archivo de las preferencias del browser.  
                prefs_file = filetools.join(prefs_file, prefs_path)
                browser_prefs = filetools.read(prefs_file, silent=True)
                res = scrapertools.find_single_match(browser_prefs, browser_params[browser][3]).replace('\\\\', '\\')
                if not res and browser_prefs:
                    logger.debug('Archivo de Preferencias sin PARÁMETRO %s: %s' % (prefs_file, str(browser_params[browser][3])))
                elif not res:
                    logger.error('Archivo de preferencias no encontrado/accesible: %s' % (prefs_file))
                    for prefs_dir in PREF_PATHS:
                        logger.debug('Listado de %s - %s' % (prefs_dir, sorted(filetools.listdir(prefs_dir))))

                # En Android puede haber problemas de permisos.  Si no se encuentra el path, se asume un path por defecto
                if SAVED_D_PATH and not filetools.exists(SAVED_D_PATH):
                    logger.debug('Path de DESCARGAS almacenado NO EXISTE.  Reseteado: %s' % SAVED_D_PATH)
                    SAVED_D_PATH = ''
                    config.set_setting("capture_thru_browser_path", SAVED_D_PATH, server="torrent")
                if not res and not download_path and not SAVED_D_PATH:
                    for folder in DOWNLOADS_PATH:
                        if filetools.exists(folder):
                            res = folder
                            logger.debug('Path de DESCARGAS por defecto: %s' % (folder))
                            break

                # Si se ha pasado la opción de download_path y difiere del path obtenido, se pasa a otro browser
                if download_path and download_path.lower() != res.lower():
                    logger.info('Paths de DESCARGA DIFERENTES: download_PATH: %s - RES: %s' % (download_path, res), force=True)
                    continue
                # Si no se ha obtenido el path y se ha pedido la opción strict, se pasa a otro browser
                if not res and strict:
                    continue
                # Si no se ha obtenido el path y no hay ninguno guardado, se notifica
                if not res and not SAVED_D_PATH:
                    res = None
                # Si no se ha obtenido el path pero hay uno guardado, se notifica
                elif not res and SAVED_D_PATH:
                    res = True
                else:
                    break
            
            else:
                # Se ha encontrado un browser aceptable.  Se llama al browser
                break
                
        else:
            if browsers:
                browser = browsers[0][0]
                path = browsers[0][1]
                # Si hay browser(s) pero no hay res pero se ha suministrado un download path, y existe, se usa éste último con el primer browser
                if not strict and not res and (download_path or SAVED_D_PATH):
                    if download_path and filetools.exists(download_path):
                        res = download_path
                        logger.info('No RES. Se toma Path de entrada: download_path: %s' % download_path, force=True)
                    elif SAVED_D_PATH and filetools.exists(SAVED_D_PATH):
                        res = SAVED_D_PATH
                        logger.info('No RES. Se toma Path Almacenado: SAVED_D_PATH: %s' % SAVED_D_PATH, force=True)
                elif strict and not res and (download_path or SAVED_D_PATH):
                    logger.info('Browser no encontrado en mod STRICT.  Disponible: %s' % browser.capitalize(), force=True)
                    return (False, False)

            else:
                # Si no se ha encontrado ningún browser que cumpla las condiciones, se vuelve con error
                logger.error('No se ha encontrado ningún BROWSER: %s' % str(exePath))
                if PM_LIST: logger.debug('PACKAGE LIST: %s' % PM_LIST)
                logger.debug('Listado de APPS INSTALADAS en %s: %s' % (PATHS[0], sorted(filetools.listdir(PATHS[0]))))
                if len(PATHS) > 1:
                    logger.debug('Listado de APPS INSTALADAS en %s: %s' % (PATHS[1], sorted(filetools.listdir(PATHS[1]))))
                for prefs_dir in PREF_PATHS:
                    logger.debug('Listado de %s - %s' % (prefs_dir, sorted(filetools.listdir(prefs_dir))))
                return (False, False)
        
        if lookup:
            logger.info('LOOKUP: Selección BROWSER: %s, RES: %s' % (browser, res), force=True)
            return (browser.capitalize(), res)
        
        
        # Ahora hacemos la Call al Browser detectado
        # Si la plataforma es Android, se llama de una forma diferente.
        if xbmc.getCondVisibility("system.platform.Android"):
            cmd = "StartAndroidActivity(%s,%s,%s,%s)" % (filetools.basename(path), intent, dataType, url)
            logger.info('Android Browser call: %s' % cmd, force=True)
            xbmc.executebuiltin(cmd)
        
        else:
            # Se crea una página .html intermedia con los parámetros necesarios para que funcione la llamada al browser
            if browser == 'chromium':
                browser_call = url
            else:
                browser_call = filetools.join(config.get_data_path(), 'browser_call.html')
                filetools.write(browser_call, browser_params[browser][0])

            params = [path]
            # Se añaden las opciones de llamada del browser seleccionado
            for option in browser_params[browser][1]:
                params += [option]
            params += [browser_call]
            
            try:
                # Se crea un subproceso con la llama al browser
                if xbmc.getCondVisibility("system.platform.Windows"):
                    s = subprocess.Popen(params, shell=False, creationflags=creationFlags, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    s = subprocess.Popen(params, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res = s
                
                # Si se ha pedido esperar hasta que termine el browser...
                if wait:
                    output_cmd, error_cmd = s.communicate()
                    if error_cmd: res = False
                    logger.error('Error "%s" en Browser %s, Comando %s' % (str(error_cmd), browser, str(params)))
            except:
                res = False
                logger.error('Error "%s" en Browser %s, Comando %s' % (str(error_cmd), browser, str(params)))

    except:
        logger.error(traceback.format_exc())
        return (False, False)
    
    return (browser.capitalize(), res)


def dejuice(data):
    logger.info()
    # Metodo para desobfuscar datos de JuicyCodes

    juiced = scrapertools.find_single_match(data, 'JuicyCodes.Run\((.*?)\);')
    b64_data = juiced.replace('+', '').replace('"', '')
    b64_decode = base64.b64decode(b64_data)
    dejuiced = jsunpack.unpack(b64_decode)

    return dejuiced


def privatedecrypt(url, headers=None):

    data = httptools.downloadpage(url, headers=headers, follow_redirects=False).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    packed = scrapertools.find_single_match(data, '(eval\(.*?);var')
    unpacked = jsunpack.unpack(packed)
    server = scrapertools.find_single_match(unpacked, "src:.'(http://\D+)/")
    id = scrapertools.find_single_match(unpacked, "src:.'http://\D+/.*?description:.'(.*?).'")
    if server == '':
        if 'powvideo' in unpacked:
            id = scrapertools.find_single_match(unpacked, ",description:.'(.*?).'")
            server = 'https://powvideo.net'
    if server != '' and id != '':
        url = '%s/%s' % (server, id)
    else:
        url = ''
    return url


def rec(site_key, co, sa, loc):
    api_url = "https://www.google.com/recaptcha/api.js"
    headers = {
               "User-Agent": httptools.get_user_agent(),
               "Referer": loc,
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "ro-RO,ro;q=0.8,en-US;q=0.6,en-GB;q=0.4,en;q=0.2"
               }

    r_data = httptools.downloadpage(api_url, headers=headers, follow_redirects=False).data
    v = scrapertools.find_single_match(r_data, "releases/([^/]+)")
    cb = "123456789"
    base_url = "https://www.google.com/recaptcha/api2/anchor?ar=1&k=%s&co=%s&hl=ro&v=%s&size=invisible&cb%s" % (site_key, co, v, cb)

    r_data = httptools.downloadpage(base_url, headers=headers, follow_redirects=False).data
    c = scrapertools.find_single_match(r_data, 'id="recaptcha-token" value="([^"]+)"')

    t_url = "https://www.google.com/recaptcha/api2/reload?k=%s" % site_key

    post = {"v": v, "reason": "q", "k": site_key, "c": c, "sa": sa, "co": co}
    p = "v=%s&reason=q&k=%s&c=%s&sa=%s&co=%s" % (v, site_key, c, sa, co)
    head = {
            "Accept": "*/*'",
            "Accept-Language": "ro-RO,ro;q=0.8,en-US;q=0.6,en-GB;q=0.4,en;q=0.2",
            "Accept-Encoding": "deflate",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Content-Length": "%s" % len(p),
            "Connection": "keep-alive",
            "referer": base_url
            }

    r_data = httptools.downloadpage(t_url, headers=head, follow_redirects=False, post=post).data
    response = scrapertools.find_single_match(r_data, '"rresp","([^"]+)"')
    return response