# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Lista de vídeos favoritos
# ------------------------------------------------------------
import xbmc
from core import filetools
from core import scrapertools
from core.item import Item
from core.jsontools import json
from platformcode import config, logger
from platformcode import platformtools

# Fijamos la ruta a favourites.xml
if config.is_xbmc():

    FAVOURITES_PATH = filetools.translatePath("special://profile/favourites.xml")
else:
    FAVOURITES_PATH = filetools.join(config.get_data_path(), "favourites.xml")


def mainlist(item):
    logger.info()
    itemlist = []

    for name, thumb, data in read_favourites():
        if "plugin://plugin.video.%s/?" % config.PLUGIN_NAME in data:
            # Windows usa la entidad html &quot; para las comillas, Android no. 
            # Así que me aseguro de decodificar las comillas para normalizar.
            data = data.replace("&quot;", '"')
            url = scrapertools.find_single_match(data, 'plugin://plugin.video.%s/\?([^"]*)' % config.PLUGIN_NAME)
            item = Item().fromurl(url)
            item.title = name
            item.thumbnail = thumb
            item.isFavourite = True

            if isinstance(item.context, str):
                item.context = item.context.split("|")
            elif not isinstance(item.context, list):
                item.context = []

            item.context.extend([{"title": config.get_localized_string(30154),  # "Quitar de favoritos"
                                  "action": "delFavourite",
                                  "module": "favorites",
                                  "from_title": item.title},
                                 {"title": config.get_localized_string(70278),  # "Renombrar"
                                  "action": "renameFavourite",
                                  "module": "favorites",
                                  "from_title": item.title}
                                 ])
            # logger.debug(item.tostring('\n'))
            itemlist.append(item)

    return itemlist


def read_favourites():
    logger.info()
    favourites_list = []
    if filetools.exists(FAVOURITES_PATH):
        data = filetools.read(FAVOURITES_PATH)

        matches = scrapertools.find_multiple_matches(data, "<favourite([^<]*)</favourite>")
        for match in matches:
            name = scrapertools.find_single_match(match, 'name="([^"]*)')
            thumb = scrapertools.find_single_match(match, 'thumb="([^"]*)')
            data = scrapertools.find_single_match(match, '[^>]*>([^<]*)')
            favourites_list.append((name, thumb, data))

    return favourites_list


def save_favourites(favourites_list):
    logger.info()
    raw = '<favourites>' + chr(10)
    for name, thumb, data in favourites_list:
        raw += '    <favourite name="%s" thumb="%s">%s</favourite>' % (name, thumb, data) + chr(10)
    raw += '</favourites>' + chr(10)

    return filetools.write(FAVOURITES_PATH, raw)


def get_favourite(item):
    logger.info()
    fav_item = dict()
    for favourite in get_favourites():
        if favourite['title'] == item.from_title:
            fav_item = favourite
            break

    return fav_item


def add_remove_favourite(item):
    logger.info()
    # Comportamiento de Favourites.AddFavourite : Si existe el item se borra, si no existe se añade
    if item.isFavourite:
        favourite = get_favourite(item)
    else:
        favourite = {
          "title": item.title,
          "type": "window",
          "window": "10025",
          "windowparameter": "plugin://plugin.video.%s/?" % config.PLUGIN_NAME + item.tourl().replace('%3D','%3d'),
          "thumbnail": item.thumbnail
        }

    request = {
      "jsonrpc": "2.0",
      "method": "Favourites.AddFavourite",
      "params": favourite,
      "id": 1
    }

    return json.loads(xbmc.executeJSONRPC(json.dumps(request)))


def get_favourites():
    logger.info()
    request = {
      "jsonrpc": "2.0",
      "method": "Favourites.GetFavourites",
      "params": {
        "properties": ["path","window","windowparameter","thumbnail"]
      },
      "id": 1
    }

    return json.loads(xbmc.executeJSONRPC(json.dumps(request)))['result']['favourites']


def addFavourite(item):
    logger.info()
    response = add_remove_favourite(item)
    if response['result'] == 'OK':
        platformtools.dialog_ok(config.get_localized_string(30102), item.title,
                                config.get_localized_string(30108))  # 'se ha añadido a favoritos'


def delFavourite(item):
    logger.info()
    response = add_remove_favourite(item)
    if response['result'] == 'OK':
        platformtools.dialog_ok(config.get_localized_string(30102), item.from_title,
                                config.get_localized_string(30105).lower())  # 'Se ha quitado de favoritos'
        platformtools.itemlist_refresh()


def renameFavourite(item):
    logger.info()
    # logger.debug(item.tostring('\n'))

    # Buscar el item q queremos renombrar en favourites.xml
    favourites_list = read_favourites()
    for i, fav in enumerate(favourites_list):
        if fav[0] == item.from_title:
            # abrir el teclado
            new_title = platformtools.dialog_input(item.from_title, item.title)
            if new_title:
                favourites_list[i] = (new_title, fav[1], fav[2])
                if save_favourites(favourites_list):
                    platformtools.dialog_ok(config.get_localized_string(30102), item.from_title,
                                            "se ha renombrado como:", new_title)  # 'Se ha quitado de favoritos'
                    platformtools.itemlist_refresh()

