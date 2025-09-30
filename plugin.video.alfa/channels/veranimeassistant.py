# -*- coding: utf-8 -*-
# -*- Channel VerAnime Assistant -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

from channels import veranime

def mainlist(item):
    return veranime.mainlist(item)

def sub_menu(item):
    return veranime.sub_menu(item)

def section(item):
    return veranime.section(item)

def list_all(item):
    return veranime.list_all(item)

def seasons(item):
    return veranime.seasons(item)

def episodesxseason(item, **AHkwargs):
    return veranime.episodesxseason(item, **AHkwargs)

def episodios(item):
    return veranime.episodios(item)

def findvideos(item):
    return veranime.findvideos(item)

def play(item):
    return veranime.play(item)

def actualizar_titulos(item):
    return veranime.actualizar_titulos(item)

def search(item, texto):
    return veranime.search(item, texto)

def newest(categoria, **AHkwargs):
    return newest(categoria, **AHkwargs)