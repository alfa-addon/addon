# -*- coding: utf-8 -*-
# --------------------------------------------------------
# alfa_assistant tools v. 1.0.376 (07/09/2020)
# --------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import base64
import json
import re
import xbmc

from platformcode import config
from core import httptools
from platformcode import logger
if not PY3:
    from lib import alfaresolver
else:
    from lib import alfaresolver_py3 as alfaresolver


EXTRA_TIMEOUT = 10000

ASSISTANT_SERVER = "http://127.0.0.1"

isAlfaAssistantOpen = False

if config.get_setting("assistant_mode") == "otro":
    if config.get_setting("assistant_custom_address"):
        ASSISTANT_SERVER = "http://%s" % config.get_setting("assistant_custom_address")


JS_CODE_CLICK_ON_VJS_BIG_PLAY_BUTTON = """
((() => { 
    try {
        document.documentElement.getElementsByClassName('vjs-big-play-button')[0].click();
    } catch (e) {
        console.error('##Error getting vjs-big-play-button', e);
    };
}))();
"""

JS_CODE_CLICK_ON_JWPLAYER = """
((() => {
    try {
        document.documentElement.getElementsByClassName('jwplayer')[0].click();
    } catch (e) {
        console.error('##Error getting jwplayer', e);
    };
}))();
"""

## Comunica con el navegador Alfa Assistant ##################################################################################################################################
#
# Recupera el código fuente de los recursos visitados y las URLS
#
def get_source_by_page_finished(url=None, timeout=None, jsCode=None, jsDirectCodeNoReturn=None, jsDirectCode2NoReturn=None, extraPostDelay=None, userAgent=None, debug=None, headers=None, malwareWhiteList=None, disableCache = None, closeAfter = None, getData = None, postData = None):
    return get_generic_call('getSourceByPageFinished', url, timeout, jsCode, jsDirectCodeNoReturn, jsDirectCode2NoReturn, extraPostDelay, userAgent, debug, headers, malwareWhiteList, disableCache, closeAfter, getData, postData)
##############################################################################################################################################################################

## Comunica con el navegador Alfa Assistant ##################################################################################################################################
#
# Recupera las URLS de los recursos visitados
#
def get_urls_by_page_finished(url=None, timeout=None, jsCode=None, jsDirectCodeNoReturn=None, jsDirectCode2NoReturn=None, extraPostDelay=None, userAgent=None, debug=None, headers=None, malwareWhiteList=None, disableCache = None, closeAfter = None, getData = None, postData = None):
    return get_generic_call('getUrlsByPageFinished', url, timeout, jsCode, jsDirectCodeNoReturn, jsDirectCode2NoReturn, extraPostDelay, userAgent, debug, headers, malwareWhiteList, disableCache, closeAfter, getData, postData)
##############################################################################################################################################################################

## Comunica con el navegador Alfa Assistant ##################################################################################################################################
#
# [Uso de parámetros]
#
# - Dirección Web done Assistant va a navegar (GET) usando "url". Para usar POST ver "postData". El audio de la Web se silenciará para no molestar al usuario.
#   Ejemplo:
#       url = "https://www.myhost.com"
#
# - Configurar tiempo extra de espera tras la carga de la Web (para permitir que JS realice tareas).
#   Ejemplo (milisegundos):
#       timeout = 1000
#
# - Envío de datos JSON a través de POST usando "postData".
#   Ejemplo:
#       postData = '''{"jsonKey1":"jsonValue1", "jsonKey2":"jsonValue2"}'''
#
# - Envío de datos de formulario a través de POST usando "postData".
#   Ejemplo:
#       postData = '''formKey1=formValue1&formkey2=formValue2'''
#
# - Envío de datos de formulario a través de GET usando "getData": mismos ejemplos de uso que "postData".
#
# - Configurar "UserAgent" para TODA la navegación en Assistant.
#   Ejemplo:
#       userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
#
# - Añadir "headers" a la URL inicial. El User Agent no se debería indicar aquí pues solo valdría para la URL inicial y no el resto (usar mejor parámetro "useAgent").
#   Ejemplo:
#       headers = '''[
#       {"name": "referer", "value": "https://www.myWebsite.com/"},
#       {"name": "otherKey", "value": "otherValue"},
#       ]'''
#
# - Ejecución de Javascript (CON retorno opcional) usando "jsCode".
#   Ejemplo:
#       jsCode = """
#           ((() => {
#               try {
#                   document.documentElement.getElementsByClassName('myClass')[0].click();
#                   return 'OK';    //LÍNEA OPCIONAL!!
#               } catch (e) {
#                   console.error('##Error getting jwplayer', e);
#                   return 'KO';    //LÍNEA OPCIONAL!!
#               };
#           }))();
#       """
#
# - Ejecución de Javascript SIN retorno usando "jsDirectCodeNoReturn": mismo uso y ejemplos que jsCode pero sin "return".
#
# - Ejecución de Javascript SIN retorno usando jsDirectCode2NoReturn: mismo uso y ejemplos que jsCode pero sin "return".
#
# - Espera tras ejecución de JS (o sea tras "jsCode", "jsDirectCodeNoReturn" o "jsDirectCode2NoReturn") usando "extraPostDelay".
#   Ejemplo (milisegundos):
#       extraPostDelay = 1000
#
# - Por defecto y para acelerar las consultas repetitivas, Assistant usa caché de respuestas (con caducidad de 24 horas).
#   Ejemplo de desactivación:
#       disableCache = True
#
# - Cierre automático de Assistant tras su uso (sino queda abierto -aunque no en primer plano sino de fondo-).
#   Ejemplo de cierre tras uso de Assistant:
#       closeAfter = True
#
# - Assistant filtra los recursos que se intentan usar en la navegación a partir de varios repositorios online anti-malware, anti-mining, etc. Se pueden añadir exclusiones a esta lista a través del parámetro "malwareWhiteList" (usando Regex de tipo Java).
#   Ejemplo:
#       malwareWhiteList = '''[
#       ".*google.*com",
#       ".*yahoo.*com",
#       ]'''
#
#
#
# - NUNCA USAR EN PRODUCCIÓN: PARA AYUDAR A LOS DESARROLLADORES se puede mostrar lo que el navegador Assistant está haciendo. Cuidado: ni limpia recursos ni se cierra, además se puede incluso oir el audio de la Web visitada.
#   Ejemplo de activación de depuración:
#       debug = true
#
def get_generic_call(endpoint, url=None, timeout=None, jsCode=None, jsDirectCodeNoReturn=None, jsDirectCode2NoReturn=None, extraPostDelay=None, userAgent=None, debug=None, headers=None, malwareWhiteList=None, disableCache = None, closeAfter = None, getData = None, postData = None):
    open_alfa_assistant(closeAfter)
    logger.info('##Assistant Endpoint: %s' % endpoint)
    if url:
        logger.info('##Assistant URL: %s' % url)
    else:
        url = 'about:blank'
    if timeout:
        logger.info('##Assistant delay-after-html-load: %s' % timeout)
    else:
        timeout = 0
    serverCall = '%s:48884/%s?url=%s&time=%s' % (ASSISTANT_SERVER, endpoint, base64.b64encode(url), timeout)
    if jsCode:
        serverCall += '&jsCode=%s' % base64.b64encode(jsCode)
        logger.info('##Assistant js-to-run-directly-with-return: %s' % jsCode)
    if jsDirectCodeNoReturn:
        serverCall += '&jsDirectCodeNoReturn=%s' % base64.b64encode(jsDirectCodeNoReturn)
        logger.info('##Assistant js-to-run-directly-with-no-return(type I): %s' % jsDirectCodeNoReturn)
    if jsDirectCode2NoReturn:
        serverCall += '&jsDirectCode2NoReturn=%s' % base64.b64encode(jsDirectCode2NoReturn)
        logger.info('##Assistant js-to-run-directly-with-no-return(type II): %s' % jsDirectCode2NoReturn)
    if extraPostDelay:
        serverCall += '&extraPostDelay=%s' % extraPostDelay
        logger.info('##Assistant delay-after-js-load: %s' % extraPostDelay)
    if userAgent:
        serverCall += '&userAgent=%s' % base64.b64encode(userAgent)
        logger.info('##Assistant user-agent: %s' % userAgent)
    if debug:
        serverCall += '&debug=%s' % debug
        logger.info('##Assistant debug-mode: %s' % debug)
    ## Por defecto se usa la caché pero en casos como mixdrop es mejor no usarla
    if disableCache:
        serverCall += '&cache=false'
        logger.info('##Assistant cache: False')
    if headers:
        serverCall += '&headers=%s' % base64.b64encode(headers)
        logger.info('##Assistant headers: %s' % headers)
    if malwareWhiteList:
        serverCall += '&malwareWhiteList=%s' % base64.b64encode(malwareWhiteList)
        logger.info('##Assistant malware-white-list: %s' % malwareWhiteList)
    if getData:
        serverCall += '&getData=%s' % base64.b64encode(getData)
        logger.info('##Assistant get-data: %s' % getData)
    if postData:
        serverCall += '&postData=%s' % base64.b64encode(postData)
        logger.info('##Assistant post-data: %s' % postData)

    logger.info('##Assistant Alfa Assistant URL: ' + serverCall)
    data = httptools.downloadpage(serverCall, timeout=timeout + EXTRA_TIMEOUT).data

    #if closeAfter:
    #    close_alfa_assistant()

    if data:
        return string_to_json(data)
    else:
        return data
##############################################################################################################################################################################


def string_to_json(data):
    return json.loads(data)

#
# Lista el código fuente (decodificado) según filtro regex (parámetro "pattern") entre los datos que devuelve el navegador Alfa Assistant (parámetro "data")
#
def find_htmlsource_by_url_pattern(data, pattern):
    if not data:
        logger.info('##Assistant NOT received data from Alfa Mobile Helper')
    else:
        logger.info('##Assistant Received data from Alfa Mobile Helper')
        if data['htmlSources'] and len(data['htmlSources']) > 1:
            for attrs in data['htmlSources']:
                if re.search(pattern, attrs['url']):
                    logger.info('##Assistant iFrame URL found: ' + attrs['url'])
                    return {
                        'url': attrs['url'],
                        'source': base64.b64decode(attrs['source'])
                    }
                else:
                    logger.info('##Assistant The data found in Alfa Assistant has not the right info')
    return

#
# Prepara en una línea los argumentos necesarios para constituir una URL a partir de una lista que proviene de consultar Alfa Assistant
# Ejemplo:
#   from lib import alfa_assistant
#   data_assistant = alfa_assistant.get_urls_by_page_finished(global_url, 1000, jsDirectCode2NoReturn=js_code, extraPostDelay=2000, userAgent=ua, disableCache=True, closeAfter=True)
#   for visited in data_assistant["urlsVisited"]:
#       url = visited["url"] + alfa_assistant.getInlineRequestedHeaders(visited["requestHeaders"], [])
#
def getInlineRequestedHeaders(requestHeaders, namesExceptionList = None):
    res = ""
    try:
        count = 0
        if requestHeaders:
            for requestHeader in requestHeaders:
                name = requestHeader["name"]
                if not namesExceptionList or name not in namesExceptionList:
                    value = requestHeader["value"]
                    if count == 0:
                        res += "|%s=%s" % (name, value)
                    else:
                        res += "&%s=%s" % (name, value)
                    count += 1

    except:
        logger.error('##Assistant getInlineRequestedHeaders Error')
        pass

    return res    #Ejemplo: |param1=value1&param2=value2


##############################################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################
## F U N C I O N E S   D E   B A J O   N I V E L #############################################################################################################################
################# NO TOCAR ###################################################################################################################################################
##############################################################################################################################################################################
##############################################################################################################################################################################

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def open_alfa_assistant(closeAfter = None):
    global isAlfaAssistantOpen
    if not isAlfaAssistantOpen:
        try:
            if (ASSISTANT_SERVER == "http://127.0.0.1" or ASSISTANT_SERVER == "http://localhost") and is_alfa_installed():
                logger.info('##Assistant Open Assistant at ' + ASSISTANT_SERVER)

                if closeAfter:
                    res = execute_in_alfa_assistant_with_cmd('openAndQuit')
                    isAlfaAssistantOpen = True
                else:
                    res = execute_in_alfa_assistant_with_cmd('open')
                    isAlfaAssistantOpen = True
                import time
                time.sleep(3)
                return res

            else:
                logger.info('##Assistant Assistant don\'t need to be open if not local. IP: ' + ASSISTANT_SERVER)
        except:
            logger.error('##Assistant Error opening it')
            pass
    else:
        logger.info('##Assistant Already was Assistant')

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def close_alfa_assistant():
    global isAlfaAssistantOpen
    isAlfaAssistantOpen = False
    try:
        if (ASSISTANT_SERVER == "http://127.0.0.1" or ASSISTANT_SERVER == "http://localhost") and is_alfa_installed():
            return get_generic_call('quit')
        else:
            logger.info('##Assistant Assistant don\'t need to be closed if not local. IP: ' + ASSISTANT_SERVER)
    except:
        logger.error('##Assistant Error closing Assistant')
        pass

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def is_alfa_installed(remote=''):
    respuesta, app_name = alfaresolver.install_alfa_assistant(update=False, remote=remote)
    return respuesta

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def update_alfa_assistant(remote=''):
    #return execute_in_alfa_assistant_with_cmd('update')
    return alfaresolver.install_alfa_assistant(update=True, remote=remote)

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def check_permissions_alfa_assistant():
    return execute_in_alfa_assistant_with_cmd('checkPermissions')

#
## Comunica DIRECTAMENTE con el navegador Alfa Assistant ##################################################################################################################################
#
def execute_in_alfa_assistant_with_cmd(cmd):
    if xbmc.getCondVisibility("system.platform.Android"):
        # try:
        #     ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
        # except:
        #     ANDROID_STORAGE = ''
        # if not ANDROID_STORAGE:
        #     if "'HOME'" in os.environ:
        #         ANDROID_STORAGE = scrapertools.find_single_match(os.getenv('HOME'), '^(\/.*?)\/')
        #         if not ANDROID_STORAGE:
        #             ANDROID_STORAGE = '/storage'
        #     else:
        #         ANDROID_STORAGE = '/storage'

        # path = '/emulated/0/Android/data/com.alfa.alfamobilehelper'
        # xbmc.executebuiltin("StartAndroidActivity(%s,,,%s)" % ('com.alfa.alfamobilehelper', 'open'))
        # xbmc.executebuiltin("StartAndroidActivity(%s,,,%s)" % (filetools.basename(path), 'open'))
        # xbmc.executebuiltin("StartAndroidActivity(%s,%s,,%s)" % ('com.alfa.alfamobilehelper', 'android.intent.action.VIEW', 'open'))
        try:
            app = 'com.alfa.alfamobileassistant'
            intent = ''  # com.alfa.alfamobilehelper.MainActivity'
            dataType = cmd
            # dataType = 'openForDebug'
            dataURI = 'about:blank'
            cmd = 'StartAndroidActivity("%s", "%s", "%s", "%s")' % (app, intent, dataType, dataURI)
            xbmc.executebuiltin(cmd)
            return True
        except:
            return False
