# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import tmdb

## italiafilm                                             \'([^\']+)\'

host = 'http://www.txxx.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Ultimas" , action="peliculas", url=host + "/latest-updates/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valoradas" , action="peliculas", url=host + "/top-rated/"))
    itemlist.append( Item(channel=item.channel, title="Mas polpular" , action="peliculas", url=host + "/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="CHANNELS" , action="catalogo", url=host + "/channels-list/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?keyword=%s" % texto


    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Channels(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

                            # <div class="channel-thumb">
                            #     <a href="/channels/twistys/" title="Twistys Network" class="channel-thumb--image"><img src="http://www.txxx.com/contents/cst/228/c3_twistys285x165-2.jpg" alt="Twistys Network" />
                            #         <div class="channel--overlay channel--overlay-video"><i class="i i--color-white i--size--s"><svg xmlns="http://www.w3.org/2000/svg" version="1.1"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#i--video"></use></svg></i><span>1256</span>
                            #         </div>
                            #     </a>
                            #     <div class="channel-thumb--subscribe">
                            #         <button class="thumb__add-to-btn btn btn--size--m hint js-subscription" data-action="subscribe" data-subsribed="true" data-id="228" data-subscribe-to="cs" type="button" data-hint="Subscribe"><i class="i i--size--m"><svg xmlns="http://www.w3.org/2000/svg" version="1.1"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#i--plus"></use></svg></i>
                            #         </button>
                            #         <button class="thumb__add-to-btn btn btn--size--m hint js-subscription is-hidden" data-action="unsubscribe" data-subsribed="false" data-id="228" data-subscribe-to="cs" type="button" data-hint="Unsubscribe"><i class="i i--size--m"><svg xmlns="http://www.w3.org/2000/svg" version="1.1"><use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#i--minus"></use></svg></i>
                            #         </button>
                            #     </div>
                            #     <div class="channel-thumb--title"><a href="/channels/twistys/" title="Twistys Network" class="link">Twistys Network</a>
                            #     </div>
                            #     <div class="channel-thumb--info"><span>Categories:</span><a href="/channels-list/babes/" class="link">Babes</a>, <a href="/channels-list/hd/" class="link">HD</a>, <a href="/channels-list/masturbate/" class="link">Masturbation</a>, <a href="/channels-list/dildos-toys/" class="link">Dildos/Toys</a>, <a href="/channels-list/lingerie/" class="link">Lingerie</a>
                            #     </div>
                            # </div>

    patron  = '<div class="channel-thumb">.*?<a href="([^"]+)" title="([^"]+)".*?<img src="([^"]+)".*?<span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,num in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        title = scrapedtitle + "[COLOR yellow]  " + num + "[/COLOR]"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


#               <a class=" btn btn--size--l btn--next" href="/categories/big-natural-tits/2/" title="Next Page"


# "Next page >>"
    else:
        patron  = '<a class=" btn btn--size--l btn--next" href="([^"]+)" title="Next Page"'
        next_page = re.compile(patron,re.DOTALL).findall(data)
#        next_page = scrapertools.find_single_match(data,'class="last" title=.*?<a href="([^"]+)">')
        next_page =  next_page[0]
        next_page = host + next_page
        itemlist.append( Item(channel=item.channel, action="catalogo", title=next_page , text_color="blue", url=next_page ) )
    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Categories(.*?)<li class="divider"')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#       <li class="list__item ex-cat-link" data-viewed="69336"><a class="link--pressed " href="http://www.txxx.com/categories/3d-toons/">3D Toons <span class="link__badge">(312)</span></a></li>


    patron  = '<div class="c-thumb">.*?<a href="([^"]+)".*?<img src="([^"]+)".*?<div class="c-thumb--overlay c-thumb--overlay-title">([^"]+)</div>.*?<span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle,num in matches:
        scrapedplot = ""
        title = scrapedtitle + "[COLOR yellow]  " + num + "[/COLOR]"
#        scrapedthumbnail = ""
#        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div id="wrapper" class="ortala">(.*?)Son &raquo;</a>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    # <div class="un-grid un-grid-video">
    #                           <div class="un-grid--thumb" data-video-id="6006316">
    #                              <div class="un-grid--thumb--content">
    #                                 <a href="https://www.txxx.com/videos/6006316/virgin-student-anal-and-oral-to-26-cm/" class="image js-thumb-pagination" data-screen_main="7" data-screen_amount="12"><img src="https://txxx-tn1.yurivideo.com/contents/videos_screenshots/6006000/6006316/220x165/7.jpg" alt="virgin student ,anal and oral to 26 cm." class="EoCk7" data-sgid="21" data-video-id="6006316"></a>
    #                                 <div class="thumb__box"><span class="thumb__duration">41:56</span></div>
    #                              </div>
    #                              <div class="un-grid--thumb--info">
    #                                 <a class="thumb__title thumb__title--left link title" href="https://www.txxx.com/videos/6006316/virgin-student-anal-and-oral-to-26-cm/" title="virgin student ,anal and oral to 26 cm.">virgin student ,anal and oral to 26 cm.</a>
    #                                 <div class="statistics thumb-info">
    #                                    <span class="viewed">
    #                                       <i class="i i--size--xs i--color-gray">
    #                                          <svg>
    #                                             <use xlink:href="#i--thumb-eye"></use>
    #                                          </svg>
    #                                       </i>
    #                                       0
    #                                    </span>
    #                                    <span class="thumb__rating">
    #                                       <i class="i i--size--xs i--color-gray">
    #                                          <svg>
    #                                             <use xlink:href="#i--thumb-thumb-up"></use>
    #                                          </svg>
    #                                       </i>
    #                                       0%
    #                                    </span>
    #                                    <span class="date">14 seconds ago</span>
    #                                 </div>
    #                              </div>
    #                           </div>


#    patron  = '<div class="content ">.*?<img class="content_image" src="([^"]+).mp4/\d+.mp4-\d.jpg" alt="([^"]+)".*?this.src="([^"]+)"'
    patron  = 'data-video-id="\d+">.*?<a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)".*?<span class="thumb__duration">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
#        title = scrapedtitle
        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
#        scrapedurl = scrapedurl.replace("/thumbs/", "/videos/") + ".mp4"

        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))


#               <a href="/latest-updates/2/" class="btn more-videos btn--size--l btn--width--full" title="Show next videos">
#               <a class=" btn btn--size--l btn--next" href="/categories/big-natural-tits/2/" title="Next Page"


# "Next page >>"
    else:
        patron  = '<a class=" btn btn--size--l btn--next" href="([^"]+)" title="Next Page"'
        next_page = re.compile(patron,re.DOTALL).findall(data)
#        next_page = scrapertools.find_single_match(data,'class="last" title=.*?<a href="([^"]+)">')
        next_page =  next_page[0]
        next_page = host + next_page
        itemlist.append( Item(channel=item.channel, action="peliculas", title=next_page , text_color="blue", url=next_page ) )

    return itemlist

def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#           var video_url="aHR0cHМ6Ly93d3cudHh4eС5jb20vZ2V0X2ZpbGUvМjЕvМDNjZWЕxZDYwYjliYjQyZmNhOTI3ZjQzZTZmМmNjNDYvNjU2МzАwМС82NTYzNDI4LzY1NjМ0МjhfaHЕubXА0Lz9kPTgzJmJyPTY2OА~~";
#           video_url+="||/get_file/21/03cea1d60b9bb42fca927f43e6f2cc46cd5c25d950/||193.111.52.130||1538503158";



    video_url = scrapertools.find_single_match(data, 'var video_url="([^"]*)"')
    video_url += scrapertools.find_single_match(data, 'video_url\+="([^"]*)"')

    partes = video_url.split('||')
    video_url = decode_url(partes[0])
    video_url = re.sub('/get_file/\d+/[0-9a-z]{32}/', partes[1], video_url)
    video_url += '&' if '?' in video_url else '?'
    video_url += 'lip=' + partes[2] + '&lt=' + partes[3]

    itemlist.append(item.clone(action="play", title=item.title, url=video_url))

    return itemlist

def decode_url(txt):
    _0x52f6x15 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    reto = ''; n = 0
    # En las dos siguientes líneas, ABCEM ocupan 2 bytes cada letra! El replace lo deja en 1 byte. !!!!: АВСЕМ (10 bytes) ABCEM (5 bytes)
    txt = re.sub('[^АВСЕМA-Za-z0-9\.\,\~]', '', txt)
    txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M')

    while n < len(txt):
        a = _0x52f6x15.index(txt[n])
        n += 1
        b = _0x52f6x15.index(txt[n])
        n += 1
        c = _0x52f6x15.index(txt[n])
        n += 1
        d = _0x52f6x15.index(txt[n])
        n += 1

        a = a << 2 | b >> 4
        b = (b & 15) << 4 | c >> 2
        e = (c & 3) << 6 | d
        reto += chr(a)
        if c != 64: reto += chr(b)
        if d != 64: reto += chr(e)

    return urllib.unquote(reto)
