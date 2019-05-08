# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Localiza las variables de entorno más habituales (kodi)
# ------------------------------------------------------------

import xbmc
import xbmcaddon

import os
import subprocess
import re
import platform
import sys
import ctypes
import traceback

from core import filetools, scrapertools
from platformcode import logger, config

PLUGIN_NAME = "alfa"
__settings__ = xbmcaddon.Addon(id="plugin.video." + PLUGIN_NAME)
__language__ = __settings__.getLocalizedString


def get_environment():
    """
    Devuelve las variables de entorno del OS, de Kodi y de Alfa más habituales,
    necesarias para el diagnóstico de fallos 
    """

    try:
        import base64
        import ast
        
        environment = config.get_platform(full_version=True)
        environment['num_version'] = str(environment['num_version'])
        environment['python_version'] = str(platform.python_version())
        
        environment['os_release'] = str(platform.release())
        if xbmc.getCondVisibility("system.platform.Windows"):
            try:
                if platform._syscmd_ver()[2]:
                    environment['os_release'] = str(platform._syscmd_ver()[2])
            except:
                pass
        environment['prod_model'] = ''
        if xbmc.getCondVisibility("system.platform.Android"):
            environment['os_name'] = 'Android'
            try:
                for label_a in subprocess.check_output('getprop').split('\n'):
                    if 'build.version.release' in label_a:
                        environment['os_release'] = str(scrapertools.find_single_match(label_a, ':\s*\[(.*?)\]$'))
                    if 'product.model' in label_a:
                        environment['prod_model'] = str(scrapertools.find_single_match(label_a, ':\s*\[(.*?)\]$'))
            except:
                try:
                    for label_a in filetools.read(os.environ['ANDROID_ROOT'] + '/build.prop').split():
                        if 'build.version.release' in label_a:
                            environment['os_release'] = str(scrapertools.find_single_match(label_a, '=(.*?)$'))
                        if 'product.model' in label_a:
                            environment['prod_model'] = str(scrapertools.find_single_match(label_a, '=(.*?)$'))
                except:
                    pass
        
        elif xbmc.getCondVisibility("system.platform.Linux.RaspberryPi"):
            environment['os_name'] = 'RaspberryPi'
        else:
            environment['os_name'] = str(platform.system())

        environment['machine'] = str(platform.machine())
        environment['architecture'] = str(sys.maxsize > 2 ** 32 and "64-bit" or "32-bit")
        environment['language'] = str(xbmc.getInfoLabel('System.Language'))

        environment['cpu_usage'] = str(xbmc.getInfoLabel('System.CpuUsage'))
        
        environment['mem_total'] = str(xbmc.getInfoLabel('System.Memory(total)')).replace('MB', '').replace('KB', '')
        environment['mem_free'] = str(xbmc.getInfoLabel('System.Memory(free)')).replace('MB', '').replace('KB', '')
        if not environment['mem_total'] or not environment['mem_free']:
            try:
                if environment['os_name'].lower() == 'windows':
                    kernel32 = ctypes.windll.kernel32
                    c_ulong = ctypes.c_ulong
                    c_ulonglong = ctypes.c_ulonglong
                    class MEMORYSTATUS(ctypes.Structure):
                        _fields_ = [
                            ('dwLength', c_ulong),
                            ('dwMemoryLoad', c_ulong),
                            ('dwTotalPhys', c_ulonglong),
                            ('dwAvailPhys', c_ulonglong),
                            ('dwTotalPageFile', c_ulonglong),
                            ('dwAvailPageFile', c_ulonglong),
                            ('dwTotalVirtual', c_ulonglong),
                            ('dwAvailVirtual', c_ulonglong),
                            ('availExtendedVirtual', c_ulonglong)
                        ]
                 
                    memoryStatus = MEMORYSTATUS()
                    memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
                    kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))
                    environment['mem_total'] = str(int(memoryStatus.dwTotalPhys) / (1024**2))
                    environment['mem_free'] = str(int(memoryStatus.dwAvailPhys) / (1024**2))

                else:
                    with open('/proc/meminfo') as f:
                        meminfo = f.read()
                    environment['mem_total'] = str(int(re.search(r'MemTotal:\s+(\d+)', meminfo).groups()[0]) / 1024)
                    environment['mem_free'] = str(int(re.search(r'MemAvailable:\s+(\d+)', meminfo).groups()[0]) / 1024)
            except:
                environment['mem_total'] = ''
                environment['mem_free'] = ''
            
        try:
            environment['kodi_buffer'] = '20'
            environment['kodi_bmode'] = '0'
            environment['kodi_rfactor'] = '4.0'
            if filetools.exists(filetools.join(xbmc.translatePath("special://userdata"), "advancedsettings.xml")):
                advancedsettings = filetools.read(filetools.join(xbmc.translatePath("special://userdata"), 
                                "advancedsettings.xml")).split('\n')
                for label_a in advancedsettings:
                    if 'memorysize' in label_a:
                        environment['kodi_buffer'] = str(int(scrapertools.find_single_match
                                (label_a, '>(\d+)<\/')) / 1024**2)
                    if 'buffermode' in label_a:
                        environment['kodi_bmode'] = str(scrapertools.find_single_match
                                (label_a, '>(\d+)<\/'))
                    if 'readfactor' in label_a:
                        environment['kodi_rfactor'] = str(scrapertools.find_single_match
                                (label_a, '>(.*?)<\/'))
        except:
            pass
        
        environment['userdata_path'] = str(xbmc.translatePath(config.get_data_path()))
        try:
            if environment['os_name'].lower() == 'windows':
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['userdata_path']), 
                                None, None, ctypes.pointer(free_bytes))
                environment['userdata_free'] = str(round(float(free_bytes.value) / (1024**3), 3))
            else:
                disk_space = os.statvfs(environment['userdata_path'])
                if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
                environment['userdata_free'] = str(round((float(disk_space.f_bavail) / \
                                (1024**3)) * float(disk_space.f_frsize), 3))
        except:
            environment['userdata_free'] = '?'

        try:
            environment['videolab_series'] = '?'
            environment['videolab_episodios'] = '?'
            environment['videolab_pelis'] = '?'
            environment['videolab_path'] = str(xbmc.translatePath(config.get_videolibrary_path()))
            if filetools.exists(filetools.join(environment['videolab_path'], \
                                config.get_setting("folder_tvshows"))):
                environment['videolab_series'] = str(len(filetools.listdir(filetools.join(environment['videolab_path'], \
                                config.get_setting("folder_tvshows")))))
                counter = 0
                for root, folders, files in filetools.walk(filetools.join(environment['videolab_path'], \
                                    config.get_setting("folder_tvshows"))):
                    for file in files:
                        if file.endswith('.strm'): counter += 1
                environment['videolab_episodios'] = str(counter)
            if filetools.exists(filetools.join(environment['videolab_path'], \
                                config.get_setting("folder_movies"))):
                environment['videolab_pelis'] = str(len(filetools.listdir(filetools.join(environment['videolab_path'], \
                                config.get_setting("folder_movies")))))
        except:
            pass
        try:
            video_updates = ['No', 'Inicio', 'Una vez', 'Inicio+Una vez']
            environment['videolab_update'] = str(video_updates[config.get_setting("update", "videolibrary")])
        except:
            environment['videolab_update'] = '?'
        try:
            if environment['os_name'].lower() == 'windows':
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['videolab_path']), 
                                None, None, ctypes.pointer(free_bytes))
                environment['videolab_free'] = str(round(float(free_bytes.value) / (1024**3), 3))
            else:
                disk_space = os.statvfs(environment['videolab_path'])
                if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
                environment['videolab_free'] = str(round((float(disk_space.f_bavail) / \
                                (1024**3)) * float(disk_space.f_frsize), 3))
        except:
            environment['videolab_free'] = '?'

        environment['torrentcli_name'] = ''
        environment['torrentcli_dload_path'] = ''
        environment['torrentcli_buffer'] = ''
        environment['torrentcli_dload_estrgy'] = ''
        environment['torrentcli_mem_size'] = ''
        environment['torrentcli_free'] = ''
        if config.get_setting("torrent_client", server="torrent") == 4:
            __settings__ = xbmcaddon.Addon(id="plugin.video.torrenter")
            environment['torrentcli_name'] = 'Torrenter'
            environment['torrentcli_dload_path'] = str(xbmc.translatePath(__settings__.getSetting('storage')))
            environment['torrentcli_buffer'] = str(__settings__.getSetting('pre_buffer_bytes'))
        elif config.get_setting("torrent_client", server="torrent") == 3:
            for client_torrent in ['quasar', 'elementum']:
                if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s" )' % client_torrent):
                    __settings__ = xbmcaddon.Addon(id="plugin.video.%s" % client_torrent)
                    environment['torrentcli_name'] = str(client_torrent)
                    environment['torrentcli_dload_path'] = str(xbmc.translatePath(__settings__.getSetting('download_path')))
                    environment['torrentcli_buffer'] = str(__settings__.getSetting('buffer_size'))
                    environment['torrentcli_dload_estrgy'] = str(__settings__.getSetting('download_storage'))
                    environment['torrentcli_mem_size'] = str(__settings__.getSetting('memory_size'))
        
        if environment['torrentcli_dload_path']:
            try:
                if environment['os_name'].lower() == 'windows':
                    free_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['torrentcli_dload_path']), 
                                None, None, ctypes.pointer(free_bytes))
                    environment['torrentcli_free'] = str(round(float(free_bytes.value) / \
                                (1024**3), 3))
                else:
                    disk_space = os.statvfs(environment['torrentcli_dload_path'])
                    if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
                    environment['torrentcli_free'] = str(round((float(disk_space.f_bavail) / \
                                (1024**3)) * float(disk_space.f_frsize), 3))
            except:
                environment['torrentcli_free'] = '?'

        environment['proxy_active'] = ''
        try:
            proxy_channel_bloqued_str = base64.b64decode(config.get_setting('proxy_channel_bloqued')).decode('utf-8')
            proxy_channel_bloqued = dict()
            proxy_channel_bloqued = ast.literal_eval(proxy_channel_bloqued_str)
            for channel_bloqued, proxy_active in proxy_channel_bloqued.items():
                if proxy_active == 'ON':
                    environment['proxy_active'] += channel_bloqued + ', '
        except:
            pass
        if not environment['proxy_active']: environment['proxy_active'] = 'OFF'
        environment['proxy_active'] = environment['proxy_active'].rstrip(', ')

        for root, folders, files in filetools.walk(xbmc.translatePath("special://logpath/")):
            for file in files:
                if file.lower() in ['kodi.log', 'jarvis.log', 'spmc.log', 'cemc.log', \
                                'mygica.log', 'wonderbox.log', 'leiapp,log', \
                                'leianmc.log', 'kodiapp.log', 'anmc.log', \
                                'latin-anmc.log']:
                    environment['log_path'] = str(filetools.join(root, file))
                    break
            else:
                environment['log_path'] = ''
            break
        
        if environment['log_path']:
            environment['log_size_bytes'] = str(filetools.getsize(environment['log_path']))
            environment['log_size'] = str(round(float(environment['log_size_bytes']) / \
                                (1024*1024), 3))
        else:
            environment['log_size_bytes'] = ''
            environment['log_size'] = ''
        
        environment['debug'] = str(config.get_setting('debug'))
        environment['addon_version'] = str(config.get_addon_version())

    except:
        logger.error(traceback.format_exc())
        environment = {}
        environment['log_size'] = ''
        environment['cpu_usage'] = ''
        environment['python_version'] = ''
        environment['log_path'] = ''
        environment['userdata_free'] = ''
        environment['mem_total'] = ''
        environment['torrentcli_mem_size'] = ''
        environment['torrentcli_dload_path'] = ''
        environment['torrentcli_dload_estrgy'] = ''
        environment['machine'] = ''
        environment['platform'] = ''
        environment['torrentcli_buffer'] = ''
        environment['videolab_path'] = ''
        environment['num_version'] = ''
        environment['os_name'] = ''
        environment['torrentcli_free'] = ''
        environment['video_db'] = ''
        environment['userdata_path'] = ''
        environment['log_size_bytes'] = ''
        environment['name_version'] = ''
        environment['language'] = ''
        environment['mem_free'] = ''
        environment['prod_model'] = ''
        environment['proxy_active'] = ''
        environment['architecture'] = ''
        environment['os_release'] = ''
        environment['videolab_free'] = ''
        environment['torrentcli_name'] = ''
        environment['kodi_buffer'] = ''
        environment['kodi_bmode'] = ''
        environment['kodi_rfactor'] = ''
        environment['videolab_series'] = ''
        environment['videolab_episodios'] = ''
        environment['videolab_pelis'] = ''
        environment['videolab_update'] = ''
        environment['debug'] = ''
        environment['addon_version'] = ''
        
    return environment


def list_env(environment={}):
    if not environment:
        environment = get_environment()
        
    if environment['debug'] == 'False':
        logger.log_enable(True)
    
    logger.info('----------------------------------------------')
    logger.info('Variables de entorno Alfa: ' + environment['addon_version'] + 
                ' Debug: ' + environment['debug'])
    logger.info("----------------------------------------------")

    logger.info(environment['os_name'] + ' ' + environment['prod_model'] + ' ' + 
                environment['os_release'] + ' ' + environment['machine'] + ' ' + 
                environment['architecture'] + ' ' + environment['language'])
    
    logger.info('Kodi ' + environment['num_version'] + ', Vídeo: ' + 
                environment['video_db'] + ', Python ' + environment['python_version'])
    
    if environment['cpu_usage']:
        logger.info('CPU: ' + environment['cpu_usage'])
    
    if environment['mem_total'] or environment['mem_free']: 
        logger.info('Memoria: Total: ' + environment['mem_total'] + ' MB / Disp.: ' + 
                    environment['mem_free'] + ' MB / Buffers: ' + 
                    str(int(environment['kodi_buffer']) * 3) + ' MB / Buffermode: ' + 
                    environment['kodi_bmode']  + ' / Readfactor: ' + 
                    environment['kodi_rfactor'])

    logger.info('Userdata: ' + environment['userdata_path'] + ' - Free: ' + 
                environment['userdata_free'] +  ' GB')
    
    logger.info('Videoteca: Series/Epis: ' + environment['videolab_series'] + '/' + 
                    environment['videolab_episodios'] + ' - Pelis: ' + 
                    environment['videolab_pelis'] + ' - Upd: ' + 
                    environment['videolab_update'] + ' - Path: ' + 
                    environment['videolab_path'] + ' - Free: ' + 
                    environment['videolab_free'] +  ' GB')
    
    if environment['torrentcli_name']:
        torrentcli_buffer = environment['torrentcli_buffer']
        if environment['torrentcli_mem_size']:
            torrentcli_buffer +=  ' MB / memoria: ' + environment['torrentcli_mem_size']
        logger.info('%s buffer: ' % environment['torrentcli_name'] + 
                    torrentcli_buffer + ' MB / descargas: ' + 
                    environment['torrentcli_dload_path'] + ' - Free: ' + 
                    environment['torrentcli_free'] +  ' GB')
    
    logger.info('Proxy: ' + environment['proxy_active'])
    
    logger.info('TAMAÑO del LOG: ' + environment['log_size'] + ' MB')
    logger.info("----------------------------------------------")
    
    if environment['debug'] == 'False':
        logger.log_enable(False)
    
    return environment
    
    
def paint_env(item, environment={}):
    from core.item import Item
    from channelselector import get_thumb
    
    if not environment:
        environment = get_environment()
    environment = list_env(environment)
    
    itemlist = []
    
    thumb = get_thumb("setting_0.png")
    
    cabecera = """\
    Muestra las [COLOR yellow]variables[/COLOR] del ecosistema de Kodi que puden ser relevantes para el diagnóstico de problema en Alfa:
        - Versión de Alfa con Fix
        - Debug Alfa: True/False
    """
    plataform = """\
    Muestra los datos especificos de la [COLOR yellow]plataforma[/COLOR] en la que está alojado Kodi:
        - Sistema Operativo
        - Modelo (opt)
        - Versión SO
        - Procesador
        - Aquitectura
        - Idioma de Kodi
    """
    kodi = """\
    Muestra los datos especificos de la instalación de [COLOR yellow]Kodi[/COLOR]:
        - Versión de Kodi
        - Base de Datos de Vídeo
        - Versión de Python
    """
    cpu = """\
    Muestra los datos consumo actual de [COLOR yellow]CPU(s)[/COLOR]
    """
    memoria = """\
    Muestra los datos del uso de [COLOR yellow]Memoria[/COLOR] del sistema:
        - Memoria total
        - Memoria disponible
        - en [COLOR yellow]Advancedsettings.xml[/COLOR]
             - Buffer de memoria 
                 configurado: 
                 para Kodi: 3 x valor de 
                 <memorysize>
             - Buffermode: cachea: 
                 * Internet (0, 2)
                 * También local (1)
                 * No Buffer (3)
             - Readfactor: readfactor * 
                 avg bitrate vídeo
    """
    userdata = """\
    Muestra los datos del "path" de [COLOR yellow]Userdata[/COLOR]:
        - Path
        - Espacio disponible
    """
    videoteca = """\
    Muestra los datos de la [COLOR yellow]Videoteca[/COLOR]:
        - Nº de Series y Episodios
        - Nº de Películas
        - Tipo de actulización
        - Path
        - Espacio disponible
    """
    torrent = """\
    Muestra los datos del [COLOR yellow]Cliente Torrent[/COLOR]:
        - Nombre del Cliente
        - Tamaño de buffer inicial
        - Tamaño de buffer en Memoria 
                (opt)
        - Path de descargas
        - Espacio disponible
    """
    proxy = """\
    Muestra las direcciones de canales o servidores que necesitan [COLOR yellow]Proxy[/COLOR]
    """
    log = """\
    Muestra el tamaño actual del [COLOR yellow]Log[/COLOR]
    """
    reporte = """\
    Enlaza con la utilidad que permite el [COLOR yellow]envío del Log[/COLOR] de Kodi a través de un servicio Pastebin
    """

    itemlist.append(Item(channel=item.channel, title="[COLOR orange][B]Variables " +
                    "de entorno Alfa: %s Debug: %s[/B][/COLOR]" % 
                     (environment['addon_version'], environment['debug']), 
                    action="", plot=cabecera, thumbnail=thumb, folder=False)) 

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]%s[/COLOR]' % 
                    environment['os_name'] + ' ' + environment['prod_model'] + ' ' + 
                    environment['os_release'] + ' '  + environment['machine'] + ' ' + 
                    environment['architecture'] + ' ' + environment['language'], 
                    action="", plot=plataform, thumbnail=thumb, folder=False))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Kodi [/COLOR]' + 
                    environment['num_version'] + ', Vídeo: ' + environment['video_db'] + 
                    ', Python ' + environment['python_version'], action="", 
                    plot=kodi, thumbnail=thumb, folder=False))
    
    if environment['cpu_usage']:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]CPU: [/COLOR]' + 
                    environment['cpu_usage'], action="", plot=cpu, thumbnail=thumb, 
                    folder=False))
    
    if environment['mem_total'] or  environment['mem_free']: 
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Memoria: [/COLOR]Total: ' + 
                    environment['mem_total'] + ' MB / Disp.: ' + 
                    environment['mem_free'] + ' MB / Buffers: ' + 
                    str(int(environment['kodi_buffer']) * 3) + ' MB / Buffermode: ' + 
                    environment['kodi_bmode']  + ' / Readfactor: ' + 
                    environment['kodi_rfactor'], 
                    action="", plot=memoria, thumbnail=thumb, folder=False))

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Userdata: [/COLOR]' + 
                    environment['userdata_path'] + ' - Free: ' + environment['userdata_free'] + 
                    ' GB', action="", plot=userdata, thumbnail=thumb, folder=False))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Videoteca: [/COLOR]Series/Epis: ' + 
                    environment['videolab_series'] + '/' + environment['videolab_episodios'] + 
                    ' - Pelis: ' + environment['videolab_pelis'] + ' - Upd: ' + 
                    environment['videolab_update'] + ' - Path: ' + 
                    environment['videolab_path'] + ' - Free: ' + environment['videolab_free'] +  
                    ' GB', action="", plot=videoteca, thumbnail=thumb, folder=False))
    
    if not environment['torrentcli_name']: environment['torrentcli_name'] = 'Torrent: None'
    torrentcli_buffer = environment['torrentcli_buffer']
    if environment['torrentcli_mem_size']:
        torrentcli_buffer +=  ' MB / memoria: ' + environment['torrentcli_mem_size']
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]%s [/COLOR]buffer: ' % 
                    environment['torrentcli_name'] + torrentcli_buffer + 
                    ' MB / descargas: ' + environment['torrentcli_dload_path'] +  
                    ' - Free: ' + environment['torrentcli_free'] +  ' GB', action="", 
                    plot=torrent, thumbnail=thumb, folder=False))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Proxy: [/COLOR]' + 
                    environment['proxy_active'], action="", plot=proxy, thumbnail=thumb, 
                    folder=False))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]TAMAÑO del LOG: [/COLOR]' + 
                    environment['log_size'] + ' MB', action="", plot=log, thumbnail=thumb, 
                    folder=False))
                    
    itemlist.append(Item(title="[COLOR hotpink][B]==> Reportar un fallo[/B][/COLOR]", 
                    channel="setting", action="report_menu", category='Configuración', 
                    unify=False, plot=reporte, thumbnail=get_thumb("error.png")))
    
    return (itemlist, environment)