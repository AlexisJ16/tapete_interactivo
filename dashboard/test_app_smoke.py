"""Smoke headless de la GUI (PyQt6 en plataforma 'offscreen')."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import smoke


def test_app_smoke():
    assert smoke() == 0
