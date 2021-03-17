#from future import standard_library
#standard_library.install_aliases()
from future.builtins import map
#from future.builtins import str
from future.builtins import range

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.request as urllib2
else:
    import urllib2

import os
import re
import stat
import time
import xbmc
import shutil
import socket
import xbmcgui
import threading
import subprocess
import xbmcvfs
from quasar.logger import log
from quasar.osarch import PLATFORM
from quasar.config import QUASARD_HOST
from quasar.addon import ADDON, ADDON_ID, ADDON_PATH
from quasar.util import notify, system_information, getLocalizedString, getWindowsShortPath

def translatePath(path):
    """
    Kodi 19: xbmc.translatePath is deprecated and might be removed in future kodi versions. Please use xbmcvfs.translatePath instead.
    @param path: cadena con path special://
    @type path: str
    @rtype: str
    @return: devuelve la cadena con el path real
    """
    if PY3:
        if isinstance(path, bytes):
            path = path.decode('utf-8')
        path = xbmcvfs.translatePath(path)
        if isinstance(path, bytes):
            path = path.decode('utf-8')
    else:
        path = xbmc.translatePath(path)
    return path

def ensure_exec_perms(file_):
    st = os.stat(file_)
    os.chmod(file_, st.st_mode | stat.S_IEXEC)
    return file_

def android_get_current_appid():
    with open("/proc/%d/cmdline" % os.getpid()) as fp:
        return fp.read().rstrip("\0")

def get_quasard_checksum(path):
    try:
        with open(path) as fp:
            fp.seek(-40, os.SEEK_END)  # we put a sha1 there
            return fp.read()
    except Exception:
        return ""

def get_quasar_binary():
    binary = "quasar" + (PLATFORM["os"] == "windows" and ".exe" or "")

    log.info("PLATFORM: %s" % str(PLATFORM))
    binary_dir = os.path.join(ADDON_PATH, "resources", "bin", "%(os)s_%(arch)s" % PLATFORM)
    if PLATFORM["os"] == "android":
        log.info("Detected binary folder: %s" % binary_dir)
        binary_dir_legacy = binary_dir.replace("/storage/emulated/0", "/storage/emulated/legacy")
        if os.path.exists(binary_dir_legacy):
            binary_dir = binary_dir_legacy
        app_id = android_get_current_appid()
        xbmc_data_path = os.path.join("/data", "data", app_id, 'files', 'quasar')
        log.info("Trying binary Kodi folder: %s" % xbmc_data_path)
        
        try:                    #Test if there is any permisions problem
            if not os.path.exists(xbmc_data_path):
                os.makedirs(xbmc_data_path)
        except Exception as e:
            log.info("ERROR %s in binary Kodi folder: %s" % (str(e), xbmc_data_path))
            xbmc_data_path = ''
        
        if not os.path.exists(xbmc_data_path):
            log.info("Trying alternative binary Kodi folder: %s" % \
                        (xbmc_data_path, translatePath("special://xbmcbin/").replace('cache/apk/assets', 'files/quasar')))
            xbmc_data_path = translatePath("special://xbmcbin/").replace('cache/apk/assets', 'files/quasar')

            try:                    #Test if there is any permisions problem
                if not os.path.exists(xbmc_data_path):
                    os.makedirs(xbmc_data_path)
            except Exception as e:
                log.info("ERROR %s in alternative binary Kodi folder: %s" % (str(e), xbmc_data_path))
                xbmc_data_path = ''

        dest_binary_dir = xbmc_data_path
    else:
        if not PY3:
            dest_binary_dir = os.path.join(translatePath(ADDON.getAddonInfo("profile")).decode('utf-8'), "bin", "%(os)s_%(arch)s" % PLATFORM)
        else:
            dest_binary_dir = os.path.join(translatePath(ADDON.getAddonInfo("profile")), "bin", "%(os)s_%(arch)s" % PLATFORM)
    
    if PY3 and isinstance(dest_binary_dir, bytes):
        dest_binary_dir = dest_binary_dir.decode("utf8")
    log.info("Using destination binary folder: %s" % dest_binary_dir)
    binary_path = os.path.join(binary_dir, binary)
    dest_binary_path = os.path.join(dest_binary_dir, binary)

    if not os.path.exists(binary_path):
        notify((getLocalizedString(30103) + " %(os)s_%(arch)s" % PLATFORM), time=7000)
        system_information()
        try:
            log.info("Source directory (%s):\n%s" % (binary_dir, os.listdir(os.path.join(binary_dir, ".."))))
            log.info("Destination directory (%s):\n%s" % (dest_binary_dir, os.listdir(os.path.join(dest_binary_dir, ".."))))
        except Exception:
            pass
        return False, False

    if os.path.isdir(dest_binary_path):
        log.warning("Destination path is a directory, expected previous binary file, removing...")
        try:
            shutil.rmtree(dest_binary_path)
        except Exception as e:
            log.error("Unable to remove destination path for update: %s" % e)
            system_information()
            return False, False

    if not os.path.exists(dest_binary_path) or get_quasard_checksum(dest_binary_path) != get_quasard_checksum(binary_path):
        log.info("Updating quasar daemon...")
        try:
            os.makedirs(dest_binary_dir)
        except OSError:
            pass
        try:
            shutil.rmtree(dest_binary_dir)
        except Exception as e:
            log.error("Unable to remove destination path for update: %s" % e)
            system_information()
            pass
        try:
            shutil.copytree(binary_dir, dest_binary_dir)
        except Exception as e:
            log.error("Unable to copy to destination path for update: %s" % e)
            system_information()
            return False, False

    # Clean stale files in the directory, as this can cause headaches on
    # Android when they are unreachable
    dest_files = set(os.listdir(dest_binary_dir))
    orig_files = set(os.listdir(binary_dir))
    log.info("Deleting stale files %s" % (dest_files - orig_files))
    for file_ in (dest_files - orig_files):
        path = os.path.join(dest_binary_dir, file_)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    return dest_binary_dir, ensure_exec_perms(dest_binary_path)

def clear_fd_inherit_flags():
    # Ensure the spawned quasar binary doesn't inherit open files from Kodi
    # which can break things like addon updates. [WINDOWS ONLY]
    
    try:
        from ctypes import windll
    except:
        log.error("Error clearing inherit flag, disk file handle. NO CTYPES")
        return

    HANDLE_RANGE = list(range(0, 65536))
    HANDLE_FLAG_INHERIT = 1
    FILE_TYPE_DISK = 1

    for hd in HANDLE_RANGE:
        if windll.kernel32.GetFileType(hd) == FILE_TYPE_DISK:
            if not windll.kernel32.SetHandleInformation(hd, HANDLE_FLAG_INHERIT, 0):
                log.error("Error clearing inherit flag, disk file handle %x" % hd)


def jsonrpc_enabled(notify=False):
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 9090))
        s.close()
        log.info("Kodi's JSON-RPC service is available, starting up...")
        del s
        return True
    except Exception as e:
        log.error(repr(e))
        if notify:
            xbmc.executebuiltin("ActivateWindow(ServiceSettings)")
            dialog = xbmcgui.Dialog()
            dialog.ok("Quasar", getLocalizedString(30199))
    return False

def start_quasard(**kwargs):
    jsonrpc_failures = 0
    while jsonrpc_enabled() is False:
        jsonrpc_failures += 1
        log.warning("Unable to connect to Kodi's JSON-RPC service, retrying...")
        if jsonrpc_failures > 1:
            time.sleep(5)
            if not jsonrpc_enabled(notify=True):
                log.error("Unable to reach Kodi's JSON-RPC service, aborting...")
                return False
            else:
                break
        time.sleep(3)

    quasar_dir, quasar_binary = get_quasar_binary()

    if quasar_dir is False or quasar_binary is False:
        return False

    lockfile = os.path.join(ADDON_PATH, ".lockfile")
    if os.path.exists(lockfile):
        log.warning("Existing process found from lockfile, killing...")
        try:
            with open(lockfile) as lf:
                pid = int(lf.read().rstrip(" \t\r\n\0"))
            os.kill(pid, 9)
        except Exception as e:
            log.error(repr(e))

        if PLATFORM["os"] == "windows":
            log.warning("Removing library.db.lock file...")
            try:
                if not PY3:
                    library_lockfile = os.path.join(translatePath(ADDON.getAddonInfo("profile")).decode('utf-8'), "library.db.lock")
                else:
                    library_lockfile = os.path.join(translatePath(ADDON.getAddonInfo("profile")), "library.db.lock")
                    if isinstance(library_lockfile, bytes):
                        library_lockfile = library_lockfile.decode("utf8")
                os.remove(library_lockfile)
            except Exception as e:
                log.error(repr(e))

    SW_HIDE = 0
    STARTF_USESHOWWINDOW = 1

    args = [quasar_binary]
    kwargs["cwd"] = quasar_dir

    if PLATFORM["os"] == "windows":
        args[0] = getWindowsShortPath(quasar_binary)
        kwargs["cwd"] = getWindowsShortPath(quasar_dir)
        si = subprocess.STARTUPINFO()
        si.dwFlags = STARTF_USESHOWWINDOW
        si.wShowWindow = SW_HIDE
        clear_fd_inherit_flags()
        kwargs["startupinfo"] = si
    else:
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "%s:%s" % (quasar_dir, env.get("LD_LIBRARY_PATH", ""))
        kwargs["env"] = env
        kwargs["close_fds"] = True

    wait_counter = 1
    while xbmc.getCondVisibility('Window.IsVisible(10140)') or xbmc.getCondVisibility('Window.IsActive(10140)'):
        if wait_counter == 1:
            log.info('Add-on settings currently opened, waiting before starting...')
        if wait_counter > 300:
            break
        time.sleep(1)
        wait_counter += 1

    return call_binary('openBinary', args, **kwargs)

def shutdown():
    try:
        urllib2.urlopen(QUASARD_HOST + "/shutdown")
    except:
        pass

def wait_for_abortRequested(proc, monitor):
    monitor.closing.wait()
    log.info("quasard: exiting quasard daemon")
    try:
        proc.terminate()
    except OSError:
        pass  # Process already exited, nothing to terminate
    log.info("quasard: quasard daemon exited")

def quasard_thread(monitor):
    crash_count = 0
    try:
        monitor_abort = xbmc.Monitor()  # For Kodi >= 14
        while not monitor_abort.abortRequested():
            log.info("quasard: starting quasard")
            proc = start_quasard(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if not proc:
                break
            threading.Thread(target=wait_for_abortRequested, args=[proc, monitor]).start()
            
            try:
                if proc.app:
                    assistant = True
                else:
                    assistant = False
            except:
                assistant = False
            
            def polling_assistant(proc, monitor):
                while not monitor_abort.abortRequested():
                    while proc.poll() is None:
                        time.sleep(1)
                    break
            if assistant:
                threading.Thread(target=polling_assistant, args=[proc, monitor]).start()

            if PLATFORM["os"] == "windows":
                while proc.poll() is None:
                    log.info(proc.stdout.readline())
            
            elif assistant:
                while proc.poll() is None:
                    for line in iter(proc.stdout.readline, proc.stdout.read(0)):
                        if PY3 and isinstance(line, bytes):
                            line = line.decode()
                        log.info(line)
                    time.sleep(1)
           
            else:
                # Kodi hangs on some Android (sigh...) systems when doing a blocking
                # read. We count on the fact that Quasar daemon flushes its log
                # output on \n, creating a pretty clean output
                import fcntl
                import select
                fd = proc.stdout.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                while proc.poll() is None:
                    try:
                        to_read, _, _ = select.select([proc.stdout], [], [])
                        for ro in to_read:
                            line = ro.readline()
                            if line == "":  # write end is closed
                                break
                    except IOError:
                        time.sleep(1)  # nothing to read, sleep

            log.info("quasard: proc.return code: %s" % str(proc.returncode))
            if proc.returncode == 0 or proc.returncode == -9 or monitor_abort.abortRequested():
                break

            crash_count += 1
            notify(getLocalizedString(30100), time=3000)
            xbmc.executebuiltin("Dialog.Close(all, true)")
            system_information()
            time.sleep(5)
            if crash_count >= 3:
                notify(getLocalizedString(30110), time=3000)
                break

    except Exception as e:
        import traceback
        list(map(log.error, traceback.format_exc().split("\n")))
        if not PY3:
            notify("%s: %s" % (getLocalizedString(30226), repr(e).encode('utf-8')))
        else:
            notify("%s: %s" % (getLocalizedString(30226), repr(e)))
        raise


# Launching Quasar through an external APP for Android >= 10 and Kodi >= 19
def call_binary(function, cmd, retry=False, p=None, **kwargs):
    import xbmc
    import xbmcaddon
    import traceback
    import base64
    import requests
    import time
    import json
    
    # Lets try first the traditional way
    if not p:
        try:
            p = subprocess.Popen(cmd, **kwargs)
            log.info('## Executing Popen.CMD: %s - PID: %s' % (cmd, p.pid))
            return p
        except Exception as e:
            if not PY3:
                e = unicode(str(e), "utf8", errors="replace").encode("utf8")
            elif PY3 and isinstance(e, bytes):
                e = e.decode("utf8")
            log.error('Exception Popen ERROR: %s, %s' % (str(cmd), str(e)))
            
            if PLATFORM["os"] != "android" or 'Errno 13' not in str(e):
                return p

    # The traditional way did not work, so most probably we hit the SDK 29 problem
    APP_PARAMS = {
                  'Quasar':  {
                               'ACTIVE': 0, 
                               'USER_ADDON': 'plugin.video.quasar', 
                               'USER_ADDON_STATUS': xbmc.getCondVisibility('System.HasAddon("plugin.video.quasar")'), 
                               'USER_ADDON_USERDATA': os.path.join(xbmc.translatePath('special://masterprofile/'), 
                                            'addon_data', 'plugin.video.quasar'), 
                               'USER_APK': [os.path.join(xbmc.translatePath('special://xbmcbinaddons/'), 
                                            'plugin.video.quasar', 'resources', 'apk', 
                                            'quasar-mobile-assistant.apk')], 
                               'USER_APP': 'com.quasar.quasarmobileassistant', 
                               'USER_APP_CONTROL': 'quasar-mobile-assistant.version',
                               'USER_APP_URL': 'http://127.0.0.1', 
                               'USER_APP_PORT': '66666'
                              }, 
                  'Alfa':     {
                               'ACTIVE': 1, 
                               'USER_ADDON': 'plugin.video.alfa', 
                               'USER_ADDON_STATUS': xbmc.getCondVisibility('System.HasAddon("plugin.video.alfa")'), 
                               'USER_ADDON_USERDATA': os.path.join(xbmc.translatePath('special://masterprofile/'), 
                                            'addon_data', 'plugin.video.alfa'), 
                               'USER_APK': ['https://github.com/alfa-addon/alfa-repo/raw/master/downloads/assistant/alfa-mobile-assistant.apk',
                                            'https://github.com/alfa-addon/alfa-repo/raw/master/downloads/assistant/alfa-mobile-assistant.version'], 
                               'USER_APP': 'com.alfa.alfamobileassistant', 
                               'USER_APP_CONTROL': 'alfa-mobile-assistant.version',
                               'USER_APP_URL': 'http://127.0.0.1', 
                               'USER_APP_PORT': '48884'
                              }
                  }
    
    QUASAR_ADDON_SETTING = xbmcaddon.Addon()
    USER_APP_URL = ''
    USER_ADDON = ''
    USER_ADDON_STATUS = False
    ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
    if not ANDROID_STORAGE: ANDROID_STORAGE = '/storage'
    USER_APP = ''
    USER_APP_PATH = os.path.join(ANDROID_STORAGE, 'emulated', '0', 'Android', 'data')
    USER_APP_STATUS = False

    for user_addon, user_params in list(APP_PARAMS.items()):
        if not user_params['ACTIVE'] or not user_params['USER_ADDON_STATUS']: continue
        
        if user_addon == 'Quasar':
            try:
                # Quasar add-on and Quasar Assistant installed
                USER_ADDON = user_params['USER_ADDON']
                USER_ADDON_STATUS = True
                if os.path.exists(os.path.join(USER_APP_PATH, user_params['USER_APP'])):
                    USER_APP = user_params['USER_APP']
                    USER_APP_STATUS = True
                    USER_APP_URL = "%s:%s" % (user_params['USER_APP_URL'], user_params['USER_APP_PORT'])
                if USER_APP_STATUS: break
            except:
                log.error(traceback.format_exc())
        
        if user_addon == 'Alfa':
            try:
                try:
                    # Alfa add-on and Alfa Assistant installed
                    USER_ADDON_SETTING = xbmcaddon.Addon(id="%s" % user_params['USER_ADDON'])
                    USER_ADDON = user_params['USER_ADDON']
                    USER_ADDON_STATUS = True
                    if USER_ADDON_SETTING.getSetting('assistant_mode') == 'este' and \
                            os.path.exists(os.path.join(USER_APP_PATH, user_params['USER_APP'])):
                        USER_APP = user_params['USER_APP']
                        USER_APP_STATUS = True
                        if USER_ADDON_SETTING.getSetting('assistant_custom_address'):
                            USER_APP_URL = "http://%s" % USER_ADDON_SETTING.getSetting('assistant_custom_address')
                        else:
                            USER_APP_URL = user_params['USER_APP_URL']
                        USER_APP_URL = "%s:%s" % (USER_APP_URL, user_params['USER_APP_PORT'])
                except:
                    # Only Alfa Assistant installed
                    if os.path.exists(os.path.join(os.path.dirname(xbmc.translatePath(
                            'special://xbmcbinaddons/'), user_params['USER_APP']))):
                        USER_APP_STATUS = True
                if USER_APP_STATUS: break
            except:
                log.error(traceback.format_exc())

    if not USER_APP_STATUS:
        res = install_app(APP_PARAMS)
        if not res:
            raise ValueError("No app:  Must be installed")
        else:
            USER_APP = user_params['USER_APP']
            USER_APP_STATUS = True
            USER_APP_URL = "%s:%s" % (user_params['USER_APP_URL'], user_params['USER_APP_PORT'])

    if USER_APP_STATUS:
        try:
            """
            Assistant APP acts as a CONSOLE for binaries management in Android 10+ and Kodi 19+
            
            Syntax StartAndroidActivity("USER_APP", "", "function", "cmd|arg| ... |arg|||dict{env} in format |key=value|... "):
                  
                  - cmd: binary name in format '$PWD/lib'binary_name'.so'
                  - 'open':                                                     START the Assitant
                  - "OpenBinary", "$PWD/libBINARY.so|-port|61235|-settings|/storage/emulated/.../settings.json|||
                                    (kwargs[env]): |key=value|etc=etc":         CALL binary
            
            Syntax Http requests: http://127.0.0.1:48884/command?option=value
                  
                  - /openBinary?cmd=base64OfFullCommand($PWD/libBINARY.so|-port|61235| 
                                    -settings|/storage/emulated/.../settings.json|||
                                    (kwargs[env]): |key=value|etc=etc):         CALL binary
                          - returns: {
                                      "pid": 999,
                                      "output": "Base64encoded",
                                      "error": "Base64encoded",
                                      "startDate": "Base64encoded(2021-12-13 14:00:12)",
                                      "endDate": "Base64encoded([2021-12-13 14:00:12])",    If ended
                                      "retCode": "0|1|number|None"                          None if not ended
                                      "cmd": "Base64encoded(command *args **kwargs)"        Full command as sent to the app
                                      "finalCmd": "Base64encoded($PWD/command *args)"       Actual command executed vy the app
                                      
                  - /openBinary?cmd=base64OfFullCommand([[ANY Android/Linux command: killall libquasar.so (kills all Quasar binaries)]])
                          - returns: {As in /openBinary?cmd}
                  
                  - /getBinaryStatus?pid=999:                                   Request binary STATUS by PID
                          - returns: {As in /openBinary?cmd}
                  
                  - /killBinary?pid=999:                                        Request KILL binary PID
                          - returns: {As in /openBinary?cmd}

                  - /getBinaryList:                                             Return a /getBinaryStatus per binary launched during app session
                          - returns: {As in /openBinary?cmd}
            """
            
            # Lets start the Assistant app
            separator = '|'
            separator_escaped = '\|'
            separator_kwargs = '|||'
            url = USER_APP_URL + '/openBinary?cmd='
            url_killall = url + base64.b64encode(str('killall%slibquasar.so' % separator).encode('utf8')).decode('utf8')
            if isinstance(p, int):
                url_killall = USER_APP_URL + '/killBinary?pid=%s' % p
            command = []
            status_code = 0
            cmd_android = 'StartAndroidActivity("%s", "", "%s", "%s")' % (USER_APP, 'open', 'about:blank')
            xbmc.executebuiltin(cmd_android)
            time.sleep(3)

            # Build the command & params
            cmd_app = ''
            if isinstance(cmd, list):
                command.append(cmd)
                command.append(kwargs)
                # Convert Args to APP format
                cmd_bis = cmd[:]
                cmd_bis[0] = '$PWD/libquasar.so'
                for args in cmd_bis:
                    cmd_app += args.replace(separator, separator_escaped) + separator
                cmd_app = cmd_app.rstrip(separator)
                # Convert Kwargs to APP format
                if kwargs.get('env', {}):
                    cmd_app += separator_kwargs
                for key, value in list(kwargs.get('env', {}).items()):
                    if key == 'LD_LIBRARY_PATH':
                        # The app will replace $PWD by the binary/lib path
                        value = '$PWD'
                    cmd_app += '%s=%s%s' % (key.replace(separator, separator_escaped), value.replace(separator, separator_escaped), separator)
                cmd_app = cmd_app.rstrip(separator)
                command_base64 = base64.b64encode(cmd_app.encode('utf8')).decode('utf8')
            else:
                command_base64 = cmd
                cmd = p.args_
                kwargs = p.kwargs_
                command.append(cmd)
                command.append(kwargs)

            # Launch the Binary
            try:
                session = requests.Session()
                # First, cancel existing Binary sessions
                log.info('## Killing Quasar from Assistant App')
                resp = session.get(url_killall, timeout=5)
                time.sleep(1)
                # Now lets launch the Binary
                log.info('## Calling Quasar from Assistant App: %s - Retry = %s' % (cmd, retry))
                resp = session.get(url+command_base64, timeout=5)
            except Exception as e:
                resp = requests.Response()
                resp.status_code = str(e)
            status_code = resp.status_code
            if status_code != 200 and not retry:
                log.error("## Calling Quasar: Invalid app requests response: %s" % status_code)
                time.sleep(3)
                return call_binary(function, cmd, retry=True, **kwargs)
            elif status_code != 200 and retry:
                log.error("## Calling Quasar: Invalid app requests response: %s" % status_code)
                raise ValueError("No app response:  error code: %s" % status_code)
            try:
                app_response = resp.content
                if PY3 and isinstance(app_response, bytes):
                    app_response = app_response.decode()
                app_response = re.sub('\n|\r|\t', '', app_response)
                app_response = json.loads(app_response)
            except:
                status_code = resp.content
                raise ValueError("Invalid app response: %s" % resp.content)

            # Simulate the response from subprocess.Popen
            pipeout, pipein = os.pipe()
            class Proc:
                pid = 0
                stdout = os.fdopen(pipeout, 'rb')
                stdin = os.fdopen(pipein, 'wb')
                stderr = stdout
                returncode = None
                startDate = ''
                endDate = ''
                poll = ''
                terminate = ''
                communicate = ''
                app = USER_APP
                url_app = USER_APP_URL
                cmd_app = command_base64
                finalCmd = ''
                sess = session
                args_ = cmd
                kwargs_ = kwargs
            
            p = Proc()
            
            def redirect_terminate(p=p, action='killBinary'):
                return binary_stat(p, action)
            def redirect_poll(p=p, action='poll'):
                return binary_stat(p, action)
            def redirect_communicate(p=p, action='communicate'):
                return binary_stat(p, action)
            p.poll = redirect_poll
            p.terminate = redirect_terminate
            p.communicate = redirect_communicate
            try:
                p.pid = int(app_response['pid'])
            except:
                raise ValueError("No valid PID returned:  PID code: %s" % resp.content)
            
            # Handle initial messages
            time.sleep(2)
            if app_response.get('output') or app_response.get('error'):
                res = binary_stat(p, 'poll', app_response=app_response)
            else:
                for x in range(20):
                    res = binary_stat(p, 'poll', init=True)
                    if res: break
                    time.sleep(1)
                else:
                    # Is the binary hung?  Lets restart it
                    return call_binary(function, command_base64, retry=True, kwargs={})

            log.info('## Assistant executing CMD: %s - PID: %s' % (command[0], p.pid))
            #log.warning('## Assistant executing CMD **kwargs: %s' % command[1])
        except:
            log.info('## Assistant ERROR %s in CMD: %s%s' % (status_code, url, command))
            log.error(traceback.format_exc())
            p = None
            
    return p

def binary_stat(p, action, retry=False, init=False, app_response={}):
    if init: log.info('## Binary_stat: action: %s; PID: %s; retry: %s; init: %s; app_r: %s' % (action, p.pid, retry, init, app_response))
    import traceback
    import base64
    import requests
    import json
    import time
    import xbmc
    
    try:
        if action in ['poll', 'communicate']:
            url = p.url_app + '/getBinaryStatus?pid=%s&flushAfterRead=true' % str(p.pid)

        if action == 'killBinary':
            url = p.url_app + '/killBinary?pid=%s' % str(p.pid)

        cmd_android = 'StartAndroidActivity("%s", "", "%s", "%s")' % (p.app, 'open', 'about:blank')
        cmd_android_permissions = 'StartAndroidActivity("%s", "", "%s", "%s")' % (p.app, 'checkPermissions', 'about:blank')

        finished = False
        retry = False
        stdout_acum = ''
        stderr_acum = ''
        msg = ''
        while not finished:
            if not app_response:
                try:
                    resp = p.sess.get(url, timeout=5)
                except Exception as e:
                    resp = requests.Response()
                    resp.status_code = str(e)
                
                if resp.status_code != 200 and not retry:
                    retry = True
                    log.error("## Binary_stat: Invalid app requests response: %s - retry: %s" % (resp.status_code, retry))
                    msg += resp.status_code
                    stdout_acum += resp.status_code
                    xbmc.executebuiltin(cmd_android)
                    time.sleep(3)
                    continue
                if resp.status_code != 200 and retry:
                    log.error("## Binary_stat: Invalid app requests response: %s - retry: %s" % (resp.status_code, retry))
                    msg += resp.status_code
                    stdout_acum += resp.status_code
                    app_response = {'pid': p.pid, 'retCode': 999}

                if resp.status_code == 200:
                    try:
                        app_response = resp.content
                        if PY3 and isinstance(app_response, bytes):
                            app_response = app_response.decode()
                        app_response_save = app_response
                        app_response = re.sub('\n|\r|\t', '', app_response)
                        app_response = json.loads(app_response)
                        test_json = app_response["pid"]
                    except:
                        status_code = resp.content
                        log.error("## Binary_stat: Invalid app response: %s - retry: %s" % (resp.content, retry))
                        if retry:
                            app_response = {'pid': p.pid}
                            app_response['retCode'] = 999
                            msg += app_response_save
                            stdout_acum += app_response_save
                        else:
                            retry = True
                            app_response = {}
                            time.sleep(1)
                            continue
                        
            if app_response.get("pid", 0):
                if app_response.get('output'):
                    stdout_acum += base64.b64decode(app_response['output']).decode('utf-8')
                    msg += base64.b64decode(app_response['output']).decode('utf-8')
                if app_response.get('error'): 
                    stderr_acum += base64.b64decode(app_response['error']).decode('utf-8')
                    msg += base64.b64decode(app_response['error']).decode('utf-8')
                if app_response.get('startDate'): 
                    p.startDate = base64.b64decode(app_response['startDate']).decode('utf-8')
                if app_response.get('endDate'): 
                    p.endDate = base64.b64decode(app_response['endDate']).decode('utf-8')
                if app_response.get('cmd'): 
                    p.cmd_app = base64.b64decode(app_response['cmd']).decode('utf-8')
                if app_response.get('finalCmd'): 
                    p.finalCmd = base64.b64decode(app_response['finalCmd']).decode('utf-8')

                # If still app permissions not allowed, give it a retry
                if 'permission denied' in msg:
                    from lib import kodi
                    kodi.notification('Accept Assitant permissions', time=15000)
                    time.sleep(5)
                    xbmc.executebuiltin(cmd_android_permissions)
                    time.sleep(15)
                    app_response['retCode'] = 999
                    msg = ''
                
                if msg:
                    try:
                        for line in msg.split('\n'):
                            line += '\n'
                            if PY3 and not isinstance(line, (bytes, bytearray)):
                                line = line.encode()
                            p.stdin.write(line)
                            p.stdin.flush()
                    except:
                        pass
            
            p.returncode = None
            if app_response.get('retCode', '') != '' or action == 'killBinary' or \
                            (action == 'communicate' and p.returncode is not None):
                try:
                    p.stdin.flush()
                    p.stdin.close()
                except:
                    pass
                try:
                    p.returncode = int(app_response['retCode'])
                except:
                    p.returncode = app_response['retCode'] or p.returncode
                
            if action == 'communicate' and p.returncode is not None:
                log.info("## Binary_stat: communicate Quasar: %s - Returncode: %s" % (p.pid, p.returncode))
                return stdout_acum, stderr_acum
            
            elif action == 'poll':
                if init and msg:
                    #log.warning('## Binary_stat: Quasar initial response: %s' % msg)
                    return True
                return p.returncode
            
            elif action == 'killBinary':
                log.info("## Binary_stat: killBinary Quasar: %s - Returncode: %s" % (p.pid, p.returncode))
                return p
            
            time.sleep(5)
            msg = ''
            app_response = {}

    except:
        log.error(traceback.format_exc())
    return None

def install_app(APP_PARAMS):
    import traceback
    import requests
    import xbmc
    import time
    from lib import kodi
    
    try:
        apk_OK = False
        res = False
        ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
        if not ANDROID_STORAGE: ANDROID_STORAGE = '/storage'
        LOCAL_DOWNLOAD_PATH = os.path.join(ANDROID_STORAGE, 'emulated', '0', 'Download')
        USER_APP_PATH = os.path.join(ANDROID_STORAGE, 'emulated', '0', 'Android', 'data')

        for user_addon, user_params in list(APP_PARAMS.items()):
            if not user_params['ACTIVE']: continue
                
            for apk_path in user_params['USER_APK']:
                if apk_path.endswith('.apk'):
                    download_path = LOCAL_DOWNLOAD_PATH
                elif user_params['USER_ADDON_STATUS']:
                    download_path = user_params['USER_ADDON_USERDATA']
                else:
                    continue
                
                if apk_path.startswith('http'):
                    try:
                        apk_body = requests.get(apk_path, timeout=10)
                    except Exception as e:
                        apk_body = requests.Response()
                        apk_body.status_code = str(e)
                    if apk_body.status_code != 200:
                        log.error("## Install_app: Invalid app requests response: %s" % (apk_body.status_code))
                        apk_OK = False
                        continue
                    with open(os.path.join(download_path, \
                            os.path.basename(apk_path)), "wb") as f:
                        f.write(apk_body.content)
                    apk_OK = True
                
                else:
                    if os.path.exists(apk_path):
                        shutil.copy(apk_path, download_path)
                        apk_OK = True
                    else:
                        continue
                if not apk_OK:
                    break
            
            if apk_OK:
                log.info("## Install_app: Installing the APK from: %s" % LOCAL_DOWNLOAD_PATH)
                kodi.notification('Install your Assistant %s from folder %s' % \
                            (os.path.basename(user_params['USER_APK'][0]), \
                            LOCAL_DOWNLOAD_PATH))
                cmd_android = 'StartAndroidActivity("%s", "", "%s", "%s")' % (user_params['USER_APP'], 'open', 'about:blank')
                cmd_android_permissions = 'StartAndroidActivity("%s", "", "%s", "%s")' % (user_params['USER_APP'], 'checkPermissions', 'about:blank')
                url_close = "%s:%s?quit" % (user_params['USER_APP_URL'], user_params['USER_APP_PORT'])
                
                # Lets give the user 5 minutes to install the app an retry automatically
                for x in range(300):
                    if os.path.exists(os.path.join(USER_APP_PATH, user_params['USER_APP'])):
                        log.info("## Install_app: APP installed: %s" % user_params['USER_APP'])
                        kodi.notification('Accept Assistant permissions')
                        time.sleep(5)
                        log.info("## Install_app: Requesting permissions: %s" % user_params['USER_APP'])
                        xbmc.executebuiltin(cmd_android_permissions)
                        time.sleep(15)
                        log.info("## Install_app: closing APP: %s" % user_params['USER_APP'])
                        kodi.notification('Accept Assistant permissions')
                        try:
                            permissions = requests.get(url_close, timeout=5)
                            log.info("## Install_app: APP closed: %s" % user_params['USER_APP'])
                        except Exception as e:
                            log.error("## Install_app: APP inaccessible.  Re-init Kodi. ERROR: %s" % str(e))
                        time.sleep(3)
                        return True
                    
                    xbmc.executebuiltin(cmd_android)
                    time.sleep(1)
                break
    
    except:
        log.info(traceback.format_exc())
    return res