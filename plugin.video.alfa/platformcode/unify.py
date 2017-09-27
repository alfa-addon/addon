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
    string = string.strip()
    string = string.decode('utf-8')
    notilde = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
    string = notilde.decode()
    string = string.lower()

    return string

def set_lang(language):
    logger.info()
    lang_color_1 = 'yellow'
    lang_color_2 = 'limegreen'
    lang_color_3 = 'red'
    lang_color_4 = 'orange'
    lang_color_5 = 'white'

    cast =['castellano','espanol','cast','esp','espaol', 'es','zc']
    lat=['latino','lat','la', 'espanol latino', 'espaol latino', 'zl', 'mx', 'co']
    vose=['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','subs castellano',
          'sub: español', 'vs', 'zs']
    vos=['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles']
    vo=['ingles', 'en','vo', 'ovos', 'eng']
    language = scrapertools.decodeHtmlentities(language)
    old_lang = language
    logger.debug('language: %s'%language)
    language = re.sub(r'\[*.?COLOR.*?\]|\[|\]|\(|\)', '', language)
    logger.debug('language re.sub: x%sx' % language)

    language = simplify(language)

    logger.debug('language simplify: %s' % language)

    if language in cast:
        language = '[COLOR %s][CAST][/COLOR]'% lang_color_1
    elif language in lat:
        language = '[COLOR %s][LAT][/COLOR]' % lang_color_2
    elif language in vose:
        language = '[COLOR %s][VOSE][/COLOR]'% lang_color_3
    elif language in vos:
        language = '[COLOR %s][VOS][/COLOR]' % lang_color_4
    elif language in vo:
        language = '[COLOR %s][VO][/COLOR]' % lang_color_4
    else:
        language = '[COLOR %s][OTRO](%s)[/COLOR]' % (lang_color_5, old_lang)

    return language

def title_format(item):
    logger.info()
    #color_scheme={'movie':'cyan', 'tvshow':'goldenrod','server':'orange', 'quality':'gold', 'year':'orchid',
    #              'library':'hotpink', 'rating':'blue'}

    color_scheme = {'movie': 'white', 'tvshow': 'white', 'server': 'white', 'quality': 'white', 'year': 'white',
                    'library': 'white', 'rating':'gold'}

    excluded = ['Enlaces Online', 'Enlaces Descargas', 'Online', 'Downloads', 'Buscar Tráiler']

    lang = False

    if item.action == 'mainlist':
        item.language =''

    info = item.infoLabels
    logger.debug('item: %s'%item)
    if item.title not in excluded:

        if not 'library' in item.action:

            if item.contentSerieName:
                if item.contentType == 'episode' and info['episode'] != '':
                    if info['title'] == '':
                        info['title'] = 'Episodio %s'% info['episode']
                    elif 'Episode' in info['title']:
                        info['title'] = info['title'].replace('Episode', 'Episodio')

                    title = ''
                    item.title = '[COLOR %s]%sx%s - %s[/COLOR]' % (color_scheme['tvshow'], info['season'],
                                                                   info['episode'], info['title'])
                else:
                    item.title = '[COLOR %s]%s[/COLOR]' % (color_scheme['tvshow'], item.title)
            elif item.contentTitle:
                item.title = '[COLOR %s]%s[/COLOR]'%(color_scheme['movie'],item.contentTitle)

        else:
            item.title = '[COLOR %s]%s[/COLOR]' % (color_scheme['library'], item.title)

        if isinstance(item.language,list):
            language_list =[]
            for language in item.language:
                if language != '':
                    lang = True
                    language_list.append(set_lang(language))
                    logger.debug('language_list: %s' % language_list)
            item.language = language_list
        else:
            if item.language != '':
                lang = True
                item.language = set_lang(item.language)

        # Damos formato al año si existiera
        if item.info and item.info.get("year", "") != "":
            try:
                year = '[COLOR %s][%s][/COLOR]' % (color_scheme['year'], info['year'])
                item.title = item.title = '%s %s' % (item.title, year)
            except:
                logger.debug('infoLabels: %s'%info)

        # Damos formato al puntaje si existiera
        if info and info['rating'] and info['rating']!='0.0':
            rating = '[COLOR %s][%s][/COLOR]' % (color_scheme['rating'], info['rating'])
            item.title = '%s %s' % (item.title, rating)

        # Damos formato a la calidad si existiera
        if item.quality:
            quality = '[COLOR %s][%s][/COLOR]' % (color_scheme['quality'], item.quality.strip())
            item.title = '%s %s' % (item.title, quality)
        else:
            quality = ''
        # Damos formato al idioma si existiera
        if lang:
            if isinstance(item.language, list):
                for language in item.language:
                    item.title = '%s %s' % (item.title, language)
            else:
                item.title = '%s %s' % (item.title, item.language)

        if item.server:
            server = '[COLOR %s][%s][/COLOR]' % (color_scheme['server'], item.server.strip())

        # Compureba si estamos en findvideos, y si hay server, si es asi no se muestra el
        # titulo sino el server, en caso contrario se muestra el titulo normalmente.

        if item.action != 'play' and item.server:
            item.title ='%s %s'%(item.title, server.strip())
        elif item.action == 'play' and item.server:
            #item.title = 'S:%s  Q:%s I:%s' % (server, quality, item.language)
            item.title = '%s %s %s' % (server.strip(), quality.strip(), item.language)
        else:
            item.title = '%s' % item.title

    # Formatear titulo

    if item.text_bold:
        item.title = '[B]%s[/B]' % item.title
    if item.text_italic:
        item.title = '[I]%s[/I]' % item.title

    return item

def thumbnail_type(item):
    logger.info()

    # Se comprueba que tipo de thumbnail se utilizara en findvideos,
    # Poster o logo del servidor

    thumb_type = config.get_setting('video_thumbnail_type')
    logger.debug('thumb_type: %s' % thumb_type)
    info = item.infoLabels
    logger.debug('item.thumbnail: %s'%item.thumbnail)
    if item.action == 'play':
        if thumb_type == 0:
            if info and info['thumbnail'] != '':
                item.thumbnail = info['thumbnail']
        elif thumb_type == 1:
            from core.servertools import get_server_parameters
            logger.debug('item.server: %s'%item.server)
            server_parameters = get_server_parameters(item.server.lower())
            item.thumbnail = server_parameters.get("thumbnail", "")
            logger.debug('thumbnail: %s' % item.thumb)

    return item.thumbnail