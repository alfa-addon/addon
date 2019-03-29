# support functions that are needed by many channels, to no repeat the same code
import base64, urlparse, re, os, inspect
from core import httptools, scrapertoolsV2, servertools, tmdb
from core.item import Item
import urllib

from lib import unshortenit
from platformcode import logger, config
from channelselector import thumb


def hdpass_get_servers(item):
    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n', '')
    patron = r'<iframe(?: id="[^"]+")? width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
    url = scrapertoolsV2.find_single_match(data, patron).replace("?alta", "")
    url = url.replace("&download=1", "")
    if 'https' not in url:
        url = 'https:' + url

    if 'hdpass' in url:
        data = httptools.downloadpage(url).data

        start = data.find('<div class="row mobileRes">')
        end = data.find('<div id="playerFront">', start)
        data = data[start:end]

        patron_res = '<div class="row mobileRes">(.*?)</div>'
        patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
        patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="([^"]+)" id="urlEmbed" value="([^"]+)"\s*/>'

        res = scrapertoolsV2.find_single_match(data, patron_res)

        itemlist = []

        for res_url, res_video in scrapertoolsV2.find_multiple_matches(res, '<option.*?value="([^"]+?)">([^<]+?)</option>'):

            data = httptools.downloadpage(urlparse.urljoin(url, res_url)).data.replace('\n', '')

            mir = scrapertoolsV2.find_single_match(data, patron_mir)

            for mir_url, server in scrapertoolsV2.find_multiple_matches(mir, '<option.*?value="([^"]+?)">([^<]+?)</value>'):

                data = httptools.downloadpage(urlparse.urljoin(url, mir_url)).data.replace('\n', '')
                for media_label, media_url in scrapertoolsV2.find_multiple_matches(data, patron_media):
                    itemlist.append(Item(channel=item.channel,
                                         action="play",
                                         title=item.title+"["+color(server, 'orange')+"]"+" - "+color(res_video, 'green'),
                                         fulltitle=item.fulltitle,
                                         quality=res_video,
                                         show=item.show,
                                         thumbnail=item.thumbnail,
                                         contentType=item.contentType,
                                         server=server,
                                         url=url_decode(media_url)))
                    logger.info("video ->" + res_video)

    return itemlist


def url_decode(url_enc):
    lenght = len(url_enc)
    if lenght % 2 == 0:
        len2 = lenght / 2
        first = url_enc[0:len2]
        last = url_enc[len2:lenght]
        url_enc = last + first
        reverse = url_enc[::-1]
        return base64.b64decode(reverse)

    last_car = url_enc[lenght - 1]
    url_enc[lenght - 1] = ' '
    url_enc = url_enc.strip()
    len1 = len(url_enc)
    len2 = len1 / 2
    first = url_enc[0:len2]
    last = url_enc[len2:len1]
    url_enc = last + first
    reverse = url_enc[::-1]
    reverse = reverse + last_car
    return base64.b64decode(reverse)


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"


def scrape(item, patron = '', listGroups = [], headers="", blacklist="", data="", patron_block="",
           patronNext="", action="findvideos", url_host=""):
    # patron: the patron to use for scraping page, all capturing group must match with listGroups
    # listGroups: a list containing the scraping info obtained by your patron, in order
    # accepted values are: url, title, thumb, quality, year, plot, duration, genre, rating

    # header: values to pass to request header
    # blacklist: titles that you want to exclude(service articles for example)
    # data: if you want to pass data manually, maybe because you need some custom replacement
    # patron_block: patron to get parts of the page (to scrape with patron attribute),
    #               if you need a "block inside another block" you can create a list, please note that all matches
    #               will be packed as string
    # patronNext: patron for scraping next page link
    # action: if you want results perform an action different from "findvideos", useful when scraping film by genres
    # url_host: string to prepend to scrapedurl, useful when url don't contain host
    # example usage:
    #   import support
    #   itemlist = []
    #   patron = 'blablabla'
    #   headers = [['Referer', host]]
    #   blacklist = 'Request a TV serie!'
    #   return support.scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'],
    #                           headers=headers, blacklist=blacklist)

    itemlist = []

    if not data:
        data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
        data = re.sub('\n|\t', '', data)
        # replace all ' with " and eliminate newline, so we don't need to worry about
        logger.info('DATA ='+data)

        if patron_block:
            if type(patron_block) == str:
                patron_block = [patron_block]

            for n, regex in enumerate(patron_block):
                blocks = scrapertoolsV2.find_multiple_matches(data, regex)
                data = str(blocks)
                logger.info('BLOCK '+str(n)+'=' + data)
    if patron and listGroups:
        matches = scrapertoolsV2.find_multiple_matches(data, patron)
        logger.info('MATCHES ='+str(matches))

        for match in matches:
            if len(listGroups) > len(match):  # to fix a bug
                match = list(match)
                match.extend([''] * (len(listGroups)-len(match)))

            scrapedurl = url_host+match[listGroups.index('url')] if 'url' in listGroups else ''
            scrapedtitle = match[listGroups.index('title')] if 'title' in listGroups else ''
            scrapedthumb = match[listGroups.index('thumb')] if 'thumb' in listGroups else ''
            scrapedquality = match[listGroups.index('quality')] if 'quality' in listGroups else ''
            scrapedyear = match[listGroups.index('year')] if 'year' in listGroups else ''
            scrapedplot = match[listGroups.index('plot')] if 'plot' in listGroups else ''
            scrapedduration = match[listGroups.index('duration')] if 'duration' in listGroups else ''
            scrapedgenre = match[listGroups.index('genre')] if 'genre' in listGroups else ''
            scrapedrating = match[listGroups.index('rating')] if 'rating' in listGroups else ''

            title = scrapertoolsV2.decodeHtmlentities(scrapedtitle)
            plot = scrapertoolsV2.decodeHtmlentities(scrapedplot)
            if scrapedquality:
                longtitle = '[B]' + title + '[/B] [COLOR blue][' + scrapedquality + '][/COLOR]'
            else:
                longtitle = '[B]' + title + '[/B]'

            infolabels = {}
            if scrapedyear:
                infolabels['year'] = scrapedyear
            if scrapedplot:
                infolabels['plot'] = plot
            if scrapedduration:
                infolabels['duration'] = scrapedduration
            if scrapedgenre:
                infolabels['genre'] = scrapertoolsV2.find_multiple_matches(scrapedgenre, '(?:<[^<]+?>)?([^<>]+)') # delete all html tags and match text
            if scrapedrating:
                infolabels['rating'] = scrapertoolsV2.decodeHtmlentities(scrapedrating)
            if not scrapedtitle in blacklist:
                itemlist.append(
                    Item(channel=item.channel,
                         action=action,
                         contentType=item.contentType,
                         title=longtitle,
                         fulltitle=title,
                         show=title,
                         quality=scrapedquality,
                         url=scrapedurl,
                         infoLabels=infolabels,
                         thumbnail=scrapedthumb
                         )
                )

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if patronNext:
            next_page = scrapertoolsV2.find_single_match(data, patronNext)
            logger.info('NEXT ' + next_page)

            if next_page != "":
                itemlist.append(
                    Item(channel=item.channel,
                         action="peliculas",
                         contentType=item.contentType,
                         title="[COLOR blue]" + config.get_localized_string(30992) + " >[/COLOR]",
                         url=next_page))

    return itemlist


def dooplay_get_links(item, host):
    # get links from websites using dooplay theme and dooplay_player
    # return a list of dict containing these values: url, title and server

    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    ret = []

    for type, post, nume, title, server in matches:
        postData = urllib.urlencode({
            "action": "doo_player_ajax",
            "post": post,
            "nume": nume,
            "type": type
        })
        dataAdmin = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=postData,headers={'Referer': item.url}).data
        link = scrapertoolsV2.get_match(dataAdmin, "<iframe.*src='([^']+)'")
        ret.append({
            'url': link,
            'title': title,
            'server': server
        })

    return ret


def dooplay_films(item, blacklist=""):
    patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="([^"]+)".*?<span class="quality">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a></h3> (?:<span>([0-9]{4})</span>)?.*?(?:<span>([0-9]+) min</span>)?.*?(?:<div class="texto">([^<>]+).*?)?(?:genres">(.*?)</div>)?'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    return scrape(item, patron, ['thumb', 'quality', 'url', 'title', 'year', 'duration', 'plot', 'genre'], blacklist=blacklist, patronNext=patronNext)
    
    
def dooplay_search(item, blacklist=""):
    patron = '<div class="result-item">.*?<img src="([^"]+)".*?<span class="movies">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a>.*?<span class="year">([0-9]{4}).*?<div class="contenido"><p>([^<>]+)'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    return scrape(item, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'], blacklist=blacklist, patronNext=patronNext)


def swzz_get_url(item):
    if "/link/" in item.url:
        data = httptools.downloadpage(item.url).data
        if "link =" in data:
            data = scrapertoolsV2.get_match(data, 'link = "([^"]+)"')
        else:
            match = scrapertoolsV2.get_match(data, r'<meta name="og:url" content="([^"]+)"')
            match = scrapertoolsV2.get_match(data, r'URL=([^"]+)">') if not match else match

            if not match:
                from lib import jsunpack

                try:
                    data = scrapertoolsV2.get_match(data, r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>")
                    data = jsunpack.unpack(data)

                    logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
                except IndexError:
                    logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

                data = scrapertoolsV2.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
                data, c = unshortenit.unwrap_30x_only(data)
            else:
                data = match
        if data.startswith('/'):
            data = urlparse.urljoin("http://swzz.xyz", data)
            data = httptools.downloadpage(data).data
        logger.debug("##### play /link/ data ##\n%s\n##" % data)
    else:
        data = item.url

    return data

def menu(itemlist, title='', action='', url='', contentType='movie'):    
    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename).replace('.py','')
    logger.info('FILENAME= ' + filename)

    title = typo(title)

    if contentType == 'movie': extra = 'movie'
    else: extra = 'tvshow'
    logger.info('EXTRA= ' + title + ' '+extra)

    itemlist.append(Item(
        channel = filename,
        title = title,
        action = action,
        url = url,
        extra = extra,
        contentType = contentType
    ))
    from channelselector import thumb
    thumb(itemlist)
    return itemlist

def typo(string):
    if '[]' in string:
        string = '[' + re.sub(r'\s\[\]','',string) + ']'
    if '()' in string:
        string = '(' + re.sub(r'\s\(\)','',string) + ')'
    if '{}' in string:
        string = '{' + re.sub(r'\s\{\}','',string) + '}'
    if 'submenu' in string:
        string = ' > ' + re.sub('\ssubmenu','',string)
    if 'color' in string:
        color = scrapertoolsV2.find_single_match(string,'color ([a-z]+)')
        string = '[COLOR '+ color +']' + re.sub('\scolor\s([a-z]+)','',string) + '[/COLOR]'
    if 'bold' in string:
        string = '[B]' + re.sub('\sbold','',string) + '[/B]'
    if 'italic' in string:
        string = '[I]' + re.sub('\sitalic','',string) + '[/I]' 
    if '_' in string:
        string = ' ' + re.sub('\s_','',string)

    return string

def match(item, patron='', patron_block='', headers=''):
    data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
    data = re.sub('\n|\t', '', data)
    log('DATA= ',data)
    if patron_block:
        block = scrapertoolsV2.find_single_match(data, patron_block)
        log('BLOCK= ',block)
    else:
        data = block
    matches = scrapertoolsV2.find_multiple_matches(block, patron)
    log('MATCHES=',matches)
    return matches

def videolibrary(itemlist, item, typography=''):
    if item.contentType != 'episode':
        action = 'add_pelicula_to_library'
        extra = 'findvideos'
    else:
        action = 'add_serie_to_library'
        extra = 'episodios'

    title = typo(config.get_localized_string(30161) + ' ' + typography)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 title=title,
                 url=item.url,
                 action=action,
                 contentTitle=item.fulltitle))

def nextPage(itemlist, item, data, patron):
    next_page = scrapertoolsV2.find_single_match(data, patron)
    logger.info('NEXT ' + next_page)

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992) + ' > color blue'),
                 url=next_page,
                 thumbnails=thumb()))

    return itemlist

def server(item, data='', headers=''):
    
    if not data:
        data = httptools.downloadpage(item.url, headers=headers).data

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, ' ', typo(videoitem.title + ' color blue []')])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    return itemlist

def log(stringa1="", stringa2="", stringa3="", stringa4="", stringa5=""):
    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename)    
    logger.info("[" + filename + "] - [" + inspect.stack()[1][3] + "] " + str(stringa1) + str(stringa2) + str(stringa3) + str(stringa4) + str(stringa5))