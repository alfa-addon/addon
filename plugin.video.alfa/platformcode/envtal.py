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
    Devuelve las variables de entorno del OS, de Kodi y de Alfa más habituales, necesarias para el diagnóstico de fallos
    """
    import base64
    import ast
    
    environment = config.get_platform(full_version=True)
    environment['num_version'] = str(environment['num_version'])
    environment['python_version'] = str(platform.python_version())
    
    environment['os_release'] = str(platform.release())
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
        if filetools.exists(filetools.join(xbmc.translatePath("special://userdata"), "advancedsettings.xml")):
            for label_a in filetools.read(filetools.join(xbmc.translatePath("special://userdata"), "advancedsettings.xml")).split('\n'):
                if 'memorysize' in label_a:
                    environment['kodi_buffer'] = str(int(scrapertools.find_single_match(label_a, '>(\d+)<\/')) / 1024**2)
                    break
    except:
        pass
    
    environment['userdata_path'] = str(xbmc.translatePath(config.get_data_path()))
    try:
        if environment['os_name'].lower() == 'windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['userdata_path']), None, None, ctypes.pointer(free_bytes))
            environment['userdata_free'] = str(round(float(free_bytes.value) / (1024**3), 3))
        else:
            disk_space = os.statvfs(environment['userdata_path'])
            if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
            environment['userdata_free'] = str(round((float(disk_space.f_bavail) / (1024**3)) * float(disk_space.f_frsize), 3))
    except:
        environment['userdata_free'] = '?'

    environment['videolab_path'] = str(xbmc.translatePath(config.get_videolibrary_path()))
    try:
        if environment['os_name'].lower() == 'windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['videolab_path']), None, None, ctypes.pointer(free_bytes))
            environment['videolab_free'] = str(round(float(free_bytes.value) / (1024**3), 3))
        else:
            disk_space = os.statvfs(environment['videolab_path'])
            if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
            environment['videolab_free'] = str(round((float(disk_space.f_bavail) / (1024**3)) * float(disk_space.f_frsize), 3))
    except:
        environment['videolab_free'] = '?'

    environment['torrentcli_name'] = ''
    environment['torrentcli_dload_path'] = ''
    environment['torrentcli_buffer'] = ''
    environment['torrentcli_dload_estrgy'] = ''
    environment['torrentcli_mem_size'] = ''
    if config.get_setting("torrent_client", server="torrent") == 3:
        for client_torrent in ['quasar', 'elementum', 'torrenter']:
            if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s" )' % client_torrent):
                __settings__ = xbmcaddon.Addon(id="plugin.video.%s" % client_torrent)
                environment['torrentcli_name'] = str(client_torrent)
                if client_torrent == 'torrenter':
                    environment['torrentcli_dload_path'] = str(xbmc.translatePath(__settings__.getSetting('storage')))
                    environment['torrentcli_buffer'] = str(__settings__.getSetting('pre_buffer_bytes'))
                else:
                    environment['torrentcli_dload_path'] = str(xbmc.translatePath(__settings__.getSetting('download_path')))
                    environment['torrentcli_buffer'] = str(__settings__.getSetting('buffer_size'))
                    environment['torrentcli_dload_estrgy'] = str(__settings__.getSetting('download_storage'))
                    environment['torrentcli_mem_size'] = str(__settings__.getSetting('memory_size'))
                try:
                    if environment['os_name'].lower() == 'windows':
                        free_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(environment['torrentcli_dload_path']), None, None, ctypes.pointer(free_bytes))
                        environment['torrentcli_free'] = str(round(float(free_bytes.value) / (1024**3), 3))
                    else:
                        disk_space = os.statvfs(environment['torrentcli_dload_path'])
                        if not disk_space.f_frsize: disk_space.f_frsize = disk_space.f_frsize.f_bsize
                        environment['torrentcli_free'] = str(round((float(disk_space.f_bavail) / (1024**3)) * float(disk_space.f_frsize), 3))
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
            if file.lower() in ['kodi.log', 'jarvis.log', 'spmc.log', 'cemc.log', 'mygica.log', 'wonderbox.log', 'leiapp,log', 'leianmc.log', 'kodiapp.log', 'anmc.log', 'latin-anmc.log']:
                environment['log_path'] = str(filetools.join(root, file))
                break
        else:
            environment['log_path'] = ''
        break
    
    if environment['log_path']:
        environment['log_size_bytes'] = str(filetools.getsize(environment['log_path']))
        environment['log_size'] = str(round(float(environment['log_size_bytes']) / (1024*1024), 3))
    else:
        environment['log_size_bytes'] = ''
        environment['log_size'] = ''

    return environment


def list_env(environment={}):
    if not environment:
        environment = get_environment()
        
    logger.info("----------------------------------------------")
    logger.info("Variables de entorno Alfa: " + str(config.get_addon_version()))
    logger.info("----------------------------------------------")

    logger.info(environment['os_name'] + ' ' + environment['prod_model'] + ' ' + environment['os_release'] + ' ' + environment['machine'] + ' ' + environment['architecture'] + ' ' + environment['language'])
    logger.info('Kodi ' + environment['num_version'] + ', Vídeo: ' + environment['video_db'] + ', Python ' + environment['python_version'])
    
    if environment['cpu_usage']:
        logger.info('CPU: ' + environment['cpu_usage'])
    
    if environment['mem_total'] and environment['mem_free']: 
        logger.info('Memoria: Total: ' + environment['mem_total'] + ' MB / Disp.: ' + environment['mem_free'] + ' MB / Buffer: ' + str(int(environment['kodi_buffer']) * 3) + ' MB')

    logger.info('Userdata: ' + environment['userdata_path'] + ' - Free: ' + environment['userdata_free'] +  ' GB')
    logger.info('Videoteca: ' + environment['videolab_path'] + ' - Free: ' + environment['videolab_free'] +  ' GB')
    
    if environment['torrentcli_name']:
        if environment['torrentcli_mem_size']:
            environment['torrentcli_buffer'] = environment['torrentcli_buffer'] + 'MB / memoria: ' + environment['torrentcli_mem_size']
        logger.info('%s buffer: ' % environment['torrentcli_name'] + environment['torrentcli_buffer'] + ' MB / descargas: ' + environment['torrentcli_dload_path'] + ' - Free: ' + environment['torrentcli_free'] +  ' GB')
    
    logger.info('Proxy: ' + environment['proxy_active'])
    
    logger.info('TAMAÑO del LOG: ' + environment['log_size'] + ' MB')
    logger.info("----------------------------------------------")
    
    return environment
    
    
def paint_env(item, environment={}):
    from core.item import Item
    
    if not environment:
        environment = get_environment()
    itemlist = []

    itemlist.append(Item(channel=item.channel, title="[COLOR orange]Variables de entorno Alfa: %s[/COLOR]" % str(config.get_addon_version()), action=""))

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]%s[/COLOR]' % environment['os_name'] + ' ' + environment['prod_model'] + ' ' + environment['os_release'] + ' '  + environment['machine'] + ' ' + environment['architecture'] + ' ' + environment['language'], action=""))
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Kodi [/COLOR]' + environment['num_version'] + ', Vídeo: ' + environment['video_db'] + ', Python ' + environment['python_version'], action=""))
    
    if environment['cpu_usage']:
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]CPU: [/COLOR]' + environment['cpu_usage'], action=""))
    
    if environment['mem_total'] and environment['mem_free']: 
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Memoria: [/COLOR]Total: ' + environment['mem_total'] + ' MB / Disp.: ' + environment['mem_free'] + ' MB / Buffer: ' + str(int(environment['kodi_buffer']) * 3) + ' MB', action=""))

    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Userdata: [/COLOR]' + environment['userdata_path'] + ' - Free: ' + environment['userdata_free'] +  ' GB', action=""))
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Videoteca: [/COLOR]' + environment['videolab_path'] + ' - Free: ' + environment['videolab_free'] +  ' GB', action=""))
    
    if environment['torrentcli_name']:
        if environment['torrentcli_mem_size']:
            environment['torrentcli_buffer'] = environment['torrentcli_buffer'] + 'MB / memoria: ' + environment['torrentcli_mem_size']
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]%s [/COLOR]buffer: ' % environment['torrentcli_name'] + environment['torrentcli_buffer'] + ' MB / descargas: ' + environment['torrentcli_dload_path'] + ' - Free: ' + environment['torrentcli_free'] +  ' GB', action=""))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Proxy: [/COLOR]' + environment['proxy_active'], action=""))
    
    itemlist.append(Item(channel=item.channel, title='[COLOR yellow]TAMAÑO del LOG: [/COLOR]' + environment['log_size'] + ' MB', action=""))
    
    return (itemlist, environment)