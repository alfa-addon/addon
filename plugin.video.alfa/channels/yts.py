# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from lib import generictools
from platformcode import logger

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel = item.channel,
                         title = "Browse",
                         action = "movies",
                         opt = 0,
                         url = "https://yts.am/browse-movies"
                        ))

    itemlist.append(Item(channel = item.channel,
                         title = "Popular",
                         action = "movies",
                         opt = 1,
                         url = "https://yts.am" ))    

    itemlist.append(Item(channel = item.channel,
                         title = "Search",
                         action = "search",
                         opt = 0,
                         url = "https://yts.am/browse-movies"
                        ))

    return itemlist

def movies(item):
    logger.info()
    itemlist = []
    infoLabels = {}
    data = httptools.downloadpage(item.url).data

    patron = '(?s)class="browse-movie-wrap.*?a href="([^"]+).*?' #Movie link
    patron += 'img class.*?src="([^"]+).*?' #Image
    patron += 'movie-title">.*?([^<]+)' #Movie title
    patron += '.*?year">(.*?)<' #Year

    matches = scrapertools.find_multiple_matches(data, patron)
    idx = 0

    for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:
        if item.opt == 1:
            scrapedthumbnail = 'https://yts.am' + scrapedthumbnail
            infoLabels['plot'] = findplot(scrapedurl)

        itemlist.append(Item(action = "findvideo",
                            channel = item.channel,
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
        pattern = '(?s)href="([^"]+)">Next.*?'
        next_page = scrapertools.find_single_match(data, pattern)

        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                action="movies",
                                title='Next >>>',
                                url='https://yts.am' + next_page))

    return itemlist

def findplot(url):
    data = httptools.downloadpage(url).data

    pattern = '(?s)<p class="hidden-xs">(.*?)</p>' #Synopsis

    plot = scrapertools.find_single_match(data, pattern)

    return plot

def findvideo(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data

    patron = '(?s)modal-quality.*?<span>(.*?)</span>' #Quality
    patron += '.*?size">(.*?)</p>' #Type
    patron += '.*?href="([^"]+)" rel' #Torrent link

    matches = scrapertools.find_multiple_matches(data, patron)
    
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
        item.url = 'https://yts.am/browse-movies/' + text + '/all/all/0/latest'
        itemlist = movies(item)

        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []