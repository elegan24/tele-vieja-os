#!/usr/bin/env python3
"""Prepara el marco (bezel) para mpv. Lo llama sistema/marco.lua:
   marco.py preparar CARPETA ANCHO ALTO CACHE  -> una línea JSON"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from televieja import marcos  # noqa: E402

sys.exit(marcos.main(sys.argv[1:]))
