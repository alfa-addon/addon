# support functions that are needed by many channels, to no repeat the same code
import base64, urlparse, re, os, inspect
from core import httptools, scrapertoolsV2, servertools, tmdb
from core.item import Item
import urllib

from lib import unshortenit
from platformcode import logger, config


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


def scrape(item, itemlist, patron, listGroups, headers="", blacklist="", data="", patron_block="", patronNext="", action="findvideos", url_host=""):
    # patron: the patron to use for scraping page, all capturing group must match with listGroups
    # listGroups: a list containing the scraping info obtained by your patron, in order
    # accepted values are: url, title, thumb, quality, year, plot, duration, genre

    # header: values to pass to request header
    # blacklist: titles that you want to exclude(service articles for example)
    # patronNext: patron for scraping next page link
    # action: if you want results perform an action different from "findvideos", useful when scraping film by genres
    # url_host: string to prepend to scrapedurl, useful when url don't contain host
    # example usage:
    #   import support
    #   itemlist = []
    #   patron = 'blablabla'
    #   headers = [['Referer', host]]
    #   blacklist = 'Request a TV serie!'
    #   support.scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'], headers=headers, blacklist=blacklist)
    #   return itemlist
    # return data for debugging purposes

    if not data:
        data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
        # replace all ' with ", so we don't need to worry about

    if patron_block:
        block = scrapertoolsV2.get_match(data, patron_block)
    else:
        block = data

    matches = scrapertoolsV2.find_multiple_matches(block, patron)

    for match in matches:
        scrapedurl = url_host+match[listGroups.index('url')] if 'url' in listGroups else ''
        scrapedtitle = match[listGroups.index('title')] if 'title' in listGroups else ''
        scrapedthumb = match[listGroups.index('thumb')] if 'thumb' in listGroups else ''
        scrapedquality = match[listGroups.index('quality')] if 'quality' in listGroups else ''
        scrapedyear = match[listGroups.index('year')] if 'year' in listGroups else ''
        scrapedplot = match[listGroups.index('plot')] if 'plot' in listGroups else ''
        scrapedduration = match[listGroups.index('duration')] if 'duration' in listGroups else ''
        scrapedgenre = match[listGroups.index('genre')] if 'genre' in listGroups else ''

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

    return block


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


def dooplay_films(item, itemlist, blacklist=""):
    patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="([^"]+)".*?<span class="quality">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a></h3> (?:<span>([0-9]{4})</span>)?.*?(?:<span>([0-9]+) min</span>)?.*?(?:<div class="texto">([^<>]+).*?)?(?:genres">(.*?)</div>)?'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'duration', 'plot', 'genre'], blacklist=blacklist, patronNext=patronNext)
    
    
def dooplay_search(item, itemlist, blacklist=""):
    patron = '<div class="result-item">.*?<img src="([^"]+)".*?<span class="movies">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a>.*?<span class="year">([0-9]{4}).*?<div class="contenido"><p>([^<>]+)'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'], blacklist=blacklist, patronNext=patronNext)


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

    itemlist.append(Item(
        channel = filename,
        title = title,
        action = action,
        url = url,
        contentType = contentType
    ))
    from channelselector import thumb
    itemlist = thumb(itemlist)
    return itemlist