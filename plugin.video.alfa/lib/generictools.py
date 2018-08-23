# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# GenericTools
# ------------------------------------------------------------
# Código reusable de diferentes partes de los canales que pueden
# ser llamadados desde otros canales, y así carificar el formato
# y resultado de cada canal y reducir el costo su mantenimiento
# ------------------------------------------------------------

import re
import sys
import urllib
import urlparse
import datetime

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import channeltools
from core import filetools
from core.item import Item
from platformcode import config, logger, platformtools
from core import tmdb

channel_py = "newpct1"
intervenido_judicial = 'Dominio intervenido por la Autoridad Judicial'
intervenido_policia = '<!--CATEGORY:Judicial_Policia_Nacional'
intervenido_guardia = '<!--CATEGORY:Judicial_Guardia_Civil'
intervenido_sucuri = 'Access Denied - Sucuri Website Firewall'


def update_title(item):
    logger.info()
    from core import scraper

    """
    Utilidad para desambiguar Títulos antes de añadirlos a la Videoteca.  Puede ser llamado desde Videolibrarytools
    o desde Episodios en un Canal.  Si se llama desde un canal, la llamada sería así (incluida en post_tmdb_episodios(item, itemlist)):
    
        #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
        item.from_action = item.action      #Salvamos la acción...
        item.from_title = item.title        #... y el título
        itemlist.append(item.clone(title="** [COLOR limegreen]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="episodios", tmdb_stat=False))
    
    El canal deberá añadir un método para poder recibir la llamada desde Kodi/Alfa, y poder llamar a este método:
    
    def actualizar_titulos(item):
        logger.info()
        itemlist = []
        from lib import generictools
        from platformcode import launcher
        
        item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
        
        #Volvemos a la siguiente acción en el canal
        return launcher.run(item)
    
    Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado, borrando los IDs existentes
    El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
    o puede cancelar e introducir un nuevo título en la segunda pantalla
    Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
    Si lo hace en "Completar Información", cambia al nuevo título, pero no busca en TMDB.  Hay que hacerlo de nuevo
    Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir
    """
    #logger.debug(item)
    
    #Restauramos y borramos las etiquetas intermedias (si se ha llamado desde el canal)
    if item.from_action:
        item.action = item.from_action
        del item.from_action
    if item.from_update:
        if item.from_title_tmdb:            #Si se salvó el título del contenido devuelto por TMDB, se restaura.
            item.title = item.from_title_tmdb
    else:
        item.add_videolibrary = True        #Estamos Añadiendo a la Videoteca.  Indicador para control de uso de los Canales
    if item.add_videolibrary:
        if item.season_colapse: del item.season_colapse
        if item.from_num_season_colapse: del item.from_num_season_colapse
        if item.from_title_season_colapse: del item.from_title_season_colapse
        if item.contentType == "movie":
            if item.from_title_tmdb:        #Si se salvó el título del contenido devuelto por TMDB, se restaura.
                item.title = item.from_title_tmdb
            del item.add_videolibrary
        if item.channel_host:               #Borramos ya el indicador para que no se guarde en la Videoteca
            del item.channel_host
        if item.contentTitle:
            item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
            item.title = re.sub(r' -%s-' % item.category, '', item.title)
    if item.contentType == 'movie':
        from_title_tmdb = item.contentTitle
    else:
        from_title_tmdb = item.contentSerieName
    
    #Sólo ejecutamos este código si no se ha hecho antes en el Canal.  Por ejemplo, si se ha llamado desde Episodios o Findvideos,
    #ya no se ejecutará al Añadia a Videoteca, aunque desde el canal se podrá llamar tantas veces como se quiera, 
    #o hasta que encuentre un título no ambiguo
    if item.tmdb_stat:
        if item.from_title_tmdb: del item.from_title_tmdb
        if item.from_title: del item.from_title
        item.from_update = True
        del item.from_update
        if item.contentType == "movie":
            if item.channel == channel_py:  #Si es una peli de NewPct1, ponemos el nombre del clone
                item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
    else:
        new_item = item.clone()             #Salvamos el Item inicial para restaurarlo si el usuario cancela
        if item.contentType == "movie":
            if item.channel == channel_py:  #Si es una peli de NewPct1, ponemos el nombre del clone
                item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
        #Borramos los IDs y el año para forzar a TMDB que nos pregunte
        if item.infoLabels['tmdb_id'] or item.infoLabels['tmdb_id'] == None: item.infoLabels['tmdb_id'] = ''
        if item.infoLabels['tvdb_id'] or item.infoLabels['tvdb_id'] == None: item.infoLabels['tvdb_id'] = ''
        if item.infoLabels['imdb_id'] or item.infoLabels['imdb_id'] == None: item.infoLabels['imdb_id'] = ''
        if item.infoLabels['season']: del item.infoLabels['season'] #Funciona mal con num. de Temporada.  Luego lo restauramos
        item.infoLabels['year'] = '-'
        
        if item.from_title:
            if item.from_title_tmdb:
                if scrapertools.find_single_match(item.from_title_tmdb, '^(?:\[COLOR \w+\])?(.*?)(?:\[)'):
                    from_title_tmdb = scrapertools.find_single_match(item.from_title_tmdb, '^(?:\[COLOR \w+\])?(.*?)(?:\[)').strip()
            item.title = item.title.replace(from_title_tmdb, item.from_title)
            item.infoLabels['title'] = item.from_title
            
            if item.from_title_tmdb: del item.from_title_tmdb
        if not item.from_update and item.from_title: del item.from_title

        if item.contentSerieName:           #Copiamos el título para que sirva de referencia en menú "Completar Información"
            item.infoLabels['originaltitle'] = item.contentSerieName
            item.contentTitle = item.contentSerieName
        else:
            item.infoLabels['originaltitle'] = item.contentTitle
            
        scraper_return = scraper.find_and_set_infoLabels(item)

        if not scraper_return:  #Si el usuario ha cancelado, restituimos los datos a la situación inicial y nos vamos
            item = new_item.clone()
        else:
            #Si el usuario ha cambiado los datos en "Completar Información" hay que ver el título definitivo en TMDB
            if not item.infoLabels['tmdb_id']:
                if item.contentSerieName:
                    item.contentSerieName = item.contentTitle                       #Se pone título nuevo
                item.infoLabels['noscrap_id'] = ''                                  #Se resetea, por si acaso
                item.infoLabels['year'] = '-'                                       #Se resetea, por si acaso
                scraper_return = scraper.find_and_set_infoLabels(item)              #Se intenta de nuevo

                #Parece que el usuario ha cancelado de nuevo.  Restituimos los datos a la situación inicial
                if not scraper_return or not item.infoLabels['tmdb_id']:
                    item = new_item.clone()
                else:
                    item.tmdb_stat = True           #Marcamos Item como procesado correctamente por TMDB (pasada 2)
            else:
                item.tmdb_stat = True               #Marcamos Item como procesado correctamente por TMDB (pasada 1)

            #Si el usuario ha seleccionado una opción distinta o cambiado algo, ajustamos los títulos
            if item.contentType != 'movie' or item.from_update:
                item.channel = new_item.channel     #Restuaramos el nombre del canal, por si lo habíamos cambiado
            if item.tmdb_stat == True:
                if new_item.contentSerieName:       #Si es serie...
                    if config.get_setting("filter_languages", item.channel) >= 0:
                        item.title_from_channel = new_item.contentSerieName         #Guardo el título incial para Filtertools
                        item.contentSerieName = new_item.contentSerieName           #Guardo el título incial para Filtertools
                    else:
                        item.title = item.title.replace(new_item.contentSerieName, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                        item.contentSerieName = item.contentTitle
                    if new_item.contentSeason: item.contentSeason = new_item.contentSeason      #Restauramos Temporada
                    if item.infoLabels['title']: del item.infoLabels['title']       #Borramos título de peli (es serie)
                else:                                                               #Si es película...
                    item.title = item.title.replace(new_item.contentTitle, item.contentTitle).replace(from_title_tmdb, item.contentTitle)
                if new_item.infoLabels['year']:                                     #Actualizamos el Año en el título
                    item.title = item.title.replace(str(new_item.infoLabels['year']), str(item.infoLabels['year']))
                if new_item.infoLabels['rating']:                                   #Actualizamos en Rating en el título
                    try:
                        rating_old = ''
                        if new_item.infoLabels['rating'] and new_item.infoLabels['rating'] != 0.0:
                            rating_old = float(new_item.infoLabels['rating'])
                            rating_old = round(rating_old, 1)
                        rating_new = ''
                        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
                            rating_new = float(item.infoLabels['rating'])
                            rating_new = round(rating_new, 1)
                        item.title = item.title.replace("[" + str(rating_old) + "]", "[" + str(rating_new) + "]")
                    except:
                        pass
                if item.wanted:                                                      #Actualizamos Wanted, si existe
                    item.wanted = item.contentTitle
                if new_item.contentSeason:                                           #Restauramos el núm. de Temporada después de TMDB
                    item.contentSeason = new_item.contentSeason
                    
                if item.from_update: 
                    item.from_update = True 
                    del item.from_update
                    platformtools.itemlist_update(item)
     
        #Para evitar el "efecto memoria" de TMDB, se le llama con un título ficticio para que resetee los buffers
        if item.contentSerieName:
            new_item.infoLabels['tmdb_id'] = '289'                                  #una serie no ambigua
        else:
            new_item.infoLabels['tmdb_id'] = '111'                                  #una peli no ambigua
        new_item.infoLabels['year'] = '-'
        if new_item.contentSeason:
            del new_item.infoLabels['season']                                       #Funciona mal con num. de Temporada
        scraper_return = scraper.find_and_set_infoLabels(new_item)
        
    #logger.debug(item)
    
    return item
    

def post_tmdb_listado(item, itemlist):
    logger.info()
    itemlist_fo = []
    
    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Listado y Listado_Búsqueda.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.
    
    También restaura varios datos salvados desde el título antes de pasarlo por TMDB, ya que mantenerlos no habría encontrado el título (title_subs)
    
    La llamada al método desde Listado o Listado_Buscar, despues de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    """
    #logger.debug(item)
    
    #Borramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel_alt:
        channel_alt = item.channel_alt
        del item.channel_alt
    if item.url_alt:
        del item.url_alt
    if item.extra2:
        del item.extra2
    #Ajustamos el nombre de la categoría
    if not item.category_new:
        item.category_new = ''
    item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()

    for item_local in itemlist:                                 #Recorremos el Itenlist generado por el canal
        title = item_local.title
        #logger.debug(item_local)
        
        item_local.last_page = 0
        del item_local.last_page                                #Borramos restos de paginación

        if item_local.contentSeason_save:                       #Restauramos el num. de Temporada
            item_local.contentSeason = item_local.contentSeason_save

        #Borramos valores para cada Contenido si ha habido fail-over
        if item_local.channel_alt:
            del item_local.channel_alt
        if item_local.url_alt:
            del item_local.url_alt
        if item_local.extra2:
            del item_local.extra2
        
        #Ajustamos el nombre de la categoría
        item_local.category = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        
        #Restauramos la info adicional guarda en la lista title_subs, y la borramos de Item
        title_add = ' '
        if item_local.title_subs:
            for title_subs in item_local.title_subs:
                if "audio" in title_subs.lower():                   #se restaura info de Audio
                    title_add += scrapertools.find_single_match(title_subs, r'[a|A]udio (.*?)')
                    continue
                if scrapertools.find_single_match(title_subs, r'(\d{4})'):      #Se restaura el año, s no lo ha dado TMDB
                    if not item_local.infoLabels['year'] or item_local.infoLabels['year'] == "-":
                        item_local.infoLabels['year'] = scrapertools.find_single_match(title_subs, r'(\d{4})')
                    continue

                title_add = title_add.rstrip()
                title_add = '%s -%s-' % (title_add, title_subs)     #se agregan el resto de etiquetas salvadas
        item_local.title_subs = []
        del item_local.title_subs

        #Preparamos el Rating del vídeo
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            pass

        # Si TMDB no ha encontrado el vídeo limpiamos el año
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
            
        # Si TMDB no ha encontrado nada y hemos usado el año de la web, lo intentamos sin año
        if not item_local.infoLabels['tmdb_id']:
            if item_local.infoLabels['year']:                                   #lo intentamos de nuevo solo si había año, puede que erroneo
                year = item_local.infoLabels['year']                            #salvamos el año por si no tiene éxito la nueva búsqueda
                item_local.infoLabels['year'] = "-"                             #reseteo el año
                try:
                    tmdb.set_infoLabels(item_local, True)                       #pasamos otra vez por TMDB
                except:
                    pass
                if not item_local.infoLabels['tmdb_id']:                        #ha tenido éxito?
                    item_local.infoLabels['year'] = year                        #no, restauramos el año y lo dejamos ya

        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        if item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        if item_local.from_title:
            if item_local.contentType == 'movie':
                item_local.contentTitle = item_local.from_title
                item_local.title = item_local.from_title
            else:
                item_local.contentSerieName = item_local.from_title
            if item_local.contentType == 'season':
                item_local.title = item_local.from_title
        
        # Preparamos el título para series, con los núm. de temporadas, si las hay
        if item_local.contentType in ['season', 'tvshow', 'episode']:
            if item_local.contentType == "episode":
                if "Temporada" in title:     #Compatibilizamos "Temporada" con Unify
                    title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
                if " al " in title:        #Si son episodios múltiples, ponemos nombre de serie
                    if " al 99" in title.lower():   #Temporada completa.  Buscamos num total de episodios
                        title = title.replace("99", str(item_local.infoLabels['temporada_num_episodios']))
                    title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
                elif item_local.infoLabels['episodio_titulo']:
                    title = '%s %s, %s' % (title, item_local.infoLabels['episodio_titulo'], item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s- %s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.contentSerieName, item_local.infoLabels['year'], rating)
                    
                else:       #Si no hay título de episodio, ponermos el nombre de la serie
                    if item_local.contentSerieName not in title:
                        title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)
                    
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    if "Episodio" in title_add:
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, 'Episodio (\d+)x(\d+)')
                        title = '%s [%s] [%s]' % (title, item_local.infoLabels['year'], rating)

            elif item_local.contentType == "season":
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, '-(\d+)x')
                if not item_local.contentSeason:
                    item_local.contentSeason = scrapertools.find_single_match(item_local.url, '-temporadas?-(\d+)')
                if item_local.contentSeason:
                    title = '%s -Temporada %s' % (title, str(item_local.contentSeason))
                    if not item_local.contentSeason_save:                           #Restauramos el num. de Temporada
                        item_local.contentSeason_save = item_local.contentSeason    #Y lo volvemos a salvar
                    del item_local.infoLabels['season']         #Funciona mal con num. de Temporada.  Luego lo restauramos
                else:
                    title = '%s -Temporada !!!' % (title)

            elif item.action == "search":
                title += " -Serie-"
        
        if (item_local.extra == "varios" or item_local.extra == "documentales") and (item.action == "search" or item.action == "listado_busqueda"):
            title += " -Varios-"
            item_local.contentTitle += " -Varios-"
        
        title += title_add                  #Se añaden etiquetas adicionales, si las hay

        #Ahora maquillamos un poco los titulos dependiendo de si se han seleccionado títulos inteleigentes o no
        if not config.get_setting("unify"):         #Si Titulos Inteligentes NO seleccionados:
            title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_local.infoLabels['year']), rating, item_local.quality, str(item_local.language))

        else:                                       #Si Titulos Inteligentes SÍ seleccionados:
            title = title.replace("[", "-").replace("]", "-").replace(".", ",")
        
        #Limpiamos las etiquetas vacías
        if item_local.infoLabels['episodio_titulo']:
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace(" []", "").strip()
        title = title.replace("--", "").replace(" []", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', title).strip()
        title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', title).strip()
    
        if item.category_new == "newest":       #Viene de Novedades.  Marcamos el título con el nombre del canal
            title += ' -%s-' % scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            if item_local.contentType == "movie": 
                item_local.contentTitle += ' -%s-' % scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            elif "Episodio " in title:
                if not item_local.contentSeason or not item_local.contentEpisodeNumber:
                    item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title_add, 'Episodio (\d+)x(\d+)')

        item_local.title = title
        
        #logger.debug("url: " + item_local.url + " / title: " + item_local.title + " / content title: " + item_local.contentTitle + "/" + item_local.contentSerieName + " / calidad: " + item_local.quality + "[" + str(item_local.language) + "]" + " / year: " + str(item_local.infoLabels['year']))
        
        #logger.debug(item_local)
    
    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt and item.category_new != "newest":
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] inaccesible'))
    
    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist
        
    del item.category_new
        
    return (item, itemlist)


def post_tmdb_seasons(item, itemlist):
    logger.info()
    
    """
        
    Pasada para gestión del menú de Temporadas de una Serie
    
    La clave de activación de este método es la variable item.season_colapse que pone el canal en el Item de Listado.
    Esta variable tendrá que desaparecer cuando se aña a la Videoteca para que se analicen los episodios de la forma tradicional
    
    Repasa todos los episodios producidos en itemlist por "episodios" del canal para extraer las temporadas.  Pone un título para Todas la Temps.
    Crea un menú con las diferentes temporadas, así como con los títulos de Actualización de Título y de Añadir a Videoteca
    Si ha habido un Fail-over o una Intervención Judicial, también lo anuncia
    
    La llamada al método desde Episodios, antes de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)
        
    Si solo hay una temporada, devuelte el itemlist original para que se pinten los episodios de la forma tradicional
    
    """
    #logger.debug(item)
    
    season = 0
    itemlist_temporadas = []
    itemlist_fo = []
    
    #Restauramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel == channel_py:
        if item.channel_alt:
            channel_alt = item.category
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    else:
        if item.channel_alt:
            channel_alt = item.channel
            item.channel = item.channel_alt
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt
    
    # Primero creamos un título para TODAS las Temporadas
    # Pasada por TMDB a Serie, para datos adicionales
    try:
        tmdb.set_infoLabels(item, True)                             #TMDB de cada Temp
    except:
        pass
    
    item_season = item.clone()
    if item_season.season_colapse:                                  #Quitamos el indicador de listado por Temporadas
        del item_season.season_colapse
    title = '** Todas las Temporadas'                               #Agregamos título de TODAS las Temporadas (modo tradicional)
    if item_season.infoLabels['number_of_episodes']:                #Ponemos el núm de episodios de la Serie
        title += ' [%s epi]' % str(item_season.infoLabels['number_of_episodes'])
    
    rating = ''                                                     #Ponemos el rating, si es diferente del de la Serie
    if item_season.infoLabels['rating'] and item_season.infoLabels['rating'] != 0.0:
        try:
            rating = float(item_season.infoLabels['rating'])
            rating = round(rating, 1)
        except:
            pass
    if rating and rating == 0.0:
        rating = ''
    
    if not config.get_setting("unify"):                             #Si Titulos Inteligentes NO seleccionados:
        title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_season.infoLabels['year']), rating, item_season.quality, str(item_season.language))
    else:                                                           #Lo arreglamos un poco para Unify
        title = title.replace('[', '-').replace(']', '-').replace('.', ',').strip()
    title = title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
    
    itemlist_temporadas.append(item_season.clone(title=title, from_title_season_colapse=item.title))
    
    #Repasamos todos los episodios para detectar las diferentes temporadas
    for item_local in itemlist:
        if item_local.contentSeason != season:
            season = item_local.contentSeason                       #Si se detecta una temporada distinta se prepara un título
            item_season = item.clone()
            item_season.contentSeason = item_local.contentSeason    #Se pone el núm de Temporada para obtener mejores datos de TMDB
            item_season.title = 'Temporada %s' % item_season.contentSeason
            itemlist_temporadas.append(item_season.clone(from_title_season_colapse=item.title))
            
    #Si hay más de una temporada se sigue, si no se devuelve el Itemlist original
    if len(itemlist_temporadas) > 2:
        for item_local in itemlist_temporadas:
            if "** Todas las Temporadas" in item_local.title:       #Si es el título de TODAS las Temporadas, lo ignoramos
                continue
            
            # Pasada por TMDB a las Temporada
            try:
                tmdb.set_infoLabels(item_local, True)               #TMDB de cada Temp
            except:
                pass
        
            if item_local.infoLabels['temporada_air_date']:         #Fecha de emisión de la Temp
                item_local.title += ' [%s]' % str(scrapertools.find_single_match(str(item_local.infoLabels['temporada_air_date']), r'\/(\d{4})'))
            
            #rating = ''                                            #Ponemos el rating, si es diferente del de la Serie
            #if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
            #    try:
            #        rating = float(item_local.infoLabels['rating'])
            #        rating = round(rating, 1)
            #    except:
            #        pass
            #if rating and rating > 0.0:
            #    item_local.title += ' [%s]' % str(rating)
            
            if item_local.infoLabels['temporada_num_episodios']:    #Núm. de episodios de la Temp
                item_local.title += ' [%s epi]' % str(item_local.infoLabels['temporada_num_episodios'])
                
            if not config.get_setting("unify"):                     #Si Titulos Inteligentes NO seleccionados:
                item_local.title = '%s [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.quality, str(item_local.language))
            else:                                                   #Lo arreglamos un poco para Unify
                item_local.title = item_local.title.replace('[', '-').replace(']', '-').replace('.', ',').strip()
            item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
            
            #logger.debug(item_local)
        
    else:                                                           #Si hay más de una temporada se sigue, si no se devuelve el Itemlist original
        if item.season_colapse:
            del item.season_colapse
        return (item, itemlist)
    
    #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
    itemlist_temporadas.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))
    
    #Es un canal estándar, sólo una linea de Añadir a Videoteca
    title = ''
    if item.infoLabels['status'] and item.infoLabels['status'].lower() == "ended":
        title += ' [TERMINADA]'
    itemlist_temporadas.append(item_season.clone(title="[COLOR yellow]Añadir esta serie a videoteca-[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))

    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() + '[/COLOR] inaccesible'))
    
    if len(itemlist_fo) > 0:
        itemlist_temporadas = itemlist_fo + itemlist_temporadas
    
    return (item, itemlist_temporadas)
    
    
def post_tmdb_episodios(item, itemlist):
    logger.info()
    itemlist_fo = []
        
    """
        
    Pasada para maquillaje de los títulos obtenidos desde TMDB en Episodios.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título
    para que sea compatible con Unify, y si no se tienen Títulos Inteligentes, para que el formato sea lo más
    parecido al de Unify.

    Lleva un control del num. de episodios por temporada, tratando de arreglar los errores de la Web y de TMDB
    
    La llamada al método desde Episodios, despues de pasar Itemlist pot TMDB, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    """
    #logger.debug(item)
    
    modo_serie_temp = ''
    if config.get_setting('seleccionar_serie_temporada', item.channel) >= 0:
        modo_serie_temp = config.get_setting('seleccionar_serie_temporada', item.channel)
    modo_ultima_temp = ''
    if config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is True or config.get_setting('seleccionar_ult_temporadda_activa', item.channel) is False:
        modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel)

    #Inicia variables para el control del núm de episodios por temporada
    num_episodios = 1
    num_episodios_lista = []
    for i in range(0, 50):  num_episodios_lista += [0]
    num_temporada = 1
    num_temporada_max = 99
    num_episodios_flag = True
    
    #Restauramos el num de Temporada para hacer más flexible la elección de Videoteca
    contentSeason = item.contentSeason
    if item.contentSeason_save:
        contentSeason = item.contentSeason_save
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save

    #Ajustamos el nombre de la categoría
    item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
    
    #Restauramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel == channel_py:
        if item.channel_alt:
            channel_alt = item.category
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    else:
        if item.channel_alt:
            channel_alt = item.channel
            item.channel = item.channel_alt
            item.category = item.channel_alt.capitalize()
            del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt
    if item.title_from_channel:
        del item.title_from_channel
    if item.ow_force:
        del item.ow_force
    if item.season_colapse:
        del item.season_colapse
        
    for item_local in itemlist:                     #Recorremos el Itemlist generado por el canal
        if item_local.add_videolibrary:
            del item_local.add_videolibrary
        if item_local.add_menu:
            del item_local.add_menu
        if item_local.contentSeason_save:
            del item_local.contentSeason_save
        if item_local.title_from_channel:
            del item_local.title_from_channel
        if item_local.library_playcounts:
            del item_local.library_playcounts
        if item_local.library_urls:
            del item_local.library_urls
        if item_local.path:
            del item_local.path
        if item_local.nfo:
            del item_local.nfo
        if item_local.update_last:
            del item_local.update_last
        if item_local.update_next:
            del item_local.update_next
        if item_local.channel_host:
            del item_local.channel_host         
        if item_local.intervencion:
            del item_local.intervencion
        if item_local.ow_force:
            del item_local.ow_force
        if item_local.season_colapse:
            del item_local.season_colapse
        #logger.debug(item_local)
        
        #Ajustamos el nombre de la categoría si es un clone de NewPct1
        item_local.category = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
        
        #Restauramos valores para cada Episodio si ha habido fail-over de un clone de NewPct1
        if item_local.channel == channel_py:
            if item_local.channel_alt:
                item_local.category = item_local.channel_alt
                del item_local.channel_alt
        else:
            if item_local.channel_alt:
                item_local.channel = item_local.channel_alt
                del item_local.channel_alt
        if item_local.url_alt:
            host_act = scrapertools.find_single_match(item_local.url, ':\/\/(.*?)\/')
            host_org = scrapertools.find_single_match(item_local.url_alt, ':\/\/(.*?)\/')
            item_local.url = item_local.url.replace(host_act, host_org)
            del item_local.url_alt
            
        #Si está actualizando videoteca de una serie NewPct1, restauramos el channel con el nombre del clone
        if item_local.channel == channel_py and (item.library_playcounts or item.add_videolibrary):
            item_local.channel = scrapertools.find_single_match(item_local.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
        
        #Si el título de la serie está verificado en TMDB, se intenta descubrir los eisodios fuera de rango,
        #que son probables errores de la Web
        if item.tmdb_stat:
            if item_local.infoLabels['number_of_seasons']:
                #Si el num de temporada está fuera de control, se pone 0, y se reclasifica itemlist
                if item_local.contentSeason > item_local.infoLabels['number_of_seasons'] + 1:
                    logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(item_local.infoLabels['number_of_seasons']) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
                else:
                    num_temporada_max = item_local.infoLabels['number_of_seasons']
            else:
                if item_local.contentSeason > num_temporada_max + 1:
                    logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(num_temporada_max) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
                    item_local.contentSeason = 0
                    itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
        
        #Salvamos en número de episodios de la temporada
        try:
            if num_temporada != item_local.contentSeason:
                num_temporada = item_local.contentSeason
                num_episodios = 0
            if item_local.infoLabels['temporada_num_episodios'] and int(item_local.infoLabels['temporada_num_episodios']) > int(num_episodios):
                num_episodios = item_local.infoLabels['temporada_num_episodios']
        except:
            num_episodios = 0
        
        #Preparamos el Rating del vídeo
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != 0.0:
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
                if rating == 0.0:
                    rating = ''
        except:
            pass
        
        # Si TMDB no ha encontrado el vídeo limpiamos el año
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        elif item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')

        #Preparamos el título para que sea compatible con Añadir Serie a Videoteca           
        if "Temporada" in item_local.title:             #Compatibilizamos "Temporada" con Unify
            item_local.title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
        if " al " in item_local.title:                  #Si son episodios múltiples, ponemos nombre de serie
            if " al 99" in item_local.title.lower():    #Temporada completa.  Buscamos num total de episodios de la temporada
                item_local.title = item_local.title.replace("99", str(num_episodios))
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s - %s [%s] [%s]' % (scrapertools.find_single_match(item_local.title, r'(al \d+)'), item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
        elif item_local.infoLabels['episodio_titulo']:
            item_local.title = '%s %s' % (item_local.title, item_local.infoLabels['episodio_titulo']) 
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.infoLabels['year'], rating)
            
        else:       #Si no hay título de episodio, ponermos el nombre de la serie
            item_local.title = '%s %s' % (item_local.title, item_local.contentSerieName)
            item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)
        
        #Componemos el título final, aunque con Unify usará infoLabels['episodio_titulo']
        item_local.infoLabels['title'] = item_local.infoLabels['episodio_titulo']
        item_local.title = '%s [%s] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.title, item_local.infoLabels['year'], rating, item_local.quality, str(item_local.language))
    
        #Quitamos campos vacíos
        item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace(" []", "").strip()
        item_local.infoLabels['title'] = item_local.infoLabels['title'].replace(" []", "").strip()
        item_local.title = item_local.title.replace(" []", "").strip()
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip()
        item_local.title = re.sub(r'\s\[COLOR \w+\]-\[\/COLOR\]', '', item_local.title).strip()
        
        #Si la información de num. total de episodios de TMDB no es correcta, tratamos de calcularla
        if num_episodios < item_local.contentEpisodeNumber:
            num_episodios = item_local.contentEpisodeNumber
        if num_episodios > item_local.contentEpisodeNumber:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        if num_episodios and not item_local.infoLabels['temporada_num_episodios']:
            item_local.infoLabels['temporada_num_episodios'] = num_episodios
            num_episodios_flag = False
        num_episodios_lista[item_local.contentSeason] = num_episodios

        #logger.debug("title: " + item_local.title + " / url: " + item_local.url + " / calidad: " + item_local.quality + " / Season: " + str(item_local.contentSeason) + " / EpisodeNumber: " + str(item_local.contentEpisodeNumber) + " / num_episodios_lista: " + str(num_episodios_lista) + str(num_episodios_flag))
        #logger.debug(item_local)
    
    #Si está actualizando videoteca de una serie NewPct1, restauramos el channel con el nombre del clone
    if item.channel == channel_py and (item.library_playcounts or item.add_videolibrary):
        item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/')
    
    #Terminado el repaso de cada episodio, cerramos con el pié de página
    #En primer lugar actualizamos todos los episodios con su núm máximo de episodios por temporada
    try:
        if not num_episodios_flag:  #Si el num de episodios no está informado, acualizamos episodios de toda la serie
            for item_local in itemlist:
                item_local.infoLabels['temporada_num_episodios'] = int(num_episodios_lista[item_local.contentSeason])
    except:
        logger.error("ERROR 07: EPISODIOS: Num de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(num_temporada_max) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
    
    #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
    itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))
    
    #Borro num. Temporada si no viene de menú de Añadir a Videoteca y no está actualizando la Videoteca
    if not item.library_playcounts:                     #si no está actualizando la Videoteca
        if modo_serie_temp != '':                       #y puede cambiara a serie-temporada
            if item.contentSeason and not item.add_menu:
                del item.infoLabels['season']               #La decisión de ponerlo o no se toma en la zona de menús

    #Ponemos el título de Añadir a la Videoteca, con el núm. de episodios de la última temporada y el estado de la Serie
    if config.get_videolibrary_support() and len(itemlist) > 1:
        item_local = itemlist[-2]
        title = ''
        
        if item_local.infoLabels['temporada_num_episodios']:
            title += ' [Temp. de %s ep.]' % item_local.infoLabels['temporada_num_episodios']
            
        if item_local.infoLabels['status'] and item_local.infoLabels['status'].lower() == "ended":
            title += ' [TERMINADA]'
            
        if item_local.quality:      #La Videoteca no toma la calidad del episodio, sino de la serie.  Pongo del episodio
            item.quality = item_local.quality
        
        if modo_serie_temp != '':
            #Estamos en un canal que puede seleccionar entre gestionar Series completas o por Temporadas
            #Tendrá una línea para Añadir la Serie completa y otra para Añadir sólo la Temporada actual

            if item.action == 'get_seasons':        #si es actualización desde videoteca, título estándar
                #Si hay una nueva Temporada, se activa como la actual
                if item.library_urls[item.channel] != item.url and (item.contentType == "season" or modo_ultima_temp):
                    item.library_urls[item.channel] = item.url          #Se actualiza la url apuntando a la última Temporada
                    try:
                        from core import videolibrarytools              #Se fuerza la actualización de la url en el .nfo
                        itemlist_fake = []                              #Se crea un Itemlist vacio para actualizar solo el .nfo
                        videolibrarytools.save_tvshow(item, itemlist_fake)      #Se actualiza el .nfo
                    except:
                        logger.error("ERROR 08: EPISODIOS: No se ha podido actualizar la URL a la nueva Temporada")
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + title, action="add_serie_to_library"))
                
            elif modo_serie_temp == 1:      #si es Serie damos la opción de guardar la última temporada o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir última Temp. a Videoteca-[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, url=item_local.url, add_menu=True))
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))

            else:                           #si no, damos la opción de guardar la temporada actual o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca-[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))
                if item.add_videolibrary and not item.add_menu:
                    item.contentSeason = contentSeason
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Temp. a Videoteca-[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, add_menu=True))

        else:   #Es un canal estándar, sólo una linea de Añadir a Videoteca
            itemlist.append(item.clone(title="[COLOR yellow]Añadir esta serie a videoteca-[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))
        
    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Si ha habido fail-over, lo comento
    if channel_alt:
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
        itemlist_fo.append(item.clone(action='', title="[COLOR yellow]" + item.category.capitalize() + '[/COLOR] inaccesible'))
    
    if len(itemlist_fo) > 0:
        itemlist = itemlist_fo + itemlist

    if item.add_videolibrary:               #Estamos Añadiendo a la Videoteca.
        del item.add_videolibrary           #Borramos ya el indicador
        if item.add_menu:                   #Opción que avisa si se ha añadido a la Videoteca 
            del item.add_menu               #desde la página de Episodios o desde Menú Contextual   

    #logger.debug(item)
    
    return (item, itemlist)
    
    
def post_tmdb_findvideos(item, itemlist):
    logger.info()
    
    """
        
    Llamada para crear un pseudo título con todos los datos relevantes del vídeo.
    
    Toma de infoLabel todos los datos de interés y los va situando en diferentes variables, principalmente título. Lleva un control del num. de episodios por temporada
    
    La llamada al método desde Findvideos, al principio, es:
    
        from lib import generictools
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
        
    En Itemlist devuelve un Item con el pseudotítulo.  Ahí el canal irá agregando el resto.
    
    """
    #logger.debug(item)
    
    #Creción de título general del vídeo a visualizar en Findvideos
    itemlist = []
    
    # Saber si estamos en una ventana emergente lanzada desde una viñeta del menú principal,
    # con la función "play_from_library"
    item.unify = False
    try:
        import xbmc
        if xbmc.getCondVisibility('Window.IsMedia') == 1:
            item.unify = config.get_setting("unify")
    except:
        item.unify = config.get_setting("unify")
    
    if item.contentSeason_save:                                     #Restauramos el num. de Temporada
        item.contentSeason = item.contentSeason_save
        del item.contentSeason_save

    #Salvamos la información de max num. de episodios por temporada para despues de TMDB
    num_episodios = item.contentEpisodeNumber
    if item.infoLabels['temporada_num_episodios'] and item.contentEpisodeNumber <= item.infoLabels['temporada_num_episodios']:
        num_episodios = item.infoLabels['temporada_num_episodios']

    # Obtener la información actualizada del vídeo.  En una segunda lectura de TMDB da más información que en la primera
    #if not item.infoLabels['tmdb_id'] or (not item.infoLabels['episodio_titulo'] and item.contentType == 'episode'):
    #    tmdb.set_infoLabels(item, True)
    #elif (not item.infoLabels['tvdb_id'] and item.contentType == 'episode') or item.contentChannel == "videolibrary":
    #    tmdb.set_infoLabels(item, True)
    try:
        tmdb.set_infoLabels(item, True)                             #TMDB de cada Temp
    except:
        pass
    #Restauramos la información de max num. de episodios por temporada despues de TMDB
    try:
        if item.infoLabels['temporada_num_episodios']:
            if int(num_episodios) > int(item.infoLabels['temporada_num_episodios']):
                item.infoLabels['temporada_num_episodios'] = num_episodios
        else:
            item.infoLabels['temporada_num_episodios'] = num_episodios
    except:
        pass

    #Quitamos el la categoría o nombre del título, si lo tiene
    if item.contentTitle:
        item.contentTitle = re.sub(r' -%s-' % item.category, '', item.contentTitle)
        item.title = re.sub(r' -%s-' % item.category, '', item.title)
    
    #Limpiamos de año y rating de episodios
    if item.infoLabels['episodio_titulo']:
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\[.*?\]', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\(.*?\)', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = item.infoLabels['episodio_titulo'].replace(item.contentSerieName, '')
    if item.infoLabels['aired'] and item.contentType == "episode":
        item.infoLabels['year'] = scrapertools.find_single_match(str(item.infoLabels['aired']), r'\/(\d{4})')

    rating = ''     #Ponemos el rating
    try:
        if item.infoLabels['rating'] and item.infoLabels['rating'] != 0.0:
            rating = float(item.infoLabels['rating'])
            rating = round(rating, 1)
            if rating == 0.0:
                    rating = ''
    except:
        pass

    if item.quality.lower() in ['gb', 'mb']:
        item.quality = item.quality.replace('GB', 'G B').replace('Gb', 'G b').replace('MB', 'M B').replace('Mb', 'M b')

    #busco "duration" en infoLabels
    tiempo = 0
    if item.infoLabels['duration']:
        tiempo = item.infoLabels['duration']
    
    elif item.contentChannel == 'videolibrary':                                     #No hay, viene de la Videoteca? buscamos en la DB
    #Leo de la BD de Kodi la duración de la película o episodio.  En "from_fields" se pueden poner las columnas que se quiera
        nun_records = 0
        try:
            if item.contentType == 'movie':
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c11')  #Leo de la BD de Kodi la duración de la película
            else:
                nun_records, records = get_field_from_kodi_DB(item, from_fields='c09')  #Leo de la BD de Kodi la duración del episodio
        except:
            pass
        if nun_records > 0:                                                         #Hay registros?
            #Es un array, busco el campo del registro: añadir en el FOR un fieldX por nueva columna
            for strFileName, field1 in records: 
                tiempo = field1

    try:                                                                                #calculamos el timepo en hh:mm
        tiempo_final = int(tiempo)                                                      #lo convierto a int, pero puede se null
        if tiempo_final > 0:                                                            #Si el tiempo está a 0, pasamos
            if tiempo_final > 700:                                                      #Si está en segundos
                tiempo_final = tiempo_final / 60                                        #Lo transformo a minutos
            horas = tiempo_final / 60                                                   #Lo transformo a horas
            resto = tiempo_final - (horas * 60)                                         #guardo el resto de minutos de la hora
            if not scrapertools.find_single_match(item.quality, '(\[\d+:\d+)'):         #si ya tiene la duración, pasamos
                item.quality += ' [COLOR white][%s:%s h]' % (str(horas).zfill(2), str(resto).zfill(2))     #Lo agrego a Calidad del Servidor
    except:
        pass
        
    #Ajustamos el nombre de la categoría
    if item.channel != channel_py:
        item.category = item.channel.capitalize()
    
    #Formateamos de forma especial el título para un episodio
    title = ''
    title_gen = ''
    if item.contentType == "episode":                   #Series
        title = '%sx%s' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))    #Temporada y Episodio
        if item.infoLabels['temporada_num_episodios']:
            title = '%s (de %s)' % (title, str(item.infoLabels['temporada_num_episodios']))     #Total Episodios
        
        #Si son episodios múltiples, y viene de Videoteca, ponemos nombre de serie        
        if (" al " in item.title or " Al " in item.title) and not "al " in item.infoLabels['episodio_titulo']: 
            title = '%s al %s - ' % (title, scrapertools.find_single_match(item.title, '[al|Al] (\d+)'))
        else:
            title = '%s %s' % (title, item.infoLabels['episodio_titulo'])                       #Título Episodio
        title_gen = '%s, ' % title
        
    if item.contentType == "episode" or item.contentType == "season":                           #Series o Temporadas
        title_gen += '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] [%s]' % (item.contentSerieName, item.infoLabels['year'], rating, item.quality, str(item.language), scrapertools.find_single_match(item.title, '\s\[(\d+,?\d*?\s\w[b|B])\]'))                                                #Rating, Calidad, Idioma, Tamaño                
        if item.infoLabels['status'] and item.infoLabels['status'].lower() == "ended":
            title_gen = '[TERM.] %s' % title_gen        #Marca cuando la Serie está terminada y no va a haber más producción
        item.title = title_gen

    else:                                               #Películas
        title = item.title
        title_gen = item.title

    #Limpiamos etiquetas vacías
    title_gen = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', title_gen).strip()  #Quitamos etiquetas vacías
    title_gen = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', title_gen).strip()            #Quitamos colores vacíos
    title_gen = title_gen.replace(" []", "").strip()                                    #Quitamos etiquetas vacías
    title_videoteca = title_gen                                                         #Salvamos el título para Videoteca

    if not item.unify:      #Si Titulos Inteligentes NO seleccionados:
        title_gen = '**- [COLOR gold]Enlaces Ver: [/COLOR]%s[COLOR gold] -**[/COLOR]' % (title_gen)
    else:                   #Si Titulos Inteligentes SÍ seleccionados:
        title_gen = '[COLOR gold]Enlaces Ver: [/COLOR]%s' % (title_gen)    

    if item.channel_alt:
        title_gen = '[COLOR yellow]%s [/COLOR][ALT]: %s' % (item.category.capitalize(), title_gen)
    elif (config.get_setting("quit_channel_name", "videolibrary") == 1 or item.channel == channel_py) and item.contentChannel == "videolibrary":
        title_gen = '%s: %s' % (item.category.capitalize(), title_gen)

    #Si intervención judicial, alerto!!!
    if item.intervencion:
        for clone_inter, autoridad in item.intervencion:
            thumb_intervenido = get_thumb(autoridad)
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
        del item.intervencion
    
    #Pintamos el pseudo-título con toda la información disponible del vídeo
    itemlist.append(item.clone(action="", server = "", title=title_gen))		#Título con todos los datos del vídeo
    
    if item.action == 'show_result':                                            #Viene de una búsqueda global
        channel = item.channel.capitalize()
        if item.from_channel == channel_py or item.channel == channel_py:
            channel = item.category
        elif item.from_channel:
            channel = item.from_channel.capitalize()
        item.quality = '[COLOR yellow][%s][/COLOR] %s' % (channel, item.quality)
    
    #agregamos la opción de Añadir a Videoteca para péliculas (no series)
    if (item.contentType == 'movie' or item.contentType == 'season') and item.contentChannel != "videolibrary":
        #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
        itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="películas", tmdb_stat=False, from_action=item.action, from_title_tmdb=item.title, from_update=True))
        
    if item.contentType == 'movie' and item.contentChannel != "videolibrary":
        itemlist.append(item.clone(title="**-[COLOR yellow] Añadir a la videoteca [/COLOR]-**", action="add_pelicula_to_library", extra="películas", from_action=item.action, from_title_tmdb=item.title))
    
    #Añadimos la opción de ver trailers
    if item.contentChannel != "videolibrary":
        itemlist.append(item.clone(channel="trailertools", title="**-[COLOR magenta] Buscar Trailer [/COLOR]-**", action="buscartrailer", context=""))
    
    #logger.debug(item)
    
    return (item, itemlist)
    

def get_field_from_kodi_DB(item, from_fields='*', files='file'):
    logger.info()
    """
        
    Llamada para leer de la DB de Kodi los campos que se reciben de entrada (from_fields, por defecto "*") del vídeo señalado en Item
    Obviamente esto solo funciona con Kodi y si la película o serie está catalogada en las Videotecas de Alfa y Kodi
    Se puede pedir que la búdqueda se haga por archivos (defecto), o por carpeta (series)
    
    La llamada es:
        nun_records, records = generictools.get_field_from_kodi_DB(item, from_fields='cXX[, cYY,...]'[, files = 'file|folder'])
    
    Devuelve el num de registros encontrados y los registros.  Es importante que el llamador verifique que "nun_records > 0" antes de tratar "records"
    
    """

    FOLDER_MOVIES = config.get_setting("folder_movies")
    FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
    VIDEOLIBRARY_PATH = config.get_videolibrary_config_path()
    VIDEOLIBRARY_REAL_PATH = config.get_videolibrary_path()
    
    if item.contentType == 'movie':                                     #Agrego la carpeta correspondiente al path de la Videoteca
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_MOVIES)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
        folder = FOLDER_MOVIES
    else:
        path = filetools.join(VIDEOLIBRARY_REAL_PATH, FOLDER_TVSHOWS)
        path2 = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)
        folder = FOLDER_TVSHOWS

    raiz, carpetas, ficheros = filetools.walk(path).next()              #listo las series o películas en la Videoteca
    carpetas = [filetools.join(path, f) for f in carpetas]              #agrego la carpeta del contenido al path
    for carpeta in carpetas:                                            #busco el contenido seleccionado en la lista de carpetas
        if item.contentType == 'movie' and (item.contentTitle.lower() in carpeta or item.contentTitle in carpeta):   #Películas?
            path = carpeta                                              #Almacenamos la carpeta en el path
            break
        elif item.contentType in ['tvshow', 'season', 'episode'] and (item.contentSerieName.lower() in carpeta or item.contentSerieName in carpeta):                                                                #Series?
            path = carpeta                                              #Almacenamos la carpeta en el path
            break
    
    path2 += '/%s/' % scrapertools.find_single_match(path, '%s.(.*?\s\[.*?\])' % folder) #Agregamos la carpeta de la Serie o Películas, formato Android
    file_search = '%'                                                   #Por defecto busca todos los archivos de la carpeta
    if files == 'file':                                                 #Si se ha pedido son un archivo (defecto), se busca
        if item.contentType == 'episode':                               #Si es episodio, se pone el nombre, si no de deja %
            file_search = '%sx%s.strm' % (item.contentSeason, str(item.contentEpisodeNumber).zfill(2))      #Nombre para episodios

    if "\\" in path:                                                    #Ajustamos los / en función de la plataforma
        path = path.replace("/", "\\")
        path += "\\"                                                    #Terminamos el path con un /
    else:
        path += "/"

    if FOLDER_TVSHOWS in path:                                          #Compruebo si es CINE o SERIE
        contentType = "episode_view"                                    #Marco la tabla de BBDD de Kodi Video
    else:
        contentType = "movie_view"                                      #Marco la tabla de BBDD de Kodi Video
    path1 = path.replace("\\\\", "\\")                                  #para la SQL solo necesito la carpeta
    path2 = path2.replace("\\", "/")                                     #Formato no Windows

    #Ejecutmos la sentencia SQL
    if not from_fields:
        from_fields = '*'
    else:
        from_fields = 'strFileName, %s' % from_fields                       #al menos dos campos, porque uno solo genera cosas raras
    sql = 'select %s from %s where (strPath like "%s" or strPath like "%s") and strFileName like "%s"' % (from_fields, contentType, path1, path2, file_search)
    nun_records = 0
    records = None
    try:
        if config.is_xbmc():
            from platformcode import xbmc_videolibrary
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql)      #ejecución de la SQL
            if nun_records == 0:                                                #hay error?
                logger.error("Error en la SQL: " + sql + ": 0 registros")       #No estará catalogada o hay un error en el SQL
    except:
        pass
             
    return (nun_records, records)
    
    
def fail_over_newpct1(item, patron, patron2=None, timeout=None):
    logger.info()
    import ast
    
    """
        
    Llamada para encontrar una web alternativa a un canal caído, clone de NewPct1
    
    Creamos una array con los datos de los canales alternativos.  Los datos de la tupla son:
    
        - active = 0,1      Indica si el canal no está activo o sí lo está
        - channel           nombre del canal alternativo
        - channel_host      host del canal alternativo, utilizado para el reemplazo de parte de la url
        - contentType       indica que tipo de contenido que soporta el nuevo canal en fail-overs
        - action_excluded   lista las acciones que está excluidas para ese canal
    
    La llamada al método desde el principio de Submenu, Listado_Búsqueda, Episodios y Findvideos, es:
    
        from lib import generictools
        item, data = generictools.fail_over_newpct1(item, patron[, patron2=][, timeout=])
        
        - Entrada:  patron: con este patron permite verificar si los datos de la nueva web son buenos
        - Entrada (opcional): patron2: segundo patron opcional
        - Entrada (opcional): timeout: valor de espera máximo en download de página.  Por defecto 3
        - Entrada (opcional): patron=True: pide que sólo verifique si el canal en uso está activo, si no, ofrece otro
        - Salida:   data:   devuelve los datos del la nueva web.  Si vuelve vacía es que no se ha encontrado alternativa
    
    """
    #logger.debug(item)
    
    if timeout == None:
        timeout = config.get_setting('clonenewpct1_timeout_downloadpage', channel_py)           #Timeout downloadpage
    if timeout == 0: timeout = None
    if item.action == "search" or item.action == "listado_busqueda": timeout = timeout * 2      #Mas tiempo para búsquedas
    
    data = ''
    channel_failed = ''
    url_alt = []
    if not item.category:
        item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
    if not item.extra2:
        item.extra2 = 'z9z8z7z6z5'

    #Array con los datos de los canales alternativos
    #Cargamos en .json del canal para ver las listas de valores en settings
    fail_over = channeltools.get_channel_json(channel_py)
    for settings in fail_over['settings']:                             #Se recorren todos los settings
        if settings['id'] == "clonenewpct1_channels_list":             #Encontramos en setting
            fail_over = settings['default']                            #Carga lista de clones
            break
    fail_over_list = ast.literal_eval(fail_over)

    if item.from_channel:                                              #Desde search puede venir con el nombre de canal equivocado
        item.channel = item.from_channel
    #Recorremos el Array identificando el canal que falla
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        if item.channel == channel_py:
            if channel != item.category.lower():        #es el canal/categoría que falla?
                continue
        else:
            if channel != item.channel:                 #es el canal que falla?
                continue
        channel_failed = channel                        #salvamos el nombre del canal o categoría
        channel_host_failed = channel_host              #salvamos el nombre del host
        channel_url_failed = item.url                   #salvamos la url
        if patron == True and active == '1':            #solo nos han pedido verificar el clone
            return (item, data)                         #nos vamos, con el mismo clone, si está activo
        if (item.action == 'episodios' or item.action == 'findvideos') and item.contentType not in contentType:        #soporta el fail_over de este contenido?
            logger.error("ERROR 99: " + item.action.upper() + ": Acción no soportada para Fail-Over en canal: " + item.url)
            return (item, data)                         #no soporta el fail_over de este contenido, no podemos hacer nada
        break
        
    if not channel_failed:
        logger.error('Patrón: ' + str(patron) + ' / fail_over_list: ' + str(fail_over_list))
        logger.error(item)
        return (item, data)                             #Algo no ha funcionado, no podemos hacer nada

    #Recorremos el Array identificando canales activos que funcionen, distintos del caído, que soporten el contenido
    for active, channel, channel_host, contentType, action_excluded in fail_over_list:
        data_alt = ''
        if channel == channel_failed or active == '0' or item.action in action_excluded or item.extra2 in action_excluded:  #es válido el nuevo canal?
            continue
        if (item.action == 'episodios' or item.action == 'findvideos') and item.contentType not in contentType:     #soporta el contenido?
            continue
        
        #Hacemos el cambio de nombre de canal y url, conservando las anteriores como ALT
        item.channel_alt = channel_failed
        if item.channel != channel_py:
            item.channel = channel
        item.category = channel.capitalize()
        item.url_alt = channel_url_failed
        item.url = channel_url_failed
        item.url = item.url.replace(channel_host_failed, channel_host)
        url_alt += [item.url]                               #salvamos la url para el bucle
        item.channel_host = channel_host
        
        #quitamos el código de series, porque puede variar entre webs
        if item.action == "episodios" or item.action == "get_seasons":
            item.url = re.sub(r'\/\d+\/?$', '', item.url)   #parece que con el título solo ecuentra la serie, normalmente...
            url_alt = [item.url]                            #salvamos la url para el bucle, pero de momento ignoramos la inicial con código de serie
        
        #si es un episodio, generalizamos la url para que se pueda encontrar en otro clone.  Quitamos la calidad del final de la url
        elif item.action == "findvideos" and item.contentType == "episode":
            try:
                #quitamos el 0 a la izquierda del episodio.  Algunos clones no lo aceptan
                inter1, inter2, inter3 = scrapertools.find_single_match(item.url, '(http.*?\/temporada-\d+.*?\/capitulo.?-)(\d+)(.*?\/)')
                inter2 = re.sub(r'^0', '', inter2)
                if inter1 + inter2 + inter3 not in url_alt:
                    url_alt += [inter1 + inter2 + inter3]
                
                #en este formato solo quitamos la calidad del final de la url
                if scrapertools.find_single_match(item.url, 'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/') not in url_alt:
                    url_alt += [scrapertools.find_single_match(item.url, 'http.*?\/temporada-\d+.*?\/capitulo.?-\d+.*?\/')]
            except:
                logger.error("ERROR 88: " + item.action + ": Error al convertir la url: " + item.url)
            logger.debug('URLs convertidas: ' + str(url_alt))

        if patron == True:                                  #solo nos han pedido verificar el clone
            return (item, data)                             #nos vamos, con un nuevo clone
        
        #Leemos la nueva url.. Puede haber varias alternativas a la url original
        for url in url_alt:
            try:
                if item.post:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, post=item.post, timeout=timeout).data)
                else:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, timeout=timeout).data)
                data_comillas = data.replace("'", "\"")
            except:
                data = ''
            if not data:                                    #no ha habido suerte, probamos con la siguiente url
                logger.error("ERROR 01: " + item.action + ": La Web no responde o la URL es erronea: " + url)
                continue
        
            #Hemos logrado leer la web, validamos si encontramos un línk válido en esta estructura
            #Evitar páginas engañosas que puede meter al canal en un loop infinito
            if (not ".com/images/no_imagen.jpg" in data and not ".com/images/imagen-no-disponible.jpg" in data) or item.action != "episodios":
                if patron:
                    data_alt = scrapertools.find_single_match(data, patron)
                    if not data_alt:
                        data_alt = scrapertools.find_single_match(data_comillas, patron)
                    if patron2 != None:
                        data_alt = scrapertools.find_single_match(data_alt, patron2)
                if not data_alt:                            #no ha habido suerte, probamos con el siguiente canal
                    logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " + url + " / Patron: " + patron)
                    web_intervenida(item, data)
                    data = ''
                    continue
                else:
                    item.url = url                          #guardamos la url que funciona
                    break                                   #por fin !!!  Este canal parece que funciona
            else:
                logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " + url + " / Patron: " + patron)
                web_intervenida(item, data)
                data = ''
                continue
                
        if not data:                                        #no ha habido suerte, probamos con el siguiente clone
            url_alt = []
            continue
        else:
            break
    
    del item.extra2                                         #Borramos acción temporal excluyente
    if not data:                                            #Si no ha logrado encontrar nada, salimos limpiando variables
        if item.channel == channel_py:
            if item.channel_alt:
                item.category = item.channel_alt.capitalize()
                del item.channel_alt
        else:
            if item.channel_alt:
                item.channel = item.channel_alt
                del item.channel_alt
        if item.url_alt: 
            item.url = item.url_alt
            del item.url_alt
        item.channel_host = channel_host_failed
    
    #logger.debug(item)
    
    return (item, data)

    
def web_intervenida(item, data, desactivar=True):
    logger.info()
    
    """
        
    Llamada para verificar si la caída de un clone de Newpct1 es debido a una intervención judicial
    
    La llamada al método desde  es:
    
        from lib import generictools
        item = generictools.web_intervenida(item, data[, desactivar=True])
        
        - Entrada:  data: resultado de la descarga.  Nos permite analizar si se trata de una intervención
        - Entrada:  desactivar=True:  indica que desactiva el canal o clone en caso de intervención judicial
        - Salida:   item.intervencion: devuele un array con el nombre del clone intervenido y el thumb de la autoridad que interviene.  El canal puede anunciarlo.
        - Salida:   Si es un clone de Newpct1, se desactiva el clone en el .json del Canal.  Si es otro canal, se desactiva el canal en su .json.
    
    """
    
    intervencion = ()
    judicial = ''

    #Verificamos que sea una intervención judicial
    if intervenido_policia in data or intervenido_guardia in data or intervenido_sucuri in data:
        if intervenido_guardia in data:
            judicial = 'intervenido_gc.png'                             #thumb de la Benemérita
        if intervenido_policia in data:
            judicial = 'intervenido_pn.jpeg'                            #thumb de la Policia Nacional
        if intervenido_sucuri in data:
            judicial = 'intervenido_sucuri.png'                         #thumb de Sucuri
        category = item.category
        if not item.category:
            category = item.channel
        intervencion = (category, judicial)                             #Guardamos el nombre canal/categoría y el thumb judicial
        if not item.intervencion:
            item.intervencion = []                                      #Si no existe el array, lo creamos
        item.intervencion += [intervencion]                             #Añadimos esta intervención al array
        
        logger.error("ERROR 99: " + category + ": " + judicial + ": " + item.url + ": DESACTIVADO=" + str(desactivar) + " / DATA: " + data)
        
        if desactivar == False:                                         #Si no queremos desactivar el canal, nos vamos
            return item
        
        #Cargamos en .json del canal para ver las listas de valores en settings.  Carga las claves desordenadas !!!
        from core import filetools
        import json
        json_data = channeltools.get_channel_json(item.channel)
        
        if item.channel == channel_py:                                  #Si es un clone de Newpct1, lo desactivamos
            for settings in json_data['settings']:                      #Se recorren todos los settings
                if settings['id'] == "clonenewpct1_channels_list":      #Encontramos en setting
                    action_excluded = scrapertools.find_single_match(settings['default'], "\('\d', '%s', '[^']+', '[^']*', '([^']*)'\)" % item.category.lower())               #extraemos el valor de action_excluded
                    if action_excluded:
                        if "intervenido" not in action_excluded:
                            action_excluded += ', %s' % judicial        #Agregamos el thumb de la autoridad judicial
                    else:
                        action_excluded = '%s' % judicial
                        
                    #Reemplazamos el estado a desactivado y agregamos el thumb de la autoridad judicial
                    settings['default'] = re.sub(r"\('\d', '%s', ('[^']+', '[^']*'), '[^']*'\)" % item.category.lower(),  r"('0', '%s', \1, '%s')" % (item.category.lower(), action_excluded), settings['default'])

                    break
        else:
            #json_data['active'] = False                                 #Se desactiva el canal
            json_data['thumbnail'] = ', thumb_%s' % judicial            #Guardamos el thumb de la autoridad judicial

        #Guardamos los cambios hechos en el .json
        try:
            if item.channel != channel_py:
                disabled = config.set_setting('enabled', False, item.channel)                       #Desactivamos el canal
                disabled = config.set_setting('include_in_global_search', False, item.channel)      #Lo sacamos de las búquedas globales
            channel_path = filetools.join(config.get_runtime_path(), "channels", item.channel + ".json")
            with open(channel_path, 'w') as outfile:                        #Grabamos el .json actualizado
                json.dump(json_data, outfile, sort_keys = True, indent = 2, ensure_ascii = False)
        except:
            logger.error("ERROR 98 al salvar el archivo: %s" % channel_path)

    #logger.debug(item)
    
    return item

    
def redirect_clone_newpct1(item, head_nfo=None, it=None, path=False, overwrite=False, lookup=False):
    logger.info()
    
    """
        
    Llamada para redirigir cualquier llamada a un clone de NewPct1 a NewPct1.py, o de una url de un canal caido a una alternativa
    Incluye las llamadas estándar del canal y la llamadas externas:
        - Play fron Library
        - Videolibrary Update
        
    La lógica es reemplazar item.channel por "newpct1" y dejar el nombre del clone en item.category.
    De esta forma utiliza siempre el código de NewPct1.py, aunque con las urls y apariencia del clone seleccionado por el usuario.
    
    En el caso de un canal/clone caído o intervenido judicialmente, puede reemplazar el canal en item.channel, o el clone en item.category, y la parte de item.url que se introduzca en una tabla.  Esta conversión sólo se realiza si el canal original está inactivo, pero lo realiza siempre para los clones, o si el canal de origen y destino son los mismos.
    
    Este método interroga el .json de NewPct1 para extraer la lista de canales clones.  Si item.channel es un clone de NewPct1 y está en esa lista, actualiza item.channel='newpct1'
    
    También en este .json está la tabla para la conversión de canales y urls:
        - activo:       está o no activa esta entrada
        - canal_org:    canal o clone de origen
        - canal_des:    canal o clone de destino (puede ser el mismo)
        - url_org:      parte de la url a sustituir de canal o clone de origen
        - url_des:      parte de la url a sustituir de canal o clone de destino
        - patron1:      expresión Regex aplicable a la url (opcional)
        - patron2:      expresión Regex aplicable a la url (opcional)
        - patron3:      expresión Regex aplicable a la url (opcional)
        - patron4:      expresión Regex aplicable a la url (opcional)
        - patron5:      expresión Regex aplicable a la url (opcional)
        - content_inc:  contenido al que aplica esta entrada, o * (item.contentType o item.extra)
        - content_exc:  contenido que se excluye de esta entrada (item.contentType) (opcional)
        - ow_force:     indicador para la acción de "videolibrary_service.py".  Puede crear la variable item.ow_force:
                            - force:    indica al canal que analize toda la serie y que videolibrary_service la reescriba
                            - auto:     indica a videolibrary_service que la reescriba
                            - no:       no acción para videolibrary_service, solo redirige en visionado de videolibrary
        ejemplo: ('1', 'mejortorrent', 'mejortorrent1', 'http://www.mejortorrent.com/', 'https://mejortorrent1.com/', 'auto')
    
    La llamada recibe el parámetro Item, el .nfo y los devuleve actualizados, así como opcionalmente el parámetro "overwrite· que puede forzar la reescritura de todos los archivos de la serie, y el parámetro "path" si viene de videolibrary_service.  Por último, recibe opcionalmente el parámetro "lookup" si se quiere solo averigurar si habrá migración para ese título, pero sin realizarla.
    
    """
    if not it:
        it = Item()
    #logger.debug(item)
    ow_force_param = True
    channel_enabled = False
    update_stat = 0

    #Array con los datos de los canales alternativos
    #Cargamos en .json de Newpct1 para ver las listas de valores en settings
    fail_over_list = channeltools.get_channel_json(channel_py)
    for settings in fail_over_list['settings']:                             #Se recorren todos los settings
        if settings['id'] == "clonenewpct1_channels_list":                  #Encontramos en setting
            fail_over_list = settings['default']                            #Carga lista de clones
        if settings['id'] == "intervenidos_channels_list":                  #Encontramos en setting
            intervencion = settings['default']                              #Carga lista de clones y canales intervenidos

    #primero tratamos los clones de Newpct1
    channel_alt = item.channel                                              #Salvamos en nombre del canal o clone
    channel = "'%s'" % item.channel
    if channel in fail_over_list:                                           #Si es un clone de Newpct1, se actualiza el canal
        item.channel = channel_py
      
    #Ahora tratamos las webs intervenidas, tranformamos la url, el nfo y borramos los archivos obsoletos de la serie
    if channel not in intervencion and channel_alt != 'videolibrary':       #Hacemos una lookup para ver si...
        return (item, it, overwrite)                                        #... el canal/clone está listado

    import ast
    intervencion_list = ast.literal_eval(intervencion)                      #Convertir a Array el string
    #logger.debug(intervencion_list)
    
    if lookup == True:
        overwrite = False                                                   #Solo avisamos si hay cambios
    for activo, canal_org, canal_des, url_org, url_des, patron1, patron2, patron3, patron4, patron5, content_inc, content_exc, ow_force in intervencion_list:
        if activo == '1' and (canal_org == channel_alt or channel_alt == 'videolibrary'):     #Es esta nuestra entrada?
            if channel_alt == 'videolibrary':                               #Viene de videolibrary.list_movies
                for canal_vid, url_vid in item.library_urls.items():
                    if canal_org != canal_vid:                      #Miramos si canal_org de la regla está en item.library_urls
                        continue
                    else:
                        channel_alt = canal_org                             #Sí, ponermos el nombre del canal de origen
                        channel_b = "'%s'" % canal_org
                        if channel_b in fail_over_list:                     #Si es un clone de Newpct1, se actualiza a newpct1
                            channel_alt = channel_py
                if channel_alt == 'videolibrary':
                    continue
            if item.contentType == "list":                                  #Si viene de Videolibrary, le cambiamos ya el canal
                if item.channel != channel_py:
                    item.channel = canal_des                                #Cambiamos el canal.  Si es clone, lo hace el canal
                    continue                                                #Salimos sin hacer nada más. item está casi vacío
            if item.contentType not in content_inc and "*" not in content_inc:  #Está el contenido el la lista de incluidos
                continue
            if item.contentType in content_exc:                             #Está el contenido excluido?
                continue
            if item.channel != channel_py:
                channel_enabled = channeltools.is_enabled(channel_alt)      #Verificamos que el canal esté inactivo
                channel_enabled_alt = config.get_setting('enabled', channel_alt)
                channel_enabled = channel_enabled * channel_enabled_alt     #Si está inactivo en algún sitio, tomamos eso
            if channel_enabled == 1 and canal_org != canal_des:             #Si el canal está activo, puede ser solo...
                continue                                                    #... una intervención que afecte solo a una región
            if ow_force == 'no' and it.library_urls:                        #Esta regla solo vale para findvideos...
                continue                                                    #... salidmos si estamos actualizando
            if lookup == True:                                              #Queremos que el canal solo visualice sin migración?
                if ow_force != 'no':
                    overwrite = True                                        #Avisamos que hay cambios
                continue                                                    #Salimos sin tocar archivos
            url_total = ''
            if item.url:
                url_total = item.url
            elif not item.url and item.library_urls:
                url_total = item.library_urls[canal_org]
            url_total = url_total.replace(url_org, url_des)                 #reemplazamos una parte de url
            url = ''
            if patron1:                                                     #Hay expresión regex?
                url += scrapertools.find_single_match(url_total, patron1)   #La aplicamos a url
            if patron2:                                                     #Hay más expresión regex?
                url += scrapertools.find_single_match(url_total, patron2)   #La aplicamos a url
            if patron3:                                                     #Hay más expresión regex?
                url += scrapertools.find_single_match(url_total, patron3)   #La aplicamos a url
            if patron4:                                                     #Hay más expresión regex?
                url += scrapertools.find_single_match(url_total, patron4)   #La aplicamos a url
            if patron5:                                                     #Hay más expresión regex?
                url += scrapertools.find_single_match(url_total, patron5)   #La aplicamos a url
            if url:
                url_total = url                                             #Guardamos la suma de los resultados intermedios
            update_stat += 1                                                #Ya hemos actualizado algo
            canal_org_def = canal_org
            canal_des_def = canal_des
            ow_force_def = ow_force
            
    if update_stat > 0:                                                 #Ha habido alguna actualización?  Entonces salvamos
        if item.channel == channel_py or channel in fail_over_list:     #Si es Newpct1...
            if item.contentType == "tvshow":
                url_total = re.sub(r'\/\d+\/?$', '', url_total)         #parece que con el título  ecuentra la serie, normalmente...
        if item.url:
            item.url = url_total                                        #Salvamos la url convertida
        if item.library_urls:
            item.library_urls.pop(canal_org_def, None)
            item.library_urls = {canal_des_def: url_total}
            it.library_urls = item.library_urls
        if item.channel != channel_py and item.channel != 'videolibrary':
            item.channel = canal_des_def                                #Cambiamos el canal.  Si es clone, lo hace el canal
            if channel_alt == item.category.lower():                    #Actualizamos la Categoría y si la tenía
                item.category = item.channel.capitalize()
        if ow_force_def == 'force' and item.contentType != "movie":     #Queremos que el canal revise la serie entera?
            item.ow_force = '1'                                         #Se lo decimos
        if ow_force_def in ['force', 'auto']:                           #Sobreescribir la series?
            overwrite = True                                            #Sí, lo marcamos

        #logger.debug(canal_org_def + canal_des_def + ow_force_def)
        if it.library_urls and path != False and ow_force_def != 'no':      #Continuamos si hay .nfo, path, y queremos actualizarlo
            if item.update_next:
                del item.update_next                                        #Borramos estos campos para forzar la actualización ya
            if it.update_next:
                del it.update_next
        
            # Listamos todos los ficheros de la serie, asi evitamos tener que comprobar si existe uno por uno
            raiz, carpetas_series, ficheros = filetools.walk(path).next()
            ficheros = [filetools.join(path, f) for f in ficheros]          #Almacenamos la lista de archivos de la carpeta
            canal_erase = '[%s]' % canal_org_def
            for archivo in ficheros:
                if canal_erase in archivo:                                  #Borramos los .json que sean del canal intervenido
                    json_path = archivo.replace(canal_org_def, canal_des_def)   #Salvamos el path del .json para luego crearlo
                    filetools.remove(archivo)
                if item.contentType == "movie" and ".nfo" in archivo:
                    filetools.write(archivo, head_nfo + it.tojson())        #escribo el .nfo de la peli por si aborta update
                if item.contentType != "movie" and "tvshow.nfo" in archivo:
                    filetools.write(archivo, head_nfo + it.tojson())        #escribo el tvshow.nfo por si aborta update
            
            #Aquí convertimos las películas.  Después de borrado el .json, dejamos que videolibrarytools lo regenere
            if item.contentType == "movie":                                 #Dejamos que regenere el archivo .json
                item_movie = item.clone()
                item_movie.channel = canal_des_def                          #mombre del canal migrado
                del item_movie.library_playcounts                           #Borramos lo que no es necesario en el .json
                del item_movie.library_urls
                item_movie.url = url_total                                  #url migrada
                del item_movie.nfo
                del item_movie.path
                del item_movie.strm_path
                del item_movie.text_color
                filetools.write(json_path, item_movie.tojson())             #Salvamos el nuevo .json de la película

    if update_stat > 0 and path != False and ow_force_def != 'no':
        logger.debug(item)
    
    return (item, it, overwrite)
    

def dejuice(data):
    logger.info()
    # Metodo para desobfuscar datos de JuicyCodes
    
    import base64
    from lib import jsunpack

    juiced = scrapertools.find_single_match(data, 'JuicyCodes.Run\((.*?)\);')
    b64_data = juiced.replace('+', '').replace('"', '')
    b64_decode = base64.b64decode(b64_data)
    dejuiced = jsunpack.unpack(b64_decode)

    return dejuiced