# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# GenericTools
# ------------------------------------------------------------
# Código reusable de diferentes partes de los canales que pueden
# ser llamadados desde otros canales, y así carificar el formato
# y resultado de cada canal y reducir el costo su mantenimiento
# ----------------------------------------------------------

import re
import sys
import urllib
import urlparse
import datetime

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb


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
    
    #Restauramos y borramos las etiquetas intermedias (si se ha llamado desde el canal)
    if item.from_action:
        item.action = item.from_action
        del item.from_action
    if item.from_title:
        item.title = item.from_title
        del item.from_title
    else:
        item.add_videolibrary = True        #Estamos Añadiendo a la Videoteca.  Indicador para control de uso de los Canales
    
    #Sólo ejecutamos este código si no se ha hecho antes en el Canal.  Por ejemplo, si se ha llamado desde Episodios,
    #ya no se ejecutará al Añadia a Videoteca, aunque desde el canal se podrá llamar tantas veces como se quiera, 
    #o hasta que encuentre un título no ambiguo
    if not item.tmdb_stat:
        new_item = item.clone()             #Salvamos el Item inicial para restaurarlo si el usuario cancela
        #Borramos los IDs y el año para forzar a TMDB que nos pregunte
        if item.infoLabels['tmdb_id'] or item.infoLabels['tmdb_id'] == None: item.infoLabels['tmdb_id'] = ''
        if item.infoLabels['tvdb_id'] or item.infoLabels['tvdb_id'] == None: item.infoLabels['tvdb_id'] = ''
        if item.infoLabels['imdb_id'] or item.infoLabels['imdb_id'] == None: item.infoLabels['imdb_id'] = ''
        if item.infoLabels['season']: del item.infoLabels['season'] #Funciona mal con num. de Temporada.  Luego lo restauramos
        item.infoLabels['year'] = '-'
        
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
                    item.contentSerieName = item.contentTitle               #Se pone título nuevo
                item.infoLabels['noscrap_id'] = ''                          #Se resetea, por si acaso
                item.infoLabels['year'] = '-'                               #Se resetea, por si acaso
                scraper_return = scraper.find_and_set_infoLabels(item)      #Se intenta de nuevo

                #Parece que el usuario ha cancelado de nuevo.  Restituimos los datos a la situación inicial
                if not scraper_return or not item.infoLabels['tmdb_id']:
                    item = new_item.clone()
                else:
                    item.tmdb_stat = True       #Marcamos Item como procesado correctamente por TMDB (pasada 2)
            else:
                item.tmdb_stat = True           #Marcamos Item como procesado correctamente por TMDB (pasada 1)

            #Si el usuario ha seleccionado una opción distinta o cambiado algo, ajustamos los títulos
            if new_item.contentSerieName:       #Si es serie...
                item.title = item.title.replace(new_item.contentSerieName, item.contentTitle)
                item.contentSerieName = item.contentTitle
                if new_item.contentSeason: item.contentSeason = new_item.contentSeason      #Restauramos Temporada
                if item.infoLabels['title']: del item.infoLabels['title']       #Borramos título de peli (es serie)
            else:                               #Si es película...
                item.title = item.title.replace(new_item.contentTitle, item.contentTitle)
            if new_item.infoLabels['year']:     #Actualizamos el Año en el título
                item.title = item.title.replace(str(new_item.infoLabels['year']), str(item.infoLabels['year']))
            if new_item.infoLabels['rating']:   #Actualizamos en Rating en el título
                rating_old = ''
                if new_item.infoLabels['rating'] and new_item.infoLabels['rating'] != '0.0':
                    rating_old = float(new_item.infoLabels['rating'])
                    rating_old = round(rating_old, 1)
                rating_new = ''
                if item.infoLabels['rating'] and item.infoLabels['rating'] != '0.0':
                    rating_new = float(item.infoLabels['rating'])
                    rating_new = round(rating_new, 1)
                item.title = item.title.replace("[" + str(rating_old) + "]", "[" + str(rating_new) + "]")
            if item.wanted:                     #Actualizamos Wanted, si existe
                item.wanted = item.contentTitle
            if new_item.contentSeason:          #Restauramos el núm. de Temporada después de TMDB
                item.contentSeason = new_item.contentSeason
     
        #Para evitar el "efecto memoria" de TMDB, se le llama con un título ficticio para que resetee los buffers
        if item.contentSerieName:
            new_item.infoLabels['tmdb_id'] = '289'      #una serie no ambigua
        else:
            new_item.infoLabels['tmdb_id'] = '111'      #una peli no ambigua
        new_item.infoLabels['year'] = '-'
        if new_item.contentSeason:
            del new_item.infoLabels['season']           #Funciona mal con num. de Temporada
        scraper_return = scraper.find_and_set_infoLabels(new_item)
        
    #logger.debug(item)
    
    return item
    

def post_tmdb_listado(item, itemlist):
    logger.info()
    
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
    
    #Borramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel_alt:
        channel_alt = item.channel
        del item.channel_alt
    if item.url_alt:
        del item.url_alt

    for item_local in itemlist:                                 #Recorremos el Itenlist generado por el canal
        title = item_local.title
        
        if item_local.contentSeason_save:                       #Restauramos el num. de Temporada
            item_local.contentSeason = item_local.contentSeason_save

        #Borramos valores para cada Contenido si ha habido fail-over
        if item_local.channel_alt:
            del item_local.channel_alt
        if item_local.url_alt:
            del item_local.url_alt
        
        #Restauramos la info adicional guarda en la lista title_subs, y la borramos de Item
        title_add = ' '
        if item_local.title_subs:
            for title_subs in item_local.title_subs:
                if "audio" in title_subs.lower():               #se restaura info de Audio
                    title_add += scrapertools.find_single_match(title_subs, r'[a|A]udio (.*?)')
                    continue
                if scrapertools.find_single_match(title_subs, r'(\d{4})'):      #Se restaura el año, s no lo ha dado TMDB
                    if not item_local.infoLabels['year'] or item_local.infoLabels['year'] == "-":
                        item_local.infoLabels['year'] = scrapertools.find_single_match(title_subs, r'(\d{4})')
                    continue
                    
                title_add = title_add.rstrip()
                title_add += '%s -%s-' % (title_add, title_subs)     #se agregan el resto de etiquetas salvadas
            del item_local.title_subs
        
        #Preparamos el Rating del vídeo
        rating = ''
        try:
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != '0.0':
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
        except:
            pass
        
        # Si TMDB no ha encontrado el vídeo limpiamos el año
        if item_local.infoLabels['year'] == "-":
            item_local.infoLabels['year'] = ''
            item_local.infoLabels['aired'] = ''
        # Para Episodios, tomo el año de exposición y no el de inicio de la serie
        elif item_local.infoLabels['aired']:
            item_local.infoLabels['year'] = scrapertools.find_single_match(str(item_local.infoLabels['aired']), r'\/(\d{4})')
        
        # Preparamos el título para series, con los núm. de temporadas, si las hay
        if item_local.contentType in ['season', 'tvshow', 'episode']:
            if item_local.infoLabels['title']: del item_local.infoLabels['title']

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
                    item_local.infoLabels['episodio_titulo'] = '%s, %s [%s] [%s]' % (item_local.infoLabels['episodio_titulo'], item_local.contentSerieName, item_local.infoLabels['year'], rating)
                    
                else:       #Si no hay título de episodio, ponermos el nombre de la serie
                    title = '%s %s' % (title, item_local.contentSerieName)
                    item_local.infoLabels['episodio_titulo'] = '%s [%s] [%s]' % (item_local.contentSerieName, item_local.infoLabels['year'], rating)

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
        
        elif item_local.extra == "varios" and item.action == "search":
            title += " -Varios-"
            item_local.contentTitle += " -Varios-"
        
        title += title_add                  #Se añaden etiquetas adicionales, si las hay

        #Ahora maquillamos un poco los titulos dependiendo de si se han seleccionado títulos inteleigentes o no
        if not config.get_setting("unify"):         #Si Titulos Inteligentes NO seleccionados:
            title = '%s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (title, str(item_local.infoLabels['year']), rating, item_local.quality, str(item_local.language))

        else:                                       #Si Titulos Inteligentes SÍ seleccionados:
            title = title.replace("[", "-").replace("]", "-")
        
        #Limpiamos las etiquetas vacías
        if item_local.infoLabels['episodio_titulo']:
            item_local.infoLabels['episodio_titulo'] = item_local.infoLabels['episodio_titulo'].replace(" []", "").strip()
        title = title.replace("--", "").replace(" []", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', title).strip()
        title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', title).strip()
    
        if item.category == "newest":     #Viene de Novedades.  Marcamos el título con el nombre del canal
            title += ' -%s-' % item_local.channel.capitalize()
            if item_local.contentType == "movie": 
                item_local.contentTitle += ' -%s-' % item_local.channel.capitalize()

        item_local.title = title
        
        #logger.debug("url: " + item_local.url + " / title: " + item_local.title + " / content title: " + item_local.contentTitle + "/" + item_local.contentSerieName + " / calidad: " + item_local.quality + "[" + str(item_local.language) + "]" + " / year: " + str(item_local.infoLabels['year']))
        
        #logger.debug(item_local)
    
    #Si ha habido fail-over, lo comento
    if channel_alt:
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel.capitalize() + '[/COLOR] caído'))
        
    return (item, itemlist)


def post_tmdb_episodios(item, itemlist):
    logger.info()
        
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

    #Restauramos valores si ha habido fail-over
    channel_alt = ''
    if item.channel_alt:
        channel_alt = item.channel
        item.channel = item.channel_alt
        del item.channel_alt
    if item.url_alt:
        item.url = item.url_alt
        del item.url_alt
        
    for item_local in itemlist:                     #Recorremos el Itenlist generado por el canal
        if item_local.add_videolibrary:
            del item_local.add_videolibrary
        if item_local.add_menu:
            del item_local.add_menu
        
        #Restauramos valores para cada Episodio si ha habido fail-over
        if item_local.channel_alt:
            item_local.channel = item_local.channel_alt
            del item_local.channel_alt
        if item_local.url_alt:
            host_act = scrapertools.find_single_match(item_local.url, ':\/\/(.*?)\/')
            host_org = scrapertools.find_single_match(item_local.url_alt, ':\/\/(.*?)\/')
            item_local.url = item_local.url.replace(host_act, host_org)
            del item_local.url_alt
            
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
            if item_local.infoLabels['rating'] and item_local.infoLabels['rating'] != '0.0':
                rating = float(item_local.infoLabels['rating'])
                rating = round(rating, 1)
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
        if "Temporada" in item_local.title:     #Compatibilizamos "Temporada" con Unify
            item_local.title = '%sx%s al 99 -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber))
        if " al " in item_local.title:        #Si son episodios múltiples, ponemos nombre de serie
            if " al 99" in item_local.title.lower():   #Temporada completa.  Buscamos num total de episodios de la temporada
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
    
    #Terminado el repaso de cada episodio, cerramos con el pié de página
    #En primer lugar actualizamos todos los episodios con su núm máximo de episodios por temporada
    try:
        if not num_episodios_flag:  #Si el num de episodios no está informado, acualizamos episodios de toda la serie
            for item_local in itemlist:
                item_local.infoLabels['temporada_num_episodios'] = int(num_episodios_lista[item_local.contentSeason])
    except:
        logger.error("ERROR 07: EPISODIOS: Num de Temporada fuera de rango " + " / TEMPORADA: " + str(item_local.contentSeason) + " / " + str(item_local.contentEpisodeNumber) + " / MAX_TEMPORADAS: " + str(num_temporada_max) + " / LISTA_TEMPORADAS: " + str(num_episodios_lista))
    
    #Permitimos la actualización de los títulos, bien para uso inmediato, o para añadir a la videoteca
    itemlist.append(item.clone(title="** [COLOR yelow]Actualizar Títulos - vista previa videoteca[/COLOR] **", action="actualizar_titulos", extra="episodios", tmdb_stat=False, from_action=item.action, from_title=item.title))
    
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
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a la Videoteca[/COLOR]" + title, action="add_serie_to_library"))
                
            elif modo_serie_temp == 1:      #si es Serie damos la opción de guardar la última temporada o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir última Temp. a Videoteca[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, url=item_local.url, add_menu=True))
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))

            else:                           #si no, damos la opción de guardar la temporada actual o la serie completa
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Serie a Videoteca[/COLOR]" + title, action="add_serie_to_library", contentType="tvshow", add_menu=True))
                if item.add_videolibrary and not item.add_menu:
                    item.contentSeason = contentSeason
                itemlist.append(item.clone(title="[COLOR yellow]Añadir esta Temp. a Videoteca[/COLOR]" + title, action="add_serie_to_library", contentType="season", contentSeason=contentSeason, add_menu=True))

        else:   #Es un canal estándar, sólo una linea de Añadir a Videoteca
            itemlist.append(item.clone(title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]" + title, action="add_serie_to_library", extra="episodios", add_menu=True))
        
        #Si ha habido fail-over, lo comento
        if channel_alt:
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + channel_alt.capitalize() + '[/COLOR] [ALT ] en uso'))
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel.capitalize() + '[/COLOR] caído'))
    
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

    #Salvamos la información de max num. de episodios por temporada para despues de TMDB
    num_episodios = item.contentEpisodeNumber
    if item.infoLabels['temporada_num_episodios']:
        num_episodios = item.infoLabels['temporada_num_episodios']

    # Obtener la información actualizada del Episodio, si no la hay.  Siempre cuando viene de Videoteca
    if not item.infoLabels['tmdb_id'] or (not item.infoLabels['episodio_titulo'] and item.contentType == 'episode'):
        tmdb.set_infoLabels(item, True)
    elif (not item.infoLabels['tvdb_id'] and item.contentType == 'episode') or item.contentChannel == "videolibrary":
        tmdb.set_infoLabels(item, True)
    #Restauramos la información de max num. de episodios por temporada despues de TMDB
    try:
        if item.infoLabels['temporada_num_episodios']:
            if int(num_episodios) > int(item.infoLabels['temporada_num_episodios']):
                item.infoLabels['temporada_num_episodios'] = num_episodios
        else:
            item.infoLabels['temporada_num_episodios'] = num_episodios
    except:
        pass
        
    #Limpiamos de año y rating de episodios
    if item.infoLabels['episodio_titulo']:
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\[.*?\]', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = re.sub(r'\s?\(.*?\)', '', item.infoLabels['episodio_titulo'])
        item.infoLabels['episodio_titulo'] = item.infoLabels['episodio_titulo'].replace(item.contentSerieName, '')
    if item.infoLabels['aired'] and item.contentType == "episode":
        item.infoLabels['year'] = scrapertools.find_single_match(str(item.infoLabels['aired']), r'\/(\d{4})')

    rating = ''     #Ponemos el rating
    try:
        if item.infoLabels['rating'] and item.infoLabels['rating'] != '0.0':
            rating = float(item.infoLabels['rating'])
            rating = round(rating, 1)
    except:
        pass

    if item.quality.lower() in ['gb', 'mb']:
        item.quality = item.quality.replace('GB', 'G B').replace('Gb', 'G b').replace('MB', 'M B').replace('Mb', 'M b')
    
    #Formateamos de forma especial el título para un episodio
    if item.contentType == "episode":                   #Series
        title = '%sx%s' % (str(item.contentSeason), str(item.contentEpisodeNumber).zfill(2))    #Temporada y Episodio
        if item.infoLabels['temporada_num_episodios']:
            title = '%s (de %s)' % (title, str(item.infoLabels['temporada_num_episodios']))     #Total Episodios
        title = '%s %s' % (title, item.infoLabels['episodio_titulo'])                           #Título Episodio
        title_gen = '%s, %s [COLOR yellow][%s][/COLOR] [%s] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] [%s]' % (title, item.contentSerieName, item.infoLabels['year'], rating, item.quality, str(item.language), scrapertools.find_single_match(item.title, '\s\[(\d+,?\d*?\s\w[b|B])\]'))     #Rating, Calidad, Idioma, Tamaño                
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

    if not item.unify:      #Si Titulos Inteligentes NO seleccionados:
        title_gen = '**- [COLOR gold]Enlaces Ver: [/COLOR]%s[COLOR gold] -**[/COLOR]' % (title_gen)
    else:                   #Si Titulos Inteligentes SÍ seleccionados:
        title_gen = '[COLOR gold]Enlaces Ver: [/COLOR]%s' % (title_gen)    

    if item.channel_alt:
        title_gen = '[COLOR yellow]%s [/COLOR][ALT]: %s' % (item.channel.capitalize(), title_gen)
    elif config.get_setting("quit_channel_name", "videolibrary") == 1 and item.contentChannel == "videolibrary":
        title_gen = '%s: %s' % (item.channel.capitalize(), title_gen)

    #Pintamos el pseudo-título con toda la información disponible del vídeo
    item.action = ""
    item.server = ""
    itemlist.append(item.clone(title=title_gen))		#Título con todos los datos del vídeo
    
    #logger.debug(item)
    
    return (item, itemlist)
    
    
def fail_over_newpct1(item, patron, patron2=None):
    logger.info()
    import ast
    
    """
        
    Llamada para encontrar una web alternativa a un canal caído, clone de NewPct1
    
    Creamos una liat de tuplas con los datos de los canales alternativos.  Los datos de la tupla son:
    
        - active = 0,1      Indica si el canal no está activo o sí lo está
        - channel           nombre del canal alternativo
        - channel_host      host del canal alternativo, utilizado para el reemplazo de parte de la url
        - contentType       indica que tipo de contenido que soporta el nuevo canal en fail-overs
        - info              reservado para uso futuro
    
    La llamada al método desde el principio de Submenu, Episodios y Findvideos, es:
    
        from lib import generictools
        item, data = generictools.fail_over_newpct1(item, patron)
        
        - Entrada:  patron: con este patron permite verificar si los datos de la nueva web son buenos
        - Entrada (opcional): patron2: segundo patron opcional
        - Saida:    data:   devuelve los datos del la nueva web.  Si vuelve vacía es que no se ha encontrado alternativa
    
    """
    
    data = ''

    #lista de tuplas con los datos de los canales alternativos
    fail_over_list = config.get_setting('clonenewpct1_channels_list', "torrentrapid")
    fail_over_list = ast.literal_eval(fail_over_list)
    
    #Recorremos la tupla identificando el canala que falla
    for active, channel, channel_host, contentType, info in fail_over_list:
        if channel != item.channel:                     #es el canal que falla?
            continue
        channel_failed = channel                        #salvamos el nombre del canal
        channel_host_failed = channel_host              #salvamos el nombre del host
        channel_url_failed = item.url                   #salvamos la url
        if item.action != 'submenu' and item.action != 'search' and item.contentType not in contentType:        #soporta el fail_over de este contenido?
            data = ''
            return (item, data)                         #no soporta el fail_over de este contenido, no podemos hacer nada
    
    #Recorremos la tupla identificando canales activos que funcionen, distintos del caído, que soporten el contenido
    for active, channel, channel_host, contentType, info in fail_over_list:
        data_alt = ''
        if channel == channel_failed or active == '0':  #está activo el nuevo canal?
            continue
        if item.action != 'submenu' and item.action != 'search' and item.contentType not in contentType:     #soporta el contenido?
            continue
        
        #Hacemos el cambio de nombre de canal y url, conservando las anteriores como ALT
        item.channel_alt = channel_failed
        item.channel = channel
        item.url_alt = channel_url_failed
        item.url = channel_url_failed
        item.url = item.url.replace(channel_host_failed, channel_host)
        #quitamos el código de series, porque puede variar entre webs
        if item.action == "episodios" or item.action == "get_seasons":
            item.url = re.sub(r'\/\d+$', '', item.url)      #parece que con el título solo ecuentra la serie, normalmente...

        #Leemos la nueva url
        try:
            if item.post:
                data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, post=item.post, timeout=2).data)
            else:
                data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=2).data)
        except:
            data = ''
        if not data:        #no ha habido suerte, probamos con el siguiente canal válido
            logger.error("ERROR 01: " + item.action + ": La Web no responde o la URL es erronea: " + item.url)
            continue
        
        #Hemos logrado leer la web, validamos si encontramos un línk válido en esta estructura
        #Evitar páginas engañosas que puede meter al canal en un loop infinito
        if (not ".com/images/no_imagen.jpg" in data and not ".com/images/imagen-no-disponible.jpg" in data) or item.action != "episodios":
            if item.action == 'submenu':    #Para submenú hacemos un cambio total de canal
                patron = patron.replace(item.channel_alt, item.channel)   #el patron lleva el nombre de host
            if patron:
                data_alt = scrapertools.find_single_match(data, patron)
                if patron2 != None:
                    data_alt = scrapertools.find_single_match(data_alt, patron2)
            if not data_alt:                            #no ha habido suerte, probamos con el siguiente canal
                logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " + item.url + " / Patron: " + patron)
                data = ''
                if item.action == 'submenu':        #restauramos el patrón para el siguiente canal
                    patron = patron.replace(item.channel, item.channel_alt)
                continue
            else:
                #if item.action == "episodios" or item.action == "get_seasons":      #guardamos la url real de esta web
                    #item.url += str(scrapertools.find_single_match(data, '<ul class="buscar-list">.*?<img src=".*?\/pictures\/.*?(\/\d+)_'))
                #para Submenu y Search cambiamos también la Categoria
                if item.action == 'submenu' or item.action == 'search':    
                    item.category = item.channel.capitalize()
                break                               #por fin !!!  Este canal parece que funciona
        else:
            logger.error("ERROR 02: " + item.action + ": Ha cambiado la estructura de la Web: " + item.url + " / Patron: " + patron)
            data = ''
            continue
    
    #logger.debug(item)
    
    if not data:    #Si no ha logrado encontrar nada, salimos limpiando variables
        if item.channel_alt:
            item.channel = item.channel_alt
            del item.channel_alt
        if item.url_alt: 
            item.url = item.url_alt
            del item.url_alt
    
    return (item, data)