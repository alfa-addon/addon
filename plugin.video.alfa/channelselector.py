# -*- coding: utf-8 -*-

import glob
import os

from core import channeltools
from core.item import Item
from platformcode import config, logger


def getmainlist(view="thumb_"):
    logger.info()
    itemlist = list()

    # Añade los canales que forman el menú principal
    itemlist.append(Item(title=config.get_localized_string(30130), channel="news", action="mainlist",
                         thumbnail=get_thumb("news.png", view),
                         category=config.get_localized_string(30119), viewmode="thumbnails",
                         context=[{"title": "Configurar Novedades", "channel": "news", "action": "menu_opciones",
                                   "goto": True}]))

    itemlist.append(Item(title=config.get_localized_string(30118), channel="channelselector", action="getchanneltypes",
                         thumbnail=get_thumb("channels.png", view), view=view,
                         category=config.get_localized_string(30119), viewmode="thumbnails"))

    itemlist.append(Item(title=config.get_localized_string(30103), channel="search", action="mainlist",
                         thumbnail=get_thumb("search.png", view),
                         category=config.get_localized_string(30119), viewmode="list",
                         context=[{"title": "Configurar Buscador", "channel": "search", "action": "opciones",
                                   "goto": True}]))

    itemlist.append(Item(title=config.get_localized_string(30102), channel="favorites", action="mainlist",
                         thumbnail=get_thumb("favorites.png", view),
                         category=config.get_localized_string(30102), viewmode="thumbnails"))

    if config.get_videolibrary_support():
        itemlist.append(Item(title=config.get_localized_string(30131), channel="videolibrary", action="mainlist",
                             thumbnail=get_thumb("videolibrary.png", view),
                             category=config.get_localized_string(30119), viewmode="thumbnails",
                             context=[{"title": "Configurar Videoteca", "channel": "videolibrary",
                                       "action": "channel_config"}]))

    itemlist.append(Item(title=config.get_localized_string(30101), channel="downloads", action="mainlist",
                         thumbnail=get_thumb("downloads.png", view), viewmode="list",
                         context=[{"title": "Configurar Descargas", "channel": "setting", "config": "downloads",
                                   "action": "channel_config"}]))

    thumb_configuracion = "setting_%s.png" % 0  # config.get_setting("plugin_updates_available")

    itemlist.append(Item(title=config.get_localized_string(30100), channel="setting", action="mainlist",
                         thumbnail=get_thumb(thumb_configuracion, view),
                         category=config.get_localized_string(30100), viewmode="list"))
    # TODO REVISAR LA OPCION AYUDA
    # itemlist.append(Item(title=config.get_localized_string(30104), channel="help", action="mainlist",
    #                      thumbnail=get_thumb("help.png", view),
    #                      category=config.get_localized_string(30104), viewmode="list"))
    return itemlist


def getchanneltypes(view="thumb_"):
    logger.info()

    # Lista de categorias
    channel_types = ["movie", "tvshow", "anime", "documentary", "vos", "direct", "torrent", "latino"]
    dict_types_lang = {'movie': config.get_localized_string(30122), 'tvshow': config.get_localized_string(30123),
                       'anime': config.get_localized_string(30124), 'documentary': config.get_localized_string(30125),
                       'vos': config.get_localized_string(30136), 'adult': config.get_localized_string(30126),
                       'latino': config.get_localized_string(30127), 'direct': config.get_localized_string(30137)}

    if config.get_setting("adult_mode") != 0:
        channel_types.append("adult")

    channel_language = config.get_setting("channel_language")
    logger.info("channel_language=" + channel_language)

    # Ahora construye el itemlist ordenadamente
    itemlist = list()
    title = config.get_localized_string(30121)
    itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", view=view,
                         category=title, channel_type="all", thumbnail=get_thumb("channels_all.png", view),
                         viewmode="thumbnails"))

    for channel_type in channel_types:
        logger.info("channel_type=" + channel_type)
        title = dict_types_lang.get(channel_type, channel_type)
        itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", category=title,
                             channel_type=channel_type, viewmode="thumbnails",
                             thumbnail=get_thumb("channels_" + channel_type + ".png", view)))

    return itemlist


def filterchannels(category, view="thumb_"):
    logger.info()

    channelslist = []

    # Si category = "allchannelstatus" es que estamos activando/desactivando canales
    appenddisabledchannels = False
    if category == "allchannelstatus":
        category = "all"
        appenddisabledchannels = True

    # Lee la lista de canales
    channel_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    logger.info("channel_path=" + channel_path)

    channel_files = glob.glob(channel_path)
    logger.info("channel_files encontrados " + str(len(channel_files)))

    channel_language = config.get_setting("channel_language")
    logger.info("channel_language=" + channel_language)
    if channel_language == "":
        channel_language = "all"
        logger.info("channel_language=" + channel_language)

    for channel_path in channel_files:
        logger.info("channel=" + channel_path)

        channel = os.path.basename(channel_path).replace(".json", "")

        try:
            channel_parameters = channeltools.get_channel_parameters(channel)

            # si el canal no es compatible, no se muestra
            if not channel_parameters["compatible"]:
                continue

            # Si no es un canal lo saltamos
            if not channel_parameters["channel"]:
                continue
            logger.info("channel_parameters=" + repr(channel_parameters))

            # Si prefiere el banner y el canal lo tiene, cambia ahora de idea
            if view == "banner_" and "banner" in channel_parameters:
                channel_parameters["thumbnail"] = channel_parameters["banner"]

            # si el canal está desactivado no se muestra el canal en la lista
            if not channel_parameters["active"]:
                continue

            # Se salta el canal si no está activo y no estamos activando/desactivando los canales
            channel_status = config.get_setting("enabled", channel_parameters["channel"])

            if channel_status is None:
                # si channel_status no existe es que NO HAY valor en _data.json.
                # como hemos llegado hasta aquí (el canal está activo en channel.json), se devuelve True
                channel_status = True

            if not channel_status:
                # si obtenemos el listado de canales desde "activar/desactivar canales", y el canal está desactivado
                # lo mostramos, si estamos listando todos los canales desde el listado general y está desactivado,
                # no se muestra
                if not appenddisabledchannels:
                    continue

            # Se salta el canal para adultos si el modo adultos está desactivado
            if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
                continue

            # Se salta el canal si está en un idioma filtrado
            if channel_language != "all" \
                    and channel_parameters["language"] != config.get_setting("channel_language"):
                continue

            # Se salta el canal si está en una categoria filtrado
            if category != "all" and category not in channel_parameters["categories"]:
                continue

            # Si tiene configuración añadimos un item en el contexto
            context = []
            if channel_parameters["has_settings"]:
                context.append({"title": "Configurar canal", "channel": "setting", "action": "channel_config",
                                "config": channel_parameters["channel"]})

            # Si ha llegado hasta aquí, lo añade
            channelslist.append(Item(title=channel_parameters["title"], channel=channel_parameters["channel"],
                                     action="mainlist", thumbnail=channel_parameters["thumbnail"],
                                     fanart=channel_parameters["fanart"], category=channel_parameters["title"],
                                     language=channel_parameters["language"], viewmode="list",
                                     version=channel_parameters["version"], context=context))

        except:
            logger.error("Se ha producido un error al leer los datos del canal " + channel)
            import traceback
            logger.error(traceback.format_exc())

    channelslist.sort(key=lambda item: item.title.lower().strip())

    if category == "all":

        channel_parameters = channeltools.get_channel_parameters('url')
        # Si prefiere el banner y el canal lo tiene, cambia ahora de idea
        if view == "banner_" and "banner" in channel_parameters:
            channel_parameters["thumbnail"] = channel_parameters["banner"]

        channelslist.insert(0, Item(title="Tengo una URL", action="mainlist", channel="url",
                                    thumbnail=channel_parameters["thumbnail"], type="generic", viewmode="list"))

    return channelslist


def get_thumb(thumb_name, view="thumb_"):

    path = os.path.join(config.get_runtime_path(), "resources", "media", "general")

    # if config.get_setting("icons"):  # TODO obtener de la configuración el pack de thumbs seleccionado
    #     selected_icon = config.get_setting("icons")
    # else:
    #     selected_icon = os.sep + "default"

    selected_icon = os.sep + "default"
    web_path = path + selected_icon + os.sep

    return os.path.join(web_path, view + thumb_name)
