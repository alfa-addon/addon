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
from core import jsontools


## italiafilm
__channel__ = "filmpornoita"
__category__ = "F"
__type__ = "generic"
__title__ = "Filmpornoita"
__language__ = "ES"


def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.filmpornoita mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="Peliculas" , action="peliculas", url="http://www.filmpornoita.net/"))
#    itemlist.append( Item(channel=__channel__, title="Ultimas Peliculas" , action="peliculas", url="http://www.pordede.tv/"))
    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://www.filmpornoita.net/"))

#    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist




def categorias(item):
        itemlist = []

        # Descarga la pagina
        data = scrapertools.cache_page(item.url)

        '''
<ul id="menu-menu-1" class="menu">
<li id="menu-item-150" class="menu-item menu-item-type-custom menu-item-object-custom current-menu-item current_page_item menu-item-home menu-item-150"><a href="http://www.filmpornoita.net/">Home</a></li>
<li id="menu-item-3820" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-3820"><a href="http://www.filmpornoita.net/category/lesbian/">Lesbian</a></li>
<li id="menu-item-524" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-524"><a href="http://www.filmpornoita.net/category/film-ita/">Film Ita</a></li>
<li id="menu-item-525" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-525"><a href="http://www.filmpornoita.net/category/hard/">Hard</a></li>
<li id="menu-item-526" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-526"><a href="http://www.filmpornoita.net/category/anal/">Anal</a></li>
<li id="menu-item-527" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-527"><a href="http://www.filmpornoita.net/category/18-teens/">18+ Teens</a></li>
<li id="menu-item-528" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-528"><a href="http://www.filmpornoita.net/category/interracial/">Interracial</a></li>
<li id="menu-item-530" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-530"><a href="http://www.filmpornoita.net/category/gonzo/">Gonzo</a></li>
<li id="menu-item-531" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-531"><a href="http://www.filmpornoita.net/category/milf/">Milf</a></li>
<li id="menu-item-529" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-529"><a href="http://www.filmpornoita.net/category/european/">European</a></li>
<li id="menu-item-537" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-537"><a href="http://www.filmpornoita.net/category/compilation/">Compilation</a></li>
<li id="menu-item-516" class="menu-item menu-item-type-post_type menu-item-object-page menu-item-516"><a href="http://www.filmpornoita.net/dmcacopyright/">DMCA/Copyright</a></li>
</ul>




        '''

        itemlist.append( Item(channel=__channel__, action="peliculas", title="Big Tits" , url="http://www.filmpornoita.net/tag/big-tits/" , thumbnail="" , plot="" , folder=True) )

        # Extrae las entradas (carpetas)
        patron  = '<li id="menu-item-[^>]+><a href="([^"]+)">([^<]+)'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for match in matches:
            scrapedtitle = match[1]
            scrapedtitle = scrapedtitle.replace("&#8211;","-")
            scrapedtitle = scrapedtitle.replace("&#8217;","'")
            scrapedurl = match[0]
            scrapedplot = ""
            scrapedthumbnail = ""
    #        if (DEBUG): logger.info("title=["+scrapedtitle+"], url=["+scrapedurl+"], thumbnail=["+scrapedthumbnail+"]")
            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist






def peliculas(item):
    '''
 	  <div class="post" id="post-17843">

<a href="http://www.filmpornoita.net/film-ita/la-sorella-di-papa-showtime/" title="Incesti Italiani 10: La Sorella di Papa"><img width="240" height="158" src="http://www.filmpornoita.net/wp-content/uploads/2015/12/La-sorella-di-papà-dvd-hard-300x197.jpg" class="attachment-240x180 wp-post-image" alt="Incesti Italiani 10: La Sorella di Papa" title="" /></a>


<div class="link"><a href="http://www.filmpornoita.net/film-ita/la-sorella-di-papa-showtime/">Incesti Italiani 10: La Sorella di...</a></div>

<span>Added: maggio 15, 2016 at 8:40 am</span>

<span>Tags: <a href="http://www.filmpornoita.net/tag/aa-vv/" rel="tag">AA.VV.</a>, <a href="http://www.filmpornoita.net/tag/andy-casanova-actors-uma/" rel="tag">Andy Casanova Actors Uma</a>, <a href="http://www.filmpornoita.net/tag/celine-dior/" rel="tag">Celine Dior</a>, <a href="http://www.filmpornoita.net/tag/etero/" rel="tag">Etero</a>, <a href="http://www.filmpornoita.net/tag/francesco-malcom/" rel="tag">Francesco Malcom</a>, <a href="http://www.filmpornoita.net/tag/frank-vesuvio/" rel="tag">Frank Vesuvio</a>, <a href="http://www.filmpornoita.net/tag/gabriel-montoya/" rel="tag">Gabriel Montoya</a>, <a href="http://www.filmpornoita.net/tag/giorgio-grandi/" rel="tag">Giorgio Grandi</a>, <a href="http://www.filmpornoita.net/tag/incesto/" rel="tag">incesto</a>, <a href="http://www.filmpornoita.net/tag/la-sorella-di-papa-showtime/" rel="tag">La sorella di papà - ShowTime</a>, <a href="http://www.filmpornoita.net/tag/letizia-bruni/" rel="tag">Letizia Bruni</a>, <a href="http://www.filmpornoita.net/tag/letizia-bruni-starring-letizia-bruni/" rel="tag">Letizia Bruni Starring: Letizia Bruni</a>, <a href="http://www.filmpornoita.net/tag/uma/" rel="tag">Uma</a></span>

</div>



<div class="post" id="post-21137">

<a href="http://www.filmpornoita.net/film-ita/le-confessioni-della-grande-sorella/" title="Le confessioni della grande sorella"><img width="240" height="162" src="http://www.filmpornoita.net/wp-content/uploads/2016/02/Le-confessioni-della-grande-sorella-300x203.jpg" class="attachment-240x180 wp-post-image" alt="Le confessioni della grande sorella" title="" /></a>


<div class="link"><a href="http://www.filmpornoita.net/film-ita/le-confessioni-della-grande-sorella/">Le confessioni della grande sorell...</a></div>

<span>Added: maggio 15, 2016 at 8:39 am</span>

<span>Tags: <a href="http://www.filmpornoita.net/tag/clericale/" rel="tag">Clericale</a>, <a href="http://www.filmpornoita.net/tag/etero/" rel="tag">Etero</a>, <a href="http://www.filmpornoita.net/tag/film-con-trama/" rel="tag">FILM CON TRAMA</a>, <a href="http://www.filmpornoita.net/tag/jessica-rizzo/" rel="tag">Jessica Rizzo</a></span>

</div>



<div class="post" id="post-18663">

<a href="http://www.filmpornoita.net/film-ita/mentre-ti-fotto-grida-troia-fm-video/" title="Mentre Ti Fotto Grida Troia &#8211; FM Video"><img width="240" height="160" src="http://www.filmpornoita.net/wp-content/uploads/2016/01/Mentre-Ti-Fotto-Grida-Troia-300x200.jpg" class="attachment-240x180 wp-post-image" alt="Mentre Ti Fotto Grida Troia &#8211; FM Video" title="" /></a>


<div class="link"><a href="http://www.filmpornoita.net/film-ita/mentre-ti-fotto-grida-troia-fm-video/">Mentre Ti Fotto Grida Troia &#8211...</a></div>

<span>Added: maggio 15, 2016 at 8:27 am</span>

<span>Tags: <a href="http://www.filmpornoita.net/tag/amateur/" rel="tag">Amateur</a>, <a href="http://www.filmpornoita.net/tag/anal/" rel="tag">Anal</a>, <a href="http://www.filmpornoita.net/tag/asian/" rel="tag">Asian</a>, <a href="http://www.filmpornoita.net/tag/babysitter/" rel="tag">babysitter</a>, <a href="http://www.filmpornoita.net/tag/bbw/" rel="tag">BBW</a>, <a href="http://www.filmpornoita.net/tag/beurette/" rel="tag">beurette</a>, <a href="http://www.filmpornoita.net/tag/big-black-cock/" rel="tag">big black cock</a>, <a href="http://www.filmpornoita.net/tag/big-dick/" rel="tag">big dick</a>, <a href="http://www.filmpornoita.net/tag/big-tits/" rel="tag">Big Tits</a>, <a href="http://www.filmpornoita.net/tag/blowjob/" rel="tag">Blowjob</a>, <a href="http://www.filmpornoita.net/tag/bondage-step-mom/" rel="tag">Bondage Step mom</a>, <a href="http://www.filmpornoita.net/tag/brunette/" rel="tag">Brunette</a>, <a href="http://www.filmpornoita.net/tag/check/" rel="tag">check</a>, <a href="http://www.filmpornoita.net/tag/clip/" rel="tag">clip</a>, <a href="http://www.filmpornoita.net/tag/creampie/" rel="tag">Creampie</a>, <a href="http://www.filmpornoita.net/tag/ebony/" rel="tag">Ebony</a>, <a href="http://www.filmpornoita.net/tag/eros-grimaldi/" rel="tag">Eros Grimaldi</a>, <a href="http://www.filmpornoita.net/tag/facial/" rel="tag">Facial</a>, <a href="http://www.filmpornoita.net/tag/for-women/" rel="tag">For Women</a>, <a href="http://www.filmpornoita.net/tag/free/" rel="tag">Free</a>, <a href="http://www.filmpornoita.net/tag/gangbang/" rel="tag">Gangbang</a>, <a href="http://www.filmpornoita.net/tag/gaymale/" rel="tag">Gay(male)</a>, <a href="http://www.filmpornoita.net/tag/hardcore/" rel="tag">Hardcore</a>, <a href="http://www.filmpornoita.net/tag/lesbian/" rel="tag">Lesbian</a>, <a href="http://www.filmpornoita.net/tag/massage/" rel="tag">Massage</a>, <a href="http://www.filmpornoita.net/tag/mature/" rel="tag">Mature</a>, <a href="http://www.filmpornoita.net/tag/mentre-ti-fotto-grida-troia-fm-video/" rel="tag">Mentre Ti Fotto Grida Troia - FM Video</a>, <a href="http://www.filmpornoita.net/tag/milf/" rel="tag">Milf</a>, <a href="http://www.filmpornoita.net/tag/mom/" rel="tag">mom</a>, <a href="http://www.filmpornoita.net/tag/nude/" rel="tag">nude</a>, <a href="http://www.filmpornoita.net/tag/orgasm/" rel="tag">orgasm</a>, <a href="http://www.filmpornoita.net/tag/real-celebrity-sex/" rel="tag">real celebrity sex</a>, <a href="http://www.filmpornoita.net/tag/roug-sex/" rel="tag">Roug Sex</a>, <a href="http://www.filmpornoita.net/tag/squirt/" rel="tag">squirt</a>, <a href="http://www.filmpornoita.net/tag/suck/" rel="tag">suck</a>, <a href="http://www.filmpornoita.net/tag/teen/" rel="tag">Teen</a>, <a href="http://www.filmpornoita.net/tag/threesome/" rel="tag">Threesome</a>, <a href="http://www.filmpornoita.net/tag/treesome/" rel="tag">Treesome</a>, <a href="http://www.filmpornoita.net/tag/wife-novinwa/" rel="tag">wife.novinwa</a></span>

</div>



<div class="post" id="post-23950">

<a href="http://www.filmpornoita.net/film-ita/tutti-in-cam-che-poi-ce-le-chiaviam-un-bel-pov-di-roba-centoxcento/" title="Tutti in CAM che poi ce le chiaviam! un bel pov di roba &#8211; CentoXCento"><img width="240" height="162" src="http://www.filmpornoita.net/wp-content/uploads/2016/05/Tutti-in-CAM-che-poi-ce-le-chiaviam-un-bel-pov-di-roba-300x202.jpg" class="attachment-240x180 wp-post-image" alt="Tutti in CAM che poi ce le chiaviam! un bel pov di roba &#8211; CentoXCento" title="" /></a>


<div class="link"><a href="http://www.filmpornoita.net/film-ita/tutti-in-cam-che-poi-ce-le-chiaviam-un-bel-pov-di-roba-centoxcento/">Tutti in CAM che poi ce le chiavia...</a></div>

<span>Added: maggio 9, 2016 at 9:46 am</span>

<span>Tags: <a href="http://www.filmpornoita.net/tag/all-sex/" rel="tag">All Sex</a>, <a href="http://www.filmpornoita.net/tag/amateur/" rel="tag">Amateur</a>, <a href="http://www.filmpornoita.net/tag/anal/" rel="tag">Anal</a>, <a href="http://www.filmpornoita.net/tag/cento-x-cento/" rel="tag">Cento X Cento</a>, <a href="http://www.filmpornoita.net/tag/double-penetration/" rel="tag">Double Penetration</a>, <a href="http://www.filmpornoita.net/tag/film-porno-italiani/" rel="tag">Film Porno Italiani</a>, <a href="http://www.filmpornoita.net/tag/group-sex/" rel="tag">Group sex</a>, <a href="http://www.filmpornoita.net/tag/hardcore/" rel="tag">Hardcore</a>, <a href="http://www.filmpornoita.net/tag/italian/" rel="tag">Italian</a>, <a href="http://www.filmpornoita.net/tag/tutti-in-cam-che-poi-ce-le-chiaviam-un-bel-pov-di-roba-centoxcento/" rel="tag">Tutti in CAM che poi ce le chiaviam! un bel pov di roba - CentoXCento</a></span>

</div>



<div class="post" id="post-23947">

<a href="http://www.filmpornoita.net/film-ita/mungimi-signora-centoxcento/" title="Mungimi signora &#8211; CentoXCento"><img width="126" height="180" src="http://www.filmpornoita.net/wp-content/uploads/2016/05/Mungimi-signora-210x300.jpg" class="attachment-240x180 wp-post-image" alt="Mungimi signora &#8211; CentoXCento" title="" /></a>


<div class="link"><a href="http://www.filmpornoita.net/film-ita/mungimi-signora-centoxcento/">Mungimi signora &#8211; CentoXCent...</a></div>

<span>Added: maggio 9, 2016 at 9:45 am</span>

<span>Tags: <a href="http://www.filmpornoita.net/tag/all-sex/" rel="tag">All Sex</a>, <a href="http://www.filmpornoita.net/tag/amateur/" rel="tag">Amateur</a>, <a href="http://www.filmpornoita.net/tag/anal/" rel="tag">Anal</a>, <a href="http://www.filmpornoita.net/tag/cento-x-cento/" rel="tag">Cento X Cento</a>, <a href="http://www.filmpornoita.net/tag/double-penetration/" rel="tag">Double Penetration</a>, <a href="http://www.filmpornoita.net/tag/film-porno-italiani/" rel="tag">Film Porno Italiani</a>, <a href="http://www.filmpornoita.net/tag/group-sex/" rel="tag">Group sex</a>, <a href="http://www.filmpornoita.net/tag/hardcore/" rel="tag">Hardcore</a>, <a href="http://www.filmpornoita.net/tag/italian/" rel="tag">Italian</a>, <a href="http://www.filmpornoita.net/tag/mungimi-signora-centoxcento/" rel="tag">Mungimi signora - CentoXCento</a>, <a href="http://www.filmpornoita.net/tag/oral/" rel="tag">Oral</a></span>

</div>



<div class="post" id="post-23944">
<a href="http://www.filmpornoita.net/film-ita/genovesi-avare-di-cazzi-centoxcento/" title="Genovesi avare di cazzi &#8211; CentoXCento"><img width="126" height="180" src="http://www.filmpornoita.net/wp-content/uploads/2016/05/Genovesi-avare-di-cazzi-210x300.jpg" class="attachment-240x180 wp-post-image" alt="Genovesi avare di cazzi &#8211; CentoXCento" title="" /></a>
<div class="link"><a href="http://www.filmpornoita.net/film-ita/genovesi-avare-di-cazzi-centoxcento/">Genovesi avare di cazzi &#8211; Ce...</a></div>
<span>Added: maggio 9, 2016 at 9:43 am</span>
<span>Tags: <a href="http://www.filmpornoita.net/tag/all-sex/" rel="tag">All Sex</a>, <a href="http://www.filmpornoita.net/tag/amateur/" rel="tag">Amateur</a>, <a href="http://www.filmpornoita.net/tag/anal/" rel="tag">Anal</a>, <a href="http://www.filmpornoita.net/tag/cento-x-cento/" rel="tag">Cento X Cento</a>, <a href="http://www.filmpornoita.net/tag/double-penetration/" rel="tag">Double Penetration</a>, <a href="http://www.filmpornoita.net/tag/film-porno-italiani/" rel="tag">Film Porno Italiani</a>, <a href="http://www.filmpornoita.net/tag/genovesi-avare-di-cazzi-centoxcento/" rel="tag">Genovesi avare di cazzi - CentoXCento</a>, <a href="http://www.filmpornoita.net/tag/hardcore/" rel="tag">Hardcore</a>, <a href="http://www.filmpornoita.net/tag/italian/" rel="tag">Italian</a>, <a href="http://www.filmpornoita.net/tag/oral/" rel="tag">Oral</a>, <a href="http://www.filmpornoita.net/tag/streaming-movies/" rel="tag">Streaming Movies</a></span>
</div>

<div class="post" id="post-23919">
<a href="http://www.filmpornoita.net/film-ita/infermiere-del-cazzo-2-centoxcento/" title="Infermiere del cazzo 2 &#8211; CentoXCento"><img width="240" height="158" src="http://www.filmpornoita.net/wp-content/uploads/2016/05/Infermiere-del-cazzo-2-CentoXCento-300x198.jpg" class="attachment-240x180 wp-post-image" alt="Infermiere del cazzo 2 &#8211; CentoXCento" title="" /></a>
<div class="link"><a href="http://www.filmpornoita.net/film-ita/infermiere-del-cazzo-2-centoxcento/">Infermiere del cazzo 2 &#8211; Cen...</a></div>
<span>Added: maggio 5, 2016 at 9:59 am</span>
<span>Tags: <a href="http://www.filmpornoita.net/tag/all-sex/" rel="tag">All Sex</a>, <a href="http://www.filmpornoita.net/tag/amateur/" rel="tag">Amateur</a>, <a href="http://www.filmpornoita.net/tag/anal/" rel="tag">Anal</a>, <a href="http://www.filmpornoita.net/tag/cento-x-cento/" rel="tag">Cento X Cento</a>, <a href="http://www.filmpornoita.net/tag/double-penetration/" rel="tag">Double Penetration</a>, <a href="http://www.filmpornoita.net/tag/film-porno-italiani/" rel="tag">Film Porno Italiani</a>, <a href="http://www.filmpornoita.net/tag/group-sex/" rel="tag">Group sex</a>, <a href="http://www.filmpornoita.net/tag/hardcore/" rel="tag">Hardcore</a>, <a href="http://www.filmpornoita.net/tag/infermiere-del-cazzo-2-centoxcento/" rel="tag">Infermiere del cazzo 2 - CentoXCento</a>, <a href="http://www.filmpornoita.net/tag/italian/" rel="tag">Italian</a>, <a href="http://www.filmpornoita.net/tag/oral/" rel="tag">Oral</a>, <a href="http://www.filmpornoita.net/tag/streaming-movies/" rel="tag">Streaming Movies</a>, <a href="http://www.filmpornoita.net/tag/teen/" rel="tag">Teen</a>, <a href="http://www.filmpornoita.net/tag/xxx-movies/" rel="tag">XXX Movies</a></span>
</div>
<div class="ficha"(.*?)</div>

    '''
    logger.info("pelisalacarta.filmpornoita peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="post" id="(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

 #  <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>

    for match in matches:
    #<h3 class="entry-title"><a href="http://www.italia-film.co/dottore-la-fica-nel-culo-2015/" rel="bookmark">Dottore, Ho La Fica nel Culo (2015)</a></h3>

        title = scrapertools.find_single_match(match,'title="([^"]+)"')
#        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
#        url = "http://www.tripledeseo.com/"+url
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'src="([^"]+)"')
#        thumbnail = "http://www.tripledeseo.com/"+thumbnail
        # Añade al listado
        itemlist.append( Item(channel=__channel__, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''
    <div class="paginator">
    <span>Page 1 of 214</span><span class="current">1</span>
    <a href='http://www.filmpornoita.net/page/2/' class="inactive">2</a><a href='http://www.filmpornoita.net/page/3/' class="inactive">3</a><a href='http://www.filmpornoita.net/page/4/' class="inactive">4</a><a href='http://www.filmpornoita.net/page/5/' class="inactive">5</a><a href='http://www.filmpornoita.net/page/6/' class="inactive">6</a><a href='http://www.filmpornoita.net/page/7/' class="inactive">7</a><a href='http://www.filmpornoita.net/page/8/' class="inactive">8</a><a href='http://www.filmpornoita.net/page/9/' class="inactive">9</a><a href='http://www.filmpornoita.net/page/10/' class="inactive">10</a>
    <a href="http://www.filmpornoita.net/page/2/">Next &rsaquo;</a><a href='http://www.filmpornoita.net/page/214/'>Last &raquo;</a>
    </div>

    <a href="([^"]+)">Next'


    '''

    # Extrae el paginador
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)">Next')
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=__channel__ , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist




# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    peliculas_items = peliculas(mainlist_items[0])
    bien = False
    for pelicula_item in peliculas_items:
        mirrors = servertools.find_video_items( item=pelicula_item )
        if len(mirrors)>0:
            bien = True
            break

    return bien
