# -*- coding: utf-8 -*-
import sys
import os


def fix_path():
    import xbmcaddon
    if sys.version_info[0] >= 3:
        import xbmc
        import xbmcvfs
    else:
        import xbmc
        xbmcvfs = xbmc
    whitelist = ['Cryptodome', 'PIL']
    # Solo ha de suceder en Linux
    if "linux" in sys.platform and not xbmc.getCondVisibility("System.Platform.Android"):
        packages_paths = []
        alfa_lib_path = xbmcaddon.Addon().getAddonInfo("path")
        alfa_lib_path = xbmcvfs.translatePath(alfa_lib_path)
        alfa_lib_path = os.path.join(alfa_lib_path, 'lib')
        packages_paths = [
            path for path in sys.path if path.endswith("packages")]
        for system_path in packages_paths:
            sys.path.remove(system_path)
            # Creamos enlaces simbolicos a bibliotecas del sistema en whitelist
            for lib in list(whitelist):  # Clonamos la lista para modificar la original
                module_path = os.path.join(system_path, lib)
                module_symlink_path = os.path.join(alfa_lib_path, lib)
                exists = False
                # Comprobamos que no existe ya un enlace simbolico
                if os.path.exists(module_symlink_path):
                    exists = True
                # Comprobamos que existe en el sistema
                elif os.path.exists(module_path):
                    exists = True
                    os.symlink(module_path, module_symlink_path)

                if exists:
                    whitelist.remove(lib)
