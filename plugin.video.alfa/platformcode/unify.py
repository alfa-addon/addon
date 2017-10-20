# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Unify
# ------------------------------------------------------------
# Herramientas responsables de unificar diferentes tipos de
# datos obtenidos de las paginas
# ----------------------------------------------------------

import os
import sys
import urllib
import unicodedata
import re

import config
from core.item import Item
from core import scrapertools
from platformcode import logger

def remove_format(string):
    logger.info()
    #logger.debug('entra en remove: %s' % string)
    string = string.strip()
    string = re.sub(r'(\[|\[\/)(?:color|COLOR|b|B|i|I).*?\]|\s{2,}|\[|\]|\(|\)|\:', '', string)
    #logger.debug('sale de remove: %s' % string)
    return string

def simplify(string):
    logger.info()
    #logger.debug('entra en simplify: %s'%string)
    string = remove_format(string)
    string = string.strip()
    string = string.decode('utf-8')
    notilde = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
    string = notilde.decode()
    string = string.lower()
    #logger.debug('sale de simplify: %s' % string)

    return string

def set_color(title, category):
    logger.info()

    color_scheme = {'otro': 'white'}

    category = remove_format(category).lower()

    # Lista de elementos posibles en el titulo
    color_list = ['movie', 'tvshow', 'year', 'rating_1', 'rating_2', 'rating_3', 'quality', 'cast', 'lat', 'vose',
                  'vos', 'vo', 'server', 'library']

    # Se verifica el estado de la opcion de colores personalizados
    custom_colors = config.get_setting('title_color')

    # Se Forma el diccionario de colores para cada elemento, la opcion esta activas utiliza la configuracion del
    #  usuario, si no  pone el titulo en blanco.
    if title not in ['', ' ']:
        for element in color_list:
            if custom_colors:
                color_scheme[element] = remove_format(config.get_setting('%s_color' % element))
            else:
                color_scheme[element] = 'white'
        if category not in ['movie', 'tvshow', 'library', 'otro']:
            title = "[COLOR %s][%s][/COLOR]"%(color_scheme[category], title)
        else:
            title = "[COLOR %s]%s[/COLOR]" % (color_scheme[category], title)
    return title

def set_lang(language):
    logger.info()

    cast =['castellano','espanol','cast','esp','espaol', 'es','zc', 'spa', 'spanish', 'vc']
    lat=['latino','lat','la', 'espanol latino', 'espaol latino', 'zl', 'mx', 'co', 'vl']
    vose=['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','subs castellano',
          'sub: español', 'vs', 'zs', 'vs', 'english-spanish subs', 'ingles sub espanol']
    vos=['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles']
    vo=['ingles', 'en','vo', 'ovos', 'eng','v.o', 'english']

    language = scrapertools.decodeHtmlentities(language)
    old_lang = language

    language = simplify(language)

    logger.debug('language before simplify: %s' % language)
    logger.debug('old language: %s' % old_lang)
    if language in cast:
        language = 'cast'
    elif language in lat:
        language = 'lat'
    elif language in vose:
        language = 'vose'
    elif language in vos:
        language = 'vos'
    elif language in vo:
        language = 'vo'
    else:
        language = 'otro'

    logger.debug('language after simplify: %s' % language)

    return language

def title_format(item):
    logger.info()


    lang = False
    valid = True
    language_color = 'otro'

    logger.debug('item.title antes de formatear: %s' % item.title.lower())



    # TODO se deberia quitar cualquier elemento que no sea un enlace de la lista de findvideos para quitar esto
    excluded_words = ['online', 'descarga', 'downloads', 'trailer', 'videoteca', 'gb', 'autoplay']
    excluded_actions = ['buscartrailer', '']

    # Se elimina cualquier formato previo en el titulo
    if item.action != '':
        item.title = remove_format(item.title)

    # Evita que aparezcan los idiomas en los mainlist de cada canal
    if item.action == 'mainlist':
        item.language =''

    info = item.infoLabels
    logger.debug('item antes de formatear: %s'%item)

    if hasattr(item,'text_color'):
        item.text_color=''

    #Verifica si el titulo tiene palabra de la lista de exclusion
    for word in excluded_words:
        if word in item.title.lower():
            valid = False
            break

    #TODO se deberia quitar cualquier elemento que no sea un enlace de la lista de findvideos para quitar esto
    if valid and item.action not in excluded_actions and item.channel != 'trailertools':

        # Formamos el titulo para serie, se debe definir contentSerieName
        # o show en el item para que esto funcione.
        if item.contentSerieName:

            # Si se tiene la informacion en infolabels se utiliza
            if item.contentType == 'episode' and info['episode'] != '':
                if info['title'] == '':
                    info['title'] = '%s - Episodio %s'% (info['tvshowtitle'], info['episode'])
                elif 'Episode' in info['title']:
                    episode = info['title'].replace('Episode', 'Episodio')
                    info['title'] = '%s - %s' % (info['tvshowtitle'], episode)

                item.title = '%sx%s - %s' % (info['season'],info['episode'], info['title'])
                item.title = set_color(item.title, 'tvshow')
            else:

                # En caso contrario se utiliza el titulo proporcionado por el canal
                #logger.debug ('color_scheme[tvshow]: %s' % color_scheme['tvshow'])
                item.title = '%s' % set_color(item.title, 'tvshow')

        elif item.contentTitle:
            # Si el titulo no tiene contentSerieName entonces se formatea como pelicula
            item.title = '%s' % set_color(item.contentTitle, 'movie')

        if 'Novedades' in item.category and item.from_channel=='news':
            logger.debug('novedades')
            item.title = '%s [%s]'%(item.title, item.channel)

        # Verificamos si item.language es una lista, si lo es se toma
        # cada valor y se normaliza formado una nueva lista

        if hasattr(item,'language') and item.language !='':
            logger.debug('tiene language: %s'%item.language)
            if isinstance(item.language, list):
                language_list =[]
                for language in item.language:
                    if language != '':
                        lang = True
                        language_list.append(set_lang(remove_format(language)).upper())
                        #logger.debug('language_list: %s' % language_list)
                simple_language = language_list
            else:
                # Si item.language es un string se normaliza
                if item.language != '':
                    lang = True
                    simple_language = set_lang(item.language).upper()
                else:
                    simple_language = ''

            item.language = simple_language

        # Damos formato al año si existiera y lo agregamos
        # al titulo excepto que sea un episodio
        if info and info.get("year", "") not in [""," "] and item.contentType != 'episode' and not info['season']:
            try:
                year = '%s' % set_color(info['year'], 'year')
                item.title = item.title = '%s %s' % (item.title, year)
            except:
                logger.debug('infoLabels: %s'%info)

        # Damos formato al puntaje si existiera y lo agregamos al titulo
        if info and info['rating'] and info['rating']!='0.0' and not info['season']:

            # Se normaliza el puntaje del rating

            rating_value = check_rating(info['rating'])

            # Asignamos el color dependiendo el puntaje, malo, bueno, muy bueno, en caso de que exista

            if rating_value:
                value = float(rating_value)
                if value <= 3:
                    color_rating = 'rating_1'
                elif value > 3 and value <= 7:
                    color_rating = 'rating_2'
                else:
                    color_rating = 'rating_3'

                rating = '%s' % rating_value
            else:
                rating = ''
                color_rating = 'otro'
            item.title = '%s %s' % (item.title, set_color(rating, color_rating))

        # Damos formato a la calidad si existiera y lo agregamos al titulo
        if item.quality:
            quality = item.quality.strip()
            item.title = '%s %s' % (item.title, set_color(quality, 'quality'))
        else:
            quality = ''

        # Damos formato al idioma si existiera y lo agregamos al titulo
        if lang:
            if isinstance(simple_language, list):
                for language in simple_language:
                    item.title = '%s %s' % (item.title, set_color(language, language))
            else:
                item.title = '%s %s' % (item.title, set_color(simple_language, simple_language))

        # Damos formato al servidor si existiera
        if item.server:
            server = '%s' % set_color(item.server.strip().capitalize(), 'server')

        # Compureba si estamos en findvideos, y si hay server, si es asi no se muestra el
        # titulo sino el server, en caso contrario se muestra el titulo normalmente.

        logger.debug('item.title antes de server: %s'%item.title)
        if item.action != 'play' and item.server:
            item.title ='%s %s'%(item.title, server.strip())
        elif item.action == 'play' and item.server:
            if item.quality == 'default':
                quality = ''
            if lang:
                simple_language = '%s'%simple_language
            else:
                simple_language = ''

            logger.debug('language_color: %s'%language_color)
            item.title = '%s %s %s' % (server, set_color(quality,'quality'), set_color(simple_language,
                                                                                       simple_language))
            logger.debug('item.title: %s' % item.title)
        else:
            item.title = '%s' % item.title
        logger.debug('item.title despues de server: %s' % item.title)
    elif 'library' in item.action:
        item.title = '%s' % set_color(item.title, 'library')
    elif item.action == '' and item.title !='':
        item.title='**- %s -**'%item.title
    else:
        item.title = '%s' % set_color(item.title, 'otro')

    return item

def thumbnail_type(item):
    logger.info()

    # Se comprueba que tipo de thumbnail se utilizara en findvideos,
    # Poster o Logo del servidor

    thumb_type = config.get_setting('video_thumbnail_type')
    #logger.debug('thumb_type: %s' % thumb_type)
    info = item.infoLabels
    #logger.debug('item.thumbnail: %s'%item.thumbnail)

    if info['thumbnail'] !='':
        item.contentThumbnail = info['thumbnail']
    else:
        item.contentThumbnail = item.thumbnail

    if item.action == 'play':
        if thumb_type == 0:
            if info and info['thumbnail'] != '':
                item.thumbnail = info['thumbnail']
        elif thumb_type == 1:
            from core.servertools import get_server_parameters
            #logger.debug('item.server: %s'%item.server)
            server_parameters = get_server_parameters(item.server.lower())
            item.thumbnail = server_parameters.get("thumbnail", "")
            #logger.debug('thumbnail: %s' % item.thumb)

    return item.thumbnail


from decimal import *


def check_rating(rating):
    # logger.debug("\n\nrating %s" % rating)

    def check_decimal_length(_rating):
        """
       Dejamos que el float solo tenga un elemento en su parte decimal, "7.10" --> "7.1"
       @param _rating: valor del rating
       @type _rating: float
       @return: devuelve el valor modificado si es correcto, si no devuelve None
       @rtype: float|None
       """
        # logger.debug("rating %s" % _rating)

        try:
            # convertimos los deciamles p.e. 7.1
            return "%.1f" % round(_rating, 1)
        except Exception, ex_dl:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex_dl).__name__, ex_dl.args)
            logger.error(message)
            return None

    def check_range(_rating):
        """
       Comprobamos que el rango de rating sea entre 0.0 y 10.0
       @param _rating: valor del rating
       @type _rating: float
       @return: devuelve el valor si está dentro del rango, si no devuelve None
       @rtype: float|None
       """
        # logger.debug("rating %s" % _rating)
        # fix para comparacion float
        dec = Decimal(_rating)
        if 0.0 <= dec <= 10.0:
            # logger.debug("estoy en el rango!")
            return _rating
        else:
            # logger.debug("NOOO estoy en el rango!")
            return None

    def convert_float(_rating):
        try:
            return float(_rating)
        except ValueError, ex_ve:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex_ve).__name__, ex_ve.args)
            logger.error(message)
            return None

    if type(rating) != float:
        # logger.debug("no soy float")
        if type(rating) == int:
            # logger.debug("soy int")
            rating = convert_float(rating)
        elif type(rating) == str:
            # logger.debug("soy str")

            rating = rating.replace("<", "")
            rating = convert_float(rating)

            if rating is None:
                # logger.debug("error al convertir str, rating no es un float")
                # obtenemos los valores de numericos
                new_rating = scrapertools.find_single_match(rating, "(\d+)[,|:](\d+)")
                if len(new_rating) > 0:
                    rating = convert_float("%s.%s" % (new_rating[0], new_rating[1]))

        else:
            logger.error("no se que soy!!")
            # obtenemos un valor desconocido no devolvemos nada
            return None

    if rating:
        rating = check_decimal_length(rating)
        rating = check_range(rating)

    return rating
