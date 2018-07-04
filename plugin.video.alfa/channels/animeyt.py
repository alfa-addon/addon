# -*- coding: utf-8 -*-

import re
import urlparse

from channels import renumbertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from platformcode import config,logger

import gktools, random, time, urllib

__modo_grafico__ = config.get_setting('modo_grafico', 'animeyt')

HOST = "http://animeyt.tv/"

def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades", url=HOST))

    itemlist.append(Item(channel=item.channel, title="Recientes", action="recientes", url=HOST))
    
    itemlist.append(Item(channel=item.channel, title="Alfabético", action="alfabetico", url=HOST))

    itemlist.append(Item(channel=item.channel, title="Búsqueda", action="search", url=urlparse.urljoin(HOST, "busqueda?terminos=")))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def novedades(item):
    logger.info()
    itemlist = list()
    if not item.pagina:
        item.pagina = 0

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron_novedades = '<div class="capitulos-portada">[\s\S]+?<h2>Comentarios</h2>'

    data_novedades = scrapertools.find_single_match(data, patron_novedades)

    patron = 'href="([^"]+)"[\s\S]+?src="([^"]+)"[^<]+alt="([^"]+) (\d+)([^"]+)'

    matches = scrapertools.find_multiple_matches(data_novedades, patron)
    
    for url, img, scrapedtitle, eps, info in matches[item.pagina:item.pagina + 20]:
        title = scrapedtitle + " " + "1x" + eps + info
        title = title.replace("Sub Español", "").replace("sub español", "")
        infoLabels = {'filtro': {"original_language": "ja"}.items()}
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumb=img, action="findvideos", contentTitle=scrapedtitle, contentSerieName=scrapedtitle, infoLabels=infoLabels, contentType="tvshow"))
    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for it in itemlist:
                it.thumbnail = it.thumb
    except:
        pass
    
    if len(matches) > item.pagina + 20:
        pagina = item.pagina + 20
        itemlist.append(item.clone(channel=item.channel, action="novedades", url=item.url, title=">> Página Siguiente", pagina=pagina))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    
    for letra in '0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        titulo = letra
        if letra == "0":
            letra = "num"
        itemlist.append(Item(channel=item.channel, action="recientes", title=titulo,
                             url=urlparse.urljoin(HOST, "animes?tipo=0&genero=0&anio=0&letra={letra}".format(letra=letra))))


    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ","+")
    item.url = item.url+texto
    if texto!='':
       return recientes(item)


def recientes(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron_recientes = '<article class="anime">[\s\S]+?</main>'

    data_recientes = scrapertools.find_single_match(data, patron_recientes)

    patron = '<a href="([^"]+)"[^<]+<img src="([^"]+)".+?js-synopsis-reduce">(.*?)<.*?<h3 class="anime__title">(.*?)<small>(.*?)</small>'

    matches = scrapertools.find_multiple_matches(data_recientes, patron)

    for url, thumbnail, plot, title, cat in matches:
        itemlist.append(item.clone(title=title, url=url, action="episodios", show=title, thumbnail=thumbnail, plot=plot, cat=cat, context=renumbertools.context(item)))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    paginacion = scrapertools.find_single_match(data, '<a class="pager__link icon-derecha last" href="([^"]+)"')
    paginacion = scrapertools.decodeHtmlentities(paginacion)

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="recientes", title=">> Página Siguiente", url=paginacion))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
  
    patron = '<span class="icon-triangulo-derecha"></span>.*?<a href="([^"]+)">([^"]+) (\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, scrapedtitle, episode in matches:
        
        season = 1
        episode = int(episode)
        season, episode = renumbertools.numbered_for_tratk(item.channel, scrapedtitle, season, episode)
        title = "%sx%s %s" % (season, str(episode).zfill(2), scrapedtitle)
        itemlist.append(item.clone(title=title, url=url, action='findvideos'))
        
    if config.get_videolibrary_support:
        itemlist.append(Item(channel=item.channel, title="Añadir serie a la biblioteca", url=item.url, action="add_serie_to_library", extra="episodios", show=item.show))
        
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    duplicados = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    from collections import OrderedDict # cambiado dict por OrderedDict para mantener el mismo orden que en la web

    matches = scrapertools.find_multiple_matches(data, '<li><a id="mirror(\d*)" class="link-veranime[^"]*" href="[^"]*">([^<]*)')
    d_links = OrderedDict(matches)

    matches = scrapertools.find_multiple_matches(data, 'if \(mirror == (\d*)\).*?iframe src="([^"]*)"')
    d_frames = OrderedDict(matches)

    for k in d_links:
        if k in d_frames and d_frames[k] != '':
            tit = scrapertools.find_single_match(d_frames[k], '/([^\./]*)\.php\?')
            if tit == '':
                tit = 'mega' if 'mega.nz/' in d_frames[k] else 'dailymotion' if 'dailymotion.com/' in d_frames[k] else'noname'
            if tit == 'id' and 'yourupload.com/' in d_frames[k]: tit = 'yourupload'
            title = 'Opción %s (%s)' % (d_links[k], tit)
            
            itemlist.append(item.clone(channel=item.channel, folder=False, title=title, action="play", url=d_frames[k], referer=item.url))


    if item.extra != "library":
        if config.get_videolibrary_support() and item.extra:
            itemlist.append(item.clone(channel=item.channel, title="[COLOR yellow]Añadir pelicula a la videoteca[/COLOR]", url=item.url, action="add_pelicula_to_library", extra="library", contentTitle=item.show, contentType="movie"))

    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    if item.url.startswith('https://www.dailymotion.com/'):
        itemlist.append(item.clone(url=item.url, server='dailymotion'))

    elif item.url.startswith('https://mega.nz/'):
        itemlist.append(item.clone(url=item.url.replace('embed',''), server='mega'))

    elif item.url.startswith('https://s2.animeyt.tv/rakuten.php?'):
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="google-site-verification" content="([^"]*)"')
        if not gsv: return itemlist

        suto = gktools.md5_dominio(item.url)
        sufijo = '3497510'

        token = gktools.generar_token('"'+gsv+'"', suto+'yt'+suto+sufijo)

        link, subtitle = gktools.get_play_link_id(data, item.url)
        
        url = 'https://s2.animeyt.tv/rakuten/plugins/gkpluginsphp.php'
        post = "link=%s&token=%s" % (link, token)

        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer, subtitle)


    elif item.url.startswith('https://s3.animeyt.tv/amz.php?'):
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        v_token = scrapertools.find_single_match(data, "var v_token='([^']*)'")
        if not gsv or not v_token: return itemlist

        suto = gktools.md5_dominio(item.url)
        sufijo = '9457610'

        token = gktools.generar_token('"'+gsv+'"', suto+'yt'+suto+sufijo)

        url = 'https://s3.animeyt.tv/amz_animeyts.php'
        post = "v_token=%s&token=%s&handler=%s" % (v_token, token, 'Animeyt')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s2.animeyt.tv/lola.php?'):
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_cd, s_file = scrapertools.find_single_match(data, "var cd='([^']*)';\s*var file='([^']*)'")
        if not gsv or not s_cd or not s_file: return itemlist

        suto = gktools.md5_dominio(item.url)
        sufijo = '8134976'

        token = gktools.generar_token('"'+gsv+'"', suto+'yt'+suto+sufijo)

        url = 'https://s2.animeyt.tv/minha_animeyt.php'
        post = "cd=%s&file=%s&token=%s&handler=%s" % (s_cd, s_file, token, 'Animeyt')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s4.animeyt.tv/chumi.php?'): #https://s4.animeyt.tv/chumi.php?cd=3481&file=4
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_cd, s_file = scrapertools.find_single_match(item.url, '\?cd=([^&]*)&file=([^&]*)')
        if not gsv or not s_cd or not s_file: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '147268278' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s4.animeyt.tv/minha/minha_animeyt.php'
        post = "cd=%s&id=%s&archive=%s&ip=%s&Japan=%s" % (s_cd, s_file, archive, ip, 'Asia')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s3.animeyt.tv/mega.php?'): #https://s3.animeyt.tv/mega.php?v=WmpHMEVLVTNZZktyaVAwai9sYzhWV1ZRTWh0WTZlNGZ3VzFVTXhMTkx2NGlOMjRYUHhZQlMvaUFsQlJFbHBVTA==
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_v = scrapertools.find_single_match(item.url, '\?v=([^&]*)')
        if not gsv or not s_v: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '147268278' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s3.animeyt.tv/mega_animeyts.php'
        post = "v=%s&archive=%s&referer=%s&ip=%s&Japan=%s" % (s_v, archive, item.url, ip, 'Asia')

        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s2.animeyt.tv/naruto/naruto.php?'): #https://s2.animeyt.tv/naruto/naruto.php?id=3477&file=11.mp4
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_id, s_file = scrapertools.find_single_match(item.url, '\?id=([^&]*)&file=([^&]*)')
        if not gsv or not s_id or not s_file: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '147268278' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s2.animeyt.tv/naruto/narutos_animeyt.php'
        post = "id=%s&file=%s&archive=%s&referer=%s&ip=%s&Japan=%s" % (s_id, s_file, archive, urllib.quote(item.url), ip, 'Asia')

        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s4.animeyt.tv/facebook.php?'): #https://s4.animeyt.tv/facebook.php?cd=3481&id=4
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_cd, s_id = scrapertools.find_single_match(item.url, '\?cd=([^&]*)&id=([^&]*)')
        if not gsv or not s_cd or not s_id: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '147268278' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s4.animeyt.tv/facebook/facebook_animeyts.php'
        post = "cd=%s&id=%s&archive=%s&referer=%s&ip=%s&Japan=%s" % (s_cd, s_id, archive, urllib.quote(item.url), ip, 'Asia')

        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s.animeyt.tv/v4/media.php?'): #https://s.animeyt.tv/v4/media.php?id=SmdMQ2Y0NUhFK2hOZlYzbVJCbnE3QT09
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_id = scrapertools.find_single_match(item.url, '\?id=([^&]*)')
        if not gsv or not s_id: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '8049762' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s.animeyt.tv/v4/gsuite_animeyts.php'
        post = "id=%s&archive=%s&ip=%s&Japan=%s" % (s_id, archive, ip, 'Asia')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s10.animeyt.tv/yourupload.com/id.php?'): #https://s10.animeyt.tv/yourupload.com/id.php?id=62796D77774A4E4363326642
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_id = scrapertools.find_single_match(item.url, '\?id=([^&]*)')
        if not gsv or not s_id: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '8049762' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s10.animeyt.tv/yourupload.com/chinese_streaming.php'
        post = "id=%s&archive=%s&ip=%s&Japan=%s" % (s_id, archive, ip, 'Asia')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    elif item.url.startswith('https://s4.animeyt.tv/onedrive.php?'): #https://s4.animeyt.tv/onedrive.php?cd=3439&id=12
        # 1- Descargar
        data, ck = gktools.get_data_and_cookie(item)

        # 2- Calcular datos
        gsv = scrapertools.find_single_match(data, '<meta name="Animeyt-Token" content="([^"]*)"')
        s_cd, s_id = scrapertools.find_single_match(item.url, '\?cd=([^&]*)&id=([^&]*)')
        if not gsv or not s_cd or not s_id: return itemlist
        
        ip = gktools.toHex(gsv) + str(1000000 + random.randint(0,9000000)) + str(100000 + random.randint(0,900000))
        
        gsv_bis = gktools.transforma_gsv(gsv, '159753')
        p1 = '1705f5652bb6546ab3643ff698e' + gsv[-5:]
        p2 = '8388ca3fd07' + gsv[-5:] + gsv_bis
        
        texto = gktools.toHex(gktools.encode_rijndael(gsv, p1, p2))

        suto = gktools.md5_dominio(item.url)
        sufijo = '147268278' + gsv[-5:]
        prefijo = gsv[:-5] + gsv_bis

        token = gktools.generar_token('"'+texto+'"', prefijo+suto+'yt'+suto+sufijo)
        archive = gktools.toHex(token)

        url = 'https://s4.animeyt.tv/onedrive/onedrive_animeyts.php'
        post = "cd=%s&id=%s&archive=%s&ip=%s&Japan=%s" % (s_cd, s_id, archive, ip, 'Asia')
        
        # 3- Descargar json
        data = gktools.get_data_json(url, post, ck, item.url)

        # 4- Extraer enlaces
        itemlist = gktools.extraer_enlaces_json(data, item.referer)


    return itemlist
