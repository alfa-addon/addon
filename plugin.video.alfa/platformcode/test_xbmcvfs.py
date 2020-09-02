# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Test xbmcvfs
# --------------------------------------------------------------------------------

import os
import xbmc
import time

from platformcode import config, platformtools
from core import filetools, jsontools


def test_vfs():
    
    # Test des sistema de archivos nativo  XbmcVFS de Kodi
    # En los ajuste de Alfa, seleccionar en Path de Videoteca la Fuente del filesystem que se quiere probar
    path_in = config.get_runtime_path()
    path = config.get_videolibrary_path()
    file_in = 'custom_code.json'
    file_write = 'write_custom_code.json'
    file_move = 'move_custom_code.json'
    path_move = filetools.join(path, 'test1', 'test2')
    path_move_folder = filetools.join(path, 'test1', 'moved_folder')
    file_rename = 'rename_custom_code.json'
    path_mkdir = filetools.join(path, 'test1', 'test2', 'test3')
    files_test = ['test1_custom_code.json', 'test2_custom_code.json', 'test3_custom_code.json']
    path_rmdirtree = filetools.join(path, 'test1')
    
    log(' ')
    log('### COMIENZA el TEST ###')
    log(' ')
    
    # Copiamos desde la carpeta de Alfa un archivo a la carpeta del Filesystem
    log('COPIA desde Alfa al Filesystem: %s: ### %s' % (file_in, filetools.copy(filetools.join(path_in, file_in), \
                filetools.join(path, file_in))))
    log('LISTDIR COPIA %s: ### %s' % (path, filetools.listdir(path)))
    log('----------')
    
    # Lectura del archivo desde la carpeta del Filesystem
    log('LECTURA desde el Filesystem: %s: linea_inicio=10, total_lineas=7: ### %s' % \
                (filetools.join(path, file_in), filetools.read(filetools.join(path, file_in), \
                linea_inicio=10, total_lineas=7)))
    data = filetools.read(filetools.join(path, file_in))
    json_data = jsontools.load(data)
    size = filetools.getsize(filetools.join(path, file_in))
    log('LECTURA desde el Filesystem: %s: ### SIZE: %s: ### %s' % (filetools.join(path, file_in), str(size), data))
    log('----------')
                
    # Escritura del archivo desde la carpeta del Filesystem
    log('ESCRITURA de JSON desde memoria al Filesystem: %s: TOTAL: ### %s' % \
                (filetools.join(path, file_write), filetools.write(filetools.join(path, file_write), jsontools.dump(json_data))))
    log('LISTDIR ESCRITURA %s: ### %s' % (path, filetools.listdir(path)))
    log('----------')
    
    # Renombrar el archivo recien escrito
    log('RENOMBRAR el archivo recien escrito: %s: ### %s' % (file_rename, filetools.rename(filetools.join(path, file_write), file_rename)))
    log('LISTDIR RENOMBRAR %s: ### %s' % (path, filetools.listdir(path)))
    log('----------')
    
    # Renombrar el archivo recien escrito
    log('MKDIR de arbol de carpetas y rellenado: %s: ### %s' % (path_mkdir, filetools.mkdir(path_mkdir)))
    
    for x in range(10):
        time.sleep(1)
        if filetools.exists(path_mkdir): break
    if not filetools.exists(path_mkdir):
        log('### MKDIR: ERROR al crear el path %s.  Crealo manualmente y repite para continuar el test' % path_mkdir)
        platformtools.dialog_notification('MKDIR: ERROR al crear el path: ', '[COLOR yellow]%s[/B][/COLOR]. \
                Crealo manualmente y repite para continuar el test' % path_mkdir)
        return
    
    path_int = path
    for x, file_test in enumerate(files_test):
        x += 1
        path_int = filetools.join(path_int, 'test' + str(x))
        filetools.copy(filetools.join(path, file_in), filetools.join(path_int, file_test))
        log('LISTDIR MKDIR %s: ### %s' % (path_int, filetools.listdir(path_int)))
    log('----------')
        
    # ISFILE archivo
    log('ISFILE archivo: %s: ### %s' % (filetools.join(path_mkdir, file_test), filetools.isfile(filetools.join(path_mkdir, file_test))))
    log('ISDIR archivo: %s: ### %s' % (filetools.join(path_mkdir, file_test), filetools.isdir(filetools.join(path_mkdir, file_test))))
    log('----------')
    
    # ISDIR carpeta
    log('ISFILE carpeta: %s: ### %s' % (path_mkdir, filetools.isfile(path_mkdir)))
    log('ISDIR carpeta: %s: ### %s' % (path_mkdir, filetools.isdir(path_mkdir)))
    log('----------')
        
    # Borrar archivo y carpeta
    log('BORRAR archivo: %s, %s: ### %s' % (path_mkdir, file_test, filetools.remove(filetools.join(path_mkdir, file_test))))
    log('LISTDIR BORRAR archivo %s: ### %s' % (path_mkdir, filetools.listdir(path_mkdir)))
    log('BORRAR carpeta: %s: ### %s' % (path_mkdir, filetools.rmdir(path_mkdir)))
    if path_mkdir.endswith('/') or path_mkdir.endswith('\\'):
        path_mkdir = path_mkdir[:-1]
    path_mkdir = filetools.split(path_mkdir)[0]
    log('LISTDIR BORRAR carpeta %s: ### %s' % (path_mkdir, filetools.listdir(path_mkdir)))
    log('----------')
    
    # MOVE archivo y carpeta
    log('MOVE archivo: %s: ### %s' % (filetools.join(path, file_rename), filetools.move(filetools.join(path, file_rename), \
                filetools.join(path_move, file_move))))
    log('LISTDIR MOVE archivo %s: ### %s' % (filetools.join(path_move, file_move), filetools.listdir(path_move)))
    log('MOVE carpeta: %s: ### %s' % (path_move, filetools.move(path_move, path_move_folder)))
    log('LISTDIR MOVE carpeta %s: ### %s' % (path_move_folder, filetools.listdir(path_move_folder)))
    log('----------')
    
    # Borrar de arbol de archivos y carpetas
    log('BORRAR arbol de archivos y carpetas (con WALK): %s: ### %s' % (path_rmdirtree, filetools.rmdirtree(path_rmdirtree)))
    for x in range(10):
        time.sleep(1)
        if not filetools.exists(path_rmdirtree): break
    filetools.remove(filetools.join(path, file_in))
    log('LISTDIR BORRAR archivo %s: ### %s' % (path, filetools.listdir(path)))
    
    log(' ')
    log('### FIN del TEST ###')
    log(' ')
    platformtools.dialog_notification('XbmcVFS: FIN del TEST ', 'Analiza el LOG')
    
    return


def log(texto):
    xbmc.log('### XbmcVFS: ' + str(texto), xbmc.LOGNOTICE)