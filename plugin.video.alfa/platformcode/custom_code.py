# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------

import os
import json

from platformcode import config, logger

from core import jsontools
from core import filetools

json_data_file_name = 'custom_code.json'


def init():
    logger.info()

    """
    Todo el código añadido al add-on se borra con cada actualización.  Esta función permite restaurarlo automáticamente con cada actualización.
    Esto permite al usuario tener su propio código, bajo su responsabilidad, y restaurarlo al add-on cada vez que se actualiza.
    
    El mecanismo funciona copiando el contenido de la carpeta-arbol ".\userdata\addon_data\plugin.video.alfa\custom_code\..." sobre
    las carpetas de código del add-on.  No verifica el contenido, solo vuelca(reemplaza) el contenido de "custom_code".
    
    El usuario almacenará en las subcarpetas de "custom_code" su código actualizado y listo para ser copiado en cualquier momento.
    Si no se desea que copie algo, simplemente se borra de "custom_code" y ya no se copiará en la próxima actualización.
    
    Los pasos que sigue esta función, son los siguientes:
    
    1.- La función se llama desde videolibrary_service.py, desde la función inicial:
            # Copia Custom code a las carpetas de Alfa desde la zona de Userdata
            from platformcode import custom_code
            custom_code.init()
            
    2.- En el inicio de Kodi, comprueba si existe la carpeta "custom_code" en ".\userdata\addon_data\plugin.video.alfa\".  
        Si no existe, la crea y sale sin más, dando al ususario la posibilidad de copiar sobre esa estructura su código, 
        y que la función la vuelque sobre el add-on en el próximo inicio de Kodi.
        
    3.- En el siguiente inicio de Kodi, comprueba si existe el custom_code.json en la carpeta root del add-on.
        Si no existe, lo crea con el número de versión del add-on vacío, para permitir que se copien los archivos en esta pasada.
        
    4.- Verifica que el número de versión del add-on es diferente de el de custom_code.json.  Si es la misma versión, 
        se sale porque ya se realizo la copia anteriormente.
        Si la versión es distinta, se realiza el volcado de todos los archivos de la carpeta-árbol "custom_code" sobre el add-on.
        Si la carpeta de destino no existe, dará un error y se cancelará la copia.  Se considera que no tienen sentido nuevas carpetas.
        
    5.- Si la copia ha terminado con éxito, se actualiza el custom_code.json con el número de versión del add-on,
        para que en inicios sucesivos de Kodi no se realicen las copias, hasta que el add-on cambie de versión.
        En el número de versión del add-on no se considera el número de fix.
        
    Tiempos:    Copiando 7 archivos de prueba, el proceso ha tardado una décima de segundo.
    """
    
    try:
        #Existe carpeta "custom_code" ? Si no existe se crea y se sale
        custom_code_dir = os.path.join(config.get_data_path(), 'custom_code')
        if os.path.exists(custom_code_dir) == False:
            create_folder_structure(custom_code_dir)
            return
        
        else:
            #Existe "custom_code.json" ? Si no existe se crea
            custom_code_json_path = config.get_runtime_path()
            custom_code_json = os.path.join(custom_code_json_path, 'custom_code.json')
            if os.path.exists(custom_code_json) == False:
                create_json(custom_code_json_path)
            
            #Se verifica si la versión del .json y del add-on son iguales.  Si es así se sale.  Si no se copia "custom_code" al add-on
            verify_copy_folders(custom_code_dir, custom_code_json_path)
    except:
        pass
            

def create_folder_structure(custom_code_dir):
    logger.info()

    #Creamos todas las carpetas.  La importante es "custom_code".  Las otras sirven meramente de guía para evitar errores de nombres...
    os.mkdir(custom_code_dir)
    os.mkdir(filetools.join(custom_code_dir, 'channels'))
    os.mkdir(filetools.join(custom_code_dir, 'core'))
    os.mkdir(filetools.join(custom_code_dir, 'lib'))
    os.mkdir(filetools.join(custom_code_dir, 'platformcode'))
    os.mkdir(filetools.join(custom_code_dir, 'resources'))
    os.mkdir(filetools.join(custom_code_dir, 'servers'))

    return


def create_json(custom_code_json_path):
    logger.info()

    #Guardamaos el json con la versión de Alfa vacía, para permitir hacer la primera copia
    json_data_file = filetools.join(custom_code_json_path, json_data_file_name)
    json_file = open(json_data_file, "a+")
    json_file.write(json.dumps({"addon_version": ""}))
    json_file.close()
    
    return


def verify_copy_folders(custom_code_dir, custom_code_json_path):
    logger.info()
    
    #verificamos si es una nueva versión de Alfa instalada o era la existente.  Si es la existente, nos vamos sin hacer nada
    json_data_file = filetools.join(custom_code_json_path, json_data_file_name)
    json_data = jsontools.load(filetools.read(json_data_file))
    current_version = config.get_addon_version(with_fix=False)
    if current_version == json_data['addon_version']:
        return
    
    #Ahora copiamos los archivos desde el área de Userdata, Custom_code, sobre las carpetas del add-on
    for root, folders, files in os.walk(custom_code_dir):
        for file in files:
            input_file = filetools.join(root, file)
            output_file = input_file.replace(custom_code_dir, custom_code_json_path)
            if filetools.copy(input_file, output_file, silent=True) == False:
                return
    
    #Guardamaos el json con la versión actual de Alfa, para no volver a hacer la copia hasta la nueva versión
    json_data['addon_version'] = current_version
    filetools.write(json_data_file, jsontools.dump(json_data))

    return
