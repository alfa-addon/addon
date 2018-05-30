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

host = "http://cuevana2espanol.com/"
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'directo', 'yourupload', 'openload', 'dostream']

def load_data(url):
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    return data

def mainlist(item):
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "movies", 
        url = host + "ver-pelicula-online", thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Favoritas", action = "movies", 
        url = host + "calificaciones", thumbnail = get_thumb("favorites", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Destacadas", action = "movies", 
        url = host + "tendencias", thumbnail = get_thumb("hot", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Ranking IMDB", action = "moviesIMDB", 
        url = host + "raking-imdb", thumbnail = get_thumb("hot", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Busqueda", folder=False, text_bold=True,
        thumbnail = get_thumb("search", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por Letra", action = "letters",
        url = host, thumbnail = get_thumb("alphabet", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", 
        url = host + "?s=", thumbnail = get_thumb("search", auto = True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def movies(item):
    itemlist = []

    data = load_data(item.url)
    pattern = 'class="poster"><img src="([^"]+)" alt="([^"]+)".*?'
    pattern += '</span> (.*?)</div>.*?'
    pattern += 'href="([^"]+)".*?'
    pattern += '<span>(\d+)</span>.*?'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for img, title, ranking, link, age in matches:
        itemTitle = "%s [COLOR yellow](%s)[/COLOR] [COLOR blue](%s)[/COLOR]" % (title, ranking, age)
        itemlist.append(Item(channel = item.channel, title=itemTitle, fulltitle=title, thumbnail=img, 
            url=link, action="findvideos"))

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page:
        itemlist.append(Item(channel = item.channel, title="Siguiente Pagina", 
            url=next_page, action="movies"))

    return itemlist

def moviesIMDB(item):
    itemlist = []

    data = load_data(item.url)
    pattern = '"poster"><a href="([^"]+)"><img src="([^"]+)".*?'
    pattern += 'class="puesto">(\d+)</div>.*?'
    pattern += '"rating">(.*?)</div>.*?'
    pattern += '"title">.*?>(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, img, rank, rating, title in matches:
        itemTitle = "%s [COLOR blue](#%s)[/COLOR] [COLOR yellow](%s)[/COLOR]" % (title, rank, rating)
        img = img.replace('-90x135', '')

        itemlist.append(Item(channel = item.channel, title=itemTitle, fulltitle=title, thumbnail=img, 
            url=link, action="findvideos"))

    return itemlist

def byLetter(item):
    itemlist = []
    letter = item.extra

    pageForNonce = load_data(item.url)
    nonce = scrapertools.find_single_match(pageForNonce, '"nonce":"([^"]+)"')
    raw = httptools.downloadpage('http://cuevana2espanol.com/wp-json/dooplay/glossary/?term=%s&nonce=%s&type=all' % (letter, nonce)).data
    json = jsontools.load(raw).items()
    logger.info(nonce)

    for movie in json:
        data = movie[1]
        itemTitle = data['title']
        if 'year' in data:
            itemTitle += " [COLOR blue](%s)[/COLOR]" % data['year'] 
        if data['imdb']:
            itemTitle += " [COLOR yellow](%s)[/COLOR]" % data['imdb']

        itemlist.append(Item(channel = item.channel, title=itemTitle, fulltitle=data['title'], url=data['url'], 
            thumbnail=data['img'].replace('-90x135', ''), action="findvideos"))

    return itemlist

def letters(item):
    itemlist = []
    letter = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for let in letter:
        itemlist.append(item.clone(title=let, extra=let.lower(), action="byLetter"))

    return itemlist

def searchMovies(item):
    itemlist = []

    data = load_data(item.url)
    pattern = 'class="image">.*?href="([^"]+)".*?'
    pattern += 'src="([^"]+)" alt="([^"]+)".*?'
    pattern += 'class="year">(\d+)</span>.*?'
    pattern += '<p>(.*?)</p>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, img, title, year, plot in matches:
        itemTitle = "%s [COLOR blue](%s)[/COLOR]" % (title, year)
        fullimg = img.replace('-150x150', '')
        itemlist.append(Item(channel = item.channel, title=itemTitle, fulltitle=title, thumbnail=fullimg,
            url=link, plot=plot, action="findvideos"))

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page:
        itemlist.append(Item(channel = item.channel, title="Siguiente Pagina", 
            url=next_page, action="searchMovies"))

    return itemlist

def search(item, text):
    text = text.lower().replace(' ', '+')
    item.url += text

    return searchMovies(item)

def GKPluginLink(hash):
    hashdata = urllib.urlencode({r'link':hash})
    json = httptools.downloadpage('https://player4.cuevana2.com/plugins/gkpluginsphp.php', post=hashdata).data
    return jsontools.load(json)['link'] if json else ''

def getContent(item, data):
    item.infoLabels["year"] = scrapertools.find_single_match(data, 'class="date">.*?(\d+)</span>')
    item.plot = scrapertools.find_single_match(data, 'class="wp-content"><p>(.*?)</p>')
    genres = ''
    for genre in scrapertools.find_multiple_matches(data, '/genero/.*?"tag">(.*?)</a>'):
        genres += genre + ', '

    item.infoLabels['genre'] = genres.strip(', ')

def findvideos(item):
    logger.info()
    itemlist = []

    data = load_data(item.url)
    getContent(item, data)
    """
    if item.extra:
        getContentShow(data, item)
    else:
        getContentMovie(data, item)
    """
    pattern = '<iframe class="metaframe rptss" src="([^"]+)"'

    #itemlist.append(Item(channel = item.channel, title=item.url))
    for link in scrapertools.find_multiple_matches(data, pattern):
        #php.*?=(\w+)&
        #url=(.*?)&
        if 'player4' in link:
            logger.info("CUEVANA LINK %s" % link)
            if r'ir.php' in link:
                link = scrapertools.find_single_match(link, 'php.*?=(.*)').replace('%3A', ':').replace('%2F', '/')
                logger.info("CUEVANA IR %s" % link)
            elif r'gdv.php' in link:
                # google drive hace lento la busqueda de links, ademas no es tan buena opcion y es el primero que eliminan
                continue
            else:
                link = scrapertools.find_single_match(link, 'php.*?=(\w+)')
                link = GKPluginLink(link)
                if not link:
                    continue
            
            title = "[COLOR blue]Servidor [%s][/COLOR]"
        elif 'youtube' in link:
            title = "[COLOR yellow]Ver Trailer (%s)[/COLOR]"
        else: # En caso de que exista otra cosa no implementada, reportar si no aparece pelicula
            continue

        # GKplugin puede devolver multiples links con diferentes calidades, si se pudiera colocar una lista de opciones
        # personalizadas para Directo, se agradece, por ahora solo devuelve el primero que encuentre
        if type(link) is list:
            link = link[0]['link']
        if r'chomikuj.pl' in link:
            # En algunas personas la opcion CH les da error 401
            link += "|Referer=https://player4.cuevana2.com/plugins/gkpluginsphp.php" 

        itemlist.append(
            item.clone(
                channel = item.channel, 
                title=title, 
                url=link, action='play'))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist):
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     fulltitle = item.fulltitle
                                     ))
    return itemlist
