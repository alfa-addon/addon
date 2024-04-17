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
    import urllib.parse as urllib
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido
    import urllib 

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
import random
import copy

from channelselector import get_thumb
from core import scrapertools
from core import servertools
from core import channeltools
from core import filetools
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config, logger, unify

import xbmc
import xbmcgui
alfa_caching = False
window = None
video_list_str = ''
cached_btdigg = {'movie': {}, 'tvshow': {}, 'episode': {}}

try:
    window = xbmcgui.Window(10000)
    alfa_caching = bool(window.getProperty("alfa_caching"))
    if not alfa_caching:
        window.setProperty("alfa_videolab_movies_list", '')
        window.setProperty("alfa_videolab_series_list", '')
except Exception:
    alfa_caching = False
    window = None
    video_list_str = ''
    logger.error(traceback.format_exc())

channel_py = "wolfmax4k"
channel_py_episode_list = {}
idioma_busqueda = 'es'
idioma_busqueda_VO = 'es,en'
movies_videolibrary_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_movies"))
series_videolibrary_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
patron_domain = r'(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
patron_host = r'((?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?[\w|\-]+\.\w+)(?:\/|\?|$)'
patron_canal = r'(?:http.*\:)?\/\/(?:ww[^\.]*)?\.?(\w+)\.\w+(?:\/|\?|$)'
patron_local_torrent = r'(?i)(?:(?:\\\|\/)[^\[]+\[\w+\](?:\\\|\/)[^\[]+\[\w+\]_\d+\.torrent|magnet\:)'
find_alt_domains = 'atomohd'   # Solo poner uno.  Alternativas: pctmix, pctmix1, pctreload, pctreload1, maxitorrent, descargas2020, pctnew
btdigg_url = config.BTDIGG_URL
btdigg_label = config.BTDIGG_LABEL
btdigg_label_B = config.BTDIGG_LABEL_B
BTDIGG_SEARCH = [{'urls': ['%s'], 'checks': [], 'limit_search': 2, 'quality_alt': '', 'language_alt': [], 'search_order': 2}]
BTDIGG_URL_SEARCH = '%ssearch_btdig/' % btdigg_url
TEST_ON_AIR = False
VIDEOLIBRARY_UPDATE = False
SIZE_MATCHES = 5000
kwargs_json = {"indent": 2, "skipkeys": True, "sort_keys": True, "ensure_ascii": True}
DEBUG = config.get_setting('debug_report', default=False) if not TEST_ON_AIR else False


def convert_url_base64(url, host='', referer=None, rep_blanks=True, force_host=False, item=Item()):
    if not TEST_ON_AIR: logger.info('URL: ' + url + ', HOST: ' + host)
    
    host_whitelist = ['mediafire.com']
    host_whitelist_skip = ['adfly.mobi']
    domain = scrapertools.find_single_match(url, patron_domain)

    url_base64 = url
    url_sufix = ''

    if scrapertools.find_single_match(url, patron_local_torrent):
        return url_base64 + url_sufix

    if ('&dn=' in url_base64 or '&tr=' in url_base64) and not 'magnet:' in url_base64:
        url_base64_list = url_base64.split('&')
        url_base64 = url_base64_list[0]
        for param in url_base64_list[1:]:
            url_sufix += '&%s' % param
    if '=http' in url_base64 and not 'magnet:' in url_base64:
        url_base64 = scrapertools.find_single_match(url_base64, '=(http.*?$)')

    if len(url_base64) > 1 and not 'magnet:' in url_base64 and not '.torrent' in url_base64:
        patron_php = r'php(?:#|\?\w=)(.*?)(?:\&|$)'
        if not scrapertools.find_single_match(url_base64, patron_php):
            patron_php = r'\?(?:\w+=.*&)?(?:urlb64|anonym)?=(.*?)(?:\&|$)'

        url_base64 = scrapertools.find_single_match(url_base64, patron_php)
        if not url_base64:
            logger.info('Url base64 vacía: Patron incorrecto: %s' % patron_php)
            url_base64 = url
        else:
            try:
                # Da hasta 20 pasadas o hasta que de error
                for x in range(20):
                    url_base64 = base64.b64decode(url_base64).decode('utf-8')
                logger.info('Url base64 después de 20 pasadas (incompleta): %s' % url_base64)
                url_base64 = url
            except Exception:
                if url_base64 and url_base64 != url:
                    if not TEST_ON_AIR: logger.info('Url base64 convertida: %s' % url_base64)
                    if rep_blanks: url_base64 = url_base64.replace(' ', '%20')
                #logger.error(traceback.format_exc())
                if not url_base64:
                    url_base64 = url
                if url_base64.startswith('magnet') or url_base64.endswith('.torrent') or (domain and domain in host_whitelist_skip):
                    return url_base64 + url_sufix
                
                from lib.unshortenit import sortened_urls
                if domain and domain in host_whitelist:
                    url_base64_bis = sortened_urls(url_base64, url_base64, host, referer=referer, alfa_s=True, item=item)
                else:
                    url_base64_bis = sortened_urls(url, url_base64, host, referer=referer, alfa_s=True, item=item)
                host_name = scrapertools.find_single_match(url_base64_bis, patron_host)
                if host_name:
                    url_base64_bis = host_name + url_base64_bis.replace(host_name, '').replace('//', '/')
                else:
                    url_base64_bis = url_base64_bis.replace('//', '/')
                domain_bis = scrapertools.find_single_match(url_base64_bis, patron_domain)
                if domain_bis: domain = domain_bis
                if url_base64_bis != url_base64:
                    url_base64 = url_base64_bis
                    if not TEST_ON_AIR: logger.info('Url base64 RE-convertida: %s' % url_base64)
                
    if not domain: domain = 'default'
    if host and host not in url_base64 and not url_base64.startswith('magnet') \
                    and (not url_base64.startswith('http') or force_host) and domain not in str(host_whitelist):
        url_base64 = urlparse.urljoin(host, url_base64)
        if force_host:
            url_base64 = url_base64.replace('%s://%s' % (urlparse.urlparse(url_base64).scheme, 
                                                         urlparse.urlparse(url_base64).netloc), host.rstrip('/'))
        if url_base64 != url or host not in url_base64:
            host_name = scrapertools.find_single_match(url_base64, patron_host) + '/'
            url_base64 = re.sub(host_name, host, url_base64)
            if not TEST_ON_AIR: logger.info('Url base64 urlparsed: %s' % url_base64)

    return url_base64 + url_sufix


def js2py_conversion(data, url, domain_name='', channel='', size=10000, resp={}, **kwargs):

    if PY3 and isinstance(data, bytes):
        if not b'Javascript is required' in data[:size]:
            return data if not resp else resp
    elif not 'Javascript is required' in data[:size]:
        return data if not resp else resp
    
    import js2py
    from core import httptools
    global DEBUG, TEST_ON_AIR
    TEST_ON_AIR = httptools.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    
    if DEBUG: logger.debug('url: %s; domain_name: %s, channel: %s, size: %s; kwargs: %s, DATA: %s' \
                            % (url, domain_name, channel, size, kwargs, data[:1000]))
    json = kwargs.pop('json', False)
    soup = kwargs.get('soup', False)
    
    # Obtiene nombre del dominio para la cookie
    if not domain_name:
        domain_name = httptools.obtain_domain(url)

    # Obtiene nombre del canal que hace la llamada para marcarlo en su settings.xml
    if not channel and channel is not None:
        channel = inspect.getmodule(inspect.currentframe().f_back.f_back)
        try:
            channel = channel.__name__.split('.')[1]
        except Exception:
            channel = ""
    
    # Obtiene el código JS
    if PY3 and isinstance(data, bytes):
        data = "".join(chr(x) for x in bytes(data))
    patron = r',\s*S="([^"]+)"'
    data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        patron = r",\s*S='([^']+)'"
        data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        logger.error('js2py_conversion: NO data_new')
        return data if not resp else resp
        
    # Descompone el código Base64
    try:
        # Da hasta 10 pasadas o hasta que de error
        for x in range(10):
            data_end = base64.b64decode(data_new).decode('utf-8')
            data_new = data_end
    except Exception:
        js2py_code = data_new
    else:
        logger.error('js2py_conversion: base64 data_new NO Funciona: ' + str(data_new))
        return data if not resp else resp
    if not js2py_code:
        logger.error('js2py_conversion: NO js2py_code BASE64')
        return data if not resp else resp

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
        except Exception:
            pass

    # Se ejecuta de nuevo la descarga de la página, ya con la nueva cookie
    data_new = ''
    response = httptools.downloadpage(url, **kwargs)

    if resp:
        return response
    if response.code not in httptools.SUCCESS_CODES + httptools.REDIRECTION_CODES:
        return data

    if json and response.json:
        data_new = response.json
    elif soup and response.soup:
        data_new = response.soup
    else:
        data_new = re.sub(r"\n|\r|\t", "", response.data)
    if data_new:
        data = data_new
    
    return data


def check_blocked_IP(data, itemlist, url, canonical={}, verbose=True):
    logger.info()
    thumb_separador = get_thumb("next.png")
    channel = canonical.get('channel', '')
    
    host = scrapertools.find_single_match(url, patron_host)
    
    if 'Please wait while we try to verify your browser...' in data:
        logger.error('ERROR 99: La IP ha sido bloqueada por la Web "%s" / DATA: %s' % (host, data[:2500]))
        
        itemlist.append(Item(channel=channel, url=host, 
                        title="[COLOR %s]La IP ha sido bloqueada por la Web.[/COLOR]" \
                        % get_color_from_settings('library_color', default='yellow'), 
                        folder=False, thumbnail=thumb_separador))
        itemlist.append(Item(channel=channel, url=host, 
                        title="[COLOR %s]Fuerce la renovación de la IP en el Router[/COLOR]" \
                        % get_color_from_settings('library_color', default='yellow'), 
                        folder=False, thumbnail=thumb_separador))
        if verbose:
            from platformcode.platformtools import dialog_notification
            dialog_notification("IP bloqueada", "%s: Reiniciar ROUTER" % channel.upper())
        return (True, itemlist)                                                 # Web bloqueada
    
    return (False, itemlist)                                                    # No hay bloqueo


def get_color_from_settings(label, default='white'):
    
    color = config.get_setting(label)
    if not color:
        return default
    
    color = scrapertools.find_single_match(color, r'\](\w+)\[')
    
    return color or default


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
        if item.from_title_tmdb:                                    # Si se salvó el título del contenido devuelto por TMDB, se restaura.
            item.title = item.from_title_tmdb
    else:
        item.add_videolibrary = True                                # Estamos Añadiendo a la Videoteca.  Indicador para control de uso de los Canales
    if item.add_videolibrary:
        if item.season_colapse: del item.season_colapse
        if item.from_num_season_colapse: del item.from_num_season_colapse
        if item.from_title_season_colapse: del item.from_title_season_colapse
        if item.contentType == "movie":
            if item.from_title_tmdb:                                # Si se salvó el título del contenido devuelto por TMDB, se restaura.
                item.title = item.from_title_tmdb
            del item.add_videolibrary
        if item.channel_host:                                       # Borramos ya el indicador para que no se guarde en la Videoteca
            del item.channel_host
        if item.contentTitle:
            item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
            item.title = re.sub(r' -%s-' % item.category, '', item.title)
    if item.contentType == 'movie':
        from_title_tmdb = item.contentTitle
    else:
        from_title_tmdb = item.contentSerieName
    
    # Sólo ejecutamos este código si no se ha hecho antes en el Canal.  Por ejemplo, si se ha llamado desde Episodios o Findvideos,
    # ya no se ejecutará al Añadia a Videoteca, aunque desde el canal se podrá llamar tantas veces como se quiera, 
    # o hasta que encuentre un título no ambiguo
    if item.tmdb_stat:
        if item.from_title_tmdb: del item.from_title_tmdb
        if item.from_title: del item.from_title
        item.from_update = True
        del item.from_update
    else:
        new_item = item.clone()                                                 # Salvamos el Item inicial para restaurarlo si el usuario cancela
        #Borramos los IDs y el año para forzar a TMDB que nos pregunte
        if 'tmdb_id' in item.infoLabels: item.infoLabels['tmdb_id'] = ''
        if 'tvdb_id' in item.infoLabels: item.infoLabels['tvdb_id'] = ''
        if 'imdb_id' in item.infoLabels: item.infoLabels['imdb_id'] = ''
        if 'IMDBNumber' in item.infoLabels: item.infoLabels['IMDBNumber'] = ''
        if item.infoLabels['season']: del item.infoLabels['season']             # Funciona mal con num. de Temporada.  Luego lo restauramos
        item.infoLabels['year'] = '-'
        
        if item.from_title:
            if item.from_title_tmdb:
                if scrapertools.find_single_match(item.from_title_tmdb, r'^(?:\[COLOR \w+\])?(.*?)(?:\[)'):
                    from_title_tmdb = scrapertools.find_single_match(item.from_title_tmdb, r'^(?:\[COLOR \w+\])?(.*?)(?:\[)').strip()
            item.title = item.title.replace(from_title_tmdb, item.from_title)
            item.infoLabels['title'] = item.from_title
            
            if item.from_title_tmdb: del item.from_title_tmdb
        if not item.from_update and item.from_title: del item.from_title

        if item.contentSerieName:                           # Copiamos el título para que sirva de referencia en menú "Completar Información"
            item.infoLabels['originaltitle'] = item.contentSerieName
            item.contentTitle = item.contentSerieName
        else:
            item.infoLabels['originaltitle'] = item.contentTitle
            
        scraper_return = scraper.find_and_set_infoLabels(item)

        if not scraper_return:  #Si el usuario ha cancelado, restituimos los datos a la situación inicial y nos vamos
            # Al no ser procesado, el item.title es "Agregar a la videoteca", hay que sustituirlo por el nombre de la serie o pelicula.
            item = new_item.clone(title=from_title_tmdb)
        else:
            #Si el usuario ha cambiado los datos en "Completar Información" hay que ver el título definitivo en TMDB
            if not item.infoLabels['tmdb_id']:
                if item.contentSerieName:
                    item.contentSerieName = item.contentTitle                   # Se pone título nuevo
                item.infoLabels['noscrap_id'] = ''                              # Se resetea, por si acaso
                item.infoLabels['year'] = '-'                                   # Se resetea, por si acaso
                scraper_return = scraper.find_and_set_infoLabels(item)          # Se intenta de nuevo

                #Parece que el usuario ha cancelado de nuevo.  Restituimos los datos a la situación inicial
                if not scraper_return or not item.infoLabels['tmdb_id']:
                    # Al no ser procesado, el item.title es "Agregar a la videoteca", hay que sustituirlo por el nombre de la serie o pelicula.
                    item = new_item.clone(title=from_title_tmdb)
                else:
                    item.tmdb_stat = True                                       # Marcamos Item como procesado correctamente por TMDB (pasada 2)
            else:
                item.tmdb_stat = True                                           # Marcamos Item como procesado correctamente por TMDB (pasada 1)

            #Si el usuario ha seleccionado una opción distinta o cambiado algo, ajustamos los títulos
            if item.contentType != 'movie' or item.from_update:
                item.channel = new_item.channel                                 # Restuaramos el nombre del canal, por si lo habíamos cambiado
            if item.tmdb_stat == True:
                if new_item.contentSerieName:                                   # Si es serie...
                    filter_languages = config.get_setting("filter_languages", item.channel, default=-1)
                    if isinstance(filter_languages, int) and filter_languages >= 0:
                        item.title_from_channel = new_item.contentSerieName     # Guardo el título incial para Filtertools
                        item.contentSerieName = new_item.contentSerieName       # Guardo el título incial para Filtertools
                    else:
                        if new_item.contentSerieName not in item.title:         # Se ha llamado desde un item "Agregar a la videoteca"
                            item.title = new_item.contentSerieName
                        item.title = item.title.replace(new_item.contentSerieName, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                        item.contentSerieName = item.contentTitle
                    if new_item.contentSeason: item.contentSeason = new_item.contentSeason      #Restauramos Temporada
                    if item.infoLabels['title']: del item.infoLabels['title']   # Borramos título de peli (es serie)
                else:                                                           # Si es película...
                    if new_item.contentTitle not in item.title:                 # Se ha llamado desde un item "Agregar a la videoteca"
                        item.title = new_item.contentTitle
                    item.title = item.title.replace(new_item.contentTitle, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                if new_item.infoLabels['year']:                                 # Actualizamos el Año en el título
                    item.title = item.title.replace(str(new_item.infoLabels['year']), str(item.infoLabels['year']))
                if new_item.infoLabels['rating']:                               # Actualizamos en Rating en el título
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
                    except Exception:
                        logger.error(traceback.format_exc())
                if item.wanted:                                                 # Actualizamos Wanted, si existe
                    item.wanted = item.contentTitle
                if new_item.contentSeason:                                      # Restauramos el núm. de Temporada después de TMDB
                    item.contentSeason = new_item.contentSeason
                    
                if item.from_update:                                            # Si la llamda es desde el menú del canal...
                    item.from_update = True 
                    del item.from_update
                    if item.AHkwargs:
                        try:
                            item = AH_find_videolab_status({}, item, [item], **item.AHkwargs)[0]
                            del item.AHkwargs
                        except Exception:
                            logger.error(traceback.format_exc())
                    xlistitem = refresh_screen(item)                            # Refrescamos la pantallas con el nuevo Item
                    
        #Para evitar el "efecto memoria" de TMDB, se le llama con un título ficticio para que resetee los buffers
        if item.contentSerieName:
            new_item.infoLabels['tmdb_id'] = '289'                              # Una serie no ambigua
        else:
            new_item.infoLabels['tmdb_id'] = '111'                              # Una peli no ambigua
        new_item.infoLabels['year'] = '-'
        if new_item.contentSeason:
            del new_item.infoLabels['season']                                   # Funciona mal con num. de Temporada
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
        from platformcode.platformtools import itemlist_update
        
        xlistitem = xbmcgui.ListItem(path=item.url)                             # Creamos xlistitem por compatibilidad con Kodi 18
        if config.get_platform(True)['num_version'] >= 16.0:
            xlistitem.setArt({"thumb": item.contentThumbnail})                  # Cargamos el thumb
        else:
            xlistitem.setThumbnailImage(item.contentThumbnail)
        xlistitem.setInfo("video", item.infoLabels)                             # Copiamos infoLabel

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xlistitem)           # Preparamos el entorno para evitar error Kod1 18
        time.sleep(1)                                                           # Dejamos tiempo para que se ejecute
    except Exception:
        logger.error(traceback.format_exc())
    
    itemlist_update(item)                                                       # Refrescamos la pantalla con el nuevo Item
    
    return xlistitem


def format_tmdb_id(entity):
    if not entity: return

    def format_entity(item):
        try:
            if item.infoLabels:
                id_tmdb = '' if (not item.infoLabels['imdb_id'] or item.infoLabels['imdb_id'] == 'None') else item.infoLabels['imdb_id']
                if 'tmdb_id' in item.infoLabels:
                    item.infoLabels['tmdb_id'] = '' if (not item.infoLabels['tmdb_id'] \
                                                        or item.infoLabels['tmdb_id'] == 'None') \
                                                        else item.infoLabels['tmdb_id']
                if 'tvdb_id' in item.infoLabels:
                    item.infoLabels['tvdb_id'] = '' if (not item.infoLabels['tvdb_id'] \
                                                        or item.infoLabels['tvdb_id'] == 'None') \
                                                        else item.infoLabels['tvdb_id']
                if 'imdb_id' in item.infoLabels:
                    item.infoLabels['imdb_id'] = '' if (not item.infoLabels['imdb_id'] \
                                                        or item.infoLabels['imdb_id'] == 'None') \
                                                        else item.infoLabels['imdb_id']
                if 'IMDBNumber' in item.infoLabels:
                    item.infoLabels['IMDBNumber'] = '' if (not item.infoLabels['IMDBNumber'] \
                                                           or item.infoLabels['IMDBNumber'] == 'None') \
                                                           else item.infoLabels['IMDBNumber']
        except Exception:
            logger.error(traceback.format_exc())

    if not isinstance(entity, list):                                            # Es Item
        format_entity(entity)
    else:                                                                       # Es Itemlist
        for item_local in entity:
            format_entity(item_local)


def create_videolab_list(update=None):
    logger.info('update: %s' % True if update else None)
    
    patron = r"\[([^\]]+)\]"

    def build_videolab_json(videolab_list, list_movies, list_series, json_path):
        from core import videolibrarytools
        
        res = False
        hit = False

        try:
            for movie in list_movies:
                imdb_id = scrapertools.find_single_match(movie, patron)
                if imdb_id:
                    path_nfo = filetools.join(movies_videolibrary_path, movie, movie+'.nfo')
                    head_nfo, it = videolibrarytools.read_nfo(path_nfo)
                    if it and (it.infoLabels.get('imdb_id') or it.infoLabels.get('tmdb_id')):
                        videolab_list['movie'][imdb_id] = it.infoLabels
                        hit = True
            
            for tvshow in list_series:
                imdb_id = scrapertools.find_single_match(tvshow, patron)
                if imdb_id:
                    path_nfo = filetools.join(series_videolibrary_path, tvshow, 'tvshow.nfo')
                    head_nfo, it = videolibrarytools.read_nfo(path_nfo)
                    if it and (it.infoLabels.get('imdb_id') or it.infoLabels.get('tmdb_id')):
                        videolab_list['tvshow'][imdb_id] = it.infoLabels
                        hit = True

            res = filetools.write(json_path, jsontools.dump(videolab_list))
        except Exception:
            logger.error(traceback.format_exc())
            
        if not res:
            logger.error('ERROR en la ESCRITURA del videolab_list.json: %s' % videolab_list)
            filetools.remove(json_path)
        if not hit:
            logger.info('Videolibrary VACÍA para videolab_list.json', force=True)
        return res and hit

    try:
        video_list_movies = ''
        video_list_series = ''
        json_path = filetools.join(config.get_runtime_path(), 'resources', 'videolab_list.json')

        list_movies = filetools.listdir(movies_videolibrary_path)
        list_series = filetools.listdir(series_videolibrary_path)

        if not filetools.exists(json_path):
            videolab_list = {
                             'movie': {}, 
                             'tvshow': {}
                            }
            res = filetools.write(json_path, jsontools.dump(videolab_list))
            if not res:
                logger.error('ERROR en la CREACIÓN del videolab_list.json')
                return video_list_movies, video_list_series
            
            res = build_videolab_json(videolab_list, list_movies, list_series, json_path)
            if res: logger.info('CREACIÓN del videolab_list.json con ÉXITO', force=True)

        if filetools.exists(json_path) and not update:
            videolab_list = jsontools.load(filetools.read(json_path))
            if videolab_list:
                for movie in list_movies:
                    imdb_id = scrapertools.find_single_match(movie, patron)
                    if imdb_id:
                        video_list_movies += "'%s'|%s|%s|, " % (movie, videolab_list.get('movie', {}).get(imdb_id, {}).get('tmdb_id', ''),
                                                                videolab_list.get('movie', {}).get(imdb_id, {}).get('tvdb_id', ''))
                
                for tvshow in list_series:
                    imdb_id = scrapertools.find_single_match(tvshow, patron)
                    if imdb_id:
                        video_list_series += "'%s'|%s|%s|, " % (tvshow, videolab_list.get('tvshow', {}).get(imdb_id, {}).get('tmdb_id', ''),
                                                                videolab_list.get('tvshow', {}).get(imdb_id, {}).get('tvdb_id', ''))
            if DEBUG: logger.debug('videolab_list.json LEÍDO')

        elif filetools.exists(json_path) and update:
            res = False
            if update.get('mediatype') and update.get('imdb_id') and update.get('tmdb_id'):
                videolab_list = jsontools.load(filetools.read(json_path))
                videolab_list[update['mediatype']][update['imdb_id']] = update
                res = filetools.write(json_path, jsontools.dump(videolab_list))
                if not res:
                    logger.error('ERROR en la ACTUALIZACIÓN del videolab_list.json: %s' % update)
                    return
                config.cache_reset(label='alfa_videolab_series_list')
            if DEBUG: logger.debug('videolab_list.json UPDATE %s: %s' % (res, update))
            return

    except Exception:
        logger.error(traceback.format_exc())

    if DEBUG: logger.debug('video_list_movies (%s): %s' % (len(video_list_movies), video_list_movies))
    if DEBUG: logger.debug('video_list_series (%s): %s' % (len(video_list_series), video_list_series))

    return video_list_movies, video_list_series


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
    
    context = []

    if item.video_path:

        if item.contentType == 'tvshow':
            poner_marca = config.get_localized_string(60021)
            quitar_marca = config.get_localized_string(60020)
        elif item.contentType == 'season':
            poner_marca = config.get_localized_string(60029)
            quitar_marca = config.get_localized_string(60028)
        else:
            poner_marca = config.get_localized_string(60033)
            quitar_marca = config.get_localized_string(60032)

        context.extend(({"title": quitar_marca,
                        "action": "mark_video_as_watched",
                        "channel": "videolibrary",
                        "playcount": 0},
                       {"title": poner_marca,
                        "action": "mark_video_as_watched",
                        "channel": "videolibrary",
                        "playcount": 1}))
    
    if (item.video_path and item.contentType in ['tvshow']) or (item.contentType in ['episode'] and item.nfo):
        context.append(({"title": config.get_localized_string(70269),
                        "action": "update_tvshow",
                        "channel": "videolibrary"}))
    
        if not item.context: item.context = []
        if not isinstance(item.context, list):
            item.context = item.context.replace('["', '').replace('"]', '').replace("['", "").replace("']", "").split("|")
        for cont in context:
            if cont['title'] in str(item.context): continue
            item.context += [cont]

    return item


def monitor_domains_update(options=None):
    logger.info()

    monitor = xbmc.Monitor()
    server_domains_list = jsontools.load(window.getProperty("alfa_cached_domains_update") or '{}')
    window.setProperty("alfa_cached_domains_update", "")
    alfa_channels_list = {}
    alfa_domains_list = {}
    alfa_domains_errors = {}

    try:
        alfa_path = config.get_runtime_path()
        alfa_channels_path = os.path.join(alfa_path, 'channels')
        from core import httptools
        httptools.TEST_ON_AIR = True
        httptools.CACHING_DOMAINS = True
    except Exception as e:
        logger.error(str(e))
        return False

    channels = filetools.listdir(alfa_channels_path)
    for channel_ in channels:
        if not channel_.endswith('.py'): continue
        channel = channel_.replace('.py', '')

        try:
            channel_obj = __import__('channels.%s' % channel, None, None, ["channels.%s" % channel])
            if not channel_obj.canonical: continue
            if not 'host' in channel_obj.canonical or not 'host_alt' in channel_obj.canonical \
                                                   or not 'host_black_list' in channel_obj.canonical: continue
            alfa_channels_list[channel] = channel_obj
        except Exception as e:
            logger.error('%s: %s' % (channel, str(e)))

    logger.error('Verificando Host de %s canales' % len(alfa_channels_list))
    for channel, channel_obj in alfa_channels_list.items():
        if monitor and monitor.abortRequested(): 
            return

        try:
            canonical = channel_obj.canonical.copy()
            canonical_http = channel_obj.canonical.copy()
            canonical_http.update(server_domains_list.get(channel, {}))
            if 'host' in canonical_http: del canonical_http['host']
            if 'forced_proxy_opt' in canonical_http: del canonical_http['forced_proxy_opt']
            if 'forced_proxy' in canonical_http: del canonical_http['forced_proxy']
            if 'forced_proxy_ifnot_assistant' in canonical_http: del canonical_http['forced_proxy_ifnot_assistant']
            opt = {'timeout': 10, 'method': 'GET', 'proxy_retries': 0, 'canonical': canonical_http, 'alfa_s': True, 'retry_alt': False}

            response = httptools.downloadpage(canonical_http['host_alt'][0], **opt)

            if not response.sucess:
                current_host = config.get_setting("current_host", channel, default='')
                if current_host and current_host != canonical_http['host_alt'][0]:
                    response = httptools.downloadpage(current_host, **opt)

                if not response.sucess:
                    if channel in ['hdfull']:
                        url = 'https://dominioshdfull.com/'
                        response = httptools.downloadpage(url, soup=True, **opt)
                        if response.sucess and response.soup.find('div', class_='offset-md-4'):
                            url = response.soup.find('div', class_='offset-md-4').a.get('href', '').rstrip('/')
                            if url and (url + '/') not in canonical_http['host_alt'] and (url + '/') not in canonical_http['host_black_list']:
                                url += '/'
                                response = httptools.downloadpage(url, **opt)
                                if response.sucess:
                                    response.canonical = url

                if not response.sucess:
                    logger.error('### ERROR Verificando Host de canal %s: %s - %s' \
                                 % (channel.upper(), canonical_http['host_alt'][0], str(response.code)))
                    alfa_domains_errors[channel] = {'host_alt': canonical_http['host_alt'], 'error': str(response.code), 
                                                    'host': str(response.host), 'url': str(response.url), 'proxy__': str(response.proxy__), 
                                                    'data': str(response.data)[:5000], 'time': str(datetime.datetime.now())}
                    if server_domains_list.get(channel):
                        alfa_domains_list[channel] = server_domains_list[channel].copy()
                    continue

            if not canonical['host_alt'][0].endswith('/'): response.canonical = response.canonical.rstrip('/')
            if response.canonical and response.canonical != canonical['host_alt'][0] \
                                  and response.canonical not in canonical['host_black_list'] \
                                  and response.canonical not in server_domains_list.get(channel, {}).get('host_black_list', []):

                host_alt = canonical['host_alt'][0]
                if server_domains_list.get(channel):
                    alfa_domains_list[channel] = server_domains_list[channel].copy()
                else:
                    alfa_domains_list[channel] = {'host_alt': canonical['host_alt'][:], 
                                                  'host_black_list': canonical['host_black_list'][:]}

                if response.canonical not in alfa_domains_list[channel]['host_alt'] \
                                      and response.canonical not in alfa_domains_list[channel]['host_black_list']:
                    current_host = config.get_setting("current_host", channel, default='')
                    if current_host and current_host != response.canonical:
                        config.set_setting("current_host", response.canonical, channel)
                    if alfa_domains_list[channel]['host_alt'][0] not in alfa_domains_list[channel]['host_black_list']:
                        alfa_domains_list[channel]['host_black_list'].insert(0, alfa_domains_list[channel]['host_alt'][0])
                    if response.canonical not in alfa_domains_list[channel]['host_alt']:
                        del alfa_domains_list[channel]['host_alt'][0]
                        alfa_domains_list[channel]['host_alt'].insert(0, response.canonical)

                if not alfa_domains_errors.get(channel) and alfa_domains_list[channel] != server_domains_list.get(channel, {}):
                    alfa_domains_errors[channel] = alfa_domains_list[channel]
                    alfa_domains_errors[channel]['time'] = str(datetime.datetime.now())

                logger.error('Cached UPDATED DOMAIN: %s TO %s' % (host_alt, alfa_domains_list[channel]))

        except Exception as e:
            logger.error('%s: %s' % (channel, str(e)))

    window.setProperty("alfa_cached_domains_update", jsontools.dump(alfa_domains_list, **kwargs_json))
    window.setProperty("alfa_cached_domains_errors", jsontools.dump(alfa_domains_errors, **kwargs_json))
    httptools.TEST_ON_AIR = False
    httptools.CACHING_DOMAINS = False
    

def AH_find_videolab_status(self, item, itemlist, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    if DEBUG: logger.debug('video_list_str: %s; function: %s' % (video_list_str, AHkwargs.get('function', '')))

    res = False
    season_episode = ''

    try:
        format_tmdb_id(item)
        format_tmdb_id(itemlist)
        
        if AHkwargs.get('function', '') == 'list_all':
            #tmdb.set_infoLabels_itemlist(itemlist, True)
            for item_local in itemlist:
                item_local.video_path = AH_check_title_in_videolibray(self, item_local)
                if item_local.video_path:
                    item_local.title  = '(V)-%s' % item_local.title
                    item_local.contentTitle = '(V)-%s' % (item_local.contentSerieName or item_local.contentTitle)
                    item_local = context_for_videolibray(item_local)
                    item_local.unify_extended = True

                    if item_local.contentType in ['season', 'episode']:
                        season_episode = '%sx%s.strm' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        if check_marks_in_videolibray(item_local, strm=season_episode):
                            item_local.infoLabels["playcount"] = 1
                    elif item_local.contentType in ['movie']:
                        season_episode = '%s.strm' % item_local.contentTitle.replace('(V)-' , '').lower()
                        if check_marks_in_videolibray(item_local, strm=season_episode):
                            item_local.infoLabels["playcount"] = 1
                    elif item_local.contentType in ['tvshow']:
                        res, season_list = check_marks_in_videolibray(item_local, video_list_init=True)
                        if res:
                            for season, values in list(season_list.items()):
                                if values[0] < values[1]:
                                    break
                            else:
                                item_local.infoLabels["playcount"] = 1

        elif AHkwargs.get('function', '') in ['seasons']:
            if item.video_path:
                res, season_list = check_marks_in_videolibray(item, video_list_init=True)
                if res:
                    for item_local in itemlist:
                        if season_list.get(item_local.contentSeason):
                            if season_list.get(item_local.contentSeason, 0)[0] >= season_list.get(item_local.contentSeason, 0)[1]:
                                item_local.infoLabels["playcount"] = 1

        elif AHkwargs.get('function', '') in ['episodes']:
            if item.video_path:
                res, episode_list = check_marks_in_videolibray(item, video_list_init=True)
                if res:
                    for item_local in itemlist:
                        season_episode = '%sx%s.strm' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        if episode_list.get(season_episode, 0) >= 1:
                            item_local.infoLabels["playcount"] = 1

        elif AHkwargs.get('function', '') in ['get_video_options']:
            if item.video_path:
                if item.contentType in ['movie']:
                    season_episode = '%s.strm' % item.contentTitle.replace('(V)-' , '').lower()
                else:
                    season_episode = '%sx%s.strm' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))
                playcount = 1 if check_marks_in_videolibray(item, strm=season_episode) else 0
                item.infoLabels["playcount"] = playcount
                for item_local in itemlist:
                    if playcount == 0:
                        item_local.infoLabels["playcount"] = playcount
                    elif item_local.action == 'play':
                        item_local.infoLabels["playcount"] = playcount
    except Exception:
        logger.error(traceback.format_exc())

    return itemlist


def AH_check_title_in_videolibray(self, item):
    """
    Comprueba si el item listado está en la videoteca Alfa.  Si lo está devuelve True
    """
    global video_list_str
    res = False
    
    if not item.infoLabels['imdb_id'] and not item.infoLabels['tmdb_id'] and not item.infoLabels['tvdb_id']:
        return res
    
    if not video_list_str:
        if alfa_caching and window.getProperty("alfa_videolab_movies_list") \
                        and window.getProperty("alfa_videolab_series_list"):
            video_list_str = window.getProperty("alfa_videolab_movies_list")
            video_list_str += window.getProperty("alfa_videolab_series_list")
            logger.info(True)
        else:
            video_list_movies, video_list_series = create_videolab_list()
            video_list_str = video_list_movies + video_list_series
            logger.info(False)
            
            if alfa_caching:
                window.setProperty("alfa_videolab_movies_list", video_list_movies)
                window.setProperty("alfa_videolab_series_list", video_list_series)

    if (item.infoLabels['imdb_id'] and '[%s]' % item.infoLabels['imdb_id'] in video_list_str) \
        or (item.infoLabels['tmdb_id'] and '|%s|' % item.infoLabels['tmdb_id'] in video_list_str) \
        or (item.infoLabels['tvdb_id'] and '|%s|' % item.infoLabels['tvdb_id'] in video_list_str):

        for video in video_list_str.split(','):
            if (item.infoLabels['imdb_id'] and '[%s]' % item.infoLabels['imdb_id'] in video) \
                or (item.infoLabels['tmdb_id'] and '|%s|' % item.infoLabels['tmdb_id'] in video) \
                or (item.infoLabels['tvdb_id'] and '|%s|' % item.infoLabels['tvdb_id'] in video):
                res = video.split('|')[0].strip().strip("'").strip()
                if res: break

    if DEBUG: logger.debug('video "%s %s" %s en videolab: "%s"' % (item.infoLabels['title'], 
                            item.infoLabels['imdb_id'] or item.infoLabels['tmdb_id'] or item.infoLabels['tvdb_id'], 
                            'ENCONTRADO' if res else 'NO Encontrado', video_list_str))

    return res


def AH_post_tmdb_listado(self, item, itemlist, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False

    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Listado y Listado_Búsqueda.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.
    
    También restaura varios datos salvados desde el título antes de pasarlo por TMDB, ya que mantenerlos no habría encontrado el título (title_subs)
    
    """
    #logger.debug(item)

    # Ajustamos el nombre de la categoría
    if item.category_new == "newest":                                           # Viene de Novedades.  Lo marcamos para Unify
        item.from_channel = 'news'
        del item.category_new

    format_tmdb_id(item)
    format_tmdb_id(itemlist)

    for item_local in itemlist:                                                 # Recorremos el Itemlist generado por el canal
        #item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
        title = item_local.title
        season = 0
        episode = 0
        idioma = idioma_busqueda
        if 'VO' in str(item_local.language):
            idioma = idioma_busqueda_VO
        #logger.debug(item_local)

        if item_local.contentSeason_save:                                       # Restauramos el num. de Temporada
            item_local.contentSeason = item_local.contentSeason_save

        #Restauramos la info adicional guarda en la lista title_subs, y la borramos de Item
        title_add = ''
        if item_local.title_subs:
            for title_subs in item_local.title_subs:
                if not title_subs: continue
                if scrapertools.find_single_match(title_subs, r'Episodio\s*(\d+)x(\d+)'):
                    title_subs += ' (MAX_EPISODIOS)'
                title_add = '%s -%s-' % (title_add, title_subs)                 # Se agregan el resto de etiquetas salvadas
        if len(title_add) > 1: item_local.unify_extended = True
        if 'title_subs' in item_local: del item_local.title_subs  

        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        if item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        if item_local.from_title:
            if item_local.contentType == 'movie':
                item_local.contentTitle = item_local.from_title
                item_local.title = item_local.from_title
            elif item_local.contentType == 'season':
                item_local.title = item_local.from_title
            else:
                item_local.contentSerieName = item_local.from_title
            
            item_local.title = re.sub(r'(?i)online|descarga|downloads|trailer|videoteca|gb|autoplay', '', item_local.title).strip()
            title = item_local.title

        #Limpiamos calidad de títulos originales que se hayan podido colar
        if item_local.infoLabels['originaltitle'].lower() in item_local.quality.lower():
            item_local.quality = re.sub(item_local.infoLabels['originaltitle'], '', item_local.quality)

        # Preparamos el título para series, con los núm. de temporadas, si las hay
        if item_local.contentType in ['season', 'tvshow', 'episode']:
            item_local.contentSerieName = filetools.validate_path(item_local.contentSerieName.replace('/', '-').replace('  ', ' '))
            item_local.contentTitle = filetools.validate_path(item_local.contentTitle.replace('/', '-').replace('  ', ' '))
            item_local.title = filetools.validate_path(item_local.title.replace('/', '-').replace('  ', ' '))
            if item_local.from_title: item_local.from_title = filetools.validate_path(item_local.from_title.replace('/', '-').replace('  ', ' '))

            # Pasada por TMDB a Serie, para datos adicionales, y mejorar la experiencia en Novedades
            if scrapertools.find_single_match(title_add, r'Episodio\s*(\d+)x(\d+)') or ' (MAX_EPISODIOS)' in title_add:
                # Salva los datos de la Serie y lo transforma temporalmente en Season o Episode
                contentPlot = item_local.contentPlot
                contentType = item_local.contentType
                if scrapertools.find_single_match(title_add, r'Episodio\s*(\d+)x(\d+)'):
                    season, episode = scrapertools.find_single_match(title_add, r'Episodio\s*(\d+)x(\d+)')
                else:
                    season = item_local.infoLabels['season']
                    episode = item_local.infoLabels['episode']
                episode_max = int(episode)
                try:
                    item_local.infoLabels['season'] = int(season)
                    item_local.infoLabels['episode'] = int(episode)
                except Exception:
                    season = 0
                    episode = 0

                if not season:
                    title_add = re.sub(r'Episodio\s*(\d+)x(\d+)', '', title_add)
                elif '-al-' not in title_add and episode:
                    item_local.infoLabels['episode'] = episode
                    item_local.contentType = "episode"
                else:
                    item_local.contentType = "season"
                    episode_max = int(scrapertools.find_single_match(title_add, r'Episodio\s*\d+x\d+-al-(\d+)'))

                if (not item_local.infoLabels['temporada_nombre'] or not item_local.infoLabels['number_of_seasons']) \
                                                                  and item_local.infoLabels['tmdb_id'] \
                                                                  and item_local.infoLabels['season']:
                    tmdb.set_infoLabels_item(item_local, seekTmdb=True, idioma_busqueda=idioma)     # TMDB de la serie
                    format_tmdb_id(item_local)
 
                # Restaura los datos de infoLabels a su estado original, menos plot y año
                item_local.infoLabels['year'] = scrapertools.find_single_match(item_local.infoLabels['aired'], r'\d{4}')

                if item_local.infoLabels.get('temporada_num_episodios', 0) >= episode_max:
                    tot_epis = ''
                    if item_local.infoLabels.get('temporada_num_episodios', 0):
                        tot_epis = ' (de %s' % str(item_local.infoLabels['temporada_num_episodios'])
                    if (item_local.infoLabels.get('number_of_seasons', 0) > 1 \
                            and item_local.infoLabels.get('number_of_episodes', 0) > 0) \
                            or (item_local.infoLabels.get('number_of_seasons', 0) \
                            and not item_local.infoLabels.get('temporada_num_episodios', 0)):
                        tot_epis += ' (' if not tot_epis else ', '
                        tot_epis += 'de %sx%s' % (str(item_local.infoLabels['number_of_seasons']), \
                                                  str(item_local.infoLabels['number_of_episodes']))
                    if tot_epis: tot_epis += ')'
                    title_add = title_add.replace(' (MAX_EPISODIOS)', tot_epis)
                else:
                    title_add = title_add.replace(' (MAX_EPISODIOS)', '')

                if contentPlot[10:] != item_local.contentPlot[10:]:
                    item_local.contentPlot += '\n\n%s' % contentPlot

                item_local.contentType = contentType
                if item_local.contentType in ['tvshow'] and item_local.infoLabels['season']: del item_local.infoLabels['season']
                if item_local.contentType in ['season', 'tvshow'] and item_local.contentEpisodeNumber: del item_local.infoLabels['episode']

            # Exploramos los diferentes formatos
            if item_local.contentType == "episode":
                # Si no está el título del episodio, pero sí está en "title", lo rescatamos
                if not item_local.infoLabels['episodio_titulo'] and item_local.infoLabels['title'].lower() \
                                                                != item_local.infoLabels['tvshowtitle'].lower():
                    item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['title']

                if "Temporada" in title:                                        # Compatibilizamos "Temporada" con Unify
                    title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
                if " al " in title:                                             # Si son episodios múltiples, ponemos nombre de serie
                    if " al 99" in title.lower():                               # Temporada completa.  Buscamos num total de episodios
                        title = title.replace("99", str(item_local.infoLabels['temporada_num_episodios']))
                    title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s - %s %s %s' % (scrapertools.find_single_match(title, r'(al \d+)'), 
                                                               item_local.contentSerieName, unify.set_color(item_local.infoLabels['year'], 'year'), 
                                                               unify.format_rating(item_local.infoLabels['rating']))

                elif item_local.infoLabels['episodio_titulo']:
                    title = '%s %s, %s' % (title, item_local.infoLabels['episodio_titulo'], item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s, %s %s %s' % (item_local.infoLabels['episodio_titulo'], 
                                                               item_local.contentSerieName,  unify.set_color(item_local.infoLabels['year'], 'year'), 
                                                               unify.format_rating(item_local.infoLabels['rating']))

                else:                                                           # Si no hay título de episodio, ponermos el nombre de la serie
                    if item_local.contentSerieName not in title:
                        title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s %s %s' % (item_local.contentSerieName, 
                                                                                 unify.set_color(item_local.infoLabels['year'], 'year'), 
                                                                                 unify.format_rating(item_local.infoLabels['rating']))

                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    if "Episodio" in title_add:
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, 
                                                                                    r'Episodio (\d+)x(\d+)')
                        title = '%s %s %s' % (title, unify.set_color(item_local.infoLabels['year'], 'year'), 
                                                         unify.format_rating(item_local.infoLabels['rating']))

            elif item_local.contentType == "season":
                if not item_local.contentSeason:
                    item_local.contentSeason = int(scrapertools.find_single_match(item_local.url, r'-(\d+)x') or \
                                                   scrapertools.find_single_match(item_local.url, r'-temporadas?-(\d+)') or 1)
                if item_local.contentSeason:
                    title = '%s -Temporada %s' % (title, str(item_local.contentSeason))
                else:
                    title = '%s -Temporada !!!' % (title)
                item_local.unify_extended = True
                item_local.contentType = 'tvshow'

            elif item_local.contentSeason:
                item_local.unify_extended = True

        # Se añaden etiquetas adicionales, si las hay
        title += title_add.replace(' (MAX_EPISODIOS)', '').replace('BTDIGG_INFO', '(de %sx%s)' \
                                                           % (str(item_local.infoLabels['number_of_seasons']), \
                                                              str(item_local.infoLabels['number_of_episodes'])))
        if title_add and item_local.contentType == 'movie':
            item_local.contentTitle += title_add.replace(' (MAX_EPISODIOS)', '')

        # Viene de Novedades.  Lo preparamos para Unify
        if item_local.from_channel == "news":

            if item_local.contentType in ['season', 'tvshow']:
                title = '%s %s' % (item_local.contentSerieName, title_add)
            elif "Episodio " in title:
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    try:
                        item_local.contentSeason, item_local.contentEpisodeNumber = \
                                scrapertools.find_single_match(title_add, r'Episodio (\d+)x(\d+)')
                    except Exception:
                        item_local.contentSeason = item_local.contentEpisodeNumber = 1
            item_local.unify_extended = True

        # Ponemos el estado de las Series
        if item_local.infoLabels['status'] and (item_local.infoLabels['status'].lower() == "ended" \
                        or item_local.infoLabels['status'].lower() == "canceled"):
            title += ' [TERM]'
            item_local.unify_extended = True

        item_local.title = title

        #logger.debug(item_local)

    if 'from_channel' in item.from_channel:
        del item.from_channel

    return item, itemlist


def AH_find_seasons(self, item, matches, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False

    # Si hay varias temporadas, buscamos todas las ocurrencias y las filtrados por TMDB, calidad e idioma
    findS = AHkwargs.get('finds', {})
    title_search = findS.get('controls', {}).get('title_search', '')
    seasons_search = findS.get('controls', {}).get('seasons_search', '')
    modo_ultima_temp = AHkwargs.get('modo_ultima_temp', config.get_setting('seleccionar_ult_temporadda_activa', item.channel, default=True))
    language_def = AHkwargs.get('language', ['CAST'])
    function = AHkwargs.get('function', 'find_seasons')
    kwargs = {'function': function, 'kwargs': AHkwargs.get('kwargs', {})}
    if not item.language: item.language = language_def
    if not item.library_playcounts: modo_ultima_temp = False
    item.quality = item.quality.replace(btdigg_label, '')
    patron_seasons = findS.get('seasons_search_num_rgx', [[r'(?i)-(\d+)-(?:Temporada|Miniserie)', None], 
                                                          [r'(?i)(?:Temporada|Miniserie)-(\d+)(?:\W|$)', None]])
    patron_qualities = findS.get('seasons_search_qty_rgx', [[r'(?i)(?:Temporada|Miniserie)(?:-(.*?)(?:\.|\/|-$|$))', None]])
    list_temps = []
    list_temp_int = []
    list_temp = []
    seasons = []
    itemlist = []
    title_list = []
    seasons_found = 0
    for match in matches:
        list_temps.append(match['url'])
    if not list_temps:
        list_temps.append(item.url)
    
    alias = {}
    alias_in = alias_out = ''

    format_tmdb_id(item)

    try:
        # Vemos la última temporada de TMDB y del .nfo
        if item.ow_force == "1":                                                    # Si hay una migración de canal o url, se actualiza todo 
            modo_ultima_temp = False
        max_temp = int(item.infoLabels['number_of_seasons'] or 0)
        max_nfo = 0
        y = []
        if modo_ultima_temp and item.library_playcounts:                            # Averiguar cuantas temporadas hay en Videoteca
            patron = r'season (\d+)'
            matches_x = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
            for x in matches_x:
                y += [int(x)]
            max_nfo = max(y)
        if max_nfo > 0 and max_nfo != max_temp:
            max_temp = max_nfo
        if max_temp == 0 or max_nfo:
            modo_ultima_temp = min_temp = False

        item.infoLabels['number_of_seasons'] = int(scrapertools.find_single_match(item.infoLabels.get('last_series_episode_to_air', '%sx1' \
                                                                                  % item.infoLabels.get('number_of_seasons', 1)), r'(\d+)x\d+'))
        if item.infoLabels['number_of_seasons'] == 1 and not item.btdig_in_use:
            itemlist.append(item)
        else:
            # Creamos un nuevo Item para la búsqueda de las temporadas
            item_search = item.clone()
            item_search.extra = function
            item_search.c_type = item_search.c_type or 'series'
            
            if '#' in item_search.season_search:
                alias = search_btdigg_free_format_parse({}, item_search.clone(), titles_search=BTDIGG_SEARCH)[0].get('aliases', {})
                if alias:
                    alias_in = list(alias.keys())[0].replace('_', ' ').lower()
                    alias_out = list(alias.values())[0].replace('_', ' ').lower()

            title = title_search or alias_out \
                                 or scrapertools.find_single_match(item_search.season_search or item_search.contentSerieName \
                                                                   or item_search.contentTitle, r'(^.*?)\s*(?:$|\(|\[|\|)').lower()  # Limpiamos
            title = scrapertools.quote(title, plus=True)
            title_list += [title]
            title_org = scrapertools.find_single_match(item_search.infoLabels['originaltitle'], r'(^.*?)\s*(?:$|\(|\[|\|)').lower()  # Limpiamos
            title_org = scrapertools.quote(title_org, plus=True)
            if title_org != title: title_list += [title_org]

            channel = __import__('channels.%s' % item_search.channel, None, None, ["channels.%s" % item_search.channel])
            item_search.url = channel.host

            if DEBUG: logger.debug('list_temps INICAL: %s; title_list: %s' % (list_temps, title_list))
            for title_search in title_list:
                item_search.title = title_search
                item_search.infoLabels = {}

                # Llamamos a 'Listado' para que procese la búsqueda
                itemlist = getattr(channel, "search")(item_search, title_search.lower(), **kwargs)

                if not itemlist:
                    continue

                format_tmdb_id(itemlist)

                # Analizamos si las temporadas encontradas corresponden a las serie
                for item_found in itemlist:                                     # Procesamos el Itemlist de respuesta
                    item_found.quality = item_found.quality.replace(btdigg_label, '')
                    if DEBUG: logger.debug('===============================================')
                    if DEBUG: logger.debug('tmdb_id: item_found: %s / item: %s' % (item_found.infoLabels['tmdb_id'], item.infoLabels['tmdb_id']))
                    if DEBUG: logger.debug('language: item_found: %s / item: %s' % (item_found.language, item.language))
                    if DEBUG: logger.debug('quality: item_found: %s / item: %s' % (item_found.quality, item.quality))
                    if DEBUG: logger.debug('url: item_found: %s / item: %s' % (item_found.url, item.url))
                    if DEBUG: logger.debug('title: item_found: %s / item: %s' % (item_found.contentSerieName or item_found.title, 
                                                                                 item.contentSerieName or item.title))

                    if item_found.url in str(list_temps):                       # Si ya está la url, pasamos a la siguiente
                        continue
                    if not item_found.infoLabels['tmdb_id']:                    # tiene TMDB?
                        continue
                    if item_found.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']:  # Es el mismo TMDB?
                        continue
                    if item.language and item_found.language:                   # Es el mismo Idioma?
                        if item.language != item_found.language:
                            continue
                    if item_found.quality and item.quality:                     # Es la misma Calidad?, si la hay...
                        if item_found.quality.replace(btdigg_label, '') not in item.quality.replace(' AC3 5.1', '')\
                                           .replace('HDTV 720p', 'HDTV-720p').replace(btdigg_label, '').split(', '):
                            continue
                    elif patron_qualities:
                        for patron_quality in patron_qualities:
                            if scrapertools.find_single_match(item.url, patron_quality) == \
                                    scrapertools.find_single_match(item_found.url, patron_quality):     # Coincide la calidad? (alternativo)
                                break
                        else:
                            continue
                    list_temps.append(item_found.url)                           # Si hay ocurrencia, guardamos la url
                    seasons_found += 1
                    if DEBUG: logger.debug('item_found: ### TRUE ###')

                if seasons_found > 0: 
                    break
        
        if DEBUG: logger.debug('list_temps: %s' % list_temps)
        # Organizamos las temporadas válidas encontradas

        for x, url in enumerate(list_temps):
            elem_json = {}
            for y, (patron_season, none) in enumerate(patron_seasons):
                if scrapertools.find_single_match(url, patron_season):          # Está la Temporada en la url en este formato?
                    season = scrapertools.find_single_match(url, patron_season)
                    try:                                                        # Miramos si la Temporada está procesada
                        if not modo_ultima_temp or (modo_ultima_temp and max_temp >= max_nfo \
                                                    and int(season) >= max_nfo):
                            elem_json['url'] = url                              # No está procesada, la añadimos
                            elem_json['season'] = int(season)
                            elem_json['priority'] = y
                        else:
                            break
                    except Exception:
                        logger.error('ERROR Temporada %s sin num: %s' % (x + 1, url))
                        elem_json['url'] = url                                  # ERROR, la añadimos
                        elem_json['season'] = (x + 1) if list_temp_int and btdigg_url not in list_temp_int[0]['url'] else 1
                        elem_json['priority'] = y
                        logger.error(traceback.format_exc())

                    list_temp_int.append(elem_json.copy())
                    break
            else:
                if not seasons_search and not btdigg_url in url:
                    elem_json['url'] = url                                      # No está procesada, la añadimos
                    elem_json['season'] = item.contentSeason or item.infoLabels['number_of_seasons'] or 1
                    elem_json['priority'] = 0
                    list_temp_int.append(elem_json.copy())
                else:
                    logger.error('Temporada %s sin patrón: %s' % (x + 1, url))
                    elem_json['url'] = url                                      # No está procesada, la añadimos
                    elem_json['season'] = (x + 1) if list_temp_int and btdigg_url not in list_temp_int[0]['url'] else 1
                    elem_json['priority'] = 98
                    for elem_alt in list_temp_int:
                        if elem_alt['season'] == elem_json['season']: break
                    else:
                        list_temp_int.append(elem_json.copy())
        
        list_temp_int = sorted(list_temp_int, key=lambda el: (int(el['priority']), int(el['season'])))
        for x, elem_json in enumerate(list_temp_int):
            if elem_json['season'] in seasons:
                continue
            seasons += [elem_json['season']]
            list_temp.append(list_temp_int[x])
        list_temp = sorted(list_temp, key=lambda el: int(el['season']))
        
        url_changed = False
        if list_temp:
            if item.url != list_temp[-1]['url'] or (item.library_urls and item.library_urls.get(item.channel) \
                                                and item.library_urls[item.channel] != list_temp[-1]['url']):
                url_changed = True
            item.url = list_temp[-1]['url']                                     # Guardamos la url de la última Temporada en .NFO
            if item.library_urls and item.library_urls.get(item.channel):
                item.library_urls[item.channel] = item.url                      # Guardamos la url en el .nfo
        
        # Si la ha cambiado la última temporada, actualizamos el .nfo para la Videoteca
        if url_changed and (item.nfo or item.path or item.video_path):
            from core import videolibrarytools
            path = item.nfo
            if not path:
                path = filetools.join(series_videolibrary_path, item.path or item.video_path, 'tvshow.nfo')
            head_nfo, it = videolibrarytools.read_nfo(path)
            if it:
                it.library_urls[item.channel] = item.url
                res = videolibrarytools.write_nfo(path, head_nfo=head_nfo, item=it)     # Refresca el .nfo para recoger actualizaciones

    except Exception:
        logger.error('ERROR al procesar las temporadas: %s' % list_temps)
        if not list_temp:
            elem_json = {}
            elem_json['url'] = item.url                                         # No está procesada, la añadimos
            elem_json['season'] = 1
            elem_json['priority'] = 99
            list_temp.append(elem_json)
        logger.error(traceback.format_exc())

    if DEBUG: logger.debug('MATCHES (%s/%s): %s' % (len(list_temp), len(str(list_temp)), str(list_temp)))

    return list_temp


def AH_post_tmdb_seasons(self, item, itemlist, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    
    """

    Pasada para gestión del menú de Temporadas de una Serie
    
    La clave de activación de este método es la variable item.season_colapse que pone el canal en el Item de Listado.
    Esta variable tendrá que desaparecer cuando se añada a la Videoteca para que se analicen los episodios de la forma tradicional

    """
    #logger.debug(item)
    #logger.debug(config.get_setting("videolibrary_merge_seasons"))
    
    # Si no se quiere mostrar por temporadas, nos vamos...
    if item.season_colapse == False or config.get_setting("videolibrary_merge_seasons") == 2 or len(itemlist) <= 1:
        item.season_colapse = False                                             # Quitamos el indicador de listado por Temporadas
        return item, itemlist
    
    # Si no se quiere mostrar el título de TODAS las temporadas, nos vamos...
    if not config.get_setting("videolibrary_show_all_seasons_entry"):
        return item, itemlist
    
    format_tmdb_id(item)
    format_tmdb_id(itemlist)
    
    matches = AHkwargs.get('matches', [])
    
    # Se muestra una entrada para listar todas los episodios
    if itemlist and config.get_setting("videolibrary_show_all_seasons_entry"):
        item_season = item.clone()
                                 
        item_season.season_colapse = False                                      # Quitamos el indicador de listado por Temporadas
        if matches:
            item_season.matches = matches
        item_season.title = '** Todas las Temporadas'                           # Agregamos título de TODAS las Temporadas (modo tradicional)
        if item_season.infoLabels['number_of_episodes']:                        # Ponemos el núm de episodios de la Serie
            item_season.title += ' (%sx%s epis)' % (str(item_season.infoLabels['number_of_seasons']), \
                                                    str(item_season.infoLabels['number_of_episodes']))
    
        itemlist.insert(0, item_season.clone(from_title_season_colapse=item.title, unify_extended=True))

    return item, itemlist
    

def AH_post_tmdb_episodios(self, item, itemlist, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False

    itemlist_fo = []
        
    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Episodios.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.

    Lleva un control del num. de episodios por temporada, tratando de arreglar los errores de la Web y de TMDB
    
    """
    #logger.debug(item)
    
    format_tmdb_id(item)
    format_tmdb_id(itemlist)
    
    matches = AHkwargs.get('matches', [])

    # Recorremos el Itemlist generado por el canal    
    for item_local in itemlist:
        #logger.debug(item_local.title)

        # Preparamos el título para que sea compatible con Añadir Serie a Videoteca
        if "Temporada" in item_local.title:                                     # Compatibilizamos "Temporada" con Unify
            item_local.title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))

        if " al " in item_local.title:                                          # Si son episodios múltiples, ponemos nombre de serie
            if " al 99" in item_local.title.lower():                            # Temporada completa.  Buscamos num de episodios de la temporada
                item_local.title = item_local.title.replace("99", 
                                   str(item_local.infoLabels['temporada_num_episodios']) or str(item_local.infoLabels['number_of_episodes']))
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s - %s' \
                                  % (scrapertools.find_single_match(item_local.title, r'(al \d+)'), 
                                  item_local.contentSerieName)

    return item, itemlist


def AH_post_tmdb_findvideos(self, item, itemlist, **AHkwargs):
    logger.info()
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    
    """
        
    Llamada para crear un pseudo título con todos los datos relevantes del vídeo.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título. Lleva un control del num. de episodios por temporada
        
    En Itemlist devuelve un Item con el pseudotítulo.  Ahí el canal irá agregando el resto.
    
    """
    #logger.debug(item)
    
    headers = AHkwargs.get('headers', {})
 
    # Saber si estamos en una ventana emergente lanzada desde una viñeta del menú principal,
    # con la función "play_from_library"
    item.unify = False
    Window_IsMedia = False
    try:
        if xbmc.getCondVisibility('Window.IsMedia') == 1:
            Window_IsMedia = True
            item.unify = config.get_setting("unify")
    except Exception:
        item.unify = config.get_setting("unify")
        logger.error(traceback.format_exc())
    
    if item.contentSeason_save:                                                 # Restauramos el num. de Temporada
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save
    
    if item.library_filter_show:
        del item.library_filter_show
    
    if item.unify_extended:
        del item.unify_extended

    if item.contentType != 'movie' and item.nfo: 
        item = context_for_videolibray(item)
        if item.nfo and not item.video_path:
            item.video_path = filetools.basename(filetools.dirname(item.nfo))

    # Si no existe "clean_plot" se crea a partir de "plot"
    if not item.clean_plot and item.infoLabels['plot']:
        item.clean_plot = item.infoLabels['plot']

    # Guardamos la url del episodio/película para favorecer la recuperación en caso de errores
    item.url_save_rec = ([item.url, headers])
    
    if (not config.get_setting("pseudo_titulos", item.channel, default=False) and item.channel != 'url') or item.downloadFilename:
        return (item, itemlist)
    
    if item.armagedon:                                                          # Es una situación catastrófica?
        itemlist.append(item.clone(action='', title=item.category + ': [COLOR hotpink]Usando enlaces de emergencia[/COLOR]', 
                                   quality='', server='', folder=False))
    
    # Quitamos el la categoría o nombre del título, si lo tiene
    if item.contentTitle:
        item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
        item.title = re.sub(r' -%s-' % item.category, '', item.title)
    
    # Limpiamos de año y rating de episodios
    if item.infoLabels['episodio_titulo']:
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\[.*?\]', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\(.*?\)', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = item.infoLabels['episodio_titulo'].replace(item.contentSerieName, '')
    if item.infoLabels['aired'] and item.contentType == "episode":
        item.infoLabels['year'] = scrapertools.find_single_match(str(item.infoLabels['aired']), r'\/(\d{4})')

    if item.action == 'show_result':                                            # Viene de una búsqueda global
        channel = item.channel.capitalize()
        if item.from_channel:
            channel = item.from_channel.capitalize()
        item.quality = '[COLOR yellow][%s][/COLOR] %s' % (channel, item.quality)

    # Si tiene contraseña, la pintamos
    if 'RAR-' in item.torrent_info or 'RAR-' in str(item.matches_cached)  or 'RAR-' in str(item.matches):
        item.password = find_rar_password(item)
    if item.password:
        itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/COLOR]'" 
                                                     + str(item.password) + "'", quality='', server='', folder=False))
    
    #Si es ventana damos la opción de descarga, ya que no hay menú contextual
    if not Window_IsMedia:
        if item.contentType == 'movie': contentType = 'Película'
        if item.contentType == 'episode': contentType = 'Episodio'
        itemlist.append(item.clone(title="-Descargar %s-" % contentType, channel="downloads", server='torrent', 
                                   folder=False, quality='', action="save_download", from_channel=item.channel, from_action='play'))
        if item.contentType == 'episode' and not item.channel_recovery:
            itemlist.append(item.clone(title="-Descargar Epis NO Vistos-", channel="downloads", contentType="tvshow", 
                                       action="save_download", from_channel=item.channel, from_action='episodios', 
                                       folder=False, quality='', sub_action="unseen"))
            item.quality = scrapertools.find_single_match(item.quality, r'(.*?)\s\[')
            itemlist.append(item.clone(title="-Descargar Temporada-", channel="downloads", contentType="season", 
                                       action="save_download", from_channel=item.channel, from_action='episodios', 
                                       folder=False, quality='', sub_action="season"))
            itemlist.append(item.clone(title="-Descargar Serie-", channel="downloads", contentType="tvshow", 
                                       action="save_download", from_channel=item.channel, from_action='episodios', 
                                       folder=False, quality='', sub_action="tvshow"))

    #logger.debug(item)
    
    return (item, itemlist)


def post_btdigg(itemlist, channel, channel_obj=None, **AHkwargs):

    try:
        if not channel_obj:
            channel_obj = __import__('channels.%s' % channel, None, None, ["channels.%s" % channel])

        if not config.get_setting('find_alt_link_option', channel, default=False):
            return itemlist
        if not channel_obj.finds.get('controls', {}).get('btdigg', False):
            return itemlist

        for it in itemlist:
            if it.action and it.action not in ['configuracion', 'autoplay_config']:
                assistant_OK = filetools.exists(filetools.join(config.get_data_path(), 'alfa-mobile-assistant.version')) \
                               or filetools.exists(filetools.join(config.get_data_path(), 'alfa-desktop-assistant.version'))
                assistant_req = 'Puede requerir [COLOR yellow]la instalación de [B]la app Assistant[/B][/COLOR]\n\n' if not assistant_OK else ''
                it.contentPlot = config.BTDIGG_POST + assistant_req + it.contentPlot
    except Exception:
        logger.error(traceback.format_exc())
    
    return itemlist


def search_btdigg_free_format_parse(self, item, titles_search=BTDIGG_SEARCH, contentType='list', **AHkwargs):

    if BTDIGG_URL_SEARCH in item.url and not item.btdigg and item.season_search: item.btdigg = item.season_search
    btdigg = item.btdigg or item.season_search or item.contentSerieName or item.contentTitle
    url = scrapertools.find_single_match(btdigg, r'(.*?)\s*(?:\[|\||$)')
    filterTitle = []
    filterQuality = []
    filterLanguage = []
    params_list = []
    search_order = 2
    type_ = ''
    aliases = {}
    titles_search_ = copy.deepcopy(titles_search)

    if not btdigg:
        logger.info('%s: %s - %s' % (btdigg, contentType, aliases))
        return titles_search

    if '[' in btdigg:
        params = scrapertools.find_multiple_matches(btdigg, r'\s*\[(.*?)[\]|$]')
        for x, param in enumerate(params):
            for title_search in titles_search_:
                if x == 0: 
                    title_search['title_tail'] = param.split(' ') if param.split(' ') != [''] else []
                    for p in ['movie', 'tvshow', 'season', 'episode']:
                        if p in title_search['title_tail']: 
                            title_search['title_tail'].remove(p)
                            type_ = p
                    if not title_search.get('aliases'): title_search['aliases'] = {}
                    for y, p in enumerate(title_search['title_tail'][:]):
                        title_search['title_tail'][y] = title_search['title_tail'][y].replace('+', ' ').replace('_', ' ')
                        if '#' in p:
                            alias = p.split('#')
                            title_search['title_tail'][y] = alias[0].replace('+', ' ').replace('_', ' ')
                            title_search['title_tail'] += [alias[1].replace('+', ' ').replace('_', ' ')]
                            title_search['aliases'][alias[0].lower().replace('+', ' ').replace('_', ' ').lower()] = \
                                                    alias[1].replace('+', ' ').replace('_', ' ').lower()
                            aliases[contentType] = title_search['aliases']
                if x == 1: title_search['quality_alt'] = str(param.strip())
                if x == 2: title_search['language_alt'] = param.split(' ') if param.split(' ') != [''] else []

    if '|' in btdigg:
        search_order = int(scrapertools.find_single_match(btdigg, r'\s*\|(\d)') or search_order)
        limit_search = int(scrapertools.find_single_match(btdigg, r'\s*\|\d*\:(\d+)') or 0)
        for title_search in titles_search_:
            title_search['search_order'] = search_order
            if limit_search > 0 and limit_search <= 10: title_search['limit_search'] = limit_search

    for title_search in titles_search_:
        if item.btdigg or BTDIGG_URL_SEARCH in item.url:
            title_search['urls'] = [url]
            if contentType == 'list' and url and not title_search.get('title_tail', []):
                if not title_search.get('title_tail'): title_search['title_tail'] = []
                if type_:
                    item.btdigg = item.btdigg.replace(type_, '%s %s' % (type_, url.split(' ')[0]))
                else:
                    item.btdigg += ' [%s]' % url.split(' ')[0]
                item.season_search = item.btdigg
                title_search['title_tail'] += [url.split(' ')[0]]

            if contentType == 'episode': title_search['limit_search'] *= 2
            if contentType not in ['list', 'search']: title_search['contentType'] = contentType
        #if contentType not in ['movie', 'tvshow', 'season', 'episode']: title_search['contentType'] = contentType

    logger.info('%s: %s - %s' % (btdigg, contentType, aliases))
    return titles_search_


def AH_find_btdigg_matches(item, matches, **AHkwargs):
    logger.info()

    itemlist = []
    matches_out = []
    matches_index = {}
    matches_post = AHkwargs.get('matches_post_get_video_options', None)

    try:
        for match in matches:
            if item.contentType == 'movie':
                match_key = '%s [%s]' % (item.contentTitle, item.contentChannel or item.channel)
            else:
                match_key = '%sx%s [%s].json' % (match.get('season', 0), str(match.get('episode', 0)).zfill(2), item.channel)
            matches_index[match_key] = match.copy()
            if item.action == 'findvideos':
                match_key = match.get('url', '').replace(' ', '%20')
            matches_index[match_key] = match.copy()

        if not item.matches or item.nfo:
            if not item.video_path and not item.nfo: 
                return matches
            
            if item.nfo:
                path = filetools.dirname(item.nfo)
            else:
                path = filetools.join(movies_videolibrary_path if item.contentType == 'movie' else series_videolibrary_path, item.video_path)
            for epi in filetools.listdir(path):
                if not epi.endswith('.json'): continue
                if epi not in matches_index: continue

                json_path = filetools.join(path, epi)
                itemlist.append(Item().fromjson(filetools.read(json_path)))
        elif AHkwargs.get('matches'):
            itemlist.append(item.clone(matches=AHkwargs['matches']))
        else:
            itemlist.append(item)
        if DEBUG: logger.debug('Matches_index (%s/%s): %s - Matches_post: %s' \
                                % (len(matches), len(itemlist), matches_index.keys(), matches_post))

        for x, it in enumerate(itemlist):
            if not it.matches: continue
            if not isinstance(it.matches[0], dict):
                if not matches_post: continue
                AHkwargs['videolibrary'] = True
                matches_it, langs = matches_post(it, it.matches, [], {}, **AHkwargs)
                AHkwargs['videolibrary'] = False
            else:
                matches_it = it.matches.copy()

            if it.contentType == 'movie':
                match_key = '%s [%s]' % (it.contentTitle, it.channel)
            else:
                match_key = '%sx%s [%s].json' % (it.contentSeason, str(it.contentEpisodeNumber).zfill(2), it.channel)
            if not matches_index.get(match_key): continue

            for match_it in matches_it:
                if item.action == 'findvideos':
                    match_key = match_it.get('url', '').replace(' ', '%20')
                    match_it['url'] = match_it['url'].replace(' ', '%20')
                    if match_key.startswith('//'): 
                        match_key = 'https:%s' % match_key
                        match_it['url'] = 'https:%s' % match_it['url']
                if match_it.get('url', '') and match_it['url'] not in matches_index.get(match_key, {}).get('url', ''):
                    if match_it.get('quality', '').replace('*', '') and matches_index.get(match_key, {}).get('quality', '') \
                                                   and matches_index[match_key]['quality'] in match_it['quality'].replace('*', ''): continue
                    if 'Digg' in match_it.get('torrent_info', '') and not btdigg_label in match_it.get('quality', '').replace('*', ''):
                        match_it['quality'] += btdigg_label
                    matches_out.append(match_it)
    except Exception:
        logger.error(traceback.format_exc())

    if DEBUG: logger.debug('Matches AÑADIDAS: %s / %s' % (len(matches_out), matches_out))
    return matches + matches_out


def AH_find_btdigg_list_all_from_channel_py(self, item, matches=[], matches_index={}, channel_alt=channel_py, 
                                            channel_entries=20, btdigg_entries=80, **AHkwargs):
    logger.info('"%s"' % len(matches))
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False

    matches_inter = []
    matches_btdigg = matches[:]
    controls = self.finds.get('controls', {})
    quality_control = AHkwargs.get('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    patron_year = r'\(?(\d{4})\)?'

    try:
        channel = __import__('channels.%s' % channel_alt, None,
                             None, ["channels.%s" % channel_alt])
        host_alt = channel.host
        finds_alt = channel.finds
        finds_alt_controls = channel.finds.get('controls', {})
        btdigg_cfg = channel.finds.get('btdigg_cfg', {})
        headers = {'Referer': channel.host}
        if not finds_alt or not btdigg_cfg or not finds_alt_controls.get('btdigg_service', True):
            if DEBUG: logger.debug('matches_PY: %s / %s' % (len(matches_btdigg), matches_btdigg))
            return matches_btdigg, matches_index

        try:
            if canonical.get('global_search_active', False):
                channel.canonical['global_search_active'] = True
            canonical_alt = channel.canonical
        except Exception:
            canonical_alt = {}
            
        y = btdigg_entries
        token = ''
        for elem_cfg in btdigg_cfg:
            if item.c_type not in elem_cfg['c_type']: continue
            finds_find_alt = elem_cfg.get('find', {}) or finds_alt.get('find', {})
            if not finds_find_alt:
                if DEBUG: logger.debug('matches_PY: %s / %s' % (len(matches_btdigg), matches_btdigg))
                return matches_btdigg, matches_index

            if elem_cfg['c_type'] == 'search_token':
                soup = self.create_soup(elem_cfg['url'], post=elem_cfg.get('post', None), timeout=channel.timeout, 
                                        headers=headers, canonical=canonical_alt, alfa_s=True)
                token = self.parse_finds_dict(soup, finds_find_alt, c_type='search')
                continue
            
            if elem_cfg['c_type'] == 'search':
                if elem_cfg.get('post', None): 
                    elem_cfg['post'] = elem_cfg['post'] % (token, item.texto)
                else:
                    elem_cfg['url'] = elem_cfg['url'] % item.texto

            soup = self.create_soup(elem_cfg['url'] + str(item.page), post=elem_cfg.get('post', None), timeout=channel.timeout, 
                                    headers=headers, canonical=canonical_alt, alfa_s=True)

            if not self.response.sucess:
                if DEBUG: logger.debug('ERROR matches_PY: %s / %s / %s' % (self.response.code, len(matches_btdigg), matches_btdigg))
                return matches_btdigg, matches_index
            if self.response.host:
                elem_cfg['url'] = elem_cfg['url'].replace(host_alt, self.response.host)
                host_alt = self.response.host

            item.btdig_in_use= True
            matches_inter = self.parse_finds_dict(soup, finds_find_alt, c_type=elem_cfg['c_type'])
            if isinstance(matches_inter, dict):
                matches_inter = matches_inter['data']['torrents']['0']
            if not matches_inter or isinstance(matches_inter, str):
                if DEBUG: logger.debug('matches_PY: %s / %s' % (len(matches_btdigg), matches_btdigg))
                return matches_btdigg, matches_index

            x = 0
            for elem in matches_inter if isinstance(matches_inter, list) else list(matches_inter.items()):
                elem_json = {}
                #logger.error(elem)

                if isinstance(matches_inter, list):
                    if not elem.find('div', class_='card-body'): continue
                    elem_json['url'] = elem.a.get("href", "")
                    elem_json['title'] = elem.find('div', class_='card-body').find('h3', class_='title').get_text(strip=True)
                    elem_json['year'] = scrapertools.find_single_match(elem_json['title'], r'\((\d{4})\)') or '-'
                    if elem_json['year'] in ['720', '1080', '2160']: elem_json['year'] = '-'
                    elem_json['thumbnail'] = elem.find('img').get("src", "")
                    if elem_json['thumbnail'].startswith('//'): elem_json['thumbnail'] = 'https:%s' % elem_json['thumbnail']
                    elem_json['quality'] = elem.find('div', class_='quality').get_text(strip=True)
                    elem_json['quality'] = elem_json['quality'].replace('creeener', 'creener')\
                                                               .replace('AC3 5.1', '').replace('HDTV 720p', 'HDTV-720p').strip()
                    elem_json['torrent_info'] = ''
                    elem_json['size'] = ''
                    elem_json['language'] = ['CAST']
                    
                    elem_json['mediatype'] = 'movie' if (elem_cfg.get('movie_path') and elem_cfg['movie_path'] in elem_json['url']) else 'tvshow'
                    if elem_cfg['c_type'] == 'peliculas' and elem_json['mediatype'] != 'movie': continue
                    if elem_cfg['c_type'] == 'episodios' and elem_json['mediatype'] != 'episode': continue

                    if elem_json['mediatype'] == 'episode':
                        try:
                            elem_json['season'] = int(scrapertools.find_single_match(elem.find('div', class_='card-body')\
                                                                  .find('span', class_='fdi-item').get_text(strip=True), r'(\d+)'))
                            if len(str(elem_json['season'])) > 2:
                                elem_json['season'] = int(scrapertools.find_single_match(elem_json['url'], r'/temporada-(\d+)'))

                            elem_json['episode'] = int(scrapertools.find_single_match(elem.find('div', class_='card-body')\
                                                                   .find('span', class_='fdi-type').get_text(strip=True), r'(\d+)'))
                            if len(str(elem_json['episode'])) > 3:
                                elem_json['episode'] = int(scrapertools.find_single_match(elem_json['url'], r'/capitulo-(\d+)'))
                        except:
                            logger.error(elem)
                            elem_json['season'] =  1
                            elem_json['episode'] =  1

                else:
                    elem = elem[1]
                    elem_json['url'] = self.urljoin(host_alt, elem.get('guid', ''))
                    elem_json['title'] = scrapertools.find_single_match(elem.get('torrentName', ''), r'(.*?)\[').strip()
                    elem_json['year'] = scrapertools.find_single_match(re.sub(r'(?i)cap\.\d+', '', elem_json['title']), '.+?'+patron_year) or '-'
                    if elem_json['year'] in ['720', '1080', '2160']: elem_json['year'] = '-'
                    elem_json['thumbnail'] = self.urljoin(host_alt, elem.get('imagen', ''))
                    elem_json['quality'] = elem.get('calidad', '')
                    elem_json['quality'] = elem_json['quality'].replace('creeener', 'creener')\
                                                               .replace('AC3 5.1', '').replace('HDTV 720p', 'HDTV-720p').strip()
                    elem_json['language'] = ['CAST']

                elem_json['media_path'] = self.movie_path.strip('/') if elem_json['mediatype'] == 'movie' else self.tv_path.strip('/')

                for clean_org, clean_des in finds_alt.get('title_clean', []):
                    if clean_des is None:
                        if scrapertools.find_single_match(elem_json['title'], clean_org):
                            elem_json['title'] = scrapertools.find_single_match(elem_json['title'], clean_org).strip()
                            break
                    else:
                        elem_json['title'] = re.sub(clean_org, clean_des, elem_json['title']).strip()
                title = elem_json['title'].lower().replace(' ', '_')
                if elem_json['mediatype'] != 'movie' and quality_control: title = '%s_%s' % (title, elem_json['quality'].replace('*', ''))
                if elem_json['mediatype'] == 'movie': elem_json['quality'] = elem_json['quality'].capitalize()

                language = elem_json.get('language', '')
                if not language or '*' in str(language): language = ['CAST']
                key = '%s_%s_%s' % (title, language, elem_json['mediatype'])
                if matches_index.get(key):
                    if elem_json['quality'] not in matches_index[key]['quality']:
                        matches_index[key]['quality'] += elem_json['quality'] if not matches_index[key]['quality'] \
                                                                              else ', %s' % elem_json['quality']
                    if DEBUG: logger.debug('DROP title dup: %s / %s' % (key, elem_json['quality']))
                    continue

                matches_btdigg.append(elem_json.copy())
                matches_index.update({key: {'title': elem_json['title'], 'mediatype': elem_json['mediatype'], 
                                            'quality': elem_json['quality'], 'matches_cached': [], 'episode_list': {}}})
                x += 1

                if x >= elem_cfg['cnt_tot'] * channel_entries: 
                    break

            y -= x
            if y <= 0: 
                break
        
    except Exception:
        logger.error(traceback.format_exc())

    if DEBUG: logger.debug('matches_PY: %s / %s \n%s' % (len(matches_btdigg), matches_btdigg, matches_index))
    return matches_btdigg, matches_index


def AH_find_btdigg_ENTRY_from_BTDIGG(self, title='', contentType='episode', language=['CAST'], matches=[], 
                                     item=Item(), reset=False, retry=False, **AHkwargs):
    global DEBUG, TEST_ON_AIR, cached_btdigg
    if not PY3: from lib.alfaresolver import get_cached_files
    else: from lib.alfaresolver_py3 import get_cached_files

    found = {} if not title else []
    timer = 15
    cached_btdigg_AGE = 0.0
    convert = ['.=', '-= ', ':=', '&=and', '  = ']
    missing = False
    search = False
    matches_cached_len = 0
    episode_list_len = 0

    if not isinstance(contentType, list):
        contentType = [contentType]
    if 'search' in contentType:
        search = True
        contentType.remove('search')
        if 'movie' not in contentType: contentType += ['movie']
        if 'episode' not in contentType: contentType += ['episode']
    for c_type in contentType:
        if c_type not in ['movie', 'tvshow', 'episode']:
            return found
        if len(window.getProperty("alfa_cached_btdigg_%s_list" % c_type)) < 3:
            missing = True

    cached_btdigg_AGE = float(window.getProperty("alfa_cached_btdigg_list_AGE") or 0.0) if not reset else 0.0
    if DEBUG: logger.debug('"%s" / %s / %s' % (title, contentType, round((cached_btdigg_AGE-time.time())/60, 2)))
    if cached_btdigg_AGE < time.time() or missing:
        if cached_btdigg_AGE < time.time():
            for c_type in ['movie', 'tvshow', 'episode']:
                window.setProperty("alfa_cached_btdigg_%s_list" % c_type, "")
        for c_type in contentType:
            if len(window.getProperty("alfa_cached_btdigg_%s_list" % c_type)) < 3:
                item.AH_find_btdigg_ENTRY_from_BTDIGG = True
                if c_type == 'movie':
                    item.c_type = 'peliculas'
                    matches_btdigg, cached_btdigg[c_type] = AH_find_btdigg_list_all_from_BTDIGG(self, item, **AHkwargs)
                    window.setProperty("alfa_cached_btdigg_%s_list" % c_type, jsontools.dump(cached_btdigg[c_type], **kwargs_json))
                else:
                    time_now = time.time()
                    cached_btdigg[c_type] = get_cached_files(c_type)
                    window.setProperty("alfa_cached_btdigg_%s_list" % c_type, jsontools.dump(cached_btdigg[c_type], **kwargs_json))
                    if isinstance(cached_btdigg[c_type], dict):
                        for key, value in cached_btdigg[c_type].items():
                            episode_list_len += len(value.get('episode_list', {}))
                            for key_, value_ in value['episode_list'].items():
                                matches_cached_len += len(value_.get('matches_cached', []))
                                for epi in value_.get('matches_cached', []):
                                    if (epi.get('password', {}) and isinstance(epi['password'], dict)) \
                                                                or str(epi.get('password', '')) == 'Contraseña DESCONOCIDA':
                                        epi['password'] = find_rar_password(epi)
                                        if isinstance(epi['password'], dict) or str(epi.get('password', '')) == 'Contraseña DESCONOCIDA':
                                            epi['password'] = 'Contraseña DESCONOCIDA'
                                            for elem_pass in matches:
                                                if elem_pass.get('season', 0) == epi.get('season', -1) \
                                                                                 and elem_pass.get('episode', 0) == epi.get('episode', -1) \
                                                                                 and elem_pass.get('password'):
                                                    epi['password'] = elem_pass['password']
                                                    break
                    logger.info('CACHED %s[%s]: %s; e: %s q: %s' \
                                % (item.c_type or 'Seasons', round(time.time()-time_now, 2), len(cached_btdigg[c_type]), 
                                   episode_list_len, matches_cached_len), force=True)
                    episode_list_len = matches_cached_len = 0
        if cached_btdigg_AGE < time.time():
            cached_btdigg_AGE = time.time() + timer*60
            window.setProperty("alfa_cached_btdigg_list_AGE", str(cached_btdigg_AGE))

    exists = 0
    for c_type in contentType:
        if cached_btdigg[c_type]:
            exists += 1
            continue
        cached_btdigg[c_type] = jsontools.load(window.getProperty("alfa_cached_btdigg_%s_list" % c_type))
        if cached_btdigg[c_type]: exists += 1
    if exists == 0:
        window.setProperty("alfa_cached_btdigg_list_AGE", "")
        if reset:
            for c_type in contentType:
                logger.error('ERROR: missing file in %s[%s]: %s' % (c_type, round((cached_btdigg_AGE-time.time())/60, 2), 
                                                                    window.getProperty("alfa_cached_btdigg_%s_list" % c_type)))
        if not retry and not reset:
            return AH_find_btdigg_ENTRY_from_BTDIGG(self, title=title, contentType=contentType if not search else 'search', 
                                                    language=language, matches=matches, item=item, reset=reset, retry=True, **AHkwargs)
        return found

    for c_type in contentType:
        if DEBUG: logger.debug('cached_btdigg[%s/%s]: %s' % (c_type, len(cached_btdigg[c_type]), cached_btdigg[c_type].keys()))

    if not title:
        for c_type in contentType:
            if cached_btdigg.get(c_type):
                found.update(copy.deepcopy(cached_btdigg[c_type]))

    else:
        title_search = ''
        title_alt = ''
        alias = {}
        alias_in = ''
        alias_out = ''
        if '#' in item.season_search:
            alias = search_btdigg_free_format_parse({}, item, titles_search=BTDIGG_SEARCH)[0].get('aliases', {})
            if alias:
                alias_in = list(alias.keys())[0].lower().replace(' ', '_')
                alias_out = list(alias.values())[0].lower().replace(' ', '_')
        for c_type in contentType:
            title_search = title
            if "en espa" in title_search: title_search = title_search[:-11]
            title_search = alias_in or scrapertools.slugify(title_search, strict=False, convert=convert)\
                                                            .strip().lower().replace(' ', '_').replace('(V)-', '')
            title_alt = alias_out or scrapertools.slugify(item.infoLabels['title_alt'] or item.title, strict=False, convert=convert)\
                                     .strip().lower().replace(' ', '_').replace('(V)-', '').replace('class_act', '').replace('buscar', '')
            if title_search == title_alt: title_alt = ''
            if c_type == 'movie' and not search:
                title_search = '%s_%s_%s' % (title_search, str(language), c_type)
                if title_alt: title_alt = '%s_%s_%s' % (title_alt, str(language), c_type)
            if search:
                for title_s in cached_btdigg[c_type].keys():
                    #logger.error('%s, %s, %s' % (title_s, title_search, title_alt))
                    if (title_search and title_search in title_s) or (title_alt and title_alt in title_s):
                        if c_type == 'episode':
                            found.append({alias_out or title_s: AH_reset_alias(copy.deepcopy(cached_btdigg[c_type].get(title_s, {})), alias)})
                        else:
                            found.append(AH_reset_alias(copy.deepcopy(cached_btdigg[c_type].get(title_s, {})), alias))
                        matches_cached_len += len(cached_btdigg[c_type].get(title_s, {}).get('matches_cached', []))
                        episode_list_len += len(cached_btdigg[c_type].get(title_s, {}).get('episode_list', {}))
            elif cached_btdigg[c_type].get(title_search, {}) or cached_btdigg[c_type].get(title_alt or 'null', {}):
                for title_s in [title_search, title_alt]:
                    if not title_s: continue
                    if cached_btdigg[c_type].get(title_s, {}):
                        if c_type == 'episode':
                            found.append({alias_out or title_s: AH_reset_alias(copy.deepcopy(cached_btdigg[c_type].get(title_s, {})), alias)})
                        else:
                            found.append(AH_reset_alias(copy.deepcopy(cached_btdigg[c_type].get(title_s, {})), alias))
                    if found: break
                matches_cached_len += len(cached_btdigg[c_type].get(title_search, {}).get('matches_cached', []))
                episode_list_len += len(cached_btdigg[c_type].get(title_search, {}).get('episode_list', {}))

        if DEBUG: 
            logger.debug('found [%s / %s] [%s]: [%s:%s/%s] / %s' % (title_search, title_alt, contentType, 
                          len(found), matches_cached_len, episode_list_len, str(found)[:5000]))
        else:
            logger.info('found [%s / %s][%s] [%s]: [%s:%s/%s]' % (title_search, title_alt, round((cached_btdigg_AGE-time.time())/60, 2), 
                         contentType, len(found), matches_cached_len, episode_list_len))

    return found


def AH_reset_alias(content, alias):

    if not alias or not content.get('title'):
        return content

    if not alias.get(content['title'].lower()):
        return content

    if DEBUG: logger.debug('ALIAS "%s": %s -> %s' % (alias, content['title'].lower(), alias.get(content['title'].lower())))
    
    try:
        content['url'] = content['url'].replace(content['title'].lower(), alias[content['title'].lower()])
        content['title'] = content['title'].lower().replace(content['title'].lower(), alias[content['title'].lower()]).lower()
        if content.get('tmdb_id'): del content['tmdb_id']

        if content.get('matches_cached'):
            for cont_ in content['matches_cached']:
                cont_['title'] = cont_['title'].replace(cont_['title'], alias[cont_['title'].lower()]).capitalize()
                if cont_.get('tmdb_id'): del cont_['tmdb_id']

        if content.get('episode_list'):
            for epi, cont_ in content['episode_list'].items():
                cont_['title'] = cont_['title'].replace(cont_['title'], alias[cont_['title'].lower()]).capitalize()
                if cont_.get('tmdb_id'): del cont_['tmdb_id']

                if cont_.get('matches_cached'):
                    for cont__ in cont_['matches_cached']:
                        cont__['title'] = cont__['title'].replace(cont__['title'], alias[cont__['title'].lower()]).capitalize()
                        if cont__.get('tmdb_id'): del cont__['tmdb_id']
    except Exception:
        logger.error(traceback.format_exc())

    return content


def AH_reset_alias_item(item, title):

    if 'tmdb_id' in item.infoLabels: item.infoLabels['tmdb_id'] = ''
    if 'tvdb_id' in item.infoLabels: item.infoLabels['tvdb_id'] = ''
    if 'imdb_id' in item.infoLabels: item.infoLabels['imdb_id'] = ''
    if 'IMDBNumber' in item.infoLabels: item.infoLabels['IMDBNumber'] = ''
    item.infoLabels['year'] = ''
    if item.infoLabels['tvshowtitle']: item.infoLabels['tvshowtitle'] = title.capitalize()
    if item.infoLabels['title']: item.infoLabels['title'] = title.capitalize()
    if 'title_alt' in item.infoLabels: del item.infoLabels['title_alt']


def AH_find_btdigg_ENTRY_SEASON_from_BTDIGG(self, contentType='tvshow', language=['CAST'], found={}, 
                                            matches_index={}, item=Item(), search=False, **AHkwargs):
    matches_btdigg = []
    controls = self.finds.get('controls', {})
    quality_control = AHkwargs.get('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    quality = [''] if not quality_control else ['HDTV', 'HDTV-720p']

    for serie, value in found.items():
        value['mediatype'] = contentType
        value['media_path'] = 'serie'
        if value.get('season'): del value['season']
        if value.get('episode_limits'): del value['episode_limits']

        for q in quality:
            title = ('%s_%s' % (serie, q)) if q else serie
            key = '%s_%s_%s' % (title, value['language'], contentType)
            episode_list = copy.deepcopy(value.get('episode_list', {}))

            if q and episode_list:
                for epi, epi_value in episode_list.copy().items():
                    x = 0

                    for epi_qual in epi_value.get('matches_cached', [])[:]:
                        if q == 'HDTV':
                            if epi_qual.get('quality', 'HDTV-720p') != q:
                                del episode_list[epi]['matches_cached'][x]
                                continue
                        elif q == 'HDTV-720p':
                            if epi_qual.get('quality', 'HDTV-720p') == 'HDTV':
                                del episode_list[epi]['matches_cached'][x]
                                continue
                        x += 1

                    if not epi_value.get('matches_cached', []):
                        del episode_list[epi]

            if matches_index.get(key):
                if not search: matches_index[key]['episode_list'] = episode_list.copy()
                if DEBUG: logger.debug('matches_index: %s / %s' % (title, len(matches_index[key]['episode_list'])))
            else:
                value_alt = copy.deepcopy(value)
                #if not search: value_alt['episode_list'] = episode_list.copy()
                value_alt['episode_list'] = episode_list.copy()
                value_alt['quality'] = q
                value_alt['ENTRY_SEASON'] = True
                matches_btdigg.append(value_alt.copy())

    return matches_btdigg, matches_index


def AH_find_btdigg_list_all_from_BTDIGG(self, item, matches=[], matches_index={}, channel_alt=channel_py, 
                                        channel_entries=15, btdigg_entries=45, titles_search=[], **AHkwargs):
    logger.info('"%s": %s' % (len(matches), item.c_type))
    global DEBUG, TEST_ON_AIR, cached_btdigg
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    ASSISTANT_REMOTE = True if config.get_setting("assistant_mode").lower() == 'otro' else False

    matches_inter = []
    matches_btdigg = matches[:]
    matches_len = len(matches_btdigg)

    controls = self.finds.get('controls', {}) if self else {}
    btdigg_search = controls.get('btdigg_search', True)
    disable_cache = True
    quality_control = AHkwargs.get('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    if item.btdigg: quality_control = False
    canonical = AHkwargs.get('canonical', self.canonical if self else {})

    title_clean = AHkwargs.get('finds', {}).get('title_clean', [])
    title_clean.append([r'(?i)\s*UNCUT', ''])
    patron_title = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[)'
    patron_title_b = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[|\s+-)'
    patron_sea = r'(?i)Cap.(\d{1,2})\d{2}'
    patron_year = r'\(?(\d{4})\)?'
    convert = ['.=', '-= ', ':=', '&=and', '  = ']
    language_alt = []
    quality_alt = ''
    
    try:
        titles_search_finds = []
        if self and self.finds.get('titles_search', {}).get('list_all') and item.c_type != 'search':
            titles_search_finds = self.finds['titles_search']['list_all']
        if self and self.finds.get('titles_search', {}).get('search') and item.c_type == 'search' \
                and BTDIGG_URL_SEARCH not in item.texto and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
            titles_search_finds = self.finds['titles_search']['search']
        if self and self.finds.get('titles_search', {}).get('btdigg_search') and item.c_type == 'search' \
                and (BTDIGG_URL_SEARCH in item.texto or BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow):
            titles_search_finds = self.finds['titles_search']['btdigg_search']
        if titles_search_finds:
            titles_search.extend(titles_search_finds)
            if BTDIGG_URL_SEARCH in item.texto or BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow:
                titles_search = search_btdigg_free_format_parse(self, item, titles_search, item.contentType, **AHkwargs)
            elif item.c_type == 'search':
                titles_search = search_btdigg_free_format_parse(self, item, titles_search, item.c_type, **AHkwargs)
        elif BTDIGG_URL_SEARCH in item.texto or BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow:
            titles_search = search_btdigg_free_format_parse(self, item, BTDIGG_SEARCH, item.contentType, **AHkwargs)
        if not titles_search:
            if '[' in item.season_search:
                quality_alt = search_btdigg_free_format_parse(self, item.clone(), BTDIGG_SEARCH, item.contentType)[0].get('quality_alt', {})
                if quality_alt: quality_alt += ' '
            titles_search = [{'urls': ['%s ' + quality_alt + channel_alt], 'checks': ['Cast', 'Esp', 'Spanish', channel_alt.replace('4k', '')], 
                              'contentType': 'movie', 'limit_search': 1.5}]
            if not item.AH_find_btdigg_ENTRY_from_BTDIGG:
                titles_search.append({'urls': ['%s ' + (quality_alt or 'Bluray ') + 'Castellano'], 
                                      'checks': ['Cast', 'Esp', 'Spanish', channel_alt.replace('4k', '')], 
                                      'contentType': 'movie', 'limit_search': 1.5})
            titles_search.append({'urls': ['%s ' + (quality_alt or 'HDTV 720p')], 'checks': ['Cap.'], 'contentType': 'tvshow', 'limit_search': 5})
            if item.c_type == 'search' or item.AH_find_btdigg_ENTRY_from_BTDIGG:
                titles_search = search_btdigg_free_format_parse(self, item, titles_search, item.c_type, **AHkwargs)

        if canonical.get('global_search_cancelled', False) or (config.GLOBAL_SEARCH_CANCELLED \
                                                           and canonical.get('global_search_active', False)):
            logger.info('## Búsqueda global cancelada: %s: %s' % (item.channel, item.title), force=True)
            return matches_btdigg, matches_index

        format_tmdb_id(item)
        contentType = 'tvshow' if item.c_type == 'series' else 'movie' if item.c_type == 'peliculas' else ''

        if item.c_type == 'search' and not item.btdigg:
            found = (AH_find_btdigg_ENTRY_from_BTDIGG(self, title=item.texto or item.contentTitle, contentType=item.c_type, 
                                                      matches=matches_btdigg, item=item.clone(), reset=False, **AHkwargs))
            for found_item in found:
                if found_item and found_item.get('matches_cached'):
                    title = scrapertools.slugify(re.sub(r'\s*\[.*?\]', '', found_item.get('title', '')), 
                                                        strict=False, convert=convert).strip().lower().replace(' ', '_')
                    key = '%s_%s_%s' % (title, found_item.get('language', ['CAST']), found_item.get('mediatype', ''))
                    if matches_index.get(key, {}).get('quality', []):
                        if found_item.get('quality', '') not in matches_index[key]['quality']:
                            matches_index[key]['quality'] += found_item['quality'] if not matches_index[key]['quality'] \
                                                                                   else ', %s' % found_item['quality']
                        continue
                    matches_index.update({key: {'title': found_item['title'], 'mediatype': found_item['mediatype'], 
                                                'quality': found_item['quality'], 'matches_cached': [], 'episode_list': {}}})
                    matches_btdigg.append(found_item)

                else:
                    values = list(found_item.values())[0]
                    if values.get('mediatype', '') == 'season':
                        found_item, matches_index = AH_find_btdigg_ENTRY_SEASON_from_BTDIGG(self, found=found_item, matches_index=matches_index, 
                                                                                            item=item, search=True, **AHkwargs)
                        if found_item: matches_btdigg.extend(found_item)

        if not PY3: from lib.alfaresolver import find_alternative_link
        else: from lib.alfaresolver_py3 import find_alternative_link

        for title_search in titles_search:
            if contentType and title_search.get('contentType', 'movie') != contentType: continue

            if not item.btdigg:
                quality_alt = '720p 1080p 2160p 4kwebrip 4k'
                if item.c_type in ['peliculas', 'search'] and 'HDTV' not in str(title_search['urls']):
                    quality_alt += ' bluray rip screener'
                    language_alt = ['DUAL', 'CAST', 'LAT']
                    if item.c_type in ['search'] and channel_alt in str(title_search['urls']):
                        quality_alt += ' HDTV'
                else:
                    if not quality_control:
                        quality_alt += ' HDTV'
                    elif item.quality and '720' not in item.quality and '1080' not in item.quality and '4k' not in item.quality:
                        quality_alt = 'HDTV'

            limit_search = int((title_search.get('limit_search', 2) * channel_entries) / 10)
            limit_pages = limit_search
            limit_pages_min = limit_search if (channel_alt in str(title_search['urls']) or 'HDTV' in str(title_search['urls'])) \
                                           else limit_search / 2
            interface = str(config.get_setting('btdigg_status', server='torrent'))
            limit_items_found = 5 * 10 if interface != '200' else 10 * 10

            torrent_params = {
                              'find_alt_news': [title_search] if item.c_type != 'search' else [], 
                              'title_prefix': [title_search] if item.c_type == 'search' else [], 
                              'quality_alt': title_search.get('quality_alt', '') or quality_alt, 
                              'language_alt': title_search.get('language_alt', []) or language_alt, 
                              'find_alt_link_next': 0, 
                              'limit_pages': limit_pages, 
                              'domain_alt': None, #find_alt_domains,
                              'extensive_search': False if item.c_type != 'search' else True,
                              'search_order': title_search['search_order'] if 'search_order' in title_search else \
                                                                         2 if item.c_type == 'search' else 0,
                              'link_found_limit': 20000 if item.c_type != 'search' else 100000, 
                              'find_catched': True if item.c_type != 'search' else False
                              }

            x = 0
            while x < limit_pages:
                use_assistant = True
                try:
                    alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                except:
                    alfa_gateways = []
                if (xbmc.Player().isPlaying() or ASSISTANT_REMOTE) and len(alfa_gateways) > 1:
                    use_assistant = False
                torrent_params = find_alternative_link(item, torrent_params=torrent_params, cache=disable_cache, use_assistant=use_assistant)

                if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                if not torrent_params.get('find_alt_link_result') and torrent_params.get('find_alt_link_next', 0) >= limit_pages_min: x = 999999
                if not torrent_params.get('find_alt_link_next'): x = 999999
                if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                    limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                x += 1

                for y, elem in enumerate(torrent_params['find_alt_link_result']):
                    elem_json = {}
                    elem_json_save = {}
                    alias = {}
                    alias_in = alias_out = ''
                    #logger.error(torrent_params['find_alt_link_result'][y])

                    try:
                        if '#' in elem.get('season_search', ''):
                            alias = search_btdigg_free_format_parse({}, item.clone(btdigg=elem['season_search']), 
                                                                    titles_search=BTDIGG_SEARCH)[0].get('aliases', {})
                            if alias:
                                alias_in = list(alias.keys())[0].replace('_', ' ').capitalize()
                                alias_out = list(alias.values())[0].replace('_', ' ').capitalize()
                        elem_json['url'] = elem.get('url', '')
                        elem_json['language'] = elem.get('language', [])
                        elem_json['quality'] = elem.get('quality', '').replace('HDTV 720p', 'HDTV-720p').replace(btdigg_label, '').strip()
                        elem_json['mediatype'] = elem.get('mediatype', '') or 'tvshow' if 'Cap.' in elem.get('title', '')\
                                                                              .replace(btdigg_label_B, '') else 'movie'
                        if elem_json['mediatype'] == 'movie':
                            elem_json['quality'] = elem_json['quality'].capitalize()
                        else:
                            if not elem_json.get('season'):
                                elem_json['season'] = int(scrapertools.find_single_match(elem.get('title', '').replace(btdigg_label_B, '') or 1, 
                                                          patron_sea))
                            if elem.get('episode'): elem_json['episode'] = elem.get('episode')

                        elem_json['title'] = elem.get('title', '').replace(btdigg_label_B, '')
                        elem_json['year'] = scrapertools.find_single_match(re.sub(r'(?i)cap\.\d+', '', elem_json['title']), '.+?'+patron_year) or '-'
                        if elem_json['year'] in ['720', '1080', '2160']: elem_json['year'] = '-'
                        if scrapertools.find_single_match(elem_json['title'], patron_title).strip():
                            elem_json['title'] = scrapertools.find_single_match(elem_json['title'], patron_title).strip()
                        elif scrapertools.find_single_match(elem_json['title'], patron_title_b).strip():
                            elem_json['title'] = scrapertools.find_single_match(elem_json['title'], patron_title_b).strip()
                        else:
                            if DEBUG: logger.debug('Error en PATRON: %s / %s' % (elem_json['title'], patron_title))
                            continue
                        for clean_org, clean_des in title_clean:
                            if clean_des is None:
                                if scrapertools.find_single_match(elem_json['title'], clean_org):
                                    elem_json['title'] = scrapertools.find_single_match(elem_json['title'], clean_org).strip()
                                    break
                            else:
                                elem_json['title'] = re.sub(clean_org, clean_des, elem_json['title']).strip()
                        elem_json['title'] = elem_json['title'].replace('- ', '')
                        title = scrapertools.slugify(elem_json.get('title', ''), strict=False, convert=convert).strip().lower().replace(' ', '_')
                        elem_json['title'] = elem_json['title'].replace(':', '')
                        if elem_json['mediatype'] != 'movie' and quality_control: title = '%s_%s' % (title, elem_json['quality'])

                        elem_json['media_path'] = elem_json['mediatype']
                        if self:
                            elem_json['media_path'] = self.movie_path.strip('/') if elem_json['mediatype'] == 'movie' else self.tv_path.strip('/')
                        elem_json['torrent_info'] = elem.get('torrent_info', '')
                        elem_json['torrent_info'] = elem.get('size', '').replace(btdigg_label_B, '').replace('GB', 'G·B').replace('Gb', 'G·b')\
                                                                        .replace('MB', 'M·B').replace('Mb', 'M·b').replace('.', ',')\
                                                                        .replace('\xa0', ' ')
                        elem_json['torrent_info'] += ' (%s)' % (alias_in or elem_json['title'])
                        elem_json['size'] = elem.get('size', '').replace(btdigg_label_B, '')\
                                                                .replace('\xa0', ' ')\
                                                                .replace('[COLOR magenta][B]RAR-[/B][/COLOR]', '')
                        if self and elem_json['mediatype'] in ['movie', 'episode']: elem_json['size'] = self.convert_size(elem_json['size'])
                        quality = elem_json['quality'].replace(btdigg_label, '')
                        elem_json['quality'] = '%s%s' % (quality, btdigg_label)
                        elem_json['server'] = 'torrent'
                        if elem.get('title_subs'): elem_json['title_subs'] = elem['title_subs']
                        if elem.get('season_search', ''): elem_json['season_search'] = elem['season_search']
                        if item.btdigg: elem_json['btdigg'] = elem_json['season_search'] = item.btdigg

                        if (elem.get('password', {}) and isinstance(elem['password'], dict)) \
                                                     or str(elem.get('password', '')) == 'Contraseña DESCONOCIDA':
                            elem['password'] = elem_json['password'] = 'Contraseña DESCONOCIDA'
                            elem_json['password'] = find_rar_password(elem_json)
                            if str(elem_json.get('password', '')) == 'Contraseña DESCONOCIDA':
                                for elem_pass in matches_btdigg:
                                    if elem_pass.get('mediatype', '') in ['movie'] and elem_pass.get('password', ''):
                                        elem_json['password'] = elem_pass.get('password', '')
                                        break
                                    if elem_pass.get('season', 0) == elem_json.get('season', -1) \
                                                                     and elem_pass.get('episode', 0) == elem_json.get('episode', -1) \
                                                                     and elem_pass.get('password'):
                                        elem_json['password'] = elem_pass['password']
                                        break
                        elif elem.get('password'):
                            elem_json['password'] = elem['password']

                        language = elem_json['language'][:]
                        if 'DUAL' in language and len(language) > 1: language.remove('DUAL')
                        if 'DUAL' in language and len(language) == 1: language = ['CAST']
                        key = '%s_%s_%s' % (title, language, elem_json['mediatype'])
                        elem_json_save = copy.deepcopy(elem_json)
                        if elem_json_save['mediatype'] not in ['episode'] and elem_json_save.get('episode'): del elem_json_save['episode']
                        if elem_json['mediatype'] == 'season': elem_json['mediatype'] = 'episode'
                        if matches_index.get(key, {}).get('quality'):
                            if elem_json['url'] not in str(matches_index[key]):
                                if quality not in matches_index[key]['quality'].split(', '):
                                    matches_index[key]['quality'] += ', %s' % quality
                                    if DEBUG: logger.debug('QUALITY added: %s / %s' % (key, quality))
                                matches_index[key]['matches_cached'].append(elem_json.copy())
                            if elem_json['title'] not in str(matches_btdigg):
                                matches_btdigg.append(elem_json_save.copy())
                            continue

                        item.btdig_in_use =  True
                        matches_btdigg.append(elem_json_save.copy())
                        matches_index.update({key: {'title': elem_json['title'], 'mediatype': elem_json['mediatype'], 'url': elem_json['url'], 
                                                    'quality': quality, 'matches_cached': [elem_json.copy()]}})

                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    
        #if item.c_type == 'peliculas' and matches_btdigg: matches_btdigg = sorted(matches_btdigg, key=lambda it: int(-it['size']))

    except Exception:
        logger.error(traceback.format_exc())

    if item.c_type in ['peliculas']:
        window.setProperty("alfa_cached_btdigg_%s_list" % 'movie', jsontools.dump(matches_index, **kwargs_json))
    if DEBUG: logger.debug('matches_BTDIGG: %s / %s \r\n%s' % (len(matches_btdigg), str(matches_btdigg)[:SIZE_MATCHES], 
                                                               str(matches_index)[:SIZE_MATCHES]))
    return matches_btdigg, matches_index


def AH_find_btdigg_list_all(self, item, matches=[], channel_alt=channel_py, titles_search=[], **AHkwargs):
    logger.info('"%s"' % len(matches))
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False

    canonical = self.canonical
    controls = self.finds.get('controls', {})
    quality_control = AHkwargs.get('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    if item.btdigg: quality_control = False
    if not controls:
        return matches

    news_allowed = {
                    'dontorrent': ['peliculas', 'series', 'search'],
                    'ANY': ['peliculas', 'series', 'search']
                   }
    if not item or (item.c_type not in news_allowed.get(item.channel, []) and item.c_type not in news_allowed.get('ANY', [])):
        return matches

    format_tmdb_id(item)
    
    try:
        if canonical.get('global_search_cancelled', False) or (config.GLOBAL_SEARCH_CANCELLED \
                                                           and canonical.get('global_search_active', False)):
            logger.info('## Búsqueda global cancelada: %s: %s' % (item.channel, item.title), force=True)
            return matches

        channel_entries = controls.get('cnt_tot', 20)
        btdigg_entries = channel_entries * 4 if (item.c_type == 'peliculas' or quality_control) else channel_entries * 3
        matches_inter = []
        matches_btdigg = []
        matches_index = {}
        convert = ['.=', '-= ', ':=', '&=and', '  = ']
        matches_len = len(matches)

        for elem_json in matches:
            language = elem_json.get('language', '')
            if not language or '*' in str(language): language = elem_json['language'] = ['CAST']
            mediatype = elem_json['mediatype'] = elem_json.get('mediatype', '') or ('movie' if self.movie_path in elem_json['url'] else 'tvshow')

            if 'pelicula' in item.c_type or self.movie_path in elem_json.get('url', '') or mediatype == 'movie':
                title = scrapertools.slugify(re.sub(r'\s*\[.*?\]', '', elem_json.get('title', '')), 
                                             strict=False, convert=convert).strip().lower().replace(' ', '_')
                elem_json['quality'] = quality = elem_json.get('quality', '').replace('*', '').replace('-', ' ').capitalize()

            else:
                title = scrapertools.slugify(re.sub(r'\s+-\s+\d+.+?$', '', elem_json.get('title', '')), 
                                             strict=False, convert=convert).strip().lower().replace(' ', '_')
                quality = elem_json.get('quality', '').replace('*', '') or 'HDTV'
                if '[' in quality: quality = scrapertools.find_single_match(quality, r'\[(.*?)\]').strip() or 'HDTV'
                if quality_control: title = '%s_%s' % (title, quality)
            
            key = '%s_%s_%s' % (title, language, mediatype)
            if matches_index.get(key, {}).get('quality', []):
                if quality not in matches_index[key]['quality'].split(', '):
                    matches_index[key]['quality'] += quality if not matches_index[key]['quality'] else ', %s' % quality
                continue
            matches_index.update({key: {'title': elem_json['title'], 'mediatype': elem_json['mediatype'], 
                                        'quality': quality, 'matches_cached': [], 'episode_list': {}}})

            matches_inter.append(elem_json.copy())

        matches_btdigg = matches_inter[:channel_entries]
        matches = []

        if False: # channeltools.is_enabled(channel_alt):
            matches_btdigg, matches_index = AH_find_btdigg_list_all_from_channel_py(self, item, matches=matches_btdigg, 
                                                                                    matches_index=matches_index, channel_alt=channel_alt, 
                                                                                    channel_entries=channel_entries, btdigg_entries=btdigg_entries, 
                                                                                    **AHkwargs)
        matches_btdigg, matches_index = AH_find_btdigg_list_all_from_BTDIGG(self, item, matches=matches_btdigg, matches_index=matches_index, 
                                                                            channel_alt=channel_alt, channel_entries=channel_entries, 
                                                                            btdigg_entries=btdigg_entries, titles_search=titles_search, 
                                                                            **AHkwargs)

        if len(matches_btdigg) == channel_entries: matches_btdigg = matches_inter[:]
        x = 0
        for elem_json in matches_btdigg:
            #logger.error(elem_json)
            if 'magnet' in elem_json.get('url', '') or btdigg_url in elem_json.get('url', '') or channel_alt in elem_json.get('thumbnail', ''):

                season = elem_json.get('season', 0)
                if elem_json['mediatype'] not in ['episode'] and elem_json.get('season', 0): del elem_json['season']
                # Slugify, pero más light
                elem_json['title'] = scrapertools.htmlclean(elem_json['title']).strip()
                elem_json['title'] = elem_json['title'].replace("á", "a").replace("é", "e").replace("í", "i")\
                                                       .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                                                       .replace("ï¿½", "ñ").replace("Ã±", "ñ").replace(' - ', ' ')
                elem_json['title'] = scrapertools.decode_utf8_error(elem_json['title']).strip()
                if "en espa" in elem_json['title']: elem_json['title'] = elem_json['title'][:-11]

                language = 'latino' if 'latino/' in elem_json['url'] else ''
                elem_json['language'] = '*latino' if 'latino/' in elem_json['url'] else elem_json.get('language', '*')
                media_path = elem_json.pop('media_path', '')
                if item.btdigg: media_path = 'search'
                url_final = '%s%s_btdig/%s%s' % (btdigg_url, media_path, language, elem_json['title'].replace(' ', '-').lower().strip())
                quality = elem_json['quality'].replace(btdigg_label, '')
                elem_json['quality'] = '%s%s' % (quality.capitalize(), btdigg_label)
                elem_json['btdig_in_use'] = True
                url_save = scrapertools.slugify(re.sub(r'(?:\s+\(+\d{4}\)+$|\s*-\s*Temp.*?$|\s+-\s+\d+.*?$)', '', elem_json['title']), 
                                                strict=False, convert=convert)

                if elem_json['mediatype'] == 'movie':
                    elem_json['url'] = url_final
                    x += 1
                    matches.append(elem_json.copy())

                elif elem_json['mediatype'] in ['tvshow', 'season', 'episode'] or 'documental' in elem_json['url']:
                    elem_json['title'] = re.sub(r'(?i)\s*-*\s*temp\w*\s*\d*\s*', '', elem_json['title'])
                    if not quality_control or elem_json.get('ENTRY_SEASON'):
                        quality = "HDTV, HDTV-720p" if not item.btdigg and not elem_json.get('ENTRY_SEASON') else quality
                        if elem_json.get('ENTRY_SEASON'): del elem_json['ENTRY_SEASON']
                        elem_json['quality'] = "%s%s" % (quality, btdigg_label)
                        elem_json['url'] = url_final
                        if season: elem_json['url'] = '%s-temporada-%s' % (elem_json['url'], season)
                        if item.extra in ['novedades']: elem_json['title_subs'] = ['BTDIGG_INFO']
                        x += 1
                        matches.append(elem_json.copy())

                    else:
                        for q in ['HDTV', 'HDTV-720p']:
                            title_temp = '%s [%s]' % (url_save, q)
                            quality = q
                            elem_json['quality'] = '%s%s' % (q, btdigg_label)
                            elem_json['url'] = '%s%s' % (url_final, '-%s' % q if '720p' in q else '')
                            if season: elem_json['url'] = '%s-temporada-%s' % (elem_json['url'], season)
                            if item.extra in ['novedades']: 
                                elem_json['title_subs'] = ['BTDIGG_INFO', unify.set_color('720p', 'quality') if '720p' in q else '']
                            x += 1
                            matches.append(elem_json.copy())

            else:
                matches.append(elem_json.copy())

            if x >= btdigg_entries + matches_len: 
                break

    except Exception:
        logger.error(traceback.format_exc())

    for elem_json in matches:
        language = elem_json.get('language', [])
        if not language or '*' in str(language): language = ['CAST']
        if 'DUAL' in language and len(language) > 1: language.remove('DUAL')
        if 'DUAL' in language and len(language) == 1: language = ['CAST']
        mediatype = elem_json['mediatype'] = elem_json.get('mediatype', '') or ('movie' if self.movie_path in elem_json['url'] else 'tvshow')
        title = scrapertools.slugify(re.sub(r'\s+-\s+\d+.+?$', '', elem_json.get('title', '')), 
                                             strict=False, convert=convert).strip().lower().replace(' ', '_')
        if mediatype != 'movie' and quality_control: title = '%s_%s' % (title, elem_json['quality'].replace('*', '').replace(btdigg_label, ''))
        if mediatype == 'movie': elem_json['quality'].capitalize()
        key = '%s_%s_%s' % (title, language, mediatype)
        
        if matches_index.get(key, {}).get('quality'):
            quality = elem_json['quality'].replace('*', '').replace(btdigg_label, '').split(', ')
            for q in quality:
                if not q in matches_index[key]['quality'].split(', '):
                    matches_index[key]['quality'] += ', %s' % q

            elem_json['quality'] = matches_index[key]['quality']
            if matches_index.get(key, {}).get('matches_cached', []) and mediatype != 'tvshow':
                elem_json['matches_cached'] = matches_index[key]['matches_cached'][:]
                if mediatype != 'movie':
                    elem_json['matches_cached'] = sorted(elem_json['matches_cached'], key=lambda \
                                                         it: (int(it.get('season', 0)), int(it.get('episode', 0)), it.get('quality', '')))
            if matches_index.get(key, {}).get('episode_list', {}):
                elem_json['episode_list'] = matches_index[key]['episode_list'].copy()

        if btdigg_url in elem_json['url'] or ',' in elem_json['quality']:
            elem_json['quality'] = elem_json['quality'].replace(btdigg_label, '') + btdigg_label

    return matches


def CACHING_find_btdigg_list_all_NEWS_from_BTDIGG_(options=None):
    logger.info()

    monitor = xbmc.Monitor()
    if not PY3: from lib.alfaresolver import find_alternative_link
    else: from lib.alfaresolver_py3 import find_alternative_link
    from lib.AlfaChannelHelper import DictionaryAllChannel
    import ast

    item = Item()

    try:
        titles_search = ast.literal_eval(window.getProperty("alfa_cached_btdigg_movie"))
        window.setProperty("alfa_cached_btdigg_movie", "")
    except Exception as e:
        logger.error('ERROR en titles_search: %s / %s' % (window.getProperty("alfa_cached_btdigg_movie"), str(e)))
        titles_search = [{'urls': ['%sesp ' + channel_py], 'checks': ['Cast', 'Esp', 'Spanish', '%s' \
                                                           % channel_py.replace('4k', '')], 'contentType': 'movie', 'limit_search': 10}, 
                         {'urls': ['%sBluray Castellano'], 'checks': ['Cast', 'Esp', 'Spanish', '%s' \
                                                             % channel_py.replace('4k', '')], 'contentType': 'movie', 'limit_search': 3}, 
                         {'urls': ['%sHDTV 720p ' + channel_py], 'checks': ['Cap.'], 'contentType': 'tvshow', 'limit_search': 7}, 
                         {'urls': ['%sHDTV 720p'], 'checks': ['Cap.'], 'contentType': 'tvshow', 'limit_search': 3}, 
                         {'urls': ['%s ' + channel_py], 'checks': ['Cap.'], 'contentType': 'episode', 'limit_search': 5}, 
                         {'urls': ['%s Temporada #!'], 'checks': ['Cap.'], 'contentType': 'episode', 'limit_search': 5}]
    titles_search_save = copy.deepcopy(titles_search)

    btdigg_entries = 15
    disable_cache = True
    torrent_params = {}
    cached = {'movie': [], 'tvshow': [], 'episode': {}}
    language_alt = []
    matches = []
    matches_index = {}
    patron_sea = r'(?i)Cap.(\d+)\d{2}'
    patron_cap = r'(?i)Cap.\d+(\d{2})'
    patron_title = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[)'
    patron_title_b = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[|\s+-)'
    patron_year = r'\(?(\d{4})\)?'
    convert = ['.=', '-= ', ':=', '&=and', '  = ']
    title = '_'
    self = {}

    try:
        if False:   # Inhabilidado temporalemente
            channel = __import__('channels.%s' % channel_py, None,
                                 None, ["channels.%s" % channel_py])
            self = DictionaryAllChannel(channel.host, channel=channel_py, finds=channel.finds, debug=DEBUG)
            item.contentType = contentType = 'episode'
            item.c_type = 'series'

            for item.page in range(1, 3):
                matches, matches_index = (AH_find_btdigg_list_all_from_channel_py(self, item, matches=matches, matches_index=matches_index))
                if not matches: break
                if monitor.waitForAbort(10):
                    return

            for elem in matches:
                try:
                    elem['season'], elem['episode'] = scrapertools.find_single_match(elem['url'], r'(?i)\/temp\w*-?(\d+)\/cap\w*-?(\d+)')
                    elem['season'] = int(elem['season'])
                    del elem['episode']
                    elem['mediatype'] = 'season'
                    title = scrapertools.slugify(elem.get('title', ''), strict=False, convert=convert).strip().lower().replace(' ', '_')
                except Exception:
                    logger.error('Error en EPISODIO: %s' % elem['url'])

                cached[contentType][title] = elem

        for title_search in titles_search:
            contentType = title_search.get('contentType', 'movie')
            limit_search = title_search.get('limit_search', 1)
            if contentType == 'episode': continue
            if limit_search <= 0: continue

            quality_alt = '720p 1080p 2160p 4kwebrip 4k'
            if contentType == 'movie':
                quality_alt += ' bluray rip screener'
                language_alt = ['DUAL', 'CAST', 'LAT']
            else:
                quality_alt += ' HDTV'

            limit_pages = int((btdigg_entries * limit_search) / 10)
            limit_items_found = int(btdigg_entries * limit_search)
            item.contentType = contentType
            item.c_type = 'peliculas' if contentType == 'movie' else 'series'
            cached_str = str(cached[contentType])

            torrent_params = {
                              'find_alt_news': [title_search], 
                              'quality_alt': quality_alt, 
                              'language_alt': language_alt, 
                              'find_alt_link_next': 0, 
                              'limit_pages': limit_pages, 
                              'link_found_limit': limit_items_found, 
                              'domain_alt': None,
                              'extensive_search': False,
                              'search_order': title_search['search_order'] if 'search_order' in title_search else 2
                              }

            x = 0
            while x < limit_pages and not monitor.abortRequested():
                use_assistant = True
                try:
                    alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                    ASSISTANT_SERVERS = eval(window.getProperty("alfa_assistant_servers") or '127.0.0.1')
                    ASSISTANT_REMOTE = False if '127.0.0.1' in ASSISTANT_SERVERS[0] else True
                except:
                    alfa_gateways = []
                    ASSISTANT_SERVERS = ['127.0.0.1']
                    ASSISTANT_REMOTE = False
                if use_assistant and not ASSISTANT_REMOTE and len(ASSISTANT_SERVERS) < 2 and xbmc.Player().isPlaying() \
                                 and config.get_setting('btdigg_status', server='torrent', default=False):
                    if len(alfa_gateways) > 2:
                        use_assistant = False
                    else:
                        window.setProperty("alfa_cached_btdigg_episode", 'CANCEL')
                        raise Exception("CANCEL")
                
                torrent_params = find_alternative_link(item, torrent_params=torrent_params, cache=disable_cache, use_assistant=use_assistant)

                if torrent_params.get('find_alt_link_code', '') in ['200']:
                    if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                    if not torrent_params.get('find_alt_link_next'): x = 999999
                    if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                        limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                else:
                    x = 999999
                x += 1

                for elem in torrent_params.get('find_alt_link_result', []):
                    #logger.error(elem)
                    if elem.get('url', '') in cached_str: continue

                    elem['size'] = elem.get('size', '').replace('\xa0', ' ')

                    if contentType == 'tvshow':
                        title = elem.get('title', '').replace(btdigg_label_B, '')
                        if scrapertools.find_single_match(title, patron_title).strip():
                            title = scrapertools.find_single_match(title, patron_title).strip()
                        elif scrapertools.find_single_match(title, patron_title_b).strip():
                            title = scrapertools.find_single_match(title, patron_title_b).strip()
                        else:
                            if DEBUG: logger.debug('Error en PATRON: %s / %s' % (elem.get('title', '').replace(btdigg_label_B, ''), patron_title))
                            continue
                        title = title.replace('- ', '').replace('.', ' ')
                        if title in str(cached[contentType]): continue

                    cached[contentType].append(elem.copy())

                    if len(cached[contentType])> limit_items_found: 
                        x = 999999
                        break

                if monitor.waitForAbort(5):
                    return

            window.setProperty("alfa_cached_btdigg_%s" % contentType, str(cached[contentType]))
            if monitor.waitForAbort(1 * 60):
                return

        contentType = 'episode'
        if not cached[contentType] and not monitor.abortRequested():
            for t, elem_show in enumerate(cached['tvshow']):
                elem_json = {}
                alias = {}
                alias_in = alias_out = ''
                #logger.error(elem_show)

                try:
                    if elem_show.get('season_search', ''): elem_json['season_search'] = elem_show['season_search']
                    elem_json['title'] = elem_show.get('title', '').replace(btdigg_label_B, '')
                    elem_json['year'] = scrapertools.find_single_match(re.sub(r'(?i)cap\.\d+', '', elem_json['title']), '.+?'+patron_year) or '-'
                    if elem_json['year'] in ['720', '1080', '2160']: elem_json['year'] = '-'
                    if scrapertools.find_single_match(elem_json['title'], patron_title).strip():
                        elem_json['title'] = scrapertools.find_single_match(elem_json['title'], patron_title).strip()
                    elif scrapertools.find_single_match(elem_json['title'], patron_title_b).strip():
                        elem_json['title'] = scrapertools.find_single_match(elem_json['title'], patron_title_b).strip()
                    else:
                        if DEBUG: logger.debug('Error en PATRON: %s / %s' % (elem_show.get('title', '').replace(btdigg_label_B, ''), patron_title))
                        continue
                    elem_json['title'] = elem_json['title'].replace('- ', '').replace('.', ' ')
                    elem_json['title'] = scrapertools.htmlclean(elem_json['title']).strip()
                    elem_json['title'] = elem_json['title'].replace("á", "a").replace("é", "e").replace("í", "i")\
                                                           .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                                                           .replace("ï¿½", "ñ").replace("Ã±", "ñ").replace(' - ', ' ')
                    elem_json['title'] = scrapertools.decode_utf8_error(elem_json['title']).strip()
                    if "en espa" in elem_json['title']: elem_json['title'] = elem_json['title'][:-11]
                    title = scrapertools.slugify(elem_json.get('title', ''), strict=False, convert=convert).strip().lower().replace(' ', '_')
                    elem_json['title'] = elem_json['title'].replace(':', '')
                    if title in cached[contentType]: continue

                    elem_json['season'] = season_low = int(scrapertools.find_single_match(elem_show['title'], patron_sea))
                    elem_json['quality'] = ''
                    elem_json['language'] = elem_show.get('language', [])
                    elem_json['mediatype'] = 'season'
                    elem_json['episode_list'] = {}
                    elem_json['url'] = '%sserie_btdig/%s%s' % (btdigg_url, elem_json['language'], 
                                                               elem_json['title'].replace(' ', '-').lower().strip())
                    if not elem_json.get('title', '') or not elem_json.get('url', ''): continue

                    item = Item()
                    item.c_type = 'series'
                    item.contentType = 'tvshow'
                    item.contentSerieName = item.title = elem_json['title'].capitalize()
                    item.season_search = elem_json.get('season_search', '') or elem_json['title']
                    aliases = titles_search[-1].get('aliases', {})
                    if title in aliases and '[' in aliases[title]:
                        item.season_search = elem_json['season_search'] = aliases[title]
                    if '#' in item.season_search:
                        alias = search_btdigg_free_format_parse({}, item.clone(), titles_search=BTDIGG_SEARCH)[0].get('aliases', {})
                        if alias:
                            alias_in = list(alias.keys())[0].replace('_', ' ').capitalize()
                            alias_out = list(alias.values())[0].replace('_', ' ').capitalize()
                    item.url = elem_json['url']
                    item.infoLabels['year'] = elem_json.get('year', '-')
                    config.set_setting('tmdb_cache_read', False)
                    tmdb.set_infoLabels_item(item, True, idioma_busqueda='es')
                    if item.infoLabels['tmdb_id']: tmdb.set_infoLabels_item(item, True, idioma_busqueda='es')
                    if item.contentTitle and item.contentTitle.lower() != item.contentSerieName.lower():
                        item.contentTitle = item.contentTitle.replace('- ', '').replace(':', '')
                        item.contentTitle = scrapertools.htmlclean(item.contentTitle).strip()
                        item.contentTitle = item.contentTitle.replace("á", "a").replace("é", "e").replace("í", "i")\
                                                             .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                                                             .replace("ï¿½", "ñ").replace("Ã±", "ñ").replace(' - ', ' ')
                        item.contentTitle = scrapertools.decode_utf8_error(item.contentTitle).strip()
                        if "en espa" in item.contentTitle: item.contentTitle = item.contentTitle[:-11]
                    if item.infoLabels['tmdb_id']: 
                        if item.contentTitle.lower() != item.contentSerieName.lower(): item.infoLabels['title_alt'] = item.contentTitle
                        item.contentType = 'season'
                        item.infoLabels['number_of_seasons'] = int(scrapertools.find_single_match(item.infoLabels.\
                                                                   get('last_series_episode_to_air', '%sx1' \
                                                                   % item.infoLabels.get('number_of_seasons', elem_json['season'])), r'(\d+)x\d+'))
                        item.contentSeason = elem_json['season'] = item.infoLabels['number_of_seasons']
                        tmdb.set_infoLabels_item(item, True, idioma_busqueda='es')
                    config.set_setting('tmdb_cache_read', True)
                    seasons = elem_json['season']
                    if seasons != season_low: seasons = '%s-%s' % (season_low, seasons)

                    item.infoLabels['temporada_num_episodios'] = item.infoLabels['temporada_num_episodios'] or 10
                    if not isinstance(item.infoLabels['last_episode_to_air'], int):
                        item.infoLabels['last_episode_to_air'] = item.infoLabels['temporada_num_episodios']
                    if scrapertools.find_single_match(item.infoLabels.get('last_series_episode_to_air', ''), r'\d+x\d+'):
                        s, e = item.infoLabels['last_series_episode_to_air'].split('x')
                        if int(s) == item.infoLabels['season']:
                            if int(e) > item.infoLabels.get('last_episode_to_air', 0):
                                item.infoLabels['last_episode_to_air'] = int(e)
                    episodes = item.infoLabels['last_episode_to_air']
                    elem_json['episode_limits'] = 'N/A'
                    if item.infoLabels['tmdb_id']: 
                        elem_json['tmdb_id'] = item.infoLabels['tmdb_id']
                        elem_json['episode_limits'] = '%s/%s' % (episodes, item.infoLabels['temporada_num_episodios'])
                    
                    cached[contentType][title] = elem_json.copy()
                    titles_search = search_btdigg_free_format_parse(self, item.clone(), titles_search_save, contentType)

                    for title_search in titles_search:
                        limit_search = title_search.get('limit_search', 1)
                        if contentType != title_search.get('contentType', ''): continue
                        if limit_search <= 0: continue

                        for x_url, url in enumerate(title_search['urls']):
                            if 'Temporada' in url: 
                                title_search['urls'][x_url] = url.replace('#!', str(season_low))
                                #logger.debug('Temporada: %s / %s' % (seasons, title_search['urls'][x_url]))
                        
                        quality_alt = 'HDTV 720p 1080p 2160p 4kwebrip 4k'
                        language_alt = ['DUAL', 'CAST', 'LAT']

                        limit_items_found = int(item.infoLabels['temporada_num_episodios'] * limit_search) or int(episodes * limit_search)
                        limit_pages = int(((episodes * limit_search) + 9) / 10)
                        logger.info('## Serie: %s/%s - [%s/%s]; season: %s; episodes: %s/%s; limit_items_found: %s; limit_pages: %s' \
                                     % (elem_json['title'], item.infoLabels['title_alt'], t+1, len(cached['tvshow']), seasons, 
                                        episodes, item.infoLabels['temporada_num_episodios'], limit_items_found, limit_pages), force=True)

                        torrent_params = {
                                          'title_prefix': [title_search], 
                                          'quality_alt': quality_alt, 
                                          'language_alt': language_alt, 
                                          'find_alt_link_season': seasons, 
                                          'find_alt_link_next': 0, 
                                          'limit_pages': limit_pages, 
                                          'link_found_limit': limit_items_found, 
                                          'domain_alt': None,
                                          'extensive_search': False,
                                          'search_order': title_search['search_order'] if 'search_order' in title_search else 2
                                          }

                        x = y = 0
                        while x < limit_pages and not monitor.abortRequested():
                            if window.getProperty("alfa_cached_btdigg_episode") == 'TIMEOUT_CANCEL':
                                raise Exception("CANCEL")
                            use_assistant = True
                            other_season = False
                            try:
                                alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                                ASSISTANT_SERVERS = eval(window.getProperty("alfa_assistant_servers") or '127.0.0.1')
                                ASSISTANT_REMOTE = False if '127.0.0.1' in ASSISTANT_SERVERS[0] else True
                            except:
                                alfa_gateways = []
                                ASSISTANT_SERVERS = ['127.0.0.1']
                                ASSISTANT_REMOTE = False
                            if use_assistant and not ASSISTANT_REMOTE and len(ASSISTANT_SERVERS) < 2 and xbmc.Player().isPlaying() \
                                             and config.get_setting('btdigg_status', server='torrent', default=False):
                                if len(alfa_gateways) > 2:
                                    use_assistant = False
                                else:
                                    window.setProperty("alfa_cached_btdigg_episode", 'CANCEL')
                                    raise Exception("CANCEL")

                            torrent_params = find_alternative_link(item, torrent_params=torrent_params, 
                                                                   cache=disable_cache, use_assistant=use_assistant)

                            if torrent_params.get('find_alt_link_code', '') in ['200']:
                                if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                                if not torrent_params.get('find_alt_link_next'): x = 999999
                                if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                                    limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                            else:
                                x = 999999
                            x += 1

                            for elem in torrent_params.get('find_alt_link_result', []):
                                #logger.error(elem)
                                cached_str = str(cached[contentType][title])
                                if elem.get('url', '') in cached_str:
                                    if DEBUG: logger.debug('Error en URL: %s / %s' % (elem.get('url', ''), cached_str))
                                    continue
                                elem_episode = {}

                                try:
                                    elem_episode['title'] = elem.get('title', '').replace(btdigg_label_B, '')
                                    if elem.get('season_search', ''): elem_episode['season_search'] = elem['season_search']
                                    if elem_json.get('season_search', ''): elem_episode['season_search'] = elem_json['season_search']
                                    elem_episode['season'] = int(scrapertools.find_single_match(elem['title'], patron_sea))
                                    if elem_episode['season'] != elem_json['season'] and elem_episode['season'] < season_low: 
                                        other_season = True
                                        if DEBUG: logger.debug('Error en SEASON: %s / %s' % (elem_episode['season'], elem_json['season']))
                                        continue
                                    elem_episode['episode'] = int(scrapertools.find_single_match(elem['title'], patron_cap))
                                    if elem_episode['episode'] > item.infoLabels['temporada_num_episodios']:  continue
                                    sxe = '%sx%s' % (elem_episode['season'], str(elem_episode['episode']).zfill(2))
                                    if scrapertools.find_single_match(elem_episode['title'], patron_title).strip():
                                        elem_episode['title'] = scrapertools.find_single_match(elem_episode['title'], patron_title).strip()
                                    elif scrapertools.find_single_match(elem_episode['title'], patron_title_b).strip():
                                        elem_episode['title'] = scrapertools.find_single_match(elem_episode['title'], patron_title_b).strip()
                                    else:
                                        if DEBUG: logger.debug('Error en PATRON: %s / %s' % (elem_episode['title'], patron_title))
                                        continue
                                    elem_episode['title'] = elem_episode['title'].replace('- ', '').replace('.', ' ')
                                    elem_episode['title'] = scrapertools.htmlclean(elem_episode['title']).strip()
                                    if elem_episode['title'].lower() != elem_json['title'].lower(): 
                                        if DEBUG: logger.debug('Error en TÍTULO: %s / %s' % (elem_episode['title'], elem_json['title']))
                                        continue
                                    elem_episode['url'] = elem_json['url']
                                    elem_episode['mediatype'] = 'episode'
                                    if item.infoLabels['tmdb_id']: elem_episode['tmdb_id'] = item.infoLabels['tmdb_id']

                                    elem_header = elem_episode.copy()
                                    elem_episode['url'] = elem.get('url', '')
                                    elem_episode['quality'] = elem.get('quality', '').replace('HDTV 720p', 'HDTV-720p')
                                    elem_episode['server'] = 'torrent'
                                    elem_episode['torrent_info'] = elem.get('size', '').replace(btdigg_label_B, '').replace('GB', 'G·B')\
                                                                                       .replace('Gb', 'G·b').replace('MB', 'M·B')\
                                                                                       .replace('Mb', 'M·b').replace('.', ',')\
                                                                                       .replace('\xa0', ' ')
                                    elem_episode['torrent_info'] += ' (%s)' % (alias_in or elem_episode['title'])
                                    elem_episode['size'] = elem.get('size', '').replace(btdigg_label_B, '')\
                                                                               .replace('\xa0', ' ')\
                                                                               .replace('[COLOR magenta][B]RAR-[/B][/COLOR]', '')
                                    if elem.get('password', {}):
                                        elem_episode['password'] = elem['password']
                                    
                                    y += 1
                                except Exception:
                                    logger.error('Error en EPISODIO: %s' % elem)
                                    logger.error(traceback.format_exc())
                                    continue

                                if not cached[contentType][title]['episode_list'].get(sxe, {}):
                                    cached[contentType][title]['episode_list'][sxe] = elem_header.copy()
                                    cached[contentType][title]['episode_list'][sxe]['matches_cached'] = []

                                cached[contentType][title]['episode_list'][sxe]['matches_cached'] += [elem_episode.copy()]
                                
                                if y > limit_items_found: 
                                    x = 999999
                                    break

                            if other_season and limit_pages < limit_search + 2: 
                                limit_pages += 1
                            if monitor.waitForAbort(1):
                                return
                        if monitor.waitForAbort(5):
                            return

                        if len(cached[contentType][title]['episode_list']) >= episodes:
                            break

                except Exception as e:
                    if window.getProperty("alfa_cached_btdigg_episode") == 'TIMEOUT_CANCEL':
                        logger.error('##### %s' % window.getProperty("alfa_cached_btdigg_episode"))
                        window.setProperty("alfa_cached_btdigg_episode", 'CANCEL')
                        return
                    logger.error(traceback.format_exc())

                logger.debug('Serie: %s[%s]; Episodes: [%s/%s] / %s' % (elem_json['title'], seasons, episodes, 
                                                                len(cached[contentType][title].get('episode_list', {})), 
                                                                sorted(cached[contentType][title].get('episode_list', {}).keys())))
                if not cached[contentType][title].get('episode_list', {}):
                    del cached[contentType][title]

        if not window.getProperty("alfa_cached_btdigg_episode"):
            window.setProperty("alfa_cached_btdigg_episode", jsontools.dump(cached['episode'], **kwargs_json))
        if not cached['episode']:
            window.setProperty("alfa_cached_btdigg_episode", 'EXIT')

    except Exception as e:
        logger.error(traceback.format_exc())
        window.setProperty("alfa_cached_btdigg_episode", 'CANCEL')


def AH_find_btdigg_seasons(self, item, matches=[], domain_alt=channel_py, **AHkwargs):
    logger.info()
    global channel_py_episode_list, DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    ASSISTANT_REMOTE = True if config.get_setting("assistant_mode").lower() == 'otro' else False

    controls = self.finds.get('controls', {})
    btdigg_search = controls.get('btdigg_search', True)
    url = AHkwargs.pop('url', item.url)
    contentSeason = AHkwargs.pop('btdigg_contentSeason', controls.get('btdigg_contentSeason', 0))
    disable_cache = True if (not 'btdigg_cache' in AHkwargs  and not 'btdigg_cache' in controls) else \
                    not AHkwargs.pop('btdigg_cache', controls.get('btdigg_cache', True))
    quality_control = AHkwargs.pop('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    canonical = AHkwargs.pop('canonical', self.canonical)
    matches = sorted(matches, key=lambda it: int(it.get('season', 0))) if matches else []
    season_high = [elem_json['season'] for elem_json in matches] if matches else [0]
    if item.btdigg and item.matches_cached: season_high = [elem_json['season'] for elem_json in item.matches_cached if elem_json.get('season')]
    channel_py_strict = False
    contentType = 'season'
    BTDIGG_SEARCH_STAT = False

    if BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
        found = AH_find_btdigg_ENTRY_from_BTDIGG(self, title=item.contentSerieName, contentType='episode', matches=matches, 
                                                 item=item.clone(), reset=False, **AHkwargs)

        if not found and item.episode_list:
            found = [{item.contentSerieName: {'url': item.url, 'episode_list': item.episode_list, 'quality': item.quality, 
                                              'title': item.contentSerieName, 'season': item.contentSeason, 'mediatype': 'season'}}]
        for season_btdigg in found:
            season_btdigg = list(season_btdigg.values())[0]
            if season_btdigg.get('tmdb_id', item.infoLabels['tmdb_id']) == item.infoLabels['tmdb_id']:
                if not season_btdigg.get('tmdb_id'): AH_reset_alias_item(item, season_btdigg.get('title'))
                channel_py_strict = True
                for sxe in list(season_btdigg.get('episode_list', {}).keys()):
                    season_num = int(scrapertools.find_single_match(sxe, r'(\d+)x\d+') or 1)
                    if season_num > season_high[-1]:
                        season_high += [season_num]
                        season_btdigg['season'] = season_high[-1]
                        if not matches or season_btdigg['season'] > matches[-1].get('season', 0):
                            season_btdigg_alt = copy.deepcopy(season_btdigg)
                            season_btdigg_alt.pop('episode_list', {})
                            if 'episode_limits' in season_btdigg_alt: del season_btdigg_alt['episode_limits']
                            season_btdigg_alt['quality'] = item.quality
                            matches.append(season_btdigg_alt.copy())

    logger.debug('contentSeason: %s; season_high: %s; number_of_seasons: %s' \
                  % (contentSeason, season_high, item.infoLabels['number_of_seasons']))
    if (item.infoLabels.get('number_of_seasons', 0) in season_high and contentSeason == 0) \
                         or (contentSeason > 0 and contentSeason in season_high \
                         and season_high[-1] >= item.infoLabels.get('number_of_seasons', item.contentSeason or 99)):
        return matches

    if not btdigg_search:
        return matches

    try:
        if canonical.get('global_search_cancelled', False) or (config.GLOBAL_SEARCH_CANCELLED \
                                                           and canonical.get('global_search_active', False)):
            logger.info('## Búsqueda global cancelada: %s: %s' % (item.channel, item.title), force=True)
            return itemlist

        format_tmdb_id(item)

        if not PY3: from lib.alfaresolver import find_alternative_link
        else: from lib.alfaresolver_py3 import find_alternative_link

        season = item.infoLabels['number_of_seasons'] or 1
        seasons = season
        season_low = contentSeason or season_high[-1] + 1 or season
        if season != season_low:
            seasons = '%s-%s' % (season_low, season)
        elif btdigg_url in item.url and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
            seasons = '1-%s' % season
            season_low = 1
        patron_sea = r'(?i)Cap.(\d+)\d{2}'

        quality_alt = ''
        language_alt = []
        if not item.btdigg:
            quality_alt = '720p 1080p 2160p 4kwebrip 4k'
            if not quality_control:
                quality_alt +=  ' HDTV'
            elif '720' not in item.quality:
                quality_alt =  'HDTV'

            language_alt = ['DUAL', 'CAST'] if 'CAST' in item.language else ['DUAL', 'LAT'] if 'LAT' in item.language else ['DUAL', 'CAST', 'LAT']

        titles_search = []
        titles_search_finds = []
        titles_search_finds_low = []
        if self and self.finds.get('titles_search', {}).get('seasons') \
                and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
            titles_search_finds = self.finds['titles_search']['seasons']
            titles_search_finds_low = self.finds.get('titles_search_', {}).get('seasons_low', [])
        if self and self.finds.get('titles_search', {}).get('btdigg_search_seasons') \
                and (BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow):
            titles_search_finds = self.finds['titles_search']['btdigg_search_seasons']
        if season and season == season_low:
            if titles_search_finds:
                titles_search.extend(titles_search_finds[0])
            elif BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow:
                titles_search = search_btdigg_free_format_parse(self, item, BTDIGG_SEARCH, contentType, **AHkwargs)
                BTDIGG_SEARCH_STAT = True
            else:
                titles_search.extend([{'urls': ['%s HDTV ' + domain_alt], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8}])
            if not channel_py_strict:
                if titles_search_finds and len(titles_search_finds) > 1:
                    titles_search.extend(titles_search_finds[1:])
                elif not titles_search_finds and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
                    titles_search.extend([{'urls': ['%s HDTV'], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8},
                                          {'urls': ['%s Temporada ' + str(season)], 'checks': ['Cap.'], 
                                           'contentType': contentType, 'limit_search': 8}])
        if season and season != season_low:
            if titles_search_finds_low:
                titles_search.extend(titles_search_finds_low)
            elif BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
                titles_search.extend([{'urls': ['%s HDTV'], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8}])

        if not BTDIGG_SEARCH_STAT:
            titles_search = search_btdigg_free_format_parse(self, item, titles_search, contentType, **AHkwargs)
        for title_search in titles_search:
            if title_search.get('contentType', contentType) != contentType: continue

            limit_search = title_search.get('limit_search', 8)
            limit_pages = limit_search if domain_alt in str(title_search['urls']) else limit_search / 2
            limit_pages_min = (limit_search / 2) if domain_alt in str(title_search['urls']) else 1
            limit_items_found = 10 * 10

            torrent_params = {
                              'title_prefix': [title_search], 
                              'quality_alt': title_search.get('quality_alt', '') or quality_alt, 
                              'language_alt': title_search.get('language_alt', []) or language_alt, 
                              'find_alt_link_season': seasons, 
                              'find_alt_link_next': 0, 
                              'limit_pages': limit_pages, 
                              'link_found_limit': limit_items_found, 
                              'domain_alt': None,
                              'extensive_search': False if contentSeason > 0 else False,
                              'search_order': title_search['search_order'] if 'search_order' in title_search else 0
                              }

            x = 0
            while x < limit_pages:
                use_assistant = True
                try:
                    alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                except:
                    alfa_gateways = []
                if (xbmc.Player().isPlaying() or ASSISTANT_REMOTE) and len(alfa_gateways) > 1:
                    use_assistant = False
                torrent_params = find_alternative_link(item, torrent_params=torrent_params, cache=disable_cache, use_assistant=use_assistant)

                if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                if not torrent_params.get('find_alt_link_result') and torrent_params.get('find_alt_link_next', 0) >= limit_pages_min: x = 999999
                if not torrent_params.get('find_alt_link_next'): x = 999999
                if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                    limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                x += 1

                for y, elem in enumerate(torrent_params['find_alt_link_result']):
                    elem_json = {}
                    #logger.error(torrent_params['find_alt_link_result'][y])

                    try:
                        if not scrapertools.find_single_match(elem.get('title', ''), patron_sea): continue
                        elem_json['season'] = int(scrapertools.find_single_match(elem.get('title', ''), patron_sea))
                        if elem_json['season'] in season_high: continue
                        if item.infoLabels['number_of_seasons'] \
                                            and elem_json['season'] > int(item.infoLabels['number_of_seasons']): continue
                        season_high += [elem_json['season']]

                        if elem.get('season_search', ''): elem_json['season_search'] = elem['season_search']
                        if '#' in item.season_search: elem_json['season_search'] = item.season_search
                        
                        if item.btdigg:
                            elem_json['url'] = item.url
                        else:
                            elem_json['url'] = '%sseries_btdig/%s%s' % (config.BTDIGG_URL, elem.get('language', []) or item.language \
                                                if item.language else '', item.contentSerieName.lower().replace(' ', '-'))
                        elem_json['magnet'] = elem.get('url', '')
                        elem_json['quality'] = '%s%s' % (elem.get('quality', '').upper().replace('P', 'p')\
                                                        .replace('HDTV 720p', 'HDTV-720p'), btdigg_label)
                        if item.quality:
                            if elem_json['quality'].replace(btdigg_label, '') not in item.quality:
                                elem_json['quality'] = '%s, %s' % (item.quality.replace(btdigg_label, ''), elem_json['quality'])
                            else:
                                elem_json['quality'] = '%s%s' % (item.quality.replace(btdigg_label, ''), btdigg_label)
                        elem_json['language'] = elem.get('language', []) or item.language
                        elem_json['size'] = elem.get('size', '')
                        
                        elem_json['title'] = ''

                        matches.append(elem_json.copy())
                        if elem_json['season'] == season_low and elem_json['season'] == season:
                            x = 888888
                            break

                    except Exception:
                        logger.error(traceback.format_exc())
                        continue

                if isinstance(seasons, int) and seasons in season_high:
                    x = 888888
                    break
            
            if x == 888888: break

        matches = sorted(matches, key=lambda it: int(it.get('season', 0)))

    except Exception:
        logger.error(traceback.format_exc())

    return matches


def AH_find_btdigg_episodes(self, item, matches=[], domain_alt=channel_py, **AHkwargs):
    logger.info()
    global channel_py_episode_list, DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    ASSISTANT_REMOTE = True if config.get_setting("assistant_mode", default="").lower() == 'otro' else False

    controls = self.finds.get('controls', {})
    btdigg_search = controls.get('btdigg_search', True)
    contentSeason = AHkwargs.pop('btdigg_contentSeason', controls.get('btdigg_contentSeason', 0))
    disable_cache = True if str(item.infoLabels['number_of_seasons']) == '1' else \
                    not AHkwargs.pop('btdigg_cache', controls.get('btdigg_cache', True))
    disable_cache = True if BTDIGG_URL_SEARCH in item.url_tvshow else disable_cache
    quality_control = AHkwargs.pop('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    canonical = AHkwargs.pop('canonical', self.canonical)
    matches_len = len(matches)
    channel_py_strict = False
    found = False
    contentType = 'episode'
    BTDIGG_SEARCH_STAT = False

    season = seasons = item.infoLabels['season'] or 1
    episode_max = item.infoLabels['temporada_num_episodios'] or item.infoLabels['number_of_episodes'] or 1
    last_episode_to_air = item.infoLabels.get('last_episode_to_air', 0) or episode_max
    e = 0
    le = item.infoLabels.get('last_episode_to_air', 0)
    if scrapertools.find_single_match(item.infoLabels.get('last_series_episode_to_air', ''), r'\d+x\d+'):
        s, e = item.infoLabels['last_series_episode_to_air'].split('x')
        if int(s) == item.infoLabels['season']:
            if int(e) > item.infoLabels.get('last_episode_to_air', 0):
                last_episode_to_air = item.infoLabels['last_episode_to_air'] = int(e)
        else:
            e = item.infoLabels['last_series_episode_to_air']

    if BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
        found_list = AH_find_btdigg_ENTRY_from_BTDIGG(self, title=item.contentSerieName, contentType=contentType, matches=matches, 
                                                      item=item.clone(), reset=False, **AHkwargs)

        if not found_list and item.episode_list:
            found_list = [{item.contentSerieName: {'url': item.url, 'episode_list': item.episode_list, 'quality': item.quality, 
                                                   'title': item.contentSerieName, 'season': item.contentSeason, 'mediatype': 'season'}}]
        if found_list:
            for found_item in found_list:
                found_item = list(found_item.values())[0]
                if not found_item: continue
                if found_item.get('episode_list') and found_item.get('tmdb_id', item.infoLabels['tmdb_id']) == item.infoLabels['tmdb_id']:
                    found_item['tmdb_id'] = item.infoLabels['tmdb_id']
                    for epi, episodio in found_item.get('episode_list', {}).items():
                        if episodio.get('season', 0) == season:
                            for matches_cached in episodio.get('matches_cached', []):
                                if quality_control:
                                    if 'HDTV' == item.quality.replace(btdigg_label, ''):
                                        if matches_cached.get('quality', '') != 'HDTV':
                                            continue
                                    elif matches_cached.get('quality', '') == 'HDTV':
                                        continue
                                if not matches_cached.get('url'): continue
                                found = True
                                if matches_cached['url'] in str(matches): continue
                                matches_cached['quality'] = '%s%s' % (matches_cached['quality'], btdigg_label)
                                if not matches_cached.get('language', []): matches_cached['language'] = item.language or ['CAST']
                                matches_cached['matches_cached'] = []
                                matches.append(matches_cached.copy())
                                channel_py_strict = True

        if found:
            matches = sorted(matches, key=lambda it: int(it.get('episode', 0))) if matches else []
            return matches
    
    matches = sorted(matches, key=lambda it: int(it.get('episode', 0))) if matches else []
    epis_index = {}
    l_p_missing = []

    for x, epi in enumerate(matches):
        json_inter = {}
        if not epi.get('episode'): continue
        if epi['episode'] > last_episode_to_air: last_episode_to_air = epi['episode']
        epi['quality'] = epi.get('quality', 'HDTV').replace('*', '') or 'HDTV'
        if not epis_index.get(epi['episode']):
            epis_index[epi['episode']] = [[epi['episode'], x, epi['quality'].lower()]]
        else:
            epis_index[epi['episode']] += [[epi['episode'], x, epi['quality'].lower()]]

    for epi_avl in range(1, last_episode_to_air + 1):
        sxe = '%sx%s' % (item.infoLabels['number_of_seasons'], str(epi_avl).zfill(2))
        if sxe not in item.library_playcounts and epi_avl not in epis_index:
            l_p_missing += [sxe]

    logger.info('[LE: %sx%s-%s / EPI: %s / MAX: %s / MISSING: %s / MATCHES: %s]' % (item.infoLabels['season'], 
                                                                                    le, e, 
                                                                                    last_episode_to_air, episode_max, 
                                                                                    l_p_missing, epis_index))

    if item.infoLabels['last_air_date'] and matches and (item.library_playcounts or item.video_path) \
                                        and item.from_action not in ['update_tvshow'] and not l_p_missing:
        if not item.sub_action or (item.sub_action and item.sub_action in ['auto']):
            try:
                res, episode_list = check_marks_in_videolibray(item, video_list_init=True)
                if res:
                    for x, epi in enumerate(matches):
                        season_episode = '%sx%s.strm' % (str(epi.get('season', 0)), str(epi.get('episode', 0)).zfill(2))
                        if not season_episode in str(episode_list):
                            if DEBUG: logger.debug('NUEVO EPI: %s' % season_episode)
                            break
                    else:
                        if DEBUG: logger.debug('NO NUEVOS EPIs')

                        try:
                            last_air_date = datetime.datetime.strptime(item.infoLabels['last_air_date'], "%Y-%m-%d")
                        except TypeError:
                            last_air_date = datetime.datetime(*(time.strptime(item.infoLabels['last_air_date'], "%Y-%m-%d")[0:6]))

                        now = datetime.datetime.now()
                        period = datetime.datetime.now() - last_air_date
                        days = period.days
                        seconds = period.seconds
                        if days < 0: days = 0; seconds = 0
                        if seconds < 0: seconds = 0
                        elapsed = (days*60*60*24) + seconds
                        expiration = 10*60*60*24
                        if elapsed > expiration:
                            if DEBUG: logger.debug('EPIs ANTIGUOs: %s' % item.infoLabels['last_air_date'])
                            
                            matches = AH_find_btdigg_matches(item, matches, **AHkwargs)
                            matches = sorted(matches, key=lambda it: (it.get('episode', 0), self.convert_size(it.get('size', 0)))) \
                                                                      if matches else []
                            return matches
                
                        if DEBUG: logger.debug('EPIs MODERNOS: %s' % item.infoLabels['last_air_date'])

            except Exception:
                logger.error(traceback.format_exc())

    if not btdigg_search:
        return matches

    try:
        if canonical.get('global_search_cancelled', False) or (config.GLOBAL_SEARCH_CANCELLED \
                                                           and canonical.get('global_search_active', False)):
            logger.info('## Búsqueda global cancelada: %s: %s' % (item.channel, item.title), force=True)
            return itemlist

        format_tmdb_id(item)

        if not PY3: from lib.alfaresolver import find_alternative_link
        else: from lib.alfaresolver_py3 import find_alternative_link

        if BTDIGG_URL_SEARCH in item.url_tvshow and not item.library_playcounts and (epis_index.get(last_episode_to_air, []) \
                                                or item.contentSeason > item.infoLabels.get('number_of_seasons', 99)):
            return matches
        if not channel_py_strict and not l_p_missing:
            sxe_max = '%sx%s' % (item.infoLabels['number_of_seasons'], str(episode_max).zfill(2))
            if sxe_max in item.library_playcounts:
                return matches

        quality_alt = ''
        language_alt = []
        if not item.btdigg:
            quality_alt = '720p 1080p 2160p 4kwebrip 4k'
            if not quality_control:
                quality_alt +=  ' HDTV'
            elif '720' not in item.quality:
                quality_alt =  'HDTV'

            language_alt = ['DUAL', 'CAST'] if 'CAST' in item.language else ['DUAL', 'LAT'] if 'LAT' in item.language else ['DUAL', 'CAST', 'LAT']

        titles_search = []
        titles_search_finds = []
        if self and self.finds.get('titles_search', {}).get('episodes')\
                and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
            titles_search_finds = self.finds['titles_search']['episodes']
        if self and self.finds.get('titles_search', {}).get('btdigg_search_episodes') \
                and (BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow):
            titles_search_finds = self.finds['titles_search']['btdigg_search_episodes']
        if titles_search_finds:
            titles_search.extend(titles_search_finds[0])
        elif BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow:
            titles_search = search_btdigg_free_format_parse(self, item, BTDIGG_SEARCH, contentType, **AHkwargs)
            BTDIGG_SEARCH_STAT = True
        elif quality_alt ==  'HDTV':
            titles_search.extend([{'urls': ['%s HDTV ' + domain_alt], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8}])
        else:
            titles_search.extend([{'urls': ['%s HDTV ' + domain_alt, '%s 4K ' + domain_alt], 'checks': ['Cap.'], 
                                   'contentType': contentType, 'limit_search': 8}])
        if not channel_py_strict:
            if titles_search_finds and len(titles_search_finds) > 1:
                titles_search.extend(titles_search_finds[1:])
            elif not titles_search_finds and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
                titles_search.extend([{'urls': ['%s HDTV'], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8},
                                      {'urls': ['%s Temporada ' + str(season)], 'checks': ['Cap.'], 'contentType': contentType, 'limit_search': 8}])

        if not BTDIGG_SEARCH_STAT:
            titles_search = search_btdigg_free_format_parse(self, item, titles_search, contentType, **AHkwargs)
        for title_search in titles_search:
            if title_search.get('contentType', contentType) != contentType: continue

            limit_search = title_search.get('limit_search', 8)
            limit_pages = limit_search if domain_alt in str(title_search['urls']) else limit_search / 2
            limit_pages_min = (limit_search / 2) if domain_alt in str(title_search['urls']) else 1
            limit_items_found = 10 * 10
            patron_sea = r'(?i)Cap.(\d+)\d{2}'
            patron_cap = r'(?i)Cap.\d+(\d{2})'
            patron_title = r'(?i)(.*?(?:\(\d{4}\))?)\s*(?:-*\s*temp|\[)'

            torrent_params = {
                              'title_prefix': [title_search], 
                              'quality_alt': title_search.get('quality_alt', '') or quality_alt, 
                              'language_alt': title_search.get('language_alt', []) or language_alt, 
                              'find_alt_link_season': seasons, 
                              'find_alt_link_next': 0, 
                              'limit_pages': limit_pages, 
                              'link_found_limit': limit_items_found, 
                              'domain_alt': None,
                              'extensive_search': False if contentSeason > 0 else False,
                              'search_order': title_search['search_order'] if 'search_order' in title_search else 0
                              }

            x = 0
            while x < limit_pages:
                use_assistant = True
                try:
                    alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                except:
                    alfa_gateways = []
                if (xbmc.Player().isPlaying() or ASSISTANT_REMOTE) and len(alfa_gateways) > 1:
                    use_assistant = False
                torrent_params = find_alternative_link(item, torrent_params=torrent_params, cache=disable_cache, use_assistant=use_assistant)

                if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                if not torrent_params.get('find_alt_link_result') and torrent_params.get('find_alt_link_next', 0) >= limit_pages_min: x = 999999
                if not torrent_params.get('find_alt_link_next'): x = 999999
                if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                    limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                x += 1

                for y, elem in enumerate(torrent_params['find_alt_link_result']):
                    elem_json = {}
                    alias = {}
                    alias_in = alias_out = ''
                    #logger.error(torrent_params['find_alt_link_result'][y])

                    try:
                        if '#' in elem.get('season_search', ''):
                            alias = search_btdigg_free_format_parse({}, item.clone(btdigg=elem['season_search']), 
                                                                    titles_search=BTDIGG_SEARCH)[0].get('aliases', {})
                            if alias:
                                alias_in = list(alias.keys())[0].replace('_', ' ').capitalize()
                                alias_out = list(alias.values())[0].replace('_', ' ').capitalize()
                        if not scrapertools.find_single_match(elem.get('title', ''), patron_sea): continue
                        elem_json['season'] = int(scrapertools.find_single_match(elem.get('title', ''), patron_sea))
                        if elem_json['season'] != item.infoLabels['season']: continue
                        if not scrapertools.find_single_match(elem.get('title', ''), patron_cap): continue
                        elem_json['episode'] = int(scrapertools.find_single_match(elem.get('title', ''), patron_cap))
                        if elem_json['episode'] > episode_max: continue
                        if elem_json['episode'] > last_episode_to_air: last_episode_to_air = episode_max

                        elem_json['url'] = elem.get('url', '')
                        elem_json['quality'] = elem.get('quality', '').upper().replace('P', 'p').replace('HDTV 720p', 'HDTV-720p')
                        ignore = False
                        for episode, index, quality in epis_index.get(elem_json['episode'], []):
                            if elem_json['quality'].lower() == quality:
                                ignore = True
                                break
                        if ignore:
                            if DEBUG: logger.debug('DROP Cap. dup: %s / %sx%s / %s' \
                                                    % (item.contentSerieName, elem_json['season'], elem_json['episode'], elem_json['quality']))
                            continue
                        
                        if elem.get('season_search', ''): elem_json['season_search'] = elem['season_search']
                        if '#' in item.season_search: elem_json['season_search'] = item.season_search
                        elem_json['quality'] = '%s%s' % (elem_json['quality'], btdigg_label)
                        elem_json['size'] = elem.get('size', '').replace(btdigg_label_B, '')\
                                                                .replace('\xa0', ' ')
                        elem_json['torrent_info'] = elem_json['size']
                        elem_json['torrent_info'] += ' (%s)' % (alias_in or scrapertools.find_single_match(elem.get('title', '')\
                                                                            .replace(btdigg_label_B, ''), patron_title))
                        elem_json['language'] = elem.get('language', []) or item.language
                        elem_json['title'] = ''
                        elem_json['server'] = 'torrent'
                        elem_json['btdig_in_use'] = True

                        if (elem.get('password', {}) and isinstance(elem['password'], dict)) \
                                                     or str(elem.get('password', '')) == 'Contraseña DESCONOCIDA':
                            elem['password'] = elem_json['password'] = 'Contraseña DESCONOCIDA'
                            elem_json['password'] = find_rar_password(elem_json)
                            if str(elem_json.get('password', '')) == 'Contraseña DESCONOCIDA':
                                for elem_pass in matches:
                                    if elem_pass.get('season', 0) == elem_json.get('season', -1) \
                                                                     and elem_pass.get('episode', 0) == elem_json.get('episode', -1) \
                                                                     and elem_pass.get('password'):
                                        elem_json['password'] = elem_pass['password']
                                        break
                        elif elem.get('password'):
                            elem_json['password'] = elem['password']

                        if elem_json['episode'] in epis_index:
                            matches.append(elem_json.copy())
                            epis_index[elem_json['episode']] += [[elem_json['episode'], len(matches) - 1, 
                                                                  elem_json['quality'].replace(btdigg_label, '').lower()]]
                        else:
                            matches.append(elem_json.copy())
                            epis_index[elem_json['episode']] = [[elem_json['episode'], len(matches) - 1, 
                                                                 elem_json['quality'].replace(btdigg_label, '').lower()]]
                    except Exception:
                        logger.error(traceback.format_exc())

            if len(epis_index) >= last_episode_to_air: break

        if matches_len == len(matches): matches = AH_find_btdigg_matches(item, matches, **AHkwargs)
        matches = sorted(matches, key=lambda it: (it.get('episode', 0), self.convert_size(it.get('size', 0)))) if matches else []
    
    except Exception:
        logger.error(traceback.format_exc())

    return matches


def AH_find_btdigg_findvideos(self, item, matches=[], domain_alt=channel_py, **AHkwargs):
    logger.info('Look-up: %s' % AHkwargs.get('btdigg_lookup', False))
    global DEBUG, TEST_ON_AIR
    if self: TEST_ON_AIR = self.TEST_ON_AIR
    DEBUG = DEBUG if not TEST_ON_AIR else False
    ASSISTANT_REMOTE = True if config.get_setting("assistant_mode").lower() == 'otro' else False
    
    controls = self.finds.get('controls', {}) if self else {}
    btdigg_search = controls.get('btdigg_search', True)
    contentSeason = AHkwargs.pop('btdigg_contentSeason', controls.get('btdigg_contentSeason', 0))
    disable_cache = True if (not 'btdigg_cache' in AHkwargs  and not 'btdigg_cache' in controls) else \
                    not AHkwargs.pop('btdigg_cache', controls.get('btdigg_cache', True))
    quality_control = AHkwargs.pop('btdigg_quality_control', controls.get('btdigg_quality_control', False))
    canonical = AHkwargs.pop('canonical', self.canonical if self else {})
    matches_len = len(matches)
    language_alt = []
    found = False
    BTDIGG_SEARCH_STAT = False
    matches_cached = {}

    if item.matches_cached:
        for matches_cached in item.matches_cached:
            if matches_cached.get('url') and matches_cached['url'] in str(matches): continue
            if (not item.password or isinstance(item.password, dict) or str(item.password) == 'Contraseña DESCONOCIDA') \
                                  and matches_cached.get('password', {}):
                item.password = matches_cached.get('password', {})
            matches.append(matches_cached.copy())
            found = True
    elif 'matches_cached' in item:
        for matches_cached in (item.matches or []):
            if (not item.password or isinstance(item.password, dict) or str(item.password) == 'Contraseña DESCONOCIDA') \
                                  and matches_cached.get('password', {}):
                item.password = matches_cached.get('password', {})
        found = True
    elif BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
        found_list = AH_find_btdigg_ENTRY_from_BTDIGG(self, title=item.contentSerieName or item.contentTitle, 
                                                      contentType=item.contentType, matches=matches, item=item.clone(), reset=False, **AHkwargs)
        for found_item in found_list:
            if found_item and found_item.get('matches_cached'):
                for matches_cached in found_item['matches_cached']:
                    if matches_cached.get('url') and matches_cached['url'] in str(matches): continue
                    if (not item.password or isinstance(item.password, dict) or str(item.password) == 'Contraseña DESCONOCIDA') \
                                          and matches_cached.get('password', {}):
                        item.password = matches_cached.get('password', {})
                    matches.append(matches_cached.copy())
                    found = True
            else:
                found_item = list(found_item.values())[0]
                if found_item and found_item.get('episode_list') and found_item.get('tmdb_id', '') == item.infoLabels['tmdb_id']:
                    for epi, episodio in found_item.get('episode_list', {}).items():
                        if episodio.get('season', 0) == item.contentSeason and episodio.get('episode', 0) == item.contentEpisodeNumber:
                            for matches_cached in episodio.get('matches_cached', []):
                                if quality_control:
                                    if 'HDTV' == item.quality.replace(btdigg_label, ''):
                                        if matches_cached.get('quality', '') != 'HDTV':
                                            continue
                                    elif matches_cached.get('quality', '') == 'HDTV':
                                        continue
                                if not matches_cached.get('url'): continue
                                found = True
                                if matches_cached['url'] in str(matches): continue
                                if (not item.password or isinstance(item.password, dict) or str(item.password) == 'Contraseña DESCONOCIDA') \
                                                      and matches_cached.get('password', {}):
                                    item.password = matches_cached.get('password', {})
                                matches_cached['quality'] = '%s%s' % (matches_cached['quality'], btdigg_label)
                                if not matches_cached.get('language', []): matches_cached['language'] = item.language or ['CAST']
                                matches.append(matches_cached.copy())

    if found or AHkwargs.pop('btdigg_lookup', False) or (item.matches and item.channel != 'videolibrary' \
                                                     and item.contentChannel != 'videolibrary' and item.from_channel != 'videolibrary'):
        return matches

    if not btdigg_search:
        return matches

    if matches and isinstance(matches[0], list):
        matches_in = matches[:]
        matches = []
        for scrapedtitle, scrapedmagnet, scrapedsize, scrapedquality in matches_in:
            matches.append({'bt_url': '', 'title': scrapedtitle, 'url': scrapedmagnet, 'size': scrapedsize, 'quality': scrapedquality})

    try:
        if canonical.get('global_search_cancelled', False) or (config.GLOBAL_SEARCH_CANCELLED \
                                                           and canonical.get('global_search_active', False)):
            logger.info('## Búsqueda global cancelada: %s: %s' % (item.channel, item.title), force=True)
            return itemlist

        format_tmdb_id(item)

        if not PY3: from lib.alfaresolver import find_alternative_link
        else: from lib.alfaresolver_py3 import find_alternative_link

        quality_alt = ''
        language_alt = []
        titles_search = []
        titles_search_finds = []
        if self and self.finds.get('titles_search', {}).get('findvideos') \
                and BTDIGG_URL_SEARCH not in item.url and BTDIGG_URL_SEARCH not in item.url_tvshow:
            titles_search_finds = self.finds['titles_search']['findvideos']
        if self and self.finds.get('titles_search', {}).get('btdigg_search_findvideos') \
                and (BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow):
            titles_search_finds = self.finds['titles_search']['btdigg_search_findvideos']
        if titles_search_finds:
            titles_search.extend(titles_search_finds)
        elif BTDIGG_URL_SEARCH in item.url or BTDIGG_URL_SEARCH in item.url_tvshow:
            titles_search = search_btdigg_free_format_parse(self, item, BTDIGG_SEARCH, item.contentType, **AHkwargs)
            BTDIGG_SEARCH_STAT = True
        if item.contentType == 'movie':
            if not titles_search:
                titles_search = [{'urls': ['%s ' + domain_alt], 'checks': ['Cast', 'Esp', 'Spanish', domain_alt.replace('4k', '')], 
                                  'contentType': 'movie', 'limit_search': 4},
                                 {'urls': ['%s Bluray Castellano'], 'checks': ['Cast', 'Esp', 'Spanish', domain_alt.replace('4k', '')],
                                  'contentType': 'movie', 'limit_search': 4}]
            if not item.btdigg:
                quality_alt =  '720p 1080p 2160p 4kwebrip 4k bluray rip screener'
                language_alt = ['DUAL', 'CAST'] if 'CAST' in item.language else ['DUAL', 'LAT'] if 'LAT' in item.language \
                                                                                                else ['DUAL', 'CAST', 'LAT']
        else:
            if not titles_search:
                titles_search = [{'urls': ['%s Cap.' + '%s%s' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))], 
                                  'checks': ['Cap.'], 'contentType': 'episode', 'limit_search': 4}]
            if not item.btdigg:
                quality_alt =  '720p 1080p 2160p 4kwebrip 4k HDTV'
                if quality_control and '720' not in item.quality and '1080' not in item.quality and '4k' not in item.quality:
                    quality_alt =  'HDTV'
                language_alt = ['DUAL', 'CAST'] if 'CAST' in item.language else ['DUAL', 'LAT'] if 'LAT' in item.language \
                                                                                                else ['DUAL', 'CAST', 'LAT']

        if not BTDIGG_SEARCH_STAT:
            titles_search = search_btdigg_free_format_parse(self, item, titles_search, item.contentType, **AHkwargs)
        for title_search in titles_search:
            if title_search.get('contentType', 'movie') != item.contentType: continue

            limit_search = title_search.get('limit_search', 4)
            limit_pages = limit_search if domain_alt in str(title_search['urls']) else limit_search / 2
            limit_pages_min = (limit_search / 2) if domain_alt in str(title_search['urls']) else 1
            limit_items_found = 10 * 10
            patron_sea = r'(?i)Cap.(\d+)\d{2}'
            patron_cap = r'(?i)Cap.\d+(\d{2})'
            patron_title = r'(?i)(.*?(?:\(\d{4}\))?)\s*(?:-*\s*temp|\[)'

            torrent_params = {
                              'title_prefix': [title_search], 
                              'quality_alt': title_search.get('quality_alt', '') or quality_alt, 
                              'language_alt': title_search.get('language_alt', []) or language_alt, 
                              'find_alt_link_next': 0, 
                              'limit_pages': limit_pages, 
                              'link_found_limit': limit_items_found, 
                              'domain_alt': None,
                              'search_order': title_search['search_order'] if 'search_order' in title_search else 0
                              }

            x = 0
            while x < limit_pages:
                use_assistant = True
                try:
                    alfa_gateways = eval(base64.b64decode(window.getProperty("alfa_gateways")))
                except:
                    alfa_gateways = []
                if (xbmc.Player().isPlaying() or ASSISTANT_REMOTE) and len(alfa_gateways) > 1:
                    use_assistant = False
                torrent_params = find_alternative_link(item, torrent_params=torrent_params, cache=disable_cache, use_assistant=use_assistant)

                if not torrent_params.get('find_alt_link_result') and not torrent_params.get('find_alt_link_next'): x = 999999
                if not torrent_params.get('find_alt_link_result') and torrent_params.get('find_alt_link_next', 0) >= limit_pages_min: x = 999999
                if not torrent_params.get('find_alt_link_next'): x = 999999
                if torrent_params.get('find_alt_link_found') and int(torrent_params['find_alt_link_found']) < limit_items_found: 
                    limit_pages = int(int(torrent_params['find_alt_link_found']) / 10) + 1
                x += 1

                for y, elem in enumerate(torrent_params['find_alt_link_result']):
                    elem_json = {}
                    #logger.error(torrent_params['find_alt_link_result'][y])

                    try:
                        if item.contentType == 'episode':
                            if not scrapertools.find_single_match(elem.get('title', ''), patron_sea): continue
                            elem_json['season'] = int(scrapertools.find_single_match(elem.get('title', ''), patron_sea))
                            if elem_json['season'] != item.infoLabels['season']: continue
                            if not scrapertools.find_single_match(elem.get('title', ''), patron_cap): continue
                            elem_json['episode'] = int(scrapertools.find_single_match(elem.get('title', ''), patron_cap))
                            if elem_json['episode'] != item.contentEpisodeNumber: continue

                        elem_json['url'] = elem.get('url', '')
                        if elem_json['url'] in str(matches): 
                            if DEBUG: logger.debug('DROP: %s' % elem_json['url'])
                            continue

                        elem_json['language'] = elem.get('language', []) or item.language
                        elem_json['quality'] = elem.get('quality', '').replace('HDTV 720p', 'HDTV-720p').replace(btdigg_label, '')
                        q_match = False
                        for mate in matches:
                            if elem_json['quality'] in mate.get('quality', '').replace(btdigg_label, '').replace('*', ''):
                                for lang in elem_json['language']:
                                    if lang in mate.get('language', []) or mate.get('language', []) == '*':
                                        if DEBUG: logger.debug('DROP quality: %s' % elem_json['quality'])
                                        q_match = True
                        if q_match: continue
                        elem_json['quality'] = '%s%s' % (elem_json['quality'], btdigg_label)
                        elem_json['torrent_info'] = elem.get('size', '').replace('GB', 'G·B').replace('Gb', 'G·b')\
                                                                        .replace('MB', 'M·B').replace('Mb', 'M·b').replace('.', ',')\
                                                                        .replace(btdigg_label_B, '')
                        title = elem.get('title', '').replace(btdigg_label_B, '').replace('- ', '').replace(elem.get('quality', ''), '')
                        title = re.sub(r'(?i)BTDigg\s*|-\s+|\[.*?\]|Esp\w*\s*|Cast\w*\s*|Lat\w*\s*|span\w*' , '', title)
                        elem_json['torrent_info'] += ' (%s)' % title
                        elem_json['size'] = elem.get('size', '').replace(btdigg_label_B, '')\
                                                                .replace('[COLOR magenta][B]RAR-[/B][/COLOR]', '')
                        elem_json['server'] = 'torrent'
                        elem_json['btdig_in_use'] = True

                        if (elem.get('password', {}) and isinstance(elem['password'], dict)) \
                                                     or str(elem.get('password', '')) == 'Contraseña DESCONOCIDA':
                            elem['password'] = elem_json['password'] = 'Contraseña DESCONOCIDA'
                            elem_json['password'] = find_rar_password(elem_json)
                            if str(elem_json.get('password', '')) == 'Contraseña DESCONOCIDA':
                                for elem_pass in matches:
                                    if elem_pass.get('mediatype', '') in ['movie'] and elem_pass.get('password', ''):
                                        elem_json['password'] = elem_pass.get('password', '')
                                        break
                                    if elem_pass.get('season', 0) == elem_json.get('season', -1) \
                                                                     and elem_pass.get('episode', 0) == elem_json.get('episode', -1) \
                                                                     and elem_pass.get('password'):
                                        elem_json['password'] = elem_pass['password']
                                        break
                        elif elem.get('password'):
                            elem_json['password'] = elem['password']
                        if (not item.password or isinstance(item.password, dict) or str(item.password) == 'Contraseña DESCONOCIDA') \
                                              and matches_cached.get('password', {}):
                            item.password = matches_cached.get('password', {})

                        matches.append(elem_json.copy())

                    except Exception:
                        logger.error(traceback.format_exc())
                        continue

        if matches_len == len(matches): matches = AH_find_btdigg_matches(item, matches, **AHkwargs)
        if self: matches = sorted(matches, key=lambda it: (self.convert_size(it.get('size', 0)))) if matches else []
    
    except Exception:
        logger.error(traceback.format_exc())

    return matches


def find_rar_password(item):

    patron_title = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[)'
    patron_title_b = r'(?i)(.*?)\s*(?:-*\s*temp|\(|\[|\s+-)'

    try:
        if not isinstance(item, dict):
            elem_json = {'password': item.password, 'mediatype': item.contentType, 'title': item.contentSerieName or item.contentTitle, 
                         'season': item.contentSeason or 0, 'episode': item.contentEpisodeNumber or 0, 'tmdb_id': item.infoLabels['tmdb_id']}
        else:
            elem_json = item.copy()
        password = elem_json.get('password')

        if len(window.getProperty("alfa_cached_passwords")) < 5:
            if not PY3: from lib.alfaresolver import get_cached_files
            else: from lib.alfaresolver_py3 import get_cached_files
            window.setProperty("alfa_cached_passwords", jsontools.dump(get_cached_files('password'), **kwargs_json))
        alfa_cached_passwords = jsontools.load(window.getProperty("alfa_cached_passwords") or '{}')

        key = sxe = ''
        if elem_json.get('mediatype', '') != 'movie':
            sxe = '%sx%s' % (elem_json.get('season', 0), elem_json.get('episode', 0))
            key = elem_json.get('tmdb_id', elem_json.get('title', '').replace('- ', ''))
        else:
            sxe = 'movie'
            key = elem_json.get('title', '').lower()
            if scrapertools.find_single_match(elem_json.get('title', '').replace(btdigg_label_B, ''), patron_title).strip():
                key = scrapertools.find_single_match(elem_json['title'].replace(btdigg_label_B, ''), patron_title).strip()\
                                  .replace('- ', '').lower()
            elif scrapertools.find_single_match(elem_json.get('title', '').replace(btdigg_label_B, ''), patron_title_b).strip():
                key = scrapertools.find_single_match(elem_json['title'].replace(btdigg_label_B, ''), patron_title_b).strip()\
                                  .replace('- ', '').lower()

        if key and sxe and key in alfa_cached_passwords and sxe in alfa_cached_passwords[key]:
            if not isinstance(alfa_cached_passwords[key][sxe]['password'], dict) \
                                                 and str(alfa_cached_passwords[key][sxe]['password']) != 'Contraseña DESCONOCIDA':
                password = alfa_cached_passwords[key][sxe]['password']

    except Exception:
        logger.error(traceback.format_exc())

    logger.info('Contraseña vídeo: %s' % password)
    return password


def get_torrent_size(url, **kwargs):
    logger.info()
    from servers.torrent import caching_torrents
    
    """
    Módulo extraido del antiguo canal ZenTorrent
    
    Calcula el tamaño de los archivos que contienen un .torrent.  Descarga el archivo .torrent en una carpeta,
    lo lee y descodifica.  Si contiene múltiples archivos, suma el tamaño de todos ellos
    
    Llamada:            generictools.get_torrent_size(url, data_torrent=False)
    Entrada: url:       url del archivo .torrent
    Entrada: referer:   url de referer en caso de llamada con post
    Entrada: post:      contenido del post en caso de llamada con post
    torrent_params = {
                      'url': url,               url del archivo .torrent
                      'torrents_path': None,    Retorna el path the .torrent cacheado
                      'local_torr' = None,      Informa de la carpeta y archivo donde cachear el .torrent
                      'lookup', True,           en torrent.capture_thru_browser indica si solo da el aviso (False) o descarga (True)
                      'force': False,           Forzar cacheo del .torrent
                      'data_torrent': True,     Flag por si se quiere el contenido del .torretn de vuelta
                      'subtitles': True,        Se quieren subtitles_list de vuelta
                      'file_list': True,        Se quieren files de vuelta
                      'size': '',               str con el tamaño y tipo de medida ( MB, GB, etc)
                      'torrent_f': {},          dict() con el contenido del .torrent
                      'files': {},              dict() con los nombres de los archivos del torrent y su tamaño
                      'subtitles_list': [],     lista con archivos .str de subtítulos que acompañaban al .torrent
                      'cached': False,          True si el tarrent ha sido cacheado
                      'size_lista': [],         Lista de (.torrent, path)
                      'size_amount': [],        Lista de sizes si hay varios .torrents
                      'torrent_cached_list': [] Lista de torrents cacheados durante la sesión de Kodi
                      'time_elapsed':           Tiempo utilizado en la descarga del torrent.  0 si estaba cacheado
                      }
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
                data = decode_item(src.next, src.next())                        # Py2
            else:
                data = decode_item(src.__next__, next(src))                     # Py3
            for token in src:                                                   # look for more tokens
                raise SyntaxError("trailing junk")
        except (AttributeError, ValueError, StopIteration):
            try:
                data = data
            except Exception:
                data = src

        return data
        
    def tokenize(text, match=re.compile(r"([idel])|(\d+):|(-?\d+)").match):
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

    # Módulo principal: iniciamos diccionario de variables
    torrent_params = kwargs.pop('torrent_params', {})
    torrent_params['url'] = url or torrent_params.get('url', '')
    torrent_params['torrents_path'] = torrent_params.get('torrents_path', '')
    torrent_params['local_torr'] = torrent_params.get('local_torr', '')
    torrent_params['lookup'] = torrent_params.get('lookup', True)
    torrent_params['force'] = torrent_params.get('force', False)
    torrent_params['data_torrent'] = torrent_params.get('data_torrent', False)
    torrent_params['subtitles'] = torrent_params.get('subtitles', False)
    torrent_params['file_list'] = torrent_params.get('file_list', False)
    torrent_params['channel'] = torrent_params.get('channel', '')
    torrent_params['torrent_alt'] = torrent_params.get('torrent_alt', '')
    torrent_params['find_alt_link_option'] = torrent_params.get('find_alt_link_option', False)
    torrent_params['find_alt_link_result_save'] = torrent_params.get('find_alt_link_result_save', [])
    torrent_params['domain_alt'] = torrent_params.get('domain_alt', '') or find_alt_domains
    torrent_params['size'] = ''
    torrent_params['torrent_f'] = {}
    torrent_params['files'] = {}
    torrent_params['subtitles_list'] = []
    torrent_params['cached'] = False
    torrent_params['size_lista'] = []
    torrent_params['size_amount'] = []
    torrent_params['torrent_cached_list'] = []
    torrent_params['time_elapsed'] = 0
    torrent_params['find_alt_link_result'] = []
    torrent_params['find_alt_link_found'] = 0
    torrent_params['find_alt_link_next'] = 0
    
    # Google drive?
    drive_url = kwargs.get('drive_url', '') or 'https://drive.usercontent.google.com/u/0/uc?id=%s&export=download'
    if 'drive.google.com' in torrent_params['url']:
        if scrapertools.find_single_match(torrent_params['url'], r'\/\w\/(.*?)\/view\?'):
            torrent_params['url'] = url = drive_url % scrapertools.find_single_match(url, r'\/\w\/(.*?)\/view\?')
    
    if not url:
        torrent_params['size'] = 'ERROR'
        return torrent_params
    try:
        if isinstance(kwargs.get('timeout', 5), (tuple, list)): kwargs['timeout'] = kwargs['timeout'][1]
    except:
        kwargs['timeout'] = 5
    
    retry_CF = kwargs.get('retries_cloudflare', 2)
    if retry_CF < 0: torrent_params['torrents_path'] = 'CF_BLOCKED'
    torrent_file =  torrent_params.pop('torrent_file', '')
    if torrent_file: torrent_params['torrents_path'] = 'torrent_file'
    DOWNLOAD_PATH = config.get_setting('downloadpath', default='')
    
    if PY3 and isinstance(url, bytes):
        torrent_params['url'] = "".join(chr(x) for x in bytes(torrent_params['url']))
    if PY3 and isinstance(torrent_params['torrents_path'], bytes):
        torrent_params['torrents_path'] = "".join(chr(x) for x in bytes(torrent_params['torrents_path']))
    if PY3 and isinstance(torrent_params['local_torr'], bytes):
        torrent_params['local_torr'] = "".join(chr(x) for x in bytes(torrent_params['local_torr']))

    # Si queremos cachear el torrent se debe especificar el nombre del archivo de salida, con o sin path absoluto
    # Si se había cacheado previamente, se usa el archivo especificado
    if torrent_params['local_torr'] and not torrent_params['local_torr'].startswith('http') \
                       and not torrent_params['local_torr'].startswith('magnet'):
        torrent_params['cached'] = True
        if not filetools.isfile(torrent_params['local_torr']):
            if DOWNLOAD_PATH and filetools.dirname(DOWNLOAD_PATH.rstrip('/').rstrip('\\')) not in torrent_params['local_torr'] \
                             and not scrapertools.find_single_match(torrent_params['local_torr'], r'(?:\d+x\d+)?\s+\[.*?\]_\d+'):
                torrent_params['local_torr'] = filetools.join(DOWNLOAD_PATH, 
                          'cached_torrents_Alfa', torrent_params['local_torr'])
            if not filetools.isfile(torrent_params['local_torr']):
                torrent_params['cached'] = False

    try:        
        # Si es lookup, verifica si el canal tiene activado el Autoplay.  Si es así, retorna sin hacer el lookup
        if torrent_params['lookup'] and not torrent_params['force'] and not torrent_params['cached']:
            is_channel = inspect.getmodule(inspect.currentframe().f_back)
            is_channel = scrapertools.find_single_match(str(is_channel), r"<module\s*'channels\.(.*?)'")
            if is_channel:
                from modules import autoplay
                res = autoplay.is_active(is_channel)
                if res:
                    torrent_params['url'] = 'autoplay'
                    return torrent_params
        
        if not torrent_params['lookup']: kwargs['timeout'] = kwargs.get('timeout', 5) * 3
        if (torrent_params['url'] and not torrent_params['cached'] and retry_CF > 0 \
                                  and 'DUMMY' not in torrent_params['url'] and not torrent_file) \
                                  or torrent_params['url'].startswith("magnet"):
            
            torrent_file, torrent_params = caching_torrents(torrent_params['url'], torrent_params, **kwargs)
        
        elif torrent_params['cached']:
            torrent_file = filetools.read(torrent_params['local_torr'], mode='rb')
            torrent_params['torrents_path'] = torrent_params['local_torr']
        
        if torrent_params['url'].startswith("magnet"):
            torrent_params['size'] = ''
            logger.info('Torrent SIZE: %s-%s - %s' % ('MAGNET', torrent_params['torrents_path'], 
                         torrent_params['time_elapsed'] or torrent_params['cached']), force=True)
            return torrent_params
        
        if isinstance(torrent_params['torrents_path'], list):
            torrents_path_list = torrent_params['torrents_path'][:]
            torrent_lista = True
        else:
            torrents_path_list = [(torrent_params['torrents_path'], torrent_file)]
            torrent_lista = False
        
        for torrent_params['torrents_path'], torrent_file in torrents_path_list:
            torrent_params['size'] = ''
            if not torrent_params['torrents_path'] or 'CF_BLOCKED' in torrent_params['torrents_path'] \
                        or (PY3 and isinstance(torrent_file, bytes) and torrent_file.startswith(b"magnet")) \
                        or (isinstance(torrent_file, str) and torrent_file.startswith("magnet")):
                torrent_params['size'] = 'ERROR'
                
                # si el archivo .torrent está bloqueado con CF, se intentará descargarlo a través de un browser externo
                if torrent_params['torrents_path'] == 'CF_BLOCKED':
                    torrent_params['size'] += ' [COLOR hotpink][B]BLOQUEO[/B][/COLOR]'
                    browser, res = call_browser('', lookup=True, strict=True)
                    if not browser:
                        browser, res = call_browser('', lookup=True)
                    if not browser:
                        torrent_params['size'] += ': [COLOR magenta][B]Instala un browser externo para usar este enlace[/B][/COLOR] (Chrome, Firefox, Opera)'
                    elif res is None and not config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                        torrent_params['size'] += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
                    elif res is None and config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                        torrent_params['size'] += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                    elif res or config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                        if res and res is not True:
                            config.set_setting("capture_thru_browser_path", res, server="torrent")
                            torrent_params['size'] += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                        elif res and not config.get_setting("capture_thru_browser_path", server="torrent", default=""):
                            torrent_params['size'] += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
                        else:
                            torrent_params['size'] += ': [COLOR limegreen][B]Pincha para usar con [I]%s[/I][/B][/COLOR]' % browser
                    else:
                        torrent_params['size'] += ': [COLOR gold][B]Introduce la ruta para usar con [I]%s[/I][/B][/COLOR]' % browser
                    
                    if torrent_params['find_alt_link_option'] and torrent_params['find_alt_link_result_save']:
                        torrent_params['find_alt_link_result'] = torrent_params['find_alt_link_result_save'][:]
                        torrent_params['find_alt_link_result_save'] = []
                    elif torrent_params['find_alt_link_option'] and kwargs.get('item', {}):
                        if not PY3: from lib.alfaresolver import find_alternative_link
                        else: from lib.alfaresolver_py3 import find_alternative_link
                        torrent_params = find_alternative_link(kwargs['item'], torrent_params=torrent_params, cache=True)
                
                logger.info('Torrent SIZE: %s-%s - %s' % (str(torrent_params['size']), torrent_params['torrents_path'], 
                             torrent_params['time_elapsed'] or torrent_params['cached']), force=True)
                return torrent_params

            if PY3 and isinstance(torrent_file, bytes):                         # Convertimos a String para poder hacer el decode
                torrent_file = "".join(chr(x) for x in torrent_file)
            torrent_params['torrent_f'] = decode(torrent_file)                  # Decodificamos el .torrent

            #si sólo tiene un archivo, tomamos la longitud y la convertimos a una unidad legible, si no dará error
            try:
                sizet = torrent_params['torrent_f']["info"]['length']
                torrent_params['size'] = convert_size(sizet)
                
                torrent_params['files'] = torrent_params['torrent_f']["info"].copy()
                if 'path' not in torrent_params['files']: torrent_params['files'].update({'path': ['']})
                if 'piece length' in torrent_params['files']: del torrent_params['files']['piece length']
                if 'pieces' in torrent_params['files']: del torrent_params['files']['pieces']
                if 'name' in torrent_params['files']: del torrent_params['files']['name']
                torrent_params['files'] = [torrent_params['files']]
                torrent_params['files'].append({"__name": torrent_params['torrent_f']["info"]["name"], 'length': 0})
                torrent_params['size_lista'] += [(torrent_params['size'], torrent_params['torrents_path'], 
                            torrent_params['torrent_f'], torrent_params['files'])]
            except Exception:
                pass
                
            #si tiene múltiples archivos sumamos la longitud de todos
            if not torrent_params['size']:
                try:
                    check_video = scrapertools.find_multiple_matches(str(torrent_params['torrent_f']["info"]["files"]), r"'length': (\d+).*?}")
                    sizet = sum([int(i) for i in check_video])
                    torrent_params['size'] = convert_size(sizet)
                    
                    torrent_params['files'] = torrent_params['torrent_f']["info"]["files"][:]
                    torrent_params['files'].append({"__name": torrent_params['torrent_f']["info"]["name"], 'length': 0})
                    
                except Exception:
                    torrent_params['size'] = 'ERROR'
                    logger.error(traceback.format_exc())
            
            # Marcamos si es hay archivos RAR
            if '.rar' in str(torrent_params['files']):
                torrent_params['size'] = '[COLOR magenta][B]RAR-[/B][/COLOR]%s' % torrent_params['size']
                
            # Puede haber errores de decode en los paths.  Se intentan arreglar
            try:
                for entry in torrent_params['files']:
                    for file, path in list(entry.items()):
                        if file == 'path':
                            for x, file_r in enumerate(path):
                                entry[file][x] = scrapertools.decode_utf8_error(file_r)
                        elif file == '__name':
                            entry[file] = scrapertools.decode_utf8_error(path)
            except Exception:
                logger.error(traceback.format_exc())
            
            torrent_params['files'] = sorted(torrent_params['files'], reverse=True, key=lambda k: k['length'])
            torrent_params['size_lista'] += [(torrent_params['size'], torrent_params['torrents_path'], 
                            torrent_params['torrent_f'], torrent_params['files'])]
            torrent_params['size_amount'] += [torrent_params['size']]
        
        if len(torrent_params['size_amount']) > 1:
            torrent_params['size'] = str(torrent_params['size_amount'])

    except Exception:
        torrent_params['size'] = 'ERROR'
        torrent_params['torrent_f'] = {}
        torrent_params['files'] = {}
        torrent_params['torrents_path'] = ''
        torrent_params['subtitles_list'] = []
        torrent_lista = False
        logger.error('ERROR al buscar el tamaño de un .Torrent: ' + str(torrent_params['url']))
        logger.error(traceback.format_exc())

    logger.info('Torrent SIZE: %s - %s' % (str(torrent_params['size']), 
                 torrent_params['time_elapsed'] or torrent_params['cached']), force=True)

    return torrent_params


def verify_channel(channel, clones_list=False):
    
    # Lista con los datos de los canales alternativos
    # Cargamos en .json del canal para ver las listas de valores en settings
    
    clones = []

    """
    if channel_py:
        clones = channeltools.get_channel_json(channel_py)
        for settings in clones['settings']:                                     # Se recorren todos los settings
            if settings['id'] == "clonenewpct1_channels_list":                  # Encontramos en setting
                clones = settings['default']                                    # Carga lista de clones
                channel_alt = "'%s'" % channel
                break
    """

    if clones_list:
        if clones:
            import ast
            clones = ast.literal_eval(clones)
        return channel, (clones or [channel])
        
    return channel
 
                            
def call_browser(url, download_path='', lookup=False, strict=False, wait=False, intent='', dataType=''):
    logger.info()
    # Basado en el código de "Chrome Launcher 1.2.0" de Jani (@rasjani) Mikkonen
    # Llama a un browser disponible y le pasa una url
    import subprocess
    
    exePath = {}
    PATHS = []
    PLATAFORMA = config.get_system_platform()
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
                                     '', r'"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"'], 
                          "chromium": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                       ['--noerordialogs', '--disable-session-crashed-bubble', '--disable-infobars', '--start-maximized'], 
                                       '', r'"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"'], 
                          "firefox": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                      [], 
                                      r'Default=(.*?)[\r|\n]', r'user_pref\s*\("browser.download.dir",\s*"([^"]+)"\)'], 
                          "opera": ['<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url, 
                                    [], 
                                    '', r'"savefile"\s*:\s*{.*?"default_directory"\s*:\s*"([^"]+)"']
                         }

        # Establecemos las variables relativas a cada plataforma
        if PLATAFORMA in ['android', 'atv2']:
            try:
                ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
            except Exception:
                ANDROID_STORAGE = ''
            if not ANDROID_STORAGE:
                if "'HOME'" in os.environ:
                    ANDROID_STORAGE = scrapertools.find_single_match(os.getenv('HOME'), r'^(\/.*?)\/')
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
                    except Exception:
                        continue
                if not PM_LIST: raise
                
                if PY3 and isinstance(PM_LIST, bytes):
                    PM_LIST = PM_LIST.decode()
                PM_LIST = PM_LIST.replace('\n', ', ')
            except Exception:
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
        
        elif PLATAFORMA in ['windows', 'xbox']:
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

        elif PLATAFORMA in ['osx', 'ios', 'tvos', 'darwin']:
            exePath = {
                       "chrome": [['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                                   '/Applications/Google Chrome.app/AppData/AppHome'], 
                                  0, 'HOME', [], ['Library/Application Support/Google/Chrome/Default/Preferences']], 
                       "chromium": [['/Applications/Chromium.app/Contents/MacOS/Chromium', 
                                     '/Applications/Chromium.app/AppData/AppHome'], 
                                    0, 'HOME', [], ['Library/Application Support/Chromium/Default/Preferences']], 
                       "firefox": [['/Applications/Firefox.app/Contents/MacOS/firefox', 
                                    '/Applications/Firefox.app/AppData/AppHome'], 
                                   0, 'HOME', ['Library/Application Support/Firefox/installs.ini'], ['prefs.js']],
                       "opera": [['/Applications/Opera.app/Contents/MacOS/opera', 
                                  '/Applications/Opera.app/AppData/AppHome'], 
                                 0, 'HOME', [], ['/Library/Application Support/com.operasoftware.Opera/Preferences']]
                      }
            
            PATHS = ['/Applications']
            DOWNLOADS_PATH = [filetools.join(os.getenv('HOME'), 'Descargas'), filetools.join(os.getenv('HOME'), 'Downloads')]
            
            PREF_PATHS = [filetools.join(os.getenv('HOME'), '/Library/Application Support')]
            
        elif PLATAFORMA in ['raspberry']:
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
        
        elif PLATAFORMA in ['linux']:
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
                        if PATH:
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
                        if not prefs_file and PLATAFORMA in ['android', 'atv2']:
                            prefs_file = '/data'
                    except Exception:
                        if PLATAFORMA in ['android', 'atv2']:
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
                    if PLATAFORMA in ['android', 'atv2']:
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
                # Si no se ha encontrado ningún browser que cumpla las condiciones, mostramos un codigo QR
                if lookup:
                    return ('QRCODE', False)
                else:
                    from platformcode.platformtools import dialog_qr_message
                    if dialog_qr_message(config.get_localized_string(70759), url, url):
                        return ('QRCODE', False)
                # Si no esta disponible QRCODE, se vuelve con error
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
        if PLATAFORMA in ['android', 'atv2']:
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
                if PLATAFORMA in ['windows', 'xbox']:
                    s = subprocess.Popen(params, shell=False, creationflags=creationFlags, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    s = subprocess.Popen(params, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                res = s
                
                # Si se ha pedido esperar hasta que termine el browser...
                if wait:
                    output_cmd, error_cmd = s.communicate()
                    if error_cmd: res = False
                    logger.error('Error "%s" en Browser %s, Comando %s' % (str(error_cmd), browser, str(params)))
            except Exception:
                res = False
                logger.error('Error "%s" en Browser %s, Comando %s' % (str(error_cmd), browser, str(params)))

    except Exception:
        logger.error(traceback.format_exc())
        return (False, False)
    
    return (browser.capitalize(), res)


def rec(site_key, co, sa, loc):
    from core import httptools
    
    api_url = "https://www.google.com/recaptcha/api.js"
    headers = {
               "User-Agent": httptools.get_user_agent(),
               "Referer": loc,
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "ro-RO,ro;q=0.8,en-US;q=0.6,en-GB;q=0.4,en;q=0.2"
               }

    r_data = httptools.downloadpage(api_url, headers=headers, follow_redirects=False, alfa_s=True).data
    v = scrapertools.find_single_match(r_data, "releases/([^/]+)")
    cb = "123456789"
    base_url = "https://www.google.com/recaptcha/api2/anchor?ar=1&k=%s&co=%s&hl=ro&v=%s&size=invisible&cb%s" % (site_key, co, v, cb)

    r_data = httptools.downloadpage(base_url, headers=headers, follow_redirects=False, alfa_s=True).data
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

    r_data = httptools.downloadpage(t_url, headers=head, follow_redirects=False, post=post, alfa_s=True).data
    response = scrapertools.find_single_match(r_data, '"rresp","([^"]+)"')
    return response
