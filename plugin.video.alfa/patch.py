# -*- coding: utf-8 -*-
import sys

original_path = sys.path
fixed_path = [path for path in original_path if not path.endswith("packages")]


def fix_path():
    if sys.version_info[0] >= 3:
        sys.path = fixed_path


def unfix_path():
    sys.path = original_path
