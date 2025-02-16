# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger

# download
# {"src":"https://videos.porndig.com/download/index/541306/1035/a265d7632635b213bba299ff18b8d372/6",
# "label":"270p","size":"31 MB"}
# "codec":"av1"
# {"src":"https://ahhttp-av1.porndig.com/key=ShFYYMaBZtWeT6unFwfMDA,end=1739279511/videos/2025/01/clips/541306_22_av1.mp4",
# "type":"video/mp4","label":"2160p","active":false}
# {"src":"https://video-cdn.porndig.com/videos/423590_yxFEMIsPC9yl9TB/mGxDfCJA1zfDqByBt7q-JA/1739283316/qid3855v1_av1_225_360.mp4",
# "type":"video/mp4; codecs=\"av01.0.05M.08\"","label":"360p","active":false}# 
# "codec":"h264"
# {"src":"https://ahhttp-h264.porndig.com/key=Uc3PXiNtQGGXE+ba9z0Mbg,end=1739279511/videos/2025/01/clips/541306_22.mp4",
# "type":"video/mp4; codecs=\"avc1.4d4015\"","label":"2160p"}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    data = data.replace("\/", "/")
    if "<h2>WE ARE SORRY</h2>" in data or 'Not Found' in data or 'Invalid profile' in data:
        return False, "[porndig] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    datos = scrapertools.find_single_match(data, '"codec":"av1","srcSet":\[([^\]]+)')
    patron = '\{"src":"([^"]+)",.*?,"label":"([0-9]+p)"'
    matches = scrapertools.find_multiple_matches(datos, patron)
    for url,quality in matches:
        video_urls.append(["[porndig] %s" % quality, url])
    return video_urls[::-1]

