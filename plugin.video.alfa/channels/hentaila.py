# -*- coding: utf-8 -*-
import sys
import re
import datetime
import xbmcgui

from core import httptools, scrapertools, servertools, tmdb, jsontools
from core.item import Item
from platformcode import config, logger, platformtools
from channelselector import get_thumb

host = 'https://hentaila.com'
IDIOMAS = {"Versión original subtitulada español": "VOSE"}
list_language = list(IDIOMAS.values())

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Novedades",
            action = "newest",
            fanart = item.fanart,
            thumbnail = get_thumb("newest", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Más votados",
            action = "list_all",
            param = "",
            url = host + "/directorio?filter=popular",
            fanart = item.fanart,
            thumbnail = get_thumb("more voted", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Destacados",
            action = "list_all",
            param = "hot",
            url = host,
            fanart = item.fanart,
            thumbnail = get_thumb("hot", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Nuevos episodios",
            action = "list_all",
            param = "newepisodes",
            url = host,
            fanart = item.fanart,
            thumbnail = get_thumb("new episodes", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel =  item.channel,
            title = "Próximos estrenos",
            action = "premieres",
            param = "",
            url = host + '/estrenos-hentai',
            fanart = item.fanart,
            thumbnail = get_thumb("premieres", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Categorías",
            action = "categories",
            param = "",
            url = host,
            fanart = item.fanart,
            thumbnail = get_thumb("categories", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Todos",
            action = "list_all",
            param = "",
            url = host + "/directorio",
            fanart = item.fanart,
            thumbnail = get_thumb("all", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Buscar...",
            action = "search",
            param = "",
            url = host + "/api/search",
            fanart = item.fanart,
            thumbnail = get_thumb("search", auto=True)
        )
    )
    return itemlist

def categories(item):
    logger.info()
    itemlist = []
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Por género",
            action = "filter_by_selection",
            param = "genre",
            fanart = item.fanart,
            thumbnail = get_thumb("genres", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Por letra",
            action = "filter_by_selection",
            param = "alphabet",
            fanart = item.fanart,
            thumbnail = get_thumb("alphabet", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Sin censura",
            action = "list_all",
            param = "",
            url = host + "/hentai-sin-censura",
            fanart = item.fanart,
            thumbnail = get_thumb("adults", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Por estado",
            action = "filter_by_selection",
            param = "status",
            fanart = item.fanart,
            thumbnail = get_thumb("on air", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Combinar categorías",
            action = "set_adv_filter",
            param = "",
            filters = {'genre': '', 'alphabet': '', 'censor': '', 'status': '', 'orderby': ''},
            fanart = item.fanart,
            thumbnail = get_thumb("categories", auto=True)
        )
    )
    return itemlist

def filter_by_selection(item, clearUrl = False):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(host + "/directorio").data
    if item.param == 'genre':
        pattern = '(?s)a href="([^"]+)" class="">([^<]+)'
        matches = scrapertools.find_multiple_matches(data, pattern)
    elif item.param == 'alphabet':
        sectptn = '(?s)class="alpha-list".+?/section>'
        sectmatch = scrapertools.find_single_match(data, sectptn)
        pattern = '(?s)a href="([^"]+).+?>([^<]+)'
        matches = scrapertools.find_multiple_matches(sectmatch, pattern)
    elif item.param == 'censor':
        matches = (dict({'?uncensored=on': 'Solo sin censura'}).items)()
    elif item.param == 'status':
        matches = dict({'?status%5B1%5D=on': 'Solo en emisión',
                        '?status%5B2%5D=on': 'Solo finalizados'}).items()
    elif item.param == 'orderby':
        matches = dict({'?filter=popular': 'Ordenar por popularidad',
                        '?filter=recent': 'Ordenar por más recientes'}).items()
    for url, title in matches:
        if clearUrl == True:
            url = url.replace('?', '')
        else:
            if item.param != 'genre':
                url = '/directorio' + url
            url = host + url
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                title = title,
                fanart = item.fanart,
                url = url,
            )
        )
    return itemlist

def set_adv_filter(item):
    logger.info()
    genreitems = filter_by_selection(Item(param = "genre"), clearUrl = True)
    genres = ['Predeterminado (todos)']
    for i in genreitems:
        genres.append(i.title)
    result = platformtools.dialog_select('Elige un género', genres, useDetails=False)
    if result != -1 and result != 0:
        item.filters['genre'] = genreitems[result - 1]
    elif result == -1:
        return True

    alphaitems = filter_by_selection(Item(param = "alphabet"), clearUrl = True)
    letters = []
    letters.append('Predeterminado (todas)')
    for i in alphaitems:
        letters.append(i.title)
    result = platformtools.dialog_select('Elige una letra inicial', letters, useDetails=False)
    if result != -1 and result != 0:
        item.filters['alphabet'] = alphaitems[result - 1]
    elif result == -1:
        return True

    censorstates = filter_by_selection(Item(param = "censor"), clearUrl = True)
    censor = []
    censor.append('Predeterminado (con y sin censura)')
    for i in censorstates:
        censor.append(i.title)
    result = platformtools.dialog_select('Elige el tipo de censura', censor, useDetails=False)
    if result != -1 and result != 0:
        item.filters['censor'] = censorstates[result - 1]
    elif result == -1:
        return True

    statusstates = filter_by_selection(Item(param = "status"), clearUrl = True)
    statuses = []
    statuses.append('Predeterminado (ambos)')
    for i in statusstates:
        statuses.append(i.title)
    result = platformtools.dialog_select('Elige el estado de emisión', statuses, useDetails=False)
    if result != -1 and result != 0:
        item.filters['status'] = statusstates[result - 1]
    elif result == -1:
        return True

    statusstates = filter_by_selection(Item(param = "orderby"), clearUrl = True)
    statuses = []
    statuses.append('Predeterminado (ambos)')
    for i in statusstates:
        statuses.append(i.title)
    result = platformtools.dialog_select('Elige cómo ordenar los resultados', statuses, useDetails=False)
    if result != -1 and result != 0:
        item.filters['orderby'] = statusstates[result - 1]

    if item.filters['genre'] or item.filters['alphabet'] or item.filters['censor'] or item.filters['status'] or item.filters['orderby']:
        filtered_url = host
        current_filter = ''
        if item.filters['genre'] != '':
            current_filter += "Género: " + item.filters['genre'].title + ". "
            filtered_url += item.filters['genre'].url
        else:
            filtered_url += '/directorio'
        if item.filters['alphabet'] != '':
            current_filter += 'Inicial: ' + item.filters['alphabet'].title + '. '
            filtered_url += '?' + item.filters['alphabet'].url
        if item.filters['censor'] != '':
            current_filter += 'Censura: ' + item.filters['censor'].title + '. '
            filtered_url += '&' + item.filters['censor'].url
        if item.filters['status'] != '':
            current_filter += 'Estado: ' + item.filters['status'].title + '. '
            filtered_url += '&' + item.filters['status'].url
        if item.filters['orderby'] != '':
            current_filter += 'Estado: ' + item.filters['orderby'].title + '. '
            filtered_url += '&' + item.filters['orderby'].url
        filteritem = Item(
            channel =  item.channel,
            fanart = item.fanart,
            param = '',
            url = filtered_url
        )
        return list_all(filteritem)
    else:
        return True

def premieres(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    infoLabels = item.infoLabels
    sectionptn = '(?s)<section class="section section-premier-slider".+?'
    sectionptn += 'section-title[^>]+.([^<]+)'
    sectionptn += '(.+?/section>)'
    sections = scrapertools.find_multiple_matches(data, sectionptn)
    pattern = '(?s)article class="hentai".+?img src=".+?(\d.+?)\..+?".+?'
    pattern += 'h-title[^>]+.([^<]+).+?'
    pattern += 'a href="([^"]+).+?/article>'
    for sectiontitle, section in sections:
        itemlist.append(
            Item(
                channel = item.channel,
                title = '[COLOR=yellow] ═↓═ ' + sectiontitle + ' ═↓═ [/COLOR]',
                thumbnail = host + '/assets/img/media.webp',
                fanart = item.fanart,
            )
        )
        match = scrapertools.find_multiple_matches(section, pattern)
        for scpthumbid, scptitle, scpurl in match:
            itemlist.append(
                Item(
                    action = "episodios",
                    channel = item.channel,
                    contentSerieName = scptitle.strip(),
                    fanart = host + '/uploads/fondos/' + scpthumbid + '.jpg',
                    infoLabels = infoLabels,
                    title = scptitle.strip(),
                    thumbnail = host + '/uploads/portadas/' + scpthumbid + '.jpg',
                    url = host + scpurl
                )
            )
    return itemlist

def newest(item):
    item.url = host + "/directorio?filter=recent"
    item.param = ""
    return list_all(item)

def list_all(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    infoLabels = item.infoLabels
    if item.param == 'hot':
        pattern = '(?s)class="item".+?a href="([^"]+).+?'
        pattern += '>([^<]+).+?'
        pattern += 'class="status.*?>.*?>.*?>([^<]+).+?'
        pattern += '<p>([^<]+).+?'
        pattern += 'class="genres"(.+?/article>).+?'
        pattern += 'img src=".+?(\d+?)\.'
        matches = scrapertools.find_multiple_matches(data, pattern)
        for scpurl, scptitle, scpstatus, scpplot, scpgenres, scpthumbid in matches:
            infoLabels['plot'] = scpplot
            itemlist.append(
                Item(
                    action = "episodios",
                    channel = item.channel,
                    contentSerieName = scptitle.strip(),
                    fanart = host + '/uploads/fondos/' + scpthumbid + '.jpg',
                    infoLabels = infoLabels,
                    title = scptitle.strip(),
                    thumbnail = host + '/uploads/portadas/' + scpthumbid + '.jpg',
                    url = host + scpurl
                )
            )
    elif item.param == 'newepisodes':
        pattern = '(?s)class="hentai episode".+?img src="([^"]+).+?'
        pattern +='num-episode.+?>(?:.+?(\d+?))<.+?'
        pattern += 'h-title.+?>([^<]+).+?'
        pattern += 'time>([^<]+).+?'
        pattern += 'href="/ver/(.*?)-\d+?'
        matches = scrapertools.find_multiple_matches(data, pattern)
        for scpthumbnail, scpepnum, scptitle, scptime, scpurl in matches:
            infoLabels['plot'] = 'Publicado ' + scptime.lower()
            itemlist.append(
                Item(
                    action = "episodios",
                    channel = item.channel,
                    contentSerieName = scptitle.strip(),
                    fanart = host + scpthumbnail,
                    infoLabels = infoLabels,
                    title = scptitle.strip(),
                    thumbnail = host + scpthumbnail,
                    url = host + '/hentai-' + scpurl
                )
            )
    else:
        pattern = '(?s)class="hentai".+?img src=".+?(\d+?)\..+?".+?h-title.+?>([^<]+).+?href="([^"]+)'
        matches = scrapertools.find_multiple_matches(data, pattern)
        for scpthumbid, scptitle, scpurl in matches:
            itemlist.append(
                Item(
                    action = "episodios",
                    channel = item.channel,
                    contentSerieName = scptitle.strip(),
                    fanart = host + '/uploads/fondos/' + scpthumbid + '.jpg',
                    infoLabels = infoLabels,
                    title = scptitle.strip(),
                    thumbnail = host + '/uploads/portadas/' + scpthumbid + '.jpg',
                    url = host + scpurl
                )
            )
    # Si se encuentra otra página, se agrega un paginador
    nextpage = list_all_next(data)
    if nextpage:
        itemlist.append(
            Item(
                action = 'list_all',
                channel =  item.channel,
                fanart = item.fanart,
                param = item.param,
                title =  '[COLOR orange]Siguiente página > [/COLOR]',
                url = host + nextpage
            )
        )
    tmdb.set_infoLabels(itemlist, seekTmdb = False)
    return itemlist

def list_all_next(data):
    logger.info()
    nexturlptn = '(?s)a href="([^"]+?)" class="btn rnd npd fa-arrow-right"'
    nexturl = scrapertools.find_single_match(data, nexturlptn)
    if nexturl:
        return nexturl
    else:
        return False

def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    month = {'January':'01', 'February':'02', 'March':'03',
            'April':'04', 'May':'05', 'June':'06', 'July':'07',
            'August':'08', 'September':'09', 'October':'10',
            'November':'11', 'December':'12'}
    
    epsectptn = '(?s)class="episodes-list".*?/section>'
    epsectmatch = scrapertools.find_single_match(data, epsectptn)
    gensectptn = '(?s)class="genres".*?/section>'
    gensectmatch = scrapertools.find_single_match(data, gensectptn)
    eppatn = '(?s)img src="([^"]+).*?h-title.+?>(.*?)\s(?:Episodio)\s(\d*?)<.*?time>([^<]+).*?a href="([^"]+)'
    epmatch = scrapertools.find_multiple_matches(epsectmatch, eppatn)
    genpatn = '(?s)a href="(?:[^"]+)+.+?>([^<]+)'
    genmatch = scrapertools.find_multiple_matches(gensectmatch, genpatn)
    plotptn = '(?s)class="content-title".+?p>([^<]+)'
    plot = scrapertools.find_single_match(data, plotptn)
    premiereptn = '(?s)class="content-title".+?>(\d+?-\d+?-\d+?)<'
    premiere = scrapertools.find_single_match(data, premiereptn)
    ratingptn = '(?s)class="h-rating".*?class="fa-star total".*?>([^<]+)\s.+?>.+?>([^<]+)'
    rating = (scrapertools.find_multiple_matches(data, ratingptn))[0]

    infoLabels = item.infoLabels
    scpstatusptn = '(?s)class="status-.*?>.*?>.*?>([^<]+)'
    scpstatus = scrapertools.find_single_match(data, scpstatusptn)
    infoLabels['genre'] += scpstatus.strip()
    infoLabels['plot'] = plot
    infoLabels['rating'] = float(rating[0])
    infoLabels['status'] = scpstatus.strip()
    infoLabels['tvshowtitle'] = item.title
    infoLabels['votes'] = int(rating[1])
    if genmatch:
        infoLabels['genre'] = genmatch[0]
        for i in range(len(genmatch) - 1):
            infoLabels['genre'] += ', ' + genmatch[i + 1]
    for scpthumbnail, scptitle, scpepnum, scptime, scpurl in epmatch:
        # date = datetime.datetime.strptime(scptime, '%B %d, %Y')
        # infoLabels['last_air_date'] = date.strftime('%Y-%m-%d')
        date = (scrapertools.find_multiple_matches(scptime, '(.+?).(\d\d).+?(\d+)'))[0]
        infoLabels['last_air_date'] = date[2] + '-' + month[date[0]] + '-' + date[1]
        infoLabels['aired'] = infoLabels['last_air_date']
        infoLabels['premiered'] = infoLabels['last_air_date']
        infoLabels['episode'] = scpepnum
        itemlist.append(
            Item(
                action = "findvideos",
                channel = item.channel,
                contentTitle = item.title,
                fanart = item.fanart,
                infoLabels = infoLabels,
                title = 'Episodio ' + scpepnum,
                thumbnail = host + scpthumbnail,
                url = host + scpurl
            )
        )
    itemlist.reverse()
    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.extra:
        if premiere:
            itemlist.append(
                Item(
                    channel = item.channel,
                    fanart = item.fanart,
                    title = 'Estreno próximo episodio: ' + premiere,
                    thumbnail = item.thumbnail,
                )
            )
        itemlist.append(
            Item(
                channel = item.channel,
                title = '[COLOR yellow]Añadir este item a la videoteca[/COLOR]',
                url = item.url,
                action = "add_serie_to_library",
                extra = "episodesxseason",
                contentSerieName = item.contentSerieName
            )
        )
    else:
        if premiere:
            itemlist.append(
                Item(
                    channel = item.channel,
                    fanart = item.fanart,
                    title = 'Estreno próximo episodio: ' + premiere,
                    thumbnail = item.thumbnail,
                )
            )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = False)
    itemlist.append(
        Item(
            action = "comments",
            channel = item.channel,
            fanart = item.fanart,
            title = "Ver comentarios",
            url = item.url
        )
    )
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    itemlist.extend(episodios(item))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data =  jsontools.load(
                scrapertools.find_single_match
                    (httptools.downloadpage(item.url).data,
                    '(?s)var (?:videos|video) = (.+?);'
                )
            )
    urls = ''
    for i in data:
        urls += '<a href="' + i[1] + '"></a>'
    itemlist.extend(servertools.find_video_items(item = item, data = urls))
    itemlist = servertools.get_servers_itemlist(itemlist, None, True)
    for video in itemlist:
        video.channel = item.channel
        video.contentTitle = item.title
        video.fanart = item.thumbnail
        video.infoLabels = item.infoLabels
        video.title = video.title.replace((config.get_localized_string(70206) % ''), '')
        video.title = '[' + video.title + '] Ver ' + item.contentTitle
        video.thumbnail = item.thumbnail
    itemlist.append(
        Item(
            action = "comments",
            channel = item.channel,
            fanart = item.fanart,
            title = "Ver comentarios",
            url = item.url
        )
    )
    return itemlist

def comments(item):
    #############################
    ## TODO: Add image support ##
    #############################
    logger.info()
    itemlist = []
    apipage = httptools.downloadpage('https://hentaila-1.disqus.com/embed.js').data
    apikey = scrapertools.find_single_match(apipage, 'getLoaderVersionFromUrl\(".+?lounge.load\.([^\.]+)')

    base_url = 'https://disqus.com/embed/comments/?base=default&f=hentaila-1&t_u='
    source_url = urllib.quote(item.url, safe = '')
    param_url = '&s_o=default#version='
    url = base_url + source_url + param_url + apikey
    raw_data = httptools.downloadpage(url).data
    raw_jsonptn = 'id="disqus-threadData">([^<]+)</script>'
    raw_comments = (jsontools.load(scrapertools.find_single_match(raw_data, raw_jsonptn)))['response']['posts']

    for comment in raw_comments:
        author = comment['author']['name']
        image = ''
        url = ''
        # Buscamos si hay enlaces a imágenes de disqus para mostrarlas
        if scrapertools.find_single_match(comment['raw_message'], '(?s)(?:http|https)://.+?\.disquscdn\.com/images/') != '':
            image = 'https://uploads.disquscdn.com' + scrapertools.find_single_match(comment['raw_message'], '(?s)disquscdn\.com(/.+?)(?:$|\s|\\n)')
        # Buscamos si hay enlaces a HLA para mostrar redirecciones
        if scrapertools.find_single_match(comment['raw_message'], '(?s)hentaila\.com(/.+?)(?:$|\s|\\n)') != '':
            url = 'https://hentaila.com' + scrapertools.find_single_match(comment['raw_message'], '(?s)hentaila\.com(/.+?)(?:$|\s|\\n)')
        listitem = Item(
            action = 'show_actions',
            author = author,
            channel = item.channel,
            comment = comment['raw_message'],
            contentPlot = comment['raw_message'],
            id = str(comment['id']),
            nesting = 0,
            parent = str(comment['parent']),
            thumbnail = image,
            title = author,
            url = url
        )
        parentindicator = ''
        if len(itemlist) > 0:
            # Verificamos si el comentario es respuesta a otro comentario
            if itemlist[-1].parent != 'null':
                # Verificamos si el comentario anterior es el padre
                # Si no es el padre, verificamos si es del mismo padre que el anterior
                # Agregamos nesting para mantener respuestas por nivel
                if listitem.parent == itemlist[-1].id:
                    listitem.nesting = itemlist[-1].nesting + 1
                elif itemlist[-1].nesting > 0:
                    # Si no, buscamos si hay padres arriba
                    for i in range(len(itemlist) -1, -1, -1):
                        if itemlist[i].nesting > 0:
                            if listitem.parent == itemlist[i].parent:
                                listitem.nesting = itemlist[i].nesting
                        else:
                            break
                nestlevelmark = ''
                for i in range(listitem.nesting):
                    nestlevelmark += ' ^ '
                listitem.title = nestlevelmark + listitem.title
        itemlist.append(listitem)
    return itemlist

def show_actions(item):
    logger.info()
    actions = ['Ver comentario', 'Ir a enlace de HLA']
    selection = -1
    if item.url != '':
        selection = xbmcgui.Dialog().contextmenu(actions)
    if selection == 0 or item.url == '':
        platformtools.dialog_textviewer(item.author, item.comment)
        return True
    elif selection == 1:
        if scrapertools.find_single_match(item.url, '/ver/') != '':
            return findvideos(item)
        else:
            return episodios(item)

def search(item, text):
    logger.info()
    itemlist = []
    if text != '':
        try:
            results = httptools.downloadpage(item.url, post = str('value=' + text)).json
            for result in results:
                itemlist.append(
                    Item(
                        action = "episodios",
                        channel = item.channel,
                        contentSerieName = result['title'],
                        fanart = host + '/uploads/fondos/' + result['id'] + '.jpg',
                        title = result['title'],
                        thumbnail = host + '/uploads/portadas/' + result['id'] + '.jpg',
                        url = host + '/hentai-' + result['slug']
                    )
                )
            return itemlist
        except:
            for line in sys.exc_info():
                logger.error("%s" % line)
            return itemlist