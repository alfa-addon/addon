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

host = 'http://www.elitetorrent.biz'


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_buscar = get_thumb("search.png")

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host, extra="peliculas", thumbnail=thumb_pelis))
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series", thumbnail=thumb_series))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host, thumbnail=thumb_buscar))

    return itemlist
    
    
def submenu(item):
    logger.info()
    itemlist = []
    
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist     #Algo no funciona, pintamos lo que tenemos
    
    patron = '<div class="cab_menu">.*?<\/div>'     #Menú principal
    data1 = scrapertools.get_match(data, patron)
    patron = '<div id="menu_langen">.*?<\/div>'     #Menú de idiomas
    data1 += scrapertools.get_match(data, patron)
    
    patron = '<a href="(.*?)".*?title="(.*?)"'      #Encontrar todos los apartados
    matches = re.compile(patron, re.DOTALL).findall(data1)
    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data1)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('utf8').strip()
        scrapedtitle = scrapedtitle.replace(" torrent", "").replace(" Torrent", "").replace("Series y ", "").title()
        
        if "castellano" in scrapedtitle.lower():    #Evita la entrada de peliculas castellano del menú de idiomas
            continue
        
        if item.extra == "series":                  #Tratamos Series
            if not "/serie" in scrapedurl:
                continue
        else:                                       #Tratamos Películas
            if "/serie" in scrapedurl:
                continue
        
        itemlist.append(item.clone(action="listado", title=scrapedtitle, url=scrapedurl))
            
    if item.extra == "series":      #Añadimos Series VOSE que está fuera del menú principal
        itemlist.append(item.clone(action="listado", title="Series VOSE", url=host + "/series-vose/"))
    
    return itemlist
    

def listado(item):
    logger.info()
    itemlist = []

    # Descarga la página
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    if not data:        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    patron = '<div id="principal">.*?<\/nav><\/div><\/div>'
    data = scrapertools.find_single_match(data, patron)
    
    patron = '<li>.*?<a href="(.*?)".*?'        #url
    patron += 'title="(.*?)".*?'                #título
    patron += 'src="(.*?)".*?'                  #thumb
    patron += "title='(.*?)'.*?"                #categoría, idioma
    patron += '"><i>(.*?)<\/i><\/span.*?'       #calidad
    patron += '="dig1">(.*?)<.*?'               #tamaño
    patron += '="dig2">(.*?)<\/span><\/div>'    #tipo tamaño

    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches and not '<title>503 Backend fetch failed</title>' in data:       #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedcategory, scrapedcalidad, scrapedsize, scrapedsizet in matches:
        item_local = item.clone()           #Creamos copia de Item para trabajar
        
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').strip()
        title = title.replace(" torrent", "").replace(" Torrent", "").replace("Series y ", "")
        item_local.url = urlparse.urljoin(host, scrapedurl)
        item_local.thumbnail = urlparse.urljoin(host, scrapedthumbnail)
        
        if "---" in scrapedcalidad:         #limpiamos calidades
            scrapedcalidad = ''
        if "microhd" in title.lower():
            item_local.quality = "microHD"
        if not "/series-vose/" in item.url and not item_local.quality:
            item_local.quality = scrapedcalidad
        if scrapertools.find_single_match(item_local.quality, r'\d+\.\d+'):
            item_local.quality = ''
        if not item_local.quality and ("DVDRip" in title or "HDRip" in title or "BR-LINE" in title or "HDTS-SCREENER" in title or "BDRip" in title or "BR-Screener" in title or "DVDScreener" in title or "TS-Screener" in title):
            item_local.quality = scrapertools.find_single_match(title, r'\((.*?)\)')
            item_local.quality = item_local.quality.replace("Latino", "")
        if not scrapedsizet:
            scrapedsize = ''
        else:
            item_local.quality += ' [%s %s]' % (scrapedsize.replace(".", ","), scrapedsizet)
        
        item_local.language = []            #Verificamos el idioma por si encontramos algo
        if "latino" in scrapedcategory.lower() or "latino" in item.url or "latino" in title.lower():
            item_local.language += ["LAT"]
        if "ingles" in scrapedcategory.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
            if "VOSE" in scrapedcategory.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
                item_local.language += ["VOS"]
            else:
                item_local.language += ["VO"]
        if "dual" in scrapedcategory.lower() or "dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
        
        #Limpiamos el título de la basuna innecesaria
        title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "")
        title = title.replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("(HDRip)", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "")
        title = re.sub(r'\??\s?\d*?\&.*', '', title).title().strip()
        
        if item_local.extra == "peliculas":     #preparamos Item para películas
            if "/serie" in scrapedurl or "/serie" in item.url:
                continue
        if not "/serie" in scrapedurl and not "/serie" in item.url:
            item_local.contentType = "movie"
            item_local.contentTitle = title
            item_local.extra = "peliculas"
        
        if item_local.extra == "series":     #preparamos Item para series
            if not "/serie" in scrapedurl and not "/serie" in item.url:
                continue
        if "/serie" in scrapedurl or "/serie" in item.url:
            item_local.contentType = "episode"
            item_local.extra = "series"
            epi_mult = scrapertools.find_single_match(item_local.url, r'cap.*?-\d+-al-(\d+)')
            item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'temp.*?-(\d+)')
            item_local.contentEpisodeNumber = scrapertools.find_single_match(item_local.url, r'cap.*?-(\d+)')
            if not item_local.contentSeason:
                item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'-(\d+)[x|X]\d+')
            if not item_local.contentEpisodeNumber:
                item_local.contentEpisodeNumber = scrapertools.find_single_match(item_local.url, r'-\d+[x|X](\d+)')
            if item_local.contentSeason < 1:
                item_local.contentSeason = 1
            if item_local.contentEpisodeNumber < 1:
                item_local.contentEpisodeNumber = 1
            item_local.contentSerieName = title
            if epi_mult:
                title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(epi_mult).zfill(2))                  #Creamos un título con el rango de episodios
            else:
                title = '%sx%s ' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
        
        item_local.action = "findvideos"
        item_local.title = title.strip()
        item_local.infoLabels['year'] = "-"
        
        #Pasamos a TMDB cada Item, para evitar el efecto memoria de tmdb
        if item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global, pasamos
            tmdb.set_infoLabels(item_local, True)
        
        itemlist.append(item_local.clone())     #Pintar pantalla
   
    #if not item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Pasamos a TMDB la lista completa Itemlist
    #tmdb.set_infoLabels(itemlist, True)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    # Extrae el paginador
    patron = '<div class="paginacion">.*?<span class="pagina pag_actual".*?'
    patron += "<a href='([^']+)'.*?"                    #url siguiente página
    patron += 'class="pagina">(\d+)<'                #próxima página
    matches = scrapertools.find_single_match(data, patron)
    
    patron = 'class="pagina pag_sig">Siguiente.*?'
    patron += "<a href='.*?\/page\/(\d+)\/"             #total de páginas
    last_page = scrapertools.find_single_match(data, patron)
    if not last_page:
        patron = '<div class="paginacion">.*?'
        patron += 'class="pagina">(\d+)<\/a><\/div><\/nav><\/div><\/div>'       #total de páginas
        last_page = scrapertools.find_single_match(data, patron)

    if matches:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        if last_page:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s de %s' % (int(matches[1]) - 1, last_page)
        else:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s' % (int(matches[1]) - 1)
        
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=scrapedurl, extra=item.extra))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    #Bajamos los datos de la página
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    #data = unicode(data, "utf-8", errors="replace")
    
    #Añadimos el tamaño para todos
    size = scrapertools.find_single_match(item.quality, '\s\[(\d+,?\d*?\s\w[b|B]s)\]')
    if size:
        item.title = re.sub('\s\[\d+,?\d*?\s\w[b|B]s\]', '', item.title)        #Quitamos size de título, si lo traía
        item.title = '%s [%s]' % (item.title, size)                             #Agregamos size al final del título
        item.quality = re.sub('\s\[\d+,?\d*?\s\w[b|B]s\]', '', item.quality)    #Quitamos size de calidad, si lo traía
        item.quality = '%s [%s]' % (item.quality, size)                         #Agregamos size al final de calidad
        item.quality = item.quality.replace("G", "G ").replace("M", "M ")       #Se evita la palabra reservada en Unify

    patron_t = '<div class="enlace_descarga".*?<a href="(.*?\.torrent)"'
    link_torrent = scrapertools.find_single_match(data, patron_t)
    link_torrent = urlparse.urljoin(item.url, link_torrent)
    link_torrent = link_torrent.replace(" ", "%20")             #sustituimos espacios por %20, por si acaso
    #logger.info("link Torrent: " + link_torrent)
    
    patron_m = '<div class="enlace_descarga".*?<a href="(magnet:?.*?)"'
    link_magnet = scrapertools.find_single_match(data, patron_m)
    link_magnet = urlparse.urljoin(item.url, link_magnet)
    #logger.info("link Magnet: " + link_magnet)
    
    if not link_torrent and not link_magnet:                    #error
        logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron_t + " / " + patron_m + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    #Generamos una copia de Item para trabajar sobre ella
    item_local = item.clone()

    #Ahora pintamos el link del Torrent, si lo hay
    if link_torrent:		# Hay Torrent ?
        if item_local.quality:
            item_local.quality += " "
        item_local.quality += "[Torrent]"
        item_local.url = link_torrent
        item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))        #Preparamos título de Torrent
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title)    #Quitamos etiquetas vacías
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title)          #Quitamos colores vacíos
        item_local.alive = "??"         #Calidad del link sin verificar
        item_local.action = "play"      #Visualizar vídeo
        item_local.server = "torrent"   #Seridor Torrent
        
        itemlist.append(item_local.clone())     #Pintar pantalla
    
    #Ahora pintamos el link del Magnet, si lo hay
    if link_magnet:		# Hay Magnet ?
        if item_local.quality:
            item_local.quality += " "
        item_local.quality = item_local.quality.replace("[Torrent]", "") + "[Magnet]"
        item_local.url = link_magnet
        item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))        #Preparamos título de Magnet
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title)    #Quitamos etiquetas vacías
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title)          #Quitamos colores vacíos
        item_local.alive = "??"         #Calidad del link sin verificar
        item_local.action = "play"      #Visualizar vídeo
        item_local.server = "torrent"   #Seridor Torrent
        
        itemlist.append(item_local.clone())     #Pintar pantalla
    
    #logger.debug("TORRENT: " + link_torrent + "MAGNET: " + link_magnet + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + size + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
    #logger.debug(item_local)

    return itemlist


def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.url = host + "?s=%s&x=0&y=0" % texto
        itemlist = listado(item)
        
        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = host
            item.extra = "peliculas"

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
