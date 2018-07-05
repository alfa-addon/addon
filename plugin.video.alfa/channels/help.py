# -*- coding: utf-8 -*-

import os

from core.item import Item
from platformcode import config, logger, platformtools
from channelselector import get_thumb

if config.is_xbmc():

    import xbmcgui

    class TextBox(xbmcgui.WindowXMLDialog):
        """ Create a skinned textbox window """
        def __init__(self, *args, **kwargs):
            self.title = kwargs.get('title')
            self.text = kwargs.get('text')
            self.doModal()

        def onInit(self):
            try:
                self.getControl(5).setText(self.text)
                self.getControl(1).setLabel(self.title)
            except:
                pass

        def onClick(self, control_id):
            pass

        def onFocus(self, control_id):
            pass

        def onAction(self, action):
            # self.close()
            if action in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
                self.close()


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel, action="", title="FAQ:",
                         thumbnail=get_thumb("help.png"),
                         folder=False))
    if config.is_xbmc():
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60448),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="report_error"))
<<<<<<< HEAD
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60449),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="onoff_canales"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60450),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="trakt_sync"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60451),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="buscador_juntos"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60452),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="tiempo_enlaces"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60453),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="prob_busquedacont"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60454),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="canal_fallo"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(70280),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra="prob_torrent"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60455),
                             thumbnail=get_thumb("help.png"),
                             folder=True, extra="prob_bib"))
        itemlist.append(Item(channel=item.channel, action="faq",
                             title=config.get_localized_string(60456),
                             thumbnail=get_thumb("help.png"),
                             folder=False, extra=""))
=======
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - ¿Se pueden activar/desactivar los canales?",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="onoff_canales"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - ¿Es posible la sincronización automática con Trakt?",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="trakt_sync"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - ¿Es posible mostrar todos los resultados juntos en el buscador global?",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="buscador_juntos"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - Los enlaces tardan en aparecer.",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="tiempo_enlaces"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - La búsqueda de contenido no se hace correctamente.",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="prob_busquedacont"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - Algún canal no funciona correctamente.",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="canal_fallo"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - Los enlaces Torrent no funcionan.",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra="prob_torrent"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - No se actualiza correctamente la videoteca.",
                         thumbnail=get_thumb("help.png"),
                         folder=True, extra="prob_bib"))
    itemlist.append(Item(channel=item.channel, action="faq",
                         title="    - Enlaces de interés",
                         thumbnail=get_thumb("help.png"),
                         folder=False, extra=""))


    return itemlist


def faq(item):

    if item.extra == "onoff_canales":
        respuesta = platformtools.dialog_yesno(config.get_localized_string(60457),
                                               config.get_localized_string(60458))
        if respuesta == 1:
            from channels import setting
            setting.conf_tools(Item(extra='channels_onoff'))

    elif item.extra == "trakt_sync":
        respuesta = platformtools.dialog_yesno(config.get_localized_string(60457),
                                               config.get_localized_string(60459))
        if respuesta == 1:
            from channels import videolibrary
            videolibrary.channel_config(Item(channel='videolibrary'))

    elif item.extra == "tiempo_enlaces":
        respuesta = platformtools.dialog_yesno(config.get_localized_string(60457),
                                               config.get_localized_string(60460))
        if respuesta == 1:
            from channels import videolibrary
            videolibrary.channel_config(Item(channel='videolibrary'))

    elif item.extra == "prob_busquedacont":
        title = config.get_localized_string(60461) % item.title[6:]
        text = (config.get_localized_string(60462))

        return TextBox("DialogTextViewer.xml", os.getcwd(), "Default", title=title, text=text)

    elif item.extra == "canal_fallo":
        title = config.get_localized_string(60461) % item.title[6:]
        text = (config.get_localized_string(60463))

        return TextBox("DialogTextViewer.xml", os.getcwd(), "Default", title=title, text=text)

    elif item.extra == "prob_bib":
        platformtools.dialog_ok(config.get_localized_string(60457),
                                config.get_localized_string(60464))

        respuesta = platformtools.dialog_yesno(config.get_localized_string(60457),
                                               config.get_localized_string(60465))
        if respuesta == 1:
            itemlist = []
            from channels import setting
            new_item = Item(channel="setting", action="submenu_tools", folder=True)
            itemlist.extend(setting.submenu_tools(new_item))
            return itemlist

    elif item.extra == "prob_torrent":
        title = config.get_localized_string(60461) % item.title[6:]
        text = ("Puedes probar descargando el modulo 'libtorrent' de Kodi o "
                "instalando algun addon como 'Quasar' o 'Torrenter', "
                "los cuales apareceran entre las opciones de la ventana emergente "
                "que aparece al pulsar sobre un enlace torrent. "
                "'Torrenter' es más complejo pero también más completo "
                "y siempre funciona.")

        return TextBox("DialogTextViewer.xml", os.getcwd(), "Default", title=title, text=text)

    elif item.extra == "buscador_juntos":
        respuesta = platformtools.dialog_yesno(config.get_localized_string(60457),
                                               config.get_localized_string(60466))
        if respuesta == 1:
            from channels import search
            search.settings("")

    elif item.extra == "report_error":
        import xbmc
        if config.get_platform(True)['num_version'] < 14:
            log_name = "xbmc.log"
        else:
            log_name = "kodi.log"
        ruta = xbmc.translatePath("special://logpath") + log_name
        title = config.get_localized_string(60461) % item.title[6:]
        text = (config.get_localized_string(60467) % ruta)

        return TextBox("DialogTextViewer.xml", os.getcwd(), "Default", title=title, text=text)

    else:
        platformtools.dialog_ok(config.get_localized_string(60457),
                                config.get_localized_string(60468))


