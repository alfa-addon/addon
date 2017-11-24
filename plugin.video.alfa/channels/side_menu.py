# -*- coding: utf-8 -*-
# ------------------------------------------------------------

import os
from core.item import Item
from core import jsontools
from platformcode import config, logger
from platformcode import launcher
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

media_path = os.path.join(config.get_runtime_path(), "resources/skins/Default/media/side_menu/")
menu_node = jsontools.get_node_from_file('menu_settings_data.json', 'menu')
category = menu_node['categoria actual']

ACTION_SHOW_FULLSCREEN = 36
ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_DOWN = 4
ACTION_MOVE_UP = 3



def open_menu(item):
    main = Main('side_menu.xml', config.get_runtime_path())
    main.doModal()
    del main


class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []

    def onInit(self):
        self.setCoordinateResolution(2)
        self.focus = -1
        self.buttons = []
        posx= 22
        posy= 170
        space = 30

        selected = 'selected.png'
        width = 216
        height = 30
        textcolor = "0xff000000"
        shadow = "0xFFffff00"
        offsetx = 30

        label = 'Menú Clasico'
        self.button_alfa = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14', alignment=0x00000000,
                                                 noFocusTexture='', focusTexture=media_path+selected, 
                                                 textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                 textOffsetY=-3)
        self.addControl(self.button_alfa)
        self.buttons.append(self.button_alfa)
        posy += space*2
        label = 'Peliculas'
        self.button_peliculas = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                      alignment=0x00000000, noFocusTexture='',
                                                      focusTexture=media_path+selected, textColor=textcolor,
                                                      shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_peliculas)
        self.buttons.append(self.button_peliculas)
        posy += space
        label = 'Series'
        self.button_series = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                   alignment=0x00000000, noFocusTexture='',
                                                   focusTexture=media_path+selected, textColor=textcolor,
                                                   shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_series)
        self.buttons.append(self.button_series)
        posy += space
        label = 'Anime'
        self.button_anime = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14', alignment=0x00000000,
                                                  noFocusTexture='', focusTexture=media_path+selected,
                                                  textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                  textOffsetY=-3)
        self.addControl(self.button_anime)
        self.buttons.append(self.button_anime)
        posy += space
        label = 'Infantiles'
        self.button_infantil = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                     alignment=0x00000000, noFocusTexture='',
                                                     focusTexture=media_path+selected, textColor=textcolor,
                                                     shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_infantil)
        self.buttons.append(self.button_infantil)
        posy += space
        label = 'Documentales'
        self.button_docu = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                     alignment=0x00000000, noFocusTexture='',
                                                     focusTexture=media_path + selected, textColor=textcolor,
                                                     shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_docu)
        self.buttons.append(self.button_docu)
        posy += space

        label = 'Terror'
        self.button_terror = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                   alignment=0x00000000, noFocusTexture='',
                                                   focusTexture=media_path+selected, textColor=textcolor,
                                                   shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_terror)
        self.buttons.append(self.button_terror)
        posy += space
        label = 'Castellano'
        self.button_cast = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14', alignment=0x00000000,
                                                 noFocusTexture='', focusTexture=media_path+selected,
                                                 textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                 textOffsetY=-3)
        self.addControl(self.button_cast)
        self.buttons.append(self.button_cast)
        posy += space
        label = 'Latino'
        self.button_lat = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14', alignment=0x00000000,
                                                noFocusTexture='', focusTexture=media_path+selected,
                                                textColor=textcolor, shadowColor=shadow, textOffsetX=offsetx,
                                                textOffsetY=-3)
        self.addControl(self.button_lat)
        self.buttons.append(self.button_lat)
        posy += space
        label = 'Torrents'
        self.button_torrent = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                    alignment=0x00000000, noFocusTexture='',
                                                    focusTexture=media_path+selected, textColor=textcolor,
                                                    shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)
        self.addControl(self.button_torrent)
        self.buttons.append(self.button_torrent)
        posy += space
        label = 'Canales Activos'
        self.button_config = xbmcgui.ControlButton(posx, posy, width, height, label, font='font14',
                                                   alignment=0x00000000, noFocusTexture='',
                                                   focusTexture=media_path+selected, textColor=textcolor,
                                                   shadowColor=shadow, textOffsetX=offsetx, textOffsetY=-3)


        self.addControl(self.button_config)
        self.buttons.append(self.button_config)

        label=''
        self.button_close = xbmcgui.ControlButton(260, 0, 1020, 725, label, noFocusTexture='', focusTexture='')
        self.addControl(self.button_close)

    def onClick(self, control):
        new_item=''
        control = self.getControl(control).getLabel()
        if control == u'Menú Clasico':
            new_item = Item(channel='', action='getmainlist', title='Menú Alfa')
        elif control == 'Peliculas':
            new_item = Item(channel='news', action="novedades", extra="peliculas", mode='silent')
        elif control == 'Series':
            new_item = Item(channel='news', action="novedades", extra="series", mode='silent')
        elif control == 'Anime':
            new_item = Item(channel='news', action="novedades", extra="anime", mode='silent')
        elif control == 'Infantiles':
            new_item = Item(channel='news', action="novedades", extra="infantiles", mode='silent')
        elif control == 'Documentales':
            new_item = Item(channel='news', action="novedades", extra="documentales", mode='silent')
        elif control == 'Terror':
            new_item = Item(channel='news', action="novedades", extra="terror", mode='silent')
        elif control == 'Castellano':
            new_item = Item(channel='news', action="novedades", extra="castellano", mode='silent')
        elif control == 'Latino':
            new_item = Item(channel='news', action="novedades", extra="latino", mode='silent')
        elif control == 'Torrents':
            new_item = Item(channel='news', action="novedades", extra="torrent", mode='silent')
        elif control == 'Canales Activos':
            new_item = Item(channel='news', action="setting_channel", extra=category, menu=True)
        elif control == '':
            self.close()
        if new_item !='':
            self.run_action(new_item)
            
    def onAction(self, action):
        
        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.close()

        if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
            if self.focus < len(self.buttons) - 1:
                self.focus += 1
                while True:
                    id_focus = str(self.buttons[self.focus].getId())
                    if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                        self.setFocus(self.buttons[self.focus])
                        break
                    self.focus += 1
                    if self.focus == len(self.buttons):
                        break

        if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
            if self.focus > 0:
                self.focus -= 1
                while True:
                    id_focus = str(self.buttons[self.focus].getId())
                    if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                        self.setFocus(self.buttons[self.focus])
                        break
                    self.focus -= 1
                    if self.focus == len(self.buttons):
                        break

    def run_action(self, item):
        logger.info()
        if item.menu != True:
            self.close()
        xbmc.executebuiltin("Container.update(%s)"%launcher.run(item))

