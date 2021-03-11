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
        log.info("Using binary folder: %s" % binary_dir)
        app_id = android_get_current_appid()
        xbmc_data_path = os.path.join("/data", "data", app_id)
        
        try:                    #Test if there is any permisions problem
            f = open(os.path.join(xbmc_data_path, "test.txt"), "wb")
            f.write("test")
            f.close()
            os.remove(os.path.join(xbmc_data_path, "test.txt"))
        except:
            xbmc_data_path = ''
        
        if not os.path.exists(xbmc_data_path):
            log.info("%s path does not exist, so using %s as xbmc_data_path" % (xbmc_data_path, translatePath("special://xbmcbin/")))
            xbmc_data_path = translatePath("special://xbmcbin/")

            try:                    #Test if there is any permisions problem
                f = open(os.path.join(xbmc_data_path, "test.txt"), "wb")
                f.write("test")
                f.close()
                os.remove(os.path.join(xbmc_data_path, "test.txt"))
            except:
                xbmc_data_path = ''
        
        if not os.path.exists(xbmc_data_path):
            log.info("%s path does not exist, so using %s as xbmc_data_path" % (xbmc_data_path, translatePath("special://masterprofile/")))
            xbmc_data_path = translatePath("special://masterprofile/")
        dest_binary_dir = os.path.join(xbmc_data_path, "files", ADDON_ID, "bin", "%(os)s_%(arch)s" % PLATFORM)
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

    #return subprocess.Popen(args, **kwargs)
    return call_binary('OpenBinary', args, **kwargs)

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

            if PLATFORM["os"] == "windows":
                while proc.poll() is None:
                    log.info(proc.stdout.readline())
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
                            log.info(line)
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
def call_binary(function, cmd, wait=False, retry=False, **kwargs):
    import xbmcaddon
    import traceback
    import base64
    import requests
    import json

    APP_PARAMS = {
                  'Alfa':     {
                               'ACTIVE': 1, 
                               'USER_ADDON': 'plugin.video.alfa', 
                               'USER_ADDON_STATUS': xbmc.getCondVisibility('System.HasAddon("plugin.video.alfa")'), 
                               'USER_ADDON_USERDATA': os.path.join(translatePath('special://masterprofile/'), 
                                            'addon_data', 'plugin.video.alfa'), 
                               'USER_APK': ['https://github.com/alfa-addon/alfa-repo/tree/master/downloads/assistant/alfa-mobile-assistant.apk',
                                            'https://github.com/alfa-addon/alfa-repo/tree/master/downloads/assistant/alfa-mobile-assistant.version'], 
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
    USER_APP = ''
    USER_APP_STATUS = False
    USER_DEVICE_ROOTED = False
    ANDROID_VERSION = get_android_version()

    if xbmc.getCondVisibility("system.platform.Android") and PY3 and ANDROID_VERSION >= 10:
        for user_addon, user_params in list(APP_PARAMS.items()):
            if not user_params['ACTIVE'] or not user_params['USER_ADDON_STATUS']: continue

            if user_addon == 'Alfa':
                try:
                    try:
                        # Alfa add-on and Alfa Assistant installed
                        USER_ADDON_SETTING = xbmcaddon.Addon(id="%s" % user_params['USER_ADDON'])
                        USER_ADDON = user_params['USER_ADDON']
                        USER_ADDON_STATUS = True
                        if USER_ADDON_SETTING.getSetting('assistant_mode') == 'este' and \
                                os.path.exists(os.path.join(user_params['USER_ADDON_USERDATA'], \
                                user_params['USER_APP_CONTROL'])):
                            USER_APP = user_params['USER_APP']
                            USER_APP_STATUS = True
                            if USER_ADDON_SETTING.getSetting('assistant_custom_address'):
                                USER_APP_URL = "http://%s" % USER_ADDON_SETTING.getSetting('assistant_custom_address')
                            else:
                                USER_APP_URL = user_params['USER_APP_URL']
                            USER_APP_URL = "%s:%s" % (USER_APP_URL, user_params['USER_APP_PORT'])
                        if USER_ADDON_SETTING.getSetting('is_rooted_device') == 'rooted':
                            QUASAR_ADDON_SETTING.setSetting('is_rooted_device', 'rooted')
                            USER_DEVICE_ROOTED = True
                        elif USER_APP_STATUS and is_rooted(QUASAR_ADDON_SETTING) == 'rooted':
                            USER_DEVICE_ROOTED = True
                    except:
                        # Only Alfa Assistant installed
                        if os.path.exists(os.path.join(os.path.dirname(translatePath(
                                'special://xbmcbinaddons/'), user_params['USER_APP']))):
                            USER_APP_STATUS = True
                        if USER_APP_STATUS and is_rooted(QUASAR_ADDON_SETTING) == 'rooted':
                            USER_DEVICE_ROOTED = True
                    if USER_APP_STATUS: break
                except:
                    log.error(traceback.format_exc())

        if not USER_APP_STATUS:
            res = install_app(APP_PARAMS)
            if not res:
                raise ValueError("No app:  Must be installed")
            else:
                if not retry:
                    return call_binary(function, cmd, retry=True, **kwargs)
                else:
                    log.error(traceback.format_exc())
                    raise ValueError("No app:  Problem with installation")

    p = None
    if USER_APP_STATUS and not USER_DEVICE_ROOTED:
        log.info('Calling Quasar from Assistant App. Retry = %s' % retry)
        try:
            # Lets start the Assistant app
            url = USER_APP_URL + '/openBinary?cmd='
            command = []
            status_code = 0
            cmd_android = 'StartAndroidActivity("%s", "", "%s", "%s")' % (USER_APP, 'open', 'about:blank')
            xbmc.executebuiltin(cmd_android)
            time.sleep(1)
            
            # Build the command & params
            if isinstance(cmd, list):
                cmd_app = cmd.copy()
                cmd_app[0] = 'libquasart.so'
                command.append(cmd_app)
                command.append([])
                for key, value in list(kwargs.get('env', {}).items()):
                    if key == 'LD_LIBRARY_PATH':
                        # The app will replace **CWD** by the binary/lib path
                        value = '**CWD**'
                    command[1].append('%s=%s' % (key, value))
                command_base64 = base64.b64encode(str(command).encode('utf8')).decode('utf8')
            else:
                command_base64 = cmd
            
            # Launch the Binary
            try:
                resp = requests.get(url+command_base64, timeout=5)
            except:
                resp = requests.Response()
            status_code = resp.status_code
            if status_code != 200 and not retry:
                time.sleep(3)
                return call_binary(function, cmd, retry=True, **kwargs)
            elif status_code != 200 and retry:
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
            class p(object):
                {'pid': 0, 
                 'returncode': None, 
                 'stdout': '', 
                 'stdin': '', 
                 'stderr': '',
                 'startDate': '', 
                 'endDate': '', 
                 'poll': '', 
                 'terminate': '', 
                 'communicate': '', 
                 'app': '', 
                 'url': '',
                 'cmd': ''}
            
            try:
                setattr(p, 'pid', int(app_response['pid']))
            except:
                raise ValueError("No valid PID returned:  PID code: %s" % resp.content)
            pipeout, pipein = os.pipe()
            setattr(p, 'stdout', os.fdopen(pipeout, 'rb'))
            setattr(p, 'stdin', os.fdopen(pipein, 'wb'))
            setattr(p, 'stderr', p.stdout)
            setattr(p, 'returncode', None)
            setattr(p, 'startDate', '')
            setattr(p, 'endDate', '')
            setattr(p, 'terminate', '')
            setattr(p, 'communicate', '')
            setattr(p, 'poll', '')
            setattr(p, 'app', USER_APP)
            setattr(p, 'url', USER_APP_URL)
            setattr(p, 'cmd', command_base64)
            
            def redirect_terminate(p=p, action='killBinary'):
                return binary_stat(p, action)
            def redirect_poll(p=p, action='poll'):
                return binary_stat(p, action)
            def redirect_communicate(p=p, action='communicate'):
                return binary_stat(p, action)
            p.terminate = redirect_terminate
            p.poll = redirect_poll
            p.communicate = redirect_communicate

            log.info('## Assistant executing CMD: %s - PID: %s' % (command[0], p.pid))
            log.warning('## Assistant executing CMD **kwargs: %s' % command[1])
            return p
        except:
            log.error('## Assistant ERROR %s in CMD: %s%s' % (status_code, url, command))
            log.error(traceback.format_exc())
            p = None
    
    if not p:
        try:
            p = subprocess.Popen(cmd, **kwargs)
        except Exception as e:
            if not PY3:
                e = unicode(str(e), "utf8", errors="replace").encode("utf8")
            elif PY3 and isinstance(e, bytes):
                e = e.decode("utf8")
            log.error('Exception Popen ERROR: %s, %s' % (str(cmd), str(e)))
        return p
        
def binary_stat(p, action, retry=False):
    #log.info('binary_stat: action: %s - PID: %s - retry: %s' % (action, p.pid, retry))
    import traceback
    import base64
    import requests
    import json
    import time
    
    try:
        if action in ['poll', 'communicate']:
            url = p.url + '/getBinaryStatus?pid=' + str(p.pid)

        if action == 'killBinary':
            url = p.url + '/killBinary?pid=' + str(p.pid)

        finished = False
        stdout_acum = ''
        stderr_acum = ''
        while not finished:
            try:
                resp = requests.get(url, timeout=5)
            except:
                resp = requests.Response()
            if resp.status_code != 200 and not retry:
                import xbmc
                cmd_android = 'StartAndroidActivity("%s", "", "%s", "%s")' % (p.app, 'open', 'about:blank')
                xbmc.executebuiltin(cmd_android)
                time.sleep(3)
                continue
            if resp.status_code != 200 and retry:
                return call_binary('openBinary', p.cmd, retry=True)

            if resp.status_code == 200:
                try:
                    app_response = resp.content
                    if PY3 and isinstance(app_response, bytes):
                        app_response = app_response.decode()
                    app_response = re.sub('\n|\r|\t', '', app_response)
                    app_response = json.loads(app_response)
                except:
                    status_code = resp.content
                    log.info("Invalid app response: %s" % resp.content)
                    time.sleep(5)
                    continue
                
                if app_response.get("pid", 0):
                    msg = ''
                    if app_response.get('output'):
                        stdout_acum += base64.b64decode(app_response['output']).decode('utf-8') + '\n'
                        msg += base64.b64decode(app_response['output']).decode('utf-8')
                    if app_response.get('error'): 
                        stderr_acum += base64.b64decode(app_response['error']).decode('utf-8') + '\n'
                        msg += base64.b64decode(app_response['error']).decode('utf-8')

                    if msg:
                        msg += '\n'
                        if PY3 and not isinstance(msg, (bytes, bytearray)):
                            msg = msg.encode()
                        try:
                            p.stdin.write(msg)
                            p.stdin.flush()
                        except:
                            log.info(traceback.format_exc())
                
                p.returncode = None
                if app_response.get('retCode', ''):
                    try:
                        p.returncode = int(app_response['retCode'])
                    except:
                        p.returncode = app_response['retCode']
                    
                if action == 'communicate' and p.returncode is not None:
                    return stdout_acum, stderr_acum
                elif action == 'poll':
                    return p.returncode
                elif action == 'killBinary':
                    return p
            
            time.sleep(5)

    except:
        logging.info(traceback.format_exc())
    return None

def get_android_version():
    import re
    import traceback
    
    version = 8
    if PY3: FF = b'\n'
    else: FF = '\n'
    
    if xbmc.getCondVisibility("system.platform.Android"):
        try:
            for label_a in subprocess.check_output('getprop').split(FF):
                if PY3 and isinstance(label_a, bytes):
                    label_a = label_a.decode()
                if 'build.version.release' in label_a:
                    version = int(re.findall(':\s*\[(.*?)\]$', label_a, flags=re.DOTALL)[0])
                    break
        except:
            log.info(traceback.format_exc())
            try:
                if PY3: fp = open(os.environ['ANDROID_ROOT'] + '/build.prop', 'r', encoding='utf-8')
                else: fp = open(os.environ['ANDROID_ROOT'] + '/build.prop', 'r')
                for label_a in fp.read().split():
                    if PY3 and isinstance(label_a, bytes):
                        label_a = label_a.decode()
                    if 'build.version.release' in label_a:
                        version = int(re.findall('=(.*?)$', label_a, flags=re.DOTALL)[0])
                        break
                f.close()
            except:
                log.info(traceback.format_exc())
                try:
                    f.close()
                except:
                    pass
    
    return version

def is_rooted(USER_ADDON_SETTING):
    
    res = USER_ADDON_SETTING.getSetting('is_rooted_device')
    if res in ['rooted', 'no_rooted']:
        return res
    
    res = 'no_rooted'
    notify('QUASAR: Verifying Super-user privileges', \
                'If requested, you MUST accept Super-user privileges for Kodi', time=10000)
    
    try:
        for subcmd in ['-c', '-0']:
            command = ['su', subcmd, 'ls']
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_cmd, error_cmd = p.communicate()
            if not error_cmd:
                res = 'rooted'
                USER_ADDON_SETTING.setSetting('is_rooted_device', 'rooted')
                break
        else:
            USER_ADDON_SETTING.setSetting('is_rooted_device', 'no_rooted')
    except:
        USER_ADDON_SETTING.setSetting('is_rooted_device', 'no_rooted')
    
    return res

def install_app(APP_PARAMS):
    import traceback
    import requests
    
    ANDROID_STORAGE = os.getenv('ANDROID_STORAGE')
    if not ANDROID_STORAGE: ANDROID_STORAGE = '/storage'
    LOCAL_DOWNLOAD_PATH = os.path.join(ANDROID_STORAGE, 'emulated', '0', 'Download')
    apk_OK = False
    res = False
    
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
                except:
                    apk_body = requests.Response()
                if apk_body.status_code != 200:
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
            notify('QUASAR: Installing your Assistant', \
                        'Install %s from folder %s' % (os.path.basename(user_params['USER_APK']), \
                        LOCAL_DOWNLOAD_PATH), time=10000)
            # Lets give the user 5 minutes to install the app an retry automatically
            for x in range(300):
                if os.path.exists(os.path.join(os.path.dirname(translatePath(
                        'special://xbmcbinaddons/'), user_params['USER_APP']))):
                    return True
                    time.sleep(1)
            break
    
    return res