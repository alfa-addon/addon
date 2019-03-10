# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand preferiti (I miei Link)
# ============================
# - Elenco di collegamenti salvati come preferiti, solo in Kodi on Demand, non in Kodi.
# - I collegamenti sono organizzati in cartelle che l'utente può definire.
# - Un singolo file viene utilizzato per salvare tutte le cartelle e i collegamenti: user_favorites.json
# - È possibile copiare user_favorites.json su altri dispositivi poiché l'unica dipendenza locale è il thumbnail associato ai collegamenti,
# ma viene rilevato dal codice e adattato al dispositivo corrente.

# Requisiti in altri moduli per eseguire questo canale:
# - Aggiungere un collegamento a questo canale in channelselector.py
# - Modificare platformtools.py per controllare il menu contestuale e aggiungere "Salva link" in set_context_commands
# ------------------------------------------------------------

import os, re

from core import filetools
from core import jsontools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools


# Classe da caricare e salvare nel file Kodpreferiti
# --------------------------------------------------------
class KodpreferitiData:

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
            self.user_favorites.append({ 'title': config.get_localized_string(70528), 'items': [] })
            self.save()

    def save(self):
        filetools.write(self.user_favorites_file, jsontools.dump(self.user_favorites))


# ============================
# Aggiungere dal menu contestuale
# ============================

def addFavourite(item):
    logger.info()
    icapref = KodpreferitiData()

    # Se arrivi qui tramite il menu di scelta rapida, devi recuperare i parametri di azione e canale
    if item.from_action:
        item.__dict__["action"] = item.__dict__.pop("from_action")
    if item.from_channel:
        item.__dict__["channel"] = item.__dict__.pop("from_channel")

    # Cancellare il titolo e rimuovere il colore
    item.title = re.sub(r'\[COLOR [^\]]*\]', '', item.title.replace('[/COLOR]', '')).strip()
    if item.text_color:
        item.__dict__.pop("text_color")

    # Finestra di dialogo per scegliere/creare una cartella
    i_perfil = _selecciona_perfil(icapref, config.get_localized_string(70546))
    if i_perfil == -1: return False

    # Rileva che lo stesso link non esiste già nella cartella
    campos = ['channel','action','url','extra'] # Se tutti questi campi corrispondono, si considera che il collegamento esiste già
    for enlace in icapref.user_favorites[i_perfil]['items']:
        it = Item().fromurl(enlace)
        repe = True
        for prop in campos:
            if prop in it.__dict__ and prop in item.__dict__ and it.__dict__[prop] != item.__dict__[prop]:
                repe = False
                break
        if repe:
            platformtools.dialog_notification(config.get_localized_string(70529), config.get_localized_string(70530))
            return False

    # Salvare
    icapref.user_favorites[i_perfil]['items'].append(item.tourl())
    icapref.save()

    platformtools.dialog_notification(config.get_localized_string(70531), config.get_localized_string(70532) % icapref.user_favorites[i_perfil]['title'])
    
    return True


# ====================
# NAVIGAZIONE
# ====================

def mainlist(item):
    logger.info()
    icapref = KodpreferitiData()

    itemlist = []
    last_i = len(icapref.user_favorites) - 1

    for i_perfil, perfil in enumerate(icapref.user_favorites):
        context = []

        context.append({'title': config.get_localized_string(70533), 'channel': item.channel, 'action': 'editar_perfil_titulo',
                        'i_perfil': i_perfil})
        context.append({'title': config.get_localized_string(70534), 'channel': item.channel, 'action': 'eliminar_perfil',
                        'i_perfil': i_perfil})

        if i_perfil > 0:
            context.append({'title': config.get_localized_string(70535), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'top'})
            context.append({'title': config.get_localized_string(70536), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'arriba'})
        if i_perfil < last_i:
            context.append({'title': config.get_localized_string(70537), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'abajo'})
            context.append({'title': config.get_localized_string(70538), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'bottom'})

        plot = config.get_localized_string(70556) % len(perfil['items'])
        itemlist.append(Item(channel=item.channel, action='mostrar_perfil', title=perfil['title'], plot=plot, i_perfil=i_perfil, context=context))

    plot = config.get_localized_string(70539)
    plot += config.get_localized_string(70540)
    plot += config.get_localized_string(70541)
    itemlist.append(item.clone(action='crear_perfil', title=config.get_localized_string(70542), plot=plot, folder=False)) 
    
    return itemlist


def mostrar_perfil(item):
    logger.info()
    icapref = KodpreferitiData()

    itemlist = []

    i_perfil = item.i_perfil
    if not icapref.user_favorites[i_perfil]: return itemlist
    last_i = len(icapref.user_favorites[i_perfil]['items']) - 1

    ruta_runtime = config.get_runtime_path()

    for i_enlace, enlace in enumerate(icapref.user_favorites[i_perfil]['items']):
        context = []

        if i_enlace > 0:
            context.append({'title': config.get_localized_string(70535), 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'top'})
            context.append({'title': config.get_localized_string(70536), 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'arriba'})
        if i_enlace < last_i:
            context.append({'title': config.get_localized_string(70537), 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'abajo'})
            context.append({'title': config.get_localized_string(70538), 'channel': item.channel, 'action': 'mover_enlace',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil, 'direccion': 'bottom'})

        if len(icapref.user_favorites) > 1: # se hai più di una cartella, permette di spostarti tra esse
            context.append({'title': config.get_localized_string(70543), 'channel': item.channel, 'action': 'editar_enlace_carpeta',
                            'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': config.get_localized_string(70544), 'channel': item.channel, 'action': 'editar_enlace_titulo',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': config.get_localized_string(70545), 'channel': item.channel, 'action': 'editar_enlace_color',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': config.get_localized_string(70547), 'channel': item.channel, 'action': 'editar_enlace_thumbnail',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        context.append({'title': config.get_localized_string(70548), 'channel': item.channel, 'action': 'eliminar_enlace',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil})

        it = Item().fromurl(enlace)
        it.context = context
        it.plot = '[COLOR blue]Canal: ' + it.channel + '[/COLOR][CR]' + it.plot

        # Se non è un url, né ha il percorso di sistema, converti il percorso poiché sarà stato copiato da un altro dispositivo.
        # Sarebbe più ottimale se la conversione fosse eseguita con un menu di importazione, ma per il momento è controllata in run-time.
        if it.thumbnail and '://' not in it.thumbnail and not it.thumbnail.startswith(ruta_runtime):
            ruta, fichero = filetools.split(it.thumbnail)
            if ruta == '' and fichero == it.thumbnail: # in Linux la divisione con un percorso di Windows non si separa correttamente
                ruta, fichero = filetools.split(it.thumbnail.replace('\\','/'))
            if 'channels' in ruta and 'thumb' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'channels', 'thumb', fichero)
            elif 'themes' in ruta and 'default' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'themes', 'default', fichero)

        itemlist.append(it)

    return itemlist


# Routine interne condivise
# ----------------------------

# Finestra di dialogo per selezionare/creare una cartella. Restituisce l'indice della cartella in user_favorites (-1 se cancella)
def _selecciona_perfil(icapref, titulo=config.get_localized_string(70549), i_actual=-1):
    acciones = [(perfil['title'] if i_p != i_actual else '[I][COLOR pink]%s[/COLOR][/I]' % perfil['title']) for i_p, perfil in enumerate(icapref.user_favorites)]
    acciones.append(config.get_localized_string(70550))

    i_perfil = -1
    while i_perfil == -1: # Ripeti fino a quando non selezioni una cartella o annulli
        ret = platformtools.dialog_select(titulo, acciones)
        if ret == -1: return -1 # richiesta annullata
        if ret < len(icapref.user_favorites):
            i_perfil = ret
        else: # creare nuova cartella
            if _crea_perfil(icapref):
                i_perfil = len(icapref.user_favorites) - 1

    return i_perfil


# Finestra di dialogo per creare una cartella
def _crea_perfil(icapref):
    titulo = platformtools.dialog_input(default='', heading=config.get_localized_string(70551))
    if titulo is None or titulo == '':
        return False

    icapref.user_favorites.append({'title': titulo, 'items': []})
    icapref.save()

    return True


# Gestione dei profili e dei link
# -----------------------------

def crear_perfil(item):
    logger.info()
    icapref = KodpreferitiData()

    if not _crea_perfil(icapref): return False

    platformtools.itemlist_refresh()
    return True


def editar_perfil_titulo(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False

    titulo = platformtools.dialog_input(default=icapref.user_favorites[item.i_perfil]['title'], heading=config.get_localized_string(70551))
    if titulo is None or titulo == '' or titulo == icapref.user_favorites[item.i_perfil]['title']:
        return False

    icapref.user_favorites[item.i_perfil]['title'] = titulo
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_perfil(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False

    # Chiedere conferma
    if not platformtools.dialog_yesno(config.get_localized_string(70534), config.get_localized_string(70552)): return False

    del icapref.user_favorites[item.i_perfil]
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_titulo(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    if not icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(icapref.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    titulo = platformtools.dialog_input(default=it.title, heading=config.get_localized_string(70553))
    if titulo is None or titulo == '' or titulo == it.title:
        return False
    
    it.title = titulo

    icapref.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_color(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    if not icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(icapref.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    colores = ['green','yellow','red','blue','white','orange','lime','aqua','pink','violet','purple','tomato','olive','antiquewhite','gold']
    opciones = ['[COLOR %s]%s[/COLOR]' % (col, col) for col in colores]

    ret = platformtools.dialog_select(config.get_localized_string(70558), opciones)

    if ret == -1: return False # richiesta annullata
    it.text_color = colores[ret]

    icapref.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_thumbnail(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    if not icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(icapref.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    # Da Kodi 17 puoi usare xbmcgui.Dialog (). Seleziona con thumbnails (ListItem & useDetails = True)
    is_kodi17 = (config.get_platform(True)['num_version'] >= 17.0)
    if is_kodi17:
        import xbmcgui

    # Finestra di dialogo per scegliere il thumnail (quello del canale o le icone predefinite)
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
        ret = xbmcgui.Dialog().select(config.get_localized_string(70554), opciones, useDetails=True)
    else:
        ret = platformtools.dialog_select(config.get_localized_string(70554), opciones)

    if ret == -1: return False # richiesta annullata

    it.thumbnail = ids[ret]

    icapref.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_carpeta(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    if not icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    # Finestra di dialogo per scegliere/creare una cartella
    i_perfil = _selecciona_perfil(icapref, config.get_localized_string(70555), item.i_perfil)
    if i_perfil == -1 or i_perfil == item.i_perfil: return False

    icapref.user_favorites[i_perfil]['items'].append(icapref.user_favorites[item.i_perfil]['items'][item.i_enlace])
    del icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]
    icapref.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_enlace(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    if not icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    del icapref.user_favorites[item.i_perfil]['items'][item.i_enlace]
    icapref.save()

    platformtools.itemlist_refresh()
    return True


# Sposta profili e collegamenti (su, giù, in alto, in basso)
# ------------------------
def mover_perfil(item):
    logger.info()
    icapref = KodpreferitiData()

    icapref.user_favorites = _mover_item(icapref.user_favorites, item.i_perfil, item.direccion)
    icapref.save()

    platformtools.itemlist_refresh()
    return True

def mover_enlace(item):
    logger.info()
    icapref = KodpreferitiData()

    if not icapref.user_favorites[item.i_perfil]: return False
    icapref.user_favorites[item.i_perfil]['items'] = _mover_item(icapref.user_favorites[item.i_perfil]['items'], item.i_enlace, item.direccion)
    icapref.save()

    platformtools.itemlist_refresh()
    return True


# Sposta un oggetto (numerico) specifico da un elenco (su, giù, in alto, in basso) e restituisce l'elenco modificato
def _mover_item(lista, i_selected, direccion):
    last_i = len(lista) - 1
    if i_selected > last_i or i_selected < 0: return lista # indice inesistente nella lista

    if direccion == 'arriba':
        if i_selected == 0: # È già al di sopra di tutto
            return lista
        lista.insert(i_selected - 1, lista.pop(i_selected))

    elif direccion == 'abajo':
        if i_selected == last_i: # È già al di sopra di tutto
            return lista
        lista.insert(i_selected + 1, lista.pop(i_selected))

    elif direccion == 'top':
        if i_selected == 0: # È già al di sopra di tutto
            return lista
        lista.insert(0, lista.pop(i_selected))

    elif direccion == 'bottom':
        if i_selected == last_i: # È già al di sopra di tutto
            return lista
        lista.insert(last_i, lista.pop(i_selected))

    return lista
