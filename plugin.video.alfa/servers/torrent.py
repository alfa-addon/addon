# -*- coding: utf-8 -*-

#from builtins import str
from builtins import range
import sys
PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; VFS = False

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib

import time
import threading
import os
import traceback
import re

try:
    import xbmc
    import xbmcgui
    import xbmcaddon
except:
    pass

from core import filetools
from core import httptools
from core import scrapertools
from core import jsontools
from core.item import Item
from platformcode import logger
from platformcode import config
from platformcode import platformtools

extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg',
                   '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg',
                   '.mpe', '.mp4', '.ogg', '.rar', '.wmv', '.zip']

trackers = [
        "udp://tracker.openbittorrent.com:80/announce",
        "http://tracker.torrentbay.to:6969/announce",
        "http://tracker.pow7.com/announce",
        "udp://tracker.ccc.de:80/announce",
        "udp://open.demonii.com:1337",

        "http://9.rarbg.com:2710/announce",
        "http://bt.careland.com.cn:6969/announce",
        "http://explodie.org:6969/announce",
        "http://mgtracker.org:2710/announce",
        "http://tracker.best-torrents.net:6969/announce",
        "http://tracker.tfile.me/announce",
        "http://tracker1.wasabii.com.tw:6969/announce",
        "udp://9.rarbg.com:2710/announce",
        "udp://9.rarbg.me:2710/announce",
        "udp://coppersurfer.tk:6969/announce",

        "http://www.spanishtracker.com:2710/announce",
        "http://www.todotorrents.com:2710/announce",
           ]


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("server=torrent, la url es la buena")
    
    if page_url.startswith("magnet:"):
        video_urls = [["magnet: [torrent]", page_url]]
    else:
        video_urls = [[".torrent [torrent]", page_url]]

    return video_urls


class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass

xbmc_player = XBMCPlayer()


def caching_torrents(url, referer=None, post=None, torrents_path=None, timeout=10, \
                    lookup=False, data_torrent=False, headers={}, proxy_retries=1):
    if torrents_path != None:
        logger.info("path = " + torrents_path)
        if url != torrents_path:
            logger.info("url = " + url)
    else:
        logger.info("url = " + url)
    if referer and post:
        logger.info('REFERER: ' + referer)

    torrent_file = ''
    t_hash = ''
    if referer:
        headers.update({'Content-Type': 'application/x-www-form-urlencoded', 'Referer': referer})   #Necesario para el Post del .Torrent
    
    """
    Descarga en el path recibido el .torrent de la url recibida, y pasa el decode
    Devuelve el path real del .torrent, o el path vacío si la operación no ha tenido éxito
    """
    
    videolibrary_path = config.get_videolibrary_path()                          #Calculamos el path absoluto a partir de la Videoteca
    if torrents_path == None:
        if not videolibrary_path:
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                                #Si hay un error, devolvemos el "path" vacío
        torrents_path = filetools.join(videolibrary_path, 'temp_torrents_Alfa', 'cliente_torrent_Alfa.torrent')    #path de descarga temporal
    if '.torrent' not in torrents_path:
        torrents_path += '.torrent'                                             #path para dejar el .torrent
    #torrents_path_encode = filetools.encode(torrents_path)                     #encode utf-8 del path
    torrents_path_encode = torrents_path
    
    #if url.endswith(".rar") or url.startswith("magnet:"):                      #No es un archivo .torrent
    if url.endswith(".rar"):                                                    #No es un archivo .torrent
        logger.error('No es un archivo Torrent: ' + url)
        torrents_path = ''
        if data_torrent:
            return (torrents_path, torrent_file)
        return torrents_path                                                    #Si hay un error, devolvemos el "path" vacío
    
    try:
        #Descargamos el .torrent
        if url.startswith("magnet:"):
            if config.get_setting("magnet2torrent", server="torrent", default=False):
                torrent_file = magnet2torrent(url, headers=headers)             #Convierte el Magnet en un archivo Torrent
            else:
                if data_torrent:
                    return (url, torrent_file)
                return url
            if not torrent_file:
                logger.error('No es un archivo Magnet: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
        elif not url.startswith("http"):
            torrent_file = filetools.read(url, silent=True, vfs=VFS)
            if not torrent_file:
                logger.error('No es un archivo Torrent: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
            torrent_file_uncoded = torrent_file
            if PY3 and isinstance(torrent_file, bytes):
                torrent_file = "".join(chr(x) for x in bytes(torrent_file_uncoded))
        else:
            if lookup:
                proxy_retries = 0
            if post:                                                            #Descarga con POST
                response = httptools.downloadpage(url, headers=headers, post=post, \
                            follow_redirects=False, timeout=timeout, proxy_retries=proxy_retries)
            else:                                                               #Descarga sin post
                response = httptools.downloadpage(url, headers=headers, timeout=timeout, \
                            proxy_retries=proxy_retries)
            if not response.sucess:
                logger.error('Archivo .torrent no encontrado: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
            torrent_file = response.data
            torrent_file_uncoded = response.data
            if PY3 and isinstance(torrent_file, bytes):
                torrent_file = "".join(chr(x) for x in bytes(torrent_file_uncoded))

        #Si es un archivo .ZIP tratamos de extraer el contenido
        if torrent_file.startswith("PK"):
            logger.info('Es un archivo .ZIP: ' + url)
            
            torrents_path_zip = filetools.join(videolibrary_path, 'temp_torrents_zip')  #Carpeta de trabajo
            torrents_path_zip = filetools.encode(torrents_path_zip)
            torrents_path_zip_file = filetools.join(torrents_path_zip, 'temp_torrents_zip.zip')     #Nombre del .zip
            
            import time
            filetools.rmdirtree(torrents_path_zip)                              #Borramos la carpeta temporal
            time.sleep(1)                                                       #Hay que esperar, porque si no da error
            filetools.mkdir(torrents_path_zip)                                  #La creamos de nuevo
            
            if filetools.write(torrents_path_zip_file, torrent_file_uncoded, vfs=VFS):  #Salvamos el .zip
                torrent_file = ''                                               #Borramos el contenido en memoria
                try:                                                            #Extraemos el .zip
                    from core import ziptools
                    unzipper = ziptools.ziptools()
                    unzipper.extract(torrents_path_zip_file, torrents_path_zip)
                except:
                    import xbmc
                    xbmc.executebuiltin('XBMC.Extract("%s", "%s")' % (torrents_path_zip_file, torrents_path_zip))
                    time.sleep(1)
                
                for root, folders, files in filetools.walk(torrents_path_zip):  #Recorremos la carpeta para leer el .torrent
                    for file in files:
                        if file.endswith(".torrent"):
                            input_file = filetools.join(root, file)             #nombre del .torrent
                            torrent_file = filetools.read(input_file, vfs=VFS)  #leemos el .torrent
                    torrent_file_uncoded = torrent_file
                    if PY3 and isinstance(torrent_file, bytes):
                        torrent_file = "".join(chr(x) for x in bytes(torrent_file_uncoded))

            filetools.rmdirtree(torrents_path_zip)                              #Borramos la carpeta temporal

        #Si no es un archivo .torrent (RAR, HTML,..., vacío) damos error
        if not scrapertools.find_single_match(torrent_file, '^d\d+:.*?\d+:'):
            logger.error('No es un archivo Torrent: ' + url)
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                                #Si hay un error, devolvemos el "path" vacío
        
        #Calculamos el Hash del Torrent y modificamos el path
        import bencode, hashlib
        
        decodedDict = bencode.bdecode(torrent_file_uncoded)
        if not PY3:
            t_hash = hashlib.sha1(bencode.bencode(decodedDict[b"info"])).hexdigest()
        else:
            t_hash = hashlib.sha1(bencode.bencode(decodedDict["info"])).hexdigest()
        
        if t_hash and not scrapertools.find_single_match(torrents_path, '(?:\d+x\d+)?\s+\[.*?\]_\d+'):
            torrents_path = filetools.join(filetools.dirname(torrents_path), t_hash + '.torrent')
            torrents_path_encode = filetools.join(filetools.dirname(torrents_path_encode), t_hash + '.torrent')
        
        #Salvamos el .torrent
        if not lookup:
            if not url.startswith("http") and not torrent_file.startswith("PK") and filetools.isfile(url):
                if url != torrents_path:
                    ret = filetools.copy(url, torrents_path_encode, silent=True)
                else:
                    ret = True
            else:
                ret = filetools.write(torrents_path_encode, torrent_file_uncoded, silent=True, vfs=VFS)
            if not ret:
                logger.error('ERROR: Archivo .torrent no escrito: ' + torrents_path_encode)
                torrents_path = ''                                              #Si hay un error, devolvemos el "path" vacío
                torrent_file = ''                                               #... y el buffer del .torrent
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path
    except:
        torrents_path = ''                                                      #Si hay un error, devolvemos el "path" vacío
        torrent_file = ''                                                       #... y el buffer del .torrent
        logger.error('Error en el proceso de descarga del .torrent: ' + url + ' / ' + torrents_path_encode)
        logger.error(traceback.format_exc())
    
    #logger.debug(torrents_path)
    if data_torrent:
        return (torrents_path, torrent_file)
    return torrents_path
    

def magnet2torrent(magnet, headers={}):
    logger.info()
    
    torrent_file = ''
    info = ''
    post = ''
    LIBTORRENT_PATH = config.get_setting("libtorrent_path", server="torrent", default="")
    LIBTORRENT_MAGNET_PATH = filetools.join(config.get_setting("downloadpath"), 'magnet')
    MAGNET2TORRENT = config.get_setting("magnet2torrent", server="torrent", default=False)
    btih = scrapertools.find_single_match(magnet, 'urn:btih:([\w\d]+)\&').upper()

    if magnet.startswith('magnet') and MAGNET2TORRENT:

        # Tratamos de convertir el magnet on-line (opción más rápida, pero no se puede convertir más de un magnet a la vez)
        url_list = [
                    ('https://itorrents.org/torrent/', 6, '', '.torrent')
                   ]                                                            # Lista de servicios on-line testeados
        for url, timeout, id, sufix in url_list:
            if id:
                post = '%s=%s' % (id, magnet)
            else:
                url = '%s%s%s' % (url, btih, sufix)
            response = httptools.downloadpage(url, timeout=timeout, headers=headers, post=post)
            if not response.sucess:
                continue
            if not scrapertools.find_single_match(response.data, '^d\d+:.*?\d+:') and not response.data.startswith("PK"):
                continue
            torrent_file = response.data
            break

        #Usamos Libtorrent para la conversión del magnet como alternativa (es lento)
        if not torrent_file:
            lt, e, e1, e2 = import_libtorrent(LIBTORRENT_PATH)                  # Importamos Libtorrent
            if lt:
                ses = lt.session()                                              # Si se ha importado bien, activamos Libtorrent
                ses.add_dht_router("router.bittorrent.com",6881)
                ses.add_dht_router("router.utorrent.com",6881)
                ses.add_dht_router("dht.transmissionbt.com",6881)
                if ses:
                    filetools.mkdir(LIBTORRENT_MAGNET_PATH)                     # Creamos la carpeta temporal
                    params = {
                              'save_path': LIBTORRENT_MAGNET_PATH,
                              'trackers': trackers,
                              'storage_mode': lt.storage_mode_t.storage_mode_allocate
                             }                                                  # Creamos los parámetros de la sesión
                    
                    h = lt.add_magnet_uri(ses, magnet, params)                  # Abrimos la sesión
                    i = 0
                    if config.get_platform(True)['num_version'] >= 14:
                        monitor = xbmc.Monitor()                                                # For Kodi >= 14
                    else:
                        monitor = None
                    while not h.has_metadata() and not ((monitor and monitor.abortRequested()) \
                                    or (not monitor and xbmc.abortRequested)):  # Esperamos mientras Libtorrent abre la sesión
                        h.force_dht_announce()
                        time.sleep(1)
                        i += 1
                        logger.error(i)
                        if i > 5:
                            LIBTORRENT_PATH = ''                                # No puede convertir el magnet
                            break
                    
                    if LIBTORRENT_PATH:
                        info = h.get_torrent_info()                             # Obtiene la información del .torrent
                        torrent_file = lt.bencode(lt.create_torrent(info).generate())   # Obtiene los datos del .torrent
                    ses.remove_torrent(h)                                       # Desactiva Libtorrent
                    filetools.rmdirtree(LIBTORRENT_MAGNET_PATH)                 # Elimina la carpeta temporal
    
    return torrent_file    


def verify_url_torrent(url, timeout=5):
    """
    Verifica si el archivo .torrent al que apunta la url está disponible, descargándolo en un area temporal
    Entrada:    url
    Salida:     True o False dependiendo del resultado de la operación
    """

    if not url or url == 'javascript:;':                                        #Si la url viene vacía...
        return False                                                            #... volvemos con error
    torrents_path = caching_torrents(url, timeout=timeout, lookup=True)         #Descargamos el .torrent
    if torrents_path:                                                           #Si ha tenido éxito...
        return True
    else:
        return False


# Reproductor Cliente Torrent propio (libtorrent)
def bt_client(mediaurl, xlistitem, rar_files, subtitle=None, password=None, item=None):
    logger.info()
    
    # Importamos el cliente
    from btserver import Client

    played = False
    debug = False

    try:
        save_path_videos = ''
        save_path_videos = filetools.join(config.get_setting("bt_download_path", server="torrent", \
               default=config.get_setting("downloadpath")), 'BT-torrents')
        torrent_path = filetools.join(save_path_videos, '.cache', filetools.basename(mediaurl).upper())
        if mediaurl.startswith('magnet:'):
            t_hash = scrapertools.find_single_match(item.url, 'xt=urn:btih:([^\&]+)\&')
            if t_hash:
                torrent_path = filetools.join(save_path_videos, '.cache', t_hash.upper()+'.torrent')
        if not filetools.exists(torrent_path):
            filetools.copy(mediaurl, torrent_path, silent=True)
    except:
        pass
    if not config.get_setting("bt_download_path", server="torrent") and save_path_videos:
        config.set_setting("bt_download_path", filetools.join(config.get_data_path(), 'downloads'), server="torrent")
    if not save_path_videos:
        save_path_videos = filetools.join(config.get_data_path(), 'downloads', 'BT-torrents')
        config.set_setting("bt_download_path", filetools.join(config.get_data_path(), 'downloads'), server="torrent")
        
    UNRAR = config.get_setting("unrar_path", server="torrent", default="")
    BACKGROUND = config.get_setting("mct_background_download", server="torrent", default=True)
    RAR = config.get_setting("mct_rar_unpack", server="torrent", default=True)
    try:
        BUFFER = int(config.get_setting("bt_buffer", server="torrent", default="50"))
    except:
        BUFFER = 50
    DOWNLOAD_LIMIT = config.get_setting("mct_download_limit", server="torrent", default="")
    if DOWNLOAD_LIMIT:
        try:
            DOWNLOAD_LIMIT = int(DOWNLOAD_LIMIT)
        except:
            DOWNLOAD_LIMIT = 0
    else:
        DOWNLOAD_LIMIT = 0
    UPLOAD_LIMIT = 100
    
    torr_client = 'BT'
    rar_file = ''
    rar_names = []
    rar = False
    rar_res = False
    bkg_user = False
    progress_file = 0
    torrent_deleted = False
    DOWNGROUND = False
    if item.downloadFilename and item.downloadStatus in [2, 4]:                 # Descargas AUTO
        bkg_user = True
        BACKGROUND = True
        DOWNGROUND = True
    
    video_names = []
    video_file = ''
    video_path = ''
    videourl = ''
    msg_header = 'Alfa %s Cliente Torrent' % torr_client
    
    # Iniciamos el cliente:
    c = Client(url=mediaurl, is_playing_fnc=xbmc_player.isPlaying, wait_time=None, auto_shutdown=False, timeout=10,
               temp_path=save_path_videos, print_status=debug, auto_delete=False, bkg_user=bkg_user)
    
    if not rar_files and item.url.startswith('magnet:') and item.downloadServer \
                        and 'url' in str(item.downloadServer):
        from lib import generictools
        for x in range(600):
            if filetools.exists(item.downloadServer['url']):
                break
            time.sleep(1)
            continue
        time.sleep(5)
        if filetools.exists(item.downloadServer['url']):
            for x in range(30):
                size, url, torrent_f, rar_files = generictools.get_torrent_size(item.downloadServer['url'], 
                            file_list=True, lookup=False, torrents_path=item.downloadServer['url'], 
                            local_torr=item.downloadServer['url'])
                if 'ERROR' not in size:
                    break
                time.sleep(5)

    for entry in rar_files:
        for file, path in list(entry.items()):
            if file == 'path' and '.rar' in str(path):
                for file_r in path:
                    rar_names += [file_r]
                    rar = True
                    if RAR and BACKGROUND:
                        bkg_user = True
            elif file == 'path' and not '.rar' in str(path):
                for file_r in path:
                    if os.path.splitext(file_r)[1] in extensions_list:
                        video_names += [file_r]
            elif file == '__name':
                video_path = path
    if rar: rar_names = sorted(rar_names)
    if rar: rar_file = '%s/%s' % (video_path, rar_names[0])
    erase_file_path = filetools.join(save_path_videos, video_path)
    if video_names: video_file = video_names[0]
    
    if item.url.startswith('magnet:') and video_path:
        item.downloadFilename = ':%s: %s' % (torr_client, filetools.join(video_path, video_file))
        update_control(item)
    if not video_file and video_path:
        video_file = video_path
    video_path = erase_file_path
    
    if rar and RAR and not UNRAR:
        if not platformtools.dialog_yesno(msg_header, 'Se ha detectado un archivo .RAR en la descarga', \
                    'No tiene instalado el extractor UnRAR', '¿Desea descargarlo en cualquier caso?'):
            c.stop()
            return

    activo = True
    finalizado = False
    dp_cerrado = True

    # Mostramos el progreso
    if (rar and RAR and BACKGROUND) or DOWNGROUND:                                              # Si se descarga un RAR...
        progreso = platformtools.dialog_progress_bg(msg_header)
        if not DOWNGROUND:
            platformtools.dialog_notification("Descarga de RAR en curso", "Puedes realizar otras tareas en Kodi mientrastanto. " + \
                    "Te informaremos...", time=10000)
    else:
        progreso = platformtools.dialog_progress('Alfa %s Cliente Torrent' % torr_client, '')
    dp_cerrado = False

    # Mientras el progreso no sea cancelado ni el cliente cerrado
    if config.get_platform(True)['num_version'] >= 14:
        monitor = xbmc.Monitor()                                                # For Kodi >= 14
    else:
        monitor = None
    x = 1
    try:
        while not c.closed and not torrent_deleted and not ((monitor and monitor.abortRequested()) \
                                    or (not monitor and xbmc.abortRequested)):
            # Obtenemos el estado del torrent
            x += 1
            s = c.status
            if debug:
                # Montamos las tres lineas con la info del torrent
                txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                      (s.progress_file, s.file_size, s.str_state, s._download_rate)
                txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                       (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                        s.trackers, s.pieces_sum, s.pieces_len)
                txt3 = 'Origen Peers TRK: %d DHT: %d PEX: %d LSD %d ' % \
                       (s.trk_peers, s.dht_peers, s.pex_peers, s.lsd_peers)
            else:
                txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                      (s.progress_file, s.file_size, s.str_state, s._download_rate)
                txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                       (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                        s.trackers, s.pieces_sum, s.pieces_len)
                txt3 = video_file

            if (rar and RAR and BACKGROUND) or bkg_user:
                progreso.update(s.buffer, txt, txt2)
            else:
                progreso.update(s.buffer, txt, txt2, txt3)
            time.sleep(1)
            if s.progress_file > 1 and (str(x).endswith('0') or str(x).endswith('5')) and not filetools.exists(torrent_path):
                progress_file = s.progress_file
                torrent_deleted = True
                finalizado = False
                

            if (not bkg_user and progreso.iscanceled()) and (not (rar and RAR and BACKGROUND) and progreso.iscanceled()):
                
                if not dp_cerrado:
                    progreso.close()
                    dp_cerrado = True
                if 'Finalizado' in s.str_state or 'Seeding' in s.str_state:
                    """
                    if not rar and platformtools.dialog_yesno(msg_header, config.get_localized_string(70198)):
                        played = False
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress(msg_header, '')
                        progreso.update(s.buffer, txt, txt2, txt3)
                    else:
                    """
                    dp_cerrado = False
                    progreso = platformtools.dialog_progress(msg_header, '')
                    break

                else:
                    if platformtools.dialog_yesno(msg_header, "¿Borramos los archivo descargados? (incompletos)",  
                                    "Selecciona NO para seguir descargando en segundo plano"):
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress(msg_header, '')
                        break

                    else:
                        bkg_user = True
                        if not dp_cerrado: progreso.close()
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress_bg(msg_header)
                        progreso.update(s.buffer, txt, txt2)
                        if not c.closed:
                            c.set_speed_limits(DOWNLOAD_LIMIT, UPLOAD_LIMIT)    # Bajamos la velocidad en background

            # Si el buffer se ha llenado y la reproduccion no ha sido iniciada, se inicia
            if ((s.pieces_sum >= BUFFER  or 'Finalizado' in s.str_state or 'Seeding' in s.str_state) and not rar and not bkg_user) or \
                        (s.pieces_sum >= s.pieces_len - 3 and s.pieces_len > 0 and ('Finalizado' in s.str_state or 'Seeding' \
                        in s.str_state) and (rar or bkg_user)) and not played:
                
                if rar and RAR and UNRAR:
                    c.stop()
                    activo = False
                    finalizado = True
                    bkg_user = False
                    dp_cerrado = False
                    video_file, rar_res, video_path, erase_file_path = extract_files(rar_file, \
                                    save_path_videos, password, progreso, item, torr_client)  # ... extraemos el vídeo del RAR
                    
                    item.downloadFilename = video_path.replace(save_path_videos, '')
                    item.downloadFilename = filetools.join(item.downloadFilename, video_file)
                    item.downloadFilename = ':%s: %s' % ('BT', item.downloadFilename)
                    
                    if rar_res:
                        time.sleep(1)
                    else:
                        break
                elif (rar and not UNRAR) or (rar and not RAR):
                    break
                elif bkg_user:
                    finalizado = True
                    break
                
                # Cerramos el progreso
                if not dp_cerrado:
                    progreso.close()
                    dp_cerrado = True

                # Reproducimos el vídeo extraido, si no hay nada en reproducción
                if not c.closed:
                    c.set_speed_limits(DOWNLOAD_LIMIT, UPLOAD_LIMIT)            # Bajamos la velocidad en background
                bkg_auto = True
                while xbmc_player.isPlaying():
                    time.sleep(3)      
                
                # Obtenemos el playlist del torrent
                #videourl = c.get_play_list()
                if not rar_res:                                                 # Es un Magnet ?
                    video_file = filetools.join(save_path_videos, s.file_name)
                    if erase_file_path == save_path_videos:
                        erase_file_path = video_file
                    videourl = video_file
                else:
                    videourl = filetools.join(video_path, video_file)

                # Iniciamos el reproductor
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                playlist.clear()
                playlist.add(videourl, xlistitem)
                # xbmc_player = xbmc_player
                log("##### videourl: %s" % videourl)
                xbmc_player.play(playlist)

                # Marcamos como reproducido para que no se vuelva a iniciar
                played = True
                
                mark_auto_as_watched(item)
                
                # Y esperamos a que el reproductor se cierre
                bkg_auto = True
                dp_cerrado = True
                while xbmc_player.isPlaying():
                    time.sleep(1)
                    
                    if xbmc.getCondVisibility('Player.Playing'):
                        if not dp_cerrado:
                            dp_cerrado = True
                            progreso.close()
                    
                    if xbmc.getCondVisibility('Player.Paused') and not rar_res:
                        if not c.closed: s = c.status
                        txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                              (s.progress_file, s.file_size, s.str_state, s._download_rate)
                        txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                               (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                                s.trackers, s.pieces_sum, s.pieces_len)
                        txt3 = video_file[:99]
                        if dp_cerrado:
                            dp_cerrado = False
                            progreso = xbmcgui.DialogProgressBG()
                            progreso.create(msg_header)
                        progreso.update(s.buffer, msg_header, '[CR][CR]' + txt + '[CR]' + txt2)
                
                if not dp_cerrado:
                    dp_cerrado = True
                    progreso.close()
                
                # Miramos si se ha completado la descarga para borrar o no los archivos
                if activo:
                    s = c.status
                if s.pieces_sum == s.pieces_len:
                    finalizado = True
                    break

                if platformtools.dialog_yesno(msg_header, "¿Borramos los archivo descargados? (incompletos)",  
                                    "Selecciona NO para seguir descargando en segundo plano"):
                    progreso = platformtools.dialog_progress(msg_header, '')
                    dp_cerrado = False
                    break
                else:
                    bkg_user = True
                    played = False
                    if not dp_cerrado: progreso.close()
                    progreso = platformtools.dialog_progress_bg(msg_header)
                    progreso.update(s.buffer, txt, txt2)
                    dp_cerrado = False
                    continue
                
                # Cuando este cerrado,  Volvemos a mostrar el dialogo
                if not (rar and bkg_user):
                    progreso = platformtools.dialog_progress(msg_header, '')
                    progreso.update(s.buffer, txt, txt2, txt3)
                    dp_cerrado = False
                    
                break
    except:
        logger.error(traceback.format_exc(1))
        return
    
    if not dp_cerrado:
        if rar or bkg_user:
            progreso.update(100, config.get_localized_string(70200), " ")
        else:
            progreso.update(100, config.get_localized_string(70200), " ", " ")

    # Detenemos el cliente
    if activo and not c.closed:
        c.stop()
        activo = False

    # Cerramos el progreso
    if not dp_cerrado:
        progreso.close()
        dp_cerrado = True
    
    # Actualizado .json de control de descargas
    item.downloadProgress = 100
    if torrent_deleted:
        item.downloadProgress = 0
        log("##### Progreso: %s, .torrent borrado: %s" % (str(progress_file), erase_file_path))
    update_control(item)
    if item.downloadStatus in [2, 4]:
        if item.downloadProgress in [100]:
            return
    
    # Y borramos los archivos de descarga restantes
    time.sleep(1)
    if (filetools.exists(erase_file_path) and not bkg_user) or torrent_deleted:
        if finalizado and not platformtools.dialog_yesno(msg_header, '¿Borrarmos los archivos descargados? (completos)'):
            return
        log("##### erase_file_path: %s" % erase_file_path)
        for x in range(10):
            if filetools.isdir(erase_file_path):
                if erase_file_path != save_path_videos:
                    filetools.rmdirtree(erase_file_path)
                else:
                    break
            else:
                filetools.remove(erase_file_path)
            time.sleep(5)
            if not filetools.exists(erase_file_path):
                break


def call_torrent_via_web(mediaurl, torr_client):
    # Usado para llamar a los clientes externos de Torrents para automatizar la descarga de archivos que contienen .RAR
    logger.info()
    
    post = ''
    torrent_paths = torrent_dirs()
    local_host = {"quasar": ["http://localhost:65251/torrents/", "add?uri"], \
                  "elementum": ["%storrents/" % torrent_paths['ELEMENTUM_web'], "add"]}
    
    if torr_client == "quasar":
        uri = '%s%s=%s' % (local_host[torr_client][0], local_host[torr_client][1], mediaurl)
    elif torr_client == "elementum":
        uri = '%s%s' % (local_host[torr_client][0], local_host[torr_client][1])
        post = 'uri=%s&file=null&all=1' % mediaurl

    if post:
        response = httptools.downloadpage(uri, post=post, timeout=5, alfa_s=True, ignore_response_code=True)
    else:
        response = httptools.downloadpage(uri, timeout=5, alfa_s=True, ignore_response_code=True)

    if not response.sucess:
        logger.error('Error %s al acceder al la web de %s' % (str(response.code), torr_client.upper()))
    return response.sucess


def get_tclient_data(folder, torr_client, elementum_port=65220, delete=False):
    # Monitoriza el estado de descarga del torrent en Quasar y Elementum

    local_host = {"quasar": "http://localhost:65251/torrents/", "elementum": "http://localhost:%s/torrents/" % elementum_port}
    torr = ''
    torr_id = ''
    x = 0
    y = ''
    
    if torr_client not in str(local_host):
        log('##### Servicio para %s no disponible' % (torr_client))
        return '', '', 0
        
    if not folder:
        log('##### Título no disponible')
        return '', '', 0
    
    try:
        data = httptools.downloadpage(local_host[torr_client], timeout=5, alfa_s=True).data
        if not data:
            log('##### Servicio de %s no disponible: %s' % (torr_client, local_host[torr_client]))
            return '', local_host[torr_client], 0

        data = jsontools.load(data)
        data = data['items']
        for x, torr in enumerate(data):
            if not folder in torr['label']:
                continue
            if "elementum" in torr_client:
                torr_id = scrapertools.find_single_match(str(torr), 'torrents\/move\/(.*?)\)')
            if torr_id:
                y = torr_id
            else:
                y = x
            if delete:
                data = httptools.downloadpage('%sdelete/%s' % (local_host[torr_client], y), timeout=5,
                                              alfa_s=True, ignore_response_code=True).data
                time.sleep(1)
            break
        else:
            return '', local_host[torr_client], -1
    except:
        log(traceback.format_exc(1))
        return '', local_host[torr_client], 0

    return torr, local_host[torr_client], y


def torrent_dirs():
    
    torrent_options = []
    torrent_options.append("Cliente interno BT")
    torrent_options.append("Cliente interno MCT")
    torrent_options.extend(platformtools.torrent_client_installed(show_tuple=False))
    torrent_paths = {
                     'TORR_opt': 0,
                     'TORR_client': '',
                     'TORR_libtorrent_path': '',
                     'TORR_unrar_path': '',
                     'TORR_background_download': True,
                     'TORR_rar_unpack': True,
                     'BT': '',
                     'BT_torrents': '',
                     'BT_buffer': 0,
                     'MCT': '',
                     'MCT_torrents': '',
                     'MCT_buffer': 0,
                     'TORRENTER': '',
                     'TORRENTER_torrents': '',
                     'TORRENTER_buffer': 0,
                     'QUASAR': '',
                     'QUASAR_torrents': '',
                     'QUASAR_buffer': 0,
                     'QUASAR_port': 65251,
                     'QUASAR_web': 'http://localhost:65251/',
                     'ELEMENTUM': '',
                     'ELEMENTUM_torrents': '',
                     'ELEMENTUM_buffer': 0,
                     'ELEMENTUM_memory_size': 0,
                     'ELEMENTUM_port': 65220,
                     'ELEMENTUM_web': 'http://localhost:',
                     'TORRENTER': '',
                     'TORRENTER_torrents': '',
                     'TORRENTER_buffer': 0,
                     'TORRENTER_web': ''
                    }
    
    torrent_paths['TORR_opt'] = config.get_setting("torrent_client", server="torrent", default=0)
    if torrent_paths['TORR_opt'] > 0 and torrent_paths['TORR_opt'] <= len(torrent_options):
        torrent_paths['TORR_client'] = scrapertools.find_single_match(torrent_options[torrent_paths['TORR_opt']-1], ':\s*(\w+)').lower()
    if torrent_paths['TORR_opt'] == 1: torrent_paths['TORR_client'] = 'BT'
    if torrent_paths['TORR_opt'] == 2: torrent_paths['TORR_client'] = 'MCT'
    torrent_paths['TORR_libtorrent_path'] = config.get_setting("libtorrent_path", server="torrent", default='')
    torrent_paths['TORR_unrar_path'] = config.get_setting("unrar_path", server="torrent", default='')
    torrent_paths['TORR_background_download'] = config.get_setting("mct_background_download", server="torrent", default=True)
    torrent_paths['TORR_rar_unpack'] = config.get_setting("mct_rar_unpack", server="torrent", default=True)
    torr_client = ''
    
    for torr_client_g in torrent_options:
        # Localizamos el path de descarga del .torrent y la carpeta de almacenamiento de los archivos .torrent
        if 'BT' in torr_client_g:
            torr_client = 'BT'
        elif 'MCT' in torr_client_g:
            torr_client = 'MCT'
        else:
            torr_client = scrapertools.find_single_match(torr_client_g, ':\s*(\w+)').lower()
        __settings__ = ''
        
        if torr_client != 'BT' and torr_client != 'MCT':
            __settings__ = xbmcaddon.Addon(id="plugin.video.%s" % torr_client)  # Apunta settings del cliente torrent externo
        if torr_client == 'BT'and str(config.get_setting("bt_download_path", \
                            server="torrent", default='')):
            if torrent_paths['TORR_libtorrent_path']:
                torrent_paths['BT'] = filetools.join(str(config.get_setting("bt_download_path", \
                            server="torrent", default='')), 'BT-torrents')
                torrent_paths['BT_torrents'] = filetools.join(torrent_paths['BT'], '.cache')
                torrent_paths['BT_buffer'] = config.get_setting("bt_buffer", server="torrent", default=50)
        elif torr_client == 'MCT' and str(config.get_setting("mct_download_path", \
                            server="torrent", default='')):
            if torrent_paths['TORR_libtorrent_path']:
                torrent_paths['MCT'] = filetools.join(str(config.get_setting("mct_download_path", \
                            server="torrent", default='')), 'MCT-torrent-videos')
                torrent_paths['MCT_torrents'] = filetools.join(str(config.get_setting("mct_download_path", \
                            server="torrent", default='')), 'MCT-torrents')
                torrent_paths['MCT_buffer'] = config.get_setting("mct_buffer", server="torrent", default=50)
        elif 'torrenter' in torr_client.lower():
            torrent_paths[torr_client.upper()] = str(filetools.join(xbmc.translatePath(__settings__.getSetting('storage')),  "Torrenter"))
            if not torrent_paths[torr_client.upper()]:
                torrent_paths[torr_client.upper()] = str(filetools.join(xbmc.translatePath("special://home/"), \
                                       "cache", "xbmcup", "plugin.video.torrenter", "Torrenter"))
            torrent_paths[torr_client.upper()+'_torrents'] = filetools.join(torrent_paths[torr_client.upper()], 'torrents')
            torrent_paths[torr_client.upper()+'_buffer'] = __settings__.getSetting('pre_buffer_bytes')
        elif torr_client in ['quasar', 'elementum']:
            try:
                if not __settings__: continue
                torrent_paths[torr_client.upper()] = str(xbmc.translatePath(__settings__.getSetting('download_path')))
                torrent_paths[torr_client.upper() + '_torrents'] = filetools.join(torrent_paths[torr_client.upper()], 'torrents')
                torrent_paths[torr_client.upper() + '_buffer'] = __settings__.getSetting('buffer_size')
                if 'elementum' in torr_client.lower():
                    torrent_paths['ELEMENTUM_torrents'] = str(xbmc.translatePath(__settings__.getSetting('torrents_path')))
                    torrent_paths['ELEMENTUM_port'] = __settings__.getSetting('remote_port')
                    torrent_paths['ELEMENTUM_web'] = '%s%s/' % (torrent_paths['ELEMENTUM_web'], \
                                str(torrent_paths['ELEMENTUM_port']))
                    if __settings__.getSetting('download_storage') == '1':
                        torrent_paths['ELEMENTUM'] = 'Memory'
                        if __settings__.getSetting('memory_size'):
                            torrent_paths['ELEMENTUM_memory_size'] = __settings__.getSetting('memory_size')

            except:
                logger.error(traceback.format_exc(1))
        else:
            torrent_paths[torr_client.upper()] = ''
            torrent_paths[torr_client.upper() + '_torrents'] = ''
            torrent_paths[torr_client.upper() + '_buffer'] = 0
            torrent_paths[torr_client.upper() + '_web'] = ''
    
    if not torrent_paths['QUASAR']: torrent_paths['QUASAR_web'] = ''
    if not torrent_paths['ELEMENTUM']: torrent_paths['ELEMENTUM_web'] = ''
    
    #logger.debug(torrent_paths)
    
    return torrent_paths


def update_control(item):
    logger.info(
        "contentAction: %s | contentChannel: %s | downloadProgress: %s | url: %s" % \
                    (item.contentAction, item.contentChannel, item.downloadProgress, item.url))

    file = False
    
    # Crea un punto de control para gestionar las descargas Torrents de forma centralizada
    if not item.downloadProgress and not item.path.endswith('.json'):
        from lib import generictools
        item.downloadQueued = 0
        item.downloadProgress = 1
        item.downloadSize = 0
        item.downloadCompleted = 0
        item.downloadStatus = 5
        if not item.downloadServer:
            item.downloadServer = {"url": item.url, "server": item.server}
        if not item.contentThumbnail:
            item.contentThumbnail = item.thumbnail
        item.path = str(time.time()) + ".json"
        item_control = item.clone()
        item_control.server = 'torrent'
        item_control.contentAction = 'play'
        if item.category:
            item_control.contentChannel = generictools.verify_channel(item.category.lower())
        else:
            item_control.contentChannel = generictools.verify_channel(item.channel)
        item_control.action = 'menu'
        item_control.channel = 'downloads'
        item_control.url = item.url_control
        item_control.url_control = item.url
        if item_control.strm_path and item.server == 'torrent':
            if item_control.contentType == 'movie':
                PATH = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_movies"))
            else:
                PATH = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
            item_control.strm_path = item_control.strm_path.replace(PATH, '')
        file = True
    else:
        path = filetools.join(config.get_setting("downloadlistpath"), item.path)
        if path.endswith('.json') and filetools.exists(path):
            item_control = Item().fromjson(filetools.read(path))
            file = True
            item_control.server = 'torrent'
            item_control.action = 'menu'
            item_control.channel = 'downloads'
            item_control.contentAction = 'play'
            item_control.downloadQueued = item.downloadQueued
            item_control.downloadStatus = item.downloadStatus
            item_control.downloadCompleted = item.downloadCompleted
            item_control.downloadProgress = item.downloadProgress
            item_control.downloadFilename = item.downloadFilename
            item_control.torr_folder = item.torr_folder
            if not item.url.startswith('magnet:'):
                item.downloadServer = {"url": item.url, "server": item.server}
            item_control.downloadServer = item.downloadServer
            item_control.url = item.url
            item_control.url_control = item.url_control

    if file:
        ret = filetools.write(filetools.join(config.get_setting("downloadlistpath"), item.path), item_control.tojson())
    elif not file or not ret:
        logger.error('No hay archivo de CONTROL: ' + path)


def mark_torrent_as_watched():
    logger.info()

    # Si hay descargas de BT o MCT inacabadas, se reinician la descargas secuencialmente
    try:
        threading.Thread(target=restart_unfinished_downloads).start()           # Creamos un Thread independiente
        time.sleep(3)                                                           # Dejamos terminar la inicialización...
    except:                                                                     # Si hay problemas de threading, salimos
        logger.error(traceback.format_exc())

    #Inicia un rastreo de vídeos decargados: marca los VISTOS y elimina los controles de los BORRADOS
    if config.get_platform(True)['num_version'] >= 14:
        monitor = xbmc.Monitor()                                                # For Kodi >= 14
    else:
        monitor = False                                                         # For Kodi < 14
    if monitor:
        while not monitor.abortRequested():

            check_seen_torrents()                                               # Ha las comprobaciones...
            if monitor.waitForAbort(900):                                       # ... cada 15'
                break
            
    else:
        while not xbmc.abortRequested:

            check_seen_torrents()                                               # Ha las comprobaciones...
            xbmc.sleep(900)                                                     # ... cada 15'


def restart_unfinished_downloads():
    logger.info()
    
    # Si hay una descarga de BT o MCT inacabada, se reinicia la descarga
    torrent_paths = torrent_dirs()
    DOWNLOAD_LIST_PATH = config.get_setting("downloadlistpath")
    LISTDIR = sorted(filetools.listdir(DOWNLOAD_LIST_PATH))
    
    for fichero in LISTDIR:
        if not filetools.exists(filetools.join(DOWNLOAD_LIST_PATH, fichero)):
            continue
        if fichero.endswith(".json"):
            item = Item(path=filetools.join(DOWNLOAD_LIST_PATH, fichero)).fromjson(
                filetools.read(filetools.join(DOWNLOAD_LIST_PATH, fichero)))
            
            torr_client = scrapertools.find_single_match(item.downloadFilename, '\:(\w+)\:')
            if not torr_client: torr_client = torrent_paths['TORR_client']
            if not torr_client or item.server != 'torrent':
                continue
            if torr_client not in ['BT', 'MCT', 'TORRENTER']:
                continue
            if item.downloadProgress == 0 and item.downloadQueued == 0:
                continue
            if item.downloadProgress < 4 or (item.downloadQueued > 0 \
                                and item.downloadProgress < 4) or item.downloadCompleted == 1:

                if item.downloadServer and 'url' in str(item.downloadServer):
                    new_torrent_url = filetools.join(torrent_paths[torr_client+'_torrents'], \
                                filetools.basename(item.downloadServer['url']).upper())
                    if filetools.exists(new_torrent_url):
                        item.downloadServer['url'] = new_torrent_url
                        item.url = new_torrent_url

                item.downloadProgress += 1
                item.downloadQueued += 1
                update_control(item)
                if item.contentType == 'movie':
                    title = item.infoLabels['title']
                else:
                    title = '%s: %sx%s' % (item.infoLabels['tvshowtitle'], item.infoLabels['season'], item.infoLabels['episode'])
                logger.info('RECUPERANDO descarga de %s: %s' % (torr_client, title))
                from channels import downloads
                ret = downloads.start_download(item)


def check_seen_torrents():
    
    # Localiza la correspondecia entre los vídeos descargados vistos en las áreas de descarga 
    # con los registros en las Videotecas de Kody y Alfa
    from platformcode import xbmc_videolibrary
    
    torrent_paths = torrent_dirs()
    DOWNLOAD_LIST_PATH = config.get_setting("downloadlistpath")
    MOVIES = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_movies"))
    SERIES = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
    LISTDIR = sorted(filetools.listdir(DOWNLOAD_LIST_PATH))
    
    for fichero in LISTDIR:
        if fichero.endswith(".json"):
            item = Item(path=filetools.join(DOWNLOAD_LIST_PATH, fichero)).fromjson(
                filetools.read(filetools.join(DOWNLOAD_LIST_PATH, fichero)))
 
            if not item.downloadStatus in [2, 4, 5] or not item.downloadFilename:
                continue
                
            filename = filetools.basename(scrapertools.find_single_match(item.downloadFilename, '(?:\:\w+\:\s*)?(.*?)$'))
            if item.contentType == 'movie':
                PATH = MOVIES
            else:
                PATH = SERIES
            if item.strm_path and filename:                                         # Si viene de Videoteca lo procesamos
                item.strm_path = filetools.join(PATH, item.strm_path)

                sql = 'select * from files where (strFilename like "%s" and playCount not like "")' % filename
                if config.is_xbmc():
                    nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)  # ejecución de la SQL
                    if nun_records > 0:                                             # si el vídeo está visto...
                        xbmc_videolibrary.mark_content_as_watched_on_kodi(item, 1)  # ... marcamos en Kodi como visto
                        item.downloadProgress = 100
                        if item.nfo:
                            xbmc_videolibrary.mark_content_as_watched_on_alfa(item.nfo) # ... y sincronizamos los Vistos de Kodi con Alfa
                            logger.info("Status: %s | Progress: %s | File: %s | Title: %s" % \
                                            (item.downloadStatus, item.downloadProgress, fichero, filename))
                            filename = ''

            if item.server == 'torrent':
                check_deleted_sessions(item, torrent_paths, DOWNLOAD_LIST_PATH, LISTDIR, fichero, filename)


def check_deleted_sessions(item, torrent_paths, DOWNLOAD_LIST_PATH, LISTDIR, fichero, filename=''):
    if filename:
        logger.info("Status: %s | Progress: %s | File: %s | Title: %s" % \
                            (item.downloadStatus, item.downloadProgress, fichero, filename))
    
    # Busca sesiones y archivos de descarga "zombies" y los borra
    torr_client = scrapertools.find_single_match(item.downloadFilename, '\:(\w+)\:')
    downloadFilename = scrapertools.find_single_match(item.downloadFilename, '\:\w+\:\s*(.*?)$')
    file = ''
    
    if torr_client not in ['BT', 'MCT', 'QUASAR', 'ELEMENTUM'] or torrent_paths[torr_client.upper()] == 'Memory':
        if item.downloadProgress in [100]:
            filetools.remove(filetools.join(DOWNLOAD_LIST_PATH, fichero), silent=True)
            logger.info('DELETED  %s: file: %s' % (torr_client, fichero))
        return

    if 'url' in str(item.downloadServer):
        if (item.downloadServer['url'].startswith('http') or item.downloadServer['url'].startswith('magnet:')) \
                        and not item.url_control.startswith('http:') and not item.url_control.startswith('magnet:'):
            filebase = filetools.basename(item.url_control)
        else:
            filebase = filetools.basename(item.downloadServer['url'])
        if item.downloadServer['url'].startswith(':BT:') or item.downloadServer['url'].startswith(':MCT:'):
            filebase = filebase.upper()
        file = filetools.join(torrent_paths[torr_client+'_torrents'], filebase)
    
    if item.downloadQueued > 0:
        return
    if item.downloadProgress in [1, 2, 3, 100] and (not torr_client or not downloadFilename):
        filetools.remove(filetools.join(DOWNLOAD_LIST_PATH, fichero), silent=True)
        logger.info('ERROR: %s' % (fichero))
        return
    if item.downloadProgress in [0]:
        return
    if item.downloadProgress in [1, 2, 3] and file and filetools.exists(file):
        return
    
    if not filetools.exists(filetools.join(torrent_paths[torr_client], downloadFilename)):
        
        filetools.remove(filetools.join(DOWNLOAD_LIST_PATH, fichero), silent=True)
        logger.info('ERASED %s: file: %s' % (torr_client, fichero))
        
        if torr_client in ['BT', 'MCT'] and file:
            filetools.remove(file, silent=True)
            return
        
        if item.torr_folder:
            folder = item.torr_folder
        else:
            folder = filetools.dirname(scrapertools.find_single_match(item.downloadFilename, '^\:\w+\:\s*(.*?)$'))
            folder = folder.replace('\\', '').replace('/', '')

        torr_client = torr_client.lower()
        if torr_client in ['quasar', 'elementum'] and folder:
            torr_data, deamon_url, index = get_tclient_data(folder, torr_client, torrent_paths['ELEMENTUM_port'], delete=True)


def mark_auto_as_watched(item):
    
    time_limit = time.time() + 150                                              #Marcamos el timepo máx. de buffering
    while not platformtools.is_playing() and time.time() < time_limit:          #Esperamos mientra buffera    
        time.sleep(5)                                                           #Repetimos cada intervalo
        #logger.debug(str(time_limit))
    if item.subtitle:
        time.sleep(5)
        xbmc_player.setSubtitles(item.subtitle)
        #subt = xbmcgui.ListItem(path=item.url, thumbnailImage=item.thumbnail)
        #subt.setSubtitles([item.subtitle])

    if item.strm_path and platformtools.is_playing():                           #Sólo si es de Videoteca
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)                            #Marcamos como visto al terminar
        #logger.debug("Llamado el marcado")


def wait_for_download(item, mediaurl, rar_files, torr_client, password='', size='', \
                      rar_control={}):
    logger.info()

    from subprocess import Popen, PIPE, STDOUT
    from lib import generictools
    
    torrent_paths = torrent_dirs()
    
    # Analizamos los archivos dentro del .torrent
    rar = False
    rar_names = []
    video_names = []
    rar_names_abs = []
    rar_file = ''
    folder = ''
    ret = ''
    
    if not rar_files and item.url.startswith('magnet:') and item.downloadServer \
                        and 'url' in str(item.downloadServer):
        for x in range(600):
            if filetools.exists(item.downloadServer['url']):
                break
            time.sleep(1)
            continue
        time.sleep(5)
        if filetools.exists(item.downloadServer['url']):
            for x in range(30):
                size, url, torrent_f, rar_files = generictools.get_torrent_size(item.downloadServer['url'], 
                            file_list=True, lookup=False, torrents_path=item.downloadServer['url'], 
                            local_torr=item.downloadServer['url'])
                if 'ERROR' not in size:
                    if rar_control:
                        rar_control['size'] = size
                    break
                time.sleep(5)

    if rar_control:
        for x, entry in enumerate(rar_control['rar_files']):
            if '__name' in entry:
                folder = rar_control['rar_files'][x]['__name']
                break
        rar_names = [rar_control['rar_names'][0]]
    else:
        for entry in rar_files:
            for file, path in list(entry.items()):
                if file == 'path' and '.rar' in str(path):
                    for file_r in path:
                        rar_names += [file_r]
                        rar = True
                elif file == 'path' and '.rar' not in str(path):
                    for file_r in path:
                        if os.path.splitext(file_r)[1] in extensions_list:
                            video_names += [file_r]
                elif file == '__name':
                    folder = path

    if not folder:                                                              # Si no se detecta el folder...
        return ('', '', '', rar_control)                                                 # ... no podemos hacer nada
    if rar_names: rar_names = sorted(rar_names)
    if rar_names:
        rar_file = '%s/%s' % (folder, rar_names[0])
        log("##### rar_file: %s" % rar_file)
    if len(rar_names) > 1:
        log("##### rar_names: %s" % str(rar_names))
    if video_names:
        video_name = video_names[0]
        if not rar_file: log("##### video_name: %s/%s" % (folder, video_name))
    else:
        video_name = ''
    if not rar_file and not video_name:
        log("##### video_name: %s" % (folder))

    # Localizamos el path de descarga del .torrent
    save_path_videos = torrent_paths[torr_client.upper()]
    if save_path_videos == 'Memory':                                            # Descarga en memoria?
        return ('', '', folder, rar_control)                                             # volvemos
    if not save_path_videos:                                                    # No hay path de descarga?
        return ('', '', folder, rar_control)                                             # Volvemos
    log("##### save_path_videos: %s" % save_path_videos)
    
    if item.url.startswith('magnet:'):
        item.downloadFilename = ':%s: %s' % (torr_client.upper(), filetools.join(folder, video_name))
        update_control(item)
    
    # Si es nueva descarga, ponemos un archivo de control para reiniciar el UNRar si ha habido cancelación de Kodi
    # Si ya existe el archivo (llamada), se reinicia el proceso de UNRar donde se quedó
    if rar_control:
        if 'downloading' not in rar_control['status']:
            log("##### Torrent DESCARGADO Anteriormente: %s" % str(folder))
            return (rar_file, save_path_videos, folder, rar_control)
    else:
        rar_control = {
                       'torr_client': torr_client,
                       'rar_files': rar_files,
                       'rar_names': rar_names,
                       'size': size,
                       'password': password,
                       'download_path': filetools.join(save_path_videos, folder),
                       'status': 'downloading',
                       'error': 0,
                       'error_msg': '',
                       'item': item.tourl(),
                       'mediaurl': mediaurl
                      }

    # Esperamos mientras el .torrent se descarga.  Verificamos si el .RAR está descargado al completo
    #if rar_file:
    #   platformtools.dialog_notification("Automatizando la extracción", "Te iremos guiando...", time=10000)
    if rar_file:
        ret = filetools.write(filetools.join(rar_control['download_path'], \
                            '_rar_control.json'), jsontools.dump(rar_control))
    
    # Plan A: usar el monitor del cliente torrent para ver el status de la descarga
    if torrent_paths[torr_client.upper()+'_web']:                               # Tiene web para monitorizar?
    
        loop = 3600                                                             # Loop de 10 horas hasta crear archivo
        wait_time = 10
        time.sleep(wait_time)
        fast = False
        if config.get_platform(True)['num_version'] >= 14:
            monitor = xbmc.Monitor()                                            # For Kodi >= 14
        else:
            monitor = None                                                      # For Kodi < 14

        for x in range(loop):
            if (monitor and monitor.abortRequested()) or (not monitor and xbmc.abortRequested):
                return ('', '', folder, rar_control)

            torr_data, deamon_url, index = get_tclient_data(folder, torr_client, torrent_paths['ELEMENTUM_port'])
            
            if not torr_data or not deamon_url:
                if rar_file and len(filetools.listdir(rar_control['download_path'], silent=True)) <= 1:
                    filetools.remove(filetools.join(rar_control['download_path'], '_rar_control.json'), silent=True)
                    filetools.rmdir(rar_control['download_path'], silent=True)
                return ('', '', folder, rar_control)                            # Volvemos

            if (torr_client in ['quasar'] or torr_client in ['elementum']) and not \
                            torr_data['label'].startswith('0.00%') and not fast and rar_file:
                platformtools.dialog_notification("Descarga RAR en curso", "Puedes realizar otras tareas. " + \
                        "Te iremos guiando...", time=10000)
                fast = True

            if not torr_data['label'].startswith('100.00%'):
                if not ret and rar_file:
                    ret = filetools.write(filetools.join(rar_control['download_path'], \
                                    '_rar_control.json'), jsontools.dump(rar_control))
                log("##### Descargado: %s, ID: %s" % (scrapertools.find_single_match(torr_data['label'], '(^.*?\%)'), index))
                time.sleep(wait_time)
                continue
            
            if rar_file: update_rar_control(rar_control['download_path'], status='downloaded')
            log("##### Torrent FINALIZADO: %s" % str(folder))
            return (rar_file, save_path_videos, folder, rar_control)
    
    
    # Plan B: monitorizar con UnRAR si los archivos se han desacargado por completo
    unrar_path = config.get_setting("unrar_path", server="torrent", default="")
    if not unrar_path or not rar_file:                                          # Si Unrar no está instalado o no es un RAR...
        return ('', '', folder, rar_control)                                             # ... no podemos hacer nada
        
    cmd = []
    for rar_name in rar_names:                                                  # Preparamos por si es un archivo multiparte
        cmd.append(['%s' % unrar_path, 'l', '%s' % filetools.join(save_path_videos, folder, rar_name)])
    
    creationflags = ''
    if xbmc.getCondVisibility("system.platform.Windows"):
        creationflags = 0x08000000
    loop = 30                                                                   # Loop inicial de 5 minutos hasta crear archivo
    wait_time = 10
    loop_change = 0
    loop_error = 6
    part_name = ''
    y = 0
    returncode = ''
    fast = False
    while rar:
        for x in range(loop):                                                   # Loop corto (5 min.) o largo (10 h.)
            if (monitor and monitor.abortRequested()) or (not monitor and xbmc.abortRequested):
                return ('', '', folder, rar_control)
            if not rar or loop_change > 0:
                loop = loop_change                                              # Paso de loop corto a largo
                loop_change = 0
                break
            try:
                responses = []
                for z, command in enumerate(cmd):                               # Se prueba por cada parte
                    if xbmc.getCondVisibility("system.platform.Windows"):
                        data_rar = Popen(command, bufsize=0, stdout=PIPE, stdin=PIPE, \
                                     stderr=STDOUT, creationflags=creationflags)
                    else:
                        data_rar = Popen(command, bufsize=0, stdout=PIPE, stdin=PIPE, \
                                     stderr=STDOUT)
                    out_, error_ = data_rar.communicate()
                    responses.append([z, str(data_rar.returncode), out_, error_])   # Se guarda la respuesta de cada parte
            except:
                logger.error(traceback.format_exc(1))                           # Error de incompatibilidad de UnRAR
                rar = False
                break
            else:
                dl_files = 0
                for z, returncode, out__, error__ in responses:                 # Analizamos las respuestas
                    if returncode == '0':                                       # Ya se ha descargado... parte ...
                        dl_files += 1
                        part_name = scrapertools.find_single_match(str(out__), '(\.part\d+.rar)')
                        log("##### Torrent descargando: %s, %s" % (part_name, str(returncode)))
                        if dl_files == len(cmd):                                # ... o todo
                            fast = True
                            rar = False
                            break                                                   # ... o sólo una parte
                    elif returncode == '10':                                    # archivo no existe
                        if loop != 30:                                          # Si el archivo es borrado durante el proceso ...
                            rar = False
                        break                                                   #... abortamos
                    elif returncode == '6':                                     # En proceso de descarga
                        y += 1
                        #if loop == 30 and y == len(responses):                  # Si es la primera vez en proceso ...
                        if loop == 30 and y == 1:                               # Si es la primera vez en proceso ...
                            if torr_client in ['quasar']:
                                platformtools.dialog_notification("Descarga en curso", "Puedes realizar otras tareas en Kodi mientrastanto. " + \
                                        "Te informaremos...", time=10000)
                            loop_change = 3600                                  # ... pasamos a un loop de 10 horas
                        elif loop <= 6:                                         # Recuerado el error desconocido
                            loop_change = 3600                                  # ... pasamos a un loop de 10 horas
                            loop_error = 6                                      # Restauramos loop_error por si acaso
                        break
                    elif returncode == '1':                                     # Ha alcanzado el fin de archivo ??? pasamos
                        part_name = scrapertools.find_single_match(str(out__), '(\.part\d+.rar)')
                        log("##### Torrent descargando: %s, %s" % (part_name, str(returncode)))
                    else:                                                       # No entendemos el error
                        loop_change = loop_error                                # ... pasamos a un loop de 1 minutos para reintentar
                        loop_error += -1
                        break                                                   #... abortamos
                
                if str(returncode) in ['0', '6', '10']:
                    log("##### Torrent descargando: %s" % str(returncode))
                else:
                    log("##### Torrent descargando: %s, %s" % (str(out__), str(returncode)))
                if not rar or fast:
                    fast = False
                    break
                time.sleep(wait_time)                                           # Esperamos un poco y volvemos a empezar
        else:
            rar = False
            break

    if str(returncode) == '0':
        log("##### Torrent FINALIZADO: %s" % str(returncode))
    else:
        rar_file = ''
        logger.error('##### Torrent NO DESCARGADO: %s, %s' % (str(out__), str(returncode)))
    
    return (rar_file, save_path_videos, folder, rar_control)


def extract_files(rar_file, save_path_videos, password, dp, item=None, \
                        torr_client=None, rar_control={}, size='RAR-', mediaurl=''):
    logger.info()
    
    from platformcode import custom_code
    
    if not rar_control:
        rar_control = {
                       'torr_client': torr_client,
                       'rar_files': [{"__name": "%s" % rar_file.split("/")[0]}],
                       'rar_names': [filetools.basename(rar_file)],
                       'size': size,
                       'password': password,
                       'download_path': filetools.join(save_path_videos, rar_file.split("/")[0]),
                       'status': 'downloaded',
                       'error': 0,
                       'error_msg': '',
                       'item': item.tourl(),
                       'mediaurl': mediaurl
                      }
    ret = filetools.write(filetools.join(rar_control['download_path'], '_rar_control.json'), jsontools.dump(rar_control))
    
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    sys.path.insert(0, config.get_setting("unrar_path", server="torrent", default="")\
                    .replace('/unrar', '').replace('\\unrar,exe', ''))
    
    import rarfile

    # Verificamos si hay path para UnRAR
    rarfile.UNRAR_TOOL = config.get_setting("unrar_path", server="torrent", default="")
    if not rarfile.UNRAR_TOOL:
        if xbmc.getCondVisibility("system.platform.Android"):
            rarfile.UNRAR_TOOL = xbmc.executebuiltin("StartAndroidActivity(com.rarlab.rar)")
        return rar_file, False, '', ''
    log("##### unrar_path: %s" % rarfile.UNRAR_TOOL)
    rarfile.DEFAULT_CHARSET = 'utf-8'
    
    # Preparamos un path alternativo más corto para no sobrepasar la longitud máxima
    video_path = ''
    if item:
        if item.contentType == 'movie':
            video_path = '%s-%s' % (item.contentTitle, item.infoLabels['tmdb_id'])
        else:
            video_path = '%s-%sx%s-%s' % (item.contentSerieName, item.contentSeason, \
                            item.contentEpisodeNumber, item.infoLabels['tmdb_id'])
        video_path = video_path.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o")\
                               .replace("ú", "u").replace("ü", "u").replace("ñ", "n")\
                               .replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O")\
                               .replace("Ú", "U").replace("Ü", "U").replace("Ñ", "N")
    
    # Renombramos el path dejado en la descarga a uno más corto
    rename_status = False
    org_rar_file = rar_file
    org_save_path_videos = save_path_videos
    if video_path and '/' in rar_file:
        log("##### rar_file: %s" % rar_file)
        rename_status, rar_file = rename_rar_dir(org_rar_file, org_save_path_videos, video_path, torr_client)

    # Calculamos el path para del RAR
    folders = []
    if "/" in rar_file:
        folders = rar_file.split("/")
        erase_file_path = filetools.join(save_path_videos, folders[0])
        file_path = save_path_videos
        for f in folders:
            file_path = filetools.join(file_path, f)
    else:
        file_path = save_path_videos
        erase_file_path = save_path_videos

    # Calculamos el path para la extracción
    if "/" in rar_file:
        folders = rar_file.split("/")
        for f in folders:
            if not '.rar' in f:
                save_path_videos = filetools.join(save_path_videos, f)
    save_path_videos = filetools.join(save_path_videos, 'Extracted')
    if not filetools.exists(save_path_videos): filetools.mkdir(save_path_videos)
    log("##### save_path_videos: %s" % save_path_videos)
    
    rar_control = update_rar_control(erase_file_path, status='UnRARing')

    # Permite hasta 5 pasadas de extracción de .RARs anidados
    platformtools.dialog_notification("Empezando extracción...", rar_file, time=5000)
    for x in range(5):
        try:
            if not PY3:
                archive = rarfile.RarFile(file_path.decode("utf8"))
            else:
                archive = rarfile.RarFile(file_path)
        except:
            log("##### ERROR en Archivo rar: %s" % rar_file)
            log("##### ERROR en Carpeta del rar: %s" % file_path)
            log(traceback.format_exc())
            error_msg = "Error al abrir el RAR"
            error_msg1 = "Comprueba el log para más detalles"
            platformtools.dialog_notification(error_msg, error_msg1)
            rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
            return rar_file, False, '', ''

        # Analizamos si es necesaria una contraseña, que debería estar en item.password
        if archive.needs_password():
            if not password:
                pass_path = filetools.split(file_path)[0]
                password = last_password_search(pass_path, erase_file_path)
            if not password :
                password = platformtools.dialog_input(heading="Introduce la contraseña (Mira en %s)" % pass_path)
                if not password:
                    error_msg = "No se ha introducido la contraseña"
                    rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
                    dp.close()
                    return custom_code.reactivate_unrar(init=False, mute=False)
            archive.setpassword(password)
            log("##### Password rar: %s" % password)

        # Miramos el contenido del RAR a extraer
        files = archive.infolist()
        info = []
        for idx, i in enumerate(files):
            if i.file_size == 0:
                files.pop(idx)
                continue
            filename = i.filename
            if "/" in filename:
                filename = filename.rsplit("/", 1)[1]

            info.append("%s - %.2f MB" % (filename, i.file_size / 1048576.0))
        if info:
            info.append("Extraer todo sin reproducir")
        else:
            error_msg = "El RAR está vacío"
            error_msg1 = "O no contiene archivos válidos"
            platformtools.dialog_notification(error_msg, error_msg1)
            rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
            dp.close()
            return custom_code.reactivate_unrar(init=False, mute=False)

        # Seleccionamos extraer TODOS los archivos del RAR
        #selection = xbmcgui.Dialog().select("Selecciona el fichero a extraer y reproducir", info)
        selection = len(info) - 1
        if selection < 0:
            error_msg = "El RAR está vacío"
            platformtools.dialog_notification(error_msg)
            rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
            return rar_file, False, '', ''
        else:
            try:
                log("##### RAR Extract INI #####")
                if selection == len(info) - 1:
                    log("##### rar_file 1: %s" % file_path)
                    log("##### save_path_videos 1: %s" % save_path_videos)
                    dp.update(99, "Extrayendo archivos...", "Espera unos minutos....")
                    archive.extractall(save_path_videos)
                else:
                    log("##### rar_file 2: %s" % file_path)
                    log("##### save_path_videos 2: %s" % save_path_videos)
                    dp.update(99, "Espera unos minutos....", "Extrayendo archivo... %s" % info[selection])
                    archive.extract(files[selection], save_path_videos)
                log("##### RAR Extract END #####")
            except (rarfile.RarWrongPassword, rarfile.RarCRCError):
                log(traceback.format_exc(1))
                error_msg = "Error al extraer"
                error_msg1 = "Contraseña incorrecta"
                platformtools.dialog_notification(error_msg, error_msg1)
                rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg1, status='ERROR')
                dp.close()
                return custom_code.reactivate_unrar(init=False, mute=False)
            except rarfile.BadRarFile:
                log(traceback.format_exc(1))
                error_msg = "Error al extraer"
                error_msg1 = "Archivo rar con errores"
                platformtools.dialog_notification(error_msg, error_msg1)
                rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg1, status='ERROR')
                #return rar_file, False, '', erase_file_path
                dp.close()
                return custom_code.reactivate_unrar(init=False, mute=False)
            except:
                log(traceback.format_exc(1))
                error_msg = "Error al extraer"
                error_msg1 = "Comprueba el log para más detalles"
                platformtools.dialog_notification(error_msg, error_msg1)
                rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
                dp.close()
                return custom_code.reactivate_unrar(init=False, mute=False)

            extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg',
                               '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg',
                               '.mpe', '.mp4', '.ogg', '.wmv']
            
            # Localizamos el path donde se ha dejado la extracción
            folder = True
            file_result = filetools.listdir(save_path_videos)
            while folder:
                for file_r in file_result:
                    if filetools.isdir(filetools.join(save_path_videos, file_r)):
                        file_result_alt = filetools.listdir(filetools.join(save_path_videos, file_r))
                        if file_result_alt:
                            file_result = file_result_alt
                            save_path_videos = filetools.join(save_path_videos, file_r)
                        else:
                            folder = False
                        break
                else:
                    folder = False

            # Si hay RARs anidados, ajustamos los paths para la siguiente pasada
            if '.rar' in str(file_result):
                for file_r in sorted(file_result):
                    if '.rar' in file_r:
                        rar_file = file_r
                        file_path = str(filetools.join(save_path_videos, rar_file))
                        save_path_videos = filetools.join(save_path_videos, 'Extracted')
                        rar_control = update_rar_control(erase_file_path, newextract=(rar_file))
                        if not filetools.exists(save_path_videos): filetools.mkdir(save_path_videos)
                        platformtools.dialog_notification("Siguiente extracción...", rar_file, time=5000)
                        break
            
            # Si ya se ha extraido todo, preparamos el retorno            
            else:
                video_list = []
                for file_r in file_result:
                    if os.path.splitext(file_r)[1] in extensions_list:
                        video_list += [file_r]
                if len(video_list) == 0:
                    error_msg = "El rar está vacío"
                    error_msg1 = "O no contiene archivos válidos"
                    platformtools.dialog_notification(error_msg, error_msg1)
                    rar_control = update_rar_control(erase_file_path, error=True, error_msg=error_msg, status='ERROR')
                    dp.close()
                    return custom_code.reactivate_unrar(init=False, mute=False)
                else:
                    log("##### Archivo extraído: %s" % video_list[0])
                    platformtools.dialog_notification("Archivo extraído...", video_list[0], time=10000)
                    log("##### Archivo remove: %s" % file_path)
                    #rar_control = update_rar_control(erase_file_path, status='DONE')
                    ret = filetools.remove(filetools.join(erase_file_path, '_rar_control.json'), silent=True)
                    return str(video_list[0]), True, save_path_videos, erase_file_path


def rename_rar_dir(rar_file, save_path_videos, video_path, torr_client):
    logger.info()

    rename_status = False
    if config.get_platform(True)['num_version'] >= 14:
        monitor = xbmc.Monitor()                                                # For Kodi >= 14
    else:
        monitor = None
    folders = rar_file.split("/")
    if filetools.exists(filetools.join(save_path_videos, folders[0])) and video_path not in folders[0]:
        if not PY3:
            src = filetools.join(save_path_videos, folders[0]).decode("utf8")
            dst = filetools.join(save_path_videos, video_path).decode("utf8")
            dst_file = video_path.decode("utf8")
        else:
            src = filetools.join(save_path_videos, folders[0])
            dst = filetools.join(save_path_videos, video_path)
            dst_file = video_path
        
        for x in range(20):
            if (monitor and monitor.abortRequested()) or (not monitor and xbmc.abortRequested):
                return rename_status, rar_file
            xbmc.sleep(1000)
            
            # Se para la actividad para que libere los archivos descargados
            if torr_client in ['quasar', 'elementum']:
                torr_data, deamon_url, index = get_tclient_data(folders[0], torr_client)
                if torr_data and deamon_url:
                    log("##### Client URL: %s" % '%spause/%s' % (deamon_url, index))
                    data = httptools.downloadpage('%spause/%s' % (deamon_url, index), timeout=5, alfa_s=True).data

            try:
                if filetools.exists(src):
                    filetools.rename(src, dst_file, silent=True, strict=True)
                elif not filetools.exists(dst_file):
                    break
            except:
                log("##### Rename ERROR: SRC: %s" % src)
                log(traceback.format_exc(1))
            else:
                if filetools.exists(dst):
                    log("##### Renamed: SRC: %s" % src)
                    log("##### TO: DST: %s" % dst)
                    rar_file = video_path + '/' + folders[1]
                    rename_status = True
                    update_rar_control(dst, newpath=dst)
                    break
                    
    return rename_status, rar_file


def last_password_search(pass_path, erase_file_path=''):
    logger.info(pass_path)
    
    if not erase_file_path:
        erase_file_path = pass_path

    # Busca en el Path de extracción si hay algún archivo que contenga la URL donde pueda estar la CONTRASEÑA
    password = ''
    patron_url = '(http.*\:\/\/(?:www.)?\w+\.\w+\/.*?)[\n|\r|$]'
    patron_pass = '<input\s*type="text"\s*id="txt_password"\s*name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"'
    
    try:
        pass_path_list = filetools.listdir(pass_path)
        for file in pass_path_list:
            if 'contrase' in file.lower() and '.rar' not in file:
                file_pass = filetools.read(filetools.join(pass_path, file))
                url = scrapertools.find_single_match(file_pass, patron_url)
                if url:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url).data)
                    password = scrapertools.find_single_match(data, patron_pass)
            if password:
                update_rar_control(erase_file_path, password=password, status='UnRARing: Password update')
                break
    except:
        log(traceback.format_exc(1))
    
    log("##### Contraseña extraída: %s" % password)
    return password
    
    
def update_rar_control(path, newpath='', newextract='', password='', error='', error_msg='', status=''):
    #logger.info('path: %s, newpath: %s, newextract: %s, password: %s, error: %s, error_msg: %s, status: %s'% 
    #            (path, newpath, newextract, password, str(error), error_msg, status))
    try:
        rar_control = {}
        rar_control = jsontools.load(filetools.read(filetools.join(path, '_rar_control.json')))
        if rar_control:
            if newpath: 
                rar_control['download_path'] = newpath
                for x, entry in enumerate(rar_control['rar_files']):
                    if '__name' in entry:
                        rar_control['rar_files'][x]['__name'] = filetools.basename(newpath)
                        break
            if newextract:
                for x, entry in enumerate(rar_control['rar_files']):
                    if '__name' in entry:
                        #rar_control['rar_files'][x]['__name'] = filetools.join(rar_control['rar_files'][x]['__name'], 'Extracted')
                        rar_control['rar_files'][x]['__name'] = rar_control['rar_files'][x]['__name'] + '/Extracted'
                        break
                rar_control['rar_names'] = [newextract]
            if password: rar_control['password'] = password
            if error: rar_control['error'] += 1
            if error_msg: rar_control['error_msg'] = error_msg
            if status and status not in rar_control['status']: rar_control['status'] = status
            ret = filetools.write(filetools.join(rar_control['download_path'], '_rar_control.json'), \
                        jsontools.dump(rar_control))
            logger.debug('%s, %s, %s, %s, %s, %s' % (rar_control['download_path'], \
                        rar_control['rar_names'][0], rar_control['password'], \
                        str(rar_control['error']), rar_control['error_msg'], rar_control['status']))
    except:
        log(traceback.format_exc(1))
        
    return rar_control


def import_libtorrent(LIBTORRENT_PATH):
    logger.info(LIBTORRENT_PATH)

    e = ''
    e1 = ''
    e2 = ''
    fp = ''
    pathname = ''
    description = ''
    lt = ''

    try:
        sys.path.insert(0, LIBTORRENT_PATH)
        if LIBTORRENT_PATH:
            try:
                if not xbmc.getCondVisibility("system.platform.android"):
                    import libtorrent as lt
                    pathname = LIBTORRENT_PATH
                else:
                    import imp
                    from ctypes import CDLL
                    dll_path = os.path.join(LIBTORRENT_PATH, 'liblibtorrent.so')
                    liblibtorrent = CDLL(dll_path)
                    
                    path_list = [LIBTORRENT_PATH, xbmc.translatePath('special://xbmc')]
                    fp, pathname, description = imp.find_module('libtorrent', path_list)
                    
                    # Esta parte no funciona en Android.  Por algún motivo da el error "dlopen failed: library "liblibtorrent.so" not found"
                    # Hay que encontrar un hack para rodear el problema.  Lo siguiente ha sido probado sin éxito:
                    #if fp: fp.close()
                    #fp = filetools.file_open(filetools.join(LIBTORRENT_PATH, 'libtorrent.so'), mode='rb')  # Usa XbmcVFS
                    #fp = open(os.path.join(LIBTORRENT_PATH, 'libtorrent.so'), 'rb')
                    
                    try:
                        lt = imp.load_module('libtorrent', fp, pathname, description)
                    finally:
                        if fp: fp.close()
                
            except Exception as e1:
                logger.error(traceback.format_exc(1))
                log('fp = ' + str(fp))
                log('pathname = ' + str(pathname))
                log('description = ' + str(description))
                if fp: fp.close()
                from lib.python_libtorrent.python_libtorrent import get_libtorrent
                lt = get_libtorrent()

    except Exception as e2:
        try:
            logger.error(traceback.format_exc())
            if fp: fp.close()
            e = e1 or e2
            ok = platformtools.dialog_ok('ERROR en el cliente Interno Libtorrent', \
                        'Módulo no encontrado o imcompatible con el dispositivo.', \
                        'Reporte el fallo adjuntando un "log" %s' % str(e2))
        except:
            pass
    
    try:
        if not e1 and e2: e1 = e2
    except:
        try:
            if e2:
                e1 = e2
            else:
                e1 = ''
                e2 = ''
        except:
            e1 = ''
            e2 = ''
    
    return lt, e, e1, e2


def log(texto):
    try:
        xbmc.log(texto, xbmc.LOGNOTICE)
    except:
        pass
    