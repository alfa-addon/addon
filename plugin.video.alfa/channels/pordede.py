# -*- coding: utf-8 -*-

import os
import re
import sys
import urlparse

from core import channeltools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

def login():
    url_origen = "http://www.pordede.com"
    data = httptools.downloadpage(url_origen).data
    if config.get_setting("pordedeuser", "pordede") in data:
        return True

    url = "http://www.pordede.com/api/login/auth?response_type=code&client_id=appclient&redirect_uri=http%3A%2F%2Fwww.pordede.com%2Fapi%2Flogin%2Freturn&state=none"
    post = "username=%s&password=%s&authorized=autorizar" % (config.get_setting("pordedeuser", "pordede"), config.get_setting("pordedepassword", "pordede"))
    data = httptools.downloadpage(url, post).data
    if '"ok":true' in data:
        return True
    else:
        return False

def mainlist(item):
    logger.info()

    itemlist = []

    if not config.get_setting("pordedeuser", "pordede"):
       itemlist.append( Item( channel=item.channel , title="Habilita tu cuenta en la configuración..." , action="settingCanal" , url="") )
    else:
       result = login()
       if not result:
          itemlist.append(Item(channel=item.channel, action="mainlist", title="Login fallido. Volver a intentar..."))
          return itemlist
       itemlist.append( Item(channel=item.channel, action="menuseries"    , title="Series"                   , url="" ))
       itemlist.append( Item(channel=item.channel, action="menupeliculas" , title="Películas y documentales" , url="" ))
       itemlist.append( Item(channel=item.channel, action="listas_sigues" , title="Listas que sigues"        , url="http://www.pordede.com/lists/following" ))
       itemlist.append( Item(channel=item.channel, action="tus_listas"    , title="Tus listas"               , url="http://www.pordede.com/lists/yours" ))
       itemlist.append( Item(channel=item.channel, action="listas_sigues" , title="Top listas"               , url="http://www.pordede.com/lists" ))
       itemlist.append( Item(channel=item.channel, action="settingCanal"    , title="Configuración..."     , url="" ))

    return itemlist

def settingCanal(item):
    return platformtools.show_channel_settings()

def menuseries(item):
    logger.info()

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Novedades"            , url="http://www.pordede.com/series/loadmedia/offset/0/showlist/hot" ))
    itemlist.append( Item(channel=item.channel, action="generos"   , title="Por géneros"          , url="http://www.pordede.com/series" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Siguiendo"            , url="http://www.pordede.com/series/following" ))
    itemlist.append( Item(channel=item.channel, action="siguientes" , title="Siguientes Capítulos" , url="http://www.pordede.com/main/index" , viewmode="movie"))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Favoritas"            , url="http://www.pordede.com/series/favorite" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Pendientes"           , url="http://www.pordede.com/series/pending" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Terminadas"           , url="http://www.pordede.com/series/seen" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Recomendadas"         , url="http://www.pordede.com/series/recommended" ))
    itemlist.append( Item(channel=item.channel, action="search"    , title="Buscar..."            , url="http://www.pordede.com/series" ))

    return itemlist

def menupeliculas(item):
    logger.info()

    itemlist = []
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Novedades"            , url="http://www.pordede.com/pelis/loadmedia/offset/0/showlist/hot" ))
    itemlist.append( Item(channel=item.channel, action="generos" , title="Por géneros"            , url="http://www.pordede.com/pelis" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Favoritas"            , url="http://www.pordede.com/pelis/favorite" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Pendientes"           , url="http://www.pordede.com/pelis/pending" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Vistas"               , url="http://www.pordede.com/pelis/seen" ))
    itemlist.append( Item(channel=item.channel, action="peliculas" , title="Recomendadas"         , url="http://www.pordede.com/pelis/recommended" ))
    itemlist.append( Item(channel=item.channel, action="search"  , title="Buscar..."              , url="http://www.pordede.com/pelis" ))

    return itemlist

def generos(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    data = scrapertools.find_single_match(data,'<div class="section genre">(.*?)</div>')
    patron  = '<a class="mediaFilterLink" data-value="([^"]+)" href="([^"]+)">([^<]+)<span class="num">\((\d+)\)</span></a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for textid,scrapedurl,scrapedtitle,cuantos in matches:
        title = scrapedtitle.strip()+" ("+cuantos+")"
        thumbnail = ""
        plot = ""

        if "/pelis" in item.url:
            url = "http://www.pordede.com/pelis/loadmedia/offset/0/genre/"+textid.replace(" ","%20")+"/showlist/all"
        else:
            url = "http://www.pordede.com/series/loadmedia/offset/0/genre/"+textid.replace(" ","%20")+"/showlist/all"

        itemlist.append( Item(channel=item.channel, action="peliculas" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title))

    return itemlist

def search(item,texto):
    logger.info()

    if item.url=="":
       item.url="http://www.pordede.com/pelis"

    texto = texto.replace(" ","-")

    item.extra = item.url
    item.url = item.url+"/loadmedia/offset/0/query/"+texto+"/years/1950/on/undefined/showlist/all"

    try:
       return buscar(item)
    except:
      import sys
      for line in sys.exc_info():
          logger.error("%s" % line)
      return []

def buscar(item):
    logger.info()

    # Descarga la pagina
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data

    # Extrae las entradas (carpetas)
    json_object = jsontools.load(data)
    data = json_object["html"]

    return parse_mixed_results(item,data)

def parse_mixed_results(item,data):
    patron  = '<a class="defaultLink extended" href="([^"]+)"[^<]+'
    patron += '<div class="coverMini     shadow tiptip" title="([^"]+)"[^<]+'
    patron += '<img class="centeredPic.*?src="([^"]+)"'
    patron += '[^<]+<img[^<]+<div class="extra-info">'
    patron += '<span class="year">([^<]+)</span>'
    patron += '<span class="value"><i class="icon-star"></i>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedyear,scrapedvalue in matches:
        title = scrapertools.htmlclean(scrapedtitle)
        if scrapedyear != '':
           title += " ("+scrapedyear+")"
        fulltitle = title
        if scrapedvalue != '':
           title += " ("+scrapedvalue+")"
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        fanart = thumbnail.replace("mediathumb","mediabigcover")
        plot = ""

        if "/peli/" in scrapedurl or "/docu/" in scrapedurl:

            if "/peli/" in scrapedurl:
                sectionStr = "peli" 
            else:
                sectionStr = "docu"

            referer = urlparse.urljoin(item.url,scrapedurl)
            url = referer.replace("/{0}/".format(sectionStr),"/links/view/slug/")+"/what/{0}".format(sectionStr)

            itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , extra=referer, url=url, thumbnail=thumbnail, plot=plot, fulltitle=fulltitle, fanart=fanart,
                                  contentTitle=scrapedtitle, contentType="movie", context=["buscar_trailer"]))
        else:
            referer = item.url
            url = urlparse.urljoin(item.url,scrapedurl)
            itemlist.append( Item(channel=item.channel, action="episodios" , title=title , extra=referer, url=url, thumbnail=thumbnail, plot=plot, fulltitle=fulltitle, show=title, fanart=fanart,
                                  contentTitle=scrapedtitle, contentType="tvshow", context=["buscar_trailer"]))

    next_page = scrapertools.find_single_match(data, '<div class="loadingBar" data-url="([^"]+)"')
    if next_page != "":
       url = urlparse.urljoin("http://www.pordede.com", next_page)
       itemlist.append(
               Item(channel=item.channel, action="lista", title=">> Página siguiente", extra=item.extra, url=url))

    try:
       import xbmcplugin
       xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
       xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    except:
       pass

    return itemlist

def siguientes(item):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas (carpetas)
    bloque = scrapertools.find_single_match(data, '<h2>Siguiendo</h2>(.*?)<div class="box">')
    patron = '<div class="coverMini     shadow tiptip" title="([^"]+)">[^<]+'
    patron += '<img class="centeredPic centeredPicFalse"  onerror="[^"]+"  src="([^"]+)"[^<]+'
    patron += '<img src="/images/loading-mini.gif" class="loader"/>[^<]+'
    patron += '<div class="extra-info"><span class="year">[^<]+'
    patron += '</span><span class="value"><i class="icon-star"></i>[^<]+'
    patron += '</span></div>[^<]+'
    patron += '</div>[^<]+'
    patron += '</a>[^<]+'
    patron += '<a class="userepiinfo defaultLink" href="([^"]+)">(\d+)x(\d+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for scrapedtitle,scrapedthumbnail,scrapedurl,scrapedsession,scrapedepisode in matches:
        title = scrapertools.htmlclean(scrapedtitle)
        session = scrapertools.htmlclean(scrapedsession)
        episode = scrapertools.htmlclean(scrapedepisode)
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        fanart = thumbnail.replace("mediathumb","mediabigcover")
        plot = ""
        title = session + "x" + episode + " - " + title

        referer = urlparse.urljoin(item.url,scrapedurl)
        url = referer

        itemlist.append( Item(channel=item.channel, action="episodio" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title, show=title, fanart=fanart, extra=session+"|"+episode))

    return itemlist

def episodio(item):
    logger.info()
    itemlist = []

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data

    session = str(int(item.extra.split("|")[0]))
    episode = str(int(item.extra.split("|")[1]))
    patrontemporada = '<div class="checkSeason"[^>]+>Temporada '+session+'<div class="right" onclick="controller.checkSeason(.*?)\s+</div></div>'
    matchestemporadas = re.compile(patrontemporada,re.DOTALL).findall(data)

    for bloque_episodios in matchestemporadas:
        # Extrae los episodios
        patron  = '<span class="title defaultPopup" href="([^"]+)"><span class="number">'+episode+' </span>([^<]+)</span>(\s*</div>\s*<span[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></span><div[^>]*><button[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></button><div class="action([^"]*)" data-action="seen">)?'
        matches = re.compile(patron,re.DOTALL).findall(bloque_episodios)

        for scrapedurl,scrapedtitle,info,visto in matches:
            if visto.strip()=="active":
               visto_string = "[visto] "
            else:
               visto_string = ""
            numero=episode
            title = visto_string+session+"x"+numero+" "+scrapertools.htmlclean(scrapedtitle)
            thumbnail = ""
            plot = ""

            epid = scrapertools.find_single_match(scrapedurl,"id/(\d+)")
            url = "http://www.pordede.com/links/viewepisode/id/"+epid
            itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title, fanart=item.fanart, show=item.show))

    itemlist2 = []
    for capitulo in itemlist:
        itemlist2 = findvideos(capitulo)

    return itemlist2

def peliculas(item):
    logger.info()

    # Descarga la pagina
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data

    # Extrae las entradas (carpetas)
    json_object = jsontools.load(data)
    data = json_object["html"]

    return parse_mixed_results(item,data)

def episodios(item):
    logger.info()

    itemlist = []

    # Descarga la pagina
    idserie = ''
    data = httptools.downloadpage(item.url).data

    patrontemporada = '<div class="checkSeason"[^>]+>([^<]+)<div class="right" onclick="controller.checkSeason(.*?)\s+</div></div>'
    matchestemporadas = re.compile(patrontemporada,re.DOTALL).findall(data)

    idserie = scrapertools.find_single_match(data,'<div id="layout4" class="itemProfile modelContainer" data-model="serie" data-id="(\d+)"')

    for nombre_temporada,bloque_episodios in matchestemporadas:
        # Extrae los episodios
        patron  = '<span class="title defaultPopup" href="([^"]+)"><span class="number">([^<]+)</span>([^<]+)</span>(\s*</div>\s*<span[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></span><div[^>]*><button[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></button><div class="action([^"]*)" data-action="seen">)?'
        matches = re.compile(patron,re.DOTALL).findall(bloque_episodios)

        for scrapedurl,numero,scrapedtitle,info,visto in matches:
            if visto.strip()=="active":
               visto_string = "[visto] "
            else:
               visto_string = ""

            title = visto_string+nombre_temporada.replace("Temporada ", "").replace("Extras", "Extras 0")+"x"+numero+" "+scrapertools.htmlclean(scrapedtitle)
            thumbnail = item.thumbnail
            fanart= item.fanart
            plot = ""

            epid = scrapertools.find_single_match(scrapedurl,"id/(\d+)")
            url = "http://www.pordede.com/links/viewepisode/id/"+epid
            itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title, fanart= fanart, show=item.show))

    if config.get_videolibrary_support():
       show = re.sub(r"\s\(\d+\)\s\(\d+\.\d+\)", "", item.show)

       itemlist.append( Item(channel='pordede', title="Añadir esta serie a la biblioteca de XBMC", url=item.url, action="add_serie_to_library", extra="episodios###", show=show) )
       itemlist.append( Item(channel='pordede', title="Descargar todos los episodios de la serie", url=item.url, action="download_all_episodes", extra="episodios", show=show))
       itemlist.append( Item(channel='pordede', title="Marcar como Pendiente", tipo="serie", idtemp=idserie, valor="1", action="pordede_check", show=show))
       itemlist.append( Item(channel='pordede', title="Marcar como Siguiendo", tipo="serie", idtemp=idserie, valor="2", action="pordede_check", show=show))
       itemlist.append( Item(channel='pordede', title="Marcar como Finalizada", tipo="serie", idtemp=idserie, valor="3", action="pordede_check", show=show))
       itemlist.append( Item(channel='pordede', title="Marcar como Favorita", tipo="serie", idtemp=idserie, valor="4", action="pordede_check", show=show))
       itemlist.append( Item(channel='pordede', title="Quitar marca", tipo="serie", idtemp=idserie, valor="0", action="pordede_check", show=show))

    return itemlist

def parse_listas(item, patron):
    logger.info()

    # Descarga la pagina
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data

    # Extrae las entradas (carpetas)
    json_object = jsontools.load(data)
    data = json_object["html"]

    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl,scrapedtitle,scrapeduser,scrapedfichas in matches:
        title = scrapertools.htmlclean(scrapedtitle + ' (' + scrapedfichas + ' fichas, por ' + scrapeduser + ')')
        url = urlparse.urljoin(item.url,scrapedurl) + "/offset/0/loadmedia"
        thumbnail = ""
        itemlist.append( Item(channel=item.channel, action="lista" , title=title , url=url))

    nextpage = scrapertools.find_single_match(data,'data-url="(/lists/loadlists/offset/[^"]+)"')
    if nextpage != '':
       url = urlparse.urljoin(item.url,nextpage)
       itemlist.append( Item(channel=item.channel, action="listas_sigues" , title=">> Página siguiente" , extra=item.extra, url=url))

    try:
       import xbmcplugin
       xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
       xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    except:
       pass

    return itemlist

def listas_sigues(item):
    logger.info()

    patron  = '<div class="clearfix modelContainer" data-model="lista"[^<]+'
    patron += '<span class="title"><span class="name"><a class="defaultLink" href="([^"]+)">([^<]+)</a>'
    patron += '</span>[^<]+<a[^>]+>([^<]+)</a></span>\s+<div[^<]+<div[^<]+</div>\s+<div class="info">\s+<p>([0-9]+)'

    return parse_listas(item, patron)

def tus_listas(item):
    logger.info()

    patron  = '<div class="clearfix modelContainer" data-model="lista"[^<]+'
    patron += '<div class="right"[^<]+'
    patron += '<button[^<]+</button[^<]+'
    patron += '<button[^<]+</button[^<]+'
    patron += '</div[^<]+'
    patron += '<span class="title"><span class="name"><a class="defaultLink" href="([^"]+)">([^<]+)</a>'
    patron += '</span>[^<]+<a[^>]+>([^<]+)</a></span>\s+<div[^<]+<div[^<]+</div>\s+<div class="info">\s+<p>([0-9]+)'

    return parse_listas(item, patron)

def lista(item):
    logger.info()

    # Descarga la pagina
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data

    # Extrae las entradas (carpetas)
    json_object = jsontools.load(data)
    data = json_object["html"]

    return parse_mixed_results(item,data)

def findvideos(item, verTodos=False):
    logger.info()

    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    logger.info(data)

    sesion = scrapertools.find_single_match(data,'SESS = "([^"]+)";')

    patron  = '<a target="_blank" class="a aporteLink(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    idpeli = scrapertools.find_single_match(data,'<div class="buttons"><button class="defaultPopup onlyLogin" href="/links/create/ref_id/(\d+)/ref_model/4">Añadir enlace')

    if (config.get_platform().startswith("xbmc") or config.get_platform().startswith("kodi")) and "/what/peli" in item.url:
        itemlist.append( Item(channel=item.channel, action="infosinopsis" , title="INFO / SINOPSIS" , url=item.url, thumbnail=item.thumbnail, fanart=item.fanart,  folder=False ))

    itemsort = []
    sortlinks = config.get_setting("pordedesortlinks",item.channel)
    showlinks = config.get_setting("pordedeshowlinks",item.channel)

    if sortlinks != '' and sortlinks !="No":
       sortlinks = int(sortlinks)
    else:
       sortlinks = 0

    if showlinks != '' and showlinks !="No":
       showlinks = int(showlinks)
    else:
       showlinks = 0

    for match in matches:
        jdown = scrapertools.find_single_match(match,'<div class="jdownloader">[^<]+</div>')
        if (showlinks == 1 and jdown != '') or (showlinks == 2 and jdown == ''):
            continue

        idiomas = re.compile('<div class="flag([^"]+)">([^<]+)</div>',re.DOTALL).findall(match)
        idioma_0 = (idiomas[0][0].replace("&nbsp;","").strip() + " " + idiomas[0][1].replace("&nbsp;","").strip()).strip()
        if len(idiomas) > 1:
           idioma_1 = (idiomas[1][0].replace("&nbsp;","").strip() + " " + idiomas[1][1].replace("&nbsp;","").strip()).strip()
           idioma = idioma_0 + ", " + idioma_1
        else:
           idioma_1 = ''
           idioma = idioma_0

        calidad_video = scrapertools.find_single_match(match,'<div class="linkInfo quality"><i class="icon-facetime-video"></i>([^<]+)</div>')
        calidad_audio = scrapertools.find_single_match(match,'<div class="linkInfo qualityaudio"><i class="icon-headphones"></i>([^<]+)</div>')

        thumb_servidor = scrapertools.find_single_match(match,'<div class="hostimage"[^<]+<img\s*src="([^"]+)">')
        nombre_servidor = scrapertools.find_single_match(thumb_servidor,"popup_([^\.]+)\.png")

        if jdown != '':
           title = "Download "+nombre_servidor+" ("+idioma+") (Calidad "+calidad_video.strip()+", audio "+calidad_audio.strip()+")"
        else:
           title = "Ver en "+nombre_servidor+" ("+idioma+") (Calidad "+calidad_video.strip()+", audio "+calidad_audio.strip()+")"

        cuenta = []
        valoracion = 0
        for idx, val in enumerate(['1', '2', 'report']):
            nn = scrapertools.find_single_match(match,'<span\s+data-num="([^"]+)"\s+class="defaultPopup"\s+href="/likes/popup/value/'+val+'/')
            if nn != '0' and nn != '':
               cuenta.append(nn + ' ' + ['ok', 'ko', 'rep'][idx])

               if val == '1':
                  valoracion += int(nn)
               else: 
                  valoracion += -int(nn)

        if len(cuenta) > 0:
           title += ' (' + ', '.join(cuenta) + ')'

        url = urlparse.urljoin( item.url , scrapertools.find_single_match(match,'href="([^"]+)"') )
        thumbnail = thumb_servidor
        plot = ""

        if sortlinks > 0:
            if sortlinks == 1:
               orden = valoracion
            elif sortlinks == 2:
               orden = valora_idioma(idioma_0, idioma_1)
            elif sortlinks == 3:
               orden = valora_calidad(calidad_video, calidad_audio)
            elif sortlinks == 4:
               orden = (valora_idioma(idioma_0, idioma_1) * 100) + valora_calidad(calidad_video, calidad_audio)
            elif sortlinks == 5:
               orden = (valora_idioma(idioma_0, idioma_1) * 1000) + valoracion
            elif sortlinks == 6:
               orden = (valora_idioma(idioma_0, idioma_1) * 100000) + (valora_calidad(calidad_video, calidad_audio) * 1000) + valoracion

            itemsort.append({'action': "play", 'title': title, 'url':url, 'thumbnail':thumbnail, 'fanart':item.fanart, 'plot':plot, 'extra':sesion+"|"+item.url, 'fulltitle':item.fulltitle, 'orden1': (jdown == ''), 'orden2':orden})
        else:
            itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, fanart= item.fanart, plot=plot, extra=sesion+"|"+item.url, fulltitle=item.fulltitle))

    if sortlinks > 0:
        numberlinks = config.get_setting("pordedenumberlinks",item.channel)

        if numberlinks != '' and numberlinks !="No":
           numberlinks = int(numberlinks) 
        else:
           numberlinks = 0

        if numberlinks == 0:
           verTodos = True

        itemsort = sorted(itemsort, key=lambda k: (k['orden1'], k['orden2']), reverse=True)
        for i, subitem in enumerate(itemsort):
            if verTodos == False and i >= numberlinks:
               itemlist.append(Item(channel=item.channel, action='findallvideos' , title='Ver todos los enlaces', url=item.url, extra=item.extra ))
               break

            itemlist.append( Item(channel=item.channel, action=subitem['action'] , title=subitem['title'] , url=subitem['url'] , thumbnail=subitem['thumbnail'] , fanart= subitem['fanart'], plot=subitem['plot'] , extra=subitem['extra'] , fulltitle=subitem['fulltitle'] ))
    
    if "/what/peli" in item.url or "/what/docu" in item.url:
	    itemlist.append( Item(channel=item.channel, action="pordede_check" , tipo="peli", title="Marcar como Pendiente" , valor="1", idtemp=idpeli))
	    itemlist.append( Item(channel=item.channel, action="pordede_check" , tipo="peli", title="Marcar como Vista" , valor="3", idtemp=idpeli))
	    itemlist.append( Item(channel=item.channel, action="pordede_check" , tipo="peli", title="Marcar como Favorita" , valor="4", idtemp=idpeli))
	    itemlist.append( Item(channel=item.channel, action="pordede_check" , tipo="peli", title="Quitar Marca" , valor="0", idtemp=idpeli))

    return itemlist

def findallvideos(item):
    return findvideos(item, True)

def play(item):
    # Marcar como visto
    checkseen(item.extra.split("|")[1])

    headers = {'Referer': item.extra.split("|")[1]}

    data = httptools.downloadpage(item.url, post="_s="+item.extra.split("|")[0], headers=headers).data
    url = scrapertools.find_single_match(data,'<p class="nicetry links">\s+<a href="([^"]+)" target="_blank"')
    url = urlparse.urljoin(item.url,url)

    headers = {'Referer': item.url}
    media_url = httptools.downloadpage(url, headers=headers, follow_redirects=False).headers.get("location")

    itemlist = servertools.find_video_items(data=media_url)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel

    return itemlist

def checkseen(item):
    logger.info(item)

    if "/viewepisode/" in item:
        episode = item.split("/")[-1]
        httptools.downloadpage("http://www.pordede.com/ajax/action", post="model=episode&id="+episode+"&action=seen&value=1")

    if "/what/peli" in item:
        data = httptools.downloadpage(item).data

        movieid = scrapertools.find_single_match(data,'href="/links/create/ref_id/([0-9]+)/ref_model/')
        httptools.downloadpage("http://www.pordede.com/ajax/mediaaction", post="model=peli&id="+movieid+"&action=status&value=3")

    return True

def infosinopsis(item):
    logger.info()

    url_aux = item.url.replace("/links/view/slug/", "/peli/").replace("/what/peli", "")
    # Descarga la pagina

    data = httptools.downloadpage(url_aux).data

    scrapedtitle = scrapertools.find_single_match(data,'<h1>([^<]+)</h1>')
    scrapedvalue = scrapertools.find_single_match(data,'<span class="puntuationValue" data-value="([^"]+)"')
    scrapedyear = scrapertools.find_single_match(data,'<h2 class="info">[^<]+</h2>\s*<p class="info">([^<]+)</p>')
    scrapedduration = scrapertools.find_single_match(data,'<h2 class="info">[^<]+</h2>\s*<p class="info">([^<]+)</p>', 1)
    scrapedplot = scrapertools.find_single_match(data,'<div class="info text"[^>]+>([^<]+)</div>')
    scrapedgenres = re.compile('href="/pelis/index/genre/[^"]+">([^<]+)</a>',re.DOTALL).findall(data)
    scrapedcasting = re.compile('href="/star/[^"]+">([^<]+)</a><br/><span>([^<]+)</span>',re.DOTALL).findall(data)

    title = scrapertools.htmlclean(scrapedtitle)
    plot = "Año: [B]"+scrapedyear+"[/B]"
    plot += " , Duración: [B]"+scrapedduration+"[/B]"
    plot += " , Puntuación usuarios: [B]"+scrapedvalue+"[/B]"
    plot += "\nGéneros: "+", ".join(scrapedgenres)
    plot += "\n\nSinopsis:\n"+scrapertools.htmlclean(scrapedplot)
    plot += "\n\nCasting:\n"
    for actor,papel in scrapedcasting:
    	plot += actor+" ("+papel+"). "

    tbd = TextBox("DialogTextViewer.xml", os.getcwd(), "Default")
    tbd.ask(title, plot)

    del tbd
    return

try:
    import xbmcgui

    class TextBox( xbmcgui.WindowXML ):
        """ Create a skinned textbox window """
        def __init__( self, *args, **kwargs):
            pass

        def onInit( self ):
            try:
               self.getControl( 5 ).setText( self.text )
               self.getControl( 1 ).setLabel( self.title )
            except: pass

        def onClick( self, controlId ):
            pass

        def onFocus( self, controlId ):
            pass

        def onAction( self, action ):
            if action == 7:
               self.close()

        def ask(self, title, text ):
            self.title = title
            self.text = text
            self.doModal()
except:
    pass

def valora_calidad(video, audio):
    prefs_video = [ 'hdmicro', 'hd1080', 'hd720', 'hdrip', 'dvdrip', 'rip', 'tc-screener', 'ts-screener' ]
    prefs_audio = [ 'dts', '5.1', 'rip', 'line', 'screener' ]

    video = ''.join(video.split()).lower()
    if video in prefs_video:
       pts = (9 - prefs_video.index(video)) * 10
    else:
       pts = (9 - 1) * 10

    audio = ''.join(audio.split()).lower()
    if audio in prefs_audio:
       pts = (9 - prefs_audio.index(audio)) * 10
    else:
       pts = (9 - 1) * 10

    return pts

def valora_idioma(idioma_0, idioma_1):
    prefs = [ 'spanish', 'spanish LAT', 'catalan', 'english', 'french' ]

    if idioma_0 in prefs:
       pts = (9 - prefs.index(idioma_0)) * 10
    else:
       pts = (9 - 1) * 10

    if idioma_1 != '':
        idioma_1 = idioma_1.replace(' SUB', '')

        if idioma_1 in prefs:
           pts += 8 - prefs.index(idioma_1)
        else:
           pts += 8 - 1

    else:
        pts += 9

    return pts

def pordede_check(item):
    httptools.downloadpage("http://www.pordede.com/ajax/mediaaction", post="model="+item.tipo+"&id="+item.idtemp+"&action=status&value="+item.valor)

