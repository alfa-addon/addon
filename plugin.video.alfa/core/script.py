# -*- coding: utf-8 -*-
import os
import re
import shutil

from platformcode import config, logger, platformtools


def conversion():
    logger.info()
    data = ""

    try:
        # do a backup
        path_settings = os.path.join(config.get_data_path(), "settings.xml")
        path_settings_backup = os.path.join(config.get_data_path(), "settings.backup.xml")
        shutil.copy(path_settings, path_settings_backup)

        # open file
        f = open(path_settings, "r")
        # copy = open(path_settings2, "w")

        logger.info("              ---")
        logger.info("              --- 1")
        logger.info("              --- 2")
        logger.info("              --- 3")
        data_aux = ""

        begin_tag = "<settings>\n"
        end_tag = "</settings>\n"

        adult_data = '    <setting id="adult_aux_intro_password" value="" />\n'
        adult_data += '    <setting id="adult_aux_new_password1" value="" />\n'
        adult_data += '    <setting id="adult_aux_new_password2" value="" />\n'
        adult_data += '    <setting id="adult_mode" value="0" />\n'
        adult_data += '    <setting id="adult_password" value="0000" />\n'
        adult_data += '    <setting id="adult_request_password" value="false" />\n'

        for line in f:
            matches = re.findall('<setting id="([^"]*)" value="([^"]*)', line, re.DOTALL)
            logger.info("macthes %s" % matches)
            if not matches:
                logger.info("no matches")
                # for <settings></settings> tag
                # data += line
            else:
                logger.info("Matches")
                for _id, value in matches:
                    logger.info("  dentro del for")
                    logger.info("  _id:%s value:%s" % (_id, value))

                    if _id not in ["adult_aux_intro_password", "adult_aux_new_password1", "adult_aux_new_password2",
                                   "adult_mode", "adult_password", "adult_request_password", "adult_pin"]:
                        logger.info("    linea %s" % line)
                        logger.info("     value %s" % value)
                        if value:
                            # logger.info("    type value!! %s" % type(value))
                            logger.info("     antes value!! %s" % value)
                            if "(str, " in value:
                                if "(str, &apos;" in value:
                                    value = value.replace("(str, &apos;", "")
                                    value = value.replace("&apos;)", "")
                                elif "(str, '":
                                    value = value.replace("(str, '", "")
                                    value = value.replace("')", "")
                            elif "(bool, " in value:
                                value = value.replace("(bool, ", "")
                                if value == "True)":
                                    value = "true"
                                else:
                                    value = "false"

                            logger.info("     despues value!! %s" % value)

                        aux_line = '<setting id="%s" value="%s" />\n' % (_id, value)
                        logger.info("    aux_line %s" % aux_line)
                        data_aux += "    " + aux_line
        f.close()

        data = begin_tag + adult_data + data_aux + end_tag

        copy_file = open(path_settings, "w")
        copy_file.write(data)
        copy_file.close()

        while not platformtools.dialog_yesno("Alfa", "Corregido un error en la sección adultos, se ha reseteado la "
                                                     "contraseña a por defecto, tendrá que cambiarla de nuevo si lo desea.",
                                             "pulse 'Si', si lo ha entendido"):
            logger.info("En disclaimer clickó 'No'")

        logger.info("En disclaimer clickó 'Si'")
        platformtools.dialog_ok("Alfa", "Espere 5 segundos y ya estará todo OK.")
        return True

    except Exception, ex:
        template = "An exception of type %s occured. Arguments:\n%r"
        message = template % (type(ex).__name__, ex.args)
        logger.info(message)
        platformtools.dialog_ok("Alfa", "Error, en conversión")
        logger.info("Datos a guardar %s" % data)
        return False
