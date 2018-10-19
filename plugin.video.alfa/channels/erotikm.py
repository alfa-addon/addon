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
__channel__ = "erotikm"
__category__ = "F"
__type__ = "generic"
__title__ = "Erotikm"
__language__ = "ES"




def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.erotikm mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="New" , action="peliculas", url="http://www.ero-tik.com/newvideos.html"))
    itemlist.append( Item(channel=__channel__, title="Popular" , action="peliculas", url="http://www.ero-tik.com/topvideos.html"))

    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url="http://www.ero-tik.com/"))
    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = "http://www.ero-tik.com/search.php?keywords=%s" % texto

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
        <li class=""><a href="http://www.ero-tik.com/browse-bangbross-videos-1-date.html" class="">Bang Bross</a></li>

        <li class=""><a href="http://www.ero-tik.com/browse-bangbross-videos-1-date.html" class="">Bang Bross</a></li>
<li class=""><a href="http://www.ero-tik.com/browse-brazzers-videos-1-date.html" class="">Brazzers</a></li>
<li class=""><a href="http://www.ero-tik.com/browse-reality-kings-videos-1-date.html" class="">Reality Kings</a></li>


        '''
        # Extrae las entradas (carpetas)
        patron  = '<li class=""><a href="([^"]+)" class="">([^<]+)'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""
            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist


def peliculas(item):
    '''
	<div class="pm-li-video">
        <span class="pm-video-thumb pm-thumb-145 pm-thumb border-radius2">
        <span class="pm-video-li-thumb-info">
                                <span class="label label-new">New</span>
					<span class="label label-pop">Popular</span>												</span>
        <a href="http://www.ero-tik.com/luck-be-a-lady_812846094.html" class="pm-thumb-fix pm-thumb-145"><span class="pm-thumb-fix-clip">
        <img src="http://www.ero-tik.com/uploads/thumbs/812846094-1.jpg" alt="Luck be a lady" width="145"><span class="vertical-align"></span></span></a>
        </span>
        <h3><a href="http://www.ero-tik.com/luck-be-a-lady_812846094.html" class="pm-title-link" title="Luck be a lady">Luck be a lady</a></h3>
        <div class="pm-video-attr">
            <span class="pm-video-attr-author">by <a href="http://www.ero-tik.com/user/admin/">Admin</a></span>
            <span class="pm-video-attr-since"><small>Added <time datetime="2016-05-21T07:42:17+0000" title="Saturday, May 21, 2016 7:42 AM">1 day ago</time></small></span>
            <span class="pm-video-attr-numbers"><small>149 Views / 0 Likes</small></span>
        </div>
        <p class="pm-video-attr-desc">Hanging out with Brianna this week we stumbled on a cute Asian milf that was lost and looking for an address. Turns out she was looking for a club Brianna was very familiar with, the local swingers club. We went and chatted with her beach side where she r</p>
    </div>

            <div class="pm-li-video"(.*?)</h3>
            alt="([^"]+)"
            <a href="([^"]+)"
            <img src="([^"]+)"

    				<div class="pm-li-video1">
				    <span class="pm-video-thumb pm-thumb-350 pm-thumb border-radius2">
				    <span class="pm-video-li-thumb-info">
                    										                    				    </span>
				    <a href="http://www.ero-tik.com/depositing-a-giant-load_93cc20083.html" class="pm-thumb-fix pm-thumb-350"><span class="pm-thumb-fix-clip"><img src="http://www.ero-tik.com/uploads/thumbs/93cc20083-1.jpg" alt="Depositing A Giant Load" width="340"><span class="vertical-align"></span></span></a>
				    </span>

				    <h3><a href="http://www.ero-tik.com/depositing-a-giant-load_93cc20083.html" class="pm-title-link " title="Depositing A Giant Load">Depositing A Giant Load</a></h3>
				    <div class="pm-video-attr">
				        <span class="pm-video-attr-author">por <a href="http://www.ero-tik.com/profile.html?u=admin">Admin</a></span>
				        <span class="pm-video-attr-since"><small>Agregado <time datetime="2016-12-09T15:52:04+0100" title="Friday, December 9, 2016 3:52 PM">20 horas hace</time></small></span>
				        <span class="pm-video-attr-numbers"><small>253 Vistas / 0 Likes</small></span>
					</div>
				    <p class="pm-video-attr-desc">This week we met up with this hot chick named Vickie. She works at a bank but is interested in the porn business. She was only able to shoot in her lunch break, so we scooped her up at her branch and headed over to the set. We slowly had her show us the g</p>

									</div>
    '''
    logger.info("pelisalacarta.erotikm peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="pm-li-video(.*?)</h3>'
    matches = re.compile(patron,re.DOTALL).findall(data)

 #  <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>

    for match in matches:
    #<h3 class="entry-title"><a href="http://www.italia-film.co/dottore-la-fica-nel-culo-2015/" rel="bookmark">Dottore, Ho La Fica nel Culo (2015)</a></h3>

        title = scrapertools.find_single_match(match,' alt="([^"]+)"')
#        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
#        url = "http://www.tripledeseo.com/"+url
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'<img src="([^"]+)"')
#        thumbnail = "http://www.tripledeseo.com/"+thumbnail

    
        # Añade al listado
        itemlist.append( Item(channel=__channel__, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''
<div class="clearfix"></div>
						<div class="pagination pagination-centered">
              <ul>
                					<li class="disabled">
						<a href="#" onclick="return false;">&laquo;</a>
					</li>
									<li class="active">
						<a href="#" onclick="return false;">1</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-2-date.html">2</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-3-date.html">3</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-4-date.html">4</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-5-date.html">5</a>
					</li>
									<li class="disabled">
						<a href="#" onclick="return false;">...</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-47-date.html">47</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-48-date.html">48</a>
					</li>
									<li class="">
						<a href="http://www.ero-tik.com/browse-bangbross-videos-2-date.html">&raquo;</a>
					</li>
				              </ul>
            </div>

  <li class=""><a href="([^"]+)">&raquo;


    '''

    # Extrae el paginador
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)">&raquo')
#    next_page_url = "http://www.tripledeseo.com/"+next_page_url
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
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
