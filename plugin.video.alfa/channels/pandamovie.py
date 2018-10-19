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

host= 'http://pandamovie.net/adult'

def isGeneric():
    return True

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/list-movies"))
#    itemlist.append( Item(channel=item.channel, title="Ultimas Peliculas" , action="peliculas", url="http://www.pordede.tv/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url="http://pandamovie.net/adult/list-movies"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url="http://pandamovie.net/adult/list-movies"))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "http://pandamovie.net/adult/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
        itemlist = []

        # Descarga la pagina
        data = scrapertools.cache_page(item.url)
        if item.title == "Categorias" :
            data = scrapertools.get_match(data,'<a href="#">Genres</a>(.*?)</ul>')
        else:
            data = scrapertools.get_match(data,'<a href="#">Studios</a>(.*?)</ul>')
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


        '''
        <a href="#">Genres</a>
         <ul class="menugen">
          <a href="#">Genres</a>
                     <ul class="menugen">
                        <li><a title="All Girl Movies" href="//pandamovie.co/adult/watch-all-girl-porn-movies-online-free">All Girl</a></li>
                        <li><a title="All Sex Movies" href="//pandamovie.co/adult/watch-all-sex-porn-movies-online-free">All Sex</a></li>
            <li><a title="All Girl Movies" href="//pandamovie.eu/adult/watch-all-girl-porn-movies-online-free">All Girl</a></li>
            <li><a title="All Sex Movies" href="//pandamovie.eu/adult/watch-all-sex-porn-movies-online-free">All Sex</a></li>
            <li><a title="Amateurs Movies" href="//pandamovie.eu/adult/watch-amateurs-porn-movies-online-free">Amateurs</a></li>
            <li><a title="Anal Movies" href="//pandamovie.eu/adult/watch-anal-porn-movies-online-free">Anal</a></li>
            <li><a title="Asian Movies" href="//pandamovie.eu/adult/watch-asian-porn-movies-online-free">Asian</a></li>
            <li><a title="Babysitter Movies" href="//pandamovie.eu/adult/watch-babysitter-porn-movies-online-free">Babysitter</a></li>
            <li><a title="BBW Movies" href="//pandamovie.eu/adult/watch-bbw-porn-movies-online-free">BBW</a></li>
            <li><a title="BDSM Movies" href="//pandamovie.eu/adult/watch-bdsm-porn-movies-online-free">BDSM</a></li>
            <li><a title="Bi-Sexual Movies" href="//pandamovie.eu/adult/watch-bi-sexual-porn-movies-online-free">Bi-Sexual</a></li>
            <li><a title="Big Tits Movies" href="//pandamovie.eu/adult/watch-big-boobs-porn-movies-online-free">Big Boobs</a></li>
            <li><a title="Big Butts Movies" href="//pandamovie.eu/adult/watch-big-butts-porn-movies-online-free">Big Butts</a></li>
            <li><a title="Big Cocks Movies" href="//pandamovie.eu/adult/watch-big-cocks-porns-movies-online-free">Big Cocks</a></li>
            <li><a title="Black Movies" href="//pandamovie.eu/adult/watch-black-porn-movies-online-free">Black</a></li>
            <li><a title="Blonde Movies" href="//pandamovie.eu/adult/watch-blonde-porn-movies-online-free">Blonde</a></li>
            <li><a title="Blow Jobs Movies" href="//pandamovie.eu/adult/watch-blow-jobs-porn-movies-online-free">Blow Jobs</a></li>
            <li><a title="Brazilian Movies" href="//pandamovie.eu/adult/watch-brazilian-porn-movies-online-free">Brazilian</a></li>
            <li><a title="Celebrity Movies" href="//pandamovie.eu/adult/watch-celebrity-porn-movies-online-free">Celebrity</a></li>
            <li><a title="Classic Movies" href="//pandamovie.eu/adult/watch-classic-porn-movies-online-free">Classic</a></li>
            <li><a title="Compilation Movies" href="//pandamovie.eu/adult/watch-compilation-porn-movies-online-free">Compilation</a></li>
            <li><a title="Couples Movies" href="//pandamovie.eu/adult/watch-couples-porn-movies-online-free">Couples</a></li>
            <li><a title="Cream Pie Movies" href="//pandamovie.eu/adult/watch-cream-pie-porn-movies-online-free">Cream Pie</a></li>
            <li><a title="Cuckold Movies" href="//pandamovie.eu/adult/watch-cuckold-porn-movies-online-free">Cuckold</a></li>
            <li><a title="Cumshots Movies" href="//pandamovie.eu/adult/watch-cumshots-porn-movies-online-free">Cumshots</a></li>
            <li><a title="Facial Movies" href="//pandamovie.eu/adult/watch-facial-porn-movies-online-free">Facial</a></li>
            <li><a title="Gang Bangers Movies" href="//pandamovie.eu/adult/watch-gang-bangers-porn-movies-online-free">Gang Bangers</a></li>
            <li><a title="German Movies" href="//pandamovie.eu/adult/watch-german-porn-movies-online-free">German</a></li>
            <li><a title="Gonzo Movies" href="//pandamovie.eu/adult/watch-gonzo-porn-movies-online-free">Gonzo</a></li>
            <li><a title="Hardcore Movies" href="//pandamovie.eu/adult/watch-hardcore-porn-movies-online-free">Hardcore</a></li>
		    <li><a title="Interracial Movies" href="//pandamovie.eu/adult/watch-interracial-porn-movies-online-free">Interracial</a></li>
            <li><a title="Latina Movies" href="//pandamovie.eu/adult/watch-latina-porn-movies-online-free">Latina</a></li>
            <li><a title="Lesbien Movies" href="//pandamovie.eu/adult/watch-lesbien-porn-movies-online-free">Lesbien</a></li>
            <li><a title="MILF Movies" href="//pandamovie.eu/adult/watch-milf-porn-movies-online-free">MILF</a></li>
            <li><a title="Oral Movies" href="//pandamovie.eu/adult/watch-oral-porn-movies-online-free">Oral</a></li>
            <li><a title="Parodies Movies" href="//pandamovie.eu/adult/watch-parodies-porn-parody-movies-online-free">Parodies</a></li>
            <li><a title="Squirting Movies" href="//pandamovie.eu/adult/watch-squirting-porn-movies-online-free">Squirting</a></li>
            <li><a title="Teens Movies" href="//pandamovie.eu/adult/watch-teens-porn-movies-online-free">Teens</a></li>
         </ul>


        <li><a title=[^>]+href="([^"]+)">([^<]+)

        '''
        # Extrae las entradas (carpetas)
        patron  = '<li><a title=".*?" href="([^"]+)">([^<]+)</a>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            scrapedurl = scrapedurl.replace("https:", "")
            scrapedurl = "https:" + scrapedurl
            itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist


def peliculas(item):
    '''
    <div class="item cf item-post">
    <div class="thumb">
    <span class="long_min_source_hd"></span>
    <span class="long_min">All Sex, Big Boobs, Big Cocks, MILF</span>
    <a class="clip-link" title="Interracial Affair 2 (2016)" href="http://pandamovie.net/adult/watch-interracial-affair-2-movie-online-free">
    <span class="clip">
    <img alt="Interracial Affair 2" width="190" height="266" src="http://pandamovie.net/adult/wp-content/uploads/2016/05/Interracial-Affair-2-190x269.jpg" data-qazy="true"/><span class="vertical-align"></span>
    </span>
    <span class="overlay"></span>
    </a>
    </div> <div class="data">
    <h3 class="title"><a href="http://pandamovie.net/adult/watch-interracial-affair-2-movie-online-free" title="Interracial Affair 2 (2016)">Interracial Affair 2 (2016)</a></h3>
    </div>
    </div>
    '''
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="item cf item-post"(.*?)</a></h\d+>'
    matches = re.compile(patron,re.DOTALL).findall(data)


    for match in matches:
    #<h3 class="entry-title"><a href="http://www.italia-film.co/dottore-la-fica-nel-culo-2015/" rel="bookmark">Dottore, Ho La Fica nel Culo (2015)</a></h3>

        title = scrapertools.find_single_match(match,'<a class="clip-link" title="([^"]+)"')
#        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'src="([^"]+)"')


        itemlist.append( Item(channel=item.channel, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''

    <a class="nextpostslink" rel="next" href="https://pandamovie.eu/adult/list-movies/page/2">&raquo;</a
    <a clas="next" href="http://pandamovie.net/adult/page/2?s=lena" >Next &raquo;</a>
    <a  href="https://pandamovie.eu/adult/director/reality-kings/page/2" >Next &raquo;</a>
    <link rel="next" href="https://pandamovie.eu/adult/director/reality-kings/page/2" />
    '''

#   "Next page >>"
    next_page_url = scrapertools.find_single_match(data,'<a clas.*?"next.*?href="(.*?)"')
    if next_page_url =="":
        next_page_url = scrapertools.find_single_match(data,'<link rel="next" href="(.*?)" />')

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

'''
def findvideos(item):
    logger.info()

    itemlist = []
    plot = item.plot


class="optxt"><span>Castellano</span>
<span class="q">
<img src="http://www.peliscity.com/wp-content/themes/diddli/images/flags/es_es.png" width="15"></span>
<span class="q">Hd Real 720</span>
</span></a></li>
<li><a style="cursor:pointer; cursor: hand" rel="https://openload.co/embed/cJJJrYhYVoY/Elena.secreto.avalor.m7p.CAS.Final.mkv.mp4" class="tooltip1 source_item clearfix" title="">
<span class="opnum">2</span>
<span class="optxt"><span>Castellano</span><span class="q">
<img
src="http://www.peliscity.com/wp-content/themes/diddli/images/flags/es_es.png" width="15"></span><span
class="q">Hd Real 720</span>
</span></a></li><li><a
style="cursor:pointer; cursor: hand" rel="http://uptostream.com/iframe/7f8vnm1pswxx" class="tooltip1 source_item clearfix" title="">
<span class="opnum">3</span>

patron = 'class="optxt"><span>(.*?)<.*?width.*?class="q">(.*?)</span.*?cursor: hand" rel="(.*?)"'


patron = '<li><span class=".*?href="(.*?)".*?id="#iframe">(.*?)</a>'

  <h2 class="film_trama">Watch Hall Of Famers 3 online - Links</h2>
               </div>
               <div class="under_line"></div>
               <div class="the_trama">
                  <div id="pettabs">
                     <ul>
<li><span class="openload_sprite"><a title="Hall Of Famers 3 - on Openload" href="https://openload.co/embed/P6wCQqRnWM8/Hall_Of_Famers_3_2016_1080p_DVDRip_ek84.mp4" rel="nofollow" id="#iframe">openload.co</a></li>
<li><span class="flashx_sprite"><a title="Hall Of Famers 3 - on Flashx" href="http://www.flashx.tv/embed-dj23hprnugcs-732x465.html" rel="nofollow" id="#iframe">flashx.tv</a></li>
<li><span class="nowvideo_sprite"><a title="Hall Of Famers 3 - on Nowvideo" href="http://embed.nowvideo.sx/embed.php?v=8c0d9891c0994" rel="nofollow" id="#iframe">nowvideo.sx</a></li>
<li><span class="thevideo_sprite"><a title="Hall Of Famers 3 - on Thevideo" href="http://www.thevideo.me/embed-1nmhjyzxv28a-732x465.html" rel="nofollow" id="#iframe">thevideo.me</a></li>
<li><span class="vidup_sprite"><a title="Hall Of Famers 3 - on Vidup" href="http://vidup.me/embed-01w55i64vf4q.html" rel="nofollow" id="#iframe">vidup.me</a></li>
<li><span>&nbsp;&nbsp;<img src="http://pandamovie.net/adult/wp-content/uploads/2016/10/favicons-1.png" width="16" height="16"/></span><a title="Hall Of Famers 3 - on Datoporn" href="http://datoporn.com/embed-j92g6s9uwf5f-732x465.html" rel="nofollow" id="#iframe">datoporn.com</a></li>
<li><span>&nbsp;&nbsp;<img src="http://pandamovie.net/adult/wp-content/uploads/2016/10/favicons-3.png" width="16" height="16"/></span><a title="Hall Of Famers 3 - on StreamPlay" href="http://streamplay.to/embed-9e21g0avk5bh.html" rel="nofollow" id="#iframe">streamplay.to</a></li>
<li><span>&nbsp;&nbsp;<img src="http://pandamovie.net/adult/wp-content/uploads/2016/10/favicons-2.png" width="16" height="16"/></span><a title="Hall Of Famers 3 - on Rapidvideo" href="http://rapidvideo.ws/embed-fs37gkdtkw07-732x465.html" rel="nofollow" id="#iframe">rapidvideo.ws</a></li>
<li><span class="vidgg_sprite"><a title="Hall Of Famers 3 - on Vidgg" href="http://www.vidgg.to/embed/?id=c0a55a96140df" rel="nofollow" id="#iframe">vidgg.to</a></li>
<li><span class="movshare_sprite"><a title="Hall Of Famers 3 - on WholeCloud" href="http://wholecloud.net/embed.php?v=f11795f068901" rel="nofollow" id="#iframe">wholecloud.net</a></li>
<li><span class="cloudtime_sprite"></span><a title="Hall Of Famers 3 - on Cloudtime" href="http://cloudtime.to/embed.php?v=video/009c802c0f682" rel="nofollow" id="#iframe">cloudtime.to</a></li>
<li><span class="videoweed_sprite"><a title="Hall Of Famers 3 - on Bitvid" href="http://bitvid.sx/embed.php?v=6fabea105689a" rel="nofollow" id="#iframe">bitvid.sx</a></li>
<li><span class="novamov_sprite"><a title="Hall Of Famers 3 - on Auroravid" href="http://auroravid.to/embed.php?v=5c2265916f153" rel="nofollow" id="#iframe">auroravid.to</a></li>
<li><span class="streamin_sprite"><a title="Hall Of Famers 3 - on Streamin" href="http://streamin.to/embed-xeg135s8piam-732x465.html" rel="nofollow" id="#iframe">streamin.to</a></li>
<li><span class="videomega_sprite"><a title="Hall Of Famers 3 - on Netu" href="http://netu.tv/watch_video.php?v=5Rv2FMm58jOp&width=732&height=465" rel="nofollow" id="newtabforced"  target="_blank">Netu.tv</a></li>
<li>&nbsp;&nbsp;<img src="http://pandamovie.net/wp-content/uploads/favicons-2.png" width="16" height="16"/><a title="Hall Of Famers 3 - on Streamcloud" href="http://streamcloud.eu/wv7z6yo3j6yn/Hall_Of_Famers_3_2016_1080p_DVDRip_ek84.mp4.html" rel="nofollow" id="newtabforced"  target="_blank">streamcloud.eu</a></li>
</ul>
                  </div>
               </div>
            </div>





    # Descarga la pagina
    data = scrapertools.cache_page(item.url)
    patron = '<li><span class=".*?href="(.*?)".*?id="#iframe">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)


    for scrapedidioma, scrapedcalidad, scrapedurl in matches:
        idioma =""
    #  scrapedserver=re.findall("http[s*]?://(.*?)/",scrapedurl)
        title = item.title + " ["+scrapedcalidad+"][" + scrapedidioma + "][" + scrapedserver[0] + "]"
        if  not ("omina.farlante1"  in scrapedurl or "404" in scrapedurl) :
            itemlist.append( Item(channel=item.channel, action="play", title=title, fulltitle=title , url=scrapedurl , thumbnail="" , plot=plot , show = item.show) )
    return itemlist

def play(item):
    logger.info()

    itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist

'''
