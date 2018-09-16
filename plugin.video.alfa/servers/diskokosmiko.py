# -*- coding: utf-8 -*-

from channels import kbagi
from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    domain = "diskokosmiko.mx"
    logueado, error_message = diskokosmiko.login(domain)
    if not logueado:
        return False, error_message

    data = httptools.downloadpage(page_url).data
    if ("File was deleted" or "Not Found" or "File was locked by administrator") in data:
        return False, "[%s] El archivo no existe o ha sido borrado" %domain

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = []
    data = httptools.downloadpage(page_url).data
    host = "http://diskokosmiko.mx"
    host_string = "diskokosmiko"

    url = scrapertools.find_single_match(data, '<form action="([^"]+)" class="download_form"')
    if url:
        url = host + url
        fileid = url.rsplit("f=", 1)[1]
        token = scrapertools.find_single_match(data,
                                               '<div class="download_container">.*?name="__RequestVerificationToken".*?value="([^"]+)"')
        post = "fileId=%s&__RequestVerificationToken=%s" % (fileid, token)
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        data = httptools.downloadpage(url, post, headers).data
        data = jsontools.load(data)
        mediaurl = data.get("DownloadUrl")
        extension = data.get("Extension")

        video_urls.append([".%s [%s]" % (extension, host_string), mediaurl])

    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0], video_url[1]))

    return video_urls
