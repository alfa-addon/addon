# -*- coding: utf-8 -*-

import os
import time
import urllib

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import config, logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'file was deleted' in data:
        return False, "[FlashX] El archivo no existe o ha sido borrado"
    elif 'Video is processing now' in data:
        return False, "[FlashX] El archivo se está procesando"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    pfxfx = ""
    headers = {'Host': 'www.flashx.tv',
               'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'en-US,en;q=0.5',
               'Accept-Encoding': 'gzip, deflate, br', 'Connection': 'keep-alive', 'Upgrade-Insecure-Requests': '1',
               'Cookie': ''}
    data = httptools.downloadpage(page_url, headers=headers, replace_headers=True).data
    data = data.replace("\n","")
    cgi_counter = scrapertools.find_single_match(data, '(?s)SRC="(https://www.flashx.tv/counter.cgi\?fx=[^"]+)')
    cgi_counter = cgi_counter.replace("%0A","").replace("%22","")
    playnow = scrapertools.find_single_match(data, 'https://www.flashx.tv/dl[^"]+')
    # Para obtener el f y el fxfx
    js_fxfx = scrapertools.find_single_match(data, 'src="(https://www.flashx.tv/js/code.js.*?cache=[0-9]+)')
    data_fxfx = httptools.downloadpage(js_fxfx).data
    mfxfx = scrapertools.find_single_match(data_fxfx, 'get.*?({.*?})').replace("'","").replace(" ","")
    matches = scrapertools.find_multiple_matches(mfxfx, '(\w+):(\w+)')
    for f, v in matches:
        pfxfx += f + "=" + v + "&"
    coding_url = 'https://www.flashx.tv/flashx.php?%s' %pfxfx
    # {f: 'y', fxfx: '6'}
    flashx_id = scrapertools.find_single_match(data, 'name="id" value="([^"]+)"')
    fname = scrapertools.find_single_match(data, 'name="fname" value="([^"]+)"')
    hash_f = scrapertools.find_single_match(data, 'name="hash" value="([^"]+)"')
    imhuman = scrapertools.find_single_match(data, "value='([^']+)' name='imhuman'")
    post = 'op=download1&usr_login=&id=%s&fname=%s&referer=&hash=%s&imhuman=%s' % (
        flashx_id, urllib.quote(fname), hash_f, imhuman)
    wait_time = scrapertools.find_single_match(data, "<span id='xxc2'>(\d+)")

    headers['Referer'] = "https://www.flashx.tv/"
    headers['Accept'] = "*/*"
    headers['Host'] = "www.flashx.tv"
    headers['X-Requested-With'] = 'XMLHttpRequest'

    # Obligatorio descargar estos 2 archivos, porque si no, muestra error
    httptools.downloadpage(coding_url, headers=headers, replace_headers=True)
    httptools.downloadpage(cgi_counter, headers=headers, replace_headers=True)

    try:
        time.sleep(int(wait_time) + 1)
    except:
        time.sleep(6)

    headers.pop('X-Requested-With')
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    data = httptools.downloadpage(playnow, post, headers, replace_headers=True).data

    # Si salta aviso, se carga la pagina de comprobacion y luego la inicial
    # LICENSE GPL3, de alfa-addon: https://github.com/alfa-addon/ ES OBLIGATORIO AÑADIR ESTAS LÍNEAS
    if "You try to access this video with Kodi" in data:
        url_reload = scrapertools.find_single_match(data, 'try to reload the page.*?href="([^"]+)"')
        try:
            data = httptools.downloadpage(url_reload, cookies=False).data
            data = httptools.downloadpage(playnow, post, headers, replace_headers=True).data
        # LICENSE GPL3, de alfa-addon: https://github.com/alfa-addon/ ES OBLIGATORIO AÑADIR ESTAS LÍNEAS
        except:
            pass
    
    matches = scrapertools.find_multiple_matches(data, "(eval\(function\(p,a,c,k.*?)\s+</script>")
    video_urls = []
    for match in matches:
        try:
            match = jsunpack.unpack(match)
            match = match.replace("\\'", "'")

            # {src:\'https://bigcdn.flashx1.tv/cdn25/5k7xmlcjfuvvjuw5lx6jnu2vt7gw4ab43yvy7gmkvhnocksv44krbtawabta/normal.mp4\',type:\'video/mp4\',label:\'SD\',res:360},
            media_urls = scrapertools.find_multiple_matches(match, "{src:'([^']+)'.*?,label:'([^']+)'")
            subtitle = ""
            for media_url, label in media_urls:
                if media_url.endswith(".srt") and label == "Spanish":
                    try:
                        from core import filetools
                        data = scrapertools.downloadpage(media_url)
                        subtitle = os.path.join(config.get_data_path(), 'sub_flashx.srt')
                        filetools.write(subtitle, data)
                    except:
                        import traceback
                        logger.info("Error al descargar el subtítulo: " + traceback.format_exc())

            for media_url, label in media_urls:
                if not media_url.endswith("png") and not media_url.endswith(".srt"):
                    video_urls.append(["." + media_url.rsplit('.', 1)[1] + " [flashx]", media_url, 0, subtitle])

            for video_url in video_urls:
                logger.info("%s - %s" % (video_url[0], video_url[1]))
        except:
            pass

    return video_urls
