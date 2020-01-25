from future import standard_library
standard_library.install_aliases()
from future.builtins import map
#from future.builtins import str
from future.builtins import range

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import stat
import time
import xbmc
import shutil
import socket
import urllib.request, urllib.error, urllib.parse
import xbmcgui
import threading
import subprocess
from quasar.logger import log
from quasar.osarch import PLATFORM
from quasar.config import QUASARD_HOST
from quasar.addon import ADDON, ADDON_ID, ADDON_PATH
from quasar.util import notify, system_information, getLocalizedString, getWindowsShortPath

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
            log.info("%s path does not exist, so using %s as xbmc_data_path" % (xbmc_data_path, xbmc.translatePath("special://xbmcbin/")))
            xbmc_data_path = xbmc.translatePath("special://xbmcbin/")

            try:                    #Test if there is any permisions problem
                f = open(os.path.join(xbmc_data_path, "test.txt"), "wb")
                f.write("test")
                f.close()
                os.remove(os.path.join(xbmc_data_path, "test.txt"))
            except:
                xbmc_data_path = ''
        
        if not os.path.exists(xbmc_data_path):
            log.info("%s path does not exist, so using %s as xbmc_data_path" % (xbmc_data_path, xbmc.translatePath("special://masterprofile/")))
            xbmc_data_path = xbmc.translatePath("special://masterprofile/")
        dest_binary_dir = os.path.join(xbmc_data_path, "files", ADDON_ID, "bin", "%(os)s_%(arch)s" % PLATFORM)
    else:
        if not PY3:
            dest_binary_dir = os.path.join(xbmc.translatePath(ADDON.getAddonInfo("profile")).decode('utf-8'), "bin", "%(os)s_%(arch)s" % PLATFORM)
        else:
            dest_binary_dir = os.path.join(xbmc.translatePath(ADDON.getAddonInfo("profile")), "bin", "%(os)s_%(arch)s" % PLATFORM)
            if isinstance(dest_binary_dir, bytes):
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
                    library_lockfile = os.path.join(xbmc.translatePath(ADDON.getAddonInfo("profile")).decode('utf-8'), "library.db.lock")
                else:
                    library_lockfile = os.path.join(xbmc.translatePath(ADDON.getAddonInfo("profile")), "library.db.lock")
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

    return subprocess.Popen(args, **kwargs)

def shutdown():
    try:
        urllib.request.urlopen(QUASARD_HOST + "/shutdown")
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
        while not xbmc.abortRequested:
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
            if proc.returncode == 0 or xbmc.abortRequested:
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
