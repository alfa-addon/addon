# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from lib import generictools
from platformcode import logger

URL_BROWSE = "https://yts.am/browse-movies"
URL = "https://yts.am"

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel = item.channel,
                         title = "Explorar por generos",
                         action = "categories",
                         opt = 'genre',
                         url = URL_BROWSE
                         ))

    itemlist.append(Item(channel = item.channel,
                         title = "Explorar por calidad",
                         action = "categories",
                         opt = 'quality',
                         url = URL_BROWSE
                         ))

    itemlist.append(Item(channel = item.channel,
                         title = "Explorar películas",
                         action = "movies",
                         opt = 0,
                         url = URL_BROWSE
                        ))

    itemlist.append(Item(channel = item.channel,
                         title = "Más populares",
                         action = "movies",
                         opt = 1,
                         url = URL ))    

    itemlist.append(Item(channel = item.channel,
                         title = "Buscar",
                         action = "search",
                         opt = 0,
                         url = URL_BROWSE
                        ))

    return itemlist


def categories(item):
    logger.info()
    itemList = []
    data = httptools.downloadpage(item.url).data
    
    block = scrapertools.find_single_match( data, '(?s)<.*?="' + item.opt + '">(.*?)</select>')
    pattern = '<option value=".*?">(?!All)(.*?)</option>'
    categories = scrapertools.find_multiple_matches( block, pattern )

    for category in categories:
        url = URL_BROWSE + '/0/all/' + category + '/0/latest' if item.opt == "genre" else URL_BROWSE + '/0/' + category + '/all/0/latest'

        itemList.append( Item( action = "movies",
                               channel = item.channel,
                               title = category,
                               url = url ))

    return itemList

def movies(item):
    logger.info()
    itemlist = []
    infoLabels = {}
    data = httptools.downloadpage(item.url).data

    pattern = '(?s)class="browse-movie-wrap.*?a href="([^"]+).*?' #Movie link
    pattern += 'img class.*?src="([^"]+).*?' #Image
    pattern += 'movie-title">.*?([^<]+)' #Movie title
    pattern += '.*?year">(.*?)<' #Year

    matches = scrapertools.find_multiple_matches(data, pattern)
    idx = 0

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:
        if item.opt == 1:
            scrapedthumbnail = URL + scrapedthumbnail
        infoLabels['year'] = year

        itemlist.append(Item(action = "findvideo",
                            channel = item.channel,
                            contentTitle = scrapedtitle,
                            infoLabels = infoLabels,
                            title = scrapedtitle + ' (' + year + ')',
                            thumbnail = scrapedthumbnail,
                            url = scrapedurl
                            ))
        idx += 1
        if item.opt == 1 and idx == 4:
            break
    if itemlist != []:
        actual_page = item.url
        nextPattern = '(?s)href="([^"]+)">Next.*?'
        next_page = scrapertools.find_single_match(data, nextPattern)

        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                action="movies",
                                title='Next >>>',
                                url=URL + next_page))

    tmdb.set_infoLabels_itemlist( itemlist, seekTmdb=True)

    return itemlist

def findvideo(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data

    pattern = '(?s)modal-quality.*?<span>(.*?)</span>' #Quality
    pattern += '.*?size">(.*?)</p>' #Type
    pattern += '.*?href="([^"]+)" rel' #Torrent link

    matches = scrapertools.find_multiple_matches(data, pattern)
    
    for quality, videoType, link in matches:
        
        title = item.title + ' ' + quality + ' ' + videoType
        itemlist.append(Item(channel = item.channel,
                            title=title,
                            url = link,
                            thumbnail = item.thumbnail,
                            action='play',
                            server='torrent'
                            ))
    
    return itemlist

def search(item, text):
    logger.info('search: ' + text)

    try:
        item.url = URL_BROWSE + text + '/all/all/0/latest'
        itemlist = movies(item)

        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []