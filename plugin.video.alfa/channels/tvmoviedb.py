# -*- coding: utf-8 -*-

import re
import urllib
from base64 import b64decode as bdec

from core import filetools
from core import httptools
from core import jsontools
from core import scrapertools
from core.item import Item
from core.tmdb import Tmdb
from core import trakt_tools
from platformcode import config, logger
from platformcode import platformtools

__perfil__ = config.get_setting('perfil', "tvmoviedb")

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFF088A08', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFF088A08', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFF088A08', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5, color6 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = color6 = ""

langs = ['de', 'fr', 'pt', 'it', 'es-MX', 'ca', 'en', 'es', 'pt-BR']
langt = langs[config.get_setting('tmdb', "tvmoviedb")]
langt_alt = langs[config.get_setting('tmdb_alternativo', "tvmoviedb")]
langs = ['co', 'cl', 'ar', 'mx', 'en', 'es', 'pt-BR']
langf = langs[config.get_setting('filmaff', "tvmoviedb")]
langs = ['de-de', 'fr-fr', 'pt-pt', 'it-it', 'es-MX', 'ca-es', 'en', 'es']
langi = langs[config.get_setting('imdb', "tvmoviedb")]
adult_mal = config.get_setting('adult_mal', "tvmoviedb")
mal_ck = "MzE1MDQ2cGQ5N2llYTY4Z2xwbGVzZjFzbTY="
images_predef = "https://raw.githubusercontent.com/master-1970/resources/master/images/genres/"
default_fan = filetools.join(config.get_runtime_path(), "fanart1_2.jpg")


def mainlist(item):
    logger.info()
    item.text_color = color1
    itemlist = []

    #itemlist.append(item.clone(title=config.get_localized_string(70021), action="", text_color=color2))
    #itemlist.append(item.clone(title=config.get_localized_string(70022), action="tmdb", extra="movie",
    #                           thumbnail="%s0/Movies.png" % images_predef))
    #itemlist.append(item.clone(title=config.get_localized_string(70023), action="tmdb", extra="tv",
    #                           thumbnail=images_predef + "0/TV%20Series.png"))
    itemlist.append(item.clone(title=config.get_localized_string(70024), action="", text_color=color2))
    itemlist.append(item.clone(title=config.get_localized_string(70022), action="filmaf", extra="movie",
                               thumbnail="%s0/Movies.png" % images_predef))
    itemlist.append(item.clone(title=config.get_localized_string(70023), action="filmaf", extra="tv",
                               thumbnail=images_predef + "0/TV%20Series.png"))
    itemlist.append(item.clone(title=config.get_localized_string(70025), action="", text_color=color2))
    itemlist.append(item.clone(title=config.get_localized_string(70022), action="imdb", extra="movie",
                               url='&title_type=feature,tv_movie',
                               thumbnail="%s0/Movies.png" % images_predef))
    itemlist.append(item.clone(title=config.get_localized_string(70023), action="imdb", extra="tv",
                               url='&title_type=tv_series,tv_special,mini_series',
                               thumbnail=images_predef + "0/TV%20Series.png"))
    itemlist.append(
        item.clone(title=config.get_localized_string(70415), action="trakt", text_color=color2, thumbnail="http://i.imgur.com/5sQjjuk.png"))
    itemlist.append(
        item.clone(title=config.get_localized_string(70026), action="mal", text_color=color2, thumbnail="http://i.imgur.com/RhsYWmd.png"))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(
        item.clone(title=config.get_localized_string(70027), action="configuracion", text_color=color6, folder=False))
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret

def search_star(item):
    logger.info()

    itemlist = []
    item.type='movie'
    itemlist.extend(search_(item))
    item.type='tvshow'
    itemlist.extend(search_(item))
    return itemlist

def search_(item):
    texto = platformtools.dialog_input(heading=item.title)
    if texto:
        if "imdb" in item.url:
            item.url += texto.replace(" ", "+")
            item.action = "listado_imdb"
            return listado_imdb(item)
        if "filmaffinity" in item.url:
            item.url += texto.replace(" ", "+")
            item.action = "listado_fa"
            return listado_fa(item)
        if "myanimelist" in item.url:
            item.url += texto.replace(" ", "%20")
            item.url += "&type=0&score=0&status=0&p=0&r=0&sm=0&sd=0&sy=0&em=0&ed=0&ey=0&c[0]=a" \
                        "&c[1]=b&c[2]=c&c[3]=d&c[4]=f&gx=0"
            item.action = "busqueda_mal"
            return busqueda_mal(item)

        item.search['query'] = texto
        item.action = "listado_tmdb"

        if item.star == True:
            types = ['movie','tv']
            itemlist = []
            for type in types:
                item.contentType = type
                item.search['type']=type
                itemlist.extend(listado_tmdb(item))
            return itemlist
        else:
            return listado_tmdb(item)


def busqueda(item):
    logger.info()

    new_item = Item(title=item.contentTitle, text=item.contentTitle.replace("+", " "), mode=item.contentType,
         infoLabels=item.infoLabels)

    from channels import search
    return search.channel_search(new_item)


def tmdb(item):
    item.contentType = item.extra.replace("tv", "tvshow")

    itemlist = []
    itemlist.append(item.clone(title=config.get_localized_string(70028), action="listado_tmdb",
                               search={'url': item.extra + "/popular", 'language': langt, 'page': 1}))
    itemlist.append(item.clone(title=config.get_localized_string(70029), action="listado_tmdb",
                               search={'url': item.extra + "/top_rated", 'language': langt, 'page': 1}))
    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70030), action="listado_tmdb",
                                   search={'url': item.extra + "/now_playing", 'language': langt, 'page': 1}))
    else:
        itemlist.append(item.clone(title=config.get_localized_string(70031), action="listado_tmdb",
                                   search={'url': item.extra + "/on_the_air", 'language': langt, 'page': 1}))
    itemlist.append(item.clone(title=config.get_localized_string(70032), action="indices_tmdb",
                               thumbnail="%s0/Genres.png" % images_predef))
    itemlist.append(item.clone(title=config.get_localized_string(70042), action="indices_tmdb", thumbnail="%s0/Year.png" % images_predef))

    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70033), action="listado_tmdb",
                                   search={'url': 'person/popular', 'language': langt, 'page': 1}))
        itemlist.append(item.clone(title=config.get_localized_string(70034), action="listado_tmdb",
                                   search={'url': item.extra + "/upcoming", 'language': langt, 'page': 1}))

    if config.get_platform() != "plex":
        title = item.contentType.replace("movie", config.get_localized_string(70283)).replace("tvshow", "serie")
        itemlist.append(item.clone(title=config.get_localized_string(70035) % title, action="search_",
                                   search={'url': 'search/%s' % item.extra, 'language': langt, 'page': 1}))

        itemlist.append(item.clone(title=config.get_localized_string(70036), action="search_",
                                   search={'url': 'search/person', 'language': langt, 'page': 1}))
        if item.extra == "movie":
            itemlist.append(item.clone(title=config.get_localized_string(70037), action="search_",
                                       search={'url': "search/person", 'language': langt, 'page': 1}, crew=True))

    itemlist.append(item.clone(title=config.get_localized_string(70038), action="filtro", text_color=color4))
    itemlist.append(item.clone(title=config.get_localized_string(70039), action="filtro", text_color=color4))

    return itemlist


def imdb(item):
    item.contentType = item.extra.replace("tv", "tvshow")

    itemlist = []
    itemlist.append(item.clone(title=config.get_localized_string(70028), action="listado_imdb"))
    itemlist.append(item.clone(title=config.get_localized_string(70029), action="listado_imdb",
                               url=item.url + "&num_votes=25000,&sort=user_rating,desc"))
    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70030), action="listado_imdb",
                                   url="http://www.imdb.com/showtimes/location?ref_=inth_ov_sh_sm"))
    itemlist.append(item.clone(title=config.get_localized_string(70032), action="indices_imdb",
                               thumbnail="%s0/Genres.png" % images_predef))
    itemlist.append(item.clone(title=config.get_localized_string(70042), action="indices_imdb", thumbnail="%s0/Year.png" % images_predef))

    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70033), action="listado_imdb",
                                   url="http://www.imdb.com/search/name?gender=male,female&ref_=nv_cel_m_3"))

        itemlist.append(item.clone(title=config.get_localized_string(70034), action="listado_imdb",
                                   url="http://www.imdb.com/movies-coming-soon/?ref_=shlc_cs"))

    if config.get_platform() != "plex":
        title = item.contentType.replace("movie", config.get_localized_string(70283)).replace("tvshow", "serie")
        itemlist.append(item.clone(title="Buscar %s" % title, action="search_",
                                   url="http://www.imdb.com/search/title?title=" + item.url))

        itemlist.append(item.clone(title=config.get_localized_string(70036), action="search_",
                                   url="http://www.imdb.com/search/name?name="))

    itemlist.append(item.clone(title=config.get_localized_string(70038), action="filtro_imdb", text_color=color4))

    return itemlist


def filmaf(item):
    item.contentType = item.extra.replace("tv", "tvshow")
    login, message = login_fa()

    itemlist = []
    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70040), action="listado_fa", extra="top",
                                   url="http://m.filmaffinity.com/%s/topgen.php?genre=&country=&"
                                       "fromyear=&toyear=&notvse=1&nodoc=1" % langf))
        itemlist.append(item.clone(title=config.get_localized_string(70030), action="listado_fa",
                                   url="http://m.filmaffinity.com/%s/rdcat.php?id=new_th_%s" % (langf, langf)))
        itemlist.append(item.clone(title=config.get_localized_string(70032), action="indices_fa", url="http://m.filmaffinity.com/%s/topgen.php"
                                                                             % langf,
                                   thumbnail="%s0/Genres.png" % images_predef))
    else:
        itemlist.append(item.clone(title=config.get_localized_string(70040), action="listado_fa", extra="top",
                                   url="http://m.filmaffinity.com/%s/topgen.php?genre=TV_SE&country=&"
                                       "fromyear=&toyear=&nodoc" % langf))
        itemlist.append(item.clone(title="Series de actualidad", action="listado_fa",
                                   url="http://m.filmaffinity.com/%s/category.php?id=current_tv" % langf))

    itemlist.append(item.clone(title=config.get_localized_string(70042), action="indices_fa", thumbnail="%s0/Year.png" % images_predef))
    if item.extra == "movie":
        itemlist.append(item.clone(title=config.get_localized_string(70043), action="listado_fa", extra="estrenos",
                                   url="http://m.filmaffinity.com/%s/rdcat.php?id=upc_th_%s" % (langf, langf)))
        itemlist.append(item.clone(title=config.get_localized_string(70044), action="indices_fa", extra="sagas",
                                   url="http://www.filmaffinity.com/%s/movie-groups-all.php" % langf))
    itemlist.append(item.clone(title=config.get_localized_string(70045), action="indices_fa",
                               url='http://m.filmaffinity.com/%s/topics.php' % langf, text_color=color3))
    if config.get_platform() != "plex":
        itemlist.append(item.clone(title=config.get_localized_string(70046), action="search_", text_color=color4,
                                   url="http://m.filmaffinity.com/%s/search.php?stype=title&stext=" % langf))

        itemlist.append(item.clone(title=config.get_localized_string(70036), action="search_", text_color=color4,
                                   url="http://m.filmaffinity.com/%s/search.php?stype=cast&stext=" % langf))
        itemlist.append(item.clone(title=config.get_localized_string(70047), action="search_", text_color=color4,
                                   url="http://m.filmaffinity.com/%s/search.php?stype=director&stext=" % langf))

    itemlist.append(item.clone(title=config.get_localized_string(70038), action="filtro_fa", text_color=color4, extra="top"))
    itemlist.append(item.clone(title=config.get_localized_string(70048), action="cuenta_fa", text_color=color3))

    return itemlist


def trakt(item):
    itemlist = []
    item.text_color = color1
    token_auth = config.get_setting("token_trakt", "trakt")
    page = "?page=1&limit=20&extended=full"
    if not item.extra:
        item.extra = "movie"
        itemlist.append(item.clone(title="[COLOR yellow][B]%s[/B][/COLOR]" % config.get_localized_string(70416), action=""))
        itemlist.append(item.clone(title=config.get_localized_string(70049), action="acciones_trakt", url="movies/popular%s" % page))
        itemlist.append(
            item.clone(title=config.get_localized_string(70050), action="acciones_trakt", url="movies/trending%s" % page))
        itemlist.append(item.clone(title=config.get_localized_string(70053), action="acciones_trakt", url="movies/watched/all%s" % page))
        itemlist.append(
            item.clone(title=config.get_localized_string(70051), action="acciones_trakt", url="movies/anticipated%s" % page))
        if token_auth:
            itemlist.append(item.clone(title=config.get_localized_string(70052), action="acciones_trakt",
                                       url="recommendations/movies?limit=100&extended=full", pagina=0))
        itemlist.append(item.clone(title="[COLOR yellow][B]%s[/B][/COLOR]" % config.get_localized_string(70417), action="",))
        item.extra = "show"
        itemlist.append(item.clone(title=config.get_localized_string(70049), action="acciones_trakt", url="shows/popular%s" % page))
        itemlist.append(item.clone(title=config.get_localized_string(70050), action="acciones_trakt", url="shows/trending%s" % page))
        itemlist.append(item.clone(title=config.get_localized_string(70053), action="acciones_trakt", url="shows/watched/all%s" % page))
        itemlist.append(
            item.clone(title=config.get_localized_string(70051), action="acciones_trakt", url="shows/anticipated%s" % page))
        if token_auth:
            itemlist.append(item.clone(title=config.get_localized_string(70052), action="acciones_trakt",
                                       url="recommendations/shows?limit=100&extended=full", pagina=0))
        itemlist.append(item.clone(title="[COLOR red][B]%s[/B][/COLOR]" % config.get_localized_string(70048), extra="cuenta"))
    else:
        item.extra = "movie"
        # Se comprueba si existe un token guardado y sino se ejecuta el proceso de autentificación
        if not token_auth:
            #folder = (config.get_platform() == "plex")
            itemlist.append(item.clone(title=config.get_localized_string(70054), action="auth_trakt", folder=folder))
        else:
            itemlist.append(item.clone(title=config.get_localized_string(70055), action="", text_color=color2))
            itemlist.append(
                item.clone(title=config.get_localized_string(60651), action="acciones_trakt", url="users/me/watchlist/movies%s" % page,
                           order="added", how="desc"))
            itemlist.append(
                item.clone(title=config.get_localized_string(60652), action="acciones_trakt", url="users/me/watchlist/shows%s" % page,
                           extra="show",
                           order="added", how="desc"))
            itemlist.append(item.clone(title=config.get_localized_string(70056), action="", text_color=color2))
            itemlist.append(
                item.clone(title=config.get_localized_string(60651), action="acciones_trakt", url="users/me/watched/movies%s" % page,
                           order="added", how="desc"))
            itemlist.append(
                item.clone(title=config.get_localized_string(60652), action="acciones_trakt", url="users/me/watched/shows%s" % page,
                           extra="show",
                           order="added", how="desc"))
            itemlist.append(item.clone(title=config.get_localized_string(70068), action="", text_color=color2))
            itemlist.append(
                item.clone(title=config.get_localized_string(60651), action="acciones_trakt", url="users/me/collection/movies%s" % page,
                           order="added", how="desc"))
            itemlist.append(
                item.clone(title=config.get_localized_string(60652), action="acciones_trakt", url="users/me/collection/shows%s" % page,
                           extra="show",
                           order="added", how="desc"))
            itemlist.append(
                item.clone(title=config.get_localized_string(70057), action="acciones_trakt", url="users/me/lists", text_color=color2))

    return itemlist


def mal(item):
    itemlist = []
    item.text_color = color1
    login, message, user = login_mal()
    if login:
        item.login = True

    itemlist.append(
        item.clone(title=config.get_localized_string(70058), url="https://myanimelist.net/topanime.php?type=tv&limit=0", action="top_mal",
                   contentType="tvshow", extra="tv"))
    itemlist.append(item.clone(title=config.get_localized_string(70059), url="https://myanimelist.net/topanime.php?type=movie&limit=0",
                               action="top_mal",
                               contentType="movie", extra="movie"))
    itemlist.append(
        item.clone(title=config.get_localized_string(70061), url="https://myanimelist.net/topanime.php?type=ova&limit=0", action="top_mal",
                   contentType="tvshow", extra="tv", tipo="ova"))
    itemlist.append(
        item.clone(title=config.get_localized_string(70028), url="https://myanimelist.net/topanime.php?type=bypopularity&limit=0",
                   action="top_mal"))
    itemlist.append(item.clone(title=config.get_localized_string(70060), url="https://myanimelist.net/topanime.php?type=upcoming&limit=0",
                               action="top_mal"))
    itemlist.append(item.clone(title=config.get_localized_string(70062), url="", action="indices_mal"))
    itemlist.append(item.clone(title=config.get_localized_string(70063), url="", action="indices_mal"))
    if config.get_platform() != "plex":
        itemlist.append(item.clone(title=config.get_localized_string(70064), url="https://myanimelist.net/anime.php?q=",
                                   action="search_"))
    itemlist.append(item.clone(title=config.get_localized_string(70038), action="filtro_mal", text_color=color4))

    itemlist.append(item.clone(title=config.get_localized_string(70057), action="cuenta_mal", text_color=color3))

    return itemlist


##-------------------- SECCION TMDB ------------------------##
def listado_tmdb(item):
    # Listados principales de la categoría Tmdb (Más populares, más vistas, etc...)
    itemlist = []
    item.text_color = color1
    item.fanart = default_fan
    if not item.pagina:
        item.pagina = 1

    # Listado de actores
    if 'nm' in item.infoLabels['imdb_id']:
        try:

            ob_tmdb = Tmdb(discover=item.search, tipo=item.extra, idioma_busqueda=langt)
            id_cast = ob_tmdb.result["person_results"][0]["id"]
            if item.contentType == "movie":
                item.search = {'url': 'discover/movie', 'with_cast': id_cast, 'page': item.pagina,
                               'sort_by': 'primary_release_date.desc', 'language': langt}
            else:
                item.search = {'url': 'person/%s/tv_credits' % id_cast, 'language': langt}
            ob_tmdb = Tmdb(discover=item.search, tipo=item.extra, idioma_busqueda=langt)
        except:
            pass
    else:
        ob_tmdb = Tmdb(discover=item.search, tipo=item.extra, idioma_busqueda=langt)

    # Sagas y colecciones
    if "collection" in item.search["url"]:
        try:
            new_item = item.clone(action="", url='')
            new_item.infoLabels["plot"] = ob_tmdb.result["overview"]
            itemlist.append(new_item)
            for parte in ob_tmdb.result["parts"]:
                new_item = item.clone(action="detalles")
                new_item.infoLabels = ob_tmdb.get_infoLabels(new_item.infoLabels, origen=parte)
                if new_item.infoLabels['thumbnail']:
                    new_item.thumbnail = new_item.infoLabels['thumbnail']
                if new_item.infoLabels['fanart']:
                    new_item.fanart = new_item.infoLabels['fanart']

                if new_item.infoLabels['year']:
                    new_item.title = "%s  (%s) [COLOR %s]%s[/COLOR]" \
                                     % (new_item.contentTitle, new_item.infoLabels['year'], color6,
                                        str(new_item.infoLabels['rating']).replace("0.0", ""))
                else:
                    new_item.title = "%s  [COLOR %s]%s[/COLOR]" \
                                     % (new_item.contentTitle, color6, new_item.infoLabels['rating'].replace("0.0", ""))
                itemlist.append(new_item)
        except:
            pass
    else:
        try:
            orden = False
            # Si se hace una búsqueda por actores o directores, se extraen esos resultados
            if "cast" in ob_tmdb.result and not item.crew:
                ob_tmdb.results = ob_tmdb.result["cast"]
                orden = True
            elif "crew" in ob_tmdb.result and item.crew:
                ob_tmdb.results = ob_tmdb.result["crew"]
                orden = True
            for i in range(0, len(ob_tmdb.results)):
                new_item = item.clone(action="detalles", url='', infoLabels={'mediatype': item.contentType})
                new_item.infoLabels = ob_tmdb.get_infoLabels(new_item.infoLabels, origen=ob_tmdb.results[i])
                # Si no hay sinopsis en idioma elegido, buscar en el alternativo
                if not new_item.infoLabels["plot"] and not 'person' in item.search["url"]:
                    ob_tmdb2 = Tmdb(id_Tmdb=new_item.infoLabels["tmdb_id"], tipo=item.extra, idioma_busqueda=langt_alt)
                    new_item.infoLabels["plot"] = ob_tmdb2.get_sinopsis()
                if new_item.infoLabels['thumbnail']:
                    new_item.thumbnail = new_item.infoLabels['thumbnail']
                elif new_item.infoLabels['profile_path']:
                    new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + new_item.infoLabels['profile_path']
                    new_item.infoLabels['profile_path'] = ''
                    new_item.plot = new_item.infoLabels["biography"]
                    if not item.search.get('with_cast', '') and not item.search.get('with_crew', ''):
                        if item.contentType == "movie":
                            new_item.action = "listado_tmdb"
                            cast = 'with_cast'
                            if item.crew:
                                cast = 'with_crew'
                            new_item.search = {'url': 'discover/movie', cast: new_item.infoLabels['tmdb_id'],
                                               'sort_by': 'primary_release_date.desc', 'language': langt,
                                               'page': item.pagina}
                        else:
                            new_item.action = "listado_tmdb"
                            new_item.search = {'url': 'person/%s/tv_credits' % new_item.infoLabels['tmdb_id'],
                                               'language': langt}

                elif not new_item.infoLabels['thumbnail'] and not new_item.infoLabels['profile_path']:
                    new_item.thumbnail = ''
                if new_item.infoLabels['fanart']:
                    new_item.fanart = new_item.infoLabels['fanart']

                if not 'person' in item.search["url"] or 'tv_credits' in item.search["url"]:
                    if new_item.infoLabels['year']:
                        new_item.title = "%s  (%s) [COLOR %s]%s[/COLOR]" \
                                         % (new_item.contentTitle, new_item.infoLabels['year'], color6,
                                            str(new_item.infoLabels['rating']).replace("0.0", ""))
                    else:
                        new_item.title = "%s  [COLOR %s]%s[/COLOR]" \
                                         % (new_item.contentTitle, color6,
                                            new_item.infoLabels['rating'].replace("0.0", ""))
                else:
                    # Si es una búsqueda de personas se incluye en el título y fanart una película por la que es conocido
                    known_for = ob_tmdb.results[i].get("known_for")
                    type=item.type
                    if known_for:
                        from random import randint
                        random = randint(0, len(known_for) - 1)
                        new_item.title = "%s  [COLOR %s](%s)[/COLOR] (%s)" \
                                         % (new_item.contentTitle, color6,
                                            known_for[random].get("title", known_for[random].get("name")), type)
                        if known_for[random]["backdrop_path"]:
                            new_item.fanart = 'http://image.tmdb.org/t/p/original' + known_for[random]["backdrop_path"]
                    else:
                        new_item.title = new_item.contentTitle
                itemlist.append(new_item)
        except:
            import traceback
            logger.error(traceback.format_exc())

        if orden:
            itemlist.sort(key=lambda item: item.infoLabels["year"], reverse=True)
        if "page" in item.search and ob_tmdb.total_pages > item.search["page"]:
            item.search["page"] += 1
            itemlist.append(Item(channel=item.channel, action=item.action, title=config.get_localized_string(70065),
                                 search=item.search, extra=item.extra, pagina=item.pagina + 1,
                                 contentType=item.contentType))

    return itemlist


def detalles(item):
    itemlist = []
    images = {}
    data = ""
    # Si viene de seccion imdb
    if not item.infoLabels["tmdb_id"]:
        headers = [['Accept-Language', langi]]
        #data = httptools.downloadpage("http://www.imdb.com/title/" + item.infoLabels['imdb_id'], headers=headers,
        #                                                           replace_headers=True).data
        data = httptools.downloadpage("http://www.imdb.com/title/" + item.infoLabels['imdb_id'], headers=headers).data

        pics = scrapertools.find_single_match(data, 'showAllVidsAndPics.*?href=".*?(tt\d+)')
        # Imágenes imdb
        if pics:
            images["imdb"] = {'url': 'http://www.imdb.com/_json/title/%s/mediaviewer' % pics}

        ob_tmdb = Tmdb(external_id=item.infoLabels["imdb_id"], external_source="imdb_id", tipo=item.extra,
                       idioma_busqueda=langt)
        item.infoLabels["tmdb_id"] = ob_tmdb.get_id()

    ob_tmdb = Tmdb(id_Tmdb=item.infoLabels["tmdb_id"], tipo=item.extra, idioma_busqueda=langt)

    try:
        item.infoLabels = ob_tmdb.get_infoLabels(item.infoLabels)
        # Si no hay sinopsis en idioma elegido, buscar en el alternativo
        if not item.infoLabels["plot"]:
            item.infoLabels["plot"] = ob_tmdb.get_sinopsis(idioma_alternativo=langt_alt)
    except:
        pass
    if not item.fanart and item.infoLabels['fanart']:
        item.fanart = item.infoLabels['fanart']
    if item.infoLabels['thumbnail']:
        item.thumbnail = item.infoLabels['thumbnail']

    # Sinopsis, votos de imdb
    if data:
        plot = scrapertools.find_single_match(data, 'class="inline canwrap" itemprop="description">(.*?)</div>')
        plot = scrapertools.htmlclean(plot)
        plot = re.sub(r'(?i)<em[^>]+>|\n|\s{2}', ' ', plot).strip()
        if plot and (item.infoLabels['plot'] and item.infoLabels['plot'] != plot):
            item.infoLabels['plot'] += " (TMDB)\n" + plot + " (IMDB)"
        elif plot and not item.infoLabels['plot']:
            item.infoLabels['plot'] = plot
        rating = scrapertools.find_single_match(data, 'itemprop="ratingValue">([^<]+)<')
        if rating:
            item.infoLabels['rating'] = float(rating.replace(",", "."))
        votos = scrapertools.find_single_match(data, 'itemprop="ratingCount">([^<]+)<')
        if votos:
            item.infoLabels['votes'] = votos

    if item.infoLabels['tagline']:
        itemlist.append(item.clone(title="--- %s ---" % item.infoLabels['tagline'], text_color="0xFFFF8C00", action=""))

    title = item.contentType.replace("movie", config.get_localized_string(70283)).replace("tvshow", "serie")
    # Búsqueda por títulos idioma elegido y/o versión original y español
    itemlist.append(item.clone(action="busqueda", title=config.get_localized_string(70069) % (title, item.contentTitle)))
    if item.infoLabels['originaltitle'] and item.contentTitle != item.infoLabels['originaltitle']:
        itemlist.append(item.clone(action="busqueda", contentTitle=item.infoLabels['originaltitle'],
                                   title=config.get_localized_string(70070) % item.infoLabels['originaltitle']))

    if langt != "es" and langt != "en" and item.infoLabels["tmdb_id"]:
        tmdb_lang = Tmdb(id_Tmdb=item.infoLabels["tmdb_id"], tipo=item.extra, idioma_busqueda='es')
        if tmdb_lang.result.get("title") and tmdb_lang.result["title"] != item.contentTitle \
                and tmdb_lang.result["title"] != item.infoLabels['originaltitle']:
            tmdb_lang = tmdb_lang.result["title"]
            itemlist.append(item.clone(action="busqueda", title=config.get_localized_string(70066) % tmdb_lang,
                                       contentTitle=tmdb_lang))

            # En caso de serie, opción de info por temporadas
    if item.contentType == "tvshow" and item.infoLabels['tmdb_id']:
        itemlist.append(item.clone(action="info_seasons", text_color=color4,
                                   title=config.get_localized_string(70067) % item.infoLabels["number_of_seasons"]))
    # Opción de ver el reparto y navegar por sus películas/series
    if item.infoLabels['tmdb_id']:
        itemlist.append(item.clone(action="reparto", title=config.get_localized_string(70071), text_color=color4,
                                   infoLabels={'tmdb_id': item.infoLabels['tmdb_id'],
                                               'mediatype': item.contentType}))

    if config.is_xbmc():
        item.contextual = True
    itemlist.append(item.clone(channel="trailertools", action="buscartrailer", title=config.get_localized_string(60359),
                               text_color=color5))

    try:
        images['tmdb'] = ob_tmdb.result["images"]
        itemlist.append(item.clone(action="imagenes", title=config.get_localized_string(70316), text_color=color5, images=images,
                                   extra="menu"))
    except:
        pass

    try:
        if item.contentType == "movie" and item.infoLabels["year"] < 2014:
            post_url = "https://theost.com/search/custom/?key=%s&year=%s&country=0&genre=0" % (
            item.infoLabels['originaltitle'].replace(" ", "+"), item.infoLabels["year"])
            url = "https://nl.hideproxy.me/includes/process.php?action=update"
            post = "u=%s&proxy_formdata_server=nl&allowCookies=1&encodeURL=1&encodePage=0&stripObjects=0&stripJS=0&go=" % urllib.quote(
                post_url)
            while True:
                response = httptools.downloadpage(url, post=post, follow_redirects=False)
                if response.headers.get("location"):
                    url = response.headers["location"]
                    post = ""
                else:
                    data_music = response.data
                    break

            url_album = scrapertools.find_single_match(data_music, 'album(?:|s) on request.*?href="([^"]+)"')
            if url_album:
                url_album = "https://nl.hideproxy.me" + url_album
                itemlist.append(
                    item.clone(action="musica_movie", title=config.get_localized_string(70317), url=url_album,
                               text_color=color5))
    except:
        pass

    token_auth = config.get_setting("token_trakt", "trakt")
    if token_auth:
        itemlist.append(item.clone(title=config.get_localized_string(70318), action="menu_trakt"))

    itemlist.append(item.clone(title="", action=""))
    # Es parte de una colección
    try:
        if ob_tmdb.result.get("belongs_to_collection"):
            new_item = item.clone(search='', infoLabels={'mediatype': item.contentType})
            saga = ob_tmdb.result["belongs_to_collection"]
            new_item.infoLabels["tmdb_id"] = saga["id"]
            if saga["poster_path"]:
                new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + saga["poster_path"]
            if saga["backdrop_path"]:
                new_item.fanart = 'http://image.tmdb.org/t/p/original' + saga["backdrop_path"]
            new_item.search = {'url': 'collection/%s' % saga['id'], 'language': langt}
            itemlist.append(new_item.clone(title=config.get_localized_string(70327) % saga["name"], action="listado_tmdb",
                                           text_color=color5))
    except:
        pass

    # Películas/Series similares y recomendaciones
    if item.infoLabels['tmdb_id']:
        item.extra = item.contentType.replace('tvshow', 'tv')
        title = title.replace("película", config.get_localized_string(70137)).replace("serie", config.get_localized_string(30123))
        itemlist.append(item.clone(title=config.get_localized_string(70328) % title, action="listado_tmdb",
                                   search={'url': '%s/%s/similar' % (item.extra, item.infoLabels['tmdb_id']),
                                           'language': langt, 'page': 1}, infoLabels={'mediatype': item.contentType},
                                   text_color=color2))
        itemlist.append(
            item.clone(title=config.get_localized_string(70315), action="listado_tmdb", infoLabels={'mediatype': item.contentType},
                       search={'url': '%s/%s/recommendations' % (item.extra, item.infoLabels['tmdb_id']),
                               'language': langt, 'page': 1}, text_color=color2))

    return itemlist


def reparto(item):
    # Actores y equipo de rodaje de una película/serie
    itemlist = []
    item.text_color = color1
    item.extra=item.contentType.replace('tvshow','tv')
    item.search = {'url': '%s/%s/credits' % (item.extra, item.infoLabels['tmdb_id'])}
    ob_tmdb = Tmdb(discover=item.search, tipo=item.extra, idioma_busqueda=langt)

    try:
        cast = ob_tmdb.result["cast"]
        if cast:
            itemlist.append(item.clone(title=config.get_localized_string(70314), action="", text_color=color2))
            for actor in cast:
                new_item = item.clone(action="listado_tmdb", fanart=default_fan)
                new_item.title = "    " + actor["name"] + " as " + actor["character"]
                if actor["profile_path"]:
                    new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + actor["profile_path"]
                if item.contentType == "movie":
                    new_item.search = {'url': 'discover/movie', 'with_cast': actor['id'],
                                       'language': langt, 'page': 1,
                                       'sort_by': 'primary_release_date.desc'}
                else:
                    new_item.search = {'url': 'person/%s/tv_credits' % actor['id'], 'language': langt}
                itemlist.append(new_item)
    except:
        pass

    try:
        crew = ob_tmdb.result["crew"]
        if crew:
            itemlist.append(item.clone(title=config.get_localized_string(70319), action="", text_color=color2))
            for c in crew:
                new_item = item.clone(action="listado_tmdb", fanart=default_fan)
                new_item.title = "    " + c["job"] + ": " + c["name"]
                if c["profile_path"]:
                    new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + c["profile_path"]
                if item.contentType == "movie":
                    new_item.search = {'url': 'discover/movie', 'with_crew': c['id'], 'page': 1,
                                       'sort_by': 'primary_release_date.desc'}
                else:
                    new_item.search = {'url': 'person/%s/tv_credits' % c['id'], 'language': langt}
                    new_item.crew = True
                itemlist.append(new_item)
    except:
        pass

    return itemlist


def info_seasons(item):
    # Info de temporadas y episodios
    itemlist = []
    item.text_color = color4
    ob_tmdb = Tmdb(id_Tmdb=item.infoLabels["tmdb_id"], tipo="tv", idioma_busqueda=langt)

    for temp in range(item.infoLabels["number_of_seasons"], 0, -1):
        temporada = ob_tmdb.get_temporada(temp)
        if temporada:
            new_item = item.clone(action="", mediatype="season")
            new_item.infoLabels['title'] = temporada['name']
            new_item.infoLabels['season'] = temp
            if temporada['overview']:
                new_item.infoLabels['plot'] = temporada['overview']
            if temporada['air_date']:
                date = temporada['air_date'].split('-')
                new_item.infoLabels['aired'] = date[2] + "/" + date[1] + "/" + date[0]
                new_item.infoLabels['year'] = date[0]
            if temporada['poster_path']:
                new_item.infoLabels['poster_path'] = 'http://image.tmdb.org/t/p/original' + temporada['poster_path']
                new_item.thumbnail = new_item.infoLabels['poster_path']
            new_item.title = config.get_localized_string(60027) % temp
            itemlist.append(new_item)

            for epi in range(1, len(temporada["episodes"])):
                episodio = ob_tmdb.get_episodio(temp, epi)
                if episodio:
                    new_item = item.clone(action="", text_color=color1, mediatype="episode")
                    new_item.infoLabels['season'] = temp
                    new_item.infoLabels['episode'] = epi
                    new_item.infoLabels['title'] = episodio['episodio_titulo']
                    if episodio['episodio_sinopsis']:
                        new_item.infoLabels['plot'] = episodio['episodio_sinopsis']
                    if episodio['episodio_imagen']:
                        new_item.infoLabels['poster_path'] = episodio['episodio_imagen']
                        new_item.thumbnail = new_item.infoLabels['poster_path']
                    if episodio['episodio_air_date']:
                        new_item.infoLabels['aired'] = episodio['episodio_air_date']
                        new_item.infoLabels['year'] = episodio['episodio_air_date'].rsplit("/", 1)[1]
                    if episodio['episodio_vote_average']:
                        new_item.infoLabels['rating'] = episodio['episodio_vote_average']
                        new_item.infoLabels['votes'] = episodio['episodio_vote_count']
                    new_item.title = "      %sx%s - %s" % (temp, epi, new_item.infoLabels['title'])
                    itemlist.append(new_item)

    return itemlist


def indices_tmdb(item):
    # Indices por genero y año
    itemlist = []
    from datetime import datetime
    if config.get_localized_string(70032) in item.title:
        thumbnail = {}
        url = ('http://api.themoviedb.org/3/genre/%s/list?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s'
               % (item.extra, langt))
        lista_generos = {}
        try:
            lista = jsontools.load(httptools.downloadpage(url, cookies=False).data)["genres"]
            for l in lista:
                lista_generos[str(l["id"])] = l["name"]
                if "es" in langt:
                    thumbnail[str(l["id"])] = "%s1/%s.jpg" % (images_predef, l["name"].lower() \
                                                              .replace("ó", "o").replace("í", "i") \
                                                              .replace(" ", "%20").replace("Aventuras", "Aventura")
                                                              .replace("ú", "u"))
                else:
                    thumbnail[str(l["id"])] = "%s2/%s.jpg" % (images_predef, l["name"])
        except:
            pass

        fecha = datetime.now().strftime('%Y-%m-%d')
        sort_by = 'release_date.desc'
        param_year = 'release_date.lte'
        if item.contentType == 'tvshow':
            sort_by = 'first_air_date.desc'
            param_year = 'air_date.lte'
        for key, value in lista_generos.items():
            search = {'url': 'discover/%s' % item.extra, 'with_genres': key, 'sort_by': sort_by,
                        param_year: fecha,
                        'language': langt, 'page': 1}
            new_item = item.clone(title=value, thumbnail=thumbnail[key], action="listado_tmdb", search=search)
            itemlist.append(new_item)

        itemlist.sort(key=lambda item: item.title)
    else:
        year = datetime.now().year + 3
        for i in range(year, 1899, -1):
            if item.contentType == 'tvshow':
                param_year = 'first_air_date_year'
            else:
                param_year = 'primary_release_year'
            search = {'url': 'discover/%s' % item.extra, param_year: i, 'language': langt, 'page': 1}
            itemlist.append(item.clone(title=str(i), action='listado_tmdb', search=search))

    return itemlist


def filtro(item):
    logger.info()

    from datetime import datetime
    list_controls = []
    valores = {}

    dict_values = None

    list_controls.append({'id': 'years', 'label': config.get_localized_string(60232), 'enabled': True, 'color': '0xFFCC2EFA',
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[0]['lvalues'] = []
    valores['years'] = []
    year = datetime.now().year + 1
    for i in range(1900, year + 1):
        list_controls[0]['lvalues'].append(str(i))
        valores['years'].append(str(i))
    list_controls[0]['lvalues'].append(config.get_localized_string(70450))
    valores['years'].append('')

    if "Personalizado" in item.title:
        # Se utilizan los valores por defecto/guardados
        valores_guardados = config.get_setting("filtro_defecto_" + item.extra, item.channel)
        if valores_guardados:
            dict_values = valores_guardados
        url = ('http://api.themoviedb.org/3/genre/%s/list?api_key=f7f51775877e0bb6703520952b3c7840&language=%s'
               % (item.extra, langt))
        try:
            lista = jsontools.load(httptools.downloadpage(url, cookies=False).data)["genres"]
            if lista:
                list_controls.append({'id': 'labelgenre', 'enabled': True, 'type': 'label', 'default': None,
                                      'label': config.get_localized_string(70451),
                                      'visible': True, 'color': '0xFFC52020'})
                for l in lista:
                    list_controls.append({'id': 'genre' + str(l["id"]), 'label': l["name"], 'enabled': True,
                                          'type': 'bool', 'default': False, 'visible': True})
        except:
            pass

        list_controls.append({'id': 'orden', 'label': config.get_localized_string(70455), 'enabled': True, 'color': '0xFF25AA48',
                              'type': 'list', 'default': -1, 'visible': True})
        orden = [config.get_localized_string(70456), config.get_localized_string(70457), config.get_localized_string(70458), config.get_localized_string(70459), config.get_localized_string(70460), config.get_localized_string(70461)]
        if item.extra == "movie":
            orden.extend([config.get_localized_string(70462), config.get_localized_string(70463)])
        orden_tmdb = ['popularity.desc', 'popularity.asc', 'release_date.desc', 'release_date.asc',
                      'vote_average.desc', 'vote_average.asc', 'original_title.asc', 'original_title.desc']
        valores['orden'] = []
        list_controls[-1]['lvalues'] = []
        for i, tipo_orden in enumerate(orden):
            list_controls[-1]['lvalues'].insert(0, tipo_orden)
            valores['orden'].insert(0, orden_tmdb[i])

        list_controls.append({'id': 'espacio', 'label': '', 'enabled': False,
                              'type': 'label', 'default': None, 'visible': True})
        list_controls.append({'id': 'save', 'label': config.get_localized_string(70464), 'enabled': True,
                              'type': 'bool', 'default': False, 'visible': True})
    else:
        list_controls.append({'id': 'keyword', 'label': config.get_localized_string(70465), 'enabled': True,
                              'type': 'text', 'default': '', 'visible': True})

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70320), item=item, callback='filtrado')


def filtrado(item, values):
    values_copy = values.copy()
    # Guarda el filtro para que sea el que se cargue por defecto
    if "save" in values and values["save"]:
        values_copy.pop("save")
        config.set_setting("filtro_defecto_" + item.extra, values_copy, item.channel)

    year = item.valores["years"][values["years"]]
    if "Personalizado" in item.title:
        orden = item.valores["orden"][values["orden"]]
        if item.extra == "tv":
            orden = orden.replace('release_date', 'first_air_date')

        genero_ids = []
        for v in values:
            if "genre" in v:
                if values[v]:
                    genero_ids.append(v.replace('genre', ''))
        genero_ids = ",".join(genero_ids)

    if "clave" in item.title:
        item.search = {'url': 'search/%s' % item.extra, 'year': year, 'query': values["keyword"],
                       'language': langt, 'page': 1}
    elif item.extra == "movie":
        item.search = {'url': 'discover/%s' % item.extra, 'sort_by': orden, 'primary_release_year': year,
                       'with_genres': genero_ids, 'vote_count.gte': '10', 'language': langt, 'page': 1}
    else:
        item.search = {'url': 'discover/%s' % item.extra, 'sort_by': orden, 'first_air_date_year': year,
                       'with_genres': genero_ids, 'vote_count.gte': '10', 'language': langt, 'page': 1}

    item.action = "listado_tmdb"
    return listado_tmdb(item)


def musica_movie(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<td class="left">([^<]+)<br><small>([^<]+)</small>.*?<td>(\d+:\d+).*?<p id="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for titulo, artist, duration, id_p in matches:
        title = "%s (%s) [%s]" % (titulo, artist, duration)
        url = scrapertools.find_single_match(data, "AudioPlayer.embed\('%s'.*?soundFile: '([^']+)'" % id_p)
        itemlist.append(Item(channel=item.channel, action="play", server="directo", url=url, title=title,
                             thumbnail=item.thumbnail, fanart=item.fanart, text_color=color5))
    return itemlist


##-------------------- SECCION IMDB ------------------------##
def listado_imdb(item):
    # Método principal para secciones de imdb
    itemlist = []
    item.text_color = color1

    headers = [['Accept-Language', langi]]
    if "www.imdb.com" in item.url:
        #data = httptools.downloadpage(item.url, headers=headers, replace_headers=True).data
        data = httptools.downloadpage(item.url, headers=headers).data
    else:
        url = 'http://www.imdb.com/search/title?' + item.url
        #data = httptools.downloadpage(url, headers=headers, replace_headers=True).data
        data = httptools.downloadpage(url, headers=headers).data

    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    # Listado de actores
    if 'search/name' in item.url:
        patron = '<td class="image">.*?src="([^"]+)".*?href="/name/(nm\d+).*?>([^<]+)<.*?href.*?>([^<]+)</a>' \
                 '</span>(.*?)</td>'
        matches = scrapertools.find_multiple_matches(data, patron)
        for thumbnail, imdb_id, title, movie, datos in matches:
            new_item = item.clone(action='listado_tmdb')
            try:
                if "@" in thumbnail:
                    thumbnail = thumbnail.rsplit('@', 1)[0]
                    thumbnail += "@._UX482.jpg"
                elif "._V1_" in thumbnail:
                    thumbnail = thumbnail.rsplit('._V1_', 1)[0]
                    thumbnail += "._V1_UX482.jpg"
            except:
                pass
            new_item.thumbnail = thumbnail

            datos = datos.strip()
            if datos:
                new_item.infoLabels['plot'] = scrapertools.htmlclean(datos)
            new_item.title = title.strip() + '   [COLOR %s](%s)[/COLOR]' % (color6, movie.strip())
            new_item.infoLabels['imdb_id'] = imdb_id
            new_item.search = {'url': 'find/%s' % imdb_id, 'external_source': 'imdb_id', 'language': langt}
            itemlist.append(new_item)
    else:
        patron = '(?:<div class="image">|<div class="lister-item-image).*?(?:loadlate="([^"]+)"|src="([^"]+)")' \
                 '.*?href=".*?/(tt\d+).*?>([^<]+)</a>(.*?)(?:<p class="(?:text-muted|)">([^<]+)|"description">([^<]+)<)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for thumbnail, thumb2, imdb_id, title, datos, plot, plot2 in matches:

            new_item = item.clone(action='detalles')
            new_item.title = title.strip()
            if not thumbnail:
                thumbnail = thumb2
            try:
                if "@" in thumbnail:
                    thumbnail = thumbnail.rsplit('@', 1)[0]
                    thumbnail += "@._UX482.jpg"
                elif "._V1_" in thumbnail:
                    thumbnail = thumbnail.rsplit('._V1_', 1)[0]
                    thumbnail += "._V1_UX482.jpg"
            except:
                pass
            new_item.thumbnail = thumbnail

            if not plot:
                plot = plot2
            new_item.infoLabels['plot'] = scrapertools.htmlclean(plot.strip())

            generos = scrapertools.find_multiple_matches(datos, 'genre">([^<]+)<')
            if generos:
                new_item.infoLabels["genre"] = ", ".join(generos)
            duracion = scrapertools.find_single_match(datos, '(\d+) min')
            if duracion:
                new_item.infoLabels['duration'] = int(duracion) * 60

            new_item.infoLabels['year'] = scrapertools.find_single_match(new_item.title, '\((\d{4})')
            if not new_item.infoLabels['year']:
                new_item.infoLabels['year'] = scrapertools.find_single_match(datos, 'year.*?\((\d{4})')
                if new_item.infoLabels['year']:
                    new_item.title += '  (%s)' % new_item.infoLabels['year']

            rating = scrapertools.find_single_match(datos, '(?:rating|Metascore).*?<strong>([^<]*)</strong>')
            rating = rating.replace(",", ".")
            if rating:
                if not "." in rating:
                    try:
                        rating = float(rating) / 10
                    except:
                        rating = None
                if rating:
                    new_item.title += "  [COLOR %s]%s[/COLOR]" % (color6, str(rating))
                    new_item.infoLabels['rating'] = float(rating)
            new_item.infoLabels['imdb_id'] = imdb_id
            itemlist.append(new_item)

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]*>Next')
    if next_page:
        if not "title_type" in item.url:
            next_page = 'http://www.imdb.com' + next_page
        else:
            next_page = 'http://www.imdb.com/search/title' + next_page
        itemlist.append(item.clone(title=config.get_localized_string(70065), url=next_page, text_color=''))

    return itemlist


def filtro_imdb(item):
    logger.info()

    from datetime import datetime
    list_controls = []
    valores = {}

    dict_values = None
    # Se utilizan los valores por defecto/guardados
    valores_guardados = config.get_setting("filtro_defecto_imdb_" + item.extra, item.channel)
    if valores_guardados:
        dict_values = valores_guardados

    list_controls.append({'id': 'title', 'label': config.get_localized_string(60320), 'enabled': True,
                          'type': 'text', 'default': '', 'visible': True})

    list_controls.append({'id': 'yearsdesde', 'label': config.get_localized_string(70452), 'enabled': True, 'color': '0xFFCC2EFA',
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls.append({'id': 'yearshasta', 'label': config.get_localized_string(70453), 'enabled': True, 'color': '0xFF2ECCFA',
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[1]['lvalues'] = []
    list_controls[2]['lvalues'] = []
    valores['years'] = []
    year = datetime.now().year + 1
    for i in range(1900, year + 1):
        list_controls[1]['lvalues'].append(str(i))
        list_controls[2]['lvalues'].append(str(i))
        valores['years'].append(str(i))
    list_controls[1]['lvalues'].append(config.get_localized_string(70450))
    list_controls[2]['lvalues'].append(config.get_localized_string(70450))
    valores['years'].append('')

    try:
        generos_spa = {'Action': config.get_localized_string(70394), 'Adventure': config.get_localized_string(60267), 'Animation': config.get_localized_string(60268), 'Biography': config.get_localized_string(70403),
                       'Comedy': config.get_localized_string(60270), 'Crime': config.get_localized_string(60271), 'Documentary': config.get_localized_string(70396), 'Family': config.get_localized_string(70399),
                       'Fantasy': config.get_localized_string(60274), 'Film-Noir': config.get_localized_string(70400), 'Game-Show': config.get_localized_string(70401),
                       'History': config.get_localized_string(70405), 'Horror': config.get_localized_string(70013), 'Music': config.get_localized_string(70404), 'Mistery': config.get_localized_string(70402),
                       'News': config.get_localized_string(60279), 'Reality-TV': config.get_localized_string(70406), 'Sci-Fi': config.get_localized_string(70397), 'Sport': config.get_localized_string(70395),
                       'Talk-Show': config.get_localized_string(70398), 'War': config.get_localized_string(70407)}
        data = httptools.downloadpage("http://www.imdb.com/search/title", cookies=False).data
        bloque = scrapertools.find_single_match(data, '<h3>Genres</h3>(.*?)</table>')
        matches = scrapertools.find_multiple_matches(bloque, ' value="([^"]+)"\s*>\s*<label.*?>([^<]+)<')
        if matches:
            list_controls.append({'id': 'labelgenre', 'enabled': True, 'type': 'label', 'visible': True,
                                  'label': config.get_localized_string(70451), 'color': '0xFFC52020'})
            lista = []
            for valor, titulo in matches:
                titulo = generos_spa.get(titulo, titulo)
                lista.append([valor, titulo])
            lista.sort(key=lambda lista: lista[1])
            for valor, titulo in lista:
                list_controls.append({'id': 'genre' + valor, 'label': titulo, 'enabled': True,
                                      'type': 'bool', 'default': False, 'visible': True})
    except:
        pass

    list_controls.append({'id': 'espacio', 'label': '', 'enabled': False,
                          'type': 'label', 'default': None, 'visible': True})
    try:
        bloque = scrapertools.find_single_match(data, '<h3>Countries</h3>(.*?)Less-Common')
        matches = scrapertools.find_multiple_matches(bloque, ' value="([^"]+)"\s*>([^<]+)<')
        if matches:
            list_controls.append({'id': 'pais', 'label': config.get_localized_string(70466), 'enabled': True, 'color': '0xFFFF8000',
                                  'type': 'list', 'default': -1, 'visible': True})
            list_controls[-1]['lvalues'] = []
            list_controls[-1]['lvalues'].append(config.get_localized_string(70450))
            valores['pais'] = []
            valores['pais'].append('')
            for valor, titulo in matches:
                list_controls[-1]['lvalues'].insert(0, titulo)
                valores['pais'].insert(0, valor)

    except:
        pass

    list_controls.append({'id': 'orden', 'label': config.get_localized_string(70455), 'enabled': True, 'color': '0xFF25AA48',
                          'type': 'list', 'default': -1, 'visible': True})
    orden = [config.get_localized_string(70456), config.get_localized_string(70457), config.get_localized_string(70458), config.get_localized_string(70459), config.get_localized_string(70460), config.get_localized_string(70461),
             config.get_localized_string(70462), config.get_localized_string(70463)]

    orden_imdb = ['moviemeter,asc', 'moviemeter,desc', 'year,desc', 'year,asc',
                  'user_rating,desc', 'user_rating,asc', 'alpha,asc', 'alpha,desc']
    valores['orden'] = []
    list_controls[-1]['lvalues'] = []
    for i, tipo_orden in enumerate(orden):
        list_controls[-1]['lvalues'].insert(0, tipo_orden)
        valores['orden'].insert(0, orden_imdb[i])

    list_controls.append({'id': 'save', 'label': config.get_localized_string(70464), 'enabled': True,
                          'type': 'bool', 'default': False, 'visible': True})

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70320), item=item, callback='filtrado_imdb')


def filtrado_imdb(item, values):
    values_copy = values.copy()
    # Guarda el filtro para que sea el que se cargue por defecto
    if "save" in values and values["save"]:
        values_copy.pop("save")
        config.set_setting("filtro_defecto_imdb_" + item.extra, values_copy, item.channel)

    yeard = item.valores["years"][values["yearsdesde"]]
    yearh = item.valores["years"][values["yearshasta"]]
    orden = item.valores["orden"][values["orden"]]
    pais = item.valores["pais"][values["pais"]]

    genero_ids = []
    for v in values:
        if "genre" in v:
            if values[v]:
                genero_ids.append(v.replace('genre', ''))
    genero_ids = ",".join(genero_ids)
    try:
        votos = int(values["votos"])
    except:
        votos = ""

    item.url = 'http://www.imdb.com/search/title?countries=%s&num_votes=%s,&genres=%s&release_date=%s,%s&sort=%s&' \
               'title=%s&title_type=' % (pais, str(votos), genero_ids, yeard, yearh, orden, values["title"])
    if item.contentType == "movie":
        item.url += "feature,tv_movie"
    else:
        item.url += "tv_series,tv_special,mini_series"

    item.action = "listado_imdb"
    return listado_imdb(item)


def indices_imdb(item):
    # Índices imdb por año y genero
    itemlist = []
    from datetime import datetime
    if config.get_localized_string(70032) in item.title:
        generos_spa = {'Action': config.get_localized_string(70394), 'Adventure': config.get_localized_string(60267), 'Animation': config.get_localized_string(60268), 'Biography': config.get_localized_string(70403), 'Thriller': config.get_localized_string(70410),
                       'Comedy': config.get_localized_string(60270), 'Crime': config.get_localized_string(60271), 'Documentary': config.get_localized_string(70396), 'Family': config.get_localized_string(70399), 'Romance': config.get_localized_string(70409),
                       'Fantasy': config.get_localized_string(60274), 'Film-Noir': config.get_localized_string(70400), 'Game-Show': config.get_localized_string(70401), 'Drama': config.get_localized_string(70412), 'Western': config.get_localized_string(70411),
                       'History': config.get_localized_string(70405), 'Horror': config.get_localized_string(70013), 'Music': config.get_localized_string(70404), 'Musical': config.get_localized_string(70408),'Mystery': config.get_localized_string(70402),
                       'News': config.get_localized_string(60279), 'Reality-TV': config.get_localized_string(70406), 'Sci-Fi': config.get_localized_string(70397), 'Sport': config.get_localized_string(70395),
                       'Talk-Show': config.get_localized_string(70398), 'War': config.get_localized_string(70407)}
        data = httptools.downloadpage("http://www.imdb.com/search/title", cookies=False).data
        bloque = scrapertools.find_single_match(data, '<h3>Genres</h3>(.*?)</table>')
        matches = scrapertools.find_multiple_matches(bloque, ' value="([^"]+)"\s*>\s*<label.*?>([^<]+)<')
        if matches:
            for valor, titulo in matches:
                title = generos_spa.get(titulo, titulo)
                thumbnail = "%s2/%s.jpg" % (images_predef, titulo)
                itemlist.append(item.clone(title=title, action='listado_imdb', thumbnail=thumbnail,
                                           url='http://www.imdb.com/search/title?genres=%s%s' % (valor, item.url)))
            itemlist.sort(key=lambda item: item.title)
    else:
        year = datetime.now().year + 3
        for i in range(year, 1899, -1):
            itemlist.append(item.clone(title=str(i), action='listado_imdb',
                                       url='http://www.imdb.com/search/title?release_date=%s,%s%s' % (i, i, item.url)))

    return itemlist


##-------------------- SECCION FILMAFFINITY ------------------------##
def listado_fa(item):
    # Método para listados principales de filmaffinity
    itemlist = []
    item.text_color = color1

    # Listados con paginación por post
    if item.extra == "top":
        if item.page_fa:
            post = "from=%s" % item.page_fa
            data = httptools.downloadpage(item.url, post=post).data
            if item.total > item.page_fa:
                item.page_fa += 30
            else:
                item.page_fa = ""
        else:
            item.page_fa = 30
            data = httptools.downloadpage(item.url).data
            item.total = int(scrapertools.find_single_match(data, 'tmResCount\s*=\s*(\d+)'))
            if item.total <= item.page_fa:
                item.page_fa = ""

    else:
        data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    votaciones = []
    # Si es la sección de estrenos cambia la estructura del scraper
    if item.extra == "estrenos":
        patron = '<i class="fa fa-calendar"></i>\s*(\d+[^<]+)<(.*?)(?:<div class="panel panel-default">|' \
                 '<div class="text-center")'
        bloques = scrapertools.find_multiple_matches(data, patron)
        for fecha, bloque in bloques:
            itemlist.append(item.clone(title=fecha, action='', text_color="0xFFFF8C00"))
            patron = '<a class="list-group-item" href="([^"]+)">.*?(?:data-src="([^"]+)"|' \
                     'src="((?!/images/empty.gif)[^"]+)").*?<div class="mc-title.*?>([^<]+)<small>\((\d+)\)</small>' \
                     '.*?(?:<div class="avgrat-box in-block ">([^<]+)</div>' \
                     '\s*<small class="ratcount-box">(.*?)\s*<|</li>)'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            for url, thumb, thumb2, title, year, rating, votos in matches:
                title = title.strip()
                new_item = item.clone(action="detalles_fa", contentType="movie", extra="movie", contentTitle=title)
                if not url.startswith("http://m.filmaffinity"):
                    new_item.url = "http://m.filmaffinity.com" + url
                else:
                    new_item.url = url

                if not thumb:
                    thumb = thumb2
                new_item.thumbnail = thumb.replace("msmall", "large")
                if not new_item.thumbnail.startswith("http"):
                    new_item.thumbnail = "http://m.filmaffinity.com" + new_item.thumbnail

                new_item.title = "   " + title + "  (%s) [COLOR %s]%s[/COLOR]" % (year, color6, rating)
                new_item.infoLabels['year'] = year
                votaciones.append([rating, votos])
                if rating:
                    new_item.infoLabels['rating'] = float(rating.replace(",", "."))
                    new_item.infoLabels['votes'] = votos
                itemlist.append(new_item)
    else:
        patron = '(?:<a class="list-group-item[^"]*" href="([^"]+)">|<a href="([^"]+)" class="list-group-item[^"]*">)' \
                 '.*?(?:data-src="([^"]+)"|src="((?!/images/empty.gif)[^"]+)").*?' \
                 '<div class="mc-title.*?>([^<]+)<small>\((\d+)\)</small>.*?(?:<div class="avgrat-box in-block ">' \
                 '([^<]+)</div>\s*<small class="ratcount-box">(.*?)\s*<|</li>)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, url2, thumb, thumb2, title, year, rating, votos in matches:
            title = title.strip()
            new_item = item.clone(action="detalles_fa", extra="movie")
            if not url:
                url = url2
            if not url.startswith("http://m.filmaffinity"):
                new_item.url = "http://m.filmaffinity.com" + url
            else:
                new_item.url = url

            if not thumb:
                thumb = thumb2
            new_item.thumbnail = thumb.replace("msmall", "large")
            if not new_item.thumbnail.startswith("http"):
                new_item.thumbnail = "http://m.filmaffinity.com" + new_item.thumbnail

            new_item.title = title.replace("(Serie de TV)", "").replace("(TV)", "") + "  (%s) [COLOR %s]%s[/COLOR]" \
                                                                                      % (year, color6, rating)
            new_item.contentTitle = re.sub(r'(?i)\(serie de tv\)|\(tv\)|\(c\)', '', title)
            if re.search(r'(?i)serie de tv|\(tv\)', title):
                new_item.contentType = "tvshow"
                new_item.extra = "tv"
                new_item.infoLabels["tvshowtitle"] = new_item.contentTitle

            new_item.infoLabels['year'] = year
            votaciones.append([rating, votos])
            if rating:
                new_item.infoLabels['rating'] = float(rating.replace(",", "."))
                new_item.infoLabels['votes'] = votos
            itemlist.append(new_item)

    if len(itemlist) < 31:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, True)
        for i, it in enumerate(itemlist):
            try:
                it.infoLabels['votes'] = votaciones[i][1]
                it.infoLabels['rating'] = float(votaciones[i][0].replace(",", "."))
            except:
                pass

    next_page = scrapertools.find_single_match(data, 'aria-label="Next" href="([^"]+)"')
    if next_page:
        if not next_page.startswith("http://m.filmaffinity"):
            next_page = "http://m.filmaffinity.com" + next_page

        itemlist.append(Item(channel=item.channel, action=item.action, title=config.get_localized_string(70065), url=next_page,
                             extra=item.extra))
    elif item.page_fa:
        itemlist.append(item.clone(title=config.get_localized_string(70065), text_color=""))
    return itemlist


def indices_fa(item):
    # Índices por genero, año, temas y sagas/colecciones
    itemlist = []
    item.text_color = color1
    if item.url:
        data = httptools.downloadpage(item.url).data
        data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
        data = re.sub(r"\s{2}", " ", data)
    if "sagas" in item.extra:
        patron = '<li class="fa-shadow">.*?href="([^"]+)".*?group-name">([^<]+)<.*?src="([^"]+)".*?' \
                 '"count-movies">([^<]+)<'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, title, thumbnail, info in matches:
            new_item = item.clone(action="listado_fa")
            if not url.startswith("http://www.filmaffinity"):
                new_item.url = "http://m.filmaffinity.com" + url
            else:
                new_item.url = url.replace("www.filmaffinity.com", "m.filmaffinity.com")

            new_item.thumbnail = thumbnail.replace("mmed", "large")
            new_item.title = title.strip() + "  [COLOR %s](%s)[/COLOR]" % (color6, info)
            itemlist.append(new_item)

        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">&gt;&gt;')
        if next_page:
            if not next_page.startswith("http://www.filmaffinity.com"):
                next_page = "http://www.filmaffinity.com" + next_page
            itemlist.append(Item(channel=item.channel, action=item.action, title=config.get_localized_string(70065), url=next_page,
                                 extra=item.extra))
    elif config.get_localized_string(70032) in item.title:
        bloque = scrapertools.find_single_match(data, 'name="genre">.*?</option>(.*?)</select>')
        matches = scrapertools.find_multiple_matches(bloque, '<option value="([^"]+)">([^<]+)</option>')
        for valor, titulo in matches:
            if valor == "TV_SE":
                continue
            new_item = item.clone(title=titulo, action="listado_fa", extra="top")
            new_item.url = "http://m.filmaffinity.com/%s/topgen.php?genre=%s&country=&fromyear=&toyear=&nodoc=1" \
                           % (langf, valor)
            if item.contentType == "movie":
                new_item.url += "&notvse=1"
            generos = ['1/accion.jpg', '1/animacion.jpg', '1/aventura.jpg', '1/guerra.jpg', '1/ciencia%20ficcion.jpg',
                       '2/Film-Noir.jpg', '1/comedia.jpg', '0/Unknown.png', '1/documental.jpg', '1/drama.jpg',
                       '1/fantasia.jpg', '2/Kids.jpg', '2/Suspense.jpg', '1/musical.jpg', '1/romance.jpg',
                       '1/terror.jpg', '1/thriler.jpg', '1/western.jpg']
            if langf != "en":
                try:
                    new_item.thumbnail = "%s/%s" % (images_predef, generos[len(itemlist)])
                except:
                    new_item.thumbnail = "%s1/%s.jpg" % (images_predef, titulo.lower())
            else:
                new_item.thumbnail = "%s2/%s.jpg" % (images_predef, titulo)
            itemlist.append(new_item)
    elif "Temas" in item.title:
        bloques = scrapertools.find_multiple_matches(data, '<div class="panel-heading" id="topic_([^"]+)".*?'
                                                           '<div class="list-group">(.*?)</div>')
        for letra, bloque in bloques:
            patron = 'href="([^"]+)">([^<]+)<.*?"badge">(\d+)</span>'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            extra = len(matches) + 1
            action = ""
            folder = True
            if config.is_xbmc():
                action = "move"
                folder = False
            itemlist.append(item.clone(title=letra, text_color=color2, action=action, extra=extra, folder=folder))
            for url, titulo, numero in matches:
                new_item = item.clone(action="temas_fa")
                topic_id = scrapertools.find_single_match(url, "topic=(\d+)")
                new_item.url = "http://www.filmaffinity.com/%s/%s&attr=all" % (
                langf, url.replace("&nodoc", "").replace("&notvse", ""))
                new_item.title = titulo + " (%s)" % numero
                itemlist.append(new_item)
    else:
        from datetime import datetime
        year = datetime.now().year
        for i in range(year, 1899, -1):
            new_item = item.clone(title=str(i), action="listado_fa", extra="top")
            genre = ''
            if item.contentType == "tvshow":
                genre = 'TV_SE'
            new_item.url = "http://m.filmaffinity.com/%s/topgen.php?genre=%s&country=&fromyear=%s&toyear=%s&nodoc=1" \
                           % (langf, genre, i, i)
            if item.contentType == "movie":
                new_item.url += "&notvse=1"
            itemlist.append(new_item)

    return itemlist


def temas_fa(item):
    # Películas y series por temas
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)
    item.infoLabels['plot'] = scrapertools.find_single_match(data, '<p class="description">([^<]+)</p>')

    patron = '<div class="mc-poster">\s*<a href=".*?(\d+)\.html".*?src="([^"]+)".*?' \
             'href.*?>([^<]+)</a>\s*\((\d+)\)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumb, title, year in matches:
        title = title.strip()
        new_item = item.clone(action="detalles_fa", contentType="movie", extra="movie", text_color=color2)
        new_item.url = "http://m.filmaffinity.com/%s/movie.php?id=%s" % (langf, url)
        new_item.thumbnail = thumb.replace("msmall", "large")
        if not new_item.thumbnail.startswith("http"):
            new_item.thumbnail = "http://www.filmaffinity.com" + new_item.thumbnail
        new_item.infoLabels["year"] = year
        new_item.title = title + "  (%s)" % year
        if re.search(r'(?i)serie de tv|\(tv\)', title):
            new_item.contentType = "tvshow"
            new_item.extra = "tv"
        new_item.contentTitle = re.sub(r'(?i)\(serie de tv\)|\(tv\)|\(c\)', '', title)
        itemlist.append(new_item)

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">&gt;&gt;')
    if next_page:
        if not next_page.startswith("http://www.filmaffinity.com"):
            next_page = "http://www.filmaffinity.com/%s/%s" % (langf, next_page)
        itemlist.append(Item(channel=item.channel, action=item.action, title=config.get_localized_string(70065), url=next_page))

    return itemlist


def detalles_fa(item):
    itemlist = []
    item.plot = ""
    rating = item.infoLabels['rating']
    votos = item.infoLabels['votes']

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    # Se extrae el título original para posibles búsquedas en tmdb posteriores
    orig_title = scrapertools.find_single_match(data, 'itemprop="datePublished">.*?<dd>([^<]+)</dd>').strip()
    if item.contentType == "movie":
        item.infoLabels['originaltitle'] = re.sub(r"(?i)\(TV Series\)|\(S\)|\(TV\)", "", orig_title)
    else:
        item.infoLabels['tvshowtitle'] = re.sub(r"(?i)\(TV Series\)|\(S\)|\(TV\)", "", orig_title)
    item_tmdb = item.clone()

    if item.contentType == "movie":
        ob_tmdb = Tmdb(texto_buscado=item_tmdb.contentTitle, year=item_tmdb.infoLabels['year'], tipo=item_tmdb.extra,
                       idioma_busqueda=langt)
        if not ob_tmdb.result:
            ob_tmdb = Tmdb(texto_buscado=item_tmdb.infoLabels['originaltitle'], year=item_tmdb.infoLabels['year'],
                           tipo=item_tmdb.extra, idioma_busqueda=langt)
    else:
        ob_tmdb = Tmdb(texto_buscado=item_tmdb.contentTitle, tipo=item_tmdb.extra, idioma_busqueda=langt)
        if not ob_tmdb.result:
            ob_tmdb = Tmdb(texto_buscado=item_tmdb.infoLabels['tvshowtitle'], tipo=item_tmdb.extra,
                           idioma_busqueda=langt)

    if ob_tmdb.result:
        ob_tmdb = Tmdb(id_Tmdb=ob_tmdb.get_id(), tipo=item_tmdb.extra, idioma_busqueda=langt)
        item.infoLabels = ob_tmdb.get_infoLabels(item.infoLabels)

        # Si no hay sinopsis en idioma elegido, buscar en el alternativo
        if not item.infoLabels["plot"]:
            item.infoLabels["plot"] = ob_tmdb.get_sinopsis(idioma_alternativo=langt_alt)

    # Se concatena el plot de filmaffinity al de tmdb si lo hay
    plot = scrapertools.find_single_match(data, '<dd itemprop="description">(.*?)</dd>')
    plot = plot.replace("<br><br />", "\n")
    plot = scrapertools.decodeHtmlentities(plot).replace(" (FILMAFFINITY)", "")
    if plot and (item.infoLabels['plot'] and item.infoLabels['plot'] != plot):
        item.infoLabels['plot'] += " (TMDB)\n" + plot + " (FILMAFFINITY)"
    elif plot and not item.infoLabels['plot']:
        item.infoLabels['plot'] = plot

    # Se busca y rellena con la info de filmaffinity para diferenciarla de tmdb
    if not item.infoLabels['duration']:
        duration = scrapertools.find_single_match(data, '<dd itemprop="duration">(\d+)')
        if duration:
            item.infoLabels['duration'] = int(duration) * 60

    if not item.infoLabels['genre']:
        generos = scrapertools.find_multiple_matches(data, 'class="g-t-item">(.*?)</a>')
        genres = []
        for g in generos:
            genres.append(scrapertools.htmlclean(g.strip()))
        item.infoLabels['genre'] = ", ".join(genres)

    if not rating:
        rating = scrapertools.find_single_match(data, 'itemprop="ratingValue".*?>([^<]+)<')
        if rating:
            rating = float(rating.replace(",", "."))
        elif ob_tmdb.result:
            rating = float(ob_tmdb.result.get('vote_average', 0))
        item.infoLabels['rating'] = rating

    if not votos:
        votos = scrapertools.find_single_match(data, 'itemprop="ratingCount".*?>([^<]+)<')
        if votos == "0" and ob_tmdb.result:
            votos = ob_tmdb.result.get('vote_count', '')
        item.infoLabels['votes'] = votos

    if item.infoLabels['fanart']:
        item.fanart = item.infoLabels['fanart']
    else:
        item.fanart = scrapertools.find_single_match(data, 'Imagen Principal.*?src: "([^"]+)"')
    if item.infoLabels['thumbnail']:
        item.thumbnail = item.infoLabels['thumbnail']

    if item.infoLabels['tagline']:
        itemlist.append(item.clone(title="--- %s ---" % item.infoLabels['tagline'], text_color="0xFFFF8C00", action=""))

    title = item.contentType.replace("movie", config.get_localized_string(70283)).replace("tvshow", "serie")
    itemlist.append(item.clone(action="busqueda", title=config.get_localized_string(70069) % (title, item.contentTitle)))
    if item.infoLabels['originaltitle'] and item.contentTitle != item.infoLabels['originaltitle']:
        itemlist.append(item.clone(action="busqueda", contentTitle=item.infoLabels['originaltitle'],
                                   title=config.get_localized_string(70070) % item.infoLabels['originaltitle']))

    if langt != "es" and langt != "en" and item.infoLabels["tmdb_id"]:
        tmdb_lang = Tmdb(id_Tmdb=item.infoLabels["tmdb_id"], tipo=item.extra, idioma_busqueda='es')
        if tmdb_lang.result.get("title") and tmdb_lang.result["title"] != item.contentTitle:
            tmdb_lang = tmdb_lang.result["title"]
            itemlist.append(item.clone(action="busqueda", title=config.get_localized_string(70066) % tmdb_lang,
                                       contentTitle=tmdb_lang))

    if item.contentType == "tvshow" and ob_tmdb.result:
        itemlist.append(item.clone(action="info_seasons", text_color=color4,
                                   title=config.get_localized_string(70067) % item.infoLabels["number_of_seasons"]))
    if ob_tmdb.result:
        itemlist.append(item.clone(action="reparto", title=config.get_localized_string(70071), text_color=color4,
                                   infoLabels={'tmdb_id': item.infoLabels['tmdb_id'],
                                               'mediatype': item.contentType}))

    if config.is_xbmc():
        item.contextual = True
    trailer_url = scrapertools.find_single_match(data,
                                                 '<a href="(?:http://m.filmaffinity.com|)/%s/movieTrailer\.php\?id=(\d+)"' % langf)
    if trailer_url:
        trailer_url = "http://www.filmaffinity.com/%s/evideos.php?movie_id=%s" % (langf, trailer_url)
    itemlist.append(item.clone(channel="trailertools", action="buscartrailer", title="Buscar Tráiler",
                               text_color=color5, filmaffinity=trailer_url))

    url_img = scrapertools.find_single_match(data,
                                             'href="(?:http://m.filmaffinity.com|)(/%s/movieposters[^"]+)">' % langf)
    images = {}
    if ob_tmdb.result and ob_tmdb.result.get("images"):
        images['tmdb'] = ob_tmdb.result["images"]
    if url_img:
        images['filmaffinity'] = {}
    if images:
        itemlist.append(item.clone(action="imagenes", title=config.get_localized_string(70316), text_color=color5, images=images,
                                   url=url_img, extra="menu"))
    try:
        if item.contentType == "movie" and item.infoLabels["year"] < 2014:
            post_url = "https://theost.com/search/custom/?key=%s&year=%s&country=0&genre=0" % (
            item.infoLabels['originaltitle'].replace(" ", "+"), item.infoLabels["year"])
            url = "https://nl.hideproxy.me/includes/process.php?action=update"
            post = "u=%s&proxy_formdata_server=nl&allowCookies=1&encodeURL=1&encodePage=0&stripObjects=0&stripJS=0&go=" % urllib.quote(
                post_url)
            while True:
                response = httptools.downloadpage(url, post=post, follow_redirects=False)
                if response.headers.get("location"):
                    url = response.headers["location"]
                    post = ""
                else:
                    data_music = response.data
                    break

            url_album = scrapertools.find_single_match(data_music, 'album(?:s|) on request.*?href="([^"]+)"')
            if url_album:
                url_album = "https://nl.hideproxy.me" + url_album
                itemlist.append(
                    item.clone(action="musica_movie", title=config.get_localized_string(70317), url=url_album,
                               text_color=color5))
    except:
        pass

    token_auth = config.get_setting("token_trakt", "trakt")
    if token_auth and ob_tmdb.result:
        itemlist.append(item.clone(title=config.get_localized_string(70323), action="menu_trakt"))
    # Acciones si se configura cuenta en FA (Votar y añadir/quitar en listas)
    mivoto = scrapertools.find_single_match(data, 'bg-my-rating.*?>\s*(\d+)')
    itk = scrapertools.find_single_match(data, 'data-itk="([^"]+)"')
    folder = not config.is_xbmc()
    if mivoto:
        item.infoLabels["userrating"] = int(mivoto)
        new_item = item.clone(action="votar_fa", title=config.get_localized_string(70324) % mivoto,
                              itk=itk, voto=int(mivoto), folder=folder)
        new_item.infoLabels["duration"] = ""
        itemlist.append(new_item)
    else:
        if itk:
            new_item = item.clone(action="votar_fa", title=config.get_localized_string(70325) % title, itk=itk, accion="votar",
                                  folder=folder)
            new_item.infoLabels["duration"] = ""
            itemlist.append(new_item)

    if itk:
        itk = scrapertools.find_single_match(data, 'var itk="([^"]+)"')
        new_item = item.clone(action="acciones_fa", accion="lista_movie", itk=itk,
                              title=config.get_localized_string(70326))
        new_item.infoLabels["duration"] = ""
        itemlist.append(new_item)

    # Si pertenece a una saga/colección
    if ob_tmdb.result:
        itemlist.append(item.clone(title="", action="", infoLabels={}))
        if ob_tmdb.result.get("belongs_to_collection"):
            new_item = item.clone(infoLabels={'mediatype': item.contentType}, action="listado_tmdb", text_color=color5)
            saga = ob_tmdb.result["belongs_to_collection"]
            new_item.infoLabels["tmdb_id"] = saga["id"]
            if saga["poster_path"]:
                new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + saga["poster_path"]
            if saga["backdrop_path"]:
                new_item.fanart = 'http://image.tmdb.org/t/p/original' + saga["backdrop_path"]
            new_item.search = {'url': 'collection/%s' % saga['id'], 'language': langt}
            new_item.title = config.get_localized_string(70327) % saga["name"]
            itemlist.append(new_item)

        itemlist.append(item.clone(title=config.get_localized_string(70328) % title.capitalize(), action="listado_tmdb",
                                   search={'url': '%s/%s/similar' % (item.extra, item.infoLabels['tmdb_id']),
                                           'language': langt, 'page': 1}, infoLabels={'mediatype': item.contentType},
                                   text_color=color2))
        itemlist.append(
            item.clone(title=config.get_localized_string(70315), action="listado_tmdb", infoLabels={'mediatype': item.contentType},
                       search={'url': '%s/%s/recommendations' % (item.extra, item.infoLabels['tmdb_id']),
                               'language': langt, 'page': 1}, text_color=color2))

    return itemlist


def filtro_fa(item):
    logger.info()

    from datetime import datetime
    list_controls = []
    valores = {}

    dict_values = None
    # Se utilizan los valores por defecto/guardados
    valores_guardados = config.get_setting("filtro_defecto_filmaf_" + item.extra, item.channel)
    if valores_guardados:
        dict_values = valores_guardados

    list_controls.append({'id': 'yearsdesde', 'label': config.get_localized_string(70452), 'enabled': True,
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls.append({'id': 'yearshasta', 'label': config.get_localized_string(70453), 'enabled': True,
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[0]['lvalues'] = []
    list_controls[1]['lvalues'] = []
    valores['years'] = []
    year = datetime.now().year
    for i in range(1900, year + 1):
        list_controls[0]['lvalues'].append(str(i))
        list_controls[1]['lvalues'].append(str(i))
        valores['years'].append(str(i))
    list_controls[0]['lvalues'].append(config.get_localized_string(70450))
    list_controls[1]['lvalues'].append(config.get_localized_string(70450))
    valores['years'].append('')

    data = httptools.downloadpage("http://m.filmaffinity.com/%s/topgen.php" % langf).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)
    if item.contentType == "movie":
        try:
            bloque = scrapertools.find_single_match(data, 'name="genre">.*?</option>(.*?)</select>')
            matches = scrapertools.find_multiple_matches(bloque, '<option value="([^"]+)">([^<]+)</option>')
            if matches:
                list_controls.append({'id': 'genero', 'label': config.get_localized_string(70467), 'enabled': True,
                                      'type': 'list', 'default': -1, 'visible': True})
                list_controls[2]['lvalues'] = []
                list_controls[2]['lvalues'].append("Todos")
                valores['genero'] = []
                valores['genero'].append('')
                for valor, titulo in matches:
                    if valor == "TV_SE":
                        continue
                    list_controls[2]['lvalues'].insert(0, titulo)
                    valores['genero'].insert(0, valor)

        except:
            pass

    try:
        bloque = scrapertools.find_single_match(data, 'name="country">.*?</option>(.*?)</select>')
        matches = scrapertools.find_multiple_matches(bloque, '<option value="([^"]+)"\s*>([^<]+)</option>')
        if matches:
            list_controls.append({'id': 'pais', 'label': config.get_localized_string(70466), 'enabled': True,
                                  'type': 'list', 'default': -1, 'visible': True})
            list_controls[-1]['lvalues'] = []
            list_controls[-1]['lvalues'].append('Todos')
            valores['pais'] = []
            valores['pais'].append('')
            for valor, titulo in matches:
                list_controls[-1]['lvalues'].insert(0, titulo)
                valores['pais'].insert(0, valor)
    except:
        pass

    list_controls.append({'id': 'espacio', 'label': '', 'enabled': False,
                          'type': 'label', 'default': None, 'visible': True})
    list_controls.append({'id': 'save', 'label': config.get_localized_string(70464), 'enabled': True,
                          'type': 'bool', 'default': False, 'visible': True})

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70320), item=item, callback='filtrado_fa')


def filtrado_fa(item, values):
    values_copy = values.copy()
    # Guarda el filtro para que sea el que se cargue por defecto
    if "save" in values and values["save"]:
        values_copy.pop("save")
        config.set_setting("filtro_defecto_filmaf_" + item.extra, values_copy, item.channel)

    yeard = item.valores["years"][values["yearsdesde"]]
    yearh = item.valores["years"][values["yearshasta"]]
    pais = item.valores["pais"][values["pais"]]
    if item.contentType == "movie":
        genero = item.valores["genero"][values["genero"]]
    else:
        genero = "TV_SE"

    item.url = 'http://m.filmaffinity.com/%s/topgen.php?genre=%s&country=%s&fromyear=%s&toyear=%s&nodoc=1' \
               % (langf, genero, pais, yeard, yearh)
    if item.contentType == "movie":
        item.url += "&notvse=1"
    item.action = "listado_fa"

    return listado_fa(item)


def login_fa():
    logger.info()

    try:
        user = config.get_setting("usuariofa", "tvmoviedb")
        password = config.get_setting("passfa", "tvmoviedb")
        userid = config.get_setting("userid", "tvmoviedb")
        if user == "" or password == "":
            return False, config.get_localized_string(70329)
        data = httptools.downloadpage("http://m.filmaffinity.com/%s" % langf).data
        if "modal-menu-user" in data and userid:
            return True, ""

        post = "postback=1&rp=&username=%s&password=%s&rememberme=on" % (user, password)
        data = httptools.downloadpage("https://m.filmaffinity.com/%s/account.ajax.php?action=login" % langf, post=post).data

        if "Invalid username" in data:
            logger.error("Error en el login")
            return False, config.get_localized_string(70330)
        else:
            post = "name=user-menu&url=http://m.filmaffinity.com/%s/main.php" % langf
            data = httptools.downloadpage("http://m.filmaffinity.com/%s/tpl.ajax.php?action=getTemplate" % langf,
                                          post=post).data
            userid = scrapertools.find_single_match(data, 'id-user=(\d+)')
            if userid:
                config.set_setting("userid", userid, "tvmoviedb")
            logger.info("Login correcto")
            return True, ""
    except:
        import traceback
        logger.error(traceback.format_exc())
        return False, config.get_localized_string(70331)


def cuenta_fa(item):
    # Menú de cuenta filmaffinity
    itemlist = []
    login, message = login_fa()
    if not login:
        itemlist.append(item.clone(action="", title=message, text_color=color4))
    else:
        userid = config.get_setting("userid", "tvmoviedb")
        itemlist.append(item.clone(action="acciones_fa", title=config.get_localized_string(70332), text_color=color5, accion="votos",
                                   url="http://m.filmaffinity.com/%s/user_ratings.php?id-user=%s" % (langf, userid)))
        itemlist.append(item.clone(action="acciones_fa", title=config.get_localized_string(70057), text_color=color5, accion="listas",
                                   url="http://m.filmaffinity.com/%s/mylists.php" % langf))

    return itemlist


def acciones_fa(item):
    # Acciones cuenta filmaffinity, votar, ver listas o añadir/quitar de lista
    itemlist = []

    if item.accion == "votos" or item.accion == "lista":
        data = httptools.downloadpage(item.url).data
        data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
        data = re.sub(r"\s{2}", " ", data)
        bloques = scrapertools.find_multiple_matches(data,
                                                     'list-group-item(?:[^>]+>\s*<a| rip)(.*?</div>)\s*</div>\s*<div')
        for bloque in bloques:
            patron = 'href="([^"]+)".*?data-src="([^"]+)".*?mc-title.*?>([^<]+)' \
                     '<small>\((\d+)\)</small>.*?(?:<div class="avgrat-box in-block ">' \
                     '([^<]+)</div>\s*<small class="ratcount-box">(.*?)\s*<|</li>).*?'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            mivoto = scrapertools.find_single_match(bloque, 'bg-my-rating[^>]+>(?:\s*<strong>|)([^<]+)<')
            for url, thumb, title, year, rating, votos in matches:
                new_item = item.clone(action="detalles_fa", text_color=color1)
                if not url.startswith("http://m.filmaffinity"):
                    new_item.url = "http://m.filmaffinity.com" + url
                else:
                    new_item.url = url

                new_item.infoLabels["year"] = year
                rating = rating.replace(",", ".")
                new_item.infoLabels["rating"] = float(rating)
                new_item.infoLabels["votes"] = votos.replace(".", "")
                if mivoto.isdigit():
                    new_item.infoLabels["userrating"] = int(mivoto)
                new_item.thumbnail = thumb.replace("msmall", "large")
                if not new_item.thumbnail.startswith("http"):
                    new_item.thumbnail = "http://m.filmaffinity.com" + new_item.thumbnail

                if re.search(r'(?i)serie de tv|\(tv\)', title):
                    new_item.contentType = "tvshow"
                    new_item.extra = "tv"
                new_item.title = title.strip() + "  (%s) [COLOR %s]%s[/COLOR]/[COLOR %s]%s[/COLOR]" % (
                year, color6, rating, color4, mivoto)
                new_item.contentTitle = title.strip()
                itemlist.append(new_item)
    elif item.accion == "listas":
        orderby = config.get_setting("orderfa", "tvmoviedb")
        data = httptools.downloadpage(item.url).data
        data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
        data = re.sub(r"\s{2}", " ", data)
        patron = 'list-group-item rip.*?href="([^"]+)".*?<strong>([^<]+)</strong>.*?<em>([^<]+)</em>' \
                 '.*?(?:<div class="ls-imgs">(.*?)</a>|</a>)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, title, content, imgs in matches:
            new_item = item.clone(accion="lista", text_color=color1)
            if not url.startswith("http://m.filmaffinity.com"):
                new_item.url = "http://m.filmaffinity.com%s&orderby=%s" % (url, orderby)
            else:
                new_item.url = "%s&orderby=%s" % (url, orderby)
            new_item.title = title + "  [COLOR %s](%s)[/COLOR]" % (color6, content)
            if imgs:
                imagenes = scrapertools.find_multiple_matches(imgs, 'data-src="([^"]+)"')
                from random import randint
                random = randint(0, len(imagenes) - 1)
                new_item.thumbnail = imagenes[random].replace("msmall", "large")
            itemlist.append(new_item)
    elif item.accion == "lista_movie":
        movieid = item.url.rsplit("=", 1)[1]
        url = "http://m.filmaffinity.com/%s/edtmovielists.php?movie_id=%s" % (langf, movieid)
        data = httptools.downloadpage(url).data
        patron = 'data-list-id="([^"]+)"(.*?)<div class="in-block list-name"><strong>([^<]+)<'
        matches = scrapertools.find_multiple_matches(data, patron)
        for listid, chequeo, title in matches:
            new_item = item.clone(folder=not config.is_xbmc())
            new_item.infoLabels["duration"] = ""
            new_item.listid = listid
            if "checked" in chequeo:
                new_item.title = "[COLOR %s]%s[/COLOR] %s" % ("green", u"\u0474".encode('utf-8'), title)
                new_item.accion = "removeMovieFromList"
            else:
                new_item.title = "[COLOR %s]%s[/COLOR] %s" % (color4, u"\u04FE".encode('utf-8'), title)
                new_item.accion = "addMovieToList"
            itemlist.append(new_item)
        new_item = item.clone(action="newlist", title=config.get_localized_string(70333), text_color=color6)
        new_item.infoLabels["duration"] = ""
        itemlist.append(new_item)
    else:
        url = "http://filmaffinity.com/%s/movieslist.ajax.php" % langf
        movieid = item.url.rsplit("=", 1)[1]
        post = "action=%s&listId=%s&movieId=%s&itk=%s" % (item.accion, item.listid, movieid, item.itk)
        data = jsontools.load(httptools.downloadpage(url, post=post).data)
        if not item.folder:
            import xbmc
            return xbmc.executebuiltin("Container.Refresh")
        else:
            if data["result"] == 0:
                title = config.get_localized_string(70334)
            else:
                title = config.get_localized_string(70335)
            itemlist.append(item.clone(action="", title=title))

    return itemlist


def votar_fa(item):
    # Ventana para seleccionar el voto
    logger.info()

    list_controls = []
    valores = {}
    dict_values = None
    if item.voto:
        dict_values = {'voto': item.voto}
    list_controls.append({'id': 'voto', 'label': config.get_localized_string(70468), 'enabled': True,
                          'type': 'list', 'default': 0, 'visible': True})
    list_controls[0]['lvalues'] = ['No vista']
    valores['voto'] = ["-1"]
    for i in range(1, 11):
        list_controls[0]['lvalues'].append(str(i))
        valores['voto'].append(i)

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70336) % item.contentTitle, item=item,
                                               callback='callback_voto')


def callback_voto(item, values):
    item.voto = item.valores["voto"][values["voto"]]
    item.action = "acciones_fa"
    movieid = item.url.rsplit("=", 1)[1]
    post = "id=%s&rating=%s&itk=%s&action=rate" % (movieid, item.voto, item.itk)
    data = jsontools.load(httptools.downloadpage("http://filmaffinity.com/%s/ratingajax.php" % langf, post=post).data)

    if not item.folder:
        import xbmc
        return xbmc.executebuiltin("Container.Refresh")
    else:
        if data["result"] == 0:
            title = config.get_localized_string(70337)
        else:
            title = config.get_localized_string(70335)
        itemlist.append(item.clone(action="", title=title))
        return itemlist


def newlist(item):
    # Creación de nueva lista en filmaffinity
    itemlist = []
    if item.accion == "lista":
        location = httptools.downloadpage(item.url).headers["location"]
        data = httptools.downloadpage("http://m.filmaffinity.com" + location).data
        itemlist.append(item.clone(action="", title=config.get_localized_string(70338)))
    else:
        url = "http://m.filmaffinity.com/%s/addlist.php?rp=%s" % (langf, item.url)
        data = httptools.downloadpage(url).data
        data = re.sub(r"\n|\r|\t|&nbsp;|\s{2}", "", data)

        patron = 'data-list-id="[^"]+" href="([^"]+)"><[^>]+><div class="col-xs-10">' \
                 '([^<]+)</div><div[^>]+><div type="button" class="btn btn-primary">'
        matches = scrapertools.find_multiple_matches(data, patron)
        for scrapedurl, title in matches:
            scrapedurl = "http://m.filmaffinity.com" + scrapedurl
            itemlist.append(item.clone(title=title, url=scrapedurl, accion="lista"))

    return itemlist


##-------------------- LISTADOS DE IMAGENES ------------------------##
def imagenes(item):
    itemlist = []


    if item.extra == "menu":
        item.folder = not config.is_xbmc()
        if "tmdb" in item.images:
            itemlist.append(item.clone(title="Tmdb", text_color=color2, extra=""))
            itemlist.append(item.clone(title="Fanart.Tv", text_color=color2, extra=""))
        if "imdb" in item.images:
            itemlist.append(item.clone(title="Imdb", text_color=color2, extra=""))
        if "filmaffinity" in item.images:
            itemlist.append(item.clone(title="Filmaffinity", text_color=color2, extra=""))
        if "myanimelist" in item.images:
            data = httptools.downloadpage(item.url + "/pics", cookies=False).data
            images = scrapertools.find_multiple_matches(data,
                                                        '<div class="picSurround"><a href="([^"]+)" title="([^"]+)"')
            if images:
                for thumb, title in images:
                    item.images["myanimelist"].append([thumb, title])
                itemlist.append(item.clone(title="MyAnimeList", text_color=color2, extra=""))

        return itemlist

    if "Fanart" in item.title:
        try:
            item, resultado = fanartv(item)
        except:
            resultado = None

        if not resultado:
            itemlist.append(item.clone(title=config.get_localized_string(70338), action=""))
            return itemlist
    elif "Filmaffinity" in item.title:
        try:
            url = "http://m.filmaffinity.com" + item.url
            data = httptools.downloadpage(url).data
            matches = scrapertools.find_multiple_matches(data, 'data-src="([^"]+)" alt="[^-]+\s*([^"]+)"')
            if matches:
                item.images["filmaffinity"] = matches
            else:
                item.images.pop("filmaffinity", None)
        except:
            itemlist.append(item.clone(title=config.get_localized_string(70339), action=""))
            return itemlist
    elif "Imdb" in item.title:
        try:
            data = jsontools.load(httptools.downloadpage(item.images["imdb"]["url"], cookies=False).data)
            item.images["imdb"].pop("url")
            if data.get("allImages"):
                item.images["imdb"] = data["allImages"]
            else:
                item.images.pop("imdb", None)
        except:
            itemlist.append(item.clone(title=config.get_localized_string(70339), action=""))
            return itemlist

    if item.images:
        from channels import infoplus
        for key, value in item.images.iteritems():
            if key == "tmdb" and "Tmdb" in item.title:
                if item.folder:
                    for tipo, child in value.iteritems():
                        for i, imagen in enumerate(child):
                            thumb = 'http://image.tmdb.org/t/p/w500' + imagen["file_path"]
                            fanart = 'http://image.tmdb.org/t/p/original' + imagen["file_path"]
                            title = "   %s %s [%sx%s]" % (tipo.capitalize(), i + 1, imagen["width"], imagen["height"])
                            itemlist.append(Item(channel=item.channel, action="", thumbnail=thumb, fanart=fanart,
                                                 title=title, text_color=color1, infoLabels=item.infoLabels))
                else:
                    imagesWindow = infoplus.images(tmdb=value).doModal()

            elif key == "fanart.tv":
                if item.folder:
                    for tipo, child in value.iteritems():
                        for i, imagen in enumerate(child):
                            thumb = imagen["url"].replace("/fanart/", "/preview/")
                            fanart = imagen["url"]
                            title = "   %s %s [%s]" % (tipo.capitalize(), i + 1, imagen["lang"])
                            itemlist.append(Item(channel=item.channel, action="", thumbnail=thumb, fanart=fanart,
                                                 title=title, text_color=color1, infoLabels=item.infoLabels))
                else:
                    imagesWindow = infoplus.images(fanartv=value).doModal()

            elif key == "filmaffinity" and "Filmaffinity" in item.title:
                if item.folder:
                    for thumb, title in value:
                        thumb = thumb.replace("-s200", "-large")
                        itemlist.append(Item(channel=item.channel, action="", thumbnail=thumb, fanart=thumb,
                                             title=title, text_color=color1, infoLabels=item.infoLabels))
                else:
                    imagesWindow = infoplus.images(fa=value).doModal()

            elif key == "imdb" and "Imdb" in item.title:
                if item.folder:
                    for imagen in value:
                        thumb = imagen["msrc"]
                        fanart = imagen["src"]
                        title = imagen["altText"]
                        itemlist.append(
                            Item(channel=item.channel, action="", thumbnail=thumb, fanart=fanart, title=title,
                                 text_color=color1, infoLabels=item.infoLabels))
                else:
                    imagesWindow = infoplus.images(imdb=value).doModal()

            elif key == "myanimelist" and "MyAnimeList" in item.title:
                if item.folder:
                    for imagen, title in value:
                        itemlist.append(
                            Item(channel=item.channel, action="", thumbnail=imagen, fanart=imagen, title=title,
                                 text_color=color1, infoLabels=item.infoLabels))
                else:
                    imagesWindow = infoplus.images(mal=value).doModal()

    return itemlist


def fanartv(item):
    headers = [['Content-Type', 'application/json']]
    id_search = item.infoLabels['tmdb_id']
    if item.contentType == "tvshow" and id_search:
        search = {'url': 'tv/%s/external_ids' % item.infoLabels['tmdb_id'], 'language': langt}
        ob_tmdb = Tmdb(discover=search, idioma_busqueda=langt)
        id_search = ob_tmdb.result.get("tvdb_id")

    resultado = False
    if id_search:
        if item.contentType == "movie":
            url = "http://webservice.fanart.tv/v3/movies/%s?api_key=cab16e262d72fea6a6843d679aa10300" \
                  % item.infoLabels['tmdb_id']
        else:
            url = "http://webservice.fanart.tv/v3/tv/%s?api_key=cab16e262d72fea6a6843d679aa10300" % id_search
        #data = jsontools.load(httptools.downloadpage(url, headers=headers, replace_headers=True).data)
        data = jsontools.load(httptools.downloadpage(url, headers=headers).data)
        if data and not "error message" in data:
            item.images['fanart.tv'] = {}
            for key, value in data.items():
                if key not in ["name", "tmdb_id", "imdb_id", "thetvdb_id"]:
                    item.images['fanart.tv'][key] = value
                    resultado = True

    return item, resultado


##-------------------- SECCION TRAKT.TV ------------------------##
def auth_trakt(item):
    return trakt_tools.auth_trakt()


def menu_trakt(item):
    # Menú con acciones de cuenta trakt (vistas, watchlist, coleccion)
    itemlist = []
    token_auth = config.get_setting("token_trakt", "trakt")
    tipo = item.extra.replace("tv", "show") + "s"
    title = item.contentType.replace("movie", config.get_localized_string(70283)).replace("tvshow", "serie")
    try:
        result = acciones_trakt(item.clone(url="sync/watched/%s" % tipo))
        post = {tipo: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if '"tmdb":%s' % item.infoLabels["tmdb_id"] in result:
            itemlist.append(item.clone(title=config.get_localized_string(70341) % title, action="acciones_trakt",
                                       url="sync/history/remove", post=post))
        else:
            itemlist.append(item.clone(title=config.get_localized_string(70342) % title, action="acciones_trakt",
                                       url="sync/history", post=post))
    except:
        pass

    try:
        result = acciones_trakt(item.clone(url="sync/watchlist/%s" % tipo))
        post = {tipo: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if '"tmdb":%s' % item.infoLabels["tmdb_id"] in result:
            itemlist.append(item.clone(title=config.get_localized_string(70343) % title, action="acciones_trakt",
                                       url="sync/watchlist/remove", post=post))
        else:
            itemlist.append(item.clone(title=config.get_localized_string(70344) % title, action="acciones_trakt",
                                       url="sync/watchlist", post=post))
    except:
        pass

    try:
        result = acciones_trakt(item.clone(url="sync/collection/%s" % tipo))
        post = {tipo: [{"ids": {"tmdb": item.infoLabels["tmdb_id"]}}]}
        if '"tmdb":%s' % item.infoLabels["tmdb_id"] in result:
            itemlist.append(item.clone(title=config.get_localized_string(70345) % title, action="acciones_trakt",
                                       url="sync/collection/remove", post=post))
        else:
            itemlist.append(item.clone(title=config.get_localized_string(70346) % title, action="acciones_trakt",
                                       url="sync/collection", post=post))
    except:
        pass

    return itemlist


def acciones_trakt(item):
    token_auth = config.get_setting("token_trakt", "trakt")
    itemlist = []
    item.text_color = color1

    item.contentType = item.extra.replace("show", "tvshow")

    client_id = "c40ba210716aee87f6a9ddcafafc56246909e5377b623b72c15909024448e89d"
    headers = [['Content-Type', 'application/json'], ['trakt-api-key', client_id],
               ['trakt-api-version', '2']]
    if token_auth:
        headers.append(['Authorization', "Bearer %s" % token_auth])

    post = None
    if item.post:
        post = jsontools.dump(item.post)

    url = "http://api-v2launch.trakt.tv/%s" % item.url
    #data = httptools.downloadpage(url, post, headers=headers, replace_headers=True)
    data = httptools.downloadpage(url, post=post, headers=headers)
    if data.code == "401":
        trakt_tools.token_trakt(item.clone(extra="renew"))
        token_auth = config.get_setting("token_trakt", "trakt")
        headers[3][1] = "Bearer %s" % token_auth
        #data = httptools.downloadpage(url, post, headers=headers, replace_headers=True)
        data = httptools.downloadpage(url, post=post, headers=headers)

    data = data.data
    if data and "sync" in item.url:
        if not item.post:
            return data
        else:
            data = jsontools.load(data)
            if "not_found" in data:
                return platformtools.dialog_notification("Trakt", config.get_localized_string(70347))
            else:
                return platformtools.dialog_notification("Trakt", config.get_localized_string(70348))
    elif data and "recommendations" in item.url:
        data = jsontools.load(data)
        ratings = []
        try:
            for i, entry in enumerate(data):
                if i <= item.pagina:
                    continue
                try:
                    entry = entry[item.extra]
                except:
                    pass
                new_item = item.clone(action="detalles")
                new_item.title = entry["title"] + "  (%s)" % entry["year"]
                new_item.infoLabels["tmdb_id"] = entry["ids"]["tmdb"]
                try:
                    ratings.append(entry["rating"])
                except:
                    ratings.append(0.0)
                itemlist.append(new_item)
                if i == item.pagina + 20:
                    itemlist.append(item.clone(title=config.get_localized_string(70065), text_color="", pagina=item.pagina + 20))
                    break

            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist[:-1], True)
            for i, new_item in enumerate(itemlist[:-1]):
                if new_item.infoLabels["title"]:
                    new_item.title = new_item.infoLabels["title"] + "  (%s)" % new_item.infoLabels["year"]
                if ratings[i]:
                    new_item.title += "  [COLOR %s]Trakt:%.2f[/COLOR]/[COLOR %s]Tmdb:%.2f[/COLOR]" \
                                      % (color6, ratings[i], color4, new_item.infoLabels["rating"])
        except:
            pass

    elif data and not item.url.endswith("lists"):
        data = jsontools.load(data)
        if data and "page=1" in item.url and item.order:
            valores = {'rank': config.get_localized_string(70003), 'added': config.get_localized_string(70469), 'title': config.get_localized_string(60320), 'released': config.get_localized_string(70470),
                       'runtime': config.get_localized_string(70471), 'popularity': config.get_localized_string(70472), 'percentage': config.get_localized_string(70473),
                       'votes': config.get_localized_string(70474), 'asc': config.get_localized_string(70475), 'desc': config.get_localized_string(70476)}
            orden = valores[item.order] + " " + valores[item.how]
            # itemlist.append(item.clone(title=config.get_localized_string(70349) % orden, action="order_list",
            #                            text_color=color4))
        ratings = []
        try:
            # if item.order:
            #     if item.how == "asc":
            #         reverse = False
            #     else:
            #         reverse = True
            #     if item.order == "rank" or item.order == "added":
            #         data = sorted(data, key=lambda x: x[item.order.replace("added", "last_collected_at")], reverse=reverse)
            #     else:
            #         order = item.order.replace("popularity", "votes").replace("percentage", "rating")
            #         data = sorted(data, key=lambda x: x[x['type']].get(order, 0), reverse=reverse)

            for entry in data:
                try:
                    entry = entry[item.extra]
                except:
                    pass
                new_item = item.clone(action="detalles")
                new_item.title = entry["title"] + "  (%s)" % entry["year"]
                new_item.infoLabels["tmdb_id"] = entry["ids"]["tmdb"]
                try:
                    ratings.append(entry["rating"])
                except:
                    ratings.append("")
                itemlist.append(new_item)

            from core import tmdb
            if "page=1" in item.url and item.order:
                tmdb.set_infoLabels_itemlist(itemlist[1:], True)
                for i, new_item in enumerate(itemlist[1:]):
                    if new_item.infoLabels["title"]:
                        new_item.title = new_item.infoLabels["title"] + "  (%s)" % new_item.infoLabels["year"]
                    if ratings[i]:
                        new_item.title += "  [COLOR %s]Trakt:%.2f[/COLOR]/[COLOR %s]Tmdb:%.2f[/COLOR]" \
                                          % (color6, ratings[i], color4, new_item.infoLabels["rating"])
            else:
                tmdb.set_infoLabels_itemlist(itemlist, True)
                for i, new_item in enumerate(itemlist):
                    if new_item.infoLabels["title"]:
                        new_item.title = new_item.infoLabels["title"] + "  (%s)" % new_item.infoLabels["year"]
                    if ratings[i]:
                        new_item.title += "  [COLOR %s]Trakt:%.2f[/COLOR]/[COLOR %s]Tmdb:%.2f[/COLOR]" \
                                          % (color6, ratings[i], color4, new_item.infoLabels["rating"])
        except:
            import traceback
            logger.error(traceback.format_exc())

        if "page" in item.url and len(itemlist) == 20:
            page = scrapertools.find_single_match(item.url, 'page=(\d+)')
            page_new = int(page) + 1
            url = item.url.replace("page=" + page, "page=" + str(page_new))
            itemlist.append(item.clone(title=config.get_localized_string(70065), text_color="", url=url))
    else:
        data = jsontools.load(data)
        for entry in data:
            new_item = item.clone()
            new_item.title = entry["name"] + "  [COLOR %s](%s)[/COLOR]" % (color6, entry["item_count"])
            new_item.infoLabels["plot"] = entry.get("description")
            new_item.url = "users/me/lists/%s/items/?page=1&limit=20&extended=full" % entry["ids"]["trakt"]
            new_item.order = entry.get("sort_by")
            new_item.how = entry.get("sort_how")
            itemlist.append(new_item)

    return itemlist


def order_list(item):
    logger.info()

    list_controls = []
    valores1 = ['rating', 'added', 'title', 'released', 'runtime', 'popularity', 'percentage', 'votes']
    valores2 = ['asc', 'desc']

    dict_values = {'orderby': valores1.index(item.order), 'orderhow': valores2.index(item.how)}

    list_controls.append({'id': 'orderby', 'label': config.get_localized_string(70455), 'enabled': True,
                          'type': 'list', 'default': 0, 'visible': True})
    list_controls.append({'id': 'orderhow', 'label': 'De forma:', 'enabled': True,
                          'type': 'list', 'default': 0, 'visible': True})
    list_controls[0]['lvalues'] = ['rank', 'added', 'title', 'released', 'runtime', 'popularity', 'percentage', 'votes']
    list_controls[1]['lvalues'] = ['asc', 'desc']
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70320), item=item, callback='order_trakt')


def order_trakt(item, values):
    valores1 = ['rank', 'added', 'title', 'released', 'runtime', 'popularity', 'percentage', 'votes']
    valores2 = ['asc', 'desc']
    orderby = valores1[values["orderby"]]
    item.order = orderby
    orderhow = valores2[values["orderhow"]]
    item.how = orderhow

    item.action = "acciones_trakt"

    return acciones_trakt(item)


##-------------------- SECCION MYANIMELIST ------------------------##
def top_mal(item):
    # Para los menús principales de tops pelícuas/series/ovas
    itemlist = []
    item.text_color = color1
    data = httptools.downloadpage(item.url, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    patron = '<td class="title al va-t word-break">.*?href="([^"]+)".*?src="(.*?).jpg.*?' \
             '<div class="di-ib clearfix">.*?href.*?>([^<]+)<.*?<div class="information di-ib mt4">' \
             '(.*?)<br>.*?(\d{4}|-).*?<span class="text.*?>(.*?)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumb, title, info, year, rating in matches:
        new_item = item.clone(action="detalles_mal", url=url)
        info = info.strip()
        new_item.thumbnail = thumb.replace("r/50x70/", "") + "l.jpg"
        year = year.replace("-", "")
        if year:
            new_item.infoLabels["year"] = year
        new_item.title = title.strip()
        if not item.extra:
            new_item.title += "   %s" % info.replace("Movie (1 eps)", "Movie").replace("TV ", "")
            if "Movie (" in info or "Special (" in info:
                new_item.contentType = "movie"
                new_item.extra = "movie"
            else:
                new_item.contentType = "tvshow"
                new_item.extra = "tv"
                new_item.show = title.strip()
        else:
            new_item.title += "   (%s" % info.split("(", 1)[1]
        if not year in title and year:
            new_item.title += " [%s]" % year
        if rating != "N/A":
            new_item.infoLabels["rating"] = float(rating)
            new_item.title += "  [COLOR %s]%s[/COLOR]" % (color6, rating)
        new_item.contentTitle = title.strip()
        itemlist.append(new_item)

    next_page = scrapertools.find_single_match(data, 'limit=(\d+)" class="link-blue-box next">')
    if next_page:
        next_page = item.url.rsplit("=", 1)[0] + "=%s" % next_page
        itemlist.append(item.clone(title=config.get_localized_string(70065), url=next_page, text_color=""))

    return itemlist


def detalles_mal(item):
    itemlist = []

    cookie_session = get_cookie_value()
    header_mal = {'Cookie': '%s search_sort_anime=score; search_view=tile; is_logged_in=1' % cookie_session}
    data = httptools.downloadpage(item.url, headers=header_mal, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    item.contentTitle = item.contentTitle.replace("(TV)", "").replace("(Movie)", "")
    item.fanart = default_fan
    item.infoLabels["plot"] = ""

    title_mal = item.contentTitle
    if not item.extra:
        extra = scrapertools.find_single_match(data, 'Type:</span>.*?>([^<]+)</a>').lower()
        item.tipo = extra
        if extra == "movie" or extra == "special":
            item.extra = "movie"
            item.contentType = "movie"
        else:
            item.extra = "tv"
            item.contentType = "tvshow"

    if item.infoLabels['rating'] != "0.0":
        rating = item.infoLabels['rating']
    else:
        rating = scrapertools.find_single_match(data, '<span itemprop="ratingValue">(\d.\d+)</span>')

    if not item.infoLabels["year"]:
        item.infoLabels["year"] = scrapertools.find_single_match(data, '>Aired:</span>.*?(\d{4})')

    eng_title = scrapertools.find_single_match(data, 'English:</span> ([^<]+)</div>').strip()
    item_tmdb = item.clone()

    if item.contentType == "movie":
        ob_tmdb = Tmdb(texto_buscado=item_tmdb.contentTitle, year=item_tmdb.infoLabels['year'], tipo=item_tmdb.extra,
                       idioma_busqueda=langt)
        if not ob_tmdb.result and eng_title:
            ob_tmdb = Tmdb(texto_buscado=eng_title, year=item_tmdb.infoLabels['year'],
                           tipo=item_tmdb.extra, idioma_busqueda=langt)
        if not ob_tmdb.result and ("Special (" in item.title or item.tipo == "special"):
            item_tmdb.extra = "tv"
            search = {'url': 'search/tv', 'language': langt, 'query': item_tmdb.contentTitle,
                      'first_air_date': item_tmdb.infoLabels["year"]}
            ob_tmdb = Tmdb(discover=search, tipo=item_tmdb.extra, idioma_busqueda=langt)
    else:
        search = {'url': 'search/tv', 'language': langt, 'query': eng_title,
                  'first_air_date': item_tmdb.infoLabels["year"]}
        ob_tmdb = Tmdb(discover=search, tipo=item_tmdb.extra, idioma_busqueda=langt)
        if not ob_tmdb.result and eng_title:
            search['query'] = eng_title
            ob_tmdb = Tmdb(discover=search, tipo=item_tmdb.extra, idioma_busqueda=langt)
        if not ob_tmdb.result and ("OVA (" in item.title or item.tipo == "ova"):
            item_tmdb.extra = "movie"
            ob_tmdb = Tmdb(texto_buscado=item_tmdb.contentTitle, tipo=item_tmdb.extra, idioma_busqueda=langt,
                           year=item_tmdb.infoLabels['year'])

    if ob_tmdb.result:
        ob_tmdb = Tmdb(id_Tmdb=ob_tmdb.get_id(), tipo=item_tmdb.extra, idioma_busqueda=langt)
        item.infoLabels = ob_tmdb.get_infoLabels(item.infoLabels)

    # Se concatena sinopsis myanimelist con la de tmdb si la hubiese
    plot = scrapertools.find_single_match(data, '<span itemprop="description">(.*?)</span>')
    plot = plot.replace("<br />", "\n").replace("<i>", "[I]").replace("</i>", "[/I]")
    plot = scrapertools.decodeHtmlentities(plot)
    if plot and (item.infoLabels['plot'] and item.infoLabels['plot'] != plot):
        item.infoLabels['plot'] += " (TMDB)\n\n" + plot + " (MYANIMELIST)"
    elif plot and not item.infoLabels['plot']:
        item.infoLabels['plot'] = plot

    if not item.infoLabels['duration']:
        try:
            horas, min1, min2 = scrapertools.find_single_match(data,
                                                               'Duration:</span>\s*(?:(\d+) hr\. (\d+) min|(\d+) min)')
            if horas:
                horas = int(horas) * 360
            else:
                horas = 0
            if not min1:
                min1 = min2
            item.infoLabels['duration'] = horas + (int(min1) * 60)
        except:
            pass

    # Se sobreescribe la info de myanimelist sobre la de tmdb
    generos = scrapertools.find_single_match(data, 'Genres:</span>(.*?)</div>')
    if generos:
        item.infoLabels['genre'] = scrapertools.htmlclean(generos)

    item.infoLabels['rating'] = float(rating)
    votos = scrapertools.find_single_match(data, '<span itemprop="ratingCount">([^<]+)<')
    item.infoLabels['votes'] = votos.replace(",", "")

    if item.infoLabels['fanart']:
        item.fanart = item.infoLabels['fanart']
    if item.infoLabels['thumbnail']:
        item.thumbnail = item.infoLabels['thumbnail']
    if not item.thumbnail:
        item.thumbnail = scrapertools.find_single_match(data, '/pics">.*?<img src="([^"]+)"').replace(".jpg", "l.jpg")

    itemlist.append(
        item.clone(action="busqueda", title=config.get_localized_string(70350) % title_mal, contentTitle=title_mal,
                   extra=item.extra.replace("tv", "anime")))
    if item.infoLabels["title"] and title_mal != item.infoLabels["title"]:
        itemlist.append(item.clone(action="busqueda", contentTitle=item.infoLabels["title"],
                                   title=config.get_localized_string(70351) % item.infoLabels["title"]))

    if eng_title and item.contentTitle != eng_title and title_mal != eng_title:
        itemlist.append(item.clone(action="busqueda", contentTitle=eng_title,
                                   title=config.get_localized_string(70352) % eng_title))

    if item_tmdb.extra == "tv" and ob_tmdb.result:
        itemlist.append(item.clone(action="info_seasons", text_color=color4,
                                   title=config.get_localized_string(70067) % item.infoLabels["number_of_seasons"]))

    itemlist.append(item.clone(action="videos_mal", title=config.get_localized_string(70353), text_color=color5,
                               url=item.url + "/video"))

    # Opción para ver la info de personajes y dobladores/equipo de rodaje
    if not "No characters or voice actors" in data and not "No staff for this anime" in data:
        itemlist.append(item.clone(action="staff_mal", title=config.get_localized_string(70354), text_color=color2,
                                   url=item.url + "/characters"))
    if config.is_xbmc():
        item.contextual = True
    itemlist.append(item.clone(channel="trailertools", action="buscartrailer", title=config.get_localized_string(30162),
                               text_color=color5))

    images = {}
    if ob_tmdb.result and ob_tmdb.result.get("images"):
        images['tmdb'] = ob_tmdb.result["images"]
    images['myanimelist'] = []
    itemlist.append(item.clone(action="imagenes", title=config.get_localized_string(70316), text_color=color5, images=images,
                               extra="menu"))

    try:
        title_search = re.sub(r'[^0-9A-z]+', ' ', title_mal)
        post = "busqueda=%s&button=Search" % urllib.quote(title_search)
        data_music = httptools.downloadpage("http://www.freeanimemusic.org/song_search.php", post=post).data
        if not "NO MATCHES IN YOUR SEARCH" in data_music:
            itemlist.append(
                item.clone(action="musica_anime", title=config.get_localized_string(70317), text_color=color5,
                           post=post))
    except:
        pass

    score = scrapertools.find_single_match(data, 'id="myinfo_score".*?selected" value="(\d+)"')
    if score != "0":
        score = "[COLOR %s]Puntuado:%s" % (color4, score)
    else:
        score = "Votar"
    if item.login and "Add to My List</span>" in data and config.is_xbmc():
        itemlist.append(
            item.clone(title=config.get_localized_string(70321) % score, action="menu_mal", contentTitle=title_mal))
    elif item.login and config.is_xbmc():
        status = {'1': config.get_localized_string(70479), '2': config.get_localized_string(70480), '3': config.get_localized_string(70384), '4': config.get_localized_string(70385),
                  '6': config.get_localized_string(70481)}
        estado = scrapertools.find_single_match(data, 'myinfo_updateInfo".*?option selected="selected" value="(\d+)"')
        try:
            estado = status[estado]
            itemlist.append(
                item.clone(title=config.get_localized_string(70322) % (color6, estado, score),
                           action="menu_mal",
                           contentTitle=title_mal))
        except:
            pass

    token_auth = config.get_setting("token_trakt", "trakt")
    if token_auth and ob_tmdb.result:
        itemlist.append(item.clone(title=config.get_localized_string(70323), action="menu_trakt"))

    # Se listan precuelas, secuelas y series alternativas
    prequel = scrapertools.find_single_match(data, 'Prequel:</td>(.*?)</td>')
    if prequel:
        matches = scrapertools.find_multiple_matches(prequel, 'href="([^"]+)">(.*?)</a>')
        for url, title in matches:
            new_item = item.clone(infoLabels={'mediatype': item.contentType}, extra="", fanart=default_fan,
                                  thumbnail="")
            new_item.title = config.get_localized_string(70355) % title
            new_item.contentTitle = title
            new_item.url = "https://myanimelist.net%s" % url
            itemlist.append(new_item)

    sequel = scrapertools.find_single_match(data, 'Sequel:</td>(.*?)</td>')
    if sequel:
        matches = scrapertools.find_multiple_matches(sequel, 'href="([^"]+)">(.*?)</a>')
        for url, title in matches:
            new_item = item.clone(infoLabels={'mediatype': item.contentType}, extra="", fanart=default_fan,
                                  thumbnail="")
            new_item.title = config.get_localized_string(70356) % title
            new_item.contentTitle = title
            new_item.url = "https://myanimelist.net%s" % url
            itemlist.append(new_item)

    alt_version = scrapertools.find_single_match(data, 'Alternative version:</td>(.*?)</td>')
    if alt_version:
        matches = scrapertools.find_multiple_matches(alt_version, 'href="([^"]+)">(.*?)</a>')
        for url, title in matches:
            new_item = item.clone(infoLabels={'mediatype': item.contentType}, extra="", fanart=default_fan,
                                  thumbnail="")
            new_item.title = config.get_localized_string(70357) % title
            new_item.contentTitle = title
            new_item.url = "https://myanimelist.net%s" % url
            itemlist.append(new_item)

    if ob_tmdb.result:
        itemlist.append(item.clone(title="", action="", infoLabels={}))
        if ob_tmdb.result.get("belongs_to_collection"):
            new_item = item.clone(infoLabels={'mediatype': item.contentType}, action="listado_tmdb", text_color=color5)
            saga = ob_tmdb.result["belongs_to_collection"]
            new_item.infoLabels["tmdb_id"] = saga["id"]
            if saga["poster_path"]:
                new_item.thumbnail = 'http://image.tmdb.org/t/p/original' + saga["poster_path"]
            if saga["backdrop_path"]:
                new_item.fanart = 'http://image.tmdb.org/t/p/original' + saga["backdrop_path"]
            new_item.search = {'url': 'collection/%s' % saga['id'], 'language': langt}
            new_item.title = "Es parte de: %s" % saga["name"]
            itemlist.append(new_item)

        itemlist.append(
            item.clone(title=config.get_localized_string(70358), action="listado_tmdb", infoLabels={'mediatype': item.contentType},
                       search={'url': '%s/%s/recommendations' % (item.extra, item.infoLabels['tmdb_id']),
                               'language': langt, 'page': 1}, text_color=color2))

    # Recomendaciones myanimelist y búsqueda de info en anidb (fansubs en español)
    itemlist.append(item.clone(title=config.get_localized_string(70359), action="reco_mal"))
    anidb_link = scrapertools.find_single_match(data,
                                                '<a href="(http://anidb.info/perl-bin/animedb.pl\?show=anime&amp;aid=\d+)')
    if anidb_link:
        anidb_link = anidb_link.replace("&amp;", "&") + "&showallag=1#grouplist"
        info_anidb(item, itemlist, anidb_link)

    return itemlist


def videos_mal(item):
    # Método para episodios en crunchyroll y trailer/promocionales
    itemlist = []

    data = httptools.downloadpage(item.url, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    if not "No episode video" in data and not "http://www.hulu.com/" in data:
        patron = '<a class="video-list di-ib po-r" href="([^"]+)".*?data-src="([^"]+)".*?' \
                 '<span class="title">([^<]+)<(.*?)<span class="episode-title" title="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, thumb, epi, info, title in matches:
            if "icon-pay" in info and "icon-banned-youtube" in thumb:
                continue
            url = "https://myanimelist.net%s" % url
            new_item = item.clone(url=url, thumbnail=thumb, action="play", text_color=color1)
            new_item.title = epi + " - " + title.strip()
            if "icon-pay" in info:
                new_item.title += "  [COLOR %s](Crunchyroll Premium)[/COLOR]" % color6
            if "icon-banned-youtube" in thumb:
                new_item.title += config.get_localized_string(70360) % color4
            itemlist.append(new_item)

        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="link-blue-box">More')
        if next_page:
            itemlist.append(item.clone(title=config.get_localized_string(70361), url=next_page, text_color=""))
    if itemlist:
        itemlist.insert(0, item.clone(title=config.get_localized_string(70362), action="", text_color=color3))

    patron = '<a class="iframe.*?href="(https://www.youtube.*?)\?.*?data-src="([^"]+)".*?<span class="title">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title=config.get_localized_string(70363), action="", text_color=color3))
        for url, thumb, title in matches:
            url = url.replace("embed/", "watch?v=")
            itemlist.append(
                item.clone(title=title, url=url, server="youtube", action="play", thumbnail=thumb, text_color=color1))

    return itemlist


def reco_mal(item):
    # Recomendaciones de myanimelist
    itemlist = []

    data = httptools.downloadpage(item.url + "/userrecs", cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)
    bloque = scrapertools.find_single_match(data,
                                            '<div class="anime-slide-block" id="anime_recommendation"(.*?)</ul></div>')
    patron = '<div class="picSurround"><a href="([^"]+)".*?data-src="([^"]+)".*?<strong>(.*?)</strong>.*?' \
             '<div class="spaceit_pad">(.*?)</div>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumb, title, plot in matches:
        new_item = item.clone(infoLabels={'mediatype': item.contentType}, action="detalles_mal", fanart=default_fan,
                              title=title, contentType="", extra="",
                              contentTitle=title)
        new_item.infoLabels["plot"] = scrapertools.htmlclean(plot)
        new_item.url = "https://myanimelist.net%s" % url
        new_item.thumbnail = thumb.replace("r/50x70/", "").replace(".jpg", "l.jpg")
        itemlist.append(new_item)

    return itemlist


def indices_mal(item):
    # Índices por temporadas y generos
    itemlist = []
    url_base = ""
    if "Temporadas" in item.title:
        data = httptools.downloadpage("https://myanimelist.net/anime/season/archive", cookies=False).data
        data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
        data = re.sub(r"\s{2}", " ", data)
        matches = scrapertools.find_multiple_matches(data, '<td>\s*<a href="([^"]+)">\s*(.*?)\s*</a>')
        for url, title in matches:
            year = title.rsplit(" ", 1)[1]
            thumbnail = item.thumbnail
            if int(year) >= 1968:
                thumbnail = url_base % year
            title = title.replace("Winter", config.get_localized_string(70364)).replace("Spring", config.get_localized_string(70365)) \
                .replace("Summer", config.get_localized_string(70366)).replace("Fall", config.get_localized_string(70367))
            itemlist.append(Item(channel=item.channel, action="season_mal", title=title, url=url,
                                 thumbnail=thumbnail, text_color=color1, info=True, fanart=thumbnail))
    else:
        data = httptools.downloadpage("https://myanimelist.net/anime.php", cookies=False).data
        data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
        data = re.sub(r"\s{2}", " ", data)
        bloque = scrapertools.find_single_match(data, 'Genres</div>(.*?)View More</a>')
        matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)" class="genre-name-link">(.*?)</a>')
        for url, title in matches:
            genero = title.split(" (", 1)[0]
            thumbnail = url_base % genero.lower().replace(" ", "%20")
            if genero in ["Hentai", "Yaoi", "Yuri"] and not adult_mal:
                continue
            url = "https://myanimelist.net%s" % url
            itemlist.append(Item(channel=item.channel, action="season_mal", title=title, url=url,
                                 thumbnail=thumbnail, fanart=thumbnail, text_color=color1))

    return itemlist


def season_mal(item):
    # Scraper para temporadas de anime
    itemlist = []

    cookie_session = get_cookie_value()
    header_mal = {'Cookie': '%s search_sort_anime=score; search_view=tile; is_logged_in=1' % cookie_session}
    data = httptools.downloadpage(item.url, headers=header_mal, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    if item.info:
        patron = '<div class="anime-header">([^<]+)</div>(.*?)</div>\s*</div></div></div>'
        bloques = scrapertools.find_multiple_matches(data, patron)
        for head_title, bloque in bloques:
            head_title = head_title.replace("(New)", config.get_localized_string(70369)).replace("(Continuing)", config.get_localized_string(70369))
            patron = '<a href="([^"]+)" class="link-title">(.*?)</a>.*?<span>(\? ep|\d+ ep).*?' \
                     '<div class="genres-inner js-genre-inner">(.*?)</div>.*?<div class="image".*?src="(.*?).jpg' \
                     '.*?<span class="preline">(.*?)</span>.*?<div class="info">\s*(.*?)\s*-.*?(\d{4}).*?' \
                     'title="Score">\s*(N/A|\d\.\d+)'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            if matches:
                itemlist.append(Item(channel=item.channel, action="", title=head_title, text_color=color3))
            for url, scrapedtitle, epis, generos, thumb, plot, tipo, year, score in matches:
                if ("Hentai" in generos or "Yaoi" in generos or "Yuri" in generos) and adult_mal:
                    continue
                scrapedtitle = scrapedtitle.replace("(TV)", "").replace("(Movie)", "")
                if tipo == "Movie":
                    title = scrapedtitle + "   (%s)" % year
                else:
                    title = scrapedtitle + "   %ss (%s)" % (epis, year)
                infoLabels = {}
                if score != "N/A":
                    title += "  [COLOR %s]%s[COLOR]" % (color6, score)
                    infoLabels["rating"] = float(score)
                infoLabels["plot"] = scrapertools.htmlclean(plot)
                infoLabels["year"] = year

                genres = scrapertools.find_multiple_matches(generos, 'title="([^"]+)"')
                infoLabels["genre"] = ", ".join(genres)
                tipo = tipo.lower()
                if tipo == "movie" or tipo == "special":
                    extra = "movie"
                    contentType = "movie"
                else:
                    extra = "tv"
                    contentType = "tvshow"
                thumb = thumb.replace("r/167x242/", "") + "l.jpg"
                itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, title=title,
                                     thumbnail=thumb, infoLabels=infoLabels, extra=extra, tipo=tipo,
                                     contentTitle=scrapedtitle, contentType=contentType, text_color=color1,
                                     fanart=default_fan))
    else:
        patron = '<a href="([^"]+)" class="link-title">(.*?)</a>.*?<span>(\? ep|\d+ ep).*?' \
                 '<div class="genres-inner js-genre-inner">(.*?)</div>.*?<div class="image".*?src="(.*?).jpg.*?' \
                 '<span class="preline">(.*?)</span>.*?<div class="info">\s*(.*?)\s*-.*?(\d{4}).*?' \
                 'title="Score">\s*(N/A|\d\.\d+)'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url, scrapedtitle, epis, generos, thumb, plot, tipo, year, score in matches:
            if ("Hentai" in generos or "Yaoi" in generos or "Yuri" in generos) and not adult_mal:
                continue
            scrapedtitle = scrapedtitle.replace("(TV)", "").replace("(Movie)", "")
            if tipo == "Movie":
                title = scrapedtitle + "   (%s)" % year
            else:
                title = scrapedtitle + "   %ss (%s)" % (epis, year)
            infoLabels = {}
            if score != "N/A":
                title += "  [COLOR %s]%s[COLOR]" % (color6, score)
                infoLabels["rating"] = float(score)
            infoLabels["plot"] = scrapertools.htmlclean(plot)
            infoLabels["year"] = year

            genres = scrapertools.find_multiple_matches(generos, 'title="([^"]+)"')
            infoLabels["genre"] = ", ".join(genres)
            tipo = tipo.lower()
            if tipo == "movie" or tipo == "special":
                extra = "movie"
                contentType = "movie"
            else:
                extra = "tv"
                contentType = "tvshow"
            thumb = thumb.replace("r/167x242/", "") + "l.jpg"
            itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, title=title,
                                 thumbnail=thumb, infoLabels=infoLabels, extra=extra, tipo=tipo,
                                 contentTitle=scrapedtitle, contentType=contentType, text_color=color1,
                                 fanart=default_fan))
        next_page = scrapertools.find_single_match(data, '<a class="link current" href.*?href="([^"]+)"')
        if next_page:
            itemlist.append(Item(channel=item.channel, action="season_mal", url=next_page, text_color="",
                                 title=config.get_localized_string(70065), thumbnail=item.thumbnail))

    return itemlist


def staff_mal(item):
    # Dobladores/Equipo de rodaje
    itemlist = []
    data = httptools.downloadpage(item.url, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)
    patron = '<a href="(/character[^"]+)".*?data-src="([^"]+)".*?href=.*?>([^<]+)<.*?<small>([^<]+)</small>' \
             '(.*?)</table>'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title=config.get_localized_string(70370), action="", text_color=color3))
        for url, thumb, nombre, rol, voces in matches:
            url = "https://myanimelist.net%s" % url
            rol = rol.replace("Main", "Principal").replace("Supporting", "Secundario")
            nombre = "   %s   [%s]" % (nombre, rol)
            thumb = thumb.replace("r/46x64/", "")
            itemlist.append(Item(channel=item.channel, action="detail_staff", url=url, text_color=color2,
                                 thumbnail=thumb, fanart=default_fan, title=nombre, extra="character"))
            patron_voces = '<a href="(/people[^"]+)">([^<]+)<.*?<small>([^<]+)</small>.*?data-src="([^"]+)"'
            voces_match = scrapertools.find_multiple_matches(voces, patron_voces)
            for vurl, vnombre, vidioma, vthumb in voces_match:
                vurl = "https://myanimelist.net%s" % vurl
                vnombre = "        %s   [%s]" % (vnombre, vidioma)
                vthumb = vthumb.replace("r/46x64/", "")
                itemlist.append(Item(channel=item.channel, action="detail_staff", url=vurl, text_color=color1,
                                     thumbnail=vthumb, fanart=default_fan, title=vnombre))
    bloque = scrapertools.find_single_match(data, '<a name="staff">(.*?)</table>')
    patron = '<a href="(/people[^"]+)".*?data-src="([^"]+)".*?href=.*?>([^<]+)<.*?<small>([^<]+)</small>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    if matches:
        itemlist.append(item.clone(title="Staff", action="", text_color=color3))
        for url, thumb, nombre, rol in matches:
            url = "https://myanimelist.net%s" % url
            nombre = "   %s   [%s]" % (nombre, rol)
            thumb = thumb.replace("r/46x64/", "")
            itemlist.append(Item(channel=item.channel, action="detail_staff", url=url, text_color=color1,
                                 thumbnail=thumb, fanart=default_fan, title=nombre))

    return itemlist


def detail_staff(item):
    itemlist = []
    data = httptools.downloadpage(item.url, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    if item.extra == "character" and not "No biography written" in data:
        bio = scrapertools.find_single_match(data,
                                             'itemprop="name">.*?<div class="normal_header".*?</div>(.*?)<div class="normal_header"')
        bio = bio.replace("<br />", "\n")
        bio = scrapertools.htmlclean(bio)
        if not "questionmark" in item.thumbnail:
            data_img = httptools.downloadpage(item.url + "/pictures", cookies=False).data
            matches = scrapertools.find_multiple_matches(data_img, 'rel="gallery-character"><img src="([^"]+)"')
            for i, thumb in enumerate(matches):
                title = "Imagen %s" % (i + 1)
                infoLabels = {'plot': bio}
                itemlist.append(
                    Item(channel=item.channel, action="", title=title, infoLabels=infoLabels, text_color=color1,
                         thumbnail=thumb))

        matches = scrapertools.find_multiple_matches(data,
                                                     '<a href="(/anime[^"]+)"><img src="([^"]+)".*?href.*?>(.*?)</a>')
        if matches:
            itemlist.append(Item(channel=item.channel, title="Animes donde aparece:", action="", text_color=color3))
            for url, thumb, title in matches:
                url = "https://myanimelist.net%s" % url
                thumb = thumb.replace("r/23x32/", "")
                itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, text_color=color1,
                                     thumbnail=thumb, fanart=default_fan, title=title, contentTitle=title))
    else:
        patron_bio = '<div class="js-sns-icon-container icon-block ">.*?<div class="spaceit_pad">(.*?)</td>'
        bio = scrapertools.find_single_match(data, patron_bio)
        bio = scrapertools.htmlclean(bio.replace("</div>", "\n"))
        infoLabels = {'plot': bio}
        if not "No voice acting roles" in data:
            itemlist.append(Item(channel=item.channel, title="Da voz a/en:", action="", text_color=color3,
                                 thumbnail=item.thumbnail, infoLabels=infoLabels))
            bloque = scrapertools.find_single_match(data, 'Voice Acting Roles</div>(.*?)</table>')
            patron = '<a href="(/anime[^"]+)"><img data-src="([^"]+)".*?href.*?>(.*?)</a>.*?href="(/character[^"]+)".*?' \
                     '>(.*?)</a>.*?data-src="([^"]+)"'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            for url, thumb, title, url_p, personaje, thumb_p in matches:
                url = "https://myanimelist.net%s" % url
                url_p = "https://myanimelist.net%s" % url_p
                thumb = thumb.replace("r/46x64/", "")
                thumb_p = thumb_p.replace("r/46x64/", "")
                itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, text_color=color2,
                                     thumbnail=thumb, fanart=default_fan, title=title, contentTitle=title))
                itemlist.append(Item(channel=item.channel, action="detail_staff", url=url_p, text_color=color1,
                                     thumbnail=thumb_p, fanart=default_fan, title="   %s" % personaje,
                                     extra="character"))

        if not "No staff positions" in data:
            itemlist.append(Item(channel=item.channel, title="Staff en animes:", action="", text_color=color3,
                                 thumbnail=item.thumbnail, infoLabels=infoLabels))
            bloque = scrapertools.find_single_match(data, 'Anime Staff Positions</div>(.*?)</table>')
            patron = '<a href="(/anime[^"]+)"><img data-src="([^"]+)".*?href.*?>(.*?)</a>.*?<small>(.*?)</div>'
            matches = scrapertools.find_multiple_matches(bloque, patron)
            for url, thumb, title, rol in matches:
                url = "https://myanimelist.net%s" % url
                thumb = thumb.replace("r/46x64/", "")
                rol = scrapertools.htmlclean(rol)
                titulo = "%s   [COLOR %s][%s][/COLOR]" % (title, color6, rol)
                itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, text_color=color2,
                                     thumbnail=thumb, fanart=default_fan, title=titulo, contentTitle=title))

    return itemlist


def busqueda_mal(item):
    # Scraper para búsquedas en myanimelist
    itemlist = []

    cookie_session = get_cookie_value()
    header_mal = {'Cookie': '%s search_sort_anime=score; search_view=tile; is_logged_in=1' % cookie_session}
    data = httptools.downloadpage(item.url, headers=header_mal, cookies=False).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    patron = '<a class="hoverinfo_trigger" href="([^"]+)".*?(?:data-src|src)="([^"]+)".*?' \
             '<div class="hoverinfo".*?href.*?><strong>([^<]+)<.*?<div class="pt4">(.*?)<' \
             '.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumb, titulo, plot, tipo, epis, rating, date in matches:
        infolabels = {"mediatype": "tvshow"}
        contentType = "tvshow"
        extra = "tv"
        titulo = titulo.strip()
        tipo = tipo.strip()
        rating = rating.strip()
        epis = epis.strip()
        infolabels["plot"] = scrapertools.htmlclean(plot.strip())
        thumb = thumb.replace("r/50x70/", "").replace(".jpg", "l.jpg")
        show = titulo
        contentitle = titulo
        title = titulo
        try:
            year = date.strip().rsplit("-", 1)[1]
            if year.isdigit():
                if int(year) < 30:
                    year = "20%s" % year
                else:
                    year = "19%s" % year
                infolabels["year"] = year
                if not year in title:
                    title += "  (%s)" % year
        except:
            import traceback
            logger.error(traceback.format_exc())

        if tipo == "Movie" or tipo == "OVA":
            infolabels["mediatype"] = "movie"
            contentType = "movie"
            extra = "movie"
            show = ""

        if epis and tipo != "Movie":
            title += "  %s eps" % epis
        if rating != "0.00" and rating != "N/A":
            infolabels["rating"] = float(rating)
            title += "  [COLOR %s]%s[/COLOR]" % (color6, rating)
        itemlist.append(Item(channel=item.channel, title=title, action="detalles_mal", url=url, show=show,
                             thumbnail=thumb, infoLabels=infolabels, contentTitle=contentitle, text_color=color1,
                             contentType=contentType, tipo=tipo.lower(), extra=extra))

    if not "&show=" in item.url:
        next_page = item.url + "&show=50"
    else:
        pagina = int(item.url.rsplit("=", 1)[1])
        next_page = item.url.replace("&show=%s" % str(pagina), "&show=%s" % str(pagina + 50))

    check_page = next_page.replace("https://myanimelist.net/anime.php", "")
    if check_page in data:
        itemlist.append(item.clone(title=config.get_localized_string(70065), url=next_page, text_color=""))
    else:
        check_page = check_page.replace("[", "%5B").replace("]", "%5D")
        if check_page in data:
            itemlist.append(item.clone(title=config.get_localized_string(70065), url=next_page, text_color=""))

    return itemlist


def info_anidb(item, itemlist, url):
    # Extrae info, puntuación y fansubs en anidb
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    infoLabels = {'mediatype': item.contentType}
    plot = scrapertools.find_single_match(data, 'itemprop="description">(.*?)</div>')
    infoLabels["plot"] = scrapertools.htmlclean(plot)

    generos = scrapertools.find_multiple_matches(data, '<div class="tag".*?<span class="tagname">(.*?)</span>')
    for i, genero in enumerate(generos):
        generos[i] = genero.capitalize()
    infoLabels["genre"] = ", ".join(generos)
    rating = scrapertools.find_single_match(data, 'itemprop="ratingValue">(.*?)</span>')
    try:
        infoLabels["rating"] = float(rating)
    except:
        pass
    infoLabels["votes"] = scrapertools.find_single_match(data, 'itemprop="ratingCount">(.*?)</span>')
    thumbnail = scrapertools.find_single_match(data, '<div class="image">.*?src="([^"]+)"')
    if infoLabels:
        title = config.get_localized_string(70376) % (color6, rating)
        if re.search(r'(?:subtitle|audio) | language: spanish"', data):
            title += config.get_localized_string(70377) % color3
        itemlist.append(Item(channel=item.channel, title=title, infoLabels=infoLabels, action="",
                             thumbnail=thumbnail, text_color=color4))

    if re.search(r'(?:subtitle|audio) | language: spanish"', data):
        epi_total = scrapertools.find_single_match(data, 'itemprop="numberOfEpisodes">([^<]+)</span>')
        patron = '<td class="name group">.*?title="([^"]+)">(.*?)</a>.*?>([^<]+)</a>.*?' \
                 '<td class="epno lastep">([^<]+)</td>.*?title="audio(.*?)</td>.*?' \
                 'class="source" title="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for fansub, abrev, estado, epis, lang, source in matches:
            if not "spanish" in lang:
                continue
            title = "    " + fansub
            if abrev != title:
                title += "  [%s]" % abrev
            estado = estado.replace("complete", config.get_localized_string(70378)).replace("finished", config.get_localized_string(70379)) \
                .replace("stalled", config.get_localized_string(70380)).replace("dropped", config.get_localized_string(70381))
            title += " [COLOR %s](%s)[/COLOR] %s/%s  [%s]" % (color6, estado, epis, epi_total, source)
            itemlist.append(Item(channel=item.channel, title=title, infoLabels=infoLabels, action="",
                                 thumbnail=thumbnail, text_color=color4))


def filtro_mal(item):
    logger.info()

    list_controls = []
    valores = {}
    dict_values = None
    # Se utilizan los valores por defecto/guardados
    valores_guardados = config.get_setting("filtro_defecto_mal", item.channel)
    if valores_guardados:
        dict_values = valores_guardados

    list_controls.append({'id': 'keyword', 'label': config.get_localized_string(70465), 'enabled': True,
                          'type': 'text', 'default': '', 'visible': True})
    list_controls.append({'id': 'tipo', 'label': config.get_localized_string(70482), 'enabled': True,
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[1]['lvalues'] = [config.get_localized_string(70483), config.get_localized_string(70484), config.get_localized_string(60244), config.get_localized_string(70136), config.get_localized_string(70450)]
    valores["tipo"] = ['4', '2', '3', '1', '0']
    list_controls.append({'id': 'valoracion', 'label': config.get_localized_string(70473), 'enabled': True,
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[2]['lvalues'] = [config.get_localized_string(70486), config.get_localized_string(70487), config.get_localized_string(70488), config.get_localized_string(70489),
                                   config.get_localized_string(70490), config.get_localized_string(70491), config.get_localized_string(70492), config.get_localized_string(70493),
                                   config.get_localized_string(70494), config.get_localized_string(70495), config.get_localized_string(70450)]
    valores["valoracion"] = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '0']

    list_controls.append({'id': 'estado', 'label': config.get_localized_string(70485), 'enabled': True,
                          'type': 'list', 'default': -1, 'visible': True})
    list_controls[3]['lvalues'] = ['Por estrenar', config.get_localized_string(60264), config.get_localized_string(70379), config.get_localized_string(70450)]
    valores["estado"] = ['3', '1', '2', '0']

    try:
        data = httptools.downloadpage('https://myanimelist.net/anime.php', cookies=False).data

        patron = 'name="genre\[\]" type="checkbox" value="([^"]+)">.*?>([^<]+)<'
        generos = scrapertools.find_multiple_matches(data, patron)
        if generos:
            list_controls.append({'id': 'labelgenre', 'enabled': True, 'type': 'label', 'default': None,
                                  'label': config.get_localized_string(70451),
                                  'visible': True, 'color': '0xFFC52020'})
            for value, genre in generos:
                list_controls.append({'id': 'genre' + value, 'label': genre, 'enabled': True,
                                      'type': 'bool', 'default': False, 'visible': True})
    except:
        pass

    list_controls.append({'id': 'espacio', 'label': '', 'enabled': False,
                          'type': 'label', 'default': None, 'visible': True})
    list_controls.append({'id': 'save', 'label': config.get_localized_string(70464), 'enabled': True,
                          'type': 'bool', 'default': False, 'visible': True})

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(70320), item=item, callback='callback_mal')


def callback_mal(item, values):
    values_copy = values.copy()
    # Guarda el filtro para que sea el que se cargue por defecto
    if "save" in values and values["save"]:
        values_copy.pop("save")
        config.set_setting("filtro_defecto_mal", values_copy, item.channel)

    genero_ids = []
    for v in values:
        if "genre" in v:
            if values[v]:
                genero_ids.append("genre[%s]=%s" % (len(genero_ids), v.replace('genre', '')))

    genero_ids = "&".join(genero_ids)
    query = values["keyword"].replace(" ", "%20")
    tipo = item.valores["tipo"][values["tipo"]]
    valoracion = item.valores["valoracion"][values["valoracion"]]
    estado = item.valores["estado"][values["estado"]]

    item.url = "https://myanimelist.net/anime.php?q=%s&type=%s&score=%s&status=%s" \
               "&p=0&r=0&sm=0&sd=0&sy=0&em=0&ed=0&ey=0&c[0]=a&c[1]=b&c[2]=c&c[3]=d&c[4]=f&gx=0" \
               % (query, tipo, valoracion, estado)
    if genero_ids:
        item.url += "&" + genero_ids

    item.action = "busqueda_mal"
    return busqueda_mal(item)


def musica_anime(item):
    # Lista los animes y canciones disponibles similares al título del anime
    logger.info()
    itemlist = []

    data = httptools.downloadpage("http://www.freeanimemusic.org/song_search.php", post=item.post).data
    patron = "<span class='Estilo6'>(\d+).*?<span class='Estilo22'>([^<]+)<.*?<span class='Estilo22'>([^<]+)<" \
             ".*?href='http://www.freeanimemusic.org/anime/([^/]+)/index.php\?var=(\d+)"
    matches = scrapertools.find_multiple_matches(data, patron)
    animes = {}
    action = ""
    if config.is_xbmc():
        action = "move"
    for number, song, anime, id_anime, id_song in matches:
        if not animes.get(anime):
            animes[anime] = []
            animes[anime].append(
                Item(channel=item.channel, action=action, title="[COLOR %s][%s][/COLOR]" % (color6, anime.capitalize()),
                     url="",
                     number="0", thumbnail=item.thumbnail, fanart=item.fanart))
        title = "%s - %s" % (number, song)
        animes[anime].append(
            Item(channel=item.channel, action="play", title=title, server="directo", url=id_anime, song=id_song,
                 number=number,
                 thumbnail=item.thumbnail, fanart=item.fanart, text_color=color5))

    for k, v in sorted(animes.items()):
        v.sort(key=lambda x: (x.url, int(x.number)))
        for lt in v:
            if lt.action == "move":
                lt.extra = len(v)
                lt.folder = False
            itemlist.append(lt)

    return itemlist


def login_mal(from_list=False):
    logger.info()

    try:
        user = config.get_setting("usuariomal", "tvmoviedb")
        password = config.get_setting("passmal", "tvmoviedb")
        generic = False
        if not user or not password:
            if not from_list:
                user = bdec("Y3VlbnRhdHZtb3ZpZWRi")
                password = bdec("dFlTakE3ekYzbng1")
                generic = True
            else:
                return False, config.get_localized_string(70381), user
        data = httptools.downloadpage("https://myanimelist.net/login.php?from=%2F").data
        if re.search(r'(?i)' + user, data) and not generic:
            return True, "", user
        token = scrapertools.find_single_match(data, "name='csrf_token' content='([^']+)'")
        response = httptools.downloadpage("https://myanimelist.net/logout.php", post="csrf_token=%s" % token)
        post = "user_name=%s&password=%s&cookie=1&sublogin=Login&submit=1&csrf_token=%s" % (user, password, token)
        response = httptools.downloadpage("https://myanimelist.net/login.php?from=%2F", post=post)

        if not re.search(r'(?i)' + user, response.data):
            logger.error("Error en el login")
            return False, config.get_localized_string(70330), user
        else:
            if generic:
                return False, config.get_localized_string(70381), user
            logger.info("Login correcto")
            return True, "", user
    except:
        import traceback
        logger.error(traceback.format_exc())
        return False, config.get_localized_string(70331)


def cuenta_mal(item):
    # Menú de cuenta myanimelist
    itemlist = []
    login, message, user = login_mal(True)
    if not login:
        itemlist.append(item.clone(action="configuracion", title=message, text_color=color4))
    else:
        itemlist.append(
            item.clone(action="items_mal", title=config.get_localized_string(70382), text_color=color5, accion="lista_mal",
                       url="https://myanimelist.net/animelist/%s?status=1" % user, login=True))
        itemlist.append(item.clone(action="items_mal", title=config.get_localized_string(70383), text_color=color5, accion="lista_mal",
                                   url="https://myanimelist.net/animelist/%s?status=2" % user, login=True))
        itemlist.append(item.clone(action="items_mal", title=config.get_localized_string(70384), text_color=color5, accion="lista_mal",
                                   url="https://myanimelist.net/animelist/%s?status=3" % user, login=True))
        itemlist.append(item.clone(action="items_mal", title=config.get_localized_string(70385), text_color=color5, accion="lista_mal",
                                   url="https://myanimelist.net/animelist/%s?status=4" % user, login=True))
        itemlist.append(item.clone(action="items_mal", title=config.get_localized_string(70386), text_color=color5, accion="lista_mal",
                                   url="https://myanimelist.net/animelist/%s?status=6" % user, login=True))

    return itemlist


def items_mal(item):
    # Scraper para las listas personales
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;", "", data)
    data = re.sub(r"\s{2}", " ", data)

    data_items = scrapertools.find_single_match(data, 'data-items="([^"]+)"')
    data_items = data_items.replace("&quot;", "'").replace("null", "None") \
        .replace("false", "False").replace("true", "True")
    data_items = eval(data_items)
    for d in data_items:
        if d["anime_airing_status"] == 1:
            title = "[E]"
        if d["anime_airing_status"] == 2:
            title = "[F]"
        else:
            title = "[P]"
        title += " %s [COLOR %s][%s/%s][/COLOR] (%s)" % (
        d["anime_title"], color6, d["num_watched_episodes"], d["anime_num_episodes"], d["anime_media_type_string"])
        title = title.replace("\\", "")
        contentTitle = d["anime_title"].replace("\\", "")
        thumbnail = d["anime_image_path"].replace("\\", "").replace("r/96x136/", "").replace(".jpg", "l.jpg")
        url = "https://myanimelist.net" + d["anime_url"].replace("\\", "")
        if d["score"] != 0:
            title += " [COLOR %s]Punt:%s[/COLOR]" % (color4, d["score"])
        if title.count("(TV)") == 2:
            title = title.replace("] (TV)", "]")
        elif title.count("(Movie)") == 2:
            title = title.replace("] (Movie)", "]")
        tipo = "tvshow"
        extra = "tv"
        if "Movie" in d["anime_media_type_string"]:
            tipo = "movie"
            extra = "movie"
        itemlist.append(Item(channel=item.channel, action="detalles_mal", url=url, title=title, thumbnail=thumbnail,
                             text_color=color3,
                             contentTitle=contentTitle, contentType=tipo, extra=extra, login=True))

    if itemlist:
        itemlist.insert(0, Item(channel=item.channel, action="", title=config.get_localized_string(70387)))

    return itemlist


def menu_mal(item):
    # Opciones cuenta MAL, añadir a lista/votar
    itemlist = []

    data = httptools.downloadpage(item.url).data
    try:
        status = {'1': config.get_localized_string(70479), '2': config.get_localized_string(70480), '3': config.get_localized_string(70384), '4': config.get_localized_string(70385),
                  '6': config.get_localized_string(70481)}
        button, estado = scrapertools.find_single_match(data,
                                                        'myinfo_updateInfo"(.*?)>.*?option selected="selected" value="(\d+)"')
        if "disabled" in button:
            title_estado = config.get_localized_string(70388)
            estado = "1"
        else:
            title_estado = config.get_localized_string(70389) % (color6, status[estado])
    except:
        title_estado = config.get_localized_string(70388)

    score = scrapertools.find_single_match(data, 'id="myinfo_score".*?selected" value="(\d+)"')
    if score != "0":
        title_estado += " (Punt:%s)" % score
    if "lista" in title_estado:
        item.lista = True

    itemlist.append(item.clone(title="Anime: %s%s" % (item.contentTitle, title_estado), action=""))
    status = {'1': config.get_localized_string(70479), '2': config.get_localized_string(70480), '3': config.get_localized_string(70384), '4': config.get_localized_string(70385),
              '6': config.get_localized_string(70481)}
    for key, value in status.items():
        if not value in title_estado:
            itemlist.append(
                item.clone(title=config.get_localized_string(70391) % value, action="addlist_mal", text_color=color5, value=key,
                           estado=value))

    for i in range(10, 0, -1):
        if i != int(score):
            itemlist.append(item.clone(title=config.get_localized_string(70392) % (color6, i), action="addlist_mal",
                                       value=estado, estado=status[estado], score=i))
    return itemlist


def addlist_mal(item):
    data = httptools.downloadpage(item.url).data

    anime_id = scrapertools.find_single_match(data, 'id="myinfo_anime_id" value="([^"]+)"')
    if item.value == "2":
        vistos = scrapertools.find_single_match(data, 'id="myinfo_watchedeps".*?<span id="curEps">(\d+)')
    else:
        vistos = scrapertools.find_single_match(data, 'id="myinfo_watchedeps".*?value="(\d+)"')
    if not item.score:
        item.score = scrapertools.find_single_match(data, 'id="myinfo_score".*?selected" value="(\d+)"')
    token = scrapertools.find_single_match(data, "name='csrf_token' content='([^']+)'")

    post = {'anime_id': int(anime_id), 'status': int(item.value), 'score': int(item.score),
            'num_watched_episodes': int(vistos), 'csrf_token': token}
    headers_mal = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}
    url = "https://myanimelist.net/ownlist/anime/add.json"
    if item.lista:
        url = "https://myanimelist.net/ownlist/anime/edit.json"
    #data = httptools.downloadpage(url, post=jsontools.dump(post), headers=headers_mal, replace_headers=True).data
    data = httptools.downloadpage(url, post=jsontools.dump(post), headers=headers_mal).data
    item.title = "En tu lista"
    if config.is_xbmc():
        import xbmc
        xbmc.executebuiltin("Container.Refresh")


def move(item):
    import xbmcgui, xbmc
    item_focus = str(item.extra)
    wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    id = wnd.getFocusId()
    return xbmc.executebuiltin('Control.Move(' + str(id) + ',' + item_focus + ')')


def play(item):
    itemlist = []
    if not item.server:
        data = httptools.downloadpage(item.url).data
        if "Sorry, this video is not available to be embedded" in data:
            id_video = scrapertools.find_single_match(data, '<div class="video-embed.*?-(\d+)\&amp;aff')
            crunchy = "https://www.crunchyroll.com/affiliate_iframeplayer?aff=af-12299-plwa&media_id=%s&video_format=106&video_quality=60&auto_play=0" % id_video
        else:
            crunchy = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
        itemlist.append(item.clone(server="crunchyroll", url=crunchy))
    else:
        if item.server == "directo" and item.song:
            url = ""
            data_music = jsontools.load(
                httptools.downloadpage("http://www.musicaanime.org/scripts/resources/artists1.php").data)
            for child in data_music["data"]:
                if child["title"] == item.url.upper():
                    url = "http://www.musicaanime.org/aannmm11/%s/imagen%s.mp3" % (child["artist"], item.song.zfill(3))
                    break
            if url:
                itemlist.append(item.clone(url=url))
        else:
            itemlist.append(item)

    return itemlist


def get_cookie_value():
    cookies = filetools.join(config.get_data_path(), 'cookies.dat')
    cookiedata = filetools.read(cookies)
    malsess = scrapertools.find_single_match(cookiedata, "myanimelist.*?MALHLOGSESSID\s+([A-z0-9\+\=]+)")
    cookievalue = "MALHLOGSESSID=" + malsess
    mal_id = scrapertools.find_single_match(cookiedata, "myanimelist.*?MALSESSIONID\s+([A-z0-9\+\=\-]+)")
    if mal_id:
        cookievalue += "; MALSESSIONID=%s;" % mal_id

    return cookievalue
