# -*- coding: utf-8 -*-

import glob
import os
import re
import time
from threading import Thread

from channelselector import get_thumb
from core import channeltools
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from core import tmdb

link_list = []
max_links = 30


def mainlist(item):
    logger.info()
    item.channel = "search"

    itemlist = []
    context = [{"title": "Elegir canales incluidos", "action": "setting_channel", "channel": item.channel}]
    itemlist.append(Item(channel=item.channel, action="sub_menu", title="Buscar en canales", context=context,
                         thumbnail=get_thumb("search.png")))

    itemlist.append(Item(channel=item.channel, action='genres_menu', title='Películas por Generos', type='movie'))

    itemlist.append (Item(channel=item.channel, action='discover_list', title='Películas mas populares',
                          context=context,
                          search_type='list', list_type='movie/popular'))

    itemlist.append(Item(channel=item.channel, action='discover_list', title='Películas mejor valoradas',
                         context=context,
                         search_type='list', list_type='movie/top_rated'))

    itemlist.append(
        Item(channel=item.channel, action='discover_list', title='Películas Ahora en cines', context=context,
             search_type='list',
             list_type='movie/now_playing'))

    itemlist.append(Item(channel=item.channel, action='genres_menu', title='Series por Generos', type='tv'))

    itemlist.append(
        Item(channel=item.channel, action='discover_list', title='Series mas populares', context=context,
             search_type='list',list_type='tv/popular'))

    itemlist.append(Item(channel=item.channel, action='discover_list', title='Series en emisión', context=context,
                         search_type='list', list_type='tv/on_the_air'))


    itemlist.append(Item(channel=item.channel, action='discover_list', title='Series mejor valoradas', context=context,
                         search_type='list', list_type='tv/top_rated'))




    return itemlist


def genres_menu(item):

    itemlist = []

    genres = tmdb.get_genres(item.type)

    logger.debug(genres)
    logger.debug(genres[item.type])

    for key, value in genres[item.type].items():
        itemlist.append(item.clone(title=value, action='discover_list', search_type='discover',
                                   list_type=key, page='1'))
    return sorted(itemlist, key=lambda it: it.title)

def sub_menu(item):
    logger.info()
    item.channel = "search"

    itemlist = list()
    context = [{"title": "Elegir canales incluidos",
                "action": "setting_channel",
                "channel": item.channel}]
    itemlist.append(Item(channel=item.channel, action="search",
                         title="Buscar por titulo", context=context,
                         thumbnail=get_thumb("search.png")))

    thumbnail = get_thumb("search_star.png")

    itemlist.append(Item(channel='tvmoviedb', title="Buscar actor/actriz", action="search_",
                         search={'url': 'search/person', 'language': 'es', 'page': 1}, star=True,
                         thumbnail=thumbnail))

    itemlist.append(Item(channel=item.channel, action="search",
                         title="Buscar por categorias (búsqueda avanzada)", extra="categorias",
                         context=context,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="opciones", title="Opciones",
                         thumbnail=get_thumb("search.png")))

    itemlist.append(Item(channel="tvmoviedb", action="mainlist", title="Búsqueda alternativa",
                         thumbnail=get_thumb("search.png")))

    saved_searches_list = get_saved_searches()
    context2 = context[:]
    context2.append({"title": "Borrar búsquedas guardadas",
                     "action": "clear_saved_searches",
                     "channel": item.channel})
    logger.info("saved_searches_list=%s" % saved_searches_list)

    if saved_searches_list:
        itemlist.append(Item(channel=item.channel, action="",
                             title="Búsquedas guardadas:", context=context2,
                             thumbnail=get_thumb("search.png")))
        for saved_search_text in saved_searches_list:
            itemlist.append(Item(channel=item.channel, action="do_search",
                                 title='    "' + saved_search_text + '"',
                                 extra=saved_search_text, context=context2,
                                 category=saved_search_text,
                                 thumbnail=get_thumb("search.png")))

    return itemlist


def opciones(item):
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="setting_channel",
                         title="Elegir canales incluidos en la búsqueda", folder=False,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="clear_saved_searches", title="Borrar búsquedas guardadas",
                         folder=False, thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=item.channel, action="settings", title="Otros ajustes", folder=False,
                         thumbnail=get_thumb("search.png")))
    return itemlist


def settings(item):
    return platformtools.show_channel_settings(caption="configuración -- Buscador")


def setting_channel(item):
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    channel_language = config.get_setting("channel_language", default="all")

    list_controls = []
    for infile in sorted(glob.glob(channels_path)):
        channel_name = os.path.basename(infile)[:-5]
        channel_parameters = channeltools.get_channel_parameters(channel_name)

        # No incluir si es un canal inactivo
        if not channel_parameters["active"]:
            continue

        # No incluir si es un canal para adultos, y el modo adulto está desactivado
        if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
            continue

        # No incluir si el canal es en un idioma filtrado
        if channel_language != "all" and channel_language not in channel_parameters["language"] \
                and "*" not in channel_parameters["language"]:
            continue

        # No incluir si en la configuracion del canal no existe "include_in_global_search"
        include_in_global_search = channel_parameters["include_in_global_search"]

        if not include_in_global_search:
            continue
        else:
            # Se busca en la configuración del canal el valor guardado
            include_in_global_search = config.get_setting("include_in_global_search", channel_name)

        control = {'id': channel_name,
                   'type': "bool",
                   'label': channel_parameters["title"],
                   'default': include_in_global_search,
                   'enabled': True,
                   'visible': True}

        list_controls.append(control)

    if config.get_setting("custom_button_value", item.channel):
        custom_button_label = "Ninguno"
    else:
        custom_button_label = "Todos"

    return platformtools.show_channel_settings(list_controls=list_controls,
                                               caption="Canales incluidos en la búsqueda",
                                               callback="save_settings", item=item,
                                               custom_button={'visible': True,
                                                              'function': "cb_custom_button",
                                                              'close': False,
                                                              'label': custom_button_label})


def save_settings(item, dict_values):
    progreso = platformtools.dialog_progress("Guardando configuración...", "Espere un momento por favor.")
    n = len(dict_values)
    for i, v in enumerate(dict_values):
        progreso.update((i * 100) / n, "Guardando configuración...")
        config.set_setting("include_in_global_search", dict_values[v], v)

    progreso.close()


def cb_custom_button(item, dict_values):
    value = config.get_setting("custom_button_value", item.channel)
    if value == "":
        value = False

    for v in dict_values.keys():
        dict_values[v] = not value

    if config.set_setting("custom_button_value", not value, item.channel) == True:
        return {"label": "Ninguno"}
    else:
        return {"label": "Todos"}


def searchbycat(item):
    # Only in xbmc/kodi
    # Abre un cuadro de dialogo con las categorías en las que hacer la búsqueda

    categories = ["Películas", "Series", "Anime", "Documentales", "VOS", "Latino"]
    categories_id = ["movie", "tvshow", "anime", "documentary", "vos", "latino"]
    list_controls = []
    for i, category in enumerate(categories):
        control = {'id': categories_id[i],
                   'type': "bool",
                   'label': category,
                   'default': False,
                   'enabled': True,
                   'visible': True}

        list_controls.append(control)
    control = {'id': "separador",
               'type': "label",
               'label': '',
               'default': "",
               'enabled': True,
               'visible': True}
    list_controls.append(control)
    control = {'id': "torrent",
               'type': "bool",
               'label': 'Incluir en la búsqueda canales Torrent',
               'default': True,
               'enabled': True,
               'visible': True}
    list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, caption="Elegir categorías",
                                               callback="search_cb", item=item)


def search_cb(item, values=""):
    cat = []
    for c in values:
        if values[c]:
            cat.append(c)

    if not len(cat):
        return None
    else:
        logger.info(item.tostring())
        logger.info(str(cat))
        return do_search(item, cat)


# Al llamar a esta función, el sistema pedirá primero el texto a buscar
# y lo pasará en el parámetro "tecleado"
def search(item, tecleado):
    logger.info()
    tecleado = tecleado.replace("+", " ")
    item.category = tecleado

    if tecleado != "":
        save_search(tecleado)

    if item.extra == "categorias":
        item.extra = tecleado
        itemlist = searchbycat(item)
    else:
        item.extra = tecleado
        itemlist = do_search(item, [])

    return itemlist


def show_result(item):
    tecleado = None
    if item.adult and config.get_setting("adult_request_password"):
        # Solicitar contraseña
        tecleado = platformtools.dialog_input("", "Contraseña para canales de adultos", True)
        if tecleado is None or tecleado != config.get_setting("adult_password"):
            return []

    item.channel = item.__dict__.pop('from_channel')
    item.action = item.__dict__.pop('from_action')
    if item.__dict__.has_key('tecleado'):
        tecleado = item.__dict__.pop('tecleado')

    try:
        channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
    except:
        import traceback
        logger.error(traceback.format_exc())
        return []

    if tecleado:
        # Mostrar resultados: agrupados por canales
        return channel.search(item, tecleado)
    else:
        # Mostrar resultados: todos juntos
        try:
            from platformcode import launcher
            launcher.run(item)
        except ImportError:
            return getattr(channel, item.action)(item)


def channel_search(search_results, channel_parameters, tecleado):
    try:
        exec "from channels import " + channel_parameters["channel"] + " as module"
        mainlist = module.mainlist(Item(channel=channel_parameters["channel"]))
        search_items = [item for item in mainlist if item.action == "search"]
        if not search_items:
            search_items = [Item(channel=channel_parameters["channel"], action="search")]

        for item in search_items:
            result = module.search(item.clone(), tecleado)
            if result is None:
                result = []
            if len(result):
                if not channel_parameters["title"].capitalize() in search_results:
                    search_results[channel_parameters["title"].capitalize()] = []
                search_results[channel_parameters["title"].capitalize()].append({"item": item,
                                                                    "itemlist": result,
                                                                    "adult": channel_parameters["adult"]})

    except:
        logger.error("No se puede buscar en: %s" % channel_parameters["title"])
        import traceback
        logger.error(traceback.format_exc())


# Esta es la función que realmente realiza la búsqueda
def do_search(item, categories=None):
    logger.info("blaa categorias %s" % categories)

    if item.contextual==True:
        categories = ["Películas"]
        setting_item = Item(channel=item.channel, title="Elegir canales incluidos en la búsqueda", folder=False,
                            thumbnail=get_thumb("search.png"))
        setting_channel(setting_item)


    if categories is None:
        categories = []

    multithread = config.get_setting("multithread", "search")
    result_mode = config.get_setting("result_mode", "search")

    if item.wanted!='':
        tecleado=item.wanted
    else:
        tecleado = item.extra

    itemlist = []

    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    logger.info("channels_path=%s" % channels_path)

    channel_language = config.get_setting("channel_language", default="all")
    logger.info("channel_language=%s" % channel_language)

    # Para Kodi es necesario esperar antes de cargar el progreso, de lo contrario
    # el cuadro de progreso queda "detras" del cuadro "cargando..." y no se le puede dar a cancelar
    time.sleep(0.5)
    progreso = platformtools.dialog_progress("Buscando '%s'..." % tecleado, "")
    channel_files = sorted(glob.glob(channels_path), key=lambda x: os.path.basename(x))

    import math
    # fix float porque la division se hace mal en python 2.x
    number_of_channels = float(100) / len(channel_files)

    threads = []
    search_results = {}
    start_time = time.time()

    for index, infile in enumerate(channel_files):
        try:
            percentage = int(math.ceil((index + 1) * number_of_channels))

            basename = os.path.basename(infile)
            basename_without_extension = basename[:-5]
            logger.info("%s..." % basename_without_extension)

            channel_parameters = channeltools.get_channel_parameters(basename_without_extension)

            # No busca si es un canal inactivo
            if not channel_parameters["active"]:
                logger.info("%s -no activo-" % basename_without_extension)
                continue

            # En caso de búsqueda por categorias
            if categories:

                # Si no se ha seleccionado torrent no se muestra
                if "torrent" not in categories:
                    if "torrent" in channel_parameters["categories"]:
                        logger.info("%s -torrent-" % basename_without_extension)
                        continue

                for cat in categories:
                    if cat not in channel_parameters["categories"]:
                        logger.info("%s -no en %s-" % (basename_without_extension, cat))
                        continue

            # No busca si es un canal para adultos, y el modo adulto está desactivado
            if channel_parameters["adult"] and config.get_setting("adult_mode") == 0:
                logger.info("%s -adulto-" % basename_without_extension)
                continue

            # No busca si el canal es en un idioma filtrado
            if channel_language != "all" and channel_language not in channel_parameters["language"] \
                    and "*" not in channel_parameters["language"]:
                logger.info("%s -idioma no válido-" % basename_without_extension)
                continue

            # No busca si es un canal excluido de la búsqueda global
            include_in_global_search = channel_parameters["include_in_global_search"]
            if include_in_global_search:
                # Buscar en la configuracion del canal
                include_in_global_search = config.get_setting("include_in_global_search", basename_without_extension)

            if not include_in_global_search:
                logger.info("%s -no incluido en lista a buscar-" % basename_without_extension)
                continue

            if progreso.iscanceled():
                progreso.close()
                logger.info("Búsqueda cancelada")
                return itemlist

            # Modo Multi Thread
            if multithread:
                t = Thread(target=channel_search, args=[search_results, channel_parameters, tecleado],
                           name=channel_parameters["title"])
                t.setDaemon(True)
                t.start()
                threads.append(t)

            # Modo single Thread
            else:
                logger.info("Intentado búsqueda en %s de %s " % (basename_without_extension, tecleado))
                channel_search(search_results, channel_parameters, tecleado)

            logger.info("%s incluido en la búsqueda" % basename_without_extension)
            progreso.update(percentage,
                            "Buscando en %s..." % channel_parameters["title"])

        except:
            logger.error("No se puede buscar en: %s" % channel_parameters["title"])
            import traceback
            logger.error(traceback.format_exc())
            continue

    # Modo Multi Thread
    # Usando isAlive() no es necesario try-except,
    # ya que esta funcion (a diferencia de is_alive())
    # es compatible tanto con versiones antiguas de python como nuevas
    if multithread:
        pendent = [a for a in threads if a.isAlive()]
        t = float(100) / len(pendent)
        while pendent:
            index = (len(threads) - len(pendent)) + 1
            percentage = int(math.ceil(index * t))

            list_pendent_names = [a.getName() for a in pendent]
            mensaje = "Buscando en %s" % (", ".join(list_pendent_names))
            progreso.update(percentage, "Finalizado en %d/%d canales..." % (len(threads) - len(pendent), len(threads)),
                            mensaje)
            logger.debug(mensaje)

            if progreso.iscanceled():
                logger.info("Búsqueda cancelada")
                break

            time.sleep(0.5)
            pendent = [a for a in threads if a.isAlive()]

    total = 0

    for channel in sorted(search_results.keys()):
        for element in search_results[channel]:
            total += len(element["itemlist"])
            title = channel

            # resultados agrupados por canales
            if item.contextual == True or item.action == 'search_tmdb':
                result_mode = 1
            if result_mode == 0:
                if len(search_results[channel]) > 1:
                    title += " -%s" % element["item"].title.strip()
                title += " (%s)" % len(element["itemlist"])

                title = re.sub("\[COLOR [^\]]+\]", "", title)
                title = re.sub("\[/COLOR]", "", title)

                itemlist.append(Item(title=title, channel="search", action="show_result", url=element["item"].url,
                                     extra=element["item"].extra, folder=True, adult=element["adult"],
                                     from_action="search", from_channel=element["item"].channel, tecleado=tecleado))
            # todos los resultados juntos, en la misma lista
            else:
                title = " [ Resultados del canal %s ] " % channel
                itemlist.append(Item(title=title, channel="search", action="",
                                     folder=False, text_bold=True, from_channel=channel))
                for i in element["itemlist"]:
                    if i.action:
                        title = "    " + i.title
                        itemlist.append(i.clone(title=title, from_action=i.action, from_channel=i.channel,
                                                channel="search", action="show_result", adult=element["adult"]))

    title = "Buscando: '%s' | Encontrado: %d vídeos | Tiempo: %2.f segundos" % (
    tecleado, total, time.time() - start_time)
    itemlist.insert(0, Item(title=title, text_color='yellow'))

    progreso.close()

    #Para opcion Buscar en otros canales
    if item.contextual == True:
        return exact_results(itemlist, tecleado)
    else:
        return itemlist


def exact_results(results, wanted):
    logger.info()
    itemlist =[]

    for item in results:
        if item.action=='':
            channel=item.from_channel
        if item.action != '' and item.contentTitle==wanted:
            item.title = '%s [%s]' % (item.title, channel)
            itemlist.append(item)

    return itemlist


def save_search(text):
    saved_searches_limit = int((10, 20, 30, 40,)[int(config.get_setting("saved_searches_limit", "search"))])

    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if current_saved_searches_list is None:
        saved_searches_list = []
    else:
        saved_searches_list = list(current_saved_searches_list)

    if text in saved_searches_list:
        saved_searches_list.remove(text)

    saved_searches_list.insert(0, text)

    config.set_setting("saved_searches_list", saved_searches_list[:saved_searches_limit], "search")


def clear_saved_searches(item):
    config.set_setting("saved_searches_list", list(), "search")
    platformtools.dialog_ok("Buscador", "Búsquedas borradas correctamente")


def get_saved_searches():
    current_saved_searches_list = config.get_setting("saved_searches_list", "search")
    if current_saved_searches_list is None:
        saved_searches_list = []
    else:
        saved_searches_list = list(current_saved_searches_list)

    return saved_searches_list


def discover_list(item):
    from platformcode import unify
    itemlist = []

    result = tmdb.discovery(item)

    tvshow = False

    logger.debug(item)

    for elem in result:
        elem['tmdb_id']=elem['id']
        if 'title' in elem:
            title = unify.normalize(elem['title']).capitalize()
            elem['year'] = scrapertools.find_single_match(elem['release_date'], '(\d{4})-\d+-\d+')
        else:
            title = unify.normalize(elem['name']).capitalize()
            tvshow = True

        new_item = Item(channel='search', title=title, infoLabels=elem, action='search_tmdb', extra=title,
                        category='Resultados', context ='')

        if tvshow:
            new_item.contentSerieName = title
        else:
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if item.page != '' and len(itemlist)>0:
        next_page = str(int(item.page)+1)
        #if not 'similar' in item.list_type:
        #    itemlist.append(item.clone(title='Pagina Siguente', page=next_page))
        #else:
        itemlist.append(Item(channel=item.channel, action='discover_list', title='Pagina Siguente',
                             search_type=item.search_type, list_type=item.list_type, type=item.type, page=next_page))

    return itemlist

def search_tmdb(item):
    logger.debug(item)

    itemlist = []
    threads = []
    logger.debug(item)
    wanted = item.contentTitle

    search = do_search(item)

    if item.contentSerieName == '':
        results = exact_results(search, wanted)
        for result in results:
            logger.debug(result)
            t = Thread(target=get_links, args=[result])
            t.start()
            threads.append(t)

            for thread in threads:
                thread.join()

            # try:
            #     get_links(result)
            # except:
            #     pass

        for link in link_list:
            if link.action == 'play' and not 'trailer' in link.title.lower() and len(itemlist) < max_links:
                itemlist.append(link)

        return sorted(itemlist, key=lambda it: it.server)
    else:
        for item in search:
            if item.contentSerieName != '' and item.contentSerieName == wanted:
                logger.debug(item)
                itemlist.append(item)
        return itemlist

def get_links (item):
    logger.info()
    results =[]
    channel = __import__('channels.%s' % item.from_channel, None, None, ["channels.%s" % item.from_channel])
    if len(link_list) <= max_links:
        link_list.extend(getattr(channel, item.from_action)(item))
