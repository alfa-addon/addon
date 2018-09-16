# -*- coding: utf-8 -*-

import glob
import os

from core import channeltools
from core.item import Item
from platformcode.unify import thumb_dict
from platformcode import config, logger, unify


def getmainlist(view="thumb_"):
    logger.info()
    itemlist = list()

    # Añade los canales que forman el menú principal
    itemlist.append(Item(title=config.get_localized_string(30130), channel="news", action="mainlist",
                         thumbnail=get_thumb("news.png", view),
                         category=config.get_localized_string(30119), viewmode="thumbnails",
                         context=[{"title": config.get_localized_string(70285), "channel": "news", "action": "menu_opciones",
                                   "goto": True}]))

    itemlist.append(Item(title=config.get_localized_string(30118), channel="channelselector", action="getchanneltypes",
                         thumbnail=get_thumb("channels.png", view), view=view,
                         category=config.get_localized_string(30119), viewmode="thumbnails"))

    itemlist.append(Item(title=config.get_localized_string(70527), channel="alfavorites", action="mainlist",
                         thumbnail=get_thumb("mylink.png", view), view=view,
                         category=config.get_localized_string(70527), viewmode="thumbnails"))

    itemlist.append(Item(title=config.get_localized_string(30103), channel="search", action="mainlist",
                         thumbnail=get_thumb("search.png", view),
                         category=config.get_localized_string(30119), viewmode="list",
                         context=[{"title": config.get_localized_string(70286), "channel": "search", "action": "opciones",
                                   "goto": True}]))

    itemlist.append(Item(title=config.get_localized_string(30102), channel="favorites", action="mainlist",
                         thumbnail=get_thumb("favorites.png", view),
                         category=config.get_localized_string(30102), viewmode="thumbnails"))

    if config.get_videolibrary_support():
        itemlist.append(Item(title=config.get_localized_string(30131), channel="videolibrary", action="mainlist",
                             thumbnail=get_thumb("videolibrary.png", view),
                             category=config.get_localized_string(30119), viewmode="thumbnails",
                             context=[{"title": config.get_localized_string(70287), "channel": "videolibrary",
                                       "action": "channel_config"}]))

    itemlist.append(Item(title=config.get_localized_string(30101), channel="downloads", action="mainlist",
                         thumbnail=get_thumb("downloads.png", view), viewmode="list",
                         context=[{"title": config.get_localized_string(70288), "channel": "setting", "config": "downloads",
                                   "action": "channel_config"}]))

    thumb_setting = "setting_%s.png" % 0  # config.get_setting("plugin_updates_available")

    itemlist.append(Item(title=config.get_localized_string(30100), channel="setting", action="mainlist",
                         thumbnail=get_thumb(thumb_setting, view),
                         category=config.get_localized_string(30100), viewmode="list"))

    itemlist.append(Item(title=config.get_localized_string(30104) + " (" + config.get_localized_string(20000) +" " + config.get_addon_version(with_fix=False) + ")", channel="help", action="mainlist",
                         thumbnail=get_thumb("help.png", view),
                         category=config.get_localized_string(30104), viewmode="list"))
    return itemlist


def getchanneltypes(view="thumb_"):
    logger.info()

    # Lista de categorias
    channel_types = ["movie", "tvshow", "anime", "documentary", "vos", "direct", "torrent"]

    if config.get_setting("adult_mode") != 0:
        channel_types.append("adult")

    channel_language = config.get_setting("channel_language", default="all")
    logger.info("channel_language=%s" % channel_language)

    # Ahora construye el itemlist ordenadamente
    itemlist = list()
    title = config.get_localized_string(30121)
    itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", view=view,
                         category=title, channel_type="all", thumbnail=get_thumb("channels_all.png", view),
                         viewmode="thumbnails"))

    for channel_type in channel_types:
        title = config.get_localized_category(channel_type)
        itemlist.append(Item(title=title, channel="channelselector", action="filterchannels", category=title,
                             channel_type=channel_type, viewmode="thumbnails",
                             thumbnail=get_thumb("channels_%s.png" % channel_type, view)))

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
    logger.info("channel_path=%s" % channel_path)

    channel_files = glob.glob(channel_path)
    logger.info("channel_files encontrados %s" % (len(channel_files)))

    channel_language = config.get_setting("channel_language", default="all")
    logger.info("channel_language=%s" % channel_language)

    for channel_path in channel_files:
        logger.info("channel=%s" % channel_path)

        channel = os.path.basename(channel_path).replace(".json", "")

        try:
            channel_parameters = channeltools.get_channel_parameters(channel)

            # si el canal no es compatible, no se muestra
            if not channel_parameters["compatible"]:
                continue

            # Si no es un canal lo saltamos
            if not channel_parameters["channel"]:
                continue
            logger.info("channel_parameters=%s" % repr(channel_parameters))

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
            # Se muestran todos los canales si se elige "all" en el filtrado de idioma
            # Se muestran sólo los idiomas filtrados, cast o lat
            # Los canales de adultos se mostrarán siempre que estén activos
            if channel_language != "all" and channel_language not in channel_parameters["language"] \
                    and "*" not in channel_parameters["language"]:
                continue

            # Se salta el canal si está en una categoria filtrado
            if category != "all" and category not in channel_parameters["categories"]:
                continue

            # Si tiene configuración añadimos un item en el contexto
            context = []
            if channel_parameters["has_settings"]:
                context.append({"title": config.get_localized_string(70525), "channel": "setting", "action": "channel_config",
                                "config": channel_parameters["channel"]})

            channel_info = set_channel_info(channel_parameters)
            # Si ha llegado hasta aquí, lo añade
            channelslist.append(Item(title=channel_parameters["title"], channel=channel_parameters["channel"],
                                     action="mainlist", thumbnail=channel_parameters["thumbnail"],
                                     fanart=channel_parameters["fanart"], plot=channel_info, category=channel_parameters["title"],
                                     language=channel_parameters["language"], viewmode="list", context=context))

        except:
            logger.error("Se ha producido un error al leer los datos del canal '%s'" % channel)
            import traceback
            logger.error(traceback.format_exc())

    channelslist.sort(key=lambda item: item.title.lower().strip())

    if category == "all":
        channel_parameters = channeltools.get_channel_parameters('url')
        # Si prefiere el banner y el canal lo tiene, cambia ahora de idea
        if view == "banner_" and "banner" in channel_parameters:
            channel_parameters["thumbnail"] = channel_parameters["banner"]

        channelslist.insert(0, Item(title=config.get_localized_string(60088), action="mainlist", channel="url",
                                    thumbnail=channel_parameters["thumbnail"], type="generic", viewmode="list"))

    if category in ['movie', 'tvshow']:
        titles = [config.get_localized_string(70028), config.get_localized_string(30985), config.get_localized_string(70559), config.get_localized_string(60264), config.get_localized_string(70560)]
        ids = ['popular', 'top_rated', 'now_playing', 'on_the_air']
        for x in range(0,3):
            if x == 2 and category != 'movie':
                title=titles[x+1]
                id = ids[x+1]
            else:
                title=titles[x]
                id = ids[x]
            channelslist.insert(x,
                Item(channel='search', action='discover_list', title=title, search_type='list',
                     list_type='%s/%s' % (category.replace('show',''), id), thumbnail=get_thumb(id+".png")))

        channelslist.insert(3, Item(channel='search', action='genres_menu', title='Generos',
                                    type=category.replace('show',''), thumbnail=get_thumb("genres.png")))

    return channelslist


def get_thumb(thumb_name, view="thumb_", auto=False):

    if auto:
        thumbnail = ''

        thumb_name = unify.set_genre(unify.simplify(thumb_name))


        if thumb_name in thumb_dict:
            thumbnail = thumb_dict[thumb_name]
        return thumbnail
    else:
        icon_pack_name = config.get_setting('icon_set', default="default")
        if icon_pack_name == "default":
            resource_path = os.path.join(config.get_runtime_path(), "resources", "media", "themes")
        else:
            resource_path = "https://raw.githubusercontent.com/alfa-addon/media/master/themes/"

        media_path = os.path.join(resource_path, icon_pack_name)

        return os.path.join(media_path, view + thumb_name)


def set_channel_info(parameters):
    logger.info()

    info = ''
    language = ''
    content = ''
    langs = parameters['language']
    lang_dict = {'lat':'Latino', 'cast':'Castellano', '*':'Latino, Castellano, VOSE, VO'}
    for lang in langs:
        if 'vos' in parameters['categories']:
            lang = '*'

        if lang in lang_dict:
            if language != '' and language != '*' and not parameters['adult']:
                language = '%s, %s' % (language, lang_dict[lang])
            elif not parameters['adult']:
                language = lang_dict[lang]
        if lang == '*':
            break

    categories = parameters['categories']
    for cat in categories:
        if content != '':
            content = '%s, %s' % (content, config.get_localized_category(cat))
        else:
            content = config.get_localized_category(cat)

    info = '[COLOR yellow]Tipo de contenido:[/COLOR] %s\n\n[COLOR yellow]Idiomas:[/COLOR] %s' % (content, language)
    return info
