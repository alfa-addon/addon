# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Ricerca "Saghe"
# https://alfa-addon.com/categories/kod-addon.50/
# ------------------------------------------------------------

import datetime
import re
import urllib

from core import httptools, tmdb
from core import scrapertools
from core.item import Item
from core.tmdb import infoIca
from platformcode import logger, config

PERPAGE = 15

tmdb_key = tmdb.tmdb_auth_key  # tmdb_key = '92db8778ccb39d825150332b0a46061d'
# tmdb_key = '92db8778ccb39d825150332b0a46061d'
dttime = (datetime.datetime.utcnow() - datetime.timedelta(hours=5))
systime = dttime.strftime('%Y%m%d%H%M%S%f')
today_date = dttime.strftime('%Y-%m-%d')
month_date = (dttime - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
month2_date = (dttime - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
year_date = (dttime - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
tmdb_image = 'http://image.tmdb.org/t/p/original'
tmdb_poster = 'http://image.tmdb.org/t/p/w500'


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel=item.channel,
                     title="[COLOR yellow]Cult IMDB[/COLOR]",
                     action="movies",
                     url='https://www.imdb.com/list/ls000571226/',
                     thumbnail="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVTW_L9vDQY0sjdlpfiOZdI0Nvi_NxSBpxmltDOFUYlctVxzX0Qg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]The Marvel Universe[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/50941077760ee35e1500000c?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/6t3KOEUtrIPmmtu1czzt6p2XxJy.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]The DC Comics Universe[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/5094147819c2955e4c00006a?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/xWlaTLnD8NJMTT9PGOD9z5re1SL.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]iMDb Top 250 Movies[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/522effe419c2955e9922fcf3?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/9O7gLzmreU0nGkIB6K3BsJbzvNv.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Rotten Tomatoes top 100 movies of all times[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/5418c914c3a368462c000020?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/zGadcmcF48gy8rKCX2ubBz2ZlbF.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Reddit top 250 movies[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/54924e17c3a3683d070008c8?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/dM2w364MScsjFf8pfMbaWUcWrR.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Sci-Fi Action[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/54408e79929fb858d1000052?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/5ig0kdWz5kxR4PHjyCgyI5khCzd.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]007 - Movies[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/557b152bc3a36840f5000265?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/zlWBxz2pTA9p45kUTrI8AQiKrHm.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Disney Classic Collection[/COLOR]",
                     action="tmdb_saghe_alt",
                     url='http://api.themoviedb.org/3/list/51224e42760ee3297424a1e0?api_key=%s&language=it' % tmdb_key,
                     thumbnail="https://image.tmdb.org/t/p/w180_and_h270_bestv2/vGV35HBCMhQl2phhGaQ29P08ZgM.jpg"),
                Item(channel=item.channel,
                     title="[COLOR yellow]Bad Movies[/COLOR]",
                     action="badmovies",
                     url='http://www.badmovies.org/movies/',
                     thumbnail="http://www.badmovies.org/mainpage/badmovielogo_600.jpg")]
    return itemlist


def tmdb_saghe_alt(item):
    itemlist = []

    alphabet = dict()

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patron = '"title":"(.*?)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle in matches:
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(scrapedtitle)

    for letter in sorted(alphabet):
        itemlist.append(
            Item(channel=item.channel,
                 action="tmdb_saghe",
                 url='\n\n'.join(alphabet[letter]),
                 title=letter,
                 fulltitle=letter))

    return itemlist


def tmdb_saghe(item):
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    matches = item.url.split('\n\n')
    for i, (scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

        itemlist.append(infoIca(
            Item(channel=item.channel,
                 action="do_search",
                 contentType="movie",
                 extra=urllib.quote_plus(scrapedtitle),
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 plot=scrapedplot,
                 thumbnail=scrapedthumbnail), tipo="movie"))

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="tmdb_saghe",
                 title=config.get_localized_string(30992),
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def badmovies(item):
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,
                                          '<table width="100%" cellpadding="6" cellspacing="1" class="listtab">(.*?)<tr><td align="center" valign="top">')

    # Estrae i contenuti 
    patron = r'">([^<]+)\s*</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    scrapedurl = ""
    scrapedplot = ""
    scrapedthumbnail = ""
    for i, (scrapedtitle) in enumerate(matches):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break
        title = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(infoIca(
            Item(channel=item.channel,
                 extra=urllib.quote_plus(title),
                 action="do_search",
                 title=title,
                 url=title,
                 thumbnail=scrapedthumbnail,
                 fulltitle=title,
                 show=title,
                 plot=scrapedplot,
                 folder=True), tipo='movie'))

    if len(matches) >= p * PERPAGE:
        scrapedurl = item.url + '{}' + str(p + 1)
        itemlist.append(
            Item(channel=item.channel,
                 extra=item.extra,
                 action="badmovies",
                 title=config.get_localized_string(30992),
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def do_search(item):
    from channels import search
    return search.do_search(item)


def movies(item):
    logger.info("[saghe.py]==> movies")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    groups = scrapertools.find_multiple_matches(data,
                                                r'<div class="lister-item-image ribbonize"(.*?)<div class="wtw-option-standalone"')

    for group in groups:
        infos = \
            {
                'title': single_scrape(group, r'<a[^>]+>([^<]+)</a>'),
                'year': single_scrape(group, r'unbold">\((\d+)\)</span>'),
                'rating': single_scrape(group, r'star__rating">(\d+,?\d*)</span>'),
                'plot': single_scrape(group, r'<p class="">\s*([^<]+)</p>'),
                'genres': single_scrape(group, r'genre">\s*([^<]+)</span>'),
                'age': single_scrape(group, r'certificate">([^<]+)</span>'),
                'metascore': single_scrape(group, r'metascore[^>]*>\s*(\d+)[^>]+>'),
                'image': single_scrape(group, r'loadlate="([^"]+)"[^>]+>')
            }

        infos['title'] = scrapertools.decodeHtmlentities(infos['title']).strip()
        infos['plot'] = scrapertools.decodeHtmlentities(infos['plot']).strip()

        title = "%s (%s)%s[%s]" % (infos['title'], color(infos['year'], "gray"),
                                   (" [%s]" % age_color("%s" % infos['age'])) if infos['age'] else "",
                                   color(infos['rating'], "orange"))

        plot = "Anno: %s%s\nVoto: %s\nGeneri: %s\nMetascore: %s\nDescrizione:\n%s" % \
               (infos['year'], "\nPubblico: %s" % age_color(infos['age']) if infos['age'] else "", infos['rating'],
                infos['genres'], infos['metascore'], infos['plot'])

        itemlist.append(
            Item(channel=item.channel,
                 text_color="azure",
                 action="do_search",
                 contentTitle=infos['title'],
                 infoLabels={'year': infos['year']},
                 title=title,
                 plot=plot,
                 extra="%s{}%s" % (urllib.quote_plus(infos['title']), "movie"),
                 thumbnail=infos['image']))

    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def age_color(age):
    logger.info("[saghe.py]==> age_color")
    if age.lower() == "t":
        age = color(age, "green")
    elif age.lower() == "pg":
        age = color(age, "yellow")
    elif age.lower() == "vm14":
        age = color(age, "yellow")
    elif age.lower() == "vm18":
        age = color(age, "red")
    elif 'banned' in age.lower():
        age = color(age.replace('(', '').replace(')', '').strip(), "red")

    return age


def single_scrape(text, patron):
    logger.info("[saghe.py]==> single_scrape")
    return scrapertools.find_single_match(text, patron)


def color(text, color):
    logger.info("[saghe.py]==> color")
    return "[COLOR %s]%s[/COLOR]" % (color, text)
