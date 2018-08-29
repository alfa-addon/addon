# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa favoritos (Mis enlaces)
# ============================
# - Lista de enlaces guardados como favoritos, solamente en Alfa, no Kodi.
# - Los enlaces se organizan en carpetas que puede definir el usuario.
# - Se utiliza un sólo fichero para guardar todas las carpetas y enlaces: user_favorites.json
# - Se puede copiar user_favorites.json a otros dispositivos ya que la única dependencia local es el thumbnail asociado a los enlaces,
#   pero se detecta por código y se ajusta al dispositivo actual.

# Requerimientos en otros módulos para ejecutar este canal:
# - Añadir un enlace a este canal en channelselector.py
# - Modificar platformtools.py para controlar el menú contextual y añadir "Guardar enlace" en set_context_commands
# ------------------------------------------------------------

import os, re

from core import filetools
from core import jsontools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools


# Clase para cargar y guardar en el fichero de Alfavoritos
# --------------------------------------------------------
class AlfavoritesData:

    def __init__(self):
        self.user_favorites_file = os.path.join(config.get_data_path(), 'user_favorites.json')

        if not os.path.exists(self.user_favorites_file):
            self.user_favorites = []
        else:
            try:
                self.user_favorites = jsontools.load(filetools.read(self.user_favorites_file))
            except:
                self.user_favorites = []

        if len(self.user_favorites) == 0:
            self.user_favorites.append({ 'title': 'Carpeta por defecto', 'items': [] })
            self.save()

    def save(self):
        filetools.write(self.user_favorites_file, jsontools.dump(self.user_favorites))


# ============================
# Añadir desde menú contextual
# ============================

def addFavourite(item):
    logger.info()
    alfav = AlfavoritesData()

    # Si se llega aquí mediante el menú contextual, hay que recuperar los parámetros action y channel
    if item.from_action:
        item.__dict__["action"] = item.__dict__.pop("from_action")
    if item.from_channel:
        item.__dict__["channel"] = item.__dict__.pop("from_channel")

    # Limpiar título y quitar color
    item.title = re.sub(r'\[COLOR [^\]]*\]', '', item.title.replace('[/COLOR]', '')).strip()
    if item.text_color:
        item.__dict__.pop("text_color")

    # Diálogo para escoger/crear carpeta
    i_perfil = _selecciona_perfil(alfav, 'Guardar enlace en:')
    if i_perfil == -1: return False

    # Detectar que el mismo enlace no exista ya en la carpeta
    campos = ['channel','action','url','extra'] # si todos estos campos coinciden se considera que el enlace ya existe
    for enlace in alfav.user_favorites[i_perfil]['items']:
        it = Item().fromurl(enlace)
        repe = True
        for prop in campos:
            if prop in it.__dict__ and prop in item.__dict__ and it.__dict__[prop] != item.__dict__[prop]:
                repe = False
                break
        if repe:
            platformtools.dialog_notification('Enlace repetido', 'Ya tienes este enlace en la carpeta')
            return False

    # Guardar
    alfav.user_favorites[i_perfil]['items'].append(item.tourl())
    alfav.save()

    platformtools.dialog_notification('Guardado enlace', 'Carpeta: %s' % alfav.user_favorites[i_perfil]['title'])
    
    return True


# ====================
# NAVEGACIÓN
# ====================

def mainlist(item):
    logger.info()
    alfav = AlfavoritesData()

    itemlist = []
    last_i = len(alfav.user_favorites) - 1

    for i_perfil, perfil in enumerate(alfav.user_favorites):
        context = []

        context.append({'title': 'Cambiar nombre de la carpeta', 'channel': item.channel, 'action': 'editar_perfil_titulo',
                        'i_perfil': i_perfil})
        context.append({'title': 'Eliminar la carpeta', 'channel': item.channel, 'action': 'eliminar_perfil',
                        'i_perfil': i_perfil})

        if i_perfil > 0:
            context.append({'title': 'Mover arriba del todo', 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'top'})
            context.append({'title': 'Mover hacia arriba', 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'arriba'})
        if i_perfil < last_i:
            context.append({'title': 'Mover hacia abajo', 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'abajo'})
            context.append({'title': 'Mover abajo del todo', 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'bottom'})

        plot = '%d enlaces en la carpeta' % len(perfil['items'])
        itemlist.append(Item(channel=item.channel, action='mostrar_perfil', title=perfil['title'], plot=plot, i_perfil=i_perfil, context=context))

    plot = '* Crea diferentes carpetas para guardar tus enlaces favoritos dentro de Alfa.[CR]'
    plot += '* Para añadir enlaces a las carpetas accede al menú contextual desde cualquier punto de Alfa.[CR]'
    plot += '* Los enlaces pueden ser canales, secciones dentro de los canales, búsquedas, e incluso películas y series aunque para esto último es preferible utilizar la videoteca.'
    itemlist.append(item.clone(action='crear_perfil', title='Crear nueva carpeta ...', plot=plot, folder=False)) 
    
    return itemlist


def mostrar_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    itemlist = []

    i_perfil = item.i_perfil
    if not alfav.user_favorites[i_perfil]: return itemlist
    last_i = len(alfav.user_favorites[i_perfil]['items']) - 1

    ruta_runtime = config.get_runtime_path()

    for i_enlace, enlace in enumerate(alfav.user_favorites[i_perfil]['items']):
        context = []

        if i_enlace > 0:
            context.append({'title': 'Mover arriba del todo', 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'top'})
            context.append({'title': 'Mover hacia arriba', 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'arriba'})
        if i_enlace < last_i:
            context.append({'title': 'Mover hacia abajo', 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'abajo'})
            context.append({'title': 'Mover abajo del todo', 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'bottom'})

        if len(alfav.user_favorites) > 1: # si se tiene más de una carpeta permitir mover entre ellas
            context.append({'title': 'Mover a otra carpeta', 'channel': item.channel, 'action': 'editar_enlace_carpeta',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': 'Cambiar título', 'channel': item.channel, 'action': 'editar_enlace_titulo',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': 'Cambiar color', 'channel': item.channel, 'action': 'editar_enlace_color',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': 'Cambiar thumbnail', 'channel': item.channel, 'action': 'editar_enlace_thumbnail',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': 'Eliminar enlace', 'channel': item.channel, 'action': 'eliminar_enlace',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        it = Item().fromurl(enlace)
        it.context = context
        it.plot = '[COLOR blue]Canal: ' + it.channel + '[/COLOR][CR]' + it.plot

        # Si no es una url, ni tiene la ruta del sistema, convertir el path ya que se habrá copiado de otro dispositivo.
        # Sería más óptimo que la conversión se hiciera con un menú de importar, pero de momento se controla en run-time.
        if it.thumbnail and '://' not in it.thumbnail and not it.thumbnail.startswith(ruta_runtime):
            ruta, fichero = filetools.split(it.thumbnail)
            if ruta == '' and fichero == it.thumbnail: # en linux el split con un path de windows no separa correctamente
                ruta, fichero = filetools.split(it.thumbnail.replace('\\','/'))
            if 'channels' in ruta and 'thumb' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'channels', 'thumb', fichero)
            elif 'themes' in ruta and 'default' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'themes', 'default', fichero)

        itemlist.append(it)

    return itemlist


# Rutinas internas compartidas
# ----------------------------

# Diálogo para seleccionar/crear una carpeta. Devuelve índice de la carpeta en user_favorites (-1 si cancel)
def _selecciona_perfil(alfav, titulo='Seleccionar carpeta', i_actual=-1):
    acciones = [(perfil['title'] if i_p != i_actual else '[I][COLOR pink]%s[/COLOR][/I]' % perfil['title']) for i_p, perfil in enumerate(alfav.user_favorites)]
    acciones.append('Crear nueva carpeta')

    i_perfil = -1
    while i_perfil == -1: # repetir hasta seleccionar una carpeta o cancelar
        ret = platformtools.dialog_select(titulo, acciones)
        if ret == -1: return -1 # pedido cancel
        if ret < len(alfav.user_favorites):
            i_perfil = ret
        else: # crear nueva carpeta
            if _crea_perfil(alfav):
                i_perfil = len(alfav.user_favorites) - 1

    return i_perfil


# Diálogo para crear una carpeta
def _crea_perfil(alfav):
    titulo = platformtools.dialog_input(default='', heading='Nombre de la carpeta')
    if titulo is None or titulo == '':
        return False

    alfav.user_favorites.append({'title': titulo, 'items': []})
    alfav.save()

    return True


# Gestión de perfiles y enlaces
# -----------------------------

def crear_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    if not _crea_perfil(alfav): return False

    platformtools.itemlist_refresh()
    return True


def editar_perfil_titulo(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False

    titulo = platformtools.dialog_input(default=alfav.user_favorites[item.i_perfil]['title'], heading='Nombre de la carpeta')
    if titulo is None or titulo == '' or titulo == alfav.user_favorites[item.i_perfil]['title']:
        return False

    alfav.user_favorites[item.i_perfil]['title'] = titulo
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False

    # Pedir confirmación
    if not platformtools.dialog_yesno('Eliminar carpeta', '¿Borrar la carpeta y los enlaces que contiene?'): return False

    del alfav.user_favorites[item.i_perfil]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_titulo(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    titulo = platformtools.dialog_input(default=it.title, heading='Cambiar título del enlace')
    if titulo is None or titulo == '' or titulo == it.title:
        return False
    
    it.title = titulo

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_color(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    colores = ['green','yellow','red','blue','white','orange','lime','aqua','pink','violet','purple','tomato','olive','antiquewhite','gold']
    opciones = ['[COLOR %s]%s[/COLOR]' % (col, col) for col in colores]

    ret = platformtools.dialog_select('Seleccionar color:', opciones)

    if ret == -1: return False # pedido cancel
    it.text_color = colores[ret]

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_thumbnail(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    # A partir de Kodi 17 se puede usar xbmcgui.Dialog().select con thumbnails (ListItem & useDetails=True)
    is_kodi17 = (config.get_platform(True)['num_version'] >= 17.0)
    if is_kodi17:
        import xbmcgui

    # Diálogo para escoger thumbnail (el del canal o iconos predefinidos)
    opciones = []
    ids = []
    try:
        from core import channeltools
        channel_parameters = channeltools.get_channel_parameters(it.channel)
        if channel_parameters['thumbnail'] != '':
            nombre = 'Canal %s' % it.channel
            if is_kodi17:
                it_thumb = xbmcgui.ListItem(nombre)
                it_thumb.setArt({ 'thumb': channel_parameters['thumbnail'] })
                opciones.append(it_thumb)
            else:
                opciones.append(nombre)
            ids.append(channel_parameters['thumbnail'])
    except:
        pass
    
    resource_path = os.path.join(config.get_runtime_path(), 'resources', 'media', 'themes', 'default')
    for f in sorted(os.listdir(resource_path)):
        if f.startswith('thumb_') and not f.startswith('thumb_intervenido') and f != 'thumb_back.png':
            nombre = f.replace('thumb_', '').replace('_', ' ').replace('.png', '')
            if is_kodi17:
                it_thumb = xbmcgui.ListItem(nombre)
                it_thumb.setArt({ 'thumb': os.path.join(resource_path, f) })
                opciones.append(it_thumb)
            else:
                opciones.append(nombre)
            ids.append(os.path.join(resource_path, f))

    if is_kodi17:
        ret = xbmcgui.Dialog().select('Seleccionar thumbnail:', opciones, useDetails=True)
    else:
        ret = platformtools.dialog_select('Seleccionar thumbnail:', opciones)

    if ret == -1: return False # pedido cancel

    it.thumbnail = ids[ret]

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_carpeta(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    # Diálogo para escoger/crear carpeta
    i_perfil = _selecciona_perfil(alfav, 'Mover enlace a:', item.i_perfil)
    if i_perfil == -1 or i_perfil == item.i_perfil: return False

    alfav.user_favorites[i_perfil]['items'].append(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    del alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_enlace(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    del alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


# Mover perfiles y enlaces (arriba, abajo, top, bottom)
# ------------------------
def mover_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    alfav.user_favorites = _mover_item(alfav.user_favorites, item.i_perfil, item.direccion)
    alfav.save()

    platformtools.itemlist_refresh()
    return True

def mover_enlace(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    alfav.user_favorites[item.i_perfil]['items'] = _mover_item(alfav.user_favorites[item.i_perfil]['items'], item.i_enlace, item.direccion)
    alfav.save()

    platformtools.itemlist_refresh()
    return True


# Mueve un item determinado (numérico) de una lista (arriba, abajo, top, bottom) y devuelve la lista modificada
def _mover_item(lista, i_selected, direccion):
    last_i = len(lista) - 1
    if i_selected > last_i or i_selected < 0: return lista # índice inexistente en lista

    if direccion == 'arriba':
        if i_selected == 0: # Ya está arriba de todo
            return lista
        lista.insert(i_selected - 1, lista.pop(i_selected))

    elif direccion == 'abajo':
        if i_selected == last_i: # Ya está abajo de todo
            return lista
        lista.insert(i_selected + 1, lista.pop(i_selected))

    elif direccion == 'top':
        if i_selected == 0: # Ya está arriba de todo
            return lista
        lista.insert(0, lista.pop(i_selected))

    elif direccion == 'bottom':
        if i_selected == last_i: # Ya está abajo de todo
            return lista
        lista.insert(last_i, lista.pop(i_selected))

    return lista
