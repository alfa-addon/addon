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


## italiafilm
__channel__ = "webpeliculasporno"
__category__ = "F"
__type__ = "generic"
__title__ = "WebPeliculasPorno"
__language__ = "ES"


def mainlist(item):
    logger.info("pelisalacarta.webpeliculasporno mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="Peliculas" , action="peliculas", url="http://www.webpeliculasporno.com/"))
#    itemlist.append( Item(channel=__channel__, title="Ultimas Peliculas" , action="peliculas", url="http://www.pordede.tv/"))
    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://www.webpeliculasporno.com/"))
    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist



def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = "http://www.webpeliculasporno.com/?s=%s" % texto

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


        '''


            <li class="cat-item cat-item-30"><a href="http://www.webpeliculasporno.com/Categoria/ingles" >INGLES</a>
            <li class="cat-item [^>]+><a href="([^"]+)" >([^<]+)

        	<li id="menu-item-22189" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22189"><a href="http://www.coomelonitas.com/Categoria/asiaticas">ASIÁTICAS</a></li>
            <li id="menu-item-[^>]+><a href="([^"]+)">([^<]+)

            <li><a title="Teens Movies" href="http://pandamovie.net/adult/watch-teens-porn-movies-online-free">Teens</a></li>
            <li><a title=[^>]+href="([^"]+)">([^<]+)
        '''
        # Extrae las entradas (carpetas)
        patron  = '<li class="cat-item [^>]+><a href="([^"]+)" >([^<]+)'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""

            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist






def peliculas(item):
    '''
<ul class="listing-videos listing-tube">
<li class="border-radius-5 box-shadow">
    <img width="180" height="257" src="http://www.webpeliculasporno.com/wp-content/uploads/2016/05/Watching-My-Mommy-Go-Black-14-2016.jpg" class="attachment-full size-full wp-post-image" alt="Watching My Mommy Go Black # 14 (2016)" title="Watching My Mommy Go Black # 14 (2016)" />
    <a href="http://www.webpeliculasporno.com/watching-my-mommy-go-black-14-2016.html" title="Watching My Mommy Go Black # 14 (2016)"><span>Watching My Mommy Go Black # 14 (2016)</span></a>
            <div class="listing-infos">
            <!-- Time -->                <!-- Views -->
                <div class="views-infos">69 <span class="views-img"></span></div>
                    <div class="time-infos"> - <span class="time-img"></span></div>
                <!-- Rating -->
                    <div class="rating-infos">100%<span class="rating-img"></span></div>
            </div><!-- .listing-infos -->
</li>

     <li class="border-radius-5 box-shadow"(.*?)</span></a>
     title="([^"]+)"
     <a href="([^"]+)"
      src="([^"]+)"


     <div class="ficha">
     <div class="imagen"><a href="ficha/116048/vis-ma-vie-de-libertin"><img src="fichas_img/116048.jpg" title="Vis Ma Vie De Libertin" alt="Vis Ma Vie De Libertin"/></a></div>
     <div class="ficha"(.*?)</div>
     title="([^"]+)"
     <a href="([^"]+)"
     <img src="([^"]+)"
    '''
    logger.info("pelisalacarta.webpeliculasporno peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<li class="border-radius-5 box-shadow"(.*?)</span></a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

 #  <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>

    for match in matches:
    #<h3 class="entry-title"><a href="http://www.italia-film.co/dottore-la-fica-nel-culo-2015/" rel="bookmark">Dottore, Ho La Fica nel Culo (2015)</a></h3>

        title = scrapertools.find_single_match(match,' title="([^"]+)"')
#        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
#        url = "http://www.tripledeseo.com/"+url
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,' src="([^"]+)"')
#        thumbnail = "http://www.tripledeseo.com/"+thumbnail

        itemlist.append( Item(channel=__channel__, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''
      <div class="pagination"><ul class='page-numbers'>
<li><span class='page-numbers current'>1</span></li>
<li><a class='page-numbers' href='http://www.webpeliculasporno.com/page/2'>2</a></li>
<li><a class='page-numbers' href='http://www.webpeliculasporno.com/page/3'>3</a></li>
<li><span class="page-numbers dots">&hellip;</span></li>
<li><a class='page-numbers' href='http://www.webpeliculasporno.com/page/117'>117</a></li>
<li><a class="next page-numbers" href="http://www.webpeliculasporno.com/page/2">Next videos &raquo;</a></li>
</ul>
</div><!-- .pagination -->


    '''

    # Extrae el paginador
    next_page_url = scrapertools.find_single_match(data,'<li><a class="next page-numbers" href="([^"]+)">Next')
#    next_page_url = "http://www.tripledeseo.com/"+next_page_url
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
