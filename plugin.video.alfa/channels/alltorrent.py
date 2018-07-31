# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools

host = 'http://alltorrent.net/'
__modo_grafico__ = config.get_setting('modo_grafico', 'alltorrent')


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_buscar = get_thumb("search.png")

    itemlist.append(item.clone(title="[COLOR springgreen][B]Todas Las Películas[/B][/COLOR]", action="listado",
                               url=host, thumbnail=thumb_pelis, extra="pelicula"))
    itemlist.append(item.clone(title="[COLOR springgreen]      Incluyen 1080p[/COLOR]", action="listado",
                               url=host + "rezolucia/1080p/", thumbnail=thumb_pelis_hd, extra="pelicula"))
    itemlist.append(item.clone(title="[COLOR springgreen]      Incluyen 720p[/COLOR]", action="listado",
                               url=host + "rezolucia/720p/", thumbnail=thumb_pelis_hd, extra="pelicula"))
    itemlist.append(item.clone(title="[COLOR springgreen]      Incluyen Hdrip[/COLOR]", action="listado",
                               url=host + "rezolucia/hdrip/", thumbnail=thumb_pelis, extra="pelicula"))
    itemlist.append(item.clone(title="[COLOR springgreen]      Incluyen 3D[/COLOR]", action="listado",
                               url=host + "rezolucia/3d/", thumbnail=thumb_pelis_hd, extra="pelicula"))
    itemlist.append(item.clone(title="[COLOR floralwhite][B]Buscar[/B][/COLOR]", action="search", thumbnail=thumb_buscar,
                                       extra="titulo"))
    itemlist.append(item.clone(title="[COLOR oldlace]         Por Título[/COLOR]", action="search", thumbnail=thumb_buscar,
                                       extra="titulo"))
    itemlist.append(item.clone(title="[COLOR oldlace]         Por Año[/COLOR]", action="search", thumbnail=thumb_buscar,
                                       extra="año"))
    itemlist.append(item.clone(title="[COLOR oldlace]         Por Rating Imdb[/COLOR]", action="search", thumbnail=thumb_buscar,
                                       extra="rating"))

    return itemlist
    

def listado(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        pass
    
    if not data and item.extra != "año":        #Si la web está caída salimos sin dar error
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    elif not data and item.extra == "año":      #cuando no hay datos para un año, da error.  Tratamos de evitar el error
        return itemlist
    
    patron = '<div class="browse-movie-wrap col-xs-10 col-sm-4 col-md-5 col-lg-4"><a href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)".*?rel="tag">([^"]+)<\/a>\s?<\/div><div class="[^"]+">(.*?)<\/div><\/div><\/div>'
    #data = scrapertools.find_single_match(data, patron)
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches and not '<ul class="tsc_pagination tsc_pagination' in data:               #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedqualities in matches:
        item_local = item.clone()           #Creamos copia de Item para trabajar
        title_subs = []
        
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').strip()
        item_local.url = scrapedurl
        item_local.thumbnail = scrapedthumbnail
        
        scrapedtorrent = ''
        if scrapedqualities:
            patron_quality = '<a href="([^"]+)"\s?rel="[^"]+"\s?title="[^"]+">(.*?)<\/a>'
            matches_quality = re.compile(patron_quality, re.DOTALL).findall(scrapedqualities)
            quality = ''

            for scrapedtorrent, scrapedquality in matches_quality:
                quality_inter = scrapedquality
                quality_inter = re.sub('HDr$', 'HDrip', quality_inter)
                quality_inter = re.sub('720$', '720p', quality_inter)
                quality_inter = re.sub('1080$', '1080p', quality_inter)
                if quality:
                    quality += ', %s' % quality_inter
                else:
                    quality = quality_inter
            if quality:
                item_local.quality = quality

        item_local.language = []            #Verificamos el idioma por si encontramos algo
        if "latino" in scrapedtorrent.lower() or "latino" in item.url or "latino" in title.lower():
            item_local.language += ["LAT"]
        if "ingles" in scrapedtorrent.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
            if "VOSE" in scrapedtorrent.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
                item_local.language += ["VOS"]
            else:
                item_local.language += ["VO"]
        if "dual" in scrapedtorrent.lower() or "dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
        
        #Limpiamos el título de la basura innecesaria
        title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "")
        title = title.replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("(HDRip)", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "")
        title = re.sub(r'\??\s?\d*?\&.*', '', title).title().strip()
        item_local.from_title = title                       #Guardamos esta etiqueta para posible desambiguación de título

        item_local.contentType = "movie"
        item_local.contentTitle = title
        item_local.extra = "peliculas"
        item_local.action = "findvideos"
        item_local.title = title.strip()
        item_local.infoLabels['year'] = "-"
        
        if scrapedyear >= "1900" and scrapedyear <= "2040":
            title_subs += [scrapedyear]

        itemlist.append(item_local.clone())     #Pintar pantalla
   
    #if not item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, True)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    # Extrae el paginador
    patron = '<li><a href="[^"]+">(\d+)<\/a><\/li>'         #total de páginas
    patron += '<li><a href="([^"]+\/page\/(\d+)\/)"\s?rel="[^"]+">Página siguiente[^<]+<\/a><\/li><\/ul><\/div><\/ul>' #url siguiente
    url_next = ''
    if scrapertools.find_single_match(data, patron):
        last_page, url_next, next_num = scrapertools.find_single_match(data, patron)

    if url_next:
        if last_page:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s de %s' % (int(next_num) - 1, last_page)
        else:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s' % (int(next_num) - 1)
        
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url_next, extra=item.extra))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    #Bajamos los datos de la página
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    patron = 'id="modal-quality-\w+"><span>(.*?)</span>.*?class="quality-size">(.*?)</p>.*?href="([^"]+)"'      #coge los .torrent
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                    #error
        logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)    
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    
    for scrapedquality, scrapedsize, scrapedtorrent in matches:                             #leemos los torrents con la diferentes calidades
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        
        item_local.quality = scrapedquality
        if item.infoLabels['duration']:
            item_local.quality += scrapertools.find_single_match(item.quality, '(\s\[.*?\])')   #Copiamos la duración
        
        #Añadimos el tamaño para todos
        item_local.quality = '%s [%s]' % (item_local.quality, scrapedsize)                  #Agregamos size al final de calidad
        item_local.quality = item_local.quality.replace("G", "G ").replace("M", "M ")       #Se evita la palabra reservada en Unify

        #Ahora pintamos el link del Torrent
        item_local.url = scrapedtorrent
        item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))                    #Preparamos título de Torrent
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title)    #Quitamos etiquetas vacías
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title)      #Quitamos colores vacíos
        item_local.alive = "??"                                                             #Calidad del link sin verificar
        item_local.action = "play"                                                          #Visualizar vídeo
        item_local.server = "torrent"                                                       #Seridor Torrent
        
        itemlist.append(item_local.clone())     #Pintar pantalla

        #logger.debug("TORRENT: " + scrapedtorrent + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + scrapedsize + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)
        
    #Ahora tratamos el servidor directo
    item_local = item.clone()
    servidor = 'openload'
    item_local.quality = ''
    if item.infoLabels['duration']:
        item_local.quality = scrapertools.find_single_match(item.quality, '(\s\[.*?\])')            #Copiamos la duración
    enlace = scrapertools.find_single_match(data, 'button-green-download-big".*?href="([^"]+)"><span class="icon-play">')
    if enlace:
        try:
            devuelve = servertools.findvideosbyserver(enlace, servidor)                             #existe el link ?
            if devuelve:
                enlace = devuelve[0][1]                                                             #Se guarda el link
                item_local.alive = "??"                                                             #Se asume poe defecto que es link es dudoso
                
                #Llama a la subfunción de check_list_links(itemlist) para cada link de servidor
                item_local.alive = servertools.check_video_link(enlace, servidor, timeout=5)        #activo el link ?
                
                #Si el link no está activo se ignora
                if item_local.alive == "??":                #dudoso
                    item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), item_local.quality, str(item_local.language))
                elif item_local.alive.lower() == "no":      #No está activo.  Lo preparo, pero no lo pinto
                    item_local.title = '[COLOR red][%s][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.alive, servidor.capitalize(), item_local.quality, str(item_local.language))
                    logger.debug(item_local.alive + ": ALIVE / " + title + " / " + servidor + " / " + enlace)
                    raise
                else:               #Sí está activo
                    item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), item_local.quality, str(item_local.language))
                    
                #Preparamos el resto de variables de Item para ver los vídeos en directo    
                item_local.action = "play"
                item_local.server = servidor
                item_local.url = enlace
                item_local.title = item_local.title.replace("[]", "").strip()
                item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title).strip()
                item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title).strip()
                itemlist.append(item_local.clone())
                
                #logger.debug(item_local)
                    
        except:
            pass

    return itemlist

    
def actualizar_titulos(item):
    logger.info()
    itemlist = []
    
    from platformcode import launcher
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    if item.extra == "titulo":
        item.url = host + "?s=" + texto

    elif item.extra == "año":
        item.url = host + "weli/" + texto + "/"
    else:
        item.extra == "imdb"
        item.url = host + "imdb/" + texto + "/"
    if texto != '':
        return listado(item)
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = host
            item.extra = "peliculas"
            item.channel = "alltorrents"

            itemlist = listado(item)
            if itemlist[-1].title == "Página siguiente >>":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
