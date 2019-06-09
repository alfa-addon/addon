# -*- coding: utf-8 -*-
import re
import urllib
from channelselector import get_thumb

from core.item import Item
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from platformcode import config, logger
from channels import autoplay

host = "http://www.cuevana2.com/"
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'directo', 'yourupload', 'openload', 'dostream']

### MENUS ###

def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    # PELICULAS
    itemlist.append(Item(channel = item.channel, title = "--- Peliculas ---", folder=False, text_bold=True))

    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "movies", 
        url = host + "pelicula", thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "genre", 
        url = host + "pelicula", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "age", 
        url = host + "pelicula", thumbnail = get_thumb("year", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Favoritas", action = "movies", 
        url = host + "peliculas-destacadas", thumbnail = get_thumb("favorites", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", 
        url = host + "pelicula/?s=", thumbnail = get_thumb("search", auto = True)))

    # SERIES
    itemlist.append(Item(channel = item.channel, title = "--- Series ---", folder=False, text_bold=True))

    itemlist.append(Item(channel = item.channel, title = "Todas las Series", action = "shows", 
        url = host + "listar-series", thumbnail = get_thumb("tvshows", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", extra='1', 
        url = host + "listar-series", thumbnail = get_thumb("search", auto = True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

### FIN MENUS ###
def inArray(arr, arr2):
    for word in arr:
        if word not in arr2:
            return False

    return True

def load_data(url):
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    return data

def redirect_url(url, parameters=None):
    data = httptools.downloadpage(url, post=parameters)
    logger.info(data.url)
    return data.url

def put_movies(itemlist, item, data, pattern):
    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, img, title, rating, plot in matches:
        if 'pelicula' in link:
            itemTitle = "%s [COLOR yellow](%s/100)[/COLOR]" % (title, rating)
            itemlist.append(Item(channel = item.channel, title=itemTitle, fulltitle=title, thumbnail=img, 
                url=link, plot=plot, action="findvideos"))
            logger.info(link)

    return itemlist

def put_episodes(itemlist, item, text):
    pattern = '<li>.*?ref="([^"]+).*?"tit">(.*?)</span>'

    matches = scrapertools.find_multiple_matches(text, pattern)
    for link, title in matches:
        itemlist.append(item.clone(title=title, fulltitle=item.title, url=link, action='findvideos', extra=1))

def episodes(item):
    logger.info()
    itemlist = []

    data = load_data(item.url)
    seasonsPattern = '"#episodios(\d+)".*?>(.*?)</a>'
    episodesPattern = 'id="episodios%s">(.*?)</ul>'

    matches = scrapertools.find_multiple_matches(data, seasonsPattern)
    for season, title in matches:
        itemlist.append(Item(channel = item.channel, title="[COLOR blue]%s[/COLOR]" % title, 
            folder=False, text_bold=True))
        episodeMatches = scrapertools.find_single_match(data, episodesPattern % season)
        put_episodes(itemlist, item, episodeMatches)

    return itemlist

def shows(item):
    logger.info()
    itemlist = []

    data = load_data(item.url)
    pattern = '"in"><a href="([^"]+)">(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, title in matches:
        itemlist.append(Item(channel = item.channel, title=title, url=host + link, action="episodes"))

    return itemlist

def movies(item):
    logger.info()
    itemlist = []

    #descarga la pagina html
    data = load_data(item.url)

    #patron para buscar las peliculas
    pattern = '<a href="([^"]+)"><div class="img">' #link
    pattern += '<img width="120" height="160" src="([^"]+)" class="attachment-thumbnail wp-post-image" alt="([^"]+)".*?' #img and title
    pattern += '<span style="width:([0-9]+)%">.*?'
    pattern += '"txt">(.*?)</div>' # text

    put_movies(itemlist, item, data, pattern)

    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page:
        itemlist.append(Item(channel = item.channel, title='Siguiente Pagina', url=next_page, action="movies"))

    #coloca las peliculas encontradas en la lista
    return itemlist

def searchShows(itemlist, item, texto):
    texto = texto.lower().split()
    data = load_data(item.url)

    pattern = '"in"><a href="([^"]+)">(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, title in matches:
        keywords = title.lower().split()
        logger.info(keywords)
        logger.info(texto)

        if inArray(texto, keywords):
            itemlist.append(Item(channel = item.channel, title=title, url=host + link, action="episodes"))

def searchMovies(itemlist, item, texto):
    data = load_data(item.url + texto)
    #patron para buscar las peliculas
    pattern = '<a href="([^"]+)"><div class="img">' #link
    pattern += '<img width="120" height="160" src="([^"]+)" class="attachment-thumbnail wp-post-image" alt="([^"]+)".*?' #img and title
    pattern += '<span style="width:([0-9]+)%">.*?'
    pattern += '"txt">(.*?)</div>' # text

    #ahora ya no se necesita el do while
    put_movies(itemlist, item, data, pattern)
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')

    if next_page:
        itemlist.append(Item(channel = item.channel, title='Siguiente Pagina', url=next_page, action="movies"))

def search(item, texto):
    itemlist = []

    if item.extra:
        searchShows(itemlist, item, texto)
    else:
        searchMovies(itemlist, item, texto)

    return itemlist

def by(item, pattern):
    logger.info()
    itemlist = []

    #descarga la pagina html
    data = load_data(item.url)

    #patron para buscar en la pagina
    pattern = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">&&</a>'.replace('&&', pattern)

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, genre in matches:
        itemlist.append(Item(channel = item.channel, title=genre, url=link, action="movies"))

    return itemlist

def genre(item):
    return by(item, '(\D+)')

def age(item):
    return by(item, '(\d+)')

def GKPluginLink(hash):
    hashdata = urllib.urlencode({r'link':hash})
    try:
        json = httptools.downloadpage('https://player4.cuevana2.com/plugins/gkpluginsphp.php', post=hashdata).data
    except:
        return None
    logger.info(jsontools.load(json))

    data = jsontools.load(json) if json else False
    if data:
        return data['link'] if 'link' in data else None
    else:
        return None

def RedirectLink(hash):
    hashdata = urllib.urlencode({r'url':hash})
    return redirect_url('https://player4.cuevana2.com/r.php', hashdata)

def OpenloadLink(hash):
    hashdata = urllib.urlencode({r'h':hash})
    json = httptools.downloadpage('https://api.cuevana2.com/openload/api.php', post=hashdata).data
    logger.info("CUEVANA OL JSON %s" % json)
    data = jsontools.load(json) if json else False

    return data['url'] if data['status'] == 1 else None

#el pattern esta raro para eliminar los duplicados, de todas formas asi es un lenguaje de programacion verificando su sintaxis
def getContentMovie(data, item):
    item.infoLabels["year"] = scrapertools.find_single_match(data, 'rel="tag">(\d+)</a>')
    genre = ''
    for found_genre in scrapertools.find_multiple_matches(data, 'genero/.*?">(.*?)</a>(?=.*?</p>)'):
        genre += found_genre + ', '
    item.infoLabels["genre"] = genre.strip(', ')

    director = ''
    for found_director in scrapertools.find_multiple_matches(data, 'director/.*?">(.*?)</a>(?=.*?</p>)'):
        director += found_director + ', '
    item.infoLabels["director"] = director.strip(', ')

    item.infoLabels["cast"] = tuple(found_cast for found_cast in scrapertools.find_multiple_matches(
        data, 'reparto/.*?">(.*?)</a>(?=.*?</p>)'))

def getContentShow(data, item):
    item.thumbnail = scrapertools.find_single_match(data, 'width="120" height="160" src="([^"]+)"')
    item.infoLabels['genre'] = scrapertools.find_single_match(data, '-4px;">(.*?)</div>')

def findvideos(item):
    logger.info()
    itemlist = []

    data = load_data(item.url)
    if item.extra:
        getContentShow(data, item)
    else:
        getContentMovie(data, item)
    pattern = '<li data-playerid="([^"]+)'
    subtitles = scrapertools.find_single_match(data, 'li data-playerid=".*?sub=([^"]+)"')

    title = "[COLOR blue]Servidor [%s][/COLOR]"
    #itemlist.append(Item(channel = item.channel, title=item.url))
    for link in scrapertools.find_multiple_matches(data, pattern):
        #php.*?=(\w+)&
        #url=(.*?)&
        if 'player4' in link:
            # Por si acaso están los dos metodos, de todas maneras esto es corto circuito
            if r'ir.php' in link:
                link = scrapertools.find_single_match(link, 'php\?url=(.*?)&').replace('%3A', ':').replace('%2F', '/')
                logger.info("CUEVANA IR %s" % link)
            elif r'irgoto.php' in link:
                link = scrapertools.find_single_match(link, 'php\?url=(.*?)&').replace('%3A', ':').replace('%2F', '/')
                link = RedirectLink(link)
                logger.info("CUEVANA IRGOTO %s" % link)
            elif r'gdv.php' in link:
                # google drive hace lento la busqueda de links, ademas no es tan buena opcion y es el primero que eliminan
                continue
            else:
                link = scrapertools.find_single_match(link, 'php.*?=(\w+)&')
                link = GKPluginLink(link)
            
        elif 'openload' in link:
            link = scrapertools.find_single_match(link, '\?h=(\w+)&')
            logger.info("CUEVANA OL HASH %s" % link)
            link = OpenloadLink(link) 
            logger.info("CUEVANA OL %s" % link)

        elif 'youtube' in link:
            title = "[COLOR yellow]Ver Trailer (%s)[/COLOR]"
        else: # En caso de que exista otra cosa no implementada, reportar si no aparece pelicula
            continue

        if not link:
            continue

        # GKplugin puede devolver multiples links con diferentes calidades, si se pudiera colocar una lista de opciones
        # personalizadas para Directo, se agradece, por ahora solo devuelve el primero que encuentre
        if type(link) is list:
            link = link[0]['link']
        if r'chomikuj.pl' in link:
            # En algunas personas la opcion CH les da error 401
            link += "|Referer=https://player4.cuevana2.com/plugins/gkpluginsphp.php" 
        elif r'vidcache.net' in link:
            # Para que no salga error 500
            link += '|Referer=https://player4.cuevana2.com/yourupload.com.php'

        itemlist.append(
            item.clone(
                channel = item.channel, 
                title=title, 
                url=link, action='play', 
                subtitle=subtitles))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist):
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     fulltitle = item.fulltitle
                                     ))
    return itemlist
