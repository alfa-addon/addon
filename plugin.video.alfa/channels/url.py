# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger, platformtools


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60089), list_type='server'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60090), list_type='direct'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60091), list_type='findvideos'))
    itemlist.append(Item(channel=item.channel, action="menu_storage", title="Descargar desde Torrents almacenados", list_type='videolibrary'))

    return itemlist


# Al llamarse "search" la función, el launcher pide un texto a buscar y lo añade como parámetro
def search(item, texto):
    logger.info("texto=" + texto)

    if not texto.startswith("http"):
        texto = "http://" + texto

    itemlist = []

    if "server" in item.list_type:
        itemlist = servertools.find_video_items(data=texto)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"
    elif "direct" in item.list_type:
        itemlist.append(Item(channel=item.channel, action="play", url=texto, server="directo", title=config.get_localized_string(60092)))
    else:
        data = httptools.downloadpage(texto).data
        itemlist = servertools.find_video_items(data=data)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60093)))

    return itemlist


def findvideos(item):
    logger.info()
    from core import filetools
    from lib import generictools

    itemlist = []
    size = ''
    
    #logger.debug(item)
    
    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    FOLDER = FOLDER_TVSHOWS if item.infoLabels['mediatype'] == 'episode' else FOLDER_MOVIES
    VIDEOLIBRARY_PATH = config.get_videolibrary_path()
    MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
    TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
    VIDEO_FOLDER = filetools.join(VIDEOLIBRARY_PATH, FOLDER)

    # Viene desde Kodi/Videoteca de una canal desactivado
    if not item.list_type:
        if item.emergency_urls:
            # Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
            item.infoLabels['playcount'] = 0
            if item.contentChannel == 'videolibrary':
                item.armagedon = True                                           # Lo marcammos como URLs de Emergencia
            item.channel_recovery = 'url'
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
            
            for link in item.emergency_urls[0]:
                link_path = filetools.join(VIDEO_FOLDER, link)
                if filetools.isfile(link_path):
                    size = generictools.get_torrent_size(link_path, local_torr=link_path)
                    if size:
                        # Generamos una copia de Item para trabajar sobre ella
                        item_local = item.clone()
                        
                        item_local.channel = 'url'
                        item_local.url = link_path
                        item_local.torrent_info = size
                        
                        # Si viene de la Videoteca de Kodi, mostramos que son URLs de Emergencia
                        if item_local.contentChannel == 'videolibrary':
                            item_local.quality = '[COLOR hotpink][E][/COLOR] [COLOR limegreen]%s[/COLOR]' % item_local.quality
                        
                        #Ahora pintamos el link del Torrent
                        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                                        (item_local.quality, str(item_local.language), \
                                        item_local.torrent_info)
                        
                        # Preparamos título y calidad, quitando etiquetas vacías
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
                            item_local.alive = "??"                             #Calidad del link sin verificar
                        elif 'ERROR' in size and 'Pincha' in size:
                            item_local.alive = "ok"                             #link en error, CF challenge, Chrome disponible
                        elif 'ERROR' in size and 'Introduce' in size:
                            item_local.alive = "??"                             #link en error, CF challenge, ruta de descarga no disponible
                            item_local.channel = 'setting'
                            item_local.action = 'setting_torrent'
                            item_local.unify = False
                            item_local.folder = False
                            item_local.item_org = item.tourl()
                        elif 'ERROR' in size:
                            item_local.alive = "no"                             #Calidad del link en error, CF challenge?
                        else:
                            item_local.alive = "ok"                             #Calidad del link verificada
                        
                        item_local.action = "play"                              #Visualizar vídeo
                        item_local.server = "torrent"                           #Seridor Torrent
                        
                        itemlist.append(item_local)                             #Pintar pantalla

        return itemlist


def menu_storage(item):
    logger.info()
    from core import filetools
    from servers.torrent import torrent_dirs
    
    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    FOLDER = FOLDER_TVSHOWS if item.infoLabels['mediatype'] else FOLDER_MOVIES
    VIDEOLIBRARY_PATH = config.get_videolibrary_path()
    MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
    TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
    VIDEO_FOLDER = filetools.join(VIDEOLIBRARY_PATH, FOLDER)
    TORRENT_PATHS = torrent_dirs()

    itemlist = []
    
    if 'videolibrary' in item.list_type:
        itemlist.append(Item(channel=item.channel, action="", title="Videoteca Alfa"))
        itemlist.append(Item(channel=item.channel, action="list_storage", url=MOVIES_PATH, title="  - " + FOLDER_MOVIES))
        itemlist.append(Item(channel=item.channel, action="list_storage", url=TVSHOWS_PATH, title="  - " + FOLDER_TVSHOWS))
        
        if TORRENT_PATHS['TORREST_torrents'] or TORRENT_PATHS['QUASAR_torrents'] \
                          or TORRENT_PATHS['ELEMENTUM_torrents'] or TORRENT_PATHS['TORRENTER_torrents']:
            itemlist.append(Item(channel=item.channel, action="", title="Gestores Torrent"))
            
            if TORRENT_PATHS['TORREST_torrents']:
                itemlist.append(Item(channel=item.channel, action="list_storage", url=TORRENT_PATHS['TORREST_torrents'], title="  - Torrest"))
            if TORRENT_PATHS['QUASAR_torrents']:
                itemlist.append(Item(channel=item.channel, action="list_storage", url=TORRENT_PATHS['QUASAR_torrents'], title="  - Quasar"))
            if TORRENT_PATHS['ELEMENTUM_torrents']:
                itemlist.append(Item(channel=item.channel, action="list_storage", url=TORRENT_PATHS['ELEMENTUM_torrents'], title="  - Elementum"))
            if TORRENT_PATHS['TORRENTER_torrents']:
                itemlist.append(Item(channel=item.channel, action="list_storage", url=TORRENT_PATHS['TORRENTER_torrents'], title="  - Torrenter"))
            
            itemlist.append(Item(channel=item.channel, action="", title="Almacenamiento general"))
            itemlist.append(Item(channel=item.channel, action="list_storage", url='', title="  - Almacenamiento"))

            return itemlist


def list_storage(item):
    logger.info()
    from core import filetools
    
    itemlist = []
    
    #logger.debug(item)
    
    browse_type = 0
    path_out = item.url
    if not filetools.exists(path_out):
        path_out = ''
    
    if not path_out:
        msg = 'Seleccione carpeta de destino:'
        path_out = platformtools.dialog_browse(browse_type, msg, shares='')
        
    path_list = filetools.listdir(path_out)
    VIDEOLIBRARY_PATH = config.get_videolibrary_path()
    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    FOLDER = ''
    if VIDEOLIBRARY_PATH in path_out:
        if FOLDER_MOVIES in path_out:
            FOLDER = FOLDER_MOVIES
        elif FOLDER_TVSHOWS in path_out:
            FOLDER = FOLDER_TVSHOWS
    MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
    TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
    VIDEO_FOLDER = filetools.join(VIDEOLIBRARY_PATH, FOLDER)
    TEMP_TORRENT_FOLDER = filetools.join(VIDEOLIBRARY_PATH, 'temp_torrents_Alfa')
    
    for file in path_list:
        if FOLDER and file.endswith('.json') and file.split('.')[0]+'_01.torrent' in str(path_list):
            json_video = Item().fromjson(filetools.read(filetools.join(path_out, file)))
            json_video.channel = 'url'
            json_video.action = 'findvideos'
            itemlist.append(json_video)
        
        elif FOLDER and filetools.isdir(filetools.join(path_out, file)):
            if '.torrent' in str(filetools.listdir(filetools.join(path_out, file))):
                itemlist.append(Item(channel=item.channel, action="list_storage", url=filetools.join(path_out, file), title=file))
        
        elif not FOLDER and file.endswith('.torrent'):
            filetools.copy(filetools.join(path_out, file), filetools.join(TEMP_TORRENT_FOLDER, file))
            itemlist.append(Item(channel=item.channel, action="play", url=filetools.join(TEMP_TORRENT_FOLDER, file), 
                            server='torrent', title=filetools.join(filetools.basename(path_out.rstrip('/').rstrip('\\')), file)))

    return itemlist
