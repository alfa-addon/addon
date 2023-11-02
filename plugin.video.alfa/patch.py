# -*- coding: utf-8 -*-
import sys

def fix_path():
    new_path = []
    for path in sys.path:
        if path.endswith("packages"):
            continue
        new_path.append(path)
    sys.path = new_path

