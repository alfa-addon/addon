# -*- coding: utf-8 -*-
#https://github.com/tonikelope/neiflix

import re
import urlparse
import urllib
import urllib2
import json
import math
import os.path
import os
import hashlib
import xbmc
import base64
import pickle
import socket

from core import scrapertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from megaserver import proxy, Mega

MC_REVERSE_PORT = int(config.get_setting("neiflix_mc_reverse_port", "neiflix"))

MC_REVERSE_DATA = str(MC_REVERSE_PORT) + ":" + base64.b64encode(
    "neiflix:" + hashlib.sha1(config.get_setting("neiflix_user", "neiflix")).hexdigest())

USE_MEGA_PREMIUM = config.get_setting("neiflix_mega_premium", "neiflix")

MEGA_EMAIL = config.get_setting("neiflix_mega_email", "neiflix")

MEGA_PASSWORD = config.get_setting("neiflix_mega_password", "neiflix")

UPLOADERS_BLACKLIST = [
    x.strip() for x in config.get_setting(
        "neiflix_blacklist_uploaders",
        "neiflix").split(',')]


def login():
    logger.info("channels.neiflix login")

    scrapertools.cache_page("https://noestasinvitado.com/login/")

    neiflix_login = config.get_setting("neiflix_user", "neiflix")

    neiflix_password = config.get_setting("neiflix_password", "neiflix")

    post = "user=" + neiflix_login + "&passwrd=" + \
           neiflix_password + "&cookielength=-1"

    data = scrapertools.cache_page(
        "https://noestasinvitado.com/login2/", post=post)

    return data.find(neiflix_login) != -1


def mega_login(verbose):
    mega_sid = ''

    if USE_MEGA_PREMIUM and MEGA_EMAIL and MEGA_PASSWORD:

        filename_hash = xbmc.translatePath(
            "special://home/temp/kodi_nei_mega_" + hashlib.sha1(MEGA_EMAIL + MEGA_PASSWORD).hexdigest())

        login_ok = False

        if os.path.isfile(filename_hash):

            try:

                mega = pickle.load(open(filename_hash, "rb"))

                mega.get_user()

                login_ok = True

            except RequestError:
                pass

        if not login_ok:

            mega = Mega()

            try:
                mega.login(MEGA_EMAIL, MEGA_PASSWORD)

                pickle.dump(mega, open(filename_hash, "wb"))

                login_ok = True

            except RequestError:
                pass

        if login_ok:

            mega_sid = mega.sid

            logger.info("channels.neiflix LOGIN EN MEGA OK!")

            if verbose:
                platformtools.dialog_notification(
                    "NEIFLIX", "LOGIN EN MEGA OK!")

        else:
            logger.info("channels.neiflix ERROR AL HACER LOGIN en MEGA!")

            if verbose:
                platformtools.dialog_notification(
                    "NEIFLIX", "ERROR AL HACER LOGIN EN MEGA!")

    return mega_sid


def mainlist(item):
    logger.info("channels.neiflix mainlist")

    itemlist = []

    if config.get_setting("neiflixuser", "neiflix") == "":
        itemlist.append(
            Item(channel=item.channel, title="Habilita tu cuenta en la configuración...", action="settingCanal",
                 url=""))
    else:
        if login():
            check_megaserver_lib()
            mega_login(False)
            load_mega_proxy()
            itemlist.append(Item(channel=item.channel, title="Novedades Películas", action="foro",
                                 url="https://noestasinvitado.com/peliculas/", folder=True, fa=True, fa_genre=""))
            itemlist.append(Item(channel=item.channel, title="Novedades Series", action="foro",
                                 url="https://noestasinvitado.com/series/", folder=True, fa=True, fa_genre="TV_SE"))
            itemlist.append(Item(channel=item.channel, title="Novedades documetales", action="foro",
                                 url="https://noestasinvitado.com/documentales/", folder=True))
            itemlist.append(Item(channel=item.channel, title="Novedades vídeos deportivos", action="foro",
                                 url="https://noestasinvitado.com/deportes/", folder=True))
            itemlist.append(Item(channel=item.channel, title="Novedades ANIME", action="foro",
                                 url="https://noestasinvitado.com/anime/", folder=True))
            itemlist.append(Item(channel=item.channel, title="Novedades XXX", action="foro",
                                 url="https://noestasinvitado.com/18-15/", folder=True))
            itemlist.append(Item(channel=item.channel, title="Listados alfabéticos", action="indices",
                                 url="https://noestasinvitado.com/indices/", folder=True))
            itemlist.append(
                Item(
                    channel=item.channel,
                    title="[COLOR yellow][B]Buscar...[/B][/COLOR]",
                    action="search"))
        else:
            itemlist.append(
                Item(channel=item.channel, title="Usuario y/o password de NEI incorrecta, revisa la configuración...",
                     action="", url="", folder=False))
    return itemlist


def setting_canal(item):
    return platformtools.show_channel_settings()


def foro(item):
    logger.info("channels.neiflix foro")

    itemlist = []

    data = scrapertools.cache_page(item.url)

    mc_links = False

    final_item = False

    if '<h3 class="catbg">Subforos</h3>' in data:
        # HAY SUBFOROS
        patron = '<a class="subje(.*?)t" href="([^"]+)" name="[^"]+">([^<]+)</a(>)'
        action = "foro"
    elif '"subject windowbg4"' in data:
        patron = '<td class="subject windowbg4">.*?<div *?>.*?<span id="([^"]+)"> *?<a href="([^"]+)".*?>([^<]+)</a> ' \
                 '*?</span>.*?"Ver +perfil +de +([^"]+)"'
        final_item = True
        action = "foro"
    else:
        mc_links = True
        itemlist = find_mc_links(item, data)

    if not mc_links:

        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedmsg, scrapedurl, scrapedtitle, uploader in matches:

            if uploader not in UPLOADERS_BLACKLIST:

                url = urlparse.urljoin(item.url, scrapedurl)

                scrapedtitle = scrapertools.htmlclean(scrapedtitle)

                if uploader != '>':
                    title = scrapedtitle + " (" + uploader + ")"
                else:
                    title = scrapedtitle

                thumbnail = ""

                if final_item:

                    parsed_title = parse_title(scrapedtitle)

                    content_title = parsed_title['title']

                    year = parsed_title['year']

                    if item.fa:

                        rating = get_filmaffinity_data(
                            content_title, year, item.fa_genre)

                        if item.parent_title.startswith('Ultra HD '):
                            quality = 'UHD'
                        elif item.parent_title.startswith('HD '):
                            quality = 'HD'
                        else:
                            quality = 'SD'

                        if rating[0]:
                            if float(rating[0]) >= 7.0:
                                rating_text = "[COLOR green][FA " + \
                                              rating[0] + "][/COLOR]"
                            elif float(rating[0]) < 4.0:
                                rating_text = "[COLOR red][FA " + \
                                              rating[0] + "][/COLOR]"
                            else:
                                rating_text = "[FA " + rating[0] + "]"
                        else:
                            rating_text = "[FA ---]"

                        title = "[COLOR darkorange][B]" + content_title + "[/B][/COLOR] " + (
                            "(" + year + ")" if year else "") + " [" + quality + "] [B]" + \
                            rating_text + "[/B] (" + uploader + ")"

                        if rating[1]:
                            thumbnail = rating[1].replace('msmall', 'large')
                        else:
                            thumbnail = ""

                    item.infoLabels = {'year': year}

                else:
                    item.parent_title = title.strip()
                    content_title = ""

                itemlist.append(item.clone(
                    action=action,
                    title=title,
                    url=url,
                    thumbnail=thumbnail +
                    "|User-Agent=Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/65.0.3163.100 Safari/537.36",
                    folder=True, contentTitle=content_title))

        patron = '<div class="pagelinks">Páginas:.*?\[<strong>[^<]+</strong>\].*?<a class="navPages" href' \
                 '="(?!\#bot)([^"]+)">[^<]+</a>.*?</div>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for match in matches:
            if len(matches) > 0:
                url = match
                title = "[B]>> Página Siguiente[/B]"
                thumbnail = ""
                plot = ""
                itemlist.append(
                    item.clone(
                        action="foro",
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        folder=True))

    return itemlist


def search(item, texto):
    itemlist = []

    if texto != "":
        texto = texto.replace(" ", "+")

    post = "advanced=1&search=" + texto + "&searchtype=1&userspec=*&sort=relevance%7Cdesc&subject_only=1&" \
                                          "minage=0&maxage=9999&brd%5B6%5D=6&brd%5B227%5D=227&brd%5B229%5D" \
                                          "=229&brd%5B230%5D=230&brd%5B41%5D=41&brd%5B47%5D=47&brd%5B48%5D" \
                                          "=48&brd%5B42%5D=42&brd%5B44%5D=44&brd%5B46%5D=46&brd%5B218%5D=2" \
                                          "18&brd%5B225%5D=225&brd%5B7%5D=7&brd%5B52%5D=52&brd%5B59%5D=59&b" \
                                          "rd%5B61%5D=61&brd%5B62%5D=62&brd%5B51%5D=51&brd%5B53%5D=53&brd%5" \
                                          "B54%5D=54&brd%5B55%5D=55&brd%5B63%5D=63&brd%5B64%5D=64&brd%5B66%" \
                                          "5D=66&brd%5B67%5D=67&brd%5B65%5D=65&brd%5B68%5D=68&brd%5B69%5D=69" \
                                          "&brd%5B14%5D=14&brd%5B87%5D=87&brd%5B86%5D=86&brd%5B93%5D=93&brd" \
                                          "%5B83%5D=83&brd%5B89%5D=89&brd%5B85%5D=85&brd%5B82%5D=82&brd%5B9" \
                                          "1%5D=91&brd%5B90%5D=90&brd%5B92%5D=92&brd%5B88%5D=88&brd%5B84%5D" \
                                          "=84&brd%5B212%5D=212&brd%5B94%5D=94&brd%5B23%5D=23&submit=Buscar"

    data = scrapertools.cache_page(
        "https://noestasinvitado.com/search2/", post=post)

    patron = '<h5>[^<>]*<a[^<>]+>.*?</a>[^<>]*?<a +href="([^"]+)">(.*?)</a>[^<>]*</h5>[^<>]*<span[^<>]*>.*?' \
             '<a[^<>]*"Ver +perfil +de +([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, uploader in matches:
        url = urlparse.urljoin(item.url, scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle)

        title = scrapedtitle + " [" + uploader + "]"

        thumbnail = ""

        parsed_title = parse_title(scrapedtitle)

        year = parsed_title['year']

        content_title = parsed_title['title']

        item.infoLabels = {'year': year}

        itemlist.append(item.clone(action="foro", title=title, url=url, thumbnail=thumbnail, contentTitle=content_title,
                                   folder=True))

    patron = '\[<strong>[0-9]+</strong>\][^<>]*<a class="navPages" href="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).search(data)

    if matches:
        url = matches.group(1)
        title = "[B]>> Página Siguiente[/B]"
        thumbnail = ""
        plot = ""
        itemlist.append(
            item.clone(
                action="search_pag",
                title=title,
                url=url,
                thumbnail=thumbnail,
                folder=True))

    return itemlist


def search_pag(item):
    itemlist = []

    data = scrapertools.cache_page(item.url)

    patron = '<h5>[^<>]*<a[^<>]+>.*?</a>[^<>]*?<a +href="([^"]+)">(.*?)</a>[^<>]*</h5>[^<>]*<sp' \
             'an[^<>]*>.*?<a[^<>]*"Ver +perfil +de +([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, uploader in matches:
        url = urlparse.urljoin(item.url, scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle)

        title = scrapedtitle + " [" + uploader + "]"

        thumbnail = ""

        parsed_title = parse_title(scrapedtitle)

        year = parsed_title['year']

        content_title = parsed_title['title']

        item.infoLabels = {'year': year}

        itemlist.append(item.clone(action="foro", title=title, url=url, thumbnail=thumbnail, contentTitle=content_title,
                                   folder=True))

    patron = '\[<strong>[0-9]+</strong>\][^<>]*<a class="navPages" href="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).search(data)

    if matches:
        url = matches.group(1)
        title = "[B]>> Página Siguiente[/B]"
        thumbnail = ""
        plot = ""
        itemlist.append(
            item.clone(
                action="search_pag",
                title=title,
                url=url,
                thumbnail=thumbnail,
                folder=True))

    return itemlist


def indices(item):
    itemlist = []

    categories = ['Películas HD Español', 'Películas HD VO', 'Películas SD Español', 'Películas SD VO',
                  'Series HD Español', 'Series HD VO', 'Series SD Español', 'Series SD VO', 'Películas Anime Español',
                  'Películas Anime VO', 'Series Anime Español', 'Series Anime VO', 'Películas clásicas', 'Deportes',
                  'Películas XXX HD', 'Películas XXX SD', 'Vídeos XXX HD', 'Vídeos XXX SD']

    for cat in categories:
        itemlist.append(
            Item(channel=item.channel, title=cat, action="gen_index", url="https://noestasinvitado.com/indices/",
                 folder=True))

    return itemlist


def gen_index(item):
    categories = {'Películas HD Español': 47, 'Películas HD VO': 48, 'Películas SD Español': 44, 'Películas SD VO': 42,
                  'Series HD Español': 59, 'Series HD VO': 61, 'Series SD Español': 53, 'Series SD VO': 54,
                  'Películas Anime Español': 66, 'Películas Anime VO': 67, 'Series Anime Español': 68,
                  'Series Anime VO': 69, 'Películas clásicas': 218, 'Deportes': 23, 'Películas XXX HD': 182,
                  'Películas XXX SD': 183, 'Vídeos XXX HD': 185, 'Vídeos XXX SD': 186}

    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'Ñ', 'O', 'P', 'Q', 'R', 'S', 'T',
               'U', 'V', 'W', 'X', 'Y', 'Z', '0-9']

    itemlist = []

    start = 1

    for letter in letters:
        itemlist.append(Item(channel=item.channel, title="%s (Letra %s)" % (item.title, letter), action="indice_links",
                             url="https://noestasinvitado.com/indices/?id=%d;start=%d" % (
                                 categories[item.title], start), folder=True))
        start = start + 1

    return itemlist


def get_mc_links_group(item):
    mega_sid = mega_login(False)

    itemlist = []

    id = item.mc_group_id

    filename_hash = xbmc.translatePath(
        "special://home/temp/kodi_nei_mc_" + hashlib.sha1(item.channel + item.url + id).hexdigest())

    if os.path.isfile(filename_hash):

        file = open(filename_hash, "r")

        i = 1

        for line in file:

            line = line.rstrip()

            if i > 1:

                url = line

                url_split = url.split('#')

                name = url_split[1]

                size = url_split[2]

                title = name + ' [' + str(format_bytes(float(size))) + ']'

                itemlist.append(
                    Item(channel=item.channel, action="play", server='mega', title=title, url=url, parentContent=item,
                         folder=False))

            else:

                links_hash = line

                data = scrapertools.cache_page(
                    "https://noestasinvitado.com/gen_mc.php?id=" + id + "&raw=1")

                patron = '(.*? *?\[[0-9.]+ *?.*?\]) *?(https://megacrypter.noestasinvitado.com/.+)'

                matches = re.compile(patron).findall(data)

                if matches:

                    hasheable = ""

                    for title, url in matches:
                        hasheable += title

                    links_hash2 = hashlib.sha1(hasheable).hexdigest()

                    if links_hash != links_hash2:
                        file.close()

                        os.remove(filename_hash)

                        return get_mc_links_group(item)
                else:
                    file.close()

                    return itemlist

            i += 1

        file.close()

    else:

        data = scrapertools.cache_page(
            "https://noestasinvitado.com/gen_mc.php?id=" + id + "&raw=1")

        patron = '(.*? *?\[[0-9.]+ *?.*?\]) *?(https://megacrypter.noestasinvitado.com/.+)'

        matches = re.compile(patron).findall(data)

        if matches:

            hasheable = ""

            for title, url in matches:
                hasheable += title

            links_hash = hashlib.sha1(hasheable).hexdigest()

            compress_pattern = re.compile('\.(zip|rar|rev)$', re.IGNORECASE)

            file = open(filename_hash, "w+")

            file.write((links_hash + "\n").encode('utf-8'))

            for title, url in matches:

                url_split = url.split('/!')

                mc_api_url = url_split[0] + '/api'

                mc_info_res = mc_api_req(
                    mc_api_url, {
                        'm': 'info', 'link': url, 'reverse': MC_REVERSE_DATA})

                name = mc_info_res['name'].replace('#', '')

                size = mc_info_res['size']

                key = mc_info_res['key']

                noexpire = mc_info_res['expire'].split('#')[1]

                compress = compress_pattern.search(name)

                if compress:

                    itemlist.append(Item(channel=item.channel,
                                         title="[COLOR red][B]ESTE VÍDEO ESTÁ COMPRIMIDO Y NO ES COMPATIBLE "
                                               "(habla con el uploader para que lo suba sin comprimir).[/B][/COLOR]",
                                         action="", url="", folder=False))

                    break

                else:

                    title = name + ' [' + str(format_bytes(size)) + ']'

                    url = url + '#' + name + '#' + str(size) + '#' + key + '#' + noexpire

                    file.write((url + "\n").encode('utf-8'))

                    itemlist.append(
                        Item(channel=item.channel, action="play", server='mega', title=title, url=url + '#' + mega_sid,
                             parentContent=item, folder=False))

            file.close()

    return itemlist


def find_mc_links(item, data):
    msg_id = re.compile('subject_([0-9]+)', re.IGNORECASE).search(data)

    if msg_id:

        thanks_match = re.compile(
            '/\?action=thankyou;msg=' +
            msg_id.group(1),
            re.IGNORECASE).search(data)

        if thanks_match:
            data = scrapertools.cache_page(item.url + thanks_match.group(0))

    itemlist = []

    patron = 'id="mc_link_.*?".*?data-id="(.*?)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if matches:

        if len(matches) > 1:

            i = 1

            for id in matches:
                itemlist.append(Item(channel=item.channel, action="get_mc_links_group",
                                     title='[' + str(i) + '/' + str(len(matches)) + '] ' + item.title, url=item.url,
                                     mc_group_id=id, folder=True))

                i = i + 1
        else:
            itemlist = get_mc_links_group(
                Item(channel=item.channel, action='', title='', url=item.url, mc_group_id=matches[0], folder=True))
    else:

        mega_sid = mega_login(False)

        filename_hash = xbmc.translatePath(
            "special://home/temp/kodi_nei_mc_" + hashlib.sha1(item.channel + item.url).hexdigest())

        if os.path.isfile(filename_hash):

            file = open(filename_hash, "r")

            i = 1

            for line in file:

                line = line.rstrip()

                if i > 1:

                    url = line

                    url_split = url.split('#')

                    name = url_split[1]

                    size = url_split[2]

                    title = name + ' [' + str(format_bytes(float(size))) + ']'

                    itemlist.append(
                        Item(channel=item.channel, action="play", server='mega', title=title, url=url + '#' + mega_sid,
                             parentContent=item, folder=False))

                else:

                    links_hash = line

                    patron = 'https://megacrypter.noestasinvitado.com/[!0-9a-zA-Z_/-]+'

                    matches = re.compile(patron).findall(data)

                    if matches:

                        links_hash2 = hashlib.sha1(
                            "".join(matches)).hexdigest()

                        if links_hash != links_hash2:
                            file.close()

                            os.remove(filename_hash)

                            return find_mc_links(item, data)
                    else:

                        file.close()

                        return itemlist

                i += 1

            file.close()

        else:

            urls = []

            patron = 'https://megacrypter.noestasinvitado.com/[!0-9a-zA-Z_/-]+'

            matches = re.compile(patron).findall(data)

            if matches:

                compress_pattern = re.compile(
                    '\.(zip|rar|rev)$', re.IGNORECASE)

                file = open(filename_hash, "w+")

                links_hash = hashlib.sha1("".join(matches)).hexdigest()

                file.write((links_hash + "\n").encode('utf-8'))

                for url in matches:

                    if url not in urls:

                        urls.append(url)

                        url_split = url.split('/!')

                        mc_api_url = url_split[0] + '/api'

                        mc_info_res = mc_api_req(
                            mc_api_url, {
                                'm': 'info', 'link': url, 'reverse': MC_REVERSE_DATA})

                        name = mc_info_res['name'].replace('#', '')

                        size = mc_info_res['size']

                        key = mc_info_res['key']

                        if mc_info_res['expire']:
                            noexpire = mc_info_res['expire'].split('#')[1]
                        else:
                            noexpire = ''

                        compress = compress_pattern.search(name)

                        if compress:
                            itemlist.append(Item(channel=item.channel,
                                                 title="[COLOR red][B]ESTE VÍDEO ESTÁ COMPRIMIDO Y NO ES COMPATIBLE"
                                                       " (habla con el uploader para que lo suba sin comprimir)."
                                                       "[/B][/COLOR]",
                                                 action="", url="", folder=False))
                            break
                        else:
                            title = name + ' [' + str(format_bytes(size)) + ']'
                            url = url + '#' + name + '#' + str(size) + '#' + key + '#' + noexpire
                            file.write((url + "\n").encode('utf-8'))
                            itemlist.append(Item(channel=item.channel, action="play", server='mega', title=title,
                                                 url=url + '#' + mega_sid, parentContent=item, folder=False))

                file.close()

    return itemlist


def indice_links(item):
    itemlist = []

    data = scrapertools.cache_page(item.url)

    patron = '<tr class="windowbg2">[^<>]*<td[^<>]*>[^<>]*<img[^<>]*>[^<>]' \
             '*</td>[^<>]*<td>[^<>]*<a href="([^"]+)">(.*?)</a>[^<>]*</td>[^<>]*<td[^<>]*>[^<>]*<a[^<>]*>([^<>]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, uploader in matches:

        url = urlparse.urljoin(item.url, scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle)

        parsed_title = parse_title(scrapedtitle)

        year = parsed_title['year']

        content_title = parsed_title['title']

        if item.title.find('Películas') != -1:

            if item.title.find(' HD ') != -1:
                quality = 'HD'
            else:
                quality = 'SD'

            title = "[COLOR darkorange][B]" + content_title + \
                    "[/B][/COLOR] (" + year + ") [" + quality + \
                    "] (" + uploader + ")"
        else:
            title = scrapedtitle

        thumbnail = ""

        item.infoLabels = {'year': year}

        itemlist.append(item.clone(action="foro", title=title, url=url, thumbnail=thumbnail, folder=True,
                                   contentTitle=content_title))

    return itemlist


def post(url, data):
    import ssl
    from functools import wraps

    def sslwrap(func):
        @wraps(func)
        def bar(*args, **kw):
            kw['ssl_version'] = ssl.PROTOCOL_TLSv1
            return func(*args, **kw)

        return bar

    ssl.wrap_socket = sslwrap(ssl.wrap_socket)

    request = urllib2.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Chrome/30.0.1599.101 Safari/537.36"})

    contents = urllib2.urlopen(request).read()

    return contents


def load_mega_proxy():
    try:
        mega_proxy = proxy.MegaProxyServer('', MC_REVERSE_PORT)
        mega_proxy.daemon = True
        mega_proxy.start()
    except socket.error:
        pass


def mc_api_req(api_url, req):
    load_mega_proxy()

    res = post(api_url, json.dumps(req))

    return json.loads(res)


def format_bytes(bytes, precision=2):
    units = ['B', 'KB', 'MB', 'GB', 'TB']

    bytes = max(bytes, 0)

    pow = min(
        math.floor(
            math.log(
                bytes if bytes else 0,
                1024)),
        len(units) -
        1)

    bytes = float(bytes) / (1 << int(10 * pow))

    return str(round(bytes, precision)) + ' ' + units[int(pow)]


def extract_title(title):
    pattern = re.compile('^[^\[\]()]+', re.IGNORECASE)

    res = pattern.search(title)

    if res:

        return res.group(0)

    else:

        return ""


def extract_year(title):
    pattern = re.compile('([0-9]{4})[^p]', re.IGNORECASE)

    res = pattern.search(title)

    if res:

        return res.group(1)

    else:

        return ""


def parse_title(title):
    return {'title': extract_title(title), 'year': extract_year(title)}


def get_filmaffinity_data(title, year, genre):
    url = "https://www.filmaffinity.com/es/advsearch.php?stext=" + title.replace(' ',
                                                                                 '+') + "&stype%5B%5D" \
                                                                                        "=title&country=" \
                                                                                        "&genre=" + genre + \
          "&fromyear=" + year + "&toyear=" + year

    logger.info(url)

    data = scrapertools.cache_page(url)

    res = re.compile(
        "< *?div +class *?= *?\"avgrat-box\" *?> *?([0-9,]+) *?<",
        re.DOTALL).search(data)

    if res:

        res_thumb = re.compile(
            "https://pics\\.filmaffinity\\.com/[^\"]+-msmall\\.jpg",
            re.DOTALL).search(data)

        if res_thumb:
            thumb_url = res_thumb.group(0)
        else:
            thumb_url = None

        return [res.group(1).replace(',', '.'), thumb_url]

    else:

        url = "https://www.filmaffinity.com/es/advsearch.php?stext=" + title.replace(' ',
                                                                                     '+') + "&stype%5B%5D=" \
                                                                                            "title&country=" \
                                                                                            "&genre=" + genre

        data = scrapertools.cache_page(url)

        res_thumb = re.compile(
            "https://pics\\.filmaffinity\\.com/[^\"]+-msmall\\.jpg",
            re.DOTALL).search(data)

        if res_thumb:
            thumb_url = res_thumb.group(0)
        else:
            thumb_url = None

        res = re.compile(
            "< *?div +class *?= *?\"avgrat-box\" *?> *?([0-9,]+) *?<",
            re.DOTALL).search(data)

        if res:

            return [res.group(1).replace(',', '.'), thumb_url]

        else:

            return [None, thumb_url]


# NEIFLIX uses a modified version of MEGASERVER LIB that supports
# Megacrypter links
def check_megaserver_lib():
    update_url = 'https://raw.githubusercontent.com/tonikelope/neiflix/master/lib/megaserver/'

    megaserver_lib_path = xbmc.translatePath(
        'special://home/addons/plugin.video.alfa/lib/megaserver/')

    sha1_checksums = {'client.py': 'c1742a49b3053861280b446dc7b901536beb5a3b',
                      'crypto.py': 'a6db68758d1045bc8293f25dfb302b2b2086370c',
                      'cursor.py': '4cda5b409dc876eee531e91f3f6612fb7385371b',
                      'errors.py': 'a799c27134f696413b9fae333ec7130f6ebd5da0',
                      'file.py': '865b1c2356464ad76254dab71f90ccd40ea32d0e',
                      'handler.py': '949b5247ed28d3f95aa1c1563b1b45354f25fb2d',
                      '__init__.py': '5a2a5f6113e1b0dc9d0ef34a026511a1cf5135e4',
                      'server.py': '8694df96152941ed08f3e37e640dd95d8b6ab4b6',
                      'mega.py': '20975e9048a87f84a7826c36bd65439ef8aeb273',
                      'proxy.py': '1dea0c84e2e206682e055ab332a910580680a2a8'}

    modified = 0

    if not os.path.exists(megaserver_lib_path):
        os.mkdir(megaserver_lib_path)

    for filename, checksum in sha1_checksums.iteritems():

        if not os.path.exists(megaserver_lib_path + filename):

            urllib.urlretrieve(
                update_url + filename,
                megaserver_lib_path + filename)

            modified = 1

        elif hashlib.sha1(open(megaserver_lib_path + filename, 'rb').read()).hexdigest() != checksum:

            os.rename(
                megaserver_lib_path +
                filename,
                megaserver_lib_path +
                filename +
                ".bak")

            urllib.urlretrieve(
                update_url + filename,
                megaserver_lib_path + filename)

            modified = 1

    if modified:
        platformtools.dialog_notification(
            "NEIFLIX", "Megaserver lib actualizada")

    return modified
