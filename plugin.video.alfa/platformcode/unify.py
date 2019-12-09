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

thumb_dict = {"movies": "https://s10.postimg.cc/fxtqzdog9/peliculas.png",
    "tvshows": "https://s10.postimg.cc/kxvslawe1/series.png",
    "on air":"https://i.postimg.cc/HLLJWMcr/en-emision.png",
    "all": "https://s10.postimg.cc/h1igpgw0p/todas.png",
    "genres": "https://s10.postimg.cc/6c4rx3x1l/generos.png",
    "search": "https://s10.postimg.cc/v985e2izd/buscar.png",
    "quality": "https://s10.postimg.cc/9bbojsbjd/calidad.png",
    "audio": "https://s10.postimg.cc/b34nern7d/audio.png",
    "newest": "https://s10.postimg.cc/g1s5tf1bt/novedades.png",
    "last": "https://s10.postimg.cc/i6ciuk0eh/ultimas.png",
    "hot": "https://s10.postimg.cc/yu40x8q2x/destacadas.png",
    "year": "https://s10.postimg.cc/atzrqg921/a_o.png",
    "alphabet": "https://s10.postimg.cc/4dy3ytmgp/a-z.png",
    "recomended": "https://s10.postimg.cc/7xk1oqccp/recomendadas.png",
    "more watched": "https://s10.postimg.cc/c6orr5neh/masvistas.png",
    "more voted": "https://s10.postimg.cc/lwns2d015/masvotadas.png",
    "favorites": "https://s10.postimg.cc/rtg147gih/favoritas.png",
    "colections": "https://s10.postimg.cc/ywnwjvytl/colecciones.png",
    "categories": "https://s10.postimg.cc/v0ako5lmh/categorias.png",
    "premieres": "https://s10.postimg.cc/sk8r9xdq1/estrenos.png",
    "documentaries": "https://s10.postimg.cc/68aygmmcp/documentales.png",
    "language": "https://s10.postimg.cc/6wci189ft/idioma.png",
    "new episodes": "https://s10.postimg.cc/fu4iwpnqh/nuevoscapitulos.png",
    "country": "https://s10.postimg.cc/yz0h81j15/pais.png",
    "adults": "https://s10.postimg.cc/s8raxc51l/adultos.png",
    "recents": "https://s10.postimg.cc/649u24kp5/recents.png",
    "updated" : "https://s10.postimg.cc/46m3h6h9l/updated.png",
    "actors": "https://i.postimg.cc/tC2HMhVV/actors.png",
    "cast": "https://i.postimg.cc/qvfP5Xvt/cast.png",
    "lat": "https://i.postimg.cc/Gt8fMH0J/lat.png",
    "vose": "https://i.postimg.cc/kgmnbd8h/vose.png",
    "accion": "https://s14.postimg.cc/sqy3q2aht/action.png",
    "adolescente" : "https://s10.postimg.cc/inq7u4p61/teens.png",
    "adultos": "https://s10.postimg.cc/s8raxc51l/adultos.png",
    "animacion": "https://s14.postimg.cc/vl193mupd/animation.png",
    "anime" : "https://s10.postimg.cc/n9mc2ikzt/anime.png",
    "artes marciales" : "https://s10.postimg.cc/4u1v51tzt/martial_arts.png",
    "asiaticas" : "https://i.postimg.cc/Xq0HXD5d/asiaticas.png",
    "aventura": "https://s14.postimg.cc/ky7fy5he9/adventure.png",
    "belico": "https://s14.postimg.cc/5e027lru9/war.png",
    "biografia" : "https://s10.postimg.cc/jq0ecjxnt/biographic.png",
    "carreras": "https://s14.postimg.cc/yt5qgdr69/races.png",
    "ciencia ficcion": "https://s14.postimg.cc/8kulr2jy9/scifi.png",
    "cine negro" : "https://s10.postimg.cc/6ym862qgp/noir.png",
    "comedia": "https://s14.postimg.cc/9ym8moog1/comedy.png",
    "cortometraje" : "https://s10.postimg.cc/qggvlxndl/shortfilm.png",
    "crimen": "https://s14.postimg.cc/duzkipjq9/crime.png",
    "de la tv": "https://s10.postimg.cc/94gj0iwh5/image.png",
    "deporte": "https://s14.postimg.cc/x1crlnnap/sports.png",
    "destacadas": "https://s10.postimg.cc/yu40x8q2x/destacadas.png",
    "documental": "https://s10.postimg.cc/68aygmmcp/documentales.png",
    "doramas":"https://s10.postimg.cc/h4dyr4nfd/doramas.png",
    "drama": "https://s14.postimg.cc/fzjxjtnxt/drama.png",
    "erotica" : "https://s10.postimg.cc/dcbb9bfx5/erotic.png",
    "espanolas" : "https://s10.postimg.cc/x1y6zikx5/spanish.png",
    "estrenos" : "https://s10.postimg.cc/sk8r9xdq1/estrenos.png",
    "extranjera": "https://s10.postimg.cc/f44a4eerd/foreign.png",
    "familiar": "https://s14.postimg.cc/jj5v9ndsx/family.png",
    "fantasia": "https://s14.postimg.cc/p7c60ksg1/fantasy.png",
    "fantastico" : "https://s10.postimg.cc/tedufx5eh/fantastic.png",
    "historica": "https://s10.postimg.cc/p1faxj6yh/historic.png",
    "horror" : "https://s10.postimg.cc/8exqo6yih/horror2.png",
    "infantil": "https://s14.postimg.cc/4zyq842mp/childish.png",
    "intriga": "https://s14.postimg.cc/5qrgdimw1/intrigue.png",
    "latino" : "https://s10.postimg.cc/swip0b86h/latin.png",
    "mexicanas" : "https://s10.postimg.cc/swip0b86h/latin.png",
    "misterio": "https://s14.postimg.cc/3m73cg8ep/mistery.png",
    "musical": "https://s10.postimg.cc/hy7fhtecp/musical.png",
    "peleas" : "https://s10.postimg.cc/7a3ojbjwp/Fight.png",
    "policial" : "https://s10.postimg.cc/wsw0wbgbd/cops.png",
    "recomendadas": "https://s10.postimg.cc/7xk1oqccp/recomendadas.png",
    "religion" : "https://s10.postimg.cc/44j2skquh/religion.png",
    "romance" : "https://s10.postimg.cc/yn8vdll6x/romance.png",
    "romantica": "https://s14.postimg.cc/8xlzx7cht/romantic.png",
    "suspenso": "https://s10.postimg.cc/7peybxdfd/suspense.png",
    "telenovelas": "https://i.postimg.cc/QCXZkyDM/telenovelas.png",
    "terror": "https://s14.postimg.cc/thqtvl52p/horror.png",
    "thriller": "https://s14.postimg.cc/uwsekl8td/thriller.png",
    "western": "https://s10.postimg.cc/5wc1nokjt/western.png"
    }



def set_genre(string):
    #logger.info()

    genres_dict = {'accion':['accion', 'action', 'accion y aventura', 'action & adventure'],
                   'adultos':['adultos', 'adultos +', 'adulto'],
                   'animacion':['animacion', 'animacion e infantil', 'dibujos animados'],
                   'adolescente':['adolescente', 'adolescentes', 'adolescencia', 'adolecentes'],
                   'aventura':['aventura', 'aventuras'],
                   'belico':['belico', 'belica', 'belicas', 'guerra', 'belico guerra'],
                   'biografia':['biografia', 'biografias', 'biografica', 'biograficas', 'biografico'],
                   'ciencia ficcion':['ciencia ficcion', 'cienciaficcion', 'sci fi', 'c ficcion'],
                   'cine negro':['film noir', 'negro'],
                   'comedia':['comedia', 'comedias'],
                   'cortometraje':['cortometraje', 'corto', 'cortos'],
                   'de la tv':['de la tv', 'television', 'tv'],
                   'deporte':['deporte', 'deportes'],
                   'destacadas':['destacada', 'destacadas'],
                   'documental':['documental', 'documentales'],
                   'erotica':['erotica', 'erotica +', 'eroticas', 'eroticas +', 'erotico', 'erotico +'],
                   'estrenos':['estrenos', 'estrenos'],
                   'extranjera':['extrajera', 'extrajeras', 'foreign'],
                   'familiar':['familiar', 'familia'],
                   'fantastico':['fantastico', 'fantastica', 'fantasticas'],
                   'historica':['historica', 'historicas', 'historico', 'historia'],
                   'infantil':['infantil', 'kids'],
                   'musical':['musical', 'musicales', 'musica'],
                   'policial':['policial', 'policiaco', 'policiaca'],
                   'recomendadas':['recomedada', 'recomendadas'],
                   'religion':['religion', 'religiosa', 'religiosas'],
                   'romantica':['romantica', 'romanticas', 'romantico'],
                   'suspenso':['suspenso', 'suspense'],
                   'thriller':['thriller', 'thrillers'],
                   'western':['western', 'westerns', 'oeste western']
                   }
    string = re.sub(r'peliculas de |pelicula de la |peli |cine ','', string)
    for genre, variants in genres_dict.items():
        if string in variants:
            string = genre

    return string

def remove_format(string):
    #logger.info()
    #logger.debug('entra en remove: %s' % string)
    string = string.rstrip()
    string = re.sub(r'(\[|\[\/)(?:color|COLOR|b|B|i|I).*?\]|\[|\]|\(|\)|\:|\.', '', string)
    #logger.debug('sale de remove: %s' % string)
    return string

def normalize(string):
    string = string.decode('utf-8')
    normal = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
    return normal


def simplify(string):

    #logger.info()
    #logger.debug('entra en simplify: %s'%string)
    string = remove_format(string)
    string = string.replace('-',' ').replace('_',' ')
    string = re.sub(r'\d+','', string)
    string = string.strip()

    notilde = normalize(string)
    try:
        string = notilde.decode()
    except:
        pass
    string = string.lower()
    #logger.debug('sale de simplify: %s' % string)

    return string

def add_languages(title, languages):
    #logger.info()

    if isinstance(languages, list):
        for language in languages:
            title = '%s %s' % (title, set_color(language, language))
    else:
        title = '%s %s' % (title, set_color(languages, languages))
    return title

def add_info_plot(plot, languages, quality):
    #logger.info()
    last = '[/I][/B]\n'
    
    if languages:
        l_part = '[COLOR yellowgreen][B][I]Idiomas:[/COLOR] '
        mid = ''
        
        if isinstance(languages, list):
            for language in languages:
                mid += '%s ' % (set_color(language, language))
        else:
            mid = '%s ' % (set_color(languages, languages))
        
        p_lang = '%s%s%s' % (l_part, mid, last)
    
    if quality:
        q_part = '[COLOR yellowgreen][B][I]Calidad:[/COLOR] '
        p_quality = '%s%s%s' % (q_part, quality, last)
        
    if languages and quality:
        plot_ = '%s%s\n%s' % (p_lang, p_quality, plot)
    
    elif languages:
        plot_ = '%s\n%s' % (p_lang, plot)

    elif quality:
        plot_ = '%s\n%s' % (p_quality, plot)

    else: plot_ = plot

    return plot_

def set_color(title, category):
    #logger.info()
    from core import jsontools

    styles_path = os.path.join(config.get_runtime_path(), 'resources', 'color_styles.json')
    preset = config.get_setting("preset_style", default="Estilo 1")
    color_setting = jsontools.load((open(styles_path, "r").read()))[preset]

    color_scheme = {'otro': 'white', 'dual': 'white'}

    #logger.debug('category antes de remove: %s' % category)
    category = remove_format(category).lower()
    #logger.debug('category despues de remove: %s' % category)
    # Lista de elementos posibles en el titulo
    color_list = ['movie', 'tvshow', 'year', 'rating_1', 'rating_2', 'rating_3', 'quality', 'cast', 'lat', 'vose',
                  'vos', 'vo', 'server', 'library', 'update', 'no_update']

    # Se verifica el estado de la opcion de colores personalizados
    custom_colors = config.get_setting('title_color')

    # Se Forma el diccionario de colores para cada elemento, la opcion esta activas utiliza la configuracion del
    #  usuario, si no  pone el titulo en blanco.
    if title not in ['', ' ']:

        for element in color_list:
            if custom_colors:
                color_scheme[element] = remove_format(config.get_setting('%s_color' % element))
            else:
                color_scheme[element] = remove_format(color_setting.get(element, 'white'))
                #color_scheme[element] = 'white'

        if category in ['update', 'no_update']:
           #logger.debug('title antes de updates: %s' % title)
           title= re.sub(r'\[COLOR .*?\]','[COLOR %s]' % color_scheme[category],title)
        else:
            if category not in ['movie', 'tvshow', 'library', 'otro']:
                title = "[COLOR %s][%s][/COLOR]"%(color_scheme[category], title)
            else:
                title = "[COLOR %s]%s[/COLOR]" % (color_scheme[category], title)
    return title

def set_lang(language):
    #logger.info()

    cast =['castellano','espanol','cast','esp','espaol', 'es','zc', 'spa', 'spanish', 'vc']
    ita =['italiano','italian','ita','it']
    lat=['latino','lat','la', 'espanol latino', 'espaol latino', 'zl', 'mx', 'co', 'vl']
    vose=['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','subs castellano',
          'sub: español', 'vs', 'zs', 'vs', 'english-spanish subs', 'ingles sub espanol']
    vos=['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles']
    vo=['ingles', 'en','vo', 'ovos', 'eng','v.o', 'english']
    dual=['dual']

    language = scrapertools.decodeHtmlentities(language)
    old_lang = language

    language = simplify(language)

    #logger.debug('language before simplify: %s' % language)
    #logger.debug('old language: %s' % old_lang)
    if language in cast:
        language = 'cast'
    elif language in lat:
        language = 'lat'
    elif language in ita:
        language = 'ita'    
    elif language in vose:
        language = 'vose'
    elif language in vos:
        language = 'vos'
    elif language in vo:
        language = 'vo'
    elif language in dual:
        language = 'dual'
    else:
        language = 'otro'

    #logger.debug('language after simplify: %s' % language)

    return language





def title_format(item):
    #logger.info()

    lang = False
    valid = True
    language_color = 'otro'
    simple_language = ''

    #logger.debug('item.title antes de formatear: %s' % item.title.lower())

    # TODO se deberia quitar cualquier elemento que no sea un enlace de la lista de findvideos para quitar esto

    #Palabras "prohibidas" en los titulos (cualquier titulo que contengas estas no se procesara en unify)
    excluded_words = ['online', 'descarga', 'downloads', 'trailer', 'videoteca', 'gb', 'autoplay']

    # Actions excluidos, (se define canal y action) los titulos que contengan ambos valores no se procesaran en unify
    excluded_actions = [('videolibrary','get_episodes')]

    # Verifica el item sea valido para ser formateado por unify

    if item.channel == 'trailertools' or (item.channel.lower(), item.action.lower()) in excluded_actions or \
            item.action == '':
        valid = False
    else:
        for word in excluded_words:
            if word in item.title.lower():
                valid = False
                break
        if not valid:
            return item

    # Verifica si hay marca de visto de trakt

    visto = False
    #logger.debug('titlo con visto? %s' % item.title)

    if '[[I]v[/I]]' in item.title or '[COLOR limegreen][v][/COLOR]' in item.title:
        visto = True

    # Se elimina cualquier formato previo en el titulo
    if item.action != '' and item.action !='mainlist' and item.unify:
        item.title = remove_format(item.title)

    #logger.debug('visto? %s' % visto)

    # Evita que aparezcan los idiomas en los mainlist de cada canal
    if item.action == 'mainlist':
        item.language =''

    info = item.infoLabels
    #logger.debug('item antes de formatear: %s'%item)

    if hasattr(item,'text_color'):
        item.text_color=''



    if valid and item.unify!=False:

        # Formamos el titulo para serie, se debe definir contentSerieName
        # o show en el item para que esto funcione.
        if item.contentSerieName:

            # Si se tiene la informacion en infolabels se utiliza
            if item.contentType == 'episode' and info['episode'] != '':
                if info['title'] == '':
                    info['title'] = '%s - Episodio %s'% (info['tvshowtitle'], info['episode'])
                elif 'Episode' in info['title']:
                    episode = info['title'].lower().replace('episode', 'episodio')
                    info['title'] = '%s - %s' % (info['tvshowtitle'], episode.capitalize())
                elif info['episodio_titulo']!='':
                    #logger.debug('info[episode_titulo]: %s' % info['episodio_titulo'])
                    if 'episode' in info['episodio_titulo'].lower():
                        episode = info['episodio_titulo'].lower().replace('episode', 'episodio')
                        item.title = '%sx%s - %s' % (info['season'],info['episode'], episode.capitalize())
                    else:
                        item.title = '%sx%s - %s' % (info['season'], info['episode'], info['episodio_titulo'].capitalize())
                else:
                    item.title = '%sx%s - %s' % (info['season'],info['episode'], info['title'])
                item.title = set_color(item.title, 'tvshow')

            else:

                # En caso contrario se utiliza el titulo proporcionado por el canal
                #logger.debug ('color_scheme[tvshow]: %s' % color_scheme['tvshow'])
                item.title = '%s' % set_color(item.title, 'tvshow')

        elif item.contentTitle:
            # Si el titulo no tiene contentSerieName entonces se formatea como pelicula
            saga = False
            if 'saga' in item.title.lower():
                item.title = '%s [Saga]' % set_color(item.contentTitle, 'movie')
            elif 'miniserie' in item.title.lower():
                item.title = '%s [Miniserie]' % set_color(item.contentTitle, 'movie')
            elif 'extend' in item.title.lower():
                item.title = '%s [V.Extend.]' % set_color(item.contentTitle, 'movie')
            else:
                item.title = '%s' % set_color(item.contentTitle, 'movie')
            if item.contentType=='movie':
                if item.context:
                    if isinstance(item.context, list):
                        item.context.append('Buscar esta pelicula en otros canales')

        if ('Novedades' in item.category and item.from_channel=='news'):
            #logger.debug('novedades')
            item.title = '%s [%s]'%(item.title, item.channel)

        # Verificamos si item.language es una lista, si lo es se toma
        # cada valor y se normaliza formado una nueva lista

        if hasattr(item,'language') and item.language !='':
            #logger.debug('tiene language: %s'%item.language)
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

            #item.language = simple_language

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
        if item.quality and isinstance(item.quality, str):
            quality = item.quality.strip()
        else:
            quality = ''

        # Damos formato al idioma-calidad si existieran y los agregamos al plot
        quality_ = set_color(quality, 'quality')

        if (lang or quality) and item.action == "play":
            if hasattr(item, "clean_plot"):
                item.contentPlot = item.clear_plot

            if lang: item.title = add_languages(item.title, simple_language)
            if quality: item.title = '%s %s' % (item.title, quality_)
        
        elif (lang or quality) and item.action != "play":
            
            if item.contentPlot:
                item.clean_plot = item.contentPlot
                plot_ = add_info_plot(item.contentPlot, simple_language, quality_)
                item.contentPlot = plot_
            else:
                item.clean_plot = None
                plot_ = add_info_plot('', simple_language, quality_)
                item.contentPlot = plot_



        # Para las busquedas por canal
        if item.from_channel != '':
            from core import channeltools
            channel_parameters = channeltools.get_channel_parameters(item.from_channel)
            logger.debug(channel_parameters)
            item.title = '%s [%s]' % (item.title, channel_parameters['title'])


        # Formato para actualizaciones de series en la videoteca sobreescribe los colores anteriores

        if item.channel=='videolibrary' and item.context!='':
            if item.action=='get_seasons':
                if 'Desactivar' in item.context[1]['title']:
                    item.title= '%s' % (set_color(item.title, 'update'))
                if 'Activar' in item.context[1]['title']:
                    item.title= '%s' % (set_color(item.title, 'no_update'))

        #logger.debug('Despues del formato: %s' % item)
        # Damos formato al servidor si existiera
        if item.server:
            server = '%s' % set_color(item.server.strip().capitalize(), 'server')

        # Compureba si estamos en findvideos, y si hay server, si es asi no se muestra el
        # titulo sino el server, en caso contrario se muestra el titulo normalmente.

        #logger.debug('item.title antes de server: %s'%item.title)
        if item.action != 'play' and item.server:
            item.title ='%s %s'%(item.title, server.strip())

        elif item.action == 'play' and item.server:
            if hasattr(item, "clean_plot"):
                item.contentPlot = item.clean_plot

            if item.quality == 'default':
                quality = ''
            #logger.debug('language_color: %s'%language_color)
            item.title = '%s %s' % (server, set_color(quality,'quality'))
            if lang:
                item.title = add_languages(item.title, simple_language)
            #logger.debug('item.title: %s' % item.title)
            # Torrent_info
            if item.server == 'torrent' and item.torrent_info != '':
                item.title = '%s [%s]' % (item.title, item.torrent_info)

            if item.channel == 'videolibrary':
                item.title += ' [%s]' % item.contentChannel

            # si hay verificacion de enlaces
            if item.alive != '':
                if item.alive.lower() == 'no':
                    item.title = '[[COLOR red][B]X[/B][/COLOR]] %s' % item.title
                elif item.alive == '??':
                    item.title = '[[COLOR yellow][B]?[/B][/COLOR]] %s' % item.title
        else:
            item.title = '%s' % item.title

        #logger.debug('item.title despues de server: %s' % item.title)
    elif 'library' in item.action:
        item.title = '%s' % set_color(item.title, 'library')
    elif item.action == '' and item.title !='':
        item.title='**- %s -**'%item.title
    elif item.unify:
        item.title = '%s' % set_color(item.title, 'otro')
    #logger.debug('antes de salir %s' % item.title)
    if visto:
        try:
            check = u'\u221a'

            title = '[B][COLOR limegreen][%s][/COLOR][/B] %s' % (check, item.title.decode('utf-8'))
            item.title = title.encode('utf-8')
        except:
            check = 'v'
            title = '[B][COLOR limegreen][%s][/COLOR][/B] %s' % (check, item.title.decode('utf-8'))
            item.title = title.encode('utf-8')

    return item

def thumbnail_type(item):
    #logger.info()
    # Se comprueba que tipo de thumbnail se utilizara en findvideos,
    # Poster o Logo del servidor

    thumb_type = config.get_setting('video_thumbnail_type')
    info = item.infoLabels
    if not item.contentThumbnail:
        item.contentThumbnail = item.thumbnail

    if info:
        if info['thumbnail'] !='':
            item.contentThumbnail = info['thumbnail']

        if item.action == 'play':
            if thumb_type == 0:
                if info['thumbnail'] != '':
                    item.thumbnail = info['thumbnail']
            elif thumb_type == 1:
                from core.servertools import get_server_parameters
                #logger.debug('item.server: %s'%item.server)
                server_parameters = get_server_parameters(item.server.lower())
                item.thumbnail = server_parameters.get("thumbnail", item.contentThumbnail)

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
