# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# cloudscaper+alfa_assistant
# ------------------------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse
    from lib import alfaresolver_py3 as alfaresolver
else:
    import urlparse
    from lib import alfaresolver

import traceback
import xbmc
import time
import base64

from .exceptions import CloudflareChallengeError

from lib import alfa_assistant
from core import httptools, scrapertools, filetools, jsontools
from core.item import Item
from platformcode import logger, config, help_window

PATH_BL = filetools.join(config.get_runtime_path(), 'resources', 'cf_assistant_bl.json')
patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?([\w|\-\d]+\.(?:[\w|\-\d]+\.?)?(?:[\w|\-\d]+\.?)?(?:[\w|\-\d]+))(?:\/|\?|$)'


def get_cl(self, resp, timeout=20, debug=False, extraPostDelay=15, retry=False, blacklist=True, headers=None, 
           retryIfTimeout=True, cache=True, clearWebCache=False, mute=True, alfa_s=True, elapsed=0, **kwargs):
    blacklist_clear = True
    ua_headers = False
    if not elapsed: elapsed = time.time()
        
    if not resp:
        resp = {
                'status_code': 503, 
                'headers': {}
               }
        resp = type('HTTPResponse', (), resp)
    
    if not alfa_s: logger.debug("ERROR de descarga: %s" % resp.status_code)
    
    url = self.cloudscraper.user_url
    opt = self.cloudscraper.user_opt
    
    domain_full = urlparse.urlparse(url).netloc
    domain = domain_full
    pcb = base64.b64decode(config.get_setting('proxy_channel_bloqued')).decode('utf-8')
    if 'hideproxy' in url or 'webproxy' in url or 'hidester' in url \
                          or '__cpo=' in url or self.cloudscraper.proxies \
                          or httptools.TEST_ON_AIR or domain in pcb:
        blacklist_clear = False
        blacklist = False
    
    if timeout < 15: timeout = 20
    if timeout + extraPostDelay > 35: timeout = 20

    if blacklist and not retry: 
        blacklist_clear = check_blacklist(domain_full)
    
    if blacklist_clear:
        host = config.get_system_platform()[:1]
        
        freequent_data = [domain, 'CF2,0.0.0,0,%s0,NoApp' % host]
        
        check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=retry)
        if not isinstance(check_assistant, dict) and not retry:
            alfa_assistant.close_alfa_assistant()
            time.sleep(2)
            check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=True)
            
        if check_assistant and isinstance(check_assistant, dict):

            if check_assistant.get('assistantLatestVersion') and check_assistant.get('assistantVersion'):
                installed_version = check_assistant['assistantVersion'].split('.')
                available_version = check_assistant['assistantLatestVersion'].split('.')
                newer = False
                for i, ver in enumerate(available_version):
                    if int(ver) > int(installed_version[i]):
                        newer = True
                        break
                    if int(ver) < int(installed_version[i]):
                        break
                if newer:
                    help_window.show_info('cf_2_02', wait=False)

            if headers and isinstance(headers, dict) and headers.get('User-Agent', ''):
                ua = headers.pop('User-Agent', '')
                ua_headers = True
            else:
                ua = get_ua(check_assistant)
            
            try:
                vers = int(scrapertools.find_single_match(ua, r"Android\s*(\d+)"))
            except:
                vers = 0

            wvbVersion = check_assistant.get('wvbVersion', '0.0.0').split('.')[0]
            if len(wvbVersion) > 3: wvbVersion = wvbVersion[:2]
            freequent_data[1] = 'CF2,%s,%s,%s%s,' % (check_assistant.get('assistantVersion', '0.0.0'), wvbVersion, host, vers)

            if not ua_headers:
                if vers:
                    dan = {'User-Agent': ua}
                    resp.headers.update(dict(dan))
                    ua = None
                else:
                    ua = httptools.get_user_agent()

            if not alfa_s: logger.debug("UserAgent: %s || Android Vrs: %s" % (ua, vers))

            jscode = get_jscode(1, 'KEYCODE_ENTER', 1)

            url_cf = scrapertools.find_single_match(url, '(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?') + '|cf_clearance'

            data_assistant = alfa_assistant.get_urls_by_page_finished(url, timeout=timeout, getCookies=True, userAgent=ua,
                                                                      disableCache=cache, debug=debug, jsCode=jscode,
                                                                      extraPostDelay=extraPostDelay, clearWebCache=clearWebCache, 
                                                                      removeAllCookies=True, returnWhenCookieNameFound=url_cf,
                                                                      retryIfTimeout=retryIfTimeout, useAdvancedWebView=True, 
                                                                      headers=headers, mute=mute, alfa_s=alfa_s
                                                                     )
            if not alfa_s or "cookies" not in str(data_assistant): 
                logger.debug("data assistant: %s" % data_assistant)

            domain_ = domain
            split_lst = domain.split(".")

            if len(split_lst) > 2:
                domain = domain.replace(split_lst[0], "")
            
            if not domain.startswith('.'):
                domain = "."+domain
            
            get_ua(data_assistant)

            if isinstance(data_assistant, dict) and data_assistant.get("cookies", None):

                logger.debug("Lista cookies: %s - %s" % (data_assistant.get("cookies", []), time.time() - elapsed))
                for cookie in data_assistant["cookies"]:
                    cookieslist = cookie.get("cookiesList", '')
                    val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([A-z0-9_\-\.]+)')
                    #val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([^;]+)')
                    dom = cookie.get("urls", [])
                    logger.debug("dominios: %s" % dom[0])

                    if 'cf_clearance' in cookieslist and val:
                        
                        dict_cookie = {'domain': domain,
                                       'name': 'cf_clearance',
                                       'value': val}
                        if domain_ in dom[0]:
                            httptools.set_cookies(dict_cookie)
                            rin = {'Server': 'Alfa'}

                            resp.headers.update(dict(rin))
                            logger.debug("cf_clearence=%s" % val)
                            
                            if not retry:
                                freequent_data[1] += 'OK'
                            else:
                                freequent_data[1] += 'OK_R'
                            freequency(freequent_data)

                            return resp

                    else:
                        logger.error("No cf_clearance")
                else:
                    freequent_data[1] += 'NO-CFC'
            else:
                freequent_data[1] += 'ERR'
                logger.error("No Cookies o Error en conexión con Alfa Assistant %s" % time.time() - elapsed)

            if not retry:
                config.set_setting('cf_assistant_ua', '')
                logger.debug("No se obtuvieron resultados, reintentando...")
                return get_cl(self, resp, timeout=timeout-5, extraPostDelay=extraPostDelay, 
                            retry=True, blacklist=True, retryIfTimeout=False, 
                            cache=cache, clearWebCache=clearWebCache, 
                            elapsed=elapsed, headers=headers, mute=mute, alfa_s=False, **kwargs)
        elif host == 'a':
            help_window.show_info('cf_2_01')
        
        freequency(freequent_data)
        
        if filetools.exists(PATH_BL):
            bl_data = jsontools.load(filetools.read(PATH_BL))
        else:
            bl_data = {}
        bl_data[domain_full] = time.time()
        if not debug: filetools.write(PATH_BL, jsontools.dump(bl_data))

    msg = 'Detected a Cloudflare version 2 Captcha challenge,\
        This feature is not available in the opensource (free) version.'
    resp.status_code = msg
    
    raise CloudflareChallengeError(msg)


def get_source(url, resp, timeout=5, debug=False, extraPostDelay=5, retry=False, blacklist=True, headers=None, 
               retryIfTimeout=True, cache=False, clearWebCache=False, mute=True, alfa_s=False, elapsed=0, **kwargs):
    blacklist_clear = True
    data = ''
    source = False
    if not elapsed: elapsed = time.time()
    elapsed_max = 40
    expiration = config.get_setting('cf_assistant_bl_expiration', default=30) * 60
    expiration_final = 0
    security_error_blackout = (5 * 60) - expiration
    ua_headers = False
    
    #debug = True
    if debug: alfa_s = False
    
    if not resp:
        resp = {
                'status_code': 429, 
                'headers': {}
               }
        resp = type('HTTPResponse', (), resp)
    
    if not alfa_s: logger.debug("ERROR de descarga: %s" % resp.status_code)
    resp.status_code = 429
    
    opt = kwargs.get('opt', {})
    
    domain_full = urlparse.urlparse(url).netloc
    domain = domain_full
    pcb = base64.b64decode(config.get_setting('proxy_channel_bloqued')).decode('utf-8')
    if 'hideproxy' in url or 'webproxy' in url or 'hidester' in url or '__cpo=' in url  \
                          or httptools.TEST_ON_AIR or domain in pcb:
        blacklist_clear = False
        blacklist = False
    
    if timeout + extraPostDelay > 35: timeout = 20

    if blacklist and not retry: 
        blacklist_clear = check_blacklist(domain_full)
    
    host = config.get_system_platform()[:1]
    freequent_data = [domain, 'Cha,0.0.0,0,%s0,BlakL' % host]
    if blacklist_clear:
        freequent_data = [domain, 'Cha,0.0.0,0,%s0,App' % host]
        if not retry:
            freequent_data[1] += 'KO'
        else:
            freequent_data[1] += 'KO_R'
        
        check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=True, assistantLatestVersion=False)
        if not isinstance(check_assistant, dict) and not retry:
            alfa_assistant.close_alfa_assistant()
            time.sleep(2)
            check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=True, assistantLatestVersion=False)
            logger.debug("Reintento en acceder al Assistant: %s - %s" \
                         % ('OK' if isinstance(check_assistant, dict) else 'ERROR', time.time() - elapsed))
            
        if check_assistant and isinstance(check_assistant, dict):

            if check_assistant.get('assistantLatestVersion') and check_assistant.get('assistantVersion'):
                installed_version = check_assistant['assistantVersion'].split('.')
                available_version = check_assistant['assistantLatestVersion'].split('.')
                newer = False
                for i, ver in enumerate(available_version):
                    if int(ver) > int(installed_version[i]):
                        newer = True
                        break
                    if int(ver) < int(installed_version[i]):
                        break
                if newer:
                    help_window.show_info('cf_2_02', wait=False)

            if headers and isinstance(headers, dict) and headers.get('User-Agent', ''):
                ua = headers.pop('User-Agent', '')
                ua_headers = True
            else:
                ua = get_ua(check_assistant)
            
            try:
                vers = int(scrapertools.find_single_match(ua, r"Android\s*(\d+)"))
            except:
                vers = 0

            wvbVersion = check_assistant.get('wvbVersion', '0.0.0').split('.')[0]
            if len(wvbVersion) > 3: wvbVersion = wvbVersion[:2]
            freequent_data[1] = 'Cha,%s,%s,%s%s,' % (check_assistant.get('assistantVersion', '0.0.0'), wvbVersion, host, vers)
            if not retry:
                freequent_data[1] += 'Src'
            else:
                freequent_data[1] += 'Src_R'

            if not ua_headers:
                if vers:
                    dan = {'User-Agent': ua}
                    resp.headers.update(dict(dan))
                    ua = None
                else:
                    ua = httptools.get_user_agent()

            if not alfa_s: logger.debug("UserAgent: %s || Android Vrs: %s" % (ua, vers))

            jscode = None

            url_cf = scrapertools.find_single_match(url, '(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?') + '|cf_clearance'
            
            data_assistant = alfa_assistant.get_source_by_page_finished(url, timeout=timeout, getCookies=True, userAgent=ua,
                                                                        disableCache=cache, debug=debug, jsCode=jscode,
                                                                        extraPostDelay=extraPostDelay, clearWebCache=clearWebCache, 
                                                                        removeAllCookies=True, returnWhenCookieNameFound=url_cf,
                                                                        retryIfTimeout=retryIfTimeout, useAdvancedWebView=True, 
                                                                        headers=headers, mute=mute, alfa_s=alfa_s)
            if not alfa_s: logger.debug("data assistant: %s" % data_assistant)
            
            if isinstance(data_assistant, dict) and data_assistant.get('htmlSources', []) \
                                                and data_assistant['htmlSources'][0].get('url', ''):
                for html_source in data_assistant['htmlSources']:
                    if html_source.get('url', '') != url:
                        if not alfa_s: logger.debug('Url ignored: %s' % html_source.get('url', ''))
                        continue
                    if not alfa_s: logger.debug('Url accepted: %s' % html_source.get('url', ''))
                    try:
                        data = base64.b64decode(html_source.get('source', ''))
                        if PY3 and isinstance(data, bytes):
                            data = "".join(chr(x) for x in bytes(data))
                        source = True
                    except:
                        logger.error(traceback.format_exc(1))
                        continue
                        
                    if source and 'accessing a cross-origin frame' in data:
                        source = False
                        retry = True
                        expiration_final = security_error_blackout
                        freequent_data[1] = 'Cha,%s,%s,%s%s,' % (check_assistant.get('assistantVersion', '0.0.0'), wvbVersion, host, vers)
                        freequent_data[1] += 'KO_SecE'
                        logger.error('Error SEGURIDAD: %s - %s' % (expiration_final, data[:100]))
                    
                    elif source:
                        resp.status_code = 200
                        freequent_data[1] = 'Cha,%s,%s,%s%s,' % (check_assistant.get('assistantVersion', '0.0.0'), wvbVersion, host, vers)
                        if not retry:
                            freequent_data[1] += 'OK'
                        else:
                            freequent_data[1] += 'OK_R'
                        break
                    
            if not source and not retry:
                config.set_setting('cf_assistant_ua', '')
                logger.debug("No se obtuvieron resultados, reintentando...")
                timeout = -1 if timeout < 0 else timeout * 2
                extraPostDelay = -1 if extraPostDelay < 0 else extraPostDelay * 2
                return get_source(url, resp, timeout=timeout, debug=debug, extraPostDelay=extraPostDelay, 
                                  retry=True, blacklist=blacklist, retryIfTimeout=retryIfTimeout, 
                                  cache=cache, clearWebCache=clearWebCache, alfa_s=False, 
                                  headers=headers, mute=mute, elapsed=elapsed, **kwargs)

            domain_ = domain
            split_lst = domain.split(".")

            if len(split_lst) > 2:
                domain = domain.replace(split_lst[0], "")
            
            if not domain.startswith('.'):
                domain = "."+domain
            
            get_ua(data_assistant)

            if isinstance(data_assistant, dict) and data_assistant.get("cookies", None):

                if not alfa_s: logger.debug("Lista cookies: %s" % data_assistant.get("cookies", []))
                for cookie in data_assistant["cookies"]:
                    cookieslist = cookie.get("cookiesList", '')
                    val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([A-z0-9_\-\.]+)')
                    #val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([^;]+)')
                    dom = cookie.get("urls", [])
                    if not alfa_s: logger.debug("dominios: %s" % dom[0])

                    if 'cf_clearance' in cookieslist and val:
                        
                        dict_cookie = {'domain': domain,
                                       'name': 'cf_clearance',
                                       'value': val}
                        if domain_ in dom[0]:
                            httptools.set_cookies(dict_cookie)
                            rin = {'Server': 'Alfa'}

                            resp.headers.update(dict(rin))
                            freequent_data[1] += 'C'
                            resp.status_code = 201
                            if not alfa_s: logger.debug("cf_clearence=%s" % val)

        elif host == 'a':
            help_window.show_info('cf_2_01')
        
    freequency(freequent_data)

    if blacklist_clear and (not source or time.time() - elapsed > elapsed_max):
        if filetools.exists(PATH_BL):
            bl_data = jsontools.load(filetools.read(PATH_BL))
        else:
            bl_data = {}
        if time.time() - elapsed > elapsed_max:
            bl_data[domain_full] = time.time() + elapsed_max * 10 * 60
        else:
            bl_data[domain_full] = time.time() + expiration_final
        if not debug and not httptools.TEST_ON_AIR: filetools.write(PATH_BL, jsontools.dump(bl_data))
    
    return data, resp


def get_ua(data_assistant):
    
    if not data_assistant or not isinstance(data_assistant, dict):
        return 'Default'
    
    UA = data_assistant.get("userAgent", 'Default')
    
    if UA == httptools.get_user_agent():
        UA = 'Default'

    config.set_setting('cf_assistant_ua', UA)

    return UA


def get_jscode(count, key, n_iframe, timeout=3):
    
    count = str(count)
    focus = str(n_iframe)
    timeout = str(timeout * 1000)

    js = '''((() => {

    const KEYCODE_ENTER = 'KEYCODE_ENTER';
    const KEYCODE_TAB = 'KEYCODE_TAB';

    function sendKeyAfterNTabs(count, key) {
        try {
            for (var i = 0; i <= count; i++) {
                if (i > 0) {
                    alfaAssistantAndroidPI.sendKey(KEYCODE_TAB);
                }
                if (i == count) {
                    alfaAssistantAndroidPI.sendKey(key);
                    break;
                }
            }
        } catch (e) {
            console.error('##Error sending key ' + key, e);
        };
    };

   function setFocusToIframeNumber(nmb) {
    document.querySelectorAll('iframe')[nmb - 1].focus();
   }
    try {

        setFocusToIframeNumber('''+ focus +''');

        sendKeyAfterNTabs('''+ count +''', '''+ key +''');

        setTimeout(function() { 
            window.location.href = alfaAssistantAndroidPI.getMainURL();
            }, '''+ timeout +''');
    }
    catch(e){
            console.error('##Error focus ', e);
        };
}))();
'''
    return js


def freequency(freequent_data):
    import threading

    try:
        threading.Thread(target=alfaresolver.frequency_count, args=(Item(), [], freequent_data)).start()
        ret = True
    except:
        logger.error(traceback.format_exc())


def check_blacklist(domain, expiration=0):
    res = True
    if not filetools.exists(PATH_BL):
        return res
    
    try:
        expiration_default = 30
        bl_data = jsontools.load(filetools.read(PATH_BL))
        bl_data_clean = bl_data.copy()
        if not expiration:
            expiration = config.get_setting('cf_assistant_bl_expiration', default=expiration_default) * 60
            config.set_setting('cf_assistant_bl_expiration', expiration_default)
            expiration = expiration_default * 60
        else:
            expiration = expiration * 60
        time_today = time.time()
        
        if bl_data:
            for domain_reg, time_rec in list(bl_data_clean.items()):
                if time_today > time_rec + expiration:
                    del bl_data[domain_reg]
            filetools.write(PATH_BL, jsontools.dump(bl_data))
            for domain_reg, time_rec in list(bl_data.items()):
                if domain in domain_reg:
                    res = False
                    break
            else:
                res = True
    except:
        logger.error(traceback.format_exc())
        filetools.remove(PATH_BL)
        res = True

    return res
