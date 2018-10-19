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


## italiafilm
__channel__ = "coomelonitas"
__category__ = "F"
__type__ = "generic"
__title__ = "Coomelonitas"
__language__ = "ES"



host ='http://www.coomelonitas.com/'

def isGeneric():
    return True

def mainlist(item):
    logger.info("pelisalacarta.coomelonitas mainlist")
    itemlist = []
    itemlist.append( Item(channel=__channel__, title="Peliculas" , action="peliculas", url=host))
#    itemlist.append( Item(channel=__channel__, title="Ultimas Peliculas" , action="peliculas", url="http://www.pordede.tv/"))
    itemlist.append( Item(channel=__channel__, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=__channel__, title="Buscar", action="search"))
    return itemlist



def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
    texto = texto.replace(" ", "+")
    item.url = host+ "/?s=%s" % texto

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
        data = scrapertools.get_match(data,'<a href="#">CATEGORÍAS</a>(.*?)</ul>')

        '''
<li id="menu-item-22187" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-has-children menu-item-22187"><a href="#">CATEGORÍAS</a>
<ul class="sub-menu">
<li id="menu-item-22189" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22189"><a href="http://www.coomelonitas.com/Categoria/asiaticas">ASIÁTICAS</a></li>
<li id="menu-item-22190" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22190"><a href="http://www.coomelonitas.com/Categoria/espanol">ESPAÑOL</a></li>
<li id="menu-item-22191" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22191"><a href="http://www.coomelonitas.com/Categoria/estrenos">ESTRENOS</a></li>
<li id="menu-item-22192" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22192"><a href="http://www.coomelonitas.com/Categoria/hentai">HENTAI</a></li>
<li id="menu-item-22193" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22193"><a href="http://www.coomelonitas.com/Categoria/incesto">INCESTO</a></li>
<li id="menu-item-22194" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22194"><a href="http://www.coomelonitas.com/Categoria/ingles">INGLES</a></li>
<li id="menu-item-22195" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22195"><a href="http://www.coomelonitas.com/Categoria/latino">LATINO</a></li>
<li id="menu-item-22196" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22196"><a href="http://www.coomelonitas.com/Categoria/parodia">PARODIA</a></li>
<li id="menu-item-22197" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22197"><a href="http://www.coomelonitas.com/Categoria/peliculas-2013">PELÍCULAS 2013</a></li>
<li id="menu-item-22198" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22198"><a href="http://www.coomelonitas.com/Categoria/peliculas-2014">PELÍCULAS 2014</a></li>
<li id="menu-item-22199" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22199"><a href="http://www.coomelonitas.com/Categoria/peliculas-2015">PELÍCULAS 2015</a></li>
<li id="menu-item-22200" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22200"><a href="http://www.coomelonitas.com/Categoria/peliculas-2016">PELÍCULAS 2016</a></li>
<li id="menu-item-36777" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-36777"><a href="http://www.coomelonitas.com/Categoria/peliculas-2017">PELÍCULAS 2017</a></li>
<li id="menu-item-22201" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22201"><a href="http://www.coomelonitas.com/Categoria/peliculas-en-hd">PELÍCULAS EN HD</a></li>
<li id="menu-item-22202" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-22202"><a href="http://www.coomelonitas.com/Categoria/ruso">RUSO</a></li>
<li id="menu-item-36776" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-36776"><a href="http://www.coomelonitas.com/Categoria/peliculas-italianas">PELÍCULAS ITALIANAS</a></li>
</ul>
</li>
<li id="menu-item-36773" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-36773"><a href="http://www.coomelonitas.com/Categoria/peliculas-2017">PELÍCULAS 2017</a></li>
</ul>


        <li><a title="Teens Movies" href="http://pandamovie.net/adult/watch-teens-porn-movies-online-free">Teens</a></li>


        <li><a title=[^>]+href="([^"]+)">([^<]+)

        '''
        # Extrae las entradas (carpetas)
        patron  = '<li id="menu-item-[^>]+><a href="([^"]+)">([^<]+)</a></li>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        scrapertools.printMatches(matches)

        for scrapedurl,scrapedtitle in matches:
            scrapedplot = ""
            scrapedthumbnail = ""

            itemlist.append( Item(channel=__channel__, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

        return itemlist






def peliculas(item):
    '''
 <div id="contenido">
 <h1 class="p"><i class="fa fa-video-camera"></i> Últimas películas</h1>
    <div class="post">
        <div class="all">
            <a href="http://www.coomelonitas.com/ver-fogosas-y-tetudas-2008-espanol-pelicula-porno-online.html" title="Fogosas Y Tetudas 2008 Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Fogosas-Y-Tetudas-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>
        </div>
        <div class="sX">
            <h2 class="tp2"><a href="http://www.coomelonitas.com/ver-fogosas-y-tetudas-2008-espanol-pelicula-porno-online.html" title="Fogosas Y Tetudas 2008 Español">Fogosas Y Tetudas 2008 Español</a></h2>
            <div class="meta">
                <span><i class="fa fa-line-chart"></i> 8 veces
            </div>
        </div>
    </div>
    <div class="post">
        <div class="all">
        <a href="http://www.coomelonitas.com/ver-sex-machina-a-xxx-parody-2016-pelicula-porno-online.html" title="Sex Machina: A XXX Parody 2016"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Sex-Machina-A-XXX-Parody-2016.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>
        <div class="sX">
            <h2 class="tp2"><a href="http://www.coomelonitas.com/ver-sex-machina-a-xxx-parody-2016-pelicula-porno-online.html" title="Sex Machina: A XXX Parody 2016">Sex Machina: A XXX Parody 2016</a></h2>
            <div class="meta">
            <span><i class="fa fa-line-chart"></i> 7 veces       </div>
            </div>
    </div>
    <div class="post">

   <div class="all">
   <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español">
   <img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" />
   <span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span>
   </a>
   </div>


   <div class="sX">
    <h2 class="tp2"><a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español">Abuso De Poder Español</a></h2>
    <div class="meta">
   <span><i class="fa fa-line-chart"></i> 12 veces       </div>
   </div>
       </div>

<div class="post">
<div class="all">
<a href="http://www.coomelonitas.com/ver-sexo-desenfrenado-pelicula-porno-online.html" title="Sexo desenfrenado XXX"><img src="http://www.coomelonitas.com/wp-content/uploads/2017/10/Sexo-desenfrenado-XXX.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a> </div>
<div class="sX">
<h2 class="tp2"><a href="http://www.coomelonitas.com/ver-sexo-desenfrenado-pelicula-porno-online.html" title="Sexo desenfrenado XXX">Sexo desenfrenado XXX</a></h2>
<div class="meta">
<span><i class="fa fa-line-chart"></i> 74 veces </div>
</div>
</div>


    '''
    logger.info("pelisalacarta.coomelonitas peliculas")
    itemlist = []
    data = scrapertools.cachePage(item.url)
    patron  = '<div class="all"(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

 #  <a href="http://www.coomelonitas.com/ver-abuso-de-poder-espanol-pelicula-porno-online.html" title="Abuso De Poder Español"><img src="http://www.coomelonitas.com/wp-content/uploads/2016/05/Abuso-De-Poder-Español.jpg" alt="" /><span class="hoverPlay"><i class="fa fa-play-circle-o"></i></span></a>       </div>

    for match in matches:
    #<h3 class="entry-title"><a href="http://www.italia-film.co/dottore-la-fica-nel-culo-2015/" rel="bookmark">Dottore, Ho La Fica nel Culo (2015)</a></h3>

        title = scrapertools.find_single_match(match,'title="([^"]+)"')
#        title = scrapertools.htmlclean(title).strip()
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
        plot = scrapertools.find_single_match(match,'<p class="summary">(.*?)</p>')
#        plot = scrapertools.htmlclean(plot).strip()
        thumbnail = scrapertools.find_single_match(match,'<img src="([^"]+)"')

        itemlist.append( Item(channel=__channel__, action="findvideos", title=title , fulltitle=title, url=url , thumbnail=thumbnail , plot=plot , viewmode="movie", folder=True) )

    '''
	<div class="paginador">
        <span class="titulo"></span><span class="est">1</span>
        <a href="http://www.coomelonitas.com/page/2" class="paginas" title="Página 2">2</a><a href="http://www.coomelonitas.com/page/3" class="paginas" title="Página 3">3</a><a href="http://www.coomelonitas.com/page/4" class="paginas" title="Página 4">4</a><a href="http://www.coomelonitas.com/page/5" class="paginas" title="Página 5">5</a><a href="http://www.coomelonitas.com/page/6" class="paginas" title="Página 6">6</a><a href="http://www.coomelonitas.com/page/7" class="paginas" title="Página 7">7</a><span class="mas">...</span><a href="http://www.coomelonitas.com/page/159" class="paginas" title="Página 159">159</a>
        <a href="http://www.coomelonitas.com/page/2" class="siguiente">&raquo;</a>
    </div>


        <a href="([^"]+)" class="siguiente">

    '''

    # Extrae el paginador
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)" class="siguiente">')
    if next_page_url!="":
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
