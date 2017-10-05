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


def simplify(string):
    logger.info()
    string = re.sub(r'\[*.?COLOR.*?\]|\[|\]|\(|\)', '', string)
    string = string.strip()
    string = string.decode('utf-8')
    notilde = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
    string = notilde.decode()
    string = string.lower()

    return string

def set_lang(language):
    logger.info()

    cast =['castellano','espanol','cast','esp','espaol', 'es','zc', 'spa']
    lat=['latino','lat','la', 'espanol latino', 'espaol latino', 'zl', 'mx', 'co']
    vose=['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','subs castellano',
          'sub: español', 'vs', 'zs']
    vos=['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles']
    vo=['ingles', 'en','vo', 'ovos', 'eng']
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
    color_scheme={'movie':'white', 'tvshow':'goldenrod','server':'salmon', 'quality':'gold', 'year':'orchid',
                  'library':'hotpink', 'rating_1':'red', 'rating_2':'cyan', 'rating_3':'gold', 'cast':'yellow',
                  'lat':'limegreen', 'vose':'orange', 'vos':'red', 'vo':'red', 'otro':'white', 'videoteca':'yellow'}

    #color_scheme = {'movie': 'white', 'tvshow': 'white', 'server': 'white', 'quality': 'white', 'year': 'white',
    #                'library': 'white', 'rating':'gold','rating_1':'white', 'rating_2':'white', 'rating_3':'white'}


    # TODO se deberia quitar cualquier elemento que no sea un enlace de la lista de findvideos para quitar esto
    excluded = ['online', 'descarga', 'downloads', 'trailer', 'videoteca', 'gb', 'autoplay']

    lang = False
    valid = True
    language_color = 'otro'
    if item.action == 'mainlist':
        item.language =''

    info = item.infoLabels
    logger.debug('item: %s'%item)
    logger.debug('item.title: %s' % item.title.lower())
    for word in excluded:
        if word in item.title.lower():
            valid = False
            break

    #TODO se deberia quitar cualquier elemento que no sea un enlace de la lista de findvideos para quitar esto
    if valid and item.action != 'buscartrailer' and item.channel != 'trailertools':

        # Evitamos modificar el titulo de la videoteca
        if not 'library' in item.action:


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

                    item.title = '[COLOR %s]%sx%s - %s[/COLOR]' % (color_scheme['tvshow'], info['season'],
                                                                   info['episode'], info['title'])
                else:

                    # En caso contrario se utiliza el titulo proporcionado por el canal
                    item.title = '[COLOR %s]%s[/COLOR]' % (color_scheme['tvshow'], item.title)

            elif item.contentTitle:
                # Si el titulo no tiene contentSerieName entonces se formatea como pelicula
                item.title = '[COLOR %s]%s[/COLOR]'%(color_scheme['movie'],item.contentTitle)


            if 'Novedades' in item.category:
                logger.debug('novedades')
                item.title = '%s [%s]'%(item.title, item.channel)

            # Verificamos si item.language es una lista, si lo es se toma
            # cada valor y se normaliza formado una nueva lista

            if isinstance(item.language, list):
                language_list =[]
                for language in item.language:
                    if language != '':
                        lang = True
                        language_list.append(set_lang(language).upper())
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
            if info and info.get("year", "") != "" and item.contentType != 'episode' and not info['season']:
                try:
                    year = '[COLOR %s][%s][/COLOR]' % (color_scheme['year'], info['year'])
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
                        color_rating = color_scheme['rating_1']
                    elif value > 3 and value <= 7:
                        color_rating = color_scheme['rating_2']
                    else:
                        color_rating = color_scheme['rating_3']

                    rating = '[COLOR %s][%s][/COLOR]' % (color_rating, rating_value)
                else:
                    rating = ''
                item.title = '%s %s' % (item.title, rating)

            # Damos formato a la calidad si existiera y lo agregamos al titulo
            if item.quality:
                quality = '[COLOR %s][%s][/COLOR]' % (color_scheme['quality'], item.quality.strip())
                item.title = '%s %s' % (item.title, quality)
            else:
                quality = ''

            # Damos formato al idioma si existiera y lo agregamos al titulo
            if lang:
                if isinstance(simple_language, list):
                    for language in simple_language:
                        language_color = language.lower()
                        item.title = '%s [COLOR %s][%s][/COLOR]' % (item.title, color_scheme[language_color], language)
                else:
                    language_color = simple_language.lower()
                    item.title = '%s [COLOR %s][%s][/COLOR]' % (item.title, color_scheme[language_color], simple_language)

            # Damos formato al servidor si existiera
            if item.server:
                server = '[COLOR %s][%s][/COLOR]' % (color_scheme['server'], item.server.strip().capitalize())

            # Compureba si estamos en findvideos, y si hay server, si es asi no se muestra el
            # titulo sino el server, en caso contrario se muestra el titulo normalmente.

            if item.action != 'play' and item.server:
                item.title ='%s %s'%(item.title, server.strip())
            elif item.action == 'play' and item.server:
                #item.title = 'S:%s  Q:%s I:%s' % (server, quality, item.language)
                if item.quality == 'default':
                    quality = ''
                if lang:
                    simple_language = '[%s]'%simple_language
                else:
                    simple_language = ''

                logger.debug('language_color: %s'%language_color)
                item.title = '%s %s [COLOR %s]%s[/COLOR]' % (server, quality.strip(), color_scheme[language_color],
                                                               simple_language)
                logger.debug('item.title: %s' % item.title)
            else:
                item.title = '%s' % item.title
        else:
            item.title = '[COLOR %s]%s[/COLOR]' % (color_scheme['library'], item.title)

    # Formatear titulo
    if item.text_color !='':
        item.title = '[COLOR %s]%s[/COLOR]'%(item.text_color, item.title)
    if item.text_bold:
        item.title = '[B]%s[/B]' % item.title
    if item.text_italic:
        item.title = '[I]%s[/I]' % item.title

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
