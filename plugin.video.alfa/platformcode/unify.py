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

    cast =['castellano','espanol','cast','esp','espaol', 'es','']
    lat=['latino','lat','la', 'espanol latino', 'espaol latino']
    vose=['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','ingles','subs castellano',
          'sub: español']
    vos=['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles']
    vo=['ingles', 'en','vo', 'ovos']

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
    #language = '%s, %s'%(language, old_lang)

    return language

def title_format(item):
    logger.info()
    #color_scheme={'movie':'cyan', 'tvshow':'goldenrod','server':'orange', 'quality':'gold', 'year':'orchid',
    #              'library':'hotpink'}

    color_scheme = {'movie': 'white', 'tvshow': 'white', 'server': 'white', 'quality': 'white', 'year': 'white',
                    'library': 'white'}

    excluded = ['Enlaces Online', 'Enlaces Descargas']

    lang = False

    if item.action == 'mainlist':
        item.language =''


    if item.title not in excluded:
        if item.contentTitle and 'library' not in item.action:
            item.title = '[COLOR %s]%s[/COLOR]'%(color_scheme['movie'],item.contentTitle)
            #item.title = item.title
        elif item.contentSerieName:
            item.title = '[COLOR %s]%s[/COLOR]' %(color_scheme['tvshow'], item.title)
        elif 'library' in item.action:
            item.title = '[COLOR %s]%s[/COLOR]' % (color_scheme['library'], item.title)

        if isinstance(item.language,list):
            language_list =[]
            for language in item.language:
                #language = re.sub(r'\[COLOR .*?\]|\[/COLOR\]', '', language)
                if language != '':
                    lang = True
                    old_lang = language
                    language_list.append(set_lang(language))
                    logger.debug('language_list: %s' % language_list)
            item.language = language_list
        elif not isinstance(item.language,list):
            #item.language = re.sub(r'\[COLOR .*?\]|\[/COLOR\]', '', item.language)
            if item.language != '':
                lang = True
                old_lang = item.lang
                item.language = set_lang(item.language)
        else:
            item.language = ''
            logger.debug('item.language: %s' % item.language)


        # Damos formato al año si existiera
        if item.infoLabels.get("year", "") != "":
            try:
                year = '[COLOR %s][%s][/COLOR]' % (color_scheme['year'], item.infoLabels['year'])
                item.title = item.title = '%s %s' % (item.title, year)
            except:
                logger.debug('infoLabels: %s'%item.infoLabels)

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

        #compureba si estamos en findvideos, y si hay server, si es asi no se muestra el
        #titulo sino el server, en caso contrario se muestra el titulo normalmente.

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