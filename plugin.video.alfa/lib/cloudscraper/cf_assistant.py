# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# cloudscaper+alfa_assistant
# ------------------------------------------------------------------------------
import sys
import traceback
import xbmc
import time
import base64
import requests
import re

from .exceptions import CloudflareChallengeError

from core import scrapertools, filetools, jsontools, urlparse
from core.item import Item
from platformcode import logger, config, help_window
from lib import alfa_assistant

PY3 = sys.version_info[0] >= 3

PATH_BL = filetools.join(config.get_runtime_path(), "resources", "cf_assistant_bl.json")
patron_domain = "(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?([\w|\-\d]+\.(?:[\w|\-\d]+\.?)?(?:[\w|\-\d]+\.?)?(?:[\w|\-\d]+))(?:\/|\?|$)"
httptools = None
cf_challenges_list = ["https://challenges.cloudflare.com", "https://www.google.com/recaptcha/api2/anchor?"]

if config.is_xbmc() and config.get_platform(True)["num_version"] >= 14:
    monitor = xbmc.Monitor()  # For Kodi >= 14
else:
    monitor = False  # For Kodi < 14


def get_cl(
    self,
    resp,
    timeout=20,
    debug=False,
    CF_testing=False,
    extraPostDelay=15,
    retry=False,
    blacklist=True,
    headers=None,
    Cookie={},
    retryIfTimeout=True,
    cache=True,
    clearWebCache=False,
    removeAllCookies=True,
    mute=True,
    alfa_s=True,
    httptools_obj=None,
    elapsed=0,
    challenges=0,
    **kwargs
):

    global httptools
    httptools = httptools_obj or httptools
    if not httptools:
        from core import httptools

    try:
        url = self.cloudscraper.user_url
        opt = self.cloudscraper.user_opt
        proxies = self.cloudscraper.proxies
    except Exception:
        url = self.get("url", "") or self.get("url_save", "")
        opt = self
        proxies = {}

    if opt.get("canonical", {}).get("global_search_cancelled", False) or (
        config.GLOBAL_SEARCH_CANCELLED
        and opt.get("canonical", {}).get("global_search_active", False)
    ):
        logger.info(
            "## Búsqueda global cancelada: %s: %s"
            % (opt.get("canonical", {}).get("channel", ""), url),
            force=True,
        )
        return resp

    if opt.get("cf_assistant_get_source", False):
        kwargs["opt"] = opt
        timeout = 0.001
        extraPostDelay = timeout if timeout >= 5 else 0
        return get_source(
            url,
            resp,
            timeout=timeout,
            debug=debug,
            extraPostDelay=extraPostDelay,
            retry=retry,
            blacklist=blacklist,
            retryIfTimeout=retryIfTimeout,
            headers=opt.get("headers", headers),
            Cookie=Cookie,
            cache=cache,
            removeAllCookies=removeAllCookies,
            mute=mute,
            alfa_s=alfa_s,
            elapsed=elapsed,
            challenges=challenges,
            httptools_obj=httptools,
            from_get_cl=True,
            **kwargs
        )

    if timeout < 15:
        timeout = 20
    if timeout + extraPostDelay > 35:
        timeout = 20

    blacklist_clear = True
    ua_headers = False
    postData = None
    jscode = None
    headers_str = ""
    post_str = ""
    Cookies_send = ""
    data_assistant = {}

    if opt.get("cf_cookie_send"):
        Cookie = opt.get("cf_cookie_send")
    if headers is None and opt.get("headers") and isinstance(opt["headers"], dict):
        headers = opt["headers"].copy()
    logger.debug("HEADERS: %s" % headers)
    encoding = opt.get("encoding", "UTF-8") or "UTF-8"
    if "cf_removeAllCookies" in opt and removeAllCookies is not False:
        removeAllCookies = opt["cf_removeAllCookies"]
    if not elapsed:
        elapsed = time.time()
    debug = debug or opt.get("cf_debug", False)
    if debug or CF_testing or opt.get("CF_testing", False):
        alfa_s = False

    try:
        if resp.status_code not in [403, 503, 429, 666]:
            logger.debug("ERROR de descarga: %s. Ignorado por Assistant" % resp.status_code)
            return resp
    except Exception:
        logger.error(traceback.format_exc())
    if not alfa_s:
        logger.debug("ERROR de descarga: %s" % resp.status_code)
    resp.status_code = 503

    if CF_testing or opt.get("CF_testing", False):
        CF_testing = debug = retry = True
        timeout = extraPostDelay = 1
        resp.status_code = 403 if not opt.get("cf_v2", False) else 503
        resp.headers.update({"Server": "Alfa"})

    if (
        not opt.get("cf_assistant", True)
        or not opt.get("canonical", {}).get("cf_assistant", True)
        or opt.get("cf_v2", False)
    ):
        resp.status_code = 403
        return resp

    host_name = httptools.obtain_domain(url, scheme=True).rstrip("/") + "/"
    domain_full = urlparse.urlparse(url).netloc
    domain_ = domain = domain_full
    split_lst = domain_.split(".")
    if len(split_lst) > 2:
        domain_ = domain = domain_.replace(split_lst[0], "")
    if not domain.startswith("."):
        domain = "." + domain
    domain_host = "https://%s" % domain.lstrip(".")
    try:
        pcb = base64.b64decode(config.get_setting("proxy_channel_bloqued")).decode("utf-8")
    except Exception:
        pcb = ""

    if (
        opt.get("cf_assistant_if_proxy", False)
        or opt.get("canonical", {}).get("cf_assistant_if_proxy", False)
    ) and not httptools.TEST_ON_AIR:
        retry = True
    elif (
        "hideproxy" in url
        or "webproxy" in url
        or "hidester" in url
        or "__cpo=" in url
        or proxies
        or httptools.TEST_ON_AIR
        or domain_full in pcb
    ):
        blacklist_clear = False
        blacklist = False

    if opt.get("cf_no_blacklist", False):
        blacklist_clear = True
        blacklist = False
    if blacklist and not retry:
        blacklist_clear = check_blacklist(domain_full)

    if blacklist_clear:
        host = config.get_system_platform()[:1]

        freequent_data = [domain_full, "CF2,0.0.0,0,%s0,NoApp" % host]

        check_assistant = alfa_assistant.open_alfa_assistant(
            getWebViewInfo=True, retry=retry
        )
        if not isinstance(check_assistant, dict) and not retry:
            alfa_assistant.close_alfa_assistant()
            time.sleep(2)
            check_assistant = alfa_assistant.open_alfa_assistant(
                getWebViewInfo=True, retry=True
            )

        if check_assistant and isinstance(check_assistant, dict):
            if check_assistant.get("assistantLatestVersion") and check_assistant.get(
                "assistantVersion"
            ):
                installed_version = check_assistant["assistantVersion"].split(".")
                available_version = check_assistant["assistantLatestVersion"].split(".")
                newer = False
                for i, ver in enumerate(available_version):
                    if int(ver) > int(installed_version[i]):
                        newer = True
                        break
                    if int(ver) < int(installed_version[i]):
                        break
                if newer:
                    help_window.show_info("cf_2_02", wait=False)

            if Cookie or (headers and isinstance(headers, dict) and headers.get("Cookie")):
                Cookies_send = setup_cookies(Cookie, domain, headers)
                if Cookies_send and not opt.get("post") and not opt.get("cf_jscode"):
                    extraPostDelay += 2
                logger.debug("Cookies_send: %s" % Cookies_send)

            if opt.get("cf_assistant_ua", False):
                ua = get_ua(check_assistant)
                ua_headers = True
            elif headers and isinstance(headers, dict) and headers.get("User-Agent", ""):
                ua = headers.pop("User-Agent", "")
                ua_headers = True
            else:
                ua = get_ua(check_assistant)

            if opt.get("post"):
                headers_post = headers.copy()
                headers = {}
                headers_post["Content-Type"] = "application/x-www-form-urlencoded"
                #headers_post["Access-Control-Allow-Origin"] = "*"
                #headers_post["Origin"] = host_name.rstrip("/")

                for key, value in list(headers_post.items()):
                    headers_str += "http.setRequestHeader('%s', '%s'); " % (key, value)
                
                if isinstance(opt.get("post"), dict):
                    for key, value in list(opt["post"].items()):
                        post_str += "%s=%s&" % (key, urlparse.quote(value))
                    post_str = post_str.rstrip("&")
                else:
                    post_str = str(opt["post"]).replace("'", '"')

                jscode = get_jscode(1, "POST_FORM", 1, url=url, headers=headers_str, 
                                    postData=post_str, Cookies_send=Cookies_send)
                if not "function" in jscode:
                    jscode = None
                    headers = headers_post.copy()
                    postData = str(opt["post"]).replace("'", '"')

            try:
                vers = int(scrapertools.find_single_match(ua, r"Android\s*(\d+)"))
            except Exception:
                vers = 0

            wvbVersion = check_assistant.get("wvbVersion", "0.0.0").split(".")[0]
            if len(wvbVersion) > 3:
                wvbVersion = wvbVersion[:2]
            freequent_data[1] = "CF2,%s,%s,%s%s," % (
                check_assistant.get("assistantVersion", "0.0.0"),
                wvbVersion,
                host,
                vers,
            )

            if not ua_headers:
                if vers:
                    dan = {"User-Agent": ua}
                    resp.headers.update(dict(dan))
                    ua = None
                else:
                    ua = httptools.get_user_agent()

            if not alfa_s:
                logger.debug("UserAgent: %s || Android Vrs: %s" % (ua, vers))

            if "cf_jscode" in opt:
                if opt["cf_jscode"] and isinstance(opt["cf_jscode"], dict):
                    for key, value in opt["cf_jscode"].items():
                        if value is True:
                            jscode = get_jscode(1, key, 1, url=url, headers=headers_str, 
                                                postData=post_str, Cookies_send=Cookies_send)
                            break
                        if not value:
                            continue
                        jscode = value
                        break
                    else:
                        jscode = jscode or Cookies_send or None
                else:
                    jscode = jscode or Cookies_send or None
            else:
                jscode = jscode or Cookies_send or get_jscode(1, "KEYCODE_ENTER", 1, url=url, headers=headers_str, 
                                                              postData=post_str, Cookies_send=Cookies_send)

            url_cf = (
                scrapertools.find_single_match(
                    url, "(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?"
                )
                + "|cf_clearance"
            )

            try:
                elapsed_now = time.time()
                data_assistant = alfa_assistant.get_urls_by_page_finished(
                    url,
                    timeout=timeout,
                    getCookies=True,
                    userAgent=ua,
                    disableCache=cache,
                    debug=debug,
                    jsCode=jscode,
                    extraPostDelay=extraPostDelay,
                    getData=None,
                    postData=postData,
                    clearWebCache=clearWebCache,
                    removeAllCookies=removeAllCookies,
                    returnWhenCookieNameFound=opt["cf_cookie"]
                        .replace("$HOST", host_name.rstrip("/"))
                        .replace("$DOMAIN", domain_host)
                        if "cf_cookie" in opt else url_cf,
                    retryIfTimeout=retryIfTimeout,
                    useAdvancedWebView=True,
                    headers=headers,
                    mute=mute,
                    alfa_s=alfa_s
                )
            except Exception:
                logger.error("Cancelado por el usuario - %s" % str(time.time() - elapsed_now))
                return resp

            if not alfa_s or "cookies" not in str(data_assistant):
                logger.debug("data assistant: %s - %s" % (data_assistant, str(time.time() - elapsed_now)))

            if (
                isinstance(data_assistant, dict)
                and data_assistant.get("urlsVisited", [])
                and opt.get("cf_challenge", False)
                and challenges < (2 if opt.get("cf_challenge", False) is True else opt["cf_challenge"])
            ):
                found_url = ''
                if challenges:
                    time.sleep(5)
                for urlsVisited in data_assistant["urlsVisited"]:
                    challenge_url = ''
                    if found_url:
                        break
                    for challenge in opt.get("cf_challenges_list", cf_challenges_list):
                        if urlparse.urlparse(challenge).netloc in urlparse.urlparse(urlsVisited.get("url", "")).netloc:
                            challenge_url = get_value_by_url(
                                data_assistant['urlsVisited'], 
                                challenge,
                                url,
                                domain=domain_,
                                DEBUG=debug,
                                cache=cache,
                                ua=ua,
                                cookiesView=data_assistant.pop("cookies", []),
                                jscode=jscode,
                                extraPostDelay=extraPostDelay, 
                                **opt
                            )
                        for find_url in opt.get("cf_find_url", []):
                            found_url = get_value_by_url(
                                challenge_url.get("urlsVisited", []) if opt.get("cf_returnkey") == "url"
                                else challenge_url.get("htmlSources", []),
                                find_url,
                                find_url,
                                domain=domain_,
                                DEBUG=debug,
                                cache=cache,
                                ua=ua,
                                cookiesView=challenge_url.get("cookies", []),
                                jscode=jscode,
                                extraPostDelay=extraPostDelay, 
                                urlOnly=True,
                                **opt
                            )
                            if found_url:
                                if opt.get("cf_returnkey") == "url":
                                    resp.status_code = 200 if not from_get_cl else 207
                                    if from_get_cl:
                                        try:
                                            resp._content = jsontools.dump(found_url) if isinstance(found_url, dict) else found_url
                                        except Exception:
                                            logger.error(traceback.format_exc())
                                        return resp
                                    return found_url, resp
                                elif found_url.get("url", ""):
                                    url = found_url["url"]
                                    break

                        if challenge_url and isinstance(challenge_url, dict) and challenge_url.get("missing", False):
                            logger.debug("Challenge: %s, reintentando..." % challenge)
                            return get_cl(
                                self,
                                resp,
                                timeout=timeout,
                                debug=debug,
                                extraPostDelay=extraPostDelay,
                                retry=True,
                                blacklist=blacklist,
                                retryIfTimeout=retryIfTimeout,
                                cache=cache,
                                clearWebCache=clearWebCache,
                                removeAllCookies=False,
                                alfa_s=alfa_s,
                                headers=headers,
                                mute=mute,
                                elapsed=elapsed,
                                httptools_obj=httptools,
                                Cookie=Cookie,
                                challenges=challenges+1,
                                **kwargs
                            )
                        elif challenge_url and isinstance(challenge_url, dict) and not challenge_url.get("missing", False):
                            found_url = True
                            data_assistant = challenge_url.copy()
                            break

            get_ua(data_assistant)
            
            if isinstance(data_assistant, dict) and data_assistant.get("cookies", None):
                logger.debug(
                    "Lista cookies: %s - %s"
                    % (data_assistant.get("cookies", []), str(time.time() - elapsed))
                )
                for urlsVisited in data_assistant.get("urlsVisited", []):
                    try:
                        req = requests.Response()
                        req.url = urlsVisited.get("url", "")
                        req.status_code = 200
                        req.encoding = encoding
                        req.headers["Content-Type"] = "application/json"
                        if PY3:
                            req._content = bytes(jsontools.dump(urlsVisited), encoding.lower())
                        else:
                            req._content = jsontools.dump(urlsVisited)

                        resp.history.append(req)
                    except Exception:
                        logger.error(traceback.format_exc())
                
                for cookie in data_assistant["cookies"]:
                    cf_cookies_names = {}
                    cookieslist = cookie.get("cookiesList", "")
                    dom = cookie.get("urls", "")
                    if dom:
                        dom = urlparse.urlparse(dom[0]).netloc or dom[0]
                    logger.debug("dominios: %s => %s" % (domain, dom))

                    if domain.lstrip(".") in dom:
                        for cookie_part in cookieslist.split(";"):
                            try:
                                name, val = scrapertools.find_single_match(
                                    cookie_part, "^([^=]+)=([^$]+)$"
                                )
                                if name.strip() == "domain":
                                    continue
                            except Exception:
                                continue

                            cf_cookies_names[name.strip()] = val.strip()
                            for domain_dot in [domain, domain.lstrip("."), 
                                    domain_full if domain_full != domain.lstrip(".") else ""]:
                                if not domain_dot:
                                    continue
                                dict_cookie = {
                                    "domain": domain_dot,
                                    "name": name.strip(),
                                    "value": val.strip()
                                }
                                if "Secure" in cookie_part:
                                    dict_cookie["secure"] = True

                                httptools.set_cookies(dict_cookie, clear=False, alfa_s=True)

                    cookies_found = True
                    for key, value in opt.get("cf_cookies_names", {}).items():
                        if value:
                            continue
                        if not cf_cookies_names.get(key):
                            cookies_found = False
                            break
                    if cf_cookies_names:
                        logger.info("COOKIES añadidas='%s - %s' - found: %s" % (domain, cf_cookies_names, cookies_found), force=True)
                            
                    if cookies_found or ("cf_clearance" in cf_cookies_names and cf_cookies_names["cf_clearance"]):
                        resp.status_code = 403
                        rin = {"Server": "Alfa"}
                        resp.headers.update(dict(rin))
     
                        if not retry:
                            freequent_data[1] += "OK"
                        else:
                            freequent_data[1] += "OK_R"
                        freequency(freequent_data)

                        for urlsVisited in data_assistant.get("urlsVisited", []):
                            try:
                                req = requests.Response()
                                req.url = urlsVisited.get("url", "")
                                req.status_code = 200
                                req.encoding = encoding
                                req.headers["Content-Type"] = "application/json"
                                if PY3:
                                    req._content = bytes(jsontools.dump(urlsVisited), encoding.lower())
                                else:
                                    req._content = jsontools.dump(urlsVisited)

                                resp.history.append(req)
                            except Exception:
                                logger.error(traceback.format_exc())
                        
                        return resp

                    else:
                        logger.error("No cf_clearance")
                        freequent_data[1] += "NO-CFC"
            else:
                freequent_data[1] += "ERR"
                logger.error(
                    "No Cookies o Error en conexión con Alfa Assistant %s"
                    % str(time.time() - elapsed)
                )

            if monitor and monitor.abortRequested():
                logger.error("Cancelado por el usuario - %s" % str(time.time() - elapsed))
                return resp
            if not retry:
                config.set_setting("cf_assistant_ua", "")
                logger.debug("No se obtuvieron resultados, reintentando... - %s" % str(time.time() - elapsed))
                return get_cl(
                    self,
                    resp,
                    timeout=timeout - 5,
                    extraPostDelay=extraPostDelay,
                    debug=debug,
                    CF_testing=CF_testing,
                    retry=True,
                    blacklist=blacklist,
                    retryIfTimeout=False,
                    cache=cache,
                    clearWebCache=clearWebCache,
                    removeAllCookies=removeAllCookies,
                    elapsed=elapsed,
                    headers=headers,
                    mute=mute,
                    httptools_obj=httptools,
                    alfa_s=False,
                    Cookie=Cookie,
                    challenges=challenges+1,
                    **kwargs
                )
        elif host == "a":
            help_window.show_info("cf_2_01", wait=False)

        freequency(freequent_data)

        if blacklist and blacklist_clear:
            if filetools.exists(PATH_BL):
                bl_data = jsontools.load(filetools.read(PATH_BL))
            else:
                bl_data = {}
            bl_data[domain_full] = time.time()
            if not debug:
                filetools.write(PATH_BL, jsontools.dump(bl_data))

    if isinstance(data_assistant, dict):
        for urlsVisited in data_assistant.get("urlsVisited", []):
            try:
                req = requests.Response()
                req.url = urlsVisited.get("url", "")
                req.status_code = 200
                req.encoding = encoding
                req.headers["Content-Type"] = "application/json"
                if PY3:
                    req._content = bytes(jsontools.dump(urlsVisited), encoding.lower())
                else:
                    req._content = jsontools.dump(urlsVisited)

                resp.history.append(req)
            except Exception:
                logger.error(traceback.format_exc())

    return resp


def get_source(
    url,
    resp,
    timeout=5,
    debug=False,
    extraPostDelay=5,
    retry=False,
    blacklist=True,
    headers=None,
    from_get_cl=False,
    Cookie={},
    retryIfTimeout=True,
    cache=False,
    clearWebCache=False,
    removeAllCookies=True,
    mute=True,
    alfa_s=True,
    elapsed=0,
    httptools_obj=None,
    challenges=0,
    **kwargs
):

    global httptools
    httptools = httptools_obj or httptools
    if not httptools:
        from core import httptools

    blacklist_clear = True
    data = ""
    source = False
    headers_str = ""
    post_str = ""
    if not elapsed:
        elapsed = time.time()
    elapsed_max = 40
    expiration = config.get_setting("cf_assistant_bl_expiration", default=30) * 60
    expiration_final = 0
    security_error_blackout = (5 * 60) - expiration
    ua_headers = False
    urls_ignored = []
    postData = None
    jscode = None
    Cookies_send = ""
    data_assistant = {}

    if timeout < 0:
        timeout = 0.001

    if not resp and not from_get_cl:
        resp = requests.Response()
        resp.status_code = 429

    opt = kwargs.get("opt", {})
    if not opt.get("CF_assistant", True):
        return (data, resp) if not from_get_cl else resp
    if not opt and "btdig" in url:
        opt["CF_assistant"] = True
        opt["cf_assistant_ua"] = True
        opt["cf_assistant_get_source"] = True
        opt["cf_removeAllCookies"] = False
        opt["cf_challenge"] = True
        opt["cf_returnkey"] = "url"
        opt["cf_partial"] = True
        opt["cf_jscode"] = None
        opt["cf_cookies_names"] = {"cf_clearance": False}

    if opt.get("cf_cookie_send"):
        Cookie = opt.get("cf_cookie_send")
    if headers is None and opt.get("headers") and isinstance(opt["headers"], dict):
        headers = opt["headers"].copy()
    logger.debug("HEADERS: %s" % headers)
    encoding = opt.get("encoding", "UTF-8") or "UTF-8"
    if "cf_removeAllCookies" in opt and removeAllCookies is not False:
        removeAllCookies = opt["cf_removeAllCookies"]
    debug = debug or opt.get("cf_debug", False)
    if debug:
        alfa_s = False
    if not alfa_s:
        logger.debug("ERROR de descarga: %s" % resp.status_code)
    resp.status_code = 429 if not from_get_cl else (resp.status_code or 400)

    host_name = httptools.obtain_domain(url, scheme=True).rstrip("/") + "/"
    domain_full = urlparse.urlparse(url).netloc
    domain_ = domain = domain_full
    split_lst = domain_.split(".")
    if len(split_lst) > 2:
        domain_ = domain = domain_.replace(split_lst[0], "")
    if not domain.startswith("."):
        domain = "." + domain
    domain_host = "https://%s" % domain.lstrip(".")
    try:
        pcb = base64.b64decode(config.get_setting("proxy_channel_bloqued")).decode("utf-8")
    except Exception:
        pcb = ""

    if (
        "hideproxy" in url
        or "webproxy" in url
        or "hidester" in url
        or "__cpo=" in url
        or httptools.TEST_ON_AIR
        or domain_full in pcb
    ):
        blacklist_clear = False
        blacklist = False

    if timeout + extraPostDelay > 35:
        timeout = 20

    if opt.get("cf_no_blacklist", False):
        blacklist_clear = True
        blacklist = False
    if blacklist and not retry:
        blacklist_clear = check_blacklist(domain_full)

    host = config.get_system_platform()[:1]
    freequent_data = [domain_full, "Cha,0.0.0,0,%s0,BlakL" % host]
    if blacklist_clear:
        freequent_data = [domain_full, "Cha,0.0.0,0,%s0,App" % host]
        if not retry:
            freequent_data[1] += "KO"
        else:
            freequent_data[1] += "KO_R"

        check_assistant = alfa_assistant.open_alfa_assistant(
            getWebViewInfo=True, retry=True, assistantLatestVersion=False
        )
        if not isinstance(check_assistant, dict) and not retry:
            import xbmcgui

            window = xbmcgui.Window(10000) or None
            if "btdig" in url and len(window.getProperty("alfa_gateways")) > 5:
                logger.error("Assistant no disponible: usa gateways")
                return (data, resp) if not from_get_cl else resp

            alfa_assistant.close_alfa_assistant()
            time.sleep(2)
            check_assistant = alfa_assistant.open_alfa_assistant(
                getWebViewInfo=True, retry=True, assistantLatestVersion=False
            )
            logger.debug(
                "Reintento en acceder al Assistant: %s - %s"
                % (
                    "OK" if isinstance(check_assistant, dict) else "ERROR",
                    str(time.time() - elapsed),
                )
            )

        if check_assistant and isinstance(check_assistant, dict):
            if check_assistant.get("assistantLatestVersion") and check_assistant.get(
                "assistantVersion"
            ):
                installed_version = check_assistant["assistantVersion"].split(".")
                available_version = check_assistant["assistantLatestVersion"].split(".")
                newer = False
                for i, ver in enumerate(available_version):
                    if int(ver) > int(installed_version[i]):
                        newer = True
                        break
                    if int(ver) < int(installed_version[i]):
                        break
                if newer:
                    help_window.show_info("cf_2_02", wait=False)

            if Cookie or (headers and isinstance(headers, dict) and headers.get("Cookie")):
                Cookies_send = setup_cookies(Cookie, domain, headers)
                if Cookies_send and not opt.get("post") and not opt.get("cf_jscode"):
                    extraPostDelay += 2
                logger.debug("Cookies_send: %s" % Cookies_send)

            resp.headers["Content-Type"] = "text/html; charset=%s" % encoding
            if opt.get("cf_assistant_ua", False):
                ua = get_ua(check_assistant)
                ua_headers = True
            elif headers and isinstance(headers, dict) and headers.get("User-Agent", ""):
                ua = headers.pop("User-Agent", "")
                ua_headers = True
            else:
                ua = get_ua(check_assistant)

            if opt.get("post"):
                headers_post = headers.copy()
                headers = {}
                headers_post["Content-Type"] = "application/x-www-form-urlencoded"
                #headers_post["Access-Control-Allow-Origin"] = "*"
                #headers_post["Origin"] = host_name.rstrip("/")

                for key, value in list(headers_post.items()):
                    headers_str += "http.setRequestHeader('%s', '%s'); " % (key, value)
                
                if isinstance(opt.get("post"), dict):
                    for key, value in list(opt["post"].items()):
                        post_str += "%s=%s&" % (key, urlparse.quote(value))
                    post_str = post_str.rstrip("&")
                else:
                    post_str = str(opt["post"]).replace("'", '"')

                jscode = get_jscode(1, "POST_FORM", 1, url=url, headers=headers_str, 
                                    postData=post_str, Cookies_send=Cookies_send)
                if not "function" in jscode:
                    jscode = None
                    headers = headers_post.copy()
                    postData = str(opt["post"]).replace("'", '"')
                else:
                    extraPostDelay += 2

            try:
                vers = int(scrapertools.find_single_match(ua, r"Android\s*(\d+)"))
            except Exception:
                vers = 0

            if "cf_jscode" in opt:
                if opt["cf_jscode"] and isinstance(opt["cf_jscode"], dict):
                    for key, value in opt["cf_jscode"].items():
                        if value is True:
                            jscode = get_jscode(1, key, 1, url=url, headers=headers_str, 
                                                postData=post_str, Cookies_send=Cookies_send)
                            if jscode:
                                extraPostDelay += 2
                            break
                        if not value:
                            continue
                        jscode = value
                        break
                    else:
                        jscode = jscode or Cookies_send or None
                else:
                    jscode = jscode or Cookies_send or None
            else:
                jscode = jscode or Cookies_send or None

            wvbVersion = check_assistant.get("wvbVersion", "0.0.0").split(".")[0]
            if len(wvbVersion) > 3:
                wvbVersion = wvbVersion[:2]
            freequent_data[1] = "Cha,%s,%s,%s%s," % (
                check_assistant.get("assistantVersion", "0.0.0"),
                wvbVersion,
                host,
                vers,
            )
            if not retry:
                freequent_data[1] += "Src"
            else:
                freequent_data[1] += "Src_R"

            if not ua_headers:
                if vers:
                    dan = {"User-Agent": ua}
                    resp.headers.update(dict(dan))
                    ua = None
                else:
                    ua = httptools.get_user_agent()

            if not alfa_s:
                logger.debug("UserAgent: %s || Android Vrs: %s" % (ua, vers))

            url_cf = (
                scrapertools.find_single_match(
                    url, "(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?"
                )
                + "|cf_clearance"
            )

            try:
                elapsed_now = time.time()
                data_assistant = alfa_assistant.get_source_by_page_finished(
                    url,
                    timeout=timeout,
                    getCookies=True,
                    userAgent=ua,
                    disableCache=cache,
                    debug=debug,
                    jsCode=jscode,
                    extraPostDelay=extraPostDelay,
                    getData=str(opt.get("files", "")) if opt.get("files") else None,
                    postData=postData,
                    clearWebCache=clearWebCache,
                    removeAllCookies=removeAllCookies,
                    returnWhenCookieNameFound=None,
                    retryIfTimeout=retryIfTimeout,
                    useAdvancedWebView=True,
                    headers=headers,
                    mute=mute,
                    alfa_s=alfa_s
                )
            except Exception:
                logger.error("Cancelado por el usuario - %s" % str(time.time() - elapsed_now))
                return resp

            if not alfa_s:
                logger.debug("data assistant: %s - %s" % (data_assistant, str(time.time() - elapsed_now)))

            if (
                isinstance(data_assistant, dict)
                and data_assistant.get("urlsVisited", [])
                and opt.get("cf_challenge", False)
                and challenges < (2 if opt.get("cf_challenge", False) is True else opt["cf_challenge"])
            ):
                found_url = ''
                if challenges:
                    time.sleep(5)
                for urlsVisited in data_assistant["urlsVisited"]:
                    challenge_url = ''
                    if found_url:
                        break
                    for challenge in opt.get("cf_challenges_list", cf_challenges_list):
                        if urlparse.urlparse(challenge).netloc in urlparse.urlparse(urlsVisited.get("url", "")).netloc:
                            challenge_url = get_value_by_url(
                                data_assistant['urlsVisited'], 
                                challenge,
                                url,
                                domain=domain_,
                                DEBUG=debug,
                                cache=cache,
                                ua=ua,
                                cookiesView=data_assistant.pop("cookies", []),
                                jscode=jscode,
                                extraPostDelay=extraPostDelay,
                                **opt
                            )
                        for find_url in opt.get("cf_find_url", []):
                            found_url = get_value_by_url(
                                challenge_url.get("urlsVisited", []) if opt.get("cf_returnkey") == "url"
                                else challenge_url.get("htmlSources", []),
                                find_url,
                                find_url,
                                domain=domain_,
                                DEBUG=debug,
                                cache=cache,
                                ua=ua,
                                cookiesView=challenge_url.get("cookies", []),
                                jscode=jscode,
                                extraPostDelay=extraPostDelay,
                                urlOnly=True,
                                **opt
                            )
                            if found_url:
                                if opt.get("cf_returnkey") == "url":
                                    resp.status_code = 200 if not from_get_cl else 207
                                    if from_get_cl:
                                        try:
                                            resp._content = jsontools.dump(found_url) if isinstance(found_url, dict) else found_url
                                        except Exception:
                                            logger.error(traceback.format_exc())
                                        return resp
                                    return found_url, resp
                                elif found_url.get("url", ""):
                                    url = found_url["url"]
                                    break

                        if challenge_url and isinstance(challenge_url, dict):
                            logger.debug("Challenge: %s, reintentando..." % challenge)
                            return get_source(
                                url,
                                resp,
                                timeout=timeout,
                                debug=debug,
                                extraPostDelay=extraPostDelay,
                                retry=True,
                                blacklist=blacklist,
                                retryIfTimeout=retryIfTimeout,
                                cache=cache,
                                clearWebCache=clearWebCache,
                                removeAllCookies=False,
                                alfa_s=alfa_s,
                                from_get_cl=from_get_cl,
                                headers=headers,
                                mute=mute,
                                elapsed=elapsed,
                                httptools_obj=httptools,
                                Cookie=Cookie,
                                challenges=challenges+1,
                                **kwargs
                            )

            if (
                isinstance(data_assistant, dict)
                and data_assistant.get("htmlSources", [])
                and "url" in data_assistant["htmlSources"][0]
            ):
                for html_source in data_assistant["htmlSources"]:
                    if html_source.get("url", "") != url:
                        urls_ignored += [html_source.get("url", "")]
                        if not alfa_s:
                            logger.debug("Url ignored: %s" % html_source.get("url", ""))
                        continue
                    if not alfa_s:
                        logger.debug("Url accepted: %s" % html_source.get("url", ""))
                    try:
                        data = data_str = base64.b64decode(html_source.get("source", ""))
                        if PY3 and isinstance(data, bytes):
                            data_str = "".join(chr(x) for x in bytes(data))
                        if not from_get_cl: 
                            data = data_str
                        data_str = re.sub('<html>|<\/html>|<head>|<\/head>|<body>|<\/body>', '', data_str)
                        if not data_str:
                            continue
                        source = True
                    except Exception:
                        logger.error(traceback.format_exc(1))
                        continue

                    if source and "accessing a cross-origin frame" in data_str:
                        source = False
                        retry = True
                        expiration_final = security_error_blackout
                        freequent_data[1] = "Cha,%s,%s,%s%s," % (
                            check_assistant.get("assistantVersion", "0.0.0"),
                            wvbVersion,
                            host,
                            vers,
                        )
                        freequent_data[1] += "KO_SecE"
                        logger.error(
                            "Error SEGURIDAD: %s - %s" % (expiration_final, data_str[:100])
                        )

                    elif source:
                        resp.status_code = 200 if not from_get_cl else 207
                        freequent_data[1] = "Cha,%s,%s,%s%s," % (
                            check_assistant.get("assistantVersion", "0.0.0"),
                            wvbVersion,
                            host,
                            vers,
                        )
                        if not retry:
                            freequent_data[1] += "OK"
                        else:
                            freequent_data[1] += "OK_R"
                        break

                else:
                    if not source and 'captcha' in str(urls_ignored): retry = True

            if monitor and monitor.abortRequested():
                logger.error("Cancelado por el usuario - %s" % str(time.time() - elapsed))
                return (data, resp) if not from_get_cl else resp
            if not source and not retry:
                config.set_setting("cf_assistant_ua", "")
                logger.debug("No se obtuvieron resultados, reintentando... - %s" % str(time.time() - elapsed))
                timeout = 1 if timeout < 5 else timeout * 2
                extraPostDelay = -1 if extraPostDelay < 0 else extraPostDelay * 2
                removeAllCookies = True

                return get_source(
                    url,
                    resp,
                    timeout=timeout,
                    debug=debug,
                    extraPostDelay=extraPostDelay,
                    retry=True,
                    blacklist=blacklist,
                    retryIfTimeout=retryIfTimeout,
                    cache=cache,
                    clearWebCache=clearWebCache,
                    removeAllCookies=removeAllCookies,
                    alfa_s=False,
                    from_get_cl=from_get_cl,
                    headers=headers,
                    mute=mute,
                    elapsed=elapsed,
                    httptools_obj=httptools,
                    Cookie=Cookie,
                    challenges=challenges+1,
                    **kwargs
                )

            get_ua(data_assistant)

            if isinstance(data_assistant, dict) and data_assistant.get("cookies", None):
                if not alfa_s:
                    logger.debug(
                        "Lista cookies: %s - %s"
                        % (data_assistant.get("cookies", []), str(time.time() - elapsed))
                    )
                for cookie in data_assistant["cookies"]:
                    cf_cookies_names = {}
                    cookieslist = cookie.get("cookiesList", "")
                    dom = cookie.get("urls", "")
                    if dom:
                        dom = urlparse.urlparse(dom[0]).netloc or dom[0]
                    logger.debug("dominios: %s => %s" % (domain, dom))

                    if domain.lstrip(".") in dom:
                        for cookie_part in cookieslist.split(";"):
                            try:
                                name, val = scrapertools.find_single_match(
                                    cookie_part, "^([^=]+)=([^$]+)$"
                                )
                                if name.strip() == "domain":
                                    continue
                            except Exception:
                                continue

                            cf_cookies_names[name.strip()] = val.strip()
                            for domain_dot in [domain, domain.lstrip("."), 
                                    domain_full if domain_full != domain.lstrip(".") else ""]:
                                if not domain_dot:
                                    continue
                                dict_cookie = {
                                    "domain": domain_dot,
                                    "name": name.strip(),
                                    "value": val.strip()
                                }
                                if "Secure" in cookie_part:
                                    dict_cookie["secure"] = True

                                httptools.set_cookies(dict_cookie, clear=False, alfa_s=True)
                            resp.status_code = 201 if not from_get_cl else 208

                        freequent_data[1] += "C"

                    if cf_cookies_names:
                        logger.info("COOKIES añadidas='%s': %s" % (domain, cf_cookies_names), force=True)

        elif host == "a":
            help_window.show_info("cf_2_01", wait=False)

    freequency(freequent_data)

    if (
        blacklist
        and blacklist_clear
        and (not source or time.time() - elapsed > elapsed_max)
    ):
        if filetools.exists(PATH_BL):
            bl_data = jsontools.load(filetools.read(PATH_BL))
        else:
            bl_data = {}
        if time.time() - elapsed > elapsed_max:
            bl_data[domain_full] = time.time() + elapsed_max * 10 * 60
        else:
            bl_data[domain_full] = time.time() + expiration_final
        if not debug and not httptools.TEST_ON_AIR:
            filetools.write(PATH_BL, jsontools.dump(bl_data))

    if isinstance(data_assistant, dict):
        for urlsVisited in data_assistant.get("urlsVisited", []):
            try:
                req = requests.Response()
                req.url = urlsVisited.get("url", "")
                req.status_code = 200 if not from_get_cl else 207
                req.encoding = encoding
                req.headers["Content-Type"] = "application/json"
                if PY3:
                    req._content = bytes(jsontools.dump(urlsVisited), encoding.lower())
                else:
                    req._content = jsontools.dump(urlsVisited)

                resp.history.append(req)
            except Exception:
                logger.error(traceback.format_exc())
    if from_get_cl:
        try:
            if PY3 and not isinstance(data, bytes):
                data = bytes(data, encoding.lower())
            resp._content = data
            resp.encoding = encoding
            try:
                x = resp.json()
                resp.headers["Content-Type"] = "application/json"
            except Exception:
                pass
        except Exception:
            logger.error(traceback.format_exc())
        return resp
    return data, resp


def get_ua(data_assistant, userAgent=False):
    if not data_assistant or not isinstance(data_assistant, dict):
        return "Default"

    if userAgent:
        UA = config.get_setting("cf_assistant_ua", default="Default")
    else:
        UA = data_assistant.get("userAgent", "Default")
    if "mozilla" not in UA.lower():
        UA = "Default"

    global httptools
    if not httptools:
        from core import httptools

    if UA == "Default":
        #UA = httptools.get_user_agent()
        UA = None

    config.set_setting("cf_assistant_ua", UA)

    return UA


def setup_cookies(Cookie, domain, headers):
    Cookies_send = ""
    if not Cookie:
        Cookie = []
    
    if not isinstance(Cookie, list):
        Cookie = [Cookie]
    if headers and isinstance(headers, dict) and headers.get("Cookie"):
        Cookie += [headers.pop("Cookie")]

    for Cookie_ in Cookie:
        Cookie_send = name_ = value_ = ""
        if isinstance(Cookie_, dict):
            for key, value in list(Cookie_.items()):
                if key == "name":
                    name_ = value
                    if not value_:
                        continue
                if key == "value":
                    value_ = value
                    if not name_:
                        continue
                if name_ and value_:
                    Cookie_send += "%s=%s; " % (urlparse.quote(name_), urlparse.quote(str(value_)))
                    name_ = value_ = ""
                else:
                    Cookie_send += "%s=%s; " % (urlparse.quote(key), urlparse.quote(str(value)))
            Cookie_send = Cookie_send
        else:
            Cookie_send = str(Cookie_).rstrip(";").rstrip() + "; "
        if Cookie_send:
            if not "domain" in Cookie_send:
                Cookie_send += "%s=%s; " % ("domain", urlparse.quote(str(domain)))
            if not "path" in Cookie_send:
                Cookie_send += "%s=%s; " % ("path", "/")
            Cookies_send += "document.cookie = '%s'; " % Cookie_send.rstrip("; ")

    return Cookies_send


def get_jscode(count, key, n_iframe, timeout=3, url="", headers="", postData="", Cookies_send=""):
    count = str(count)
    # focus = str(n_iframe)
    timeout = str(timeout * 1000)
    js = None

    js_list = {
        'KEYCODE_ENTER': """(()=>{function e(e,t,n,o,i){var c,s,u,a;try{let d=alfaAssistantAndroidPI.getDPINeutral();x=t*d,y=n*d,r(o,i),c=l(o,i).x,s=l(o,i).y,u=c-0,a=s-0;let f=document.createElement("div");f.style.width="10px",f.style.height="10px",f.style.background="red",f.style.display="inline-block",f.style.borderRadius="25px",f.style.position="absolute";let $=(window.pageXOffset||document.documentElement.scrollLeft)-(document.documentElement.clientLeft||0);f.style.left=$+x/window.devicePixelRatio-5-1+u+"px";let m=(window.pageYOffset||document.documentElement.scrollTop)-(document.documentElement.clientTop||0);f.style.top=m+y/window.devicePixelRatio-5-1+a+"px",f.style.zIndex="9999999999",f.innerHTML="",document.body.appendChild(f),setTimeout(()=>{document.body.removeChild(f)},500)}catch(p){}try{setTimeout(()=>{r(o,i),console.log("alfaAssistantAndroidPI.sendMouse =>",x+u,y+a),alfaAssistantAndroidPI.sendMouse(e,x+u,y+a)},600)}catch(_){console.error("##Error sending mouse keys ",e,x,y,_)}}function t(e,t){try{for(var r=0;r<=e;r++)if(r>0&&alfaAssistantAndroidPI.sendKey("KEYCODE_TAB"),r==e){alfaAssistantAndroidPI.sendKey(t),console.log("#Current item focused:",document.activeElement);break}}catch(l){console.error("##Error sending key "+t,l)}}function r(e,t){try{document.querySelectorAll(null!=t?t:"iframe")[e-1].focus(),console.log("#Current item focused:",document.activeElement)}catch(r){console.error("##Error on setFocusToElementNumber",r)}}function l(e,t){return document.querySelectorAll(null!=t?t:"iframe")[e-1].getBoundingClientRect()}function n(e,t){let r=document.querySelectorAll(null!=t?t:"iframe")[e-1];r.style.margin=0,r.style.padding=0,r.style.left=0,r.style.top=0,r.style.border=0,r.style.position="absolute",r.style.zIndex="99999"}async function o(e){let t=null!=e?e:"iframe";for(;!document.querySelectorAll(t)[0];)await s(100)}function i(e,t){return Math.random()*(t-e)+e}function c(e,t){return i(e*(100-t)/100,e*(100+t)/100)}function s(e){return new Promise(t=>setTimeout(t,e))}async function u(){o(thisSelector='iframe[src*="challenge"]'),n(1,thisSelector),e([0,1],c(314,DIFF_PERCENTAGE=8),c(120,DIFF_PERCENTAGE),1)}try{u()}catch(a){console.error("##Error",a)}})();
        """,
        'KEYCODE_ENTER_RECAPTCHA': """ 
        document.querySelector("#recaptcha-anchor > div.recaptcha-checkbox-border").click();
        """,
        'POST_FORM': """
        var http = new XMLHttpRequest();
        var url = '%s';
        var params = '%s';
        http.open('POST', url, true);

        //Send the proper header information along with the request
        %s
        %s

        http.onreadystatechange = function() {//Call a function when the state changes.
            if(http.readyState == 4 && http.status == 200) {
                return(http.responseText);
            }
        }
        http.send(params);
        """  % (url, postData, headers, Cookies_send),
        'COOKIES': """
        //Send cookies to the site
        %s
        """  % (Cookies_send),
    }

    if key:
        js = js_list.get(key, None)
    return js


def freequency(freequent_data):
    exclude_list = ["KO_Web"]

    for exclude in exclude_list:
        if exclude.lower() in str(freequent_data).lower():
            return

    import threading

    if PY3:
        from lib.alfaresolver_py3 import frequency_count
    else:
        from lib.alfaresolver import frequency_count

    try:
        threading.Thread(
            target=frequency_count, args=(Item(), [], freequent_data)
        ).start()
        # ret = True
    except Exception:
        logger.error(traceback.format_exc())


def check_blacklist(domain, expiration=0, reset=False):
    res = True
    if not filetools.exists(PATH_BL):
        return res

    try:
        expiration_default = 5
        bl_data = jsontools.load(filetools.read(PATH_BL))
        bl_data_clean = bl_data.copy()
        if not expiration:
            expiration = (
                config.get_setting(
                    "cf_assistant_bl_expiration", default=expiration_default
                )
                * 60
            )
            if expiration / 60 != expiration_default and expiration / 60 in [30]:
                config.set_setting("cf_assistant_bl_expiration", expiration_default)
                expiration = expiration_default * 60
        else:
            expiration = expiration * 60
        time_today = time.time()

        if bl_data:
            update = False
            for domain_reg, time_rec in list(bl_data_clean.items()):
                if time_today > time_rec + expiration:
                    del bl_data[domain_reg]
                    update = True
                if reset and time_rec != 9999999999.999998:
                    if domain_reg in bl_data:
                        del bl_data[domain_reg]
                        update = True
                        logger.info(
                            "Bloqueo liberado: %s: %s" % (domain_reg, time_rec),
                            force=True,
                        )
            if update:
                filetools.write(PATH_BL, jsontools.dump(bl_data))
            for domain_reg, time_rec in list(bl_data.items()):
                if domain in domain_reg:
                    res = False
                    break
            else:
                res = True
    except Exception:
        logger.error(traceback.format_exc())
        filetools.remove(PATH_BL)
        res = True

    return res


def get_value_by_url(sources, url, host, cookiesView=[], domain="", cf_returnkey="source", 
                     extraPostDelay=15, jscode="", DEBUG=False, cache=True, ua=None, urlOnly=False, **opt):
    logger.info("Challenge: %s" % url)
    data = False
    response = None
    clear=False
    if not sources or not url or not host:
        return response

    global httptools
    if not httptools:
        from core import httptools

    host_name = httptools.obtain_domain(host, scheme=True)
    domain_full = urlparse.urlparse(host_name).netloc 
    domain = domain or domain_full
    domain_host = "https://%s" % domain
    cf_returnkey = cf_returnkey or opt.get("cf_returnkey", "source")
    cf_partial = opt.get("cf_partial", False)
    cf_cookie = opt.get("cf_cookie", "")
    if cf_cookie is not None:
        cf_cookie = cf_cookie.replace("$HOST", host_name.rstrip("/")).replace("$DOMAIN", domain_host)
    cf_cookies_names = opt.get("cf_cookies_names", {})
    if "missing" in cf_cookies_names:
        del cf_cookies_names["missing"]
    url_cf = (
        scrapertools.find_single_match(
            host, "(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?"
        )
        + "|cf_clearance"
    )
    if not cf_cookie and "cf_cookie" not in opt:
        cf_cookie = url_cf
    if not jscode and jscode is not None:
        key_js = "KEYCODE_ENTER_RECAPTCHA" if "recaptcha" in url else "KEYCODE_ENTER"
        jscode = get_jscode(1, key_js, 1)
        if extraPostDelay <= 0:
            extraPostDelay = 2

    try:
        if urlOnly:
            data = [source for source in sources if url in source["url"]][0] or ''
            logger.debug("urlOnly: %s" % data)
        elif PY3:
            if cf_partial:
                data = next(filter(lambda source: url in source["url"], sources))[cf_returnkey]
            else:
                data = next(filter(lambda source: source["url"] == url, sources))[cf_returnkey]
        else:
            if cf_partial:
                data = filter(lambda source: url in source["url"], sources)[0][cf_returnkey]
            else:
                data = filter(lambda source: source["url"] == url, sources)[0][cf_returnkey]

        try:
            if not urlOnly:
                data_copy = base64.b64decode(data).decode("utf-8", "ignore")
                data = data_copy
        except:
            pass

        if data and not urlOnly:
            for x in range(2):
                elapsed_now = time.time()
                clear = True
                response = alfa_assistant.get_urls_by_page_finished("about:blank", 1, closeAfter=True, removeAllCookies=True, 
                                                                    userAgent=ua, debug=DEBUG)
                response = alfa_assistant.get_urls_by_page_finished("{}".format(host), 20, closeAfter=True, disableCache=cache, 
                                                                    clearWebCache=True, returnWhenCookieNameFound=cf_cookie, 
                                                                    jsCode=jscode, extraPostDelay=extraPostDelay, 
                                                                    getCookies=True, userAgent=ua, debug=DEBUG)
                if DEBUG:
                    logger.debug("data assistant: %s - %s" % (response, str(time.time() - elapsed_now)))

                for cookie in response.get("cookies", []):
                    cookieslist = cookie.get("cookiesList", "")
                    if not cookieslist:
                        continue

                    dom = cookie.get("urls", "")
                    if dom:
                        dom = urlparse.urlparse(dom[0]).netloc or dom[0]
                    logger.debug("dominios: %s => %s" % (domain, dom))

                    if domain.lstrip(".") in dom:
                        for cookie_part in cookieslist.split(";"):
                            try:
                                name, val = scrapertools.find_single_match(
                                    cookie_part, "^([^=]+)=([^$]+)$"
                                )
                                if name.strip() == "domain":
                                    continue
                            except Exception:
                                continue

                            cf_cookies_names[name.strip()] = True
                            for domain_dot in [domain, domain.lstrip("."), 
                                    domain_full if domain_full != domain.lstrip(".") else ""]:
                                if not domain_dot:
                                    continue
                                dict_cookie = {
                                    "domain": domain_dot,
                                    "name": name.strip(),
                                    "value": val.strip()
                                }
                                if "Secure" in cookie_part:
                                    dict_cookie["secure"] = True

                                httptools.set_cookies(dict_cookie, clear=clear, alfa_s=True)
                            clear = False

                if DEBUG:
                    logger.debug("cf_cookies_names: %s" % cf_cookies_names)
                for key, value in cf_cookies_names.items():
                    if not value:
                        cf_cookies_names["missing"] = True
                        response = cf_cookies_names.copy()
                        time.sleep(5)
                        break
                else:
                    break

    except:
        pass

    return response or data