# -*- coding: utf-8 -*-
# -*- Channel Halloween -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import jsontools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www.imdb.com/list/ls027655523/?sort=list_order,asc&st_dt=&mode=detail&page='


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()
    item.url = host
    item.first = 60
    item.last = 80
    item.page = 1
    return list_all(item)


def list_all(item):
    logger.info()
    from core import jsontools
    itemlist = []

    data = get_source('%s%s' % (host, item.page))
    data = scrapertools.find_single_match(data, '"itemListElement":([^\]]+)\]')
    data = data + ']'
    #logger.debug(data)
    movie_list = eval(data)
    for movie in movie_list[item.first:item.last]:

        IMDBNumber = movie['url'].replace('title','').replace('/','')


        new_item = Item(channel='search', contentType='movie', action='do_search',
                             infoLabels={'imdb_id': IMDBNumber})

        #new_item.infoLabels = tmdb.find_and_set_infoLabels(new_item)
        itemlist.append(new_item)
        logger.debug('id %s' % IMDBNumber)
        #logger.debug(new_item)


    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    for movie in itemlist:
        movie.title = movie.infoLabels['title']
        movie.wanted = movie.title

    if item.last + 20 < len(movie_list):
        first = item.last
        last = item.last + 20
        page = item.page
    else:
        first = 0
        last = 20
        page = item.page + 1

    itemlist.append(Item(channel=item.channel, title='Siguiente >>', action='list_all',
                         last=last, first=first, page=page))
    return itemlist
