# -*- coding: utf-8 -*-

import os

from channelselector import get_thumb
from core import filetools
from core import scrapertools
from core import videolibrarytools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="list_movies", title=config.get_localized_string(60509),
                         category="Videoteca de películas",
                         thumbnail=get_thumb("videolibrary_movie.png")))
    itemlist.append(Item(channel=item.channel, action="list_tvshows", title=config.get_localized_string(60600),
                         category="Videoteca de series",
                         thumbnail=get_thumb("videolibrary_tvshow.png")))

    return itemlist


def channel_config(item):
    return platformtools.show_channel_settings(channelpath=os.path.join(config.get_runtime_path(), "channels",
                                                                        item.channel),
                                               caption=config.get_localized_string(60598))


def list_movies(item):
    logger.info()
    itemlist = []

    for raiz, subcarpetas, ficheros in filetools.walk(videolibrarytools.MOVIES_PATH):
        for f in ficheros:
            if f.endswith(".nfo"):
                nfo_path = filetools.join(raiz, f)
                head_nfo, new_item = videolibrarytools.read_nfo(nfo_path)

                new_item.nfo = nfo_path
                new_item.path = raiz
                new_item.thumbnail = new_item.contentThumbnail
                new_item.text_color = "blue"

                if not filetools.exists(filetools.join(new_item.path, filetools.basename(new_item.strm_path))):
                    # Si se ha eliminado el strm desde la bilbioteca de kodi, no mostrarlo
                    continue

                # Menu contextual: Marcar como visto/no visto
                visto = new_item.library_playcounts.get(os.path.splitext(f)[0], 0)
                new_item.infoLabels["playcount"] = visto
                if visto > 0:
                    texto_visto = config.get_localized_string(60016)
                    contador = 0
                else:
                    texto_visto = config.get_localized_string(60017)
                    contador = 1

                # Menu contextual: Eliminar serie/canal
                num_canales = len(new_item.library_urls)
                if "downloads" in new_item.library_urls:
                    num_canales -= 1
                if num_canales > 1:
                    texto_eliminar = config.get_localized_string(60018)
                    multicanal = True
                else:
                    texto_eliminar = config.get_localized_string(60019)
                    multicanal = False

                new_item.context = [{"title": texto_visto,
                                     "action": "mark_content_as_watched",
                                     "channel": "videolibrary",
                                     "playcount": contador},
                                    {"title": texto_eliminar,
                                     "action": "delete",
                                     "channel": "videolibrary",
                                     "multicanal": multicanal}]
                # ,{"title": "Cambiar contenido (PENDIENTE)",
                # "action": "",
                # "channel": "videolibrary"}]
                # logger.debug("new_item: " + new_item.tostring('\n'))
                itemlist.append(new_item)

    return sorted(itemlist, key=lambda it: it.title.lower())


def list_tvshows(item):
    logger.info()
    itemlist = []

    # Obtenemos todos los tvshow.nfo de la videoteca de SERIES recursivamente
    for raiz, subcarpetas, ficheros in filetools.walk(videolibrarytools.TVSHOWS_PATH):
        for f in ficheros:
            if f == "tvshow.nfo":
                tvshow_path = filetools.join(raiz, f)
                # logger.debug(tvshow_path)
                head_nfo, item_tvshow = videolibrarytools.read_nfo(tvshow_path)
                item_tvshow.title = item_tvshow.contentTitle
                item_tvshow.path = raiz
                item_tvshow.nfo = tvshow_path

                # Menu contextual: Marcar como visto/no visto
                visto = item_tvshow.library_playcounts.get(item_tvshow.contentTitle, 0)
                item_tvshow.infoLabels["playcount"] = visto
                if visto > 0:
                    texto_visto = config.get_localized_string(60020)
                    contador = 0
                else:
                    texto_visto = config.get_localized_string(60021)
                    contador = 1

                # Menu contextual: Buscar automáticamente nuevos episodios o no
                if item_tvshow.active and int(item_tvshow.active) > 0:
                    texto_update = config.get_localized_string(60022)
                    value = 0
                    item_tvshow.text_color = "green"
                else:
                    texto_update = config.get_localized_string(60023)
                    value = 1
                    item_tvshow.text_color = "0xFFDF7401"

                # Menu contextual: Eliminar serie/canal
                num_canales = len(item_tvshow.library_urls)
                if "downloads" in item_tvshow.library_urls:
                    num_canales -= 1
                if num_canales > 1:
                    texto_eliminar = config.get_localized_string(60024)
                    multicanal = True
                else:
                    texto_eliminar = config.get_localized_string(60025)
                    multicanal = False

                item_tvshow.context = [{"title": texto_visto,
                                        "action": "mark_content_as_watched",
                                        "channel": "videolibrary",
                                        "playcount": contador},
                                       {"title": texto_update,
                                        "action": "mark_tvshow_as_updatable",
                                        "channel": "videolibrary",
                                        "active": value},
                                       {"title": texto_eliminar,
                                        "action": "delete",
                                        "channel": "videolibrary",
                                        "multicanal": multicanal},
                                       {"title": "Buscar nuevos episodios ahora",
                                        "action": "update_tvshow",
                                        "channel": "videolibrary"}]
                # ,{"title": "Cambiar contenido (PENDIENTE)",
                # "action": "",
                # "channel": "videolibrary"}]

                # logger.debug("item_tvshow:\n" + item_tvshow.tostring('\n'))
                itemlist.append(item_tvshow)

    if itemlist:
        itemlist = sorted(itemlist, key=lambda it: it.title.lower())

        itemlist.append(Item(channel=item.channel, action="update_videolibrary", thumbnail=item.thumbnail,
                             title=config.get_localized_string(60026), folder=False))

    return itemlist


def get_seasons(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []
    dict_temp = {}

    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Menu contextual: Releer tvshow.nfo
    head_nfo, item_nfo = videolibrarytools.read_nfo(item.nfo)

    if config.get_setting("no_pile_on_seasons", "videolibrary") == 2:  # Siempre
        return get_episodes(item)

    for f in ficheros:
        if f.endswith('.json'):
            season = f.split('x')[0]
            dict_temp[season] = config.get_localized_string(60027) % season

    if config.get_setting("no_pile_on_seasons", "videolibrary") == 1 and len(
            dict_temp) == 1:  # Sólo si hay una temporada
        return get_episodes(item)
    else:

        # TODO mostrar los episodios de la unica temporada "no vista", en vez de mostrar el Item "temporada X" previo
        # si está marcado "ocultar los vistos" en el skin, se ejecutaria esto
        #     se comprueba cada temporada en dict_temp si está visto.
        #          si hay una sola temporada y no_pile_on_seasons == 1, se devuelve get(episodios)
        #          si está todo visto, hacemos como actualmente <-- el else no se hace nada.. CREO
        # if config.get_setting("no_pile_on_seasons", "videolibrary") == 1 and len(dict_temp_Visible) == 1:  # Sólo si hay una temporada

        # Creamos un item por cada temporada
        for season, title in dict_temp.items():
            new_item = item.clone(action="get_episodes", title=title, contentSeason=season,
                                  filtrar_season=True)

            # Menu contextual: Marcar la temporada como vista o no
            visto = item_nfo.library_playcounts.get("season %s" % season, 0)
            new_item.infoLabels["playcount"] = visto
            if visto > 0:
                texto = config.get_localized_string(60028)
                value = 0
            else:
                texto = config.get_localized_string(60029)
                value = 1
            new_item.context = [{"title": texto,
                                 "action": "mark_season_as_watched",
                                 "channel": "videolibrary",
                                 "playcount": value}]

            # logger.debug("new_item:\n" + new_item.tostring('\n'))
            itemlist.append(new_item)

        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))

        if config.get_setting("show_all_seasons", "videolibrary"):
            new_item = item.clone(action="get_episodes", title=config.get_localized_string(60030))
            new_item.infoLabels["playcount"] = 0
            itemlist.insert(0, new_item)

    return itemlist


def get_episodes(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))
    itemlist = []

    # Obtenemos los archivos de los episodios
    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Menu contextual: Releer tvshow.nfo
    head_nfo, item_nfo = videolibrarytools.read_nfo(item.nfo)

    # Crear un item en la lista para cada strm encontrado
    for i in ficheros:
        if i.endswith('.strm'):
            season_episode = scrapertools.get_season_and_episode(i)
            if not season_episode:
                # El fichero no incluye el numero de temporada y episodio
                continue
            season, episode = season_episode.split("x")
            # Si hay q filtrar por temporada, ignoramos los capitulos de otras temporadas
            if item.filtrar_season and int(season) != int(item.contentSeason):
                continue

            # Obtener los datos del season_episode.nfo
            nfo_path = filetools.join(raiz, i).replace('.strm', '.nfo')
            head_nfo, epi = videolibrarytools.read_nfo(nfo_path)

            # Fijar el titulo del capitulo si es posible
            if epi.contentTitle:
                title_episodie = epi.contentTitle.strip()
            else:
                title_episodie = config.get_localized_string(60031) % \
                                 (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))

            epi.contentTitle = "%sx%s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2))
            epi.title = "%sx%s - %s" % (epi.contentSeason, str(epi.contentEpisodeNumber).zfill(2), title_episodie)

            if item_nfo.library_filter_show:
                epi.library_filter_show = item_nfo.library_filter_show

            # Menu contextual: Marcar episodio como visto o no
            visto = item_nfo.library_playcounts.get(season_episode, 0)
            epi.infoLabels["playcount"] = visto
            if visto > 0:
                texto = config.get_localized_string(60032)
                value = 0
            else:
                texto = config.get_localized_string(60033)
                value = 1
            epi.context = [{"title": texto,
                            "action": "mark_content_as_watched",
                            "channel": "videolibrary",
                            "playcount": value,
                            "nfo": item.nfo}]

            # logger.debug("epi:\n" + epi.tostring('\n'))
            itemlist.append(epi)

    return sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))


def findvideos(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    itemlist = []
    list_canales = {}
    item_local = None

    if not item.contentTitle or not item.strm_path:
        logger.debug("No se pueden buscar videos por falta de parametros")
        return []

    content_title = filter(lambda c: c not in ":*?<>|\/", item.contentTitle.strip().lower())

    if item.contentType == 'movie':
        item.strm_path = filetools.join(videolibrarytools.MOVIES_PATH, item.strm_path)
        path_dir = os.path.dirname(item.strm_path)
        item.nfo = filetools.join(path_dir, os.path.basename(path_dir) + ".nfo")
    else:
        item.strm_path = filetools.join(videolibrarytools.TVSHOWS_PATH, item.strm_path)
        path_dir = os.path.dirname(item.strm_path)
        item.nfo = filetools.join(path_dir, 'tvshow.nfo')

    for fd in filetools.listdir(path_dir):
        if fd.endswith('.json'):
            contenido, nom_canal = fd[:-6].split('[')
            if (contenido.startswith(content_title) or item.contentType == 'movie') and nom_canal not in \
                    list_canales.keys():
                list_canales[nom_canal] = filetools.join(path_dir, fd)

    num_canales = len(list_canales)
    # logger.debug(str(list_canales))
    if 'downloads' in list_canales:
        json_path = list_canales['downloads']
        item_json = Item().fromjson(filetools.read(json_path))
        item_json.contentChannel = "local"
        # Soporte para rutas relativas en descargas
        if filetools.is_relative(item_json.url):
            item_json.url = filetools.join(videolibrarytools.VIDEOLIBRARY_PATH, item_json.url)

        del list_canales['downloads']

        # Comprobar q el video no haya sido borrado
        if filetools.exists(item_json.url):
            item_local = item_json.clone(action='play')
            itemlist.append(item_local)
        else:
            num_canales -= 1

    filtro_canal = ''
    if num_canales > 1 and config.get_setting("ask_channel", "videolibrary"):
        opciones = [config.get_localized_string(70089) % k.capitalize() for k in list_canales.keys()]
        opciones.insert(0, config.get_localized_string(70083))
        if item_local:
            opciones.append(item_local.title)

        from platformcode import platformtools
        index = platformtools.dialog_select(config.get_localized_string(30163), opciones)
        if index < 0:
            return []

        elif item_local and index == len(opciones) - 1:
            filtro_canal = 'downloads'
            platformtools.play_video(item_local)

        elif index > 0:
            filtro_canal = opciones[index].replace(config.get_localized_string(70078), "")
            itemlist = []

    for nom_canal, json_path in list_canales.items():
        if filtro_canal and filtro_canal != nom_canal.capitalize():
            continue

        # Importamos el canal de la parte seleccionada
        try:
            channel = __import__('channels.%s' % nom_canal, fromlist=["channels.%s" % nom_canal])
        except ImportError:
            exec "import channels." + nom_canal + " as channel"

        item_json = Item().fromjson(filetools.read(json_path))
        list_servers = []

        try:
            # FILTERTOOLS
            # si el canal tiene filtro se le pasa el nombre que tiene guardado para que filtre correctamente.
            if "list_language" in item_json:
                # si se viene desde la videoteca del addon
                if "library_filter_show" in item:
                    item_json.show = item.library_filter_show.get(nom_canal, "")

            # Ejecutamos find_videos, del canal o común
            item_json.contentChannel='videolibrary'
            if hasattr(channel, 'findvideos'):
                from core import servertools
                list_servers = getattr(channel, 'findvideos')(item_json)
                list_servers = servertools.filter_servers(list_servers)
            else:
                from core import servertools
                list_servers = servertools.find_video_items(item_json)
        except Exception, ex:
            logger.error("Ha fallado la funcion findvideos para el canal %s" % nom_canal)
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex).__name__, ex.args)
            logger.error(message)

        # Cambiarle el titulo a los servers añadiendoles el nombre del canal delante y
        # las infoLabels y las imagenes del item si el server no tiene
        for server in list_servers:
            #if not server.action:  # Ignorar/PERMITIR las etiquetas
            #    continue

            server.contentChannel = server.channel
            server.channel = "videolibrary"
            server.nfo = item.nfo
            server.strm_path = item.strm_path

            # Se añade el nombre del canal si se desea
            if config.get_setting("quit_channel_name", "videolibrary") == 0:
                server.title = "%s: %s" % (nom_canal.capitalize(), server.title)

            #server.infoLabels = item_json.infoLabels
            if not server.thumbnail:
                server.thumbnail = item.thumbnail

            # logger.debug("server:\n%s" % server.tostring('\n'))
            itemlist.append(server)

    # return sorted(itemlist, key=lambda it: it.title.lower())
    return itemlist


def play(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    if not item.contentChannel == "local":
        channel = __import__('channels.%s' % item.contentChannel, fromlist=["channels.%s" % item.contentChannel])
        if hasattr(channel, "play"):
            itemlist = getattr(channel, "play")(item)

        else:
            itemlist = [item.clone()]
    else:
        itemlist = [item.clone(url=item.url, server="local")]

    # Para enlaces directo en formato lista
    if isinstance(itemlist[0], list):
        item.video_urls = itemlist
        itemlist = [item]

    # Esto es necesario por si el play del canal elimina los datos
    for v in itemlist:
        if isinstance(v, Item):
            v.nfo = item.nfo
            v.strm_path = item.strm_path
            v.infoLabels = item.infoLabels
            if item.contentTitle:
                v.title = item.contentTitle
            else:
                if item.contentType == "episode":
                    v.title = config.get_localized_string(60036) % item.contentEpisodeNumber
            v.thumbnail = item.thumbnail
            v.contentThumbnail = item.thumbnail

    return itemlist


def update_videolibrary(item):
    logger.info()

    # Actualizar las series activas sobreescribiendo
    import videolibrary_service
    videolibrary_service.check_for_update(overwrite=True)

    # Eliminar las carpetas de peliculas que no contengan archivo strm
    for raiz, subcarpetas, ficheros in filetools.walk(videolibrarytools.MOVIES_PATH):
        strm = False
        for f in ficheros:
            if f.endswith(".strm"):
                strm = True
                break

        if ficheros and not strm:
            logger.debug("Borrando carpeta de pelicula eliminada: %s" % raiz)
            filetools.rmdirtree(raiz)


# metodos de menu contextual
def update_tvshow(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    heading = config.get_localized_string(60037)
    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), heading)
    p_dialog.update(0, heading, item.contentSerieName)

    import videolibrary_service
    if videolibrary_service.update(item.path, p_dialog, 1, 1, item, False) and config.is_xbmc():
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.update(folder=filetools.basename(item.path))

    p_dialog.close()


def mark_content_as_watched(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    if filetools.exists(item.nfo):
        head_nfo, it = videolibrarytools.read_nfo(item.nfo)

        if item.contentType == 'movie':
            name_file = os.path.splitext(os.path.basename(item.nfo))[0]
        elif item.contentType == 'episode':
            name_file = "%sx%s" % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))
        else:
            name_file = item.contentTitle

        if not hasattr(it, 'library_playcounts'):
            it.library_playcounts = {}
        it.library_playcounts.update({name_file: item.playcount})

        # se comprueba que si todos los episodios de una temporada están marcados, se marque tb la temporada
        if item.contentType != 'movie':
            it = check_season_playcount(it, item.contentSeason)

        # Guardamos los cambios en item.nfo
        if filetools.write(item.nfo, head_nfo + it.tojson()):
            item.infoLabels['playcount'] = item.playcount

            if item.contentType == 'tvshow':
                # Actualizar toda la serie
                new_item = item.clone(contentSeason=-1)
                mark_season_as_watched(new_item)

            if config.is_xbmc() and item.contentType == 'episode':
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.mark_content_as_watched_on_kodi(item, item.playcount)

            platformtools.itemlist_refresh()


def mark_season_as_watched(item):
    logger.info()
    # logger.debug("item:\n" + item.tostring('\n'))

    # Obtener el diccionario de episodios marcados
    f = filetools.join(item.path, 'tvshow.nfo')
    head_nfo, it = videolibrarytools.read_nfo(f)
    if not hasattr(it, 'library_playcounts'):
        it.library_playcounts = {}

    # Obtenemos los archivos de los episodios
    raiz, carpetas_series, ficheros = filetools.walk(item.path).next()

    # Marcamos cada uno de los episodios encontrados de esta temporada
    episodios_marcados = 0
    for i in ficheros:
        if i.endswith(".strm"):
            season_episode = scrapertools.get_season_and_episode(i)
            if not season_episode:
                # El fichero no incluye el numero de temporada y episodio
                continue
            season, episode = season_episode.split("x")

            if int(item.contentSeason) == -1 or int(season) == int(item.contentSeason):
                name_file = os.path.splitext(os.path.basename(f))[0]
                it.library_playcounts[name_file] = item.playcount
                episodios_marcados += 1

    if episodios_marcados:
        if int(item.contentSeason) == -1:
            # Añadimos todas las temporadas al diccionario item.library_playcounts
            for k in it.library_playcounts.keys():
                if k.startswith("season"):
                    it.library_playcounts[k] = item.playcount
        else:
            # Añadimos la temporada al diccionario item.library_playcounts
            it.library_playcounts["season %s" % item.contentSeason] = item.playcount

            # se comprueba que si todas las temporadas están vistas, se marque la serie como vista
            it = check_tvshow_playcount(it, item.contentSeason)

        # Guardamos los cambios en tvshow.nfo
        filetools.write(f, head_nfo + it.tojson())
        item.infoLabels['playcount'] = item.playcount

        if config.is_xbmc():
            # Actualizamos la BBDD de Kodi
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.mark_season_as_watched_on_kodi(item, item.playcount)

    platformtools.itemlist_refresh()


def mark_tvshow_as_updatable(item):
    logger.info()
    head_nfo, it = videolibrarytools.read_nfo(item.nfo)
    it.active = item.active
    filetools.write(item.nfo, head_nfo + it.tojson())

    platformtools.itemlist_refresh()


def delete(item):
    def delete_all(_item):
        for file in filetools.listdir(_item.path):
            if file.endswith(".strm") or file.endswith(".nfo") or file.endswith(".json"):
                filetools.remove(filetools.join(_item.path, file))
        raiz, carpeta_serie, ficheros = filetools.walk(_item.path).next()
        if ficheros == []:
            filetools.rmdir(_item.path)

        if config.is_xbmc():
            import xbmc
            # esperamos 3 segundos para dar tiempo a borrar los ficheros
            xbmc.sleep(3000)
            # TODO mirar por qué no funciona al limpiar en la videoteca de Kodi al añadirle un path
            # limpiamos la videoteca de Kodi
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.clean()

        logger.info("Eliminados todos los enlaces")
        platformtools.itemlist_refresh()

    # logger.info(item.contentTitle)
    # logger.debug(item.tostring('\n'))

    if item.contentType == 'movie':
        heading = config.get_localized_string(70084)
    else:
        heading = config.get_localized_string(70085)

    if item.multicanal:
        # Obtener listado de canales
        opciones = [config.get_localized_string(70086) % k.capitalize() for k in item.library_urls.keys() if
                    k != "downloads"]
        opciones.insert(0, heading)

        index = platformtools.dialog_select(config.get_localized_string(30163), opciones)

        if index == 0:
            # Seleccionado Eliminar pelicula/serie
            delete_all(item)

        elif index > 0:
            # Seleccionado Eliminar canal X
            canal = opciones[index].replace(config.get_localized_string(70079), "").lower()

            num_enlaces = 0
            for fd in filetools.listdir(item.path):
                if fd.endswith(canal + '].json'):
                    if filetools.remove(filetools.join(item.path, fd)):
                        num_enlaces += 1

            if num_enlaces > 0:
                # Actualizar .nfo
                head_nfo, item_nfo = videolibrarytools.read_nfo(item.nfo)
                del item_nfo.library_urls[canal]
                filetools.write(item.nfo, head_nfo + item_nfo.tojson())

            msg_txt = config.get_localized_string(70087) % (num_enlaces, canal)
            logger.info(msg_txt)
            platformtools.dialog_notification(heading, msg_txt)
            platformtools.itemlist_refresh()

    else:
        if platformtools.dialog_yesno(heading,
                                      config.get_localized_string(70088) % item.infoLabels['title']):
            delete_all(item)


def check_season_playcount(item, season):
    logger.info()

    if season:
        episodios_temporada = 0
        episodios_vistos_temporada = 0
        for key, value in item.library_playcounts.iteritems():
            if key.startswith("%sx" % season):
                episodios_temporada += 1
                if value > 0:
                    episodios_vistos_temporada += 1

        if episodios_temporada == episodios_vistos_temporada:
            # se comprueba que si todas las temporadas están vistas, se marque la serie como vista
            item.library_playcounts.update({"season %s" % season: 1})
        else:
            # se comprueba que si todas las temporadas están vistas, se marque la serie como vista
            item.library_playcounts.update({"season %s" % season: 0})

    return check_tvshow_playcount(item, season)


def check_tvshow_playcount(item, season):
    logger.info()
    if season:
        temporadas_serie = 0
        temporadas_vistas_serie = 0
        for key, value in item.library_playcounts.iteritems():
            if key == ("season %s" % season):
                temporadas_serie += 1
                if value > 0:
                    temporadas_vistas_serie += 1

        if temporadas_serie == temporadas_vistas_serie:
            item.library_playcounts.update({item.title: 1})
        else:
            item.library_playcounts.update({item.title: 0})

    else:
        playcount = item.library_playcounts.get(item.title, 0)
        item.library_playcounts.update({item.title: playcount})

    return item
